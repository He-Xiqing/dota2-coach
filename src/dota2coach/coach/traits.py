"""英雄自身的“克制能力”，避免推荐它本来就能解决的东西（比如小鱼人自带驱散）。"""

from __future__ import annotations

# 自带驱散：沉默/缠绕可以自己解，不必专门出分身/黑皇
SELF_DISPEL = {
    "slark",  # 黑暗契约
    "legion_commander",  # 压倒性优势后的强攻
    "abaddon",  # 无光之盾
    "oracle",  # 命运之诏
    "life_stealer",  # 狂暴（免控）
}

# 自带免控/魔免：先手威胁的优先级可以降低
SELF_IMMUNE = {
    "juggernaut",  # 剑刃风暴
    "life_stealer",  # 狂暴
    "omniknight",  # 守护天使（物免）
}


def has_self_dispel(short: str | None) -> bool:
    return bool(short) and short in SELF_DISPEL


def has_self_immune(short: str | None) -> bool:
    return bool(short) and short in SELF_IMMUNE
