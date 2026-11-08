from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "src/dota2coach/coach/texts.py"
text = path.read_text(encoding="utf-8")
old = '"encourage_win": "打得不错，保持这个节奏！"'
new = '"encourage_win": "这局打得不错，保持手感，继续上分！"'
if old in text:
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("updated")
else:
    print("anchor missing")
