from __future__ import annotations

import unittest

from dota2coach.coach.tp import TP_TEXT, tp_key, tp_reminder
from dota2coach.gsi.models import Snapshot


class TpReminderTests(unittest.TestCase):
    def test_before_20_minutes_is_silent(self) -> None:
        self.assertIsNone(tp_reminder(19 * 60, has_tp=False))

    def test_with_tp_scroll_is_silent(self) -> None:
        self.assertIsNone(tp_reminder(25 * 60, has_tp=True))

    def test_missing_tp_scroll_after_20_minutes(self) -> None:
        self.assertEqual(tp_reminder(20 * 60, has_tp=False), TP_TEXT)

    def test_key_changes_every_minute(self) -> None:
        self.assertNotEqual(tp_key(21 * 60), tp_key(21 * 60 + 60))
        self.assertEqual(tp_key(21 * 60), tp_key(21 * 60 + 30))

    def test_has_tp_scroll_reads_dedicated_slot(self) -> None:
        snapshot = Snapshot(
            {
                "items": {
                    "teleport0": {"name": "item_tpscroll"},
                    "slot0": {"name": "item_blink"},
                }
            }
        )
        self.assertTrue(snapshot.has_tp_scroll())

    def test_has_tp_scroll_falls_back_to_inventory(self) -> None:
        snapshot = Snapshot({"items": {"slot0": {"name": "item_tpscroll"}}})
        self.assertTrue(snapshot.has_tp_scroll())

    def test_has_tp_scroll_ignores_empty_teleport_slot(self) -> None:
        snapshot = Snapshot({"items": {"teleport0": "empty", "slot0": {"name": "item_blink"}}})
        self.assertFalse(snapshot.has_tp_scroll())
