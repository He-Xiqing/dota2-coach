from __future__ import annotations

import unittest

from dota2coach.coach.items_advice import recommend
from dota2coach.knowledge.builds import ItemInfo
from dota2coach.knowledge.meta import HeroMeta
from dota2coach.vision.heroes import HeroInfo

BEAST = HeroInfo(38, "beastmaster", "npc_dota_hero_beastmaster", "兽王")
SILENCER = HeroInfo(75, "silencer", "npc_dota_hero_silencer", "沉默术士")
DP = HeroInfo(43, "death_prophet", "npc_dota_hero_death_prophet", "死亡先知")
LION = HeroInfo(26, "lion", "npc_dota_hero_lion", "莱恩")

ITEMS = {
    1: ItemInfo("item_manta", "Manta Style", True, 4750),
    2: ItemInfo("item_black_king_bar", "Black King Bar", True, 4050),
    3: ItemInfo("item_pipe", "Pipe of Insight", True, 3475),
    4: ItemInfo("item_power_treads", "Power Treads", True, 1400),
}
NAMES = {
    "item_manta": "幻影斧",
    "item_black_king_bar": "黑皇杖",
    "item_pipe": "洞察烟斗",
    "item_power_treads": "动力鞋",
}
POPULARITY = {38: {"mid_game_items": {1: 900, 2: 500, 3: 200, 4: 100}, "late_game_items": {}}}


class RecommendTests(unittest.TestCase):
    def test_silence_picks_manta_with_reason(self) -> None:
        result = recommend(
            hero=BEAST,
            enemies=[SILENCER, None, None, None, None],
            popularity=POPULARITY,
            by_id=ITEMS,
            item_names=NAMES,
        )
        self.assertTrue(result)
        self.assertEqual(result[0].name, "item_manta")
        self.assertIn("沉默", result[0].why)
        self.assertIn("分身", result[0].how)

    def test_owned_items_are_skipped(self) -> None:
        result = recommend(
            hero=BEAST,
            enemies=[SILENCER, None, None, None, None],
            popularity=POPULARITY,
            by_id=ITEMS,
            item_names=NAMES,
            owned={"item_manta"},
        )
        self.assertNotIn("item_manta", [advice.name for advice in result])

    def test_no_enemies_gives_generic_reason(self) -> None:
        result = recommend(
            hero=BEAST,
            enemies=[None, None, None, None, None],
            popularity=POPULARITY,
            by_id=ITEMS,
            item_names=NAMES,
        )
        self.assertTrue(result)
        self.assertIn("主流出装", result[0].why)

    def test_cc_and_magic_threats(self) -> None:
        meta = {
            26: HeroMeta(26, "lion", ("Support", "Disabler", "Nuker"), 0.5, 0.5, 0.5, 10),
            43: HeroMeta(43, "death_prophet", ("Carry", "Nuker", "Disabler"), 0.5, 0.5, 0.5, 10),
        }
        result = recommend(
            hero=BEAST,
            enemies=[LION, DP, None, None, None],
            popularity=POPULARITY,
            by_id=ITEMS,
            item_names=NAMES,
            meta=meta,
        )
        reasons = " ".join(advice.why for advice in result)
        self.assertIn("控制", reasons)

    def test_unknown_hero_returns_empty(self) -> None:
        self.assertEqual(
            recommend(
                hero=None,
                enemies=[SILENCER],
                popularity=POPULARITY,
                by_id=ITEMS,
                item_names=NAMES,
            ),
            [],
        )

    def test_self_dispel_hero_skips_manta_for_silence(self) -> None:
        slark = HeroInfo(93, "slark", "npc_dota_hero_slark", "斯拉克")
        result = recommend(
            hero=slark,
            enemies=[SILENCER, None, None, None, None],
            popularity={93: {"mid_game_items": {2: 900, 1: 500, 4: 300}, "late_game_items": {}}},
            by_id=ITEMS,
            item_names=NAMES,
        )
        # 小鱼人自带驱散：不该为了沉默推荐分身（黑皇仍然合理）
        self.assertEqual(result[0].name, "item_black_king_bar")
        self.assertNotIn("沉默", result[0].why)

    def test_guide_build_item_has_priority(self) -> None:
        result = recommend(
            hero=BEAST,
            enemies=[SILENCER],
            popularity=POPULARITY,
            by_id=ITEMS,
            item_names=NAMES,
            guide_items=("洞察烟斗",),
        )
        self.assertEqual(result[0].name, "item_pipe")
        self.assertIn("攻略", result[0].why)


if __name__ == "__main__":
    unittest.main()
