from __future__ import annotations

from .texts import t

TP_SCROLL = "item_tpscroll"
TP_START = 20 * 60
TP_PERIOD = 60  # 缺 TP 时每分钟检查/提醒一次
TP_TEXT = "没带回城：20 分钟后常备 TP，能救能逃"


def tp_reminder(clock: int, has_tp: bool) -> str | None:
    """20 分钟后身上没有回城卷轴就提醒；有就保持安静。

    TP 现在有独立格子（GSI 的 teleport0），调用方用 Snapshot.has_tp_scroll() 判断。
    """
    if clock < TP_START:
        return None
    if has_tp:
        return None
    return t("tp_missing")


def tp_key(clock: int) -> str:
    """每分钟一个 key，缺 TP 时每分钟最多提醒一次。"""
    return f"tp:missing:{int(clock // TP_PERIOD)}"
