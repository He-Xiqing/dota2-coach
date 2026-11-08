"""从游戏自带的本地化文件里提取物品中文名。

数据来源：`data/abilities_schinese.txt`（从 pak01 VPK 里解出来的官方简体中文文本，
令牌形如 `"DOTA_Tooltip_Ability_item_blink" "闪烁匕首"`）。

输出 `data/item_names_zh.json`：{"item_blink": "闪烁匕首", ...}
用法：python scripts/build_item_names.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "abilities_schinese.txt"
TARGET = ROOT / "data" / "item_names_zh.json"

PAIR = re.compile(r'^\s*"([^"]+)"\s+"(.*)"\s*$')
TOKEN = re.compile(r"^dota_tooltip_ability_item_([a-z0-9_]+)$", re.IGNORECASE)
SKIP_SUFFIX = ("_description", "_lore", "_note", "_note0", "_note1", "_note2")


def main() -> int:
    if not SOURCE.exists():
        print(f"缺少 {SOURCE}（从 VPK 里解出的本地化文件）", file=sys.stderr)
        return 1
    mapping: dict[str, str] = {}
    for line in SOURCE.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        match = PAIR.match(line)
        if not match:
            continue
        token, value = match.group(1), match.group(2).strip()
        if not token.lower().startswith("dota_tooltip_ability_item_"):
            continue
        suffix = token.lower()
        if suffix.endswith(SKIP_SUFFIX) or not value:
            continue
        found = TOKEN.match(token)
        if not found:
            continue
        mapping[f"item_{found.group(1).lower()}"] = value
    TARGET.write_text(
        json.dumps(dict(sorted(mapping.items())), ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"items: {len(mapping)} -> {TARGET}")
    for probe in ("item_blink", "item_bfury", "item_manta", "item_black_king_bar"):
        print(f"  {probe}: {mapping.get(probe)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
