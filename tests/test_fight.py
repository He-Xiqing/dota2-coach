import unittest

from dota2coach.coach.fight import FightTracker, fight_targets, player_plan
from dota2coach.coach.roster import Roster
from dota2coach.vision.heroes import HeroInfo
from dota2coach.vision.minimap import MinimapDots, Point


def hero(hero_id: int, short: str, name_loc: str) -> HeroInfo:
    return HeroInfo(hero_id=hero_id, short=short, name=f"npc_dota_hero_{short}", name_loc=name_loc)


class PlayerPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        from dota2coach.knowledge.meta import HeroMeta

        self.meta = {
            10: HeroMeta(10, "axe", ("Durable", "Initiator", "Disabler"), 0.5, 0.5, 0.5, 0),
            11: HeroMeta(11, "lion", ("Support", "Disabler", "Nuker"), 0.5, 0.5, 0.5, 0),
            12: HeroMeta(12, "crystal_maiden", ("Support", "Nuker", "Disabler"), 0.5, 0.5, 0.5, 0),
            13: HeroMeta(13, "templar_assassin", ("Carry", "Escape", "Nuker"), 0.5, 0.5, 0.5, 0),
            14: HeroMeta(14, "chen", ("Support", "Pusher"), 0.5, 0.5, 0.5, 0),
            15: HeroMeta(15, "juggernaut", ("Carry", "Escape"), 0.5, 0.5, 0.5, 0),
        }
        self.roster = Roster(
            allies=(hero(15, "juggernaut", "主宰"),),
            enemies=(hero(11, "lion", "莱恩"), hero(12, "crystal_maiden", "水晶室女"), hero(10, "axe", "斧王")),
        )

    def test_tank_takes_damage(self) -> None:
        plan = player_plan(hero(10, "axe", "斧王"), self.meta, self.roster)
        self.assertTrue(any("吃第一波伤害" in line for line in plan))

    def test_controller_locks_target(self) -> None:
        plan = player_plan(hero(11, "lion", "莱恩"), self.meta, self.roster)
        self.assertTrue(any("盯住" in line for line in plan))

    def test_mage_nukes_and_protects(self) -> None:
        plan = player_plan(hero(12, "crystal_maiden", "水晶室女"), self.meta, self.roster)
        text = " ".join(plan)
        self.assertIn("甩给", text)

    def test_assassin_dives(self) -> None:
        plan = player_plan(hero(13, "templar_assassin", "圣堂刺客"), self.meta, self.roster)
        self.assertTrue(any("绕后切" in line for line in plan))

    def test_support_protects_core(self) -> None:
        plan = player_plan(hero(14, "chen", "陈"), self.meta, self.roster)
        self.assertTrue(any("保" in line for line in plan))


class FightTrackerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.roster = Roster(
            allies=(hero(1, "antimage", "敌法师"),),
            enemies=(
                hero(2, "lion", "莱恩"),
                hero(3, "axe", "斧王"),
                hero(4, "crystal_maiden", "水晶室女"),
            ),
        )

    def test_silent_before_twenty_minutes(self) -> None:
        tracker = FightTracker()
        hints = tracker.update(
            clock=600,
            dots=MinimapDots(enemies=[Point(0.5, 0.5)], allies=[]),
            roster=self.roster,
        )
        self.assertEqual(hints, [])

    def test_enemies_missing_warns(self) -> None:
        tracker = FightTracker()
        tracker.update(clock=1200, dots=MinimapDots(enemies=[Point(0.2, 0.2), Point(0.3, 0.3)]), roster=self.roster)
        tracker.update(clock=1203, dots=MinimapDots(enemies=[]), roster=self.roster)
        hints = tracker.update(clock=1206, dots=MinimapDots(enemies=[]), roster=self.roster)
        self.assertTrue(any("红点全没了" in h.text for h in hints))

    def test_fight_gives_targets(self) -> None:
        tracker = FightTracker()
        dots = MinimapDots(
            enemies=[Point(0.5, 0.5), Point(0.52, 0.5), Point(0.5, 0.53)],
            allies=[Point(0.55, 0.5), Point(0.56, 0.52)],
        )
        hints = tracker.update(clock=1300, dots=dots, roster=self.roster)
        text = " ".join(h.text for h in hints)
        self.assertIn("团战", text)
        self.assertIn("先打", text)

    def test_carry_gets_farm_route(self) -> None:
        tracker = FightTracker()
        hints = tracker.update(
            clock=1300,
            dots=MinimapDots(),
            roster=self.roster,
            roles={"Carry", "Nuker"},
            side="radiant",
        )
        self.assertTrue(any("刷钱路线" in h.text for h in hints))

    def test_support_gets_ward(self) -> None:
        tracker = FightTracker()
        hints = tracker.update(
            clock=1300,
            dots=MinimapDots(),
            roster=self.roster,
            roles={"Support"},
            side="dire",
        )
        self.assertTrue(any("眼位" in h.text for h in hints))

    def test_fight_targets_roles(self) -> None:
        focus, avoid, watch = fight_targets(self.roster)
        self.assertIn("莱恩", focus)  # 没 meta 时按静态表
        self.assertIn("斧王", avoid)
        self.assertTrue(watch)


if __name__ == "__main__":
    unittest.main()
