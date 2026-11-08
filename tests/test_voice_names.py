"""在线音色名归一化测试（兼容旧配置里的中文显示名）。"""

from __future__ import annotations

import unittest

from dota2coach.ui.voices import (
    DEFAULT_EDGE,
    PACK_BY_ID,
    effective_pack,
    normalize_edge_voice,
)


class VoiceNameTest(unittest.TestCase):
    def test_display_names(self) -> None:
        self.assertEqual(normalize_edge_voice("晓伊"), "zh-CN-XiaoyiNeural")
        self.assertEqual(normalize_edge_voice("云健 · 激昂男声"), "zh-CN-YunjianNeural")
        self.assertEqual(normalize_edge_voice("云扬"), "zh-CN-YunyangNeural")

    def test_edge_ids_pass_through(self) -> None:
        self.assertEqual(
            normalize_edge_voice("zh-TW-HsiaoChenNeural"), "zh-TW-HsiaoChenNeural"
        )
        self.assertEqual(normalize_edge_voice("en-US-AriaNeural"), "en-US-AriaNeural")

    def test_unknown_falls_back(self) -> None:
        self.assertEqual(normalize_edge_voice("foo"), DEFAULT_EDGE)
        self.assertEqual(normalize_edge_voice(""), DEFAULT_EDGE)

    def test_pack_follows_language(self) -> None:
        from dota2coach.i18n import LANGUAGES

        for code in LANGUAGES:
            pack_id = effective_pack("xiaoxiao", code)
            self.assertEqual(PACK_BY_ID[pack_id].lang, code, f"{code} 用了别的语言的包")

    def test_custom_pack_is_kept(self) -> None:
        self.assertEqual(effective_pack("custom", "en"), "custom")
        self.assertEqual(effective_pack("custom", "zh-CN"), "custom")


if __name__ == "__main__":
    unittest.main()
