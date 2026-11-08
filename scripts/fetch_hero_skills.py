"""抓官方英雄资料（中文名 + 简介 + 技能简述），生成 data/hero_skills.json。

数据源：https://www.dota2.com/datafeed/herodata?language=schinese&hero_id=N
用法：
    python scripts\\fetch_hero_skills.py            # 增量：只补缺的英雄
    python scripts\\fetch_hero_skills.py --force    # 全量重抓
    python scripts\\fetch_hero_skills.py --heroes 1,2,3
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEROES = ROOT / "data" / "heroes.json"
OUT = ROOT / "data" / "hero_skills.json"
URL = "https://www.dota2.com/datafeed/herodata?language={language}&hero_id={hero_id}"
HEADERS = {"User-Agent": "dota2-coach/0.1 (personal training tool)"}
_TAG = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"\s+")
_PLACEHOLDER = re.compile(r"%[^%]{0,40}%")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(_TAG.sub("", str(value)))
    text = _PLACEHOLDER.sub("", text)
    return _SPACES.sub(" ", text).strip()


def fetch(hero_id: int, language: str = "schinese", timeout: float = 20.0) -> dict | None:
    req = urllib.request.Request(URL.format(hero_id=hero_id, language=language), headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    heroes = (((payload.get("result") or {}).get("data") or {}).get("heroes")) or []
    if not heroes:
        return None
    hero = heroes[0]
    abilities = []
    for ability in hero.get("abilities") or []:
        name = clean_text(ability.get("name_loc"))
        desc = clean_text(ability.get("desc_loc"))
        if name and desc:
            abilities.append({"name": name, "desc": desc})
    return {
        "name": clean_text(hero.get("name_loc")),
        "bio": clean_text(hero.get("bio_loc")),
        "abilities": abilities,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="抓取官方英雄技能资料")
    parser.add_argument("--force", action="store_true", help="已存在的英雄也重抓")
    parser.add_argument("--heroes", help="逗号分隔的 hero id，只抓这些")
    parser.add_argument("--interval", type=float, default=0.3)
    parser.add_argument("--language", default="schinese", help="datafeed 语言，如 english/french/russian")
    parser.add_argument("--out", default="", help="输出文件，默认按语言命名")
    args = parser.parse_args()

    global OUT
    if args.out:
        OUT = ROOT / args.out
    elif args.language != "schinese":
        OUT = ROOT / "data" / f"hero_skills.{args.language}.json"

    heroes = json.loads(HEROES.read_text(encoding="utf-8-sig"))
    existing: dict[str, dict] = {}
    if OUT.exists() and not args.force:
        existing = json.loads(OUT.read_text(encoding="utf-8-sig"))

    ids = [int(x) for x in args.heroes.split(",")] if args.heroes else sorted(int(k) for k in heroes)
    todo = [hero_id for hero_id in ids if args.force or str(hero_id) not in existing]
    print(f"英雄 {len(ids)} 个，待抓 {len(todo)} 个")
    failed: list[int] = []
    for index, hero_id in enumerate(todo, 1):
        info = fetch(hero_id, args.language)
        if info is None:
            failed.append(hero_id)
            print(f"[{index}/{len(todo)}] 失败：{hero_id}", file=sys.stderr)
        else:
            existing[str(hero_id)] = info
            print(f"[{index}/{len(todo)}] {info['name']}：{len(info['abilities'])} 个技能")
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(args.interval)

    print(f"完成：{len(existing)} 个英雄 -> {OUT}")
    if failed:
        print(f"失败 {len(failed)} 个：{failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
