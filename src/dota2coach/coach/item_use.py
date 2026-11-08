"""物品使用提醒：团战开团队装、冷却好了就用的小件。

GSI 的 items 会给出每格的 name / cooldown / cooldown_max / charges，
所以不需要猜：cooldown <= 0 且 cooldown_max > 0 就是“可用”。
"""

from __future__ import annotations

from dataclasses import dataclass

from .texts import t

# 团战才提醒的团队装（物品名就是文案 key，见 coach/texts_items.py）
TEAM_ITEMS: tuple[str, ...] = (
    "item_pipe",
    "item_crimson_guard",
    "item_guardian_greaves",
    "item_mekansm",
    "item_glimmer_cape",
    "item_lotus_orb",
    "item_solar_crest",
    "item_pavise",
)

# 冷却好了就该用的经济/续航装
READY_ITEMS: tuple[str, ...] = (
    "item_hand_of_midas",
    "item_arcane_boots",
    "item_soul_ring",
    "item_magic_wand",
    "item_bottle",
    "item_helm_of_the_dominator",
)


@dataclass(frozen=True)
class ItemTip:
    key: str
    text: str
    urgent: bool = False


class ItemUseTracker:
    """按“团战回合 / 冷却周期”去重，避免同一件装备刷屏。"""

    def __init__(self, ready_interval: float = 90.0, fight_interval: float = 45.0) -> None:
        self.ready_interval = ready_interval
        self.fight_interval = fight_interval
        self._in_fight = False
        self._fight_seq = 0
        self._last_ready: dict[str, float] = {}
        self._last_fight: dict[str, float] = {}

    def reset(self) -> None:
        self._in_fight = False
        self._fight_seq = 0
        self._last_ready.clear()
        self._last_fight.clear()

    @staticmethod
    def _owned(snapshot) -> dict[str, dict]:
        owned: dict[str, dict] = {}
        for value in (snapshot.items or {}).values():
            if not isinstance(value, dict):
                continue
            name = str(value.get("name") or "")
            if not name.startswith("item_"):
                continue
            if value.get("purchased") is False:
                continue
            owned.setdefault(name, value)
        return owned

    @staticmethod
    def _ready(name: str, value: dict) -> bool:
        try:
            cooldown = float(value.get("cooldown") or 0)
            cooldown_max = float(value.get("cooldown_max") or 0)
            charges = float(value.get("charges") or 0)
        except (TypeError, ValueError):
            return False
        if cooldown > 0:
            return False
        if cooldown_max > 0:
            return True
        # 魔杖/瓶子这类没有冷却、按充能使用的物品
        return name in ("item_magic_wand", "item_bottle") and charges > 0

    def update(self, snapshot, clock: float, in_fight: bool) -> list[ItemTip]:
        owned = self._owned(snapshot)
        if not owned:
            return []
        if in_fight and not self._in_fight:
            self._fight_seq += 1
            self._last_fight.clear()
        self._in_fight = in_fight
        tips: list[ItemTip] = []

        if in_fight:
            for name in TEAM_ITEMS:
                value = owned.get(name)
                if value is None or not self._ready(name, value):
                    continue
                last = self._last_fight.get(name, -999.0)
                if clock - last < self.fight_interval:
                    continue
                self._last_fight[name] = clock
                tips.append(ItemTip(f"use:{name}:{self._fight_seq}", t(name), urgent=True))

        for name in READY_ITEMS:
            value = owned.get(name)
            if value is None or not self._ready(name, value):
                continue
            last = self._last_ready.get(name, -999.0)
            if clock - last < self.ready_interval:
                continue
            self._last_ready[name] = clock
            tips.append(ItemTip(f"use:{name}:{int(clock // self.ready_interval)}", t(name)))
        return tips
