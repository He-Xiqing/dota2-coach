"""语音开关的纯逻辑测试：不初始化真实 SAPI，也不发声。"""

from __future__ import annotations

import shutil
import unittest
import uuid
import wave
from pathlib import Path

from dota2coach.ui.sounds import ensure_sounds
from dota2coach.ui.voice import Speaker

ROOT = Path(__file__).resolve().parents[1]


class SpeakerToggleTest(unittest.TestCase):
    def test_sound_only_skips_sapi(self) -> None:
        speaker = Speaker(enabled=True, speak=False, beep=False)
        self.assertTrue(speaker.enabled)
        self.assertFalse(speaker.speak)
        self.assertIsNone(speaker._voice)
        speaker.say("只响提示音")  # 不应抛异常

    def test_disabled_is_noop(self) -> None:
        speaker = Speaker(enabled=False, speak=True, beep=False)
        self.assertFalse(speaker.enabled)
        speaker.say("什么都不做")

    def test_min_interval_blocks_repeat(self) -> None:
        speaker = Speaker(enabled=True, speak=False, beep=False, min_interval=60.0)
        speaker.say("第一次")
        first = speaker._last_text
        speaker.say("第二次")
        self.assertEqual(speaker._last_text, first)  # 间隔内被忽略

    def test_backend_beep_never_touches_sapi(self) -> None:
        speaker = Speaker(enabled=True, speak=True, beep=False, backend="beep")
        self.assertIsNone(speaker._voice)
        self.assertEqual(speaker.backend, "none")
        speaker.say("只响音效")  # 不应抛异常

    def test_backend_edge_skips_sapi(self) -> None:
        speaker = Speaker(enabled=True, speak=True, beep=False, backend="edge")
        self.assertIsNone(speaker._voice)  # 明确走在线朗读时不应初始化 SAPI
        self.assertIn(speaker.backend, ("edge", "none"))  # 没装 edge-tts 时退化为 none


class ChimeGenerationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = ROOT / "tests" / "_tmp" / f"sounds-{uuid.uuid4().hex[:8]}"

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_alert_sound_is_distinct(self) -> None:
        from dota2coach.ui.voice import Speaker

        speaker = Speaker(enabled=True, speak=False, beep=True, log_path=self.dir / "voice.log")
        alert = speaker._sound(False, True)
        urgent = speaker._sound(True, False)
        self.assertIsNotNone(alert)
        self.assertIsNotNone(urgent)
        self.assertEqual(alert.name, "alert.wav")
        self.assertEqual(urgent.name, "chime_urgent.wav")

    def test_ensure_sounds_writes_valid_wav(self) -> None:
        paths = ensure_sounds(self.dir)
        self.assertEqual(set(paths), {"normal", "urgent", "alert"})
        for path in paths.values():
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 2000)
            with wave.open(str(path), "rb") as handle:
                self.assertEqual(handle.getnchannels(), 1)
                self.assertEqual(handle.getsampwidth(), 2)
                self.assertEqual(handle.getframerate(), 44100)
                seconds = handle.getnframes() / handle.getframerate()
                self.assertGreater(seconds, 0.15)
                self.assertLess(seconds, 1.5)

    def test_speaker_uses_generated_chime(self) -> None:
        speaker = Speaker(
            enabled=True,
            speak=False,
            beep=True,
            log_path=self.dir / "voice.log",
        )
        path = speaker._sound(urgent=False)
        self.assertIsNotNone(path)
        self.assertEqual(path.name, "chime.wav")
        urgent = speaker._sound(urgent=True)
        self.assertIsNotNone(urgent)
        self.assertEqual(urgent.name, "chime_urgent.wav")


if __name__ == "__main__":
    unittest.main()
