"""语音/音效提醒：优先用 Windows 自带的 SAPI 朗读，失败时回退到 PowerShell。

设计原则：
- 发声失败不影响卡片和其他功能；
- 朗读失败时提示音仍然可用（两者解耦）；
- 失败原因写进 logs/voice.log，方便排查。

已知的坑与对策：
1. pywin32 的 COM 缓存写在 `win32api.GetTempPath()\\gen_py`，某些机器上该目录
   权限异常会抛 `[WinError 5] 拒绝访问`。初始化前把 TEMP/TMP 和
   `win32com.__gen_path__` 都改到项目 `logs\\pywin32_tmp`。
2. SAPI 的 `Speak` 可能报 `0x8004503A`（音频输出初始化失败）。此时改用
   PowerShell 子进程：先试 SAPI 直接朗读，再试“合成 WAV 后用 SoundPlayer 播放”，
   最后才退到 System.Speech；每一步的结果写 `logs/voice_ps.log`。
"""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from .sounds import ensure_sounds, play as play_sound

CHINESE_HINTS = ("chinese", "中文", "huihui", "yaoyao", "kangkang", "xiaoxiao")

_CREATE_NO_WINDOW = 0x08000000


def _edge_available() -> bool:
    """装了 edge-tts 才能用在线朗读（不发起网络请求，只查包）。"""
    try:
        import edge_tts  # type: ignore[import-not-found]  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


