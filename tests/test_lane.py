"""对线教练规则测试（纯离线，不依赖 Qt / 游戏）。"""

from __future__ import annotations

import unittest

from dota2coach.coach.lane import lane_tips
from dota2coach.knowledge.meta import HeroMeta
from dota2coach.vision.heroes import HeroInfo


def hero(hero_id: int, short: str, name_loc: str) -> HeroInfo:
    return HeroInfo(hero_id, short, f"npc_dota_hero_{short}", name_loc)


PUDGE = hero(14, "pudge", "帕吉")
LION = hero(26, "lion", "莱恩")
LINA = hero(31, "lina", "火女")
ZEUS = hero(22, "zuus", "宙斯")
BOUNTY = hero(62, "bounty_hunter", "赏金猎人")
SNIPER = hero(35, "sniper", "狙击手")


def meta_for(*pairs: tuple[HeroInfo, list[str]]) -> dict[int, HeroMeta]:
    out: dict[int, HeroMeta] = {}
    for info, roles in pairs:
        out[info.hero_id] = HeroMeta(
            hero_id=info.hero_id,
            name=info.short,
            roles=tuple(roles),
            pub_winrate=0.5,
            high_winrate=0.5,
            pro_winrate=0.5,
            pro_picks=0,
        )
    return out


class LaneTipsTest(unittest.TestCase):
    def test_no_tips_outside_laning(self) -> None:
        self.assertEqual(lane_tips(lane="你在中路", clock=601, enemies=[PUDGE]), [])
        self.assertEqual(lane_tips(lane="你在中路", clock=-1, enemies=[PUDGE]), [])

    def test_start_tip_uses_lane_plan(self) -> None:
        tips = lane_tips(lane="你在下路", clock=45)
        self.assertEqual(tips[0].key, "lane:plan:early")
        self.assertTrue(tips[0].text)

    def test_hero_specific_plan_overrides_generic_farm(self) -> None:
        slark = hero(93, "slark", "斯拉克")
        tips = lane_tips(lane="你在下路", clock=45, self_hero=slark)
        text = next(tip.text for tip in tips if tip.key == "lane:plan:early")
        self.assertIn("1 级", text)

    def test_lineup_threat_tips_are_disabled(self) -> None:
        # “先手多/推线强/爆发高”与是否同路无关，已全部关闭
        meta = meta_for((PUDGE, ["Disabler"]), (LION, ["Disabler"]), (LINA, ["Nuker"]), (ZEUS, ["Nuker"]))
        tips = lane_tips(lane="你在中路", clock=120, enemies=[PUDGE, LION, LINA, ZEUS], meta=meta)
        keys = {tip.key for tip in tips}
        self.assertNotIn("lane:threat:cc", keys)
        self.assertNotIn("lane:threat:push", keys)
        self.assertNotIn("lane:threat:burst", keys)

    def test_threat_tip_falls_back_without_meta(self) -> None:
        tips = lane_tips(lane="你在中路", clock=120, enemies=[LION, PUDGE, ZEUS, LINA])
        keys = {tip.key for tip in tips}
        self.assertNotIn("lane:threat:cc", keys)
        self.assertNotIn("lane:threat:burst", keys)

    def test_stealth_tip(self) -> None:
        tips = lane_tips(lane="你在下路", clock=90, enemies=[BOUNTY, SNIPER])
        self.assertIn("lane:threat:stealth", {tip.key for tip in tips})

    def test_ward_tip_around_four_minutes(self) -> None:
        self.assertIn("lane:ward", {tip.key for tip in lane_tips(lane="你在上路", clock=245)})
        self.assertNotIn("lane:ward", {tip.key for tip in lane_tips(lane="你在上路", clock=301)})

    def test_night_tip_at_five_minutes(self) -> None:
        self.assertIn("lane:night", {tip.key for tip in lane_tips(lane="你在上路", clock=305)})

    def test_low_health_is_urgent_and_repeats_per_minute(self) -> None:
        first = lane_tips(lane="你在中路", clock=200, health_percent=0.2)
        second = lane_tips(lane="你在中路", clock=260, health_percent=0.2)
        self.assertTrue(first[0].urgent)
        self.assertNotEqual(first[0].key, second[0].key)
        self.assertTrue(first[0].key.startswith("lane:hp:"))

    def test_low_mana_tip(self) -> None:
        tips = lane_tips(lane="你在中路", clock=200, health_percent=0.8, mana_percent=0.1)
        self.assertEqual(tips[0].key, "lane:mana:3")

    def test_last_hits_and_level_tips(self) -> None:
        tips = lane_tips(lane="你在中路", clock=240, last_hits=8, level=6, limit=4)
        keys = {tip.key for tip in tips}
        self.assertIn("lane:cs", keys)
        self.assertIn("lane:six", keys)

    def test_limit_respected(self) -> None:
        tips = lane_tips(
            lane="你在中路",
            clock=245,
            enemies=[PUDGE, LION],
            health_percent=0.2,
            limit=2,
        )
        self.assertLessEqual(len(tips), 2)

    def test_five_distinct_tips_in_first_ten_minutes(self) -> None:
        meta = meta_for((PUDGE, ["Disabler"]), (LION, ["Disabler"]), (LINA, ["Nuker"]))
        enemies = [PUDGE, LION, LINA, BOUNTY, SNIPER]
        seen: set[str] = set()
        for clock in range(0, 600, 5):
            tips = lane_tips(
                lane="你在中路",
                clock=float(clock),
                enemies=enemies,
                meta=meta,
                health_percent=0.5,
                mana_percent=0.5,
                last_hits=10,
                level=6,
                limit=3,
            )
            seen.update(tip.key for tip in tips)
        self.assertGreaterEqual(len(seen), 5, seen)


if __name__ == "__main__":
    unittest.main()
