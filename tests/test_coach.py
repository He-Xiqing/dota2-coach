from __future__ import annotations

import unittest

from dota2coach.coach.roster import Roster, roster_from_matches
from dota2coach.coach.state import (
    PHASE_LANING,
    PHASE_LATE,
    PHASE_MID,
    phase_for,
)
from dota2coach.coach.timers import phase_tip, upcoming
from dota2coach.knowledge.builds import ItemInfo, suggest_items
from dota2coach.vision.heroes import HeroInfo, HeroMatch

BEAST = HeroInfo(38, "beastmaster", "npc_dota_hero_beastmaster", "兽王")
DROW = HeroInfo(6, "drow_ranger", "npc_dota_hero_drow_ranger", "卓尔游侠")
PUDGE = HeroInfo(14, "pudge", "npc_dota_hero_pudge", "帕吉")


def _match(hero: HeroInfo | None, score: float = 0.8) -> HeroMatch:
    return HeroMatch((0, 0, 40, 40), hero, score, 0.1)


class RosterTests(unittest.TestCase):
    def test_summary_and_known(self) -> None:
        roster = Roster((BEAST, DROW, None, None, None), (PUDGE, None, None, None, None))
        self.assertEqual(roster.known, 3)
        self.assertFalse(roster.complete)
        self.assertIn("兽王", roster.summary())
        self.assertIn("帕吉", roster.summary())

    def test_self_hero_is_locked_first(self) -> None:
        roster = roster_from_matches(
            [_match(DROW), _match(None)], [_match(PUDGE)], self_hero=BEAST
        )
        self.assertEqual(roster.allies[0], BEAST)

    def test_duplicate_hero_dropped(self) -> None:
        roster = roster_from_matches([_match(BEAST)], [_match(BEAST), _match(PUDGE)])
        self.assertEqual(roster.enemies[0], None)
        self.assertEqual(roster.enemies[1], PUDGE)

    def test_self_lock_replaces_wrong_row_zero(self) -> None:
        # 第 0 行识别成帕吉，但 GSI 说自己是兽王：以 GSI 为准，敌方帕吉保留
        roster = roster_from_matches([_match(PUDGE)], [_match(PUDGE)], self_hero=BEAST)
        self.assertEqual(roster.allies[0], BEAST)
        self.assertEqual(roster.enemies[0], PUDGE)


class PhaseTests(unittest.TestCase):
    def test_boundaries(self) -> None:
        self.assertEqual(phase_for(0), PHASE_LANING)
        self.assertEqual(phase_for(599), PHASE_LANING)
        self.assertEqual(phase_for(600), PHASE_MID)
        self.assertEqual(phase_for(1500), PHASE_LATE)
        self.assertEqual(phase_for(-1), "准备")


class TimerTests(unittest.TestCase):
    def test_bounty_reminder_is_disabled(self) -> None:
        for clock in (170.0, 225.0, 235.0):
            self.assertFalse(any("赏金符" in hint.text for hint in upcoming(clock, horizon=30.0)))

    def test_water_runes_only_at_two_and_four(self) -> None:
        hints = upcoming(105.0, horizon=20.0)
        self.assertTrue(any("水符" in hint.text for hint in hints))
        self.assertFalse(any("水符" in hint.text for hint in upcoming(300.0, horizon=30.0)))

    def test_power_rune_starts_at_six_minutes(self) -> None:
        self.assertFalse(any("神符：" in hint.text for hint in upcoming(240.0, horizon=100.0)))
        self.assertTrue(any("神符：" in hint.text for hint in upcoming(350.0, horizon=15.0)))

    def test_power_rune_stops_after_24_minutes(self) -> None:
        # 24:10 之后即使到了下一个刷新点（26:00）也不提醒
        self.assertFalse(any("神符：" in hint.text for hint in upcoming(24 * 60 + 10, horizon=30.0)))

    def test_lotus_every_three_minutes(self) -> None:
        hints = upcoming(170.0, horizon=15.0)
        self.assertTrue(any("莲花" in hint.text for hint in hints))

    def test_lotus_stops_after_12_minutes(self) -> None:
        self.assertFalse(any("莲花" in hint.text for hint in upcoming(12 * 60 + 1, horizon=180.0)))

    def test_wisdom_shrine_every_seven_minutes(self) -> None:
        self.assertTrue(any("智慧神龛" in hint.text for hint in upcoming(410.0, horizon=15.0)))
        self.assertFalse(any("智慧神龛" in hint.text for hint in upcoming(300.0, horizon=30.0)))

    def test_wisdom_stops_after_21_minutes(self) -> None:
        self.assertFalse(any("智慧神龛" in hint.text for hint in upcoming(21 * 60 + 1, horizon=420.0)))

    def test_nothing_far_away(self) -> None:
        self.assertEqual(upcoming(200.0, horizon=5.0), [])

    def test_phase_tip_at_start(self) -> None:
        self.assertIn("开局", phase_tip(5) or "")
        self.assertIsNone(phase_tip(120))


class BuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.by_id = {
            1: ItemInfo("item_blink", "Blink Dagger", True, 2250),
            2: ItemInfo("item_blade_of_alacrity", "Blade of Alacrity", False, 1000),
            3: ItemInfo("item_tango", "Tango", True, 90),
            4: ItemInfo("item_yasha", "Yasha", True, 2050),
        }
        self.popularity = {
            11: {"mid_game_items": {2: 500, 1: 300, 3: 200, 4: 100}}
        }

    def test_skips_components_consumables_and_owned(self) -> None:
        result = suggest_items(self.popularity, 11, {"item_blink"}, self.by_id, limit=3)
        self.assertEqual(result, ["item_yasha"])

    def test_unknown_hero(self) -> None:
        self.assertEqual(suggest_items(self.popularity, 999, set(), self.by_id), [])


if __name__ == "__main__":
    unittest.main()