class Speaker:
    """朗读 + 提示音；同一句话不重复念，且遵守最小间隔。"""

    def __init__(
        self,
        enabled: bool = True,
        speak: bool = True,
        rate: int = 0,
        volume: int = 100,
        min_interval: float = 8.0,
        beep: bool = True,
        log_path: Path | None = None,
        gate=None,
        wait_max: float = 4.0,
        backend: str = "auto",
        edge_voice: str = "zh-CN-XiaoxiaoNeural",
    ) -> None:
        self.enabled = bool(enabled) and sys.platform == "win32"
        self.speak = bool(speak)
        self.beep = bool(beep)
        self.min_interval = float(min_interval)
        self.rate = max(-10, min(10, int(rate)))
        self.volume = max(0, min(100, int(volume)))
        self.log_path = log_path
        self.backend_pref = (backend or "auto").strip().lower()
        try:
            from .voices import normalize_edge_voice

            self.edge_voice = normalize_edge_voice(edge_voice)
        except Exception:  # noqa: BLE001 - 音色名修复失败不该影响启动
            self.edge_voice = edge_voice
        self.gate = gate
        self.wait_max = float(wait_max)
        self.backend = "none"
        self.last_error = ""
        self._voice = None
        self._ps_failed = False
        self._ps_failures = 0
        self._sapi_failed = False
        self._sapi_failures = 0
        self._edge_ok = False
        self._thread: threading.Thread | None = None
        self._sounds: dict[str, Path] = {}
        self._last_at = 0.0
        self._last_text = ""

        if not self.enabled:
            return
        if self.speak and self.backend_pref in ("auto", "sapi"):
            self._prepare_pywin32_tempdir()
            self._init_sapi()
        if self.speak and self.backend_pref in ("auto", "edge"):
            self._edge_ok = _edge_available()
        if self._voice is not None:
            self.backend = "sapi"
        elif self._edge_ok:
            self.backend = "edge"
        self._log(
            f"初始化：enabled={self.enabled} speak={self.speak} beep={self.beep} "
            f"pref={self.backend_pref} backend={self.backend} {self.last_error}".strip()
        )

    @property
    def edge_available(self) -> bool:
        return _edge_available()

    # ------------------------------------------------------------------ 初始化

    def _prepare_pywin32_tempdir(self) -> None:
        """把 pywin32 的 COM 缓存目录挪到项目 logs 下。"""
        try:
            base = self.log_path.parent if self.log_path is not None else Path.cwd() / "logs"
            target = (base / "pywin32_tmp").resolve()
            target.mkdir(parents=True, exist_ok=True)
            os.environ["TEMP"] = str(target)
            os.environ["TMP"] = str(target)
            tempfile.tempdir = str(target)

            import win32com  # type: ignore[import-not-found]

            gen_path = str(target / "gen_py" / f"{sys.version_info.major}.{sys.version_info.minor}")
            win32com.__gen_path__ = gen_path
            os.makedirs(gen_path, exist_ok=True)
        except Exception:  # noqa: BLE001
            pass

    def _init_sapi(self) -> None:
        errors: list[str] = []
        for label, factory in (
            ("dynamic", self._dynamic_voice),
            ("gencache", self._gencache_voice),
        ):
            try:
                voice = factory()
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{label}: {exc}")
                continue
            self._pick_chinese_voice(voice)
            try:
                voice.Rate = self.rate
                voice.Volume = self.volume
            except Exception:  # noqa: BLE001
                pass
            self._voice = voice
            self.last_error = ""
            return
        self._voice = None
        self.last_error = "SAPI 初始化失败: " + " | ".join(errors)

    @staticmethod
    def _dynamic_voice():
        from win32com.client import dynamic  # type: ignore[import-not-found]

        return dynamic.Dispatch("SAPI.SpVoice")

    @staticmethod
    def _gencache_voice():
        import win32com.client  # type: ignore[import-not-found]

        return win32com.client.Dispatch("SAPI.SpVoice")

    def _pick_chinese_voice(self, voice) -> None:
        try:
            tokens = voice.GetVoices()
        except Exception:  # noqa: BLE001
            return
        for index in range(tokens.Count):
            token = tokens.Item(index)
            try:
                desc = (token.GetDescription() or "").lower()
            except Exception:  # noqa: BLE001
                continue
            if any(hint in desc for hint in CHINESE_HINTS):
                try:
                    voice.Voice = token
                except Exception:  # noqa: BLE001
                    pass
                return

    # ------------------------------------------------------------------ 对外

    def say(self, text: str, force: bool = False, urgent: bool = False, alert: bool = False) -> None:
        if not self.enabled or not text:
            return
        text = text.strip()
        if not text:
            return
        try:
            from .tts_text import speakable

            text = speakable(text)
        except Exception:  # noqa: BLE001 - 清洗失败就按原文朗读
            pass
        if not text:
            return
        now = time.monotonic()
        if not force and not urgent:
            if text == self._last_text:
                return
            if now - self._last_at < self.min_interval:
                return
        self._last_text = text
        self._last_at = now
        self._log(f"朗读: {text} (urgent={urgent}, alert={alert})")
        if self.beep:
            self._beep(urgent, alert)
        if self.speak:
            self._speak(text)

    def _speak(self, text: str) -> None:
        if self.backend_pref == "beep":
            return
        if self._voice is not None and not self._sapi_failed:
            if self._sapi_say(text):
                return
            self._sapi_failures += 1
            if self._sapi_failures >= 2:
                self._sapi_failed = True
        if self.backend_pref in ("auto", "edge") and self._edge_ok:
            self._edge_say(text)
            return
        if self.backend_pref == "sapi" and not self._ps_failed:
            self._powershell_say(text)
            return
        self._log(f"朗读失败：{self.last_error}")

    # ------------------------------------------------------------------ 在线朗读

    def _cache_dir(self) -> Path:
        base = self.log_path.parent if self.log_path is not None else Path.cwd() / "logs"
        return (base / "tts_cache").resolve()

    def _edge_say(self, text: str) -> None:
        if not self._edge_ok:
            return
        self._thread = threading.Thread(target=self._run_edge, args=(text,), daemon=True)
        self._thread.start()

    def _wait_for_quiet(self) -> float:
        if self.gate is None:
            return 0.0
        try:
            return float(self.gate.wait_quiet(self.wait_max))
        except Exception:  # noqa: BLE001
            return 0.0

    def _run_edge(self, text: str) -> None:
        self._wait_for_quiet()
        try:
            import asyncio
            import hashlib

            import edge_tts  # type: ignore[import-not-found]

            cache = self._cache_dir()
            cache.mkdir(parents=True, exist_ok=True)
            key = hashlib.sha1(f"{self.edge_voice}|{text}".encode("utf-8")).hexdigest()[:16]
            path = cache / f"{key}.mp3"
            if not path.exists():
                tmp = cache / f"{key}.part.mp3"
                asyncio.run(edge_tts.Communicate(text, self.edge_voice).save(str(tmp)))
                tmp.replace(path)
            seconds = max(2.0, path.stat().st_size * 8 / 48000 + 1.2)
            self._play_mp3(path, seconds)
        except Exception as exc:  # noqa: BLE001
            self.last_error = f"在线朗读失败: {exc}"
            self._log(self.last_error)

    def _play_mp3(self, path: Path, seconds: float) -> None:
        # 用 Shell 的 Media.Duration（100ns）读真实时长，避免长句被截断/短句空等
        script = (
            "$sh = New-Object -ComObject Shell.Application; "
            f"$item = $sh.Namespace('{path.parent}').ParseName('{path.name}'); "
            "$ticks = $item.ExtendedProperty('System.Media.Duration'); "
            f"$ms = if ($ticks) {{ [int]($ticks / 10000) }} else {{ {int(seconds * 1000)} }}; "
            "Add-Type -AssemblyName PresentationCore; "
            "$p = New-Object System.Windows.Media.MediaPlayer; "
            f"$p.Open([uri]'{path}'); $p.Play(); "
            "Start-Sleep -Milliseconds ($ms + 150); $p.Close()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=seconds * 2 + 30,
            creationflags=_CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        self.backend = "edge"
        self.last_error = ""
        self._log("在线朗读完成")

    def _sapi_say(self, text: str) -> bool:
        if self._voice is None:
            return False
        try:
            self._voice.Speak(text, 3)  # 1=异步, 2=打断上一句
            return True
        except Exception as exc:  # noqa: BLE001
            self.last_error = f"SAPI Speak 失败: {exc}"
            return False

    # ------------------------------------------------------------------ 回退

    def _ps_log_path(self) -> Path:
        base = self.log_path.parent if self.log_path is not None else Path.cwd() / "logs"
        return (base / "voice_ps.log").resolve()

    def _wav_path(self) -> Path:
        base = self.log_path.parent if self.log_path is not None else Path.cwd() / "logs"
        return (base / "tts.wav").resolve()

    def _powershell_say(self, text: str) -> bool:
        """换一个进程发声：SAPI → 合成 WAV 播放 → System.Speech，逐级回退。

        合成耗时，放后台线程，避免卡住 Qt 主线程。
        """
        try:
            quoted = text.replace("'", "''")
            log_path = str(self._ps_log_path()).replace("'", "''")
            wav_path = str(self._wav_path()).replace("'", "''")
            script = (
                "$ProgressPreference = 'SilentlyContinue'; "
                f"$log = '{log_path}'; "
                "function Note($m) { Add-Content -LiteralPath $log -Value $m -Encoding UTF8 }; "
                "try { "
                "$v = New-Object -ComObject SAPI.SpVoice; "
                f"$v.Rate = {self.rate}; $v.Volume = {self.volume}; "
                f"$v.Speak('{quoted}', 0); "
                "Note 'sapi-ok' "
                "} catch { "
                "Note ('sapi-fail: ' + $_.Exception.Message); "
                "try { "
                "$f = New-Object -ComObject SAPI.SpFileStream; "
                f"$f.Open('{wav_path}', 3, $false); "
                "$v2 = New-Object -ComObject SAPI.SpVoice; "
                "$v2.AudioOutputStream = $f; "
                f"$v2.Speak('{quoted}', 0); "
                "$f.Close(); "
                f"(New-Object Media.SoundPlayer '{wav_path}').PlaySync(); "
                "Note 'wav-ok' "
                "} catch { "
                "Note ('wav-fail: ' + $_.Exception.Message); "
                "try { "
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$s.Rate = {self.rate}; $s.Volume = {self.volume}; "
                f"$s.Speak('{quoted}'); "
                "Note 'system-speech-ok' "
                "} catch { Note ('system-speech-fail: ' + $_.Exception.Message) } "
                "} "
                "};"
            )
        except Exception as exc:  # noqa: BLE001
            self._ps_failed = True
            self.last_error = f"PowerShell 朗读失败: {exc}"
            return False
        self._thread = threading.Thread(target=self._run_powershell, args=(script,), daemon=True)
        self._thread.start()
        return True

    def wait(self, timeout: float = 8.0) -> None:
        """等回退朗读结束（自检命令用）。"""
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout)

    def _run_powershell(self, script: str) -> None:
        try:
            encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
            creationflags = _CREATE_NO_WINDOW if sys.platform == "win32" else 0
            process = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            process.wait(timeout=60)
            note = self._read_ps_log()
            if process.returncode != 0:
                self._ps_failures += 1
                self.last_error = f"PowerShell 朗读失败(退出码 {process.returncode}) {note}"
                if self._ps_failures >= 3:
                    self._ps_failed = True
            elif note:
                self._log(f"PowerShell 回退结果: {note}")
                if note.endswith("-ok"):
                    self.backend = "powershell"
                    self.last_error = ""
                else:
                    self.last_error = f"PowerShell 回退失败: {note}"
        except Exception as exc:  # noqa: BLE001
            self._ps_failures += 1
            self.last_error = f"PowerShell 朗读失败: {exc}"
            if self._ps_failures >= 3:
                self._ps_failed = True

    def _read_ps_log(self) -> str:
        try:
            path = self._ps_log_path()
            if not path.exists():
                return ""
            lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
            return lines[-1] if lines else ""
        except Exception:  # noqa: BLE001
            return ""

    def _beep(self, urgent: bool = False, alert: bool = False) -> None:
        path = self._sound(urgent, alert)
        if path is not None and play_sound(path):
            return
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:  # noqa: BLE001
            pass

    def _sound(self, urgent: bool, alert: bool = False) -> Path | None:
        key = "alert" if alert else ("urgent" if urgent else "normal")
        if not self._sounds:
            try:
                base = self.log_path.parent if self.log_path is not None else Path.cwd() / "logs"
                self._sounds = ensure_sounds(base / "sounds")
            except Exception:  # noqa: BLE001
                return None
        return self._sounds.get(key)

    def _log(self, line: str) -> None:
        if self.log_path is None:
            return
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
        except Exception:  # noqa: BLE001
            pass
