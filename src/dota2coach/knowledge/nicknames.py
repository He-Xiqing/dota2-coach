"""英雄的社区叫法与英文缩写。

数据放在 ``data/hero_nicknames.json``，格式为 ``{short: "社区名|英文缩写"}``。
社区名和官方中文名重复时留空即可；英文缩写没有就写空字符串。
"""

from __future__ import annotations

import json
from pathlib import Path


def load_nicknames(path: Path | str | None) -> dict[str, str]:
    """读取并拼成展示用的字符串（如 ``小鱼人 · Slark``、``SF``）。"""
    if path is None:
        return {}
    file = Path(path)
    if not file.exists():
        return {}
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out: dict[str, str] = {}
    for short, value in raw.items():
        if not isinstance(value, str):
            continue
        nick, _, abbr = value.partition("|")
        nick = nick.strip()
        abbr = abbr.strip()
        if nick and abbr and nick != abbr:
            out[short] = f"{nick} · {abbr}"
        else:
            out[short] = nick or abbr
    return out
