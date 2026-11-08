"""对线期补给建议的规则测试。"""

from __future__ import annotations

import unittest

from dota2coach.coach.lane_items import lane_items
from dota2coach.knowledge.meta import HeroMeta
from dota2coach.vision.heroes import HeroInfo


def hero(hero_id: int, short: str, name: str) -> HeroInfo:
    return HeroInfo(hero_id=hero_id, short=short, name=f"npc_dota_hero_{short}", name_loc=name)


class LaneItemsTest(unittest.TestCase):
    def test_stealth_first(self) -> None:
        enemies = [hero(1, "bounty_hunter", "赏金猎人"), hero(2, "zuus", "宙斯")]
        picks = lane_items(enemies)
        self.assertEqual(picks[0][0], "粉")

    def test_nukers_get_magic_stick(self) -> None:
        meta = {
            1: HeroMeta(1, "zuus", ("Nuker",), 0.5, 0.5, 0.5, 0),
            2: HeroMeta(2, "lina", ("Nuker",), 0.5, 0.5, 0.5, 0),
        }
        picks = lane_items([hero(1, "zuus", "宙斯"), hero(2, "lina", "莉娜")], meta)
        self.assertIn("魔棒", [item for item, _ in picks])

    def test_empty_enemies(self) -> None:
        self.assertEqual(lane_items(()), [])


if __name__ == "__main__":
    unittest.main()
