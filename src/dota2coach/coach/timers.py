"""时间点提醒：只写确定无疑的机制（7.41f 实测/官方补丁说明）。

时间表（7.41f，来源：Valve 补丁说明，7.29–7.41f）：
- 赏金符：0:00 四个，之后**每 4 分钟**（7.38 起）一个；
- 水符：只在 2:00 和 4:00，两个神符点各一个；
- 神符（强化符）：**6:00 起每 2 分钟**一个；
- 智慧神龛（取代经验神符）：**每 7 分钟**刷新一次，给经验；
- 莲花池：**每 3 分钟**长一朵治疗莲花（最多 6 朵）；
- 痛苦魔方（Tormentor）：20:00 首次出现。

这些是地图机制，不随英雄/阵容变化，所以离线也能用；版本改动时只改这里的常量。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .state import format_clock
from .texts import t

BOUNTY_PERIOD = 240.0        # 7.38：每 4 分钟
BOUNTY_ENABLED = False       # 用户要求：不再提醒赏金符
WATER_TIMES = (120.0, 240.0)  # 只在 2:00 / 4:00
POWER_FIRST = 360.0          # 6:00 起
POWER_PERIOD = 120.0
POWER_UNTIL = 24 * 60.0      # 24:00 之后不再提醒强化神符
WISDOM_FIRST = 420.0         # 智慧神龛：7:00 起，每 7 分钟
WISDOM_PERIOD = 420.0
WISDOM_UNTIL = 21 * 60.0     # 21:00 之后不再提醒经验神符
LOTUS_FIRST = 180.0          # 莲花池：3:00 起，每 3 分钟
LOTUS_PERIOD = 180.0
LOTUS_UNTIL = 12 * 60.0      # 12:00 之后不再提醒莲花
TORMENTOR_FIRST = 1200.0     # 20:00


@dataclass(frozen=True)
class Hint:
    at: float
    text: str

    def label(self) -> str:
        return f"{format_clock(self.at)}  {self.text}"


def _next_at(clock: float, period: float, first: float = 0.0) -> float:
    if clock < first:
        return first
    return first + (math.floor((clock - first) / period + 1e-9) + 1) * period


def upcoming(clock: float, horizon: float = 25.0) -> list[Hint]:
    """返回未来 horizon 秒内的提醒（不含已经过去的）。"""
    if clock < 0:
        return []
    hints: list[Hint] = []

    if BOUNTY_ENABLED:
        bounty = _next_at(clock, BOUNTY_PERIOD, 0.0)
        if 0 <= bounty - clock <= horizon:
            hints.append(Hint(bounty, t("timer_bounty")))

    for water in WATER_TIMES:
        if 0 <= water - clock <= horizon:
            hints.append(Hint(water, t("timer_water")))

    power = _next_at(clock, POWER_PERIOD, POWER_FIRST)
    if clock < POWER_UNTIL and 0 <= power - clock <= horizon:
        hints.append(Hint(power, t("timer_power")))

    wisdom = _next_at(clock, WISDOM_PERIOD, WISDOM_FIRST)
    if clock < WISDOM_UNTIL and 0 <= wisdom - clock <= horizon:
        hints.append(Hint(wisdom, t("timer_wisdom")))

    lotus = _next_at(clock, LOTUS_PERIOD, LOTUS_FIRST)
    if clock < LOTUS_UNTIL and 0 <= lotus - clock <= horizon:
        hints.append(Hint(lotus, t("timer_lotus")))

    if 0 <= TORMENTOR_FIRST - clock <= horizon:
        hints.append(Hint(TORMENTOR_FIRST, t("timer_tormentor")))

    return sorted(hints, key=lambda hint: hint.at)


def phase_tip(clock: float) -> str | None:
    """阶段性的固定提醒（与阵容无关，避免乱猜）。"""
    if 0 <= clock < 30:
        return t("hint_start")
    if 9 * 60 + 45 <= clock < 10 * 60 + 15:
        return t("hint_line_end")
    if 19 * 60 + 45 <= clock < 20 * 60 + 15:
        return t("hint_20min")
    return None
