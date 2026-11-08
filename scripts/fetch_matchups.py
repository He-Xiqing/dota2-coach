"""从 OpenDota 拉"英雄之间的对位胜率"（不需要 API key）。

接口：GET http://api.opendota.com/api/heroes/{hero_id}/matchups
返回：[{"hero_id": 11, "games_played": 12345, "wins": 6789}, ...]

输出 data/matchups.json：
    {"1": {"11": [12345, 6789], ...}, ...}   # 我方英雄 -> 敌方英雄 -> [场次, 胜场]

用法：python scripts/fetch_matchups.py [--limit 20] [--sleep 1.0]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
API = "http://api.opendota.com/api/heroes/{hero_id}/matchups"


def fetch(hero_id: int, timeout: float = 20.0) -> dict[int, list[int]]:
    request = urllib.request.Request(API.format(hero_id=hero_id), headers={"User-Agent": "dota2-coach"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - 固定 http 地址
        rows = json.loads(response.read().decode("utf-8"))
    table: dict[int, list[int]] = {}
    for row in rows:
        try:
            enemy = int(row["hero_id"])
            games = int(row.get("games_played") or 0)
            wins = int(row.get("wins") or 0)
        except (KeyError, TypeError, ValueError):
            continue
        table[enemy] = [games, wins]
    return table


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="只拉前 N 个英雄（调试用）")
    parser.add_argument("--sleep", type=float, default=1.0, help="每次请求间隔秒数")
    parser.add_argument("--missing", action="store_true", help="只补抓本地还没有数据的英雄")
    args = parser.parse_args()

    heroes_path = DATA / "heroes.json"
    if not heroes_path.exists():
        print("缺少 data/heroes.json", file=sys.stderr)
        return 1
    heroes = json.loads(heroes_path.read_text(encoding="utf-8-sig"))
    ids = sorted(int(key) for key in heroes)
    if args.limit:
        ids = ids[: args.limit]

    out_path = DATA / "matchups.json"
    existing: dict[str, dict[str, list[int]]] = {}
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            existing = {}

    done = 0
    for hero_id in ids:
        if args.missing and str(hero_id) in existing and existing[str(hero_id)]:
            continue
        try:
            table = fetch(hero_id)
        except Exception as exc:  # noqa: BLE001
            print(f"[fail] {hero_id}: {exc}", file=sys.stderr)
            continue
        existing[str(hero_id)] = {str(k): v for k, v in table.items()}
        done += 1
        if done % 20 == 0:
            print(f"  ... {done}/{len(ids)}", flush=True)
        time.sleep(max(0.0, args.sleep))

    out_path.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
    print(f"done: {done} heroes -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
