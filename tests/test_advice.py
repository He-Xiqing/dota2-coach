from __future__ import annotations

import json
import shutil
import unittest
import uuid
from pathlib import Path

from dota2coach.coach.advice import lane_hint, lineup_tips
from dota2coach.knowledge.meta import HeroMeta, load_hero_meta
from dota2coach.vision.heroes import HeroInfo

ROOT = Path(__file__).resolve().parents[1]


def hero(short: str, hero_id: int = 1) -> HeroInfo:
    return HeroInfo(hero_id=hero_id, short=short, name=f"npc_dota_hero_{short}", name_loc=short)


class LineupTipsTest(unittest.TestCase):
    def test_empty_roster_gives_no_tips(self) -> None:
        self.assertEqual(lineup_tips([]), [])

    def test_stealth_enemy_asks_for_dust(self) -> None:
        tips = lineup_tips([hero("bounty_hunter")])
        self.assertTrue(any("隐身" in tip for tip in tips))

    def test_two_hard_cc_asks_for_bkb(self) -> None:
        tips = lineup_tips([hero("lion"), hero("axe")])
        joined = "".join(tips)
        self.assertIn("BKB", joined)

    def test_limit_is_respected(self) -> None:
        tips = lineup_tips(
            [hero("bounty_hunter"), hero("lion"), hero("axe"), hero("lina"), hero("necrolyte")],
            limit=1,
        )
        self.assertEqual(len(tips), 1)

    def test_roles_from_meta_drive_bkb_tip(self) -> None:
        meta = {
            900: HeroMeta(hero_id=900, name="", roles=("Disabler",)),
            901: HeroMeta(hero_id=901, name="", roles=("Disabler", "Initiator")),
        }
        # 两个没见过的英雄短名，仅靠角色标签也应触发"控制多"
        tips = lineup_tips([hero("future_hero_a", 900), hero("future_hero_b", 901)], meta=meta)
        self.assertTrue(any("控制" in tip for tip in tips))

    def test_meta_overrides_stale_static_set(self) -> None:
        # 静态表里 lina 属于爆发，但当前版本角色里没有 Nuker 时不应误报
        meta = {131: HeroMeta(hero_id=131, name="", roles=("Support",))}
        tips = lineup_tips([hero("lina", 131), hero("zuus", 131)], meta=meta)
        self.assertFalse(any("法系" in tip for tip in tips))


class HeroMetaLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = ROOT / "tests" / "_tmp" / f"meta-{uuid.uuid4().hex[:8]}"

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_load_missing_file_returns_empty(self) -> None:
        self.assertEqual(load_hero_meta(self.dir / "nope.json"), {})

    def test_load_reads_roles_and_winrate(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self.dir / "hero_meta.json"
        path.write_text(
            json.dumps(
                {
                    "source": "test",
                    "heroes": {
                        "1": {
                            "name": "npc_dota_hero_antimage",
                            "roles": ["Carry", "Escape"],
                            "pub_winrate": 0.48,
                            "pro_picks": 7,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        meta = load_hero_meta(path)
        self.assertIn(1, meta)
        self.assertEqual(meta[1].roles, ("Carry", "Escape"))
        self.assertAlmostEqual(meta[1].pub_winrate, 0.48)
        self.assertEqual(meta[1].pro_picks, 7)


class LaneHintTest(unittest.TestCase):
    def test_missing_position(self) -> None:
        self.assertIsNone(lane_hint(None, None))

    def test_mid(self) -> None:
        self.assertEqual(lane_hint(0, 0), "你在中路")

    def test_top_and_bottom(self) -> None:
        self.assertIn("上路", lane_hint(0, 3000) or "")
        self.assertIn("下路", lane_hint(0, -3000) or "")


if __name__ == "__main__":
    unittest.main()
