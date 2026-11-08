"""在线朗读自检：用 edge-tts 合成 MP3，再用 Windows 媒体播放器播放。

需要先安装（只装一次）：
    .venv\\Scripts\\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

然后运行：
    .venv\\Scripts\\python.exe tools\\voice_edge_test.py
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
TEXT = "语音测试：听到这句话，说明在线朗读可以用"
VOICE = "zh-CN-XiaoxiaoNeural"


def play(path: Path, seconds: float) -> None:
    script = (
        "Add-Type -AssemblyName PresentationCore; "
        f"$p = New-Object System.Windows.Media.MediaPlayer; "
        f"$p.Open([uri]'{path}'); $p.Play(); "
        f"Start-Sleep -Milliseconds {int(seconds * 1000)}; $p.Close()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        timeout=60,
        creationflags=0x08000000,
    )


def main() -> int:
    try:
        import edge_tts  # type: ignore[import-not-found]
    except ImportError:
        print("缺少 edge-tts，请先运行：")
        print(r"  .venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple")
        return 2

    LOGS.mkdir(parents=True, exist_ok=True)
    out = LOGS / "tts_test.mp3"
    print(f"正在合成：{TEXT}")
    try:
        asyncio.run(edge_tts.Communicate(TEXT, VOICE).save(str(out)))
    except Exception as exc:  # noqa: BLE001
        print(f"合成失败（可能需要联网）：{exc}")
        return 1
    size = out.stat().st_size
    print(f"已生成 {out}（{size} 字节），开始播放…")
    seconds = max(2.0, size * 8 / 48000 + 1.5)
    try:
        play(out, seconds)
    except Exception as exc:  # noqa: BLE001
        print(f"播放失败：{exc}")
        return 1
    print("播放结束。如果听到了“语音测试…”，把上面几行发我，我就把它接进游戏卡片。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
