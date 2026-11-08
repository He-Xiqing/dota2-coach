"""抓取 9 语言物品名（dota2.com datafeed itemlist → itemabilities）。"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.dota2.com/datafeed/itemlist?language={language}"
LANGS = {
    "english": "en",
    "tchinese": "zh-TW",
    "french": "fr",
    "russian": "ru",
    "german": "de",
    "brazilian": "pt",
    "spanish": "es",
    "turkish": "tr",
}


def fetch(language: str) -> dict[str, str]:
    req = urllib.request.Request(
        URL.format(language=language), headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = data.get("result", {}).get("data", {}).get("itemabilities", [])
    names: dict[str, str] = {}
    for item in items:
        name = (item.get("name") or "").strip()
        loc = (item.get("name_loc") or "").strip()
        if not name or not loc:
            continue
        if not name.startswith("item_"):
            name = "item_" + name
        names[name] = loc
    return names


def main() -> None:
    out_dir = ROOT / "data"
    for feed, lang in LANGS.items():
        try:
            names = fetch(feed)
            path = out_dir / f"item_names.{lang}.json"
            path.write_text(json.dumps(names, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{lang}: {len(names)} -> {path.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"{lang}: FAILED {exc}")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
