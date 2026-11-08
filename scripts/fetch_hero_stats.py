"""抓取 OpenDota 的英雄数据（角色 + 各分段胜率），生成 data/hero_meta.json。

数据来自公开对局的持续统计，不需要 API key，也不需要 OpenDota 账号。
用法：
    .\\.venv\\Scripts\\python.exe scripts\\fetch_hero_stats.py
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

URL = "http://api.opendota.com/api/heroStats"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "hero_meta.json"


def _sum_brackets(row: dict, field: str, indexes: tuple[int, ...]) -> int:
    total = 0
    for index in indexes:
        try:
            total += int(row.get(f"{index}_{field}") or 0)
        except (TypeError, ValueError):
            continue
    return total


def main() -> int:
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "dota2-coach/0.1 (personal training tool)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - 公开数据
        rows = json.loads(response.read().decode("utf-8"))
    if not isinstance(rows, list) or len(rows) < 50:
        print(f"英雄数据异常：{type(rows).__name__} len={len(rows) if hasattr(rows, '__len__') else '?'}")
        return 1

    heroes: dict[str, dict] = {}
    for row in rows:
        try:
            hero_id = int(row["id"])
        except (KeyError, TypeError, ValueError):
            continue
        picks = _sum_brackets(row, "pick", tuple(range(1, 9)))
        wins = _sum_brackets(row, "win", tuple(range(1, 9)))
        high_picks = _sum_brackets(row, "pick", (7, 8))
        high_wins = _sum_brackets(row, "win", (7, 8))
        pro_picks = int(row.get("pro_pick") or 0)
        pro_wins = int(row.get("pro_win") or 0)
        heroes[str(hero_id)] = {
            "name": row.get("name") or "",
            "localized_name": row.get("localized_name") or "",
            "roles": list(row.get("roles") or []),
            "pub_picks": picks,
            "pub_wins": wins,
            "pub_winrate": round(wins / picks, 4) if picks else 0.0,
            "high_picks": high_picks,
            "high_wins": high_wins,
            "high_winrate": round(high_wins / high_picks, 4) if high_picks else 0.0,
            "pro_picks": pro_picks,
            "pro_wins": pro_wins,
            "pro_winrate": round(pro_wins / pro_picks, 4) if pro_picks else 0.0,
        }

    payload = {"source": URL, "heroes": heroes}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"heroes: {len(heroes)} -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
