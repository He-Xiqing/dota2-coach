from pathlib import Path
import re

s = Path("src/dota2coach/i18n.py").read_text(encoding="utf-8")
print("lines", len(s.splitlines()))
for i, line in enumerate(s.splitlines()[:30], 1):
    print(i, line)
print("--- langs ---")
for m in re.finditer(r'^\s{4}"([a-zA-Z\-]+)":\s*\{', s, re.M):
    print(m.group(1))
print("--- keys in zh ---")
m = re.search(r'"zh":\s*\{(.*?)\n    \}', s, re.S)
if m:
    keys = re.findall(r'^\s{8}"([a-zA-Z0-9_]+)":', m.group(1), re.M)
    print(len(keys))
    print(keys)
