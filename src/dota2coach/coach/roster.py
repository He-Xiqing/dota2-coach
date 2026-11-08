"""双方阵容：从"战友与宿敌"面板的识别结果整理成 5v5。

约定：allies[0] 一定是自己（GSI 的 hero 优先），敌方不保证顺序。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..vision.heroes import HeroInfo, HeroMatch, HeroMatcher, ensure_min_size, identify_panel

TEAM_SIZE = 5


@dataclass(frozen=True)
class Roster:
    """一局的 5v5 阵容；未识别的位置是 None。"""

    allies: tuple[HeroInfo | None, ...]
    enemies: tuple[HeroInfo | None, ...]
    source: str = "panel"
    captured_at: str = ""

    @property
    def known(self) -> int:
        return sum(1 for hero in self.allies + self.enemies if hero is not None)

    @property
    def complete(self) -> bool:
        return self.known == TEAM_SIZE * 2

    def names(self) -> tuple[list[str], list[str]]:
        """返回（我方名字、敌方名字），未知用“?”。"""
        return (
            [hero.name_loc if hero else "?" for hero in self.allies],
            [hero.name_loc if hero else "?" for hero in self.enemies],
        )

    def summary(self) -> str:
        allies, enemies = self.names()
        return f"我方 {'、'.join(allies)} | 敌方 {'、'.join(enemies)}"


def _heroes(matches: list[HeroMatch]) -> list[HeroInfo | None]:
    heroes = [match.hero for match in matches][:TEAM_SIZE]
    heroes.extend([None] * (TEAM_SIZE - len(heroes)))
    return heroes


def _drop_duplicates(
    allies: list[HeroInfo | None], enemies: list[HeroInfo | None]
) -> tuple[list[HeroInfo | None], list[HeroInfo | None]]:
    """同一个人不会出现在两边：先出现的一方保留，重复位置置空。"""
    seen: set[int] = set()
    for group in (allies, enemies):
        for index, hero in enumerate(group):
            if hero is None:
                continue
            if hero.hero_id in seen:
                group[index] = None
            else:
                seen.add(hero.hero_id)
    return allies, enemies


def roster_from_matches(
    ally_matches: list[HeroMatch],
    enemy_matches: list[HeroMatch],
    self_hero: HeroInfo | None = None,
    captured_at: str = "",
    source: str = "panel",
) -> Roster:
    """把两侧的识别结果整理成 Roster。

    self_hero 来自 GSI，最可靠：用它覆盖第 0 行，再做去重。
    """
    allies = _heroes(ally_matches)
    enemies = _heroes(enemy_matches)
    if self_hero is not None:
        allies[0] = self_hero
    allies, enemies = _drop_duplicates(allies, enemies)
    return Roster(tuple(allies), tuple(enemies), source, captured_at)


def roster_from_panel(
    image: np.ndarray,
    matcher: HeroMatcher,
    self_hero: HeroInfo | None = None,
    min_score: float = 0.55,
    min_gap: float = 0.02,
    captured_at: str = "",
) -> Roster:
    """识别"战友与宿敌"面板（决策时间）：左列我方、右列敌方。"""
    raw = identify_panel(ensure_min_size(image), matcher, min_score=min_score, min_gap=min_gap)
    return roster_from_matches(raw["ally"], raw["enemy"], self_hero, captured_at, "panel")


def roster_from_topbar(
    matches: list[HeroMatch],
    self_hero: HeroInfo | None = None,
    captured_at: str = "",
) -> Roster:
    """顶部英雄栏：前 5 个是队友，后 5 个是对手（对局中一直存在，不依赖 Dota Plus）。"""
    allies = matches[:TEAM_SIZE]
    enemies = matches[TEAM_SIZE:TEAM_SIZE * 2]
    return roster_from_matches(allies, enemies, self_hero, captured_at, "topbar")
