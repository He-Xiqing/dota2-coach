"""顶部色条定位的回归测试。"""

import unittest

import cv2
import numpy as np

from dota2coach.vision.heroes import detect_bar_strips


def make_bar(width=1920, height=1080, card_w=150, gap=20, group_gap=520):
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:] = (30, 30, 34)
    colors = [(40, 180, 60), (60, 60, 220), (200, 120, 40), (120, 60, 200), (40, 200, 200)]
    step = card_w + gap
    for index in range(10):
        position = index % 5
        if index < 5:
            x = 60 + position * step
        else:
            x = width - 60 - card_w - (4 - position) * step
        strip = colors[index % 5]
        cv2.rectangle(image, (x, 12), (x + card_w, 18), strip, -1)
        # 卡面（低饱和，模拟英雄立绘）
        cv2.rectangle(image, (x, 19), (x + card_w, 19 + int(card_w / 1.5)), (90, 80, 70), -1)
    return image


class BarStripTests(unittest.TestCase):
    def test_detects_ten_cards(self):
        image = make_bar()
        cells = detect_bar_strips(image)
        self.assertEqual(len(cells), 10)
        widths = {cell[2] for cell in cells}
        self.assertEqual(len(widths), 1)
        self.assertGreaterEqual(widths.pop(), 140)
        xs = [cell[0] for cell in cells]
        self.assertEqual(xs, sorted(xs))
        steps = [xs[i + 1] - xs[i] for i in range(4)]
        self.assertLessEqual(max(steps) - min(steps), 3)

    def test_scaled_down_still_ten(self):
        base = make_bar()
        for scale in (0.5, 0.75, 1.0):
            image = cv2.resize(base, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            cells = detect_bar_strips(image)
            self.assertEqual(len(cells), 10, f"scale={scale}")
            self.assertTrue(all(cell[3] > 0 for cell in cells))

    def test_no_strips_returns_empty(self):
        image = np.zeros((600, 800, 3), dtype=np.uint8)
        self.assertEqual(detect_bar_strips(image), [])


if __name__ == "__main__":
    unittest.main()
