"""从攻略文本归纳对线打法的测试（纯离线）。"""

from __future__ import annotations

import unittest

from dota2coach.coach.guides import GuideTip
from dota2coach.coach.lane_style import plan_from_guides


def tip(text: str, hero: str = "slark") -> GuideTip:
    return GuideTip(id=text[:6], hero=hero, lane="任意", phase="对线期", text=text)


class PlanFromGuidesTest(unittest.TestCase):
    def test_aggressive_text_wins(self) -> None:
        plan = plan_from_guides(
            "slark",
            [tip("1级就压线换血，别让他安稳补刀"), tip("抢二后继续压，压出经验区")],
        )
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan.style, "harass")
        self.assertIn("攻略", plan.label)
        self.assertTrue(plan.early)

    def test_farm_text_wins(self) -> None:
        plan = plan_from_guides(
            "anti_mage",
            [tip("专注补刀发育，对面压线就拉野控线", "anti_mage")],
        )
        assert plan is not None
        self.assertEqual(plan.style, "farm")

    def test_not_enough_evidence(self) -> None:
        self.assertIsNone(plan_from_guides("slark", [tip("随便说两句")]))

    def test_other_hero_tips_ignored(self) -> None:
        self.assertIsNone(plan_from_guides("slark", [tip("压线换血打爆他", "lina")]))


if __name__ == "__main__":
    unittest.main()
