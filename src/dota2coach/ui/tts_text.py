"""朗读文本清洗：把界面里的符号/缩写改成适合 TTS 的句子，避免奇怪断句。"""

from __future__ import annotations

import re

_DASH = re.compile(r"[—–]+")
_CLOCK = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?![\d:])")
_KILO = re.compile(r"(\d+(?:\.\d+)?)\s*[kK]\b")
_MULTI_COMMA = re.compile(r"[，,]{2,}")
_MULTI_STOP = re.compile(r"[。！？]{2,}")
_SPACES = re.compile(r"[ \t]+")
_PUNCT_SPACE = re.compile(r"\s*([，。；！？、])\s*")


def _clock(match: re.Match[str]) -> str:
    minutes = int(match.group(1))
    seconds = int(match.group(2))
    if seconds == 0:
        return f"{minutes} 分"
    if minutes == 0:
        return f"{seconds} 秒"
    return f"{minutes} 分 {seconds} 秒"


def _kilo(match: re.Match[str]) -> str:
    value = float(match.group(1)) * 1000
    return str(int(round(value)))


def speakable(text: str) -> str:
    """把提示文本变成自然口播：统一逗号、展开时间与 k 缩写、去掉括号。"""
    raw = (text or "").strip()
    if not raw:
        return ""
    out = _DASH.sub("，", raw)
    out = out.replace("·", "，").replace("|", "，").replace("→", "，然后")
    out = out.replace("：", "，")
    out = out.replace("（", "，").replace("）", "，")
    out = out.replace("(", "，").replace(")", "，")
    out = _CLOCK.sub(_clock, out)
    out = _KILO.sub(_kilo, out)
    out = out.replace("／", "，").replace("/", "，")
    out = _MULTI_COMMA.sub("，", out)
    out = _MULTI_STOP.sub("。", out)
    out = out.replace("，。", "。")
    out = _PUNCT_SPACE.sub(r"\1", out)
    out = _SPACES.sub(" ", out)
    out = out.strip("，。；; ")
    if not out:
        return ""
    return out + "。"
