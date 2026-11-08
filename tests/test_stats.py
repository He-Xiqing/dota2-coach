from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

from dota2coach.coach.state import HealthTracker
from dota2coach.knowledge.builds import ItemInfo, display_name, load_item_table, suggest_items

ROOT = Path(__file__).resolve().parents[1]


class HealthTrackerTest(unittest.TestCase):
    def test_accumulates_damage_taken(self) -> None:
        tracker = HealthTracker()
        tracker.update(100.0, 0.0)
        tracker.update(80.0, 1.0)
        tracker.update(70.0, 2.0)
        tracker.update(60.0, 3.0)
        self.assertGreater(tracker.per_minute, 100.0)

    def test_healing_does_not_add_damage(self) -> None:
        tracker = HealthTracker()
        tracker.update(100.0, 0.0)
        tracker.update(60.0, 1.0)
        tracker.update(90.0, 2.0)
        before = tracker.total_loss
        tracker.update(95.0, 3.0)
        self.assertEqual(tracker.total_loss, before)

    def test_long_gap_is_ignored(self) -> None:
        tracker = HealthTracker()
        tracker.update(100.0, 0.0)
        tracker.update(10.0, 30.0)  # 断档 30 秒，不算
        self.assertEqual(tracker.total_loss, 0.0)


class ItemNameTest(unittest.TestCase):
    def test_display_name_accepts_prefixed_and_bare(self) -> None:
        names = {"item_blink": "闪烁匕首"}
        self.assertEqual(display_name("item_blink", names), "闪烁匕首")
        self.assertEqual(display_name("blink", names), "闪烁匕首")

    def test_load_item_table_normalizes_names(self) -> None:
        folder = ROOT / "tests" / "_tmp" / f"items-{uuid4().hex[:8]}"
        folder.mkdir(parents=True, exist_ok=True)
        try:
            path = folder / "items.json"
            path.write_text(
                json.dumps(
                    {
                        "by_id": {"1": {"name": "blink", "dname": "Blink Dagger", "created": False, "cost": 2250}},
                        "by_name": {"blink": "Blink Dagger"},
                    }
                ),
                encoding="utf-8",
            )
            by_id, by_name = load_item_table(path)
            self.assertIn("item_blink", by_name)
            self.assertEqual(by_id[1].name, "item_blink")
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def test_whole_item_is_recommended_but_cheap_component_is_not(self) -> None:
        by_id = {
            1: ItemInfo("item_blink", "Blink Dagger", created=False, cost=2250),
            2: ItemInfo("item_blade_of_alacrity", "Blade of Alacrity", created=False, cost=1000),
        }
        popularity = {11: {"mid_game_items": {1: 100, 2: 90}}}
        picked = suggest_items(popularity, 11, set(), by_id, limit=3)
        self.assertIn("item_blink", picked)
        self.assertNotIn("item_blade_of_alacrity", picked)


if __name__ == "__main__":
    unittest.main()
