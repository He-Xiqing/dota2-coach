"""把 OpenDota 的 constants/items 原始数据整理成 data/items.json。

用法：
    curl.exe -sS -o data/_items_raw.json "http://api.opendota.com/api/constants/items"
    python scripts/build_item_table.py

输出：
    {"by_id": {"1": {"name": "item_blink", "dname": "Blink Dagger",
                     "created": true, "cost": 2250}},
     "by_name": {"item_blink": "Blink Dagger"}}
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main() -> int:
    raw_path = DATA / "_items_raw.json"
    if not raw_path.exists():
        print(f"缺少 {raw_path}，先下载 constants/items")
        return 1
    raw = json.loads(raw_path.read_text(encoding="utf-8-sig"))
    by_id: dict[str, dict[str, object]] = {}
    by_name: dict[str, str] = {}
    for internal, entry in raw.items():
        if not isinstance(entry, dict) or "id" not in entry:
            continue
        dname = str(entry.get("dname") or entry.get("dn") or internal)
        by_id[str(entry["id"])] = {
            "name": internal,
            "dname": dname,
            "created": bool(entry.get("created", False)),
            "cost": int(entry.get("cost") or 0),
        }
        by_name[internal] = dname
    out = DATA / "items.json"
    out.write_text(json.dumps({"by_id": by_id, "by_name": by_name}, ensure_ascii=False), encoding="utf-8")
    print(f"items: {len(by_id)} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
