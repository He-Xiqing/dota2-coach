import re
from pathlib import Path

s = Path("src/dota2coach/i18n.py").read_text(encoding="utf-8")
m = re.search(r"_STRINGS: dict\[str, dict\[str, str\]\] = \{(.*?)\n\}", s, re.S)
keys = sorted(set(re.findall(r'"([a-z0-9_]+)":', m.group(1))))
print(len(keys))
print(", ".join(keys))
