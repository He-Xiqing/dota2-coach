"""对局状态：阶段划分与常用读数。"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..gsi.models import Snapshot
from .roster import Roster

LANING_END_S = 10 * 60
MID_END_S = 25 * 60

PHASE_PREGAME = "准备"
PHASE_LANING = "对线期"
PHASE_MID = "中期"
PHASE_LATE = "后期"


def clock_time(snapshot: Snapshot) -> float:
    """优先用 map.clock_time（和游戏内计时一致），没有就退回 game_time。"""
    game_map = snapshot.map or {}
    value = game_map.get("clock_time")
    if value is None:
        return float(snapshot.game_time or 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(snapshot.game_time or 0.0)


def phase_for(clock: float) -> str:
    if clock < 0:
        return PHASE_PREGAME
    if clock < LANING_END_S:
        return PHASE_LANING
    if clock < MID_END_S:
        return PHASE_MID
    return PHASE_LATE


def format_clock(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


@dataclass
class CoachState:
    snapshot: Snapshot | None = None
    roster: Roster | None = None

    @property
    def clock(self) -> float:
        if self.snapshot is None:
            return -1.0
        return clock_time(self.snapshot)

    @property
    def phase(self) -> str:
        return phase_for(self.clock)


class HealthTracker:
    """按快照之间的掉血量估算"每分钟承伤"。

    GSI 不给伤害统计，这里只用生命值差做近似：两次快照之间掉的血
    视为承伤（回血会抵消一部分，所以显示时标注"约"）。
    """

    def __init__(self) -> None:
        self._prev_hp: float | None = None
        self._started_at: float | None = None
        self._now: float | None = None
        self.total_loss = 0.0

    def update(self, health: float, now: float) -> None:
        if health <= 0:
            self._prev_hp = None
            return
        if self._started_at is None:
            self._started_at = now
        if self._prev_hp is not None and now > self._now:
            gap = now - self._now
            if gap <= 3.0:  # 超过 3 秒的断档不计，避免重连后误算
                loss = self._prev_hp - health
                if loss > 0:
                    self.total_loss += loss
        self._prev_hp = health
        self._now = now

    @property
    def per_minute(self) -> float:
        if self._started_at is None or self._now is None:
            return 0.0
        elapsed = max(5.0, self._now - self._started_at)
        return self.total_loss / (elapsed / 60.0)
