"""诊断本机哪条语音链路能出声。

用法（在项目根目录）：
    .venv\\Scripts\\python.exe tools\\voice_probe.py

每条都会真的尝试发声/合成，打印 OK 或失败原因。
"""

from __future__ import annotations

import base64
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _show(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "gbk"
        print(text.encode(encoding, "replace").decode(encoding, "replace"))


def _hr(exc: Exception) -> str:
    candidates: list[int] = []
    args = getattr(exc, "args", ())
    if len(args) >= 3 and isinstance(args[2], tuple) and len(args[2]) >= 6:
        inner = args[2][5]
        if isinstance(inner, int) and inner:
            candidates.append(inner)
    own = getattr(exc, "hresult", None)
    if isinstance(own, int):
        candidates.append(own)
    if args and isinstance(args[0], int):
        candidates.append(args[0])
    for code in candidates:
        if isinstance(code, int) and code:
            return f"0x{code & 0xFFFFFFFF:08X}"
    return "?"


def _voice():
    """先按产品代码的方式初始化 pywin32 缓存，再取 SAPI 对象。"""
    from dota2coach.ui.voice import Speaker

    speaker = Speaker(speak=True, beep=False, log_path=LOG_DIR / "voice_probe.log")
    if speaker._voice is None:  # noqa: SLF001 - 诊断脚本
        raise RuntimeError(speaker.last_error or "SAPI 初始化失败")
    return speaker._voice  # noqa: SLF001


def check(name: str, func) -> None:
    try:
        detail = func()
        _show(f"[OK]   {name}" + (f"  {detail}" if detail else ""))
    except Exception as exc:  # noqa: BLE001
        _show(f"[FAIL] {name}  hr={_hr(exc)}  {exc}")


def sapi_default() -> str:
    voice = _voice()
    voice.Speak("语音测试，默认输出", 0)
    return "已调用 Speak，应能听到声音"


def sapi_each_voice() -> str:
    voice = _voice()
    tokens = voice.GetVoices()
    done = []
    for index in range(tokens.Count):
        token = tokens.Item(index)
        try:
            voice.Voice = token
            voice.Speak(f"语音测试，第 {index + 1} 个音色", 0)
            done.append(token.GetDescription())
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"音色 {token.GetDescription()} 失败 hr={_hr(exc)}") from exc
    return "、".join(done)


def sapi_mm_output() -> str:
    voice = _voice()
    from win32com.client import dynamic  # type: ignore[import-not-found]

    audio_out = dynamic.Dispatch("SAPI.SpMMAudioOut")
    voice.AudioOutputStream = audio_out
    voice.Speak("语音测试，指定音频输出", 0)
    return "SpMMAudioOut 可用"


def sapi_22k_mono() -> str:
    voice = _voice()
    from win32com.client import dynamic  # type: ignore[import-not-found]

    fmt = dynamic.Dispatch("SAPI.SpAudioFormat")
    fmt.Type = 22  # SAFT22kHz16BitMono
    audio_out = dynamic.Dispatch("SAPI.SpMMAudioOut")
    audio_out.Format = fmt
    voice.AudioOutputStream = audio_out
    voice.Speak("语音测试，二十二k单声道", 0)
    return "22kHz 16bit 单声道输出可用"


def sapi_ps32() -> str:
    script = (
        "$ErrorActionPreference = 'Stop'; "
        "try { "
        "$v = New-Object -ComObject SAPI.SpVoice; "
        "$v.Speak('语音测试，三十二位进程', 0); "
        "Write-Output 'ok' "
        "} catch { Write-Output ('fail: ' + $_.Exception.Message); exit 1 }"
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    exe = Path(os.environ.get("WINDIR", r"C:\Windows")) / "SysWOW64" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    if not exe.exists():
        raise RuntimeError("没有 32 位 PowerShell")
    result = subprocess.run(
        [str(exe), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True,
        timeout=60,
        creationflags=0x08000000,
    )
    if result.returncode != 0:
        raise RuntimeError(f"退出码 {result.returncode}: {result.stderr.decode('utf-8', 'replace')[:200]}")
    return "32 位 SAPI 调用成功"


def winrt_synth() -> str:
    script = r"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
[Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null
$voices = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices
Write-Output ('voices=' + $voices.Count)
$synth = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::new()
if ($voices.Count -gt 0) { $synth.Voice = $voices[0] }
$op = $synth.SynthesizeTextToStreamAsync('语音测试，现代语音接口')
$asTask = $asTaskGeneric.MakeGenericMethod([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
$task = $asTask.Invoke($null, @($op))
$task.Wait(15000) | Out-Null
$stream = $task.Result
$net = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream)
$path = Join-Path $env:LOGDIR 'tts_winrt.wav'
$fs = [System.IO.File]::Create($path)
$net.CopyTo($fs); $fs.Close()
Write-Output ('wav=' + (Get-Item $path).Length)
"""
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    env = dict(os.environ)
    env["LOGDIR"] = str(LOG_DIR)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True,
        timeout=120,
        creationflags=0x08000000,
        env=env,
    )
    out = (result.stdout + result.stderr).decode("utf-8", "replace").strip()
    if result.returncode != 0:
        raise RuntimeError(_clean(out) or f"退出码 {result.returncode}")
    return _clean(out)


def _clean(text: str) -> str:
    """去掉 PowerShell 进度/CLIXML 噪声，只留人话。"""
    if "#< CLIXML" in text or "<Objs" in text:
        import re

        parts = re.findall(r'<S S="Error">(.*?)</S>', text, flags=re.S)
        if parts:
            text = " ".join(parts)
        text = (
            text.replace("_x000D_", " ")
            .replace("_x000A_", " ")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
        )
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("<") or line.startswith("#<") or line.startswith("<?xml"):
            continue
        lines.append(line)
    joined = " | ".join(lines) if lines else text.strip()[:200]
    return joined[:300]


def beep() -> str:
    import winsound

    winsound.MessageBeep(winsound.MB_ICONASTERISK)
    winsound.Beep(1568, 150)
    return "应听到一声系统提示音 + 一声高音叮"


def main() -> int:
    _show(f"Python {sys.version.split()[0]}  {sys.executable}")
    check("SAPI 默认输出", sapi_default)
    check("SAPI 逐个音色", sapi_each_voice)
    check("SAPI SpMMAudioOut", sapi_mm_output)
    check("SAPI 22kHz 单声道", sapi_22k_mono)
    check("SAPI 32 位 PowerShell", sapi_ps32)
    check("WinRT 合成到 WAV", winrt_synth)
    check("提示音 winsound", beep)
    _show(f"WinRT 产物: {LOG_DIR / 'tts_winrt.wav'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
