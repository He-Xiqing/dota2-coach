from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from dota2coach.vision.heroes import (
    HeroInfo,
    HeroMatcher,
    composite_on_dark,
    imwrite_path,
    load_hero_table,
    _fit_grid,
)

ROOT = Path(__file__).resolve().parents[1]


class LoadHeroTableTests(unittest.TestCase):
    def test_missing_file_returns_empty(self) -> None:
        self.assertEqual(load_hero_table(ROOT / "tests" / "_tmp" / "nope.json"), {})

    def test_reads_bom_and_int_keys(self) -> None:
        path = ROOT / "tests" / "_tmp" / f"heroes-{uuid4().hex[:8]}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"38": {"short": "beastmaster", "name_loc": "兽王"}}
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8-sig")
        try:
            table = load_hero_table(path)
            self.assertEqual(table[38].short, "beastmaster")
            self.assertEqual(table[38].name_loc, "兽王")
        finally:
            path.unlink(missing_ok=True)


class FitGridTests(unittest.TestCase):
    def test_partial_rows_use_prior_to_pick_start(self) -> None:
        # 实测：4 行被检出（面板区域坐标），真值是第 0 行在 95
        grid = _fit_grid([178.0, 261.0, 344.0, 428.0], 5, prior_start=116.7)
        assert grid is not None
        self.assertLess(abs(grid[0] - 95.0), 3.0)
        self.assertEqual(len(grid), 5)

    def test_too_few_rows_returns_none(self) -> None:
        self.assertIsNone(_fit_grid([100.0], 5))


class CompositeTests(unittest.TestCase):
    def test_transparent_pixels_become_background(self) -> None:
        image = np.zeros((4, 4, 4), dtype=np.uint8)
        image[:, :, :3] = 255  # 白色，但 alpha=0
        out = composite_on_dark(image, (40, 40, 44))
        self.assertEqual(out.shape, (4, 4, 3))
        self.assertTrue(np.all(out == np.array([40, 40, 44], dtype=np.uint8)))

    def test_opaque_pixels_are_kept(self) -> None:
        image = np.zeros((2, 2, 4), dtype=np.uint8)
        image[:, :, 0] = 200
        image[:, :, 3] = 255
        out = composite_on_dark(image)
        self.assertTrue(np.all(out[:, :, 0] == 200))


class MatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = ROOT / "tests" / "_tmp" / f"matcher-{uuid4().hex[:8]}"
        (self.dir / "icons").mkdir(parents=True, exist_ok=True)
        # 纯色块做 NCC 会退化（两者分数都是 1.0），用条纹图案区分
        red = np.zeros((32, 32, 3), dtype=np.uint8)
        red[:, ::2, 2] = 220
        blue = np.zeros((32, 32, 3), dtype=np.uint8)
        blue[::2, :, 0] = 220
        imwrite_path(self.dir / "icons" / "axe.png", red)
        imwrite_path(self.dir / "icons" / "lina.png", blue)
        self.heroes = {
            2: HeroInfo(2, "axe", "npc_dota_hero_axe", "斧王"),
            25: HeroInfo(25, "lina", "npc_dota_hero_lina", "莉娜"),
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_ranks_matching_icon_first(self) -> None:
        matcher = HeroMatcher(self.heroes, self.dir / "icons")
        self.assertTrue(matcher.ready)
        cell = np.zeros((41, 41, 3), dtype=np.uint8)
        cell[:, ::2, 2] = 210  # 竖条纹，应匹配 axe
        ranked = matcher.rank(cell, "icon")
        self.assertEqual(ranked[0][0].short, "axe")
        self.assertGreater(ranked[0][1], ranked[1][1])

    def test_identify_respects_thresholds(self) -> None:
        matcher = HeroMatcher(self.heroes, self.dir / "icons")
        image = np.zeros((60, 60, 3), dtype=np.uint8)  # 全黑：两个模板都该低分
        match = matcher.identify(image, (0, 0, 41, 41), "icon", min_score=0.55)
        self.assertIsNone(match.hero)

    def test_no_templates_means_not_ready(self) -> None:
        matcher = HeroMatcher(self.heroes, self.dir / "missing")
        self.assertFalse(matcher.ready)


if __name__ == "__main__":
    unittest.main()
