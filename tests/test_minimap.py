import unittest

import cv2
import numpy as np

from dota2coach.vision.minimap import (
    MinimapDots,
    Point,
    StaticFilter,
    cluster_count,
    crop_minimap,
    detect_dots,
    nearest_distance,
)


class MinimapDetectTest(unittest.TestCase):
    def test_crop_uses_fraction(self) -> None:
        image = np.zeros((1000, 1000, 3), np.uint8)
        crop = crop_minimap(image, (0.5, 0.5, 1.0, 1.0))
        self.assertEqual(crop.shape[:2], (500, 500))

    def test_detects_enemy_and_ally_dots(self) -> None:
        image = np.zeros((400, 400, 3), np.uint8)
        cv2.circle(image, (100, 100), 7, (0, 0, 220), -1)  # 红（BGR）
        cv2.circle(image, (300, 300), 7, (0, 200, 0), -1)  # 绿
        cv2.circle(image, (200, 200), 2, (0, 0, 220), -1)  # 小点=兵
        dots = detect_dots(image)
        self.assertEqual(len(dots.enemies), 1)
        self.assertEqual(len(dots.allies), 1)
        self.assertGreaterEqual(dots.creeps, 1)

    def test_hero_icon_mode(self) -> None:
        image = np.zeros((400, 400, 3), np.uint8)
        for x, y in ((100, 100), (120, 110), (140, 95)):
            cv2.circle(image, (x, y), 6, (0, 0, 220), -1)
        dots = detect_dots(image)
        self.assertEqual(len(dots.enemies), 3)

    def test_hero_name_mode(self) -> None:
        # 名字模式：细长文字条（多段笔画），膨胀后应并成 3 团
        image = np.zeros((400, 400, 3), np.uint8)
        for x, y in ((100, 100), (125, 105), (150, 98)):
            for dx in (0, 6, 12):
                cv2.rectangle(image, (x + dx, y), (x + dx + 4, y + 3), (0, 0, 220), -1)
        dots = detect_dots(image)
        self.assertEqual(len(dots.enemies), 3)

    def test_hero_portrait_mode(self) -> None:
        image = np.zeros((400, 400, 3), np.uint8)
        for x, y in ((90, 90), (120, 110), (150, 100)):
            cv2.rectangle(image, (x, y), (x + 18, y + 18), (0, 0, 220), -1)
        dots = detect_dots(image)
        self.assertEqual(len(dots.enemies), 3)

    def test_empty_image(self) -> None:
        dots = detect_dots(np.zeros((10, 10, 3), np.uint8))
        self.assertEqual(dots, MinimapDots())


class StaticFilterTest(unittest.TestCase):
    def test_static_point_is_dropped(self) -> None:
        f = StaticFilter(cell=0.02, hold=12.0)
        tower = [Point(0.3, 0.4)]
        self.assertEqual(len(f.update(tower, 0.0)), 1)
        self.assertEqual(len(f.update(tower, 13.0)), 0)

    def test_moving_point_is_kept(self) -> None:
        f = StaticFilter(cell=0.02, hold=12.0)
        f.update([Point(0.3, 0.4)], 0.0)
        self.assertEqual(len(f.update([Point(0.5, 0.6)], 13.0)), 1)


class ClusterTest(unittest.TestCase):
    def test_cluster_count(self) -> None:
        points = [Point(0.1, 0.1), Point(0.12, 0.1), Point(0.5, 0.5)]
        self.assertEqual(cluster_count(points, 0.05), 2)
        self.assertEqual(cluster_count([], 0.05), 0)

    def test_nearest_distance(self) -> None:
        self.assertLess(nearest_distance([Point(0.1, 0.1)], Point(0.15, 0.1)), 0.06)
        self.assertEqual(nearest_distance([], Point(0.5, 0.5)), 9.0)


if __name__ == "__main__":
    unittest.main()
