"""游戏内出装说明页的九语言测试。"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from dota2coach.knowledge.ingame_guide import LANGUAGES, ensure_guide, guide_path, render


class IngameGuideTest(unittest.TestCase):
    def test_all_languages_render(self) -> None:
        for code in LANGUAGES:
            html = render(code)
            self.assertIn("<html", html)
            self.assertNotIn("__", html.replace("__LANG__", ""))
            self.assertIn("DOTA2 Coach", html)
            if code not in ("zh-CN", "zh-TW"):
                body = re.sub(r"<[^>]+>", "", html)
                self.assertNotRegex(body, r"[\u4e00-\u9fff]", code)

    def test_unknown_language_falls_back(self) -> None:
        html = render("xx-YY")
        self.assertIn("build order", html)

    def test_ensure_guide_writes_file(self) -> None:
        tmp = Path("tests/_tmp/ingame_guide")
        tmp.mkdir(parents=True, exist_ok=True)
        target = ensure_guide(tmp, "ru")
        self.assertEqual(target, guide_path(tmp, "ru"))
        self.assertTrue(target.exists())
        self.assertIn("порядком закупки", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
