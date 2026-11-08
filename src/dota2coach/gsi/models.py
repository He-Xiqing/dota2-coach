"""GSI 报文的结构化视图。

GSI 的字段随版本/情境变化（观战、暂停、选人阶段各不相同），
所以这里全部按"可选"处理：拿不到就返回 None，绝不假设一定存在。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_STATE_IN_PROGRESS = "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"
# 赛前也算“已进入对局”：名字条要在 -1:30 的倒计时前就出现
_STATE_MATCH = (
    "STRATEGY_TIME",
    "TEAM_SHOWCASE",
    "PRE_GAME",
    "GAME_IN_PROGRESS",
)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text.lstrip("-").isdigit():
            return int(text)
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


@dataclass(frozen=True)
class Snapshot:
    """一次 GSI POST 的不可变快照。"""

    raw: dict[str, Any]

    # --- 顶层小节 -----------------------------------------------------
    def _section(self, name: str) -> dict[str, Any]:
        value = self.raw.get(name)
        return value if isinstance(value, dict) else {}

    @property
    def provider(self) -> dict[str, Any]:
        return self._section("provider")

    @property
    def map(self) -> dict[str, Any]:
        return self._section("map")

    @property
    def player(self) -> dict[str, Any]:
        return self._section("player")

    @property
    def hero(self) -> dict[str, Any]:
        return self._section("hero")

    @property
    def abilities(self) -> dict[str, Any]:
        return self._section("abilities")

    @property
    def items(self) -> dict[str, Any]:
        return self._section("items")

    @property
    def buildings(self) -> dict[str, Any]:
        return self._section("buildings")

    @property
    def game(self) -> dict[str, Any]:
        return self._section("game")

    @property
    def draft(self) -> dict[str, Any]:
        return self._section("draft")

    @property
    def events(self) -> list[Any]:
        value = self.raw.get("events")
        return value if isinstance(value, list) else []

    @property
    def top_level_keys(self) -> tuple[str, ...]:
        return tuple(sorted(k for k in self.raw if isinstance(k, str)))

    # --- 常用字段 -----------------------------------------------------
    @property
    def game_state(self) -> str | None:
        value = self.map.get("game_state")
        return str(value) if value else None

    @property
    def is_in_game(self) -> bool:
        state = self.game_state
        return bool(state) and _STATE_IN_PROGRESS in str(state)

    @property
    def in_match(self) -> bool:
        """赛前（决策/展示/加载倒计时）与对局中都算，用于提前显示名字条。"""
        state = str(self.game_state or "")
        if not state:
            return False
        return any(word in state for word in _STATE_MATCH)

    @property
    def match_id(self) -> int | None:
        match_id = _as_int(self.map.get("matchid"))
        return match_id if match_id else None

    @property
    def game_time(self) -> int | None:
        return _as_int(self.map.get("game_time"))

    @property
    def hero_id(self) -> int | None:
        return _as_int(self.hero.get("id"))

    @property
    def hero_name(self) -> str | None:
        value = self.hero.get("name")
        return str(value) if value else None

    @property
    def level(self) -> int | None:
        return _as_int(self.hero.get("level"))

    @property
    def health_percent(self) -> float | None:
        return _as_float(self.hero.get("health_percent"))

    @property
    def mana_percent(self) -> float | None:
        return _as_float(self.hero.get("mana_percent"))

    @property
    def is_alive(self) -> bool | None:
        value = self.hero.get("alive")
        return value if isinstance(value, bool) else None

    @property
    def gold(self) -> int | None:
        return _as_int(self.player.get("gold"))

    @property
    def kills(self) -> int | None:
        return _as_int(self.player.get("kills"))

    @property
    def deaths(self) -> int | None:
        return _as_int(self.player.get("deaths"))

    @property
    def assists(self) -> int | None:
        return _as_int(self.player.get("assists"))

    @property
    def last_hits(self) -> int | None:
        return _as_int(self.player.get("last_hits"))

    def ability_levels(self) -> dict[str, int]:
        """{技能内部名: 等级}，只包含真实存在的技能槽。"""
        result: dict[str, int] = {}
        for key, value in self.abilities.items():
            if not isinstance(value, dict):
                continue
            name = value.get("name")
            if not name:
                continue
            result[str(name)] = _as_int(value.get("level")) or 0
        return result

    @property
    def ability_count(self) -> int:
        return len(self.ability_levels())

    def ability_entries(self) -> list[dict[str, Any]]:
        return [v for v in self.abilities.values() if isinstance(v, dict) and v.get("name")]

    def item_names(self) -> list[str]:
        """按槽位顺序返回非空物品（含背包/储藏处）。"""
        result: list[str] = []
        for key in sorted(self.items):
            value = self.items[key]
            if isinstance(value, dict) and value.get("name"):
                result.append(str(value["name"]))
        return result

    def inventory_names(self) -> list[str]:
        """只返回身上 6 格主背包（不含储藏处/背包/中立物品）。"""
        result: list[str] = []
        for index in range(6):
            value = self.items.get(f"slot{index}")
            if isinstance(value, dict) and value.get("name"):
                result.append(str(value["name"]))
        return result

    def has_tp_scroll(self) -> bool:
        """回城卷轴新版有独立格子（teleport0），旧版在主背包里。"""
        teleport = self.items.get("teleport0")
        if isinstance(teleport, dict) and str(teleport.get("name") or "") == "item_tpscroll":
            return True
        return "item_tpscroll" in self.inventory_names()

    @property
    def item_count(self) -> int:
        return len(self.item_names())

    def kda(self) -> str:
        kills = self.kills if self.kills is not None else 0
        deaths = self.deaths if self.deaths is not None else 0
        assists = self.assists if self.assists is not None else 0
        return f"{kills}/{deaths}/{assists}"

    def summary(self) -> dict[str, Any]:
        """一行式摘要，写入 logs/gsi_summary.jsonl。"""
        return {
            "match_id": self.match_id,
            "game_state": self.game_state,
            "game_time": self.game_time,
            "hero": self.hero_name,
            "level": self.level,
            "hp": self.health_percent,
            "mana": self.mana_percent,
            "alive": self.is_alive,
            "abilities": self.ability_count,
            "items": self.item_count,
            "gold": self.gold,
            "kda": self.kda(),
            "last_hits": self.last_hits,
            "top_keys": list(self.top_level_keys),
        }
