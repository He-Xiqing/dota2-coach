"""当前 Dota 2 版本号：从 Steam 新闻里取，带本地缓存。

只有版本号匹配当前版本的攻略才会被采纳，避免把 7.40 的思路套到 7.41 上。
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Protocol

STEAM_NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
NEWS_APP_ID = 570

_PATCH_RE = re.compile(r"\b(7\.\d{1,2}[a-z]?)\b", re.IGNORECASE)


class HttpLike(Protocol):  # pragma: no cover - 类型提示
    def get(self, url: str, params: dict | None = None) -> object: ...


def find_patch(text: str) -> str | None:
    """从一段文本里取第一个像 Dota 版本的标记，如 '7.41f'。"""
    match = _PATCH_RE.search(text or "")
    return match.group(1).lower() if match else None


def _latest_patch(payload: dict) -> str | None:
    news = ((payload or {}).get("appnews") or {}).get("newsitems") or []
    best: tuple[int, str] | None = None
    for item in news:
        if not isinstance(item, dict):
            continue
        text = f"{item.get('title') or ''}\n{item.get('contents') or ''}"
        patch = find_patch(text)
        if patch is None:
            continue
        stamp = int(item.get("date") or 0)
        if best is None or stamp > best[0]:
            best = (stamp, patch)
    return best[1] if best else None


def current_patch(
    cache_path: Path | None = None,
    *,
    ttl_hours: float = 12.0,
    http: HttpLike | None = None,
    now: float | None = None,
) -> str:
    """返回当前版本号；取不到时回退到缓存，再回退空串。"""
    now = time.time() if now is None else now
    cache = cache_path or Path("data/patch.json")
    if cache.exists():
        try:
            raw = json.loads(cache.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            raw = {}
        fetched = float(raw.get("fetched_at") or 0)
        patch = str(raw.get("patch") or "")
        if patch and now - fetched < ttl_hours * 3600:
            return patch

    if http is None:  # pragma: no cover - 真实网络
        import httpx

        http = httpx.Client(timeout=10.0, follow_redirects=True)

    try:
        response = http.get(  # type: ignore[union-attr]
            STEAM_NEWS_URL,
            params={"appid": NEWS_APP_ID, "count": 12, "maxlength": 800},
        )
        payload = response.json() if callable(getattr(response, "json", None)) else response  # type: ignore[union-attr]
        patch = _latest_patch(payload if isinstance(payload, dict) else {})
    except Exception:  # noqa: BLE001 - 网络问题不该阻塞整批
        patch = None

    if patch:
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(
                json.dumps({"patch": patch, "fetched_at": now}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass
        return patch

    if cache.exists():
        try:
            raw = json.loads(cache.read_text(encoding="utf-8-sig"))
            return str(raw.get("patch") or "")
        except (OSError, json.JSONDecodeError):
            return ""
    return ""
