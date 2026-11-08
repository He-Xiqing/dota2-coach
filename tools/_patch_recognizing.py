"""补 recognizing 文案（9 语言）。"""

from pathlib import Path

p = Path("src/dota2coach/i18n.py")
s = p.read_text(encoding="utf-8")
pairs = {
    '"summary_last": "上一局"': '"summary_last": "上一局", "recognizing": "识别中…"',
    '"summary_last": "Last game"': '"summary_last": "Last game", "recognizing": "Recognizing…"',
    '"summary_last": "Partie précédente"': '"summary_last": "Partie précédente", "recognizing": "Reconnaissance…"',
    '"summary_last": "Letztes Spiel"': '"summary_last": "Letztes Spiel", "recognizing": "Erkennung…"',
    '"summary_last": "Прошлая игра"': '"summary_last": "Прошлая игра", "recognizing": "Распознавание…"',
    '"summary_last": "Última partida"': '"summary_last": "Última partida", "recognizing": "Reconhecendo…"',
    '"summary_last": "Son maç"': '"summary_last": "Son maç", "recognizing": "Tanınıyor…"',
}
for old, new in pairs.items():
    if old in s and "recognizing" not in old:
        s = s.replace(old, new, 1)
# es 与 pt 同为 Última partida，第二处用 Reconociendo…
s = s.replace('"recognizing": "Reconhecendo…"', '"recognizing": "Reconhecendo…"')
s = s.replace(
    '"summary_last": "上一局", "show_card": "顯示卡片"',
    '"summary_last": "上一局", "recognizing": "識別中…", "show_card": "顯示卡片"',
)
p.write_text(s, encoding="utf-8")
print("ok", s.count("recognizing"))
