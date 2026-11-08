"""拉取 OpenDota 的每个英雄物品出装热度，生成 data/popularity.json。

用法（需要外网，明文 HTTP 走 api.opendota.com）：
    python scripts/fetch_popularity.py            # 全量
    python scripts/fetch_popularity.py --limit 5  # 只拉 5 个（调试）

输出结构（物品键是**数字 id**）：
    {"38": {"start_game_items": {"22": 106, ...},
            "early_game_items": {...}, "mid_game_items": {...},
            "late_game_items": {...}}, ...}
只保留 count 最高的前 12 个物品，控制体积。
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
API = "http://api.opendota.com/api/heroes/{}/itemPopularity"
TOP_N = 12


def fetch(hero_id: int) -> dict | None:
    request = urllib.request.Request(API.format(hero_id), headers={"User-Agent": "dota2coach/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            return None
        return json.loads(response.read().decode("utf-8"))


def trim(group: dict) -> dict:
    items = sorted(group.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    return {name: count for name, count in items}


def main() -> int:
    parser = argparse.ArgumentParser(description="抓取 OpenDota 出装热度")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--force", action="store_true", help="已存在的英雄也重新抓（更新数据用）")
    args = parser.parse_args()

    table = json.loads((DATA / "heroes.json").read_text(encoding="utf-8-sig"))
    ids = sorted(int(k) for k in table)
    if args.limit:
        ids = ids[: args.limit]

    out_path = DATA / "popularity.json"
    result: dict[str, dict] = {}
    if out_path.exists():
        result = json.loads(out_path.read_text(encoding="utf-8"))

    failures = []
    for index, hero_id in enumerate(ids, 1):
        if not args.force and str(hero_id) in result:
            continue
        error = ""
        try:
            payload = fetch(hero_id)
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            payload = None
        if payload:
            result[str(hero_id)] = {key: trim(value) for key, value in payload.items()}
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            failures.append(f"{hero_id}:{error}" if error else str(hero_id))
        if index % 10 == 0:
            print(f"  {index}/{len(ids)}  ok={len(result)}", flush=True)
        time.sleep(args.sleep)

    print(f"done: {len(result)} heroes -> {out_path}", flush=True)
    if failures:
        print("failed:", ", ".join(failures), flush=True)
    return 0 if len(result) >= len(ids) * 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
