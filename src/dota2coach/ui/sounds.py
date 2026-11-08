"""生成并播放柔和的提示音（不依赖系统提示音方案）。

原先用 `winsound.Beep(1568, ...)`，方波 + 高频，听起来刺耳。
这里用正弦波合成两段"叮咚"：普通提示两个音上行，紧急提示三个音上行，
带指数衰减包络，音量明显更低。首次运行时生成到 logs/sounds/。
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100
_HARMONIC = 0.22  # 加一点二次谐波，比纯正弦更"亮"，但不刺耳


def _samples(freq: float, seconds: float, amp: float) -> list[float]:
    total = int(SAMPLE_RATE * seconds)
    out: list[float] = []
    for index in range(total):
        t = index / SAMPLE_RATE
        attack = min(1.0, t / 0.008)
        release = min(1.0, max(0.0, (seconds - t) / 0.05))
        envelope = attack * release * math.exp(-3.2 * t)
        value = math.sin(2 * math.pi * freq * t) + _HARMONIC * math.sin(4 * math.pi * freq * t)
        out.append(amp * envelope * value)
    return out


def _write(path: Path, notes: list[tuple[float, float, float]]) -> None:
    frames: list[float] = []
    gap = [0.0] * int(SAMPLE_RATE * 0.02)
    for freq, seconds, amp in notes:
        frames.extend(_samples(freq, seconds, amp))
        frames.extend(gap)
    data = b"".join(
        struct.pack("<h", int(max(-1.0, min(1.0, value)) * 32767)) for value in frames
    )
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(data)


def ensure_sounds(directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    normal = directory / "chime.wav"
    urgent = directory / "chime_urgent.wav"
    alert = directory / "alert.wav"
    if not normal.exists():
        _write(normal, [(659.25, 0.11, 0.20), (880.00, 0.28, 0.18)])
    if not urgent.exists():
        _write(urgent, [(523.25, 0.10, 0.20), (659.25, 0.10, 0.20), (783.99, 0.30, 0.18)])
    if not alert.exists():
        # 团战用：三声急促高音，比普通/紧急提示更抓耳
        _write(alert, [(1567.98, 0.09, 0.26), (1567.98, 0.09, 0.26), (1567.98, 0.14, 0.26)])
    return {"normal": normal, "urgent": urgent, "alert": alert}


def play(path: Path) -> bool:
    try:
        import winsound

        winsound.PlaySound(
            str(path),
            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
        )
        return True
    except Exception:  # noqa: BLE001
        return False
