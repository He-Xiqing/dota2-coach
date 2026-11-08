"""修正 YouTube ytInitialData 的截取：用括号配平代替正则。"""

from pathlib import Path

p = Path("src/dota2coach/sources/youtube.py")
s = p.read_text(encoding="utf-8")

helper = '''

def _initial_data(html: str) -> str:
    """从页面里截出 ytInitialData 的 JSON（括号配平，避开字符串里的花括号）。"""
    index = (html or "").find("ytInitialData")
    if index < 0:
        return ""
    start = html.find("{", index)
    if start < 0:
        return ""
    depth = 0
    in_string = False
    escaped = False
    for pos in range(start, len(html)):
        char = html[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return html[start : pos + 1]
    return ""
'''

if "def _initial_data(" not in s:
    marker = "def parse_search(html: str) -> list[YtVideo]:"
    s = s.replace(marker, helper.strip() + "\n\n\n" + marker, 1)

old = '''    match = _INIT_RE.search(html or "")
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
    except ValueError:
        return []'''
new = '''    payload = _initial_data(html or "")
    if not payload:
        match = _INIT_RE.search(html or "")
        payload = match.group(1) if match else ""
    if not payload:
        return []
    try:
        data = json.loads(payload)
    except ValueError:
        return []'''
if old not in s:
    raise SystemExit("parse_search anchor missing")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("parse_search fixed")
