"""把一份 GSI 原始报文（logs/gsi_raw/*.jsonl）整理成人类可读的结构报告。

用途：确认官方 GSI 到底下发哪些字段（尤其 draft / events / map），
而不是靠猜测去设计选人推荐和团战提醒。

用法:
    python tools/inspect_capture.py logs/gsi_raw/9079443351-20261107-112141.jsonl
    python tools/inspect_capture.py <file> --samples 0     # 只看统计，不打印样例
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and isinstance(item.get("payload"), dict):
                records.append(item["payload"])
            elif isinstance(item, dict):
                records.append(item)
    return records


def brief(value, limit: int = 900) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2)
    if len(text) > limit:
        text = text[:limit] + f"\n... (截断，共 {len(text)} 字符)"
    return text


def first_where(records: list[dict], predicate) -> dict | None:
    for record in records:
        if predicate(record):
            return record
    return None


def last_where(records: list[dict], predicate) -> dict | None:
    for record in reversed(records):
        if predicate(record):
            return record
    return None


def event_type(entry: dict) -> str:
    raw = entry.get("data")
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return "unparsed"
        if isinstance(decoded, dict):
            return str(decoded.get("type") or decoded.get("event_type") or "?")
    return str(entry.get("event_type") or "?")


def report(path: Path, samples: int) -> None:
    records = load_records(path)
    if not records:
        print(f"{path}: 没有可用记录")
        return

    print(f"文件      : {path}")
    print(f"报文条数  : {len(records)}")
    print()

    combos = Counter(tuple(sorted(k for k in r.keys())) for r in records)
    print("== 顶层字段组合 ==")
    for combo, count in combos.most_common(8):
        print(f"  {count:6d}  {', '.join(combo)}")
    print()

    states = Counter((r.get("map") or {}).get("game_state") for r in records if r.get("map"))
    print("== game_state 分布 ==")
    for state, count in states.most_common():
        print(f"  {count:6d}  {state}")
    print()

    times = [g for g in ((r.get("map") or {}).get("game_time") for r in records) if isinstance(g, int)]
    if times:
        print(f"== 比赛时间 ==  {min(times)}s .. {max(times)}s")
        print()

    # draft：关键在于"字段在不在"，而不在真假值
    draft_total = sum(1 for r in records if "draft" in r)
    draft_nonempty = [r for r in records if r.get("draft")]
    print("== draft ==")
    print(f"  带 draft 字段的报文: {draft_total} / {len(records)}")
    print(f"  其中非空: {len(draft_nonempty)}")
    if draft_nonempty and samples:
        print(brief(draft_nonempty[0]["draft"]))
    print()

    # events：跨所有报文聚合，data 是 JSON 字符串
    event_counter: Counter[str] = Counter()
    event_records = 0
    per_record = []
    for record in records:
        events = record.get("events")
        if isinstance(events, list) and events:
            event_records += 1
            per_record.append(len(events))
            for entry in events:
                if isinstance(entry, dict):
                    event_counter[event_type(entry)] += 1
    print("== events ==")
    print(f"  带事件的报文: {event_records}，单条事件数 {min(per_record) if per_record else 0}..{max(per_record) if per_record else 0}")
    for name, count in event_counter.most_common(15):
        print(f"    {count:6d}  {name}")
    if samples:
        sample = first_where(records, lambda r: bool(r.get("events")))
        if sample:
            print("  样例:")
            print(brief(sample["events"][:2], 700))
    print()

    # added：GSI 只推送"新增实体"，团战/视野相关可能在这里
    added_records = [r for r in records if "added" in r]
    print("== added ==")
    print(f"  带 added 字段的报文: {len(added_records)}")
    if added_records and samples:
        added = added_records[0]["added"]
        print(f"  顶层键: {sorted(added.keys()) if isinstance(added, dict) else type(added).__name__}")
        print(brief(added, 800))
    print()

    # map
    map_rec = last_where(records, lambda r: bool(r.get("map")))
    print("== map ==")
    if map_rec is None:
        print("  没有 map 字段")
    else:
        map_data = map_rec["map"]
        print(f"  字段: {sorted(map_data.keys())}")
        if samples:
            keep = {k: map_data.get(k) for k in
                    ("name", "matchid", "game_state", "game_time", "daytime",
                     "roshan_state", "radiant_score", "dire_score", "clock_time",
                     "nightstalker_night", "ward_purchase_cooldown", "win_team")
                    if k in map_data}
            print(brief(keep, 600))
    print()

    # hero / items / abilities：取一条真正在局内的报文
    in_game = last_where(records, lambda r: (r.get("hero") or {}).get("id"))
    print("== hero / items / abilities（取局内报文）==")
    if in_game is None:
        print("  没有 hero.id 非 0 的报文")
    else:
        hero = in_game["hero"]
        print(f"  hero 字段: {sorted(hero.keys())}")
        print(f"  id={hero.get('id')} name={hero.get('name')} level={hero.get('level')} "
              f"alive={hero.get('alive')} buyback={hero.get('buyback_cost')} "
              f"pos=({hero.get('xpos')},{hero.get('ypos')})")
        # 注意：abilities 是顶层字段，不在 hero 里面
        abilities = in_game.get("abilities") or {}
        print(f"  abilities 槽位: {sorted(abilities.keys())}")
        if abilities:
            ability = next(iter(abilities.values()))
            print(f"  ability 字段: {sorted(ability.keys())}")
            if samples:
                print(brief(ability, 600))
        items = in_game.get("items") or {}
        print(f"  items 槽位: {sorted(items.keys())}")
        filled = {k: v for k, v in items.items() if v}
        print(f"  非空槽位: {len(filled)}")
        if samples and filled:
            key = next(iter(filled))
            print(f"  物品样例 ({key}):")
            print(brief(filled[key], 600))
    print()

    # player
    player_rec = last_where(records, lambda r: bool(r.get("player")))
    if player_rec is not None:
        player = player_rec["player"]
        print("== player ==")
        print(f"  字段: {sorted(player.keys())}")
        keep = {k: player.get(k) for k in
                ("steamid", "name", "team_name", "team_slot", "player_slot", "activity") if k in player}
        print(f"  {json.dumps(keep, ensure_ascii=False)}")
        print()

    # buildings
    buildings_rec = last_where(records, lambda r: bool(r.get("buildings")))
    if buildings_rec is not None:
        buildings = buildings_rec["buildings"]
        print("== buildings ==")
        print(f"  队伍: {sorted(buildings.keys())}")
        for team, data in buildings.items():
            if isinstance(data, dict):
                print(f"  {team} 字段: {sorted(data.keys())[:12]}")
                tower = (data.get("towers") or {})
                if tower:
                    sample = next(iter(tower.items()))
                    print(f"  {team} 塔样例 {sample[0]}: {json.dumps(sample[1], ensure_ascii=False)[:200]}")
        print()

    prev_rec = first_where(records, lambda r: bool(r.get("previously")))
    if prev_rec is not None:
        print("== previously ==")
        print(f"  字段: {sorted(prev_rec['previously'].keys())}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--samples", type=int, default=1,
                        help="是否打印样例 JSON（0 = 不打印）")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass
    if not args.file.exists():
        print(f"文件不存在: {args.file}")
        return 1
    report(args.file, args.samples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
