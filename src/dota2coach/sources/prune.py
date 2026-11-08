"""攻略库清理：删掉噪声/重复/过旧/无归属的提示，避免越攒越脏。"""

from __future__ import annotations

import json
import time
from pathlib import Path

# 评论/弹幕里常见的噪声词，出现在提示里基本就是“垃圾”
GARBAGE_MARKERS = (
    "抽奖",
    "三连",
    "关注我",
    "点个关注",
    "加群",
    "qq群",
    "QQ群",
    "直播间",
    "笑死",
    "师傅别念",
    "别念了",
    "啊啊啊",
    "前排",
)

MIN_TEXT = 6


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def tip_is_garbage(tip: dict, hero_shorts: set[str]) -> bool:
    text = str(tip.get("text") or "").strip()
    if len(text) < MIN_TEXT:
        return True
    if any(marker in text for marker in GARBAGE_MARKERS):
        return True
    hero = str(tip.get("hero") or "")
    if not hero:
        return True
    if hero_shorts and hero not in hero_shorts:
        return True
    return False


def prune_payload(
    payload: dict,
    hero_shorts: set[str],
    *,
    max_age_days: int | None = 365,
    now: float | None = None,
) -> tuple[dict, dict[str, int]]:
    """返回 (清理后的 payload, 统计)。不修改入参。"""
    now = now if now is not None else time.time()
    tips = [tip for tip in (payload.get("tips") or []) if isinstance(tip, dict)]
    videos = payload.get("videos") or {}
    if not isinstance(videos, dict):
        videos = {}

    fresh_bvids: set[str] = set()
    for bvid, video in videos.items():
        if not isinstance(video, dict):
            continue
        pubdate = _as_int(video.get("pubdate"))
        if max_age_days is not None and pubdate > 0 and now - pubdate > max_age_days * 86400:
            continue
        fresh_bvids.add(str(bvid))

    kept: list[dict] = []
    seen: set[tuple[str, str, str, str]] = set()
    dropped_garbage = dropped_old = dropped_dup = 0
    for tip in tips:
        if tip_is_garbage(tip, hero_shorts):
            dropped_garbage += 1
            continue
        sources = [str(s) for s in (tip.get("sources") or [])]
        if max_age_days is not None and sources and fresh_bvids:
            if not any(s in fresh_bvids for s in sources):
                dropped_old += 1
                continue
        key = (
            str(tip.get("hero") or ""),
            str(tip.get("lane") or "任意"),
            str(tip.get("phase") or "任意"),
            str(tip.get("text") or ""),
        )
        if key in seen:
            dropped_dup += 1
            continue
        seen.add(key)
        kept.append(tip)

    used_bvids = {str(s) for tip in kept for s in (tip.get("sources") or [])}
    pruned_videos = {bvid: video for bvid, video in videos.items() if str(bvid) in used_bvids}

    result = dict(payload)
    result["tips"] = kept
    result["videos"] = pruned_videos
    stats = {
        "kept": len(kept),
        "dropped_garbage": dropped_garbage,
        "dropped_old": dropped_old,
        "dropped_dup": dropped_dup,
        "videos": len(pruned_videos),
    }
    return result, stats


def prune_file(path: Path, hero_shorts: set[str], *, max_age_days: int | None = 365) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cleaned, stats = prune_payload(payload, hero_shorts, max_age_days=max_age_days)
    if stats["dropped_garbage"] or stats["dropped_old"] or stats["dropped_dup"] or stats["videos"] != len(payload.get("videos") or {}):
        path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=1), encoding="utf-8")
    return stats
