"""多语言与语音包映射。"""

from __future__ import annotations

import unittest

from dota2coach.i18n import LANGUAGES, normalize_language, tr
from dota2coach.ui import voices

KEYS = (
    "app_name",
    "tag",
    "guide",
    "build",
    "settings",
    "feedback",
    "help",
    "status",
    "gsi",
    "in_match",
    "identify",
    "current_match",
    "not_started",
    "recent",
    "start",
    "stop",
    "hide_card",
    "roster",
    "allies",
    "enemies",
    "threat",
    "idle_head",
    "idle_sub",
    "idle_1",
    "idle_2",
    "idle_3",
    "idle_4",
    "f8",
    "lang_tab",
    "lang_hint",
)


class I18nTest(unittest.TestCase):
    def test_all_languages_have_all_keys(self) -> None:
        self.assertEqual(len(LANGUAGES), 9)
        for code in LANGUAGES:
            for key in KEYS:
                text = tr(code, key)
                self.assertTrue(text and text != key, f"{code}:{key} 缺失")
            # 同一语言的不同键不应全相同（防止漏翻）
            values = {tr(code, key) for key in KEYS}
            self.assertGreater(len(values), 20)

    def test_fallback(self) -> None:
        self.assertEqual(normalize_language("xx"), "zh-CN")
        self.assertEqual(normalize_language("EN"), "en")
        self.assertEqual(tr("xx", "start"), tr("zh-CN", "start"))
        self.assertEqual(tr("en", "f8", key="F8"), "Press F8 to show / hide the coach card")

    def test_language_voice_packs(self) -> None:
        for code in LANGUAGES:
            pack_id = voices.pack_for_language(code)
            self.assertIn(pack_id, voices.PACK_BY_ID)
            packs = voices.packs_for_language(code)
            self.assertTrue(packs)
            self.assertEqual(packs[-1].id, "custom")
            for pack in packs:
                self.assertIn(pack.lang, ("zh-CN", "zh-TW", "en", "fr", "ru", "de", "pt", "es", "tr"))

    def test_resolve_switches_voice(self) -> None:
        edge, rate, volume = voices.resolve("ru", "zh-CN-XiaoxiaoNeural", 0, 100)
        self.assertEqual(edge, "ru-RU-SvetlanaNeural")
        self.assertEqual(rate, 0)
        self.assertEqual(volume, 100)
        self.assertEqual(
            voices.resolve("custom", "my-voice", 3, 80), ("my-voice", 3, 80)
        )

    def test_settings_strings_complete(self) -> None:
        from dota2coach.i18n_settings import SETTINGS_STRINGS

        base = set(SETTINGS_STRINGS["zh-CN"])
        self.assertGreater(len(base), 60)
        for code in LANGUAGES:
            extra = SETTINGS_STRINGS.get(code, {})
            missing = base - set(extra)
            self.assertFalse(missing, f"{code} 缺少设置文案：{sorted(missing)}")
            if code not in ("zh-CN", "zh-TW"):
                for key, text in extra.items():
                    self.assertNotRegex(
                        text, r"[\u4e00-\u9fff]", f"{code}:{key} 仍是中文"
                    )


    def test_ui_strings_complete(self) -> None:
        keys = ("summary_last", "show_card", "tray_show", "tray_quit", "recognizing")
        for code in LANGUAGES:
            for key in keys:
                text = tr(code, key)
                self.assertNotEqual(text, key, f"{code} 缺少 {key}")
                if code not in ("zh-CN", "zh-TW"):
                    self.assertNotRegex(text, r"[\u4e00-\u9fff]", f"{code}:{key}")


    def test_variety_strings_complete(self) -> None:
        keys = (
            "greet_1", "greet_2", "greet_3", "greet_4",
            "encourage_win_2", "encourage_win_3",
            "encourage_loss_2", "encourage_loss_3",
            "encourage_win_plain_2", "encourage_loss_plain_2",
        )
        from dota2coach.coach.texts import TEXTS

        for code in LANGUAGES:
            table = TEXTS.get(code) or {}
            for key in keys:
                text = table.get(key, "")
                self.assertTrue(text, f"{code} 缂哄皯 {key}")
                if code not in ("zh-CN", "zh-TW"):
                    self.assertNotRegex(text, r"[\u4e00-\u9fff]", f"{code}:{key}")

    def test_item_strings_complete(self) -> None:
        from dota2coach.coach.texts import TEXTS
        from dota2coach.coach.texts_items import ITEM_TEXTS

        keys = set(ITEM_TEXTS["zh-CN"])
        for code in LANGUAGES:
            table = TEXTS.get(code) or {}
            for key in keys:
                text = table.get(key, "")
                self.assertTrue(text, f"{code} 缺少 {key}")
                if code not in ("zh-CN", "zh-TW"):
                    self.assertNotRegex(text, r"[\u4e00-\u9fff]", f"{code}:{key}")

if __name__ == "__main__":
    unittest.main()
