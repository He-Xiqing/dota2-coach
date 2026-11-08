"""界面按钮用到的链接。"""

from __future__ import annotations

import unittest
from pathlib import Path

from dota2coach.ui.links import (
    INGAME_GUIDE_FILE,
    OFFICIAL_HEROES_URL,
    ingame_guide_path,
    official_guide_url,
)

ROOT = Path(__file__).resolve().parents[1]


class LinksTest(unittest.TestCase):
    def test_official_guide_url(self) -> None:
        self.assertEqual(official_guide_url(None), OFFICIAL_HEROES_URL)
        self.assertEqual(official_guide_url(""), OFFICIAL_HEROES_URL)
        self.assertEqual(official_guide_url("slark"), "https://www.dota2.com/hero/slark")
        self.assertEqual(
            official_guide_url("crystal_maiden"),
            "https://www.dota2.com/hero/crystal_maiden",
        )

    def test_official_guide_url_rejects_odd_input(self) -> None:
        self.assertEqual(official_guide_url("a b"), OFFICIAL_HEROES_URL)
        self.assertEqual(official_guide_url("../../x"), OFFICIAL_HEROES_URL)

    def test_ingame_guide_exists(self) -> None:
        path = ingame_guide_path(ROOT / "data")
        self.assertTrue(path.name.endswith(INGAME_GUIDE_FILE))
        self.assertTrue(path.exists(), "data/ingame_guide.html 应随仓库分发")


if __name__ == "__main__":
    unittest.main()
