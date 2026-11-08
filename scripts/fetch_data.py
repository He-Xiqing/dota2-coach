"""从 Dota 2 官方 datafeed 拉英雄/物品数据（含简体中文名），写入 data/。

用法（项目根目录）：

    python scripts/fetch_data.py           # 下载 heroes + items
    python scripts/fetch_data.py --check   # 只看本地已有数据，不联网

数据来源：https://www.dota2.com/datafeed/herolist?language=schinese
          https://www.dota2.com/datafeed/itemlist?language=schinese
这两份接口不需要 API key，返回的是游戏客户端同源的本地化名称。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HERO_URL = "https://www.dota2.com/datafeed/herolist?language=schinese"
DEFAULT_ITEM_URL = "https://www.dota2.com/datafeed/itemlist?language=schinese"
USER_AGENT = "dota2coach/0.1 (local trainer overlay)"


def fetch_json(url: str, timeout: float = 30.0, retries: int = 3) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            print(f"  第 {attempt}/{retries} 次失败: {exc}")
            if attempt < retries:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"下载失败: {url} ({last_error})")


def unwrap(payload: dict, key: str) -> list:
    data = payload.get("result", {}).get("data", {})
    items = data.get(key) or []
    if not items:
        raise ValueError(f"响应里没有 {key} 字段，接口可能改版了")
    return items


def normalize_heroes(payload: dict) -> dict:
    heroes = []
    for hero in unwrap(payload, "heroes"):
        heroes.append({
            "id": hero.get("id"),
            "name": hero.get("name"),
            "name_zh": hero.get("name_loc"),
            "name_en": hero.get("name_english_loc"),
            "primary_attr": hero.get("primary_attr"),
            "complexity": hero.get("complexity"),
        })
    return {"count": len(heroes), "heroes": heroes}


def normalize_items(payload: dict) -> dict:
    items = []
    for item in unwrap(payload, "itemabilities"):
        name = item.get("name") or ""
        if not name:
            continue
        items.append({
            "id": item.get("id"),
            "name": name,
            "name_zh": item.get("name_loc"),
            "name_en": item.get("name_english_loc"),
            "neutral_tier": item.get("neutral_item_tier"),
            "innate": bool(item.get("is_innate")),
            "recipes": [
                entry.get("items", [])
                for entry in (item.get("recipes") or [])
            ],
        })
    return {"count": len(items), "items": items}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def check_only(data_dir: Path) -> int:
    ok = True
    for name, key in (("heroes.json", "heroes"), ("items.json", "items")):
        path = data_dir / name
        if not path.exists():
            print(f"[缺失] {path}")
            ok = False
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        print(f"[已有] {name}: {data.get('count', len(data.get(key, [])))} 条，生成于 {data.get('generated_at', '?')}")
    if not ok:
        print("先运行: python scripts/fetch_data.py")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="下载 Dota 2 官方英雄/物品数据")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--heroes-url", default=DEFAULT_HERO_URL)
    parser.add_argument("--items-url", default=DEFAULT_ITEM_URL)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--check", action="store_true", help="只检查本地数据")
    args = parser.parse_args(argv)

    if args.check:
        return check_only(args.data_dir)

    generated_at = datetime.now().isoformat(timespec="seconds")
    try:
        print("拉取英雄列表 ...")
        heroes = normalize_heroes(fetch_json(args.heroes_url, timeout=args.timeout))
        heroes.update({"generated_at": generated_at, "source": args.heroes_url})
        write_json(args.data_dir / "heroes.json", heroes)
        print(f"  ok: {heroes['count']} 个英雄")

        print("拉取物品列表 ...")
        items = normalize_items(fetch_json(args.items_url, timeout=args.timeout))
        items.update({"generated_at": generated_at, "source": args.items_url})
        write_json(args.data_dir / "items.json", items)
        print(f"  ok: {items['count']} 个物品")
    except (RuntimeError, ValueError) as exc:
        print(f"\n[失败] {exc}")
        print("如果你的网络访问不了 dota2.com，可以先用内置的 data/*.json 离线跑；")
        print("或者把这段报错发给我，我确认接口是否改版。")
        return 1

    sample = heroes["heroes"][:3]
    print("中文名示例: " + " / ".join(f"{h['name_zh']}({h['id']})" for h in sample))
    print(f"写入目录: {args.data_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
