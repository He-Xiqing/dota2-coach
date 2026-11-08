import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dota2coach.gsi.models import Snapshot  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "gsi" / "playing.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class SnapshotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = Snapshot(load_fixture())

    def test_identity(self) -> None:
        self.assertEqual(self.snapshot.hero_name, "npc_dota_hero_nevermore")
        self.assertEqual(self.snapshot.hero_id, 11)
        self.assertEqual(self.snapshot.match_id, 7890123456)
        self.assertTrue(self.snapshot.is_in_game)

    def test_time_and_stats(self) -> None:
        self.assertEqual(self.snapshot.game_time, 312)
        self.assertEqual(self.snapshot.level, 9)
        self.assertAlmostEqual(self.snapshot.health_percent or 0.0, 66.1)
        self.assertEqual(self.snapshot.gold, 812)
        self.assertEqual(self.snapshot.kda(), "4/1/5")

    def test_abilities_skip_empty_slots(self) -> None:
        levels = self.snapshot.ability_levels()
        self.assertEqual(self.snapshot.ability_count, 4)
        self.assertEqual(levels["nevermore_shadowraze1"], 4)
        self.assertNotIn("", levels)

    def test_items(self) -> None:
        names = self.snapshot.item_names()
        self.assertIn("item_power_treads", names)
        self.assertNotIn("", names)
        self.assertEqual(self.snapshot.item_count, 6)

    def test_summary(self) -> None:
        summary = self.snapshot.summary()
        self.assertEqual(summary["hero"], "npc_dota_hero_nevermore")
        self.assertEqual(summary["abilities"], 4)
        self.assertNotIn("draft", self.snapshot.top_level_keys)

    def test_missing_sections_are_safe(self) -> None:
        snapshot = Snapshot({"map": {"game_state": "DOTA_GAMERULES_STATE_HERO_SELECTION"}})
        self.assertIsNone(snapshot.match_id)
        self.assertIsNone(snapshot.hero_name)
        self.assertIsNone(snapshot.game_time)
        self.assertFalse(snapshot.is_in_game)
        self.assertEqual(snapshot.top_level_keys, ("map",))
        self.assertEqual(snapshot.item_names(), [])
        self.assertEqual(snapshot.ability_count, 0)

    def test_negative_game_time(self) -> None:
        snapshot = Snapshot({"map": {"game_time": -35}})
        self.assertEqual(snapshot.game_time, -35)


if __name__ == "__main__":
    unittest.main()
