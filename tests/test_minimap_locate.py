"""小地图自动定位与配置测试。"""

from __future__ import annotations

import numpy as np
import unittest
from pathlib import Path

from dota2coach.config import load_config, validate_config
from dota2coach.vision.minimap import MinimapRect, detect_dots, locate_minimap


def _canvas(width=800, height=600, side="right"):
    img = np.zeros((height, width, 3), np.uint8)
    size = 132
    margin = 6
    left = width - margin - size if side == "right" else margin
    top = height - margin - size
    img[top : top + size, left : left + size] = (40, 40, 45)
    img[top + 30 : top + 42, left + 20 : left + 32] = (40, 40, 200)  # 敌方红点
    img[top + 70 : top + 82, left + 80 : left + 92] = (60, 180, 60)  # 友方绿点
    return img


class LocateTest(unittest.TestCase):
    def test_locates_right(self) -> None:
        rect = locate_minimap([_canvas(side="right")])
        self.assertIsNotNone(rect)
        self.assertGreater(rect.left, 400)
        self.assertAlmostEqual(rect.width / rect.height, 1.0, delta=0.15)

    def test_locates_left(self) -> None:
        rect = locate_minimap([_canvas(side="left")])
        self.assertIsNotNone(rect)
        self.assertLess(rect.left, 200)

    def test_scale_aware_threshold(self) -> None:
        crop = np.zeros((200, 200, 3), np.uint8)
        crop[90:110, 90:110] = (30, 30, 190)
        full = detect_dots(crop, scale=1.0)
        half = detect_dots(crop, scale=0.5)
        self.assertGreaterEqual(len(full.enemies), 1)
        self.assertGreaterEqual(len(half.enemies), 1)

    def test_config_validation(self) -> None:
        cfg = load_config()
        cfg.minimap.size_percent = 10
        cfg.minimap.side = "middle"
        cfg.minimap.offset_x = 999
        problems = validate_config(cfg)
        self.assertTrue(any("小地图" in item for item in problems))
        self.assertGreaterEqual(len(problems), 2)


if __name__ == "__main__":
    unittest.main()
