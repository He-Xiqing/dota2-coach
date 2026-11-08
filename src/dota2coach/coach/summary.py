"""赛后小结：把 GSI 最后一帧整理成"上一把表现 + 提升建议 + 鼓励"。"""

from __future__ import annotations

import random
from dataclasses import dataclass

from ..gsi.models import Snapshot
from .texts import t

# 各位置的大致补刀基准（每分钟），只用于给一句提醒，不做评分
_GPM_GOOD = 380
_LH_PER_MIN = 4.0


@dataclass(frozen=True)
class MatchSummary:
    hero: str
    kills: int
    deaths: int
    assists: int
    last_hits: int
    denies: int
    gold: int
    gpm: int
    duration: int  # 秒
    win: bool | None  # None = 不知道（人机/未记录）
    is_support: bool = False  # 带 Support 标签的英雄不提醒补刀/打钱效率

    @property
    def kda(self) -> str:
        return f"{self.kills}/{self.deaths}/{self.assists}"

    @property
    def result(self) -> str:
        if self.win is None:
            return "对局结束"
        return "胜利" if self.win else "失败"


def summarize(
    snapshot: Snapshot, hero_name: str, roles: tuple[str, ...] = ()
) -> MatchSummary | None:
    """从一帧 GSI 快照里提取赛后数据；数据不够（不在对局/没英雄）返回 None。"""
    if snapshot is None or not snapshot.hero_id:
        return None
    player = snapshot.player or {}
    game_map = snapshot.map or {}
    duration = int(snapshot.game_time or 0)
    if duration <= 0:
        return None
    win: bool | None = None
    win_team = (game_map.get("win_team") or "").lower()
    my_team = (player.get("team_name") or "").lower()
    if win_team and my_team:
        win = win_team == my_team
    return MatchSummary(
        hero=hero_name or "?",
        kills=int(player.get("kills") or 0),
        deaths=int(player.get("deaths") or 0),
        assists=int(player.get("assists") or 0),
        last_hits=int(player.get("last_hits") or 0),
        denies=int(player.get("denies") or 0),
        gold=int(player.get("gold") or 0),
        gpm=int(player.get("gpm") or 0),
        duration=duration,
        win=win,
        is_support="Support" in set(roles),
    )


def improvements(summary: MatchSummary) -> list[str]:
    """1–3 条最值得改的地方，按重要性排序。"""
    tips: list[str] = []
    minutes = max(1.0, summary.duration / 60.0)

    deaths_per_10 = summary.deaths / minutes * 10.0
    if summary.deaths >= 10 or (summary.deaths >= 6 and deaths_per_10 >= 2.5):
        tips.append(
            t(
                "improve_deaths",
                n=summary.deaths,
            )
        )

    lh_per_min = summary.last_hits / minutes
    if not summary.is_support and lh_per_min < _LH_PER_MIN:
        tips.append(
            t(
                "improve_cs",
                n=summary.last_hits,
                rate=f"{lh_per_min:.1f}",
            )
        )

    if not summary.is_support and summary.gpm and summary.gpm < _GPM_GOOD:
        tips.append(
            t(
                "improve_gpm",
                gpm=summary.gpm,
            )
        )

    if not tips and summary.win is not False:
        tips.append(t("improve_good"))

    return tips[:3]


_ENCOURAGE: dict[str, tuple[str, ...]] = {
    "encourage_win": ("encourage_win", "encourage_win_2", "encourage_win_3"),
    "encourage_loss": ("encourage_loss", "encourage_loss_2", "encourage_loss_3"),
    "encourage_win_plain": ("encourage_win_plain", "encourage_win_plain_2"),
    "encourage_loss_plain": ("encourage_loss_plain", "encourage_loss_plain_2"),
}


def encourage(summary: MatchSummary, has_tips: bool = True) -> str:
    if summary.win is True:
        key = "encourage_win"
    elif summary.win is False:
        key = "encourage_loss"
    else:
        return t("summary_draw")
    if not has_tips:
        key += "_plain"
    return t(random.choice(_ENCOURAGE.get(key, (key,))))


def _result_text(summary: MatchSummary) -> str:
    if summary.win is None:
        return t("summary_draw")
    return t("win") if summary.win else t("loss")

def summary_lines(summary: MatchSummary) -> list[str]:
    """卡片正文：数据两行 + 建议若干行。"""
    minutes = int(round(summary.duration / 60.0))
    lines = [
        t(
            "summary_stats",
            hero=summary.hero,
            kda=summary.kda,
            cs=summary.last_hits,
            denies=summary.denies,
            gpm=summary.gpm,
            minutes=minutes,
        ),
        t("result", result=_result_text(summary)),
    ]
    tips = improvements(summary)
    lines.extend(tips)
    return lines
