from __future__ import annotations

import unittest

from dota2coach.coach.threats import threat_labels, threat_summary
from dota2coach.knowledge.meta import HeroMeta
from dota2coach.vision.heroes import HeroInfo


def hero(hero_id: int, short: str, name: str) -> HeroInfo:
    return HeroInfo(hero_id=hero_id, short=short, name=short, name_loc=name)


def meta(hero_id: int, roles: tuple[str, ...]) -> HeroMeta:
    return HeroMeta(hero_id=hero_id, name="x", roles=roles)


class ThreatTest(unittest.TestCase):
    def test_disabler_is_initiator(self) -> None:
        h = hero(11, "lion", "莱恩")
        m = {11: meta(11, ("Support", "Disabler", "Nuker"))}
        self.assertEqual(threat_labels(h, m), ["先手", "爆发"])

    def test_pure_nuker_only_burst(self) -> None:
        h = hero(13, "puck", "帕克")
        m = {13: meta(13, ("Initiator", "Nuker"))}
        self.assertEqual(threat_labels(h, m), ["先手", "爆发"])

    def test_stealth_hero_flagged(self) -> None:
        h = hero(32, "riki", "力丸")
        self.assertIn("隐身", threat_labels(h, {}))

    def test_unknown_hero_has_no_labels(self) -> None:
        self.assertEqual(threat_labels(None, {}), [])

    def test_summary_counts(self) -> None:
        enemies = [hero(11, "lion", "莱恩"), hero(32, "riki", "力丸"), hero(13, "puck", "帕克")]
        m = {11: meta(11, ("Disabler",)), 13: meta(13, ("Nuker",))}
        counts = threat_summary(enemies, m)
        self.assertEqual(counts["先手"], 1)
        self.assertEqual(counts["爆发"], 1)
        self.assertEqual(counts["隐身"], 1)


if __name__ == "__main__":
    unittest.main()
