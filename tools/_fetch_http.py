"""临时脚本：用明文 HTTP 从 Steam CDN 下载英雄图标/卡面（我的沙箱没有 TLS 凭据）。"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UA = {"User-Agent": "Mozilla/5.0"}

ICON = "http://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/icons/{}.png"
CARD = "http://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{}.png"


def download(url: str, path: Path) -> bool:
    if path.exists() and path.stat().st_size > 100:
        return True
    try:
        request = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
        if len(payload) < 100:
            return False
        path.write_bytes(payload)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  ! {path.name}: {exc}")
        return False


def main() -> int:
    table = json.loads((DATA / "heroes.json").read_text(encoding="utf-8-sig"))
    icons = DATA / "hero_icons"
    cards = DATA / "hero_cards"
    icons.mkdir(parents=True, exist_ok=True)
    cards.mkdir(parents=True, exist_ok=True)

    bad_icons, bad_cards = [], []
    for index, (hero_id, info) in enumerate(sorted(table.items(), key=lambda kv: int(kv[0])), 1):
        short = info["short"]
        if not download(ICON.format(short), icons / f"{short}.png"):
            bad_icons.append(short)
        if not download(CARD.format(short), cards / f"{short}.png"):
            bad_cards.append(short)
        if index % 25 == 0:
            print(f"  {index}/{len(table)}")

    print(f"icons: {len(list(icons.glob('*.png')))}  cards: {len(list(cards.glob('*.png')))}")
    if bad_icons:
        print("icon failures:", ", ".join(bad_icons))
    if bad_cards:
        print("card failures:", ", ".join(bad_cards))
    return 0


if __name__ == "__main__":
    sys.exit(main())
