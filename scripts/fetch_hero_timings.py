"""抓 OpenDota 的“按对局时长分桶”数据，算出每个英雄的强势期。

数据源：https://api.opendota.com/api/heroes/{id}/durations
返回若干 {duration_bin, games_played, wins}，用场次加权算早/中/晚胜率。

输出 data/hero_timing.json：
  {"11": {"early": 0.52, "mid": 0.49, "late": 0.47, "label": "前期", "games": 30971}}

用法：
  python scripts/fetch_hero_timings.py            # 全量
  python scripts/fetch_hero_timings.py --missing  # 只补缺的
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://api.opendota.com/api/heroes/{hid}/durations"
OUT = ROOT / "data" / "hero_timing.json"
UA = "dota2-coach/0.1 (personal training tool)"

EARLY_END = 1500  # 25 分钟
MID_END = 2700  # 45 分钟


def fetch(hero_id: int, timeout: float = 20.0) -> list[dict]:
    req = urllib.request.Request(URL.format(hid=hero_id), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def weighted(bins: list[dict], lo: float, hi: float) -> tuple[int, float]:
    games = wins = 0
    for item in bins:
        duration = float(item.get("duration_bin") or 0)
        n = int(item.get("games_played") or 0)
        if lo <= duration < hi and n > 0:
            games += n
            wins += int(item.get("wins") or 0)
    if games <= 0:
        return 0, 0.0
    return games, wins / games


def label_for(early: float, mid: float, late: float, games: int) -> str:
    if games < 500:
        return "数据少"
    best = max(early, mid, late)
    gap = 0.015
    if best == early and early - mid >= gap:
        return "前期"
    if best == late and late - mid >= gap:
        return "后期"
    if mid >= max(early, late):
        return "中期"
    return "均衡"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--missing", action="store_true", help="只补本地没有的英雄")
    parser.add_argument("--heroes", help="逗号分隔的 hero id，调试用")
    args = parser.parse_args()

    heroes_path = ROOT / "data" / "heroes.json"
    heroes = json.loads(heroes_path.read_text(encoding="utf-8-sig"))
    ids = [int(k) for k in heroes.keys()]
    if args.heroes:
        ids = [int(x) for x in args.heroes.split(",") if x.strip()]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, dict] = {}
    if OUT.exists():
        existing = json.loads(OUT.read_text(encoding="utf-8"))
    if args.missing:
        ids = [hid for hid in ids if str(hid) not in existing]

    done = 0
    failed = 0
    for index, hid in enumerate(ids, 1):
        try:
            bins = fetch(hid)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"[{index}/{len(ids)}] {hid} 失败：{exc}")
            time.sleep(1.0)
            continue
        early_games, early = weighted(bins, 0, EARLY_END)
        mid_games, mid = weighted(bins, EARLY_END, MID_END)
        late_games, late = weighted(bins, MID_END, 10**9)
        total = early_games + mid_games + late_games
        entry = {
            "early": round(early, 4),
            "mid": round(mid, 4),
            "late": round(late, 4),
            "label": label_for(early, mid, late, total),
            "games": total,
        }
        existing[str(hid)] = entry
        done += 1
        if index % 10 == 0 or index == len(ids):
            OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"[{index}/{len(ids)}] {hid} {entry['label']} games={total}")
        time.sleep(0.6)

    OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"done: {done} 成功, {failed} 失败 -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
