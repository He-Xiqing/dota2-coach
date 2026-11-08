import unittest

from dota2coach.coach.gameaudio import GameAudioGate
from dota2coach.ui import voices


class VoicePackTest(unittest.TestCase):
    def test_pack_ids_unique(self) -> None:
        ids = [pack.id for pack in voices.PACKS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_preset_overrides_voice_and_rate(self) -> None:
        edge, rate, volume = voices.resolve("yunjian", "zh-CN-XiaoxiaoNeural", 0, 100)
        self.assertEqual(edge, "zh-CN-YunjianNeural")
        self.assertEqual(rate, 2)

    def test_custom_keeps_user_values(self) -> None:
        self.assertEqual(voices.resolve("custom", "zh-CN-YunxiNeural", 3, 55), ("zh-CN-YunxiNeural", 3, 55))

    def test_unknown_pack_falls_back(self) -> None:
        self.assertEqual(voices.resolve("nope", "zh-CN-YunxiNeural", 1, 80), ("zh-CN-YunxiNeural", 1, 80))


class GameAudioGateTest(unittest.TestCase):
    def _gate(self) -> GameAudioGate:
        gate = GameAudioGate.__new__(GameAudioGate)
        gate.threshold = 0.01
        gate.music_after = 8.0
        gate._continuous_start = None
        gate._ignored = False
        return gate

    def test_silence_is_not_busy(self) -> None:
        gate = self._gate()
        gate.peak = lambda: 0.0  # type: ignore[method-assign]
        self.assertFalse(gate.busy())

    def test_loud_is_busy(self) -> None:
        gate = self._gate()
        gate.peak = lambda: 0.5  # type: ignore[method-assign]
        self.assertTrue(gate.busy())

    def test_long_continuous_audio_is_treated_as_music(self) -> None:
        import time

        gate = self._gate()
        gate.peak = lambda: 0.5  # type: ignore[method-assign]
        gate._continuous_start = time.monotonic() - 9.0
        self.assertFalse(gate.busy())

    def test_quiet_resets_state(self) -> None:
        import time

        gate = self._gate()
        gate._continuous_start = time.monotonic() - 9.0
        gate._ignored = True
        gate.peak = lambda: 0.0  # type: ignore[method-assign]
        self.assertFalse(gate.busy())
        self.assertIsNone(gate._continuous_start)
        self.assertFalse(gate._ignored)


if __name__ == "__main__":
    unittest.main()
