"""朗读文本清洗测试。"""

from __future__ import annotations

import unittest

from dota2coach.ui.tts_text import speakable


class TtsTextTest(unittest.TestCase):
    def test_symbols_become_commas(self) -> None:
        self.assertEqual(
            speakable("永恒之盘——对面控制多（帕吉、莱恩）"),
            "永恒之盘，对面控制多，帕吉、莱恩。",
        )

    def test_clock_and_kilo(self) -> None:
        self.assertEqual(speakable("7:00 智慧神龛：去拿经验"), "7 分 智慧神龛，去拿经验。")
        self.assertEqual(speakable("总经济 6.8k"), "总经济 6800。")
        self.assertEqual(speakable("0:30 水符刷新"), "30 秒 水符刷新。")
    def test_dedup_punctuation(self) -> None:
        self.assertEqual(speakable("先吃树，，别硬撑。"), "先吃树，别硬撑。")
        self.assertEqual(speakable(""), "")


if __name__ == "__main__":
    unittest.main()
