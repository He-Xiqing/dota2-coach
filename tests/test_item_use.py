import unittest

from dota2coach.coach.item_use import ItemUseTracker
from dota2coach.gsi.models import Snapshot


def snap(items: dict) -> Snapshot:
    return Snapshot({"items": items, "player": {"team_name": "radiant"}, "hero": {"id": 1}})


class ItemUseTest(unittest.TestCase):
    def test_midas_ready_is_reported(self) -> None:
        tracker = ItemUseTracker()
        s = snap({"item0": {"name": "item_hand_of_midas", "purchased": True, "cooldown": 0, "cooldown_max": 90}})
        tips = tracker.update(s, 600.0, False)
        self.assertEqual(len(tips), 1)
        self.assertIn("点金手", tips[0].text)

    def test_midas_on_cooldown_is_silent(self) -> None:
        tracker = ItemUseTracker()
        s = snap({"item0": {"name": "item_hand_of_midas", "purchased": True, "cooldown": 40, "cooldown_max": 90}})
        self.assertEqual(tracker.update(s, 600.0, False), [])

    def test_team_item_only_in_fight(self) -> None:
        tracker = ItemUseTracker()
        s = snap({"item0": {"name": "item_pipe", "purchased": True, "cooldown": 0, "cooldown_max": 60}})
        self.assertEqual(tracker.update(s, 900.0, False), [])
        tips = tracker.update(s, 901.0, True)
        self.assertEqual(len(tips), 1)
        self.assertTrue(tips[0].urgent)
        self.assertIn("笛子", tips[0].text)

    def test_team_item_once_per_fight(self) -> None:
        tracker = ItemUseTracker()
        s = snap({"item0": {"name": "item_crimson_guard", "purchased": True, "cooldown": 0, "cooldown_max": 70}})
        self.assertEqual(len(tracker.update(s, 900.0, True)), 1)
        self.assertEqual(tracker.update(s, 902.0, True), [])
        self.assertEqual(tracker.update(s, 903.0, False), [])
        self.assertEqual(len(tracker.update(s, 950.0, True)), 1)

    def test_ready_item_throttled(self) -> None:
        tracker = ItemUseTracker(ready_interval=90.0)
        s = snap({"item0": {"name": "item_arcane_boots", "purchased": True, "cooldown": 0, "cooldown_max": 55}})
        self.assertEqual(len(tracker.update(s, 600.0, False)), 1)
        self.assertEqual(tracker.update(s, 650.0, False), [])
        self.assertEqual(len(tracker.update(s, 700.0, False)), 1)


if __name__ == "__main__":
    unittest.main()
