from __future__ import annotations

import unittest

from dota2coach.coach.texts import set_language

from dota2coach.coach.summary import (
    MatchSummary,
    encourage,
    improvements,
    summarize,
    summary_lines,
)
from dota2coach.gsi.models import Snapshot


def _snapshot(**player) -> Snapshot:
    base = {
        "kills": 4,
        "deaths": 1,
        "assists": 5,
        "last_hits": 88,
        "denies": 6,
        "gold": 812,
        "gpm": 420,
        "team_name": "radiant",
    }
    base.update(player)
    return Snapshot(
        {
            "map": {"game_state": "DOTA_GAMERULES_STATE_POST_GAME", "game_time": 1800, "win_team": "radiant"},
            "hero": {"id": 11, "name": "npc_dota_hero_nevermore"},
            "player": base,
        }
    )


class SummarizeTests(unittest.TestCase):
    def test_extracts_stats_and_win(self) -> None:
        summary = summarize(_snapshot(), "影魔")
        assert summary is not None
        self.assertEqual(summary.hero, "影魔")
        self.assertEqual(summary.kda, "4/1/5")
        self.assertEqual(summary.duration, 1800)
        self.assertTrue(summary.win)

    def test_missing_hero_returns_none(self) -> None:
        raw = {"map": {"game_time": 1800}, "hero": {"id": 0}, "player": {}}
        self.assertIsNone(summarize(Snapshot(raw), "?"))

    def test_loss_detected(self) -> None:
        summary = summarize(_snapshot(team_name="dire"), "影魔")
        assert summary is not None
        self.assertFalse(summary.win)
        self.assertEqual(summary.result, "失败")

    def test_roles_mark_support(self) -> None:
        summary = summarize(_snapshot(), "水晶室女", roles=("Support", "Disabler"))
        assert summary is not None
        self.assertTrue(summary.is_support)
        core = summarize(_snapshot(), "影魔", roles=("Carry", "Nuker"))
        assert core is not None
        self.assertFalse(core.is_support)


class AdviceTests(unittest.TestCase):
    def setUp(self) -> None:
        set_language("zh-CN")
    def test_many_deaths_flagged(self) -> None:
        summary = MatchSummary("影魔", 3, 10, 4, 80, 4, 500, 300, 1800, False)
        tips = improvements(summary)
        self.assertTrue(any("死亡偏多" in tip for tip in tips))

    def test_low_farm_and_gpm_flagged(self) -> None:
        summary = MatchSummary("影魔", 2, 1, 2, 20, 1, 300, 250, 1800, False)
        tips = improvements(summary)
        self.assertTrue(any("补刀偏少" in tip for tip in tips))
        self.assertTrue(any("打钱效率" in tip for tip in tips))

    def test_support_skips_farm_tips(self) -> None:
        summary = MatchSummary(
            "水晶室女", 2, 1, 12, 20, 1, 300, 250, 1800, False, True
        )
        tips = improvements(summary)
        self.assertFalse(any("补刀偏少" in tip for tip in tips))
        self.assertFalse(any("打钱效率" in tip for tip in tips))

    def test_support_deaths_still_flagged(self) -> None:
        summary = MatchSummary(
            "水晶室女", 2, 12, 12, 20, 1, 300, 250, 1800, False, True
        )
        tips = improvements(summary)
        self.assertTrue(any("死亡偏多" in tip for tip in tips))

    def test_good_game_praises(self) -> None:
        summary = MatchSummary("影魔", 12, 1, 9, 240, 20, 2000, 700, 1800, True)
        tips = improvements(summary)
        self.assertTrue(any("稳" in tip for tip in tips))
        variants = {
            "这局打得不错，保持手感，继续上分！",
            "赢得很稳，保持这个节奏",
            "漂亮，把赢的感觉记住，下一把继续",
        }
        self.assertIn(encourage(summary), variants)

    def test_summary_lines_contain_result(self) -> None:
        summary = MatchSummary("影魔", 4, 1, 5, 88, 6, 812, 420, 1800, True)
        lines = summary_lines(summary)
        self.assertTrue(any("胜利" in line for line in lines))
        self.assertTrue(any("4/1/5" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
