"""修正 texts.py 末尾 improve_good 块（避免 PowerShell 引号问题）。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "src/dota2coach/coach/texts.py"
text = path.read_text(encoding="utf-8")
marker = "\n_EXTRA2 = {"
if marker in text:
    text = text[: text.index(marker)].rstrip() + "\n"

extra = {
    "zh-CN": "数据很稳：保持这个补刀和参团节奏",
    "zh-TW": "數據很穩：保持這個補刀和參團節奏",
    "en": "Solid numbers: keep this farm and teamfight pace",
    "fr": "Chiffres solides : gardez ce farm et ce rythme de fights",
    "ru": "Стабильные цифры: держите этот фарм и темп драк",
    "de": "Solide Werte: behalte dieses Farm- und Fight-Tempo",
    "pt": "Números sólidos: mantenha esse farm e ritmo de lutas",
    "es": "Números sólidos: mantén este farmeo y ritmo de peleas",
    "tr": "Sağlam veriler: bu farm ve savaş temposunu koru",
}

lines = ["", "_EXTRA2 = {"]
for lang, value in extra.items():
    lines.append(f"    {lang!r}: {{'improve_good': {value!r}}},")
lines += [
    "}",
    "for _lang, _extra in _EXTRA2.items():",
    "    TEXTS.setdefault(_lang, {}).update(_extra)",
    "",
]
path.write_text(text + "\n".join(lines), encoding="utf-8")
print("fixed")
