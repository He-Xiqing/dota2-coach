"""对线期补给/出门装建议：根据敌方阵容的消耗、爆发、物理压力给 2 件东西。"""

from __future__ import annotations

from typing import Sequence

from ..knowledge.meta import HeroMeta
from ..vision.heroes import HeroInfo
from .advice import FALLBACK_BURST, STEALTH, has_role
from .texts import t


def lane_items(
    enemies: Sequence[HeroInfo | None],
    meta: dict[int, HeroMeta] | None = None,
) -> list[tuple[str, str]]:
    """返回 [(物品, 理由)]，最多 2 条。"""
    heroes = [hero for hero in enemies if hero is not None]
    if not heroes:
        return []

    nukers = [hero for hero in heroes if has_role(hero, meta, "Nuker", FALLBACK_BURST)]
    carries = [hero for hero in heroes if has_role(hero, meta, "Carry", set())]
    stealth = [hero for hero in heroes if hero.short in STEALTH]

    picks: list[tuple[str, str]] = []
    if stealth:
        picks.append((t("lane_name_dust"), t("lane_dust")))
    if len(nukers) >= 2:
        picks.append((t("lane_name_wand"), t("lane_wand")))
    if len(carries) >= 2:
        picks.append((t("lane_name_shield"), t("lane_shield")))
    if not picks:
        picks.append((t("lane_name_regen"), t("lane_regen")))
    # 兜底：至少给两件
    if len(picks) == 1:
        picks.append((t("lane_name_tree"), t("lane_tree")))
    return picks[:2]
