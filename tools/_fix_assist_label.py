"""修正 assist 标签在 ru/tr/de 的译法。"""

from pathlib import Path

p = Path("src/dota2coach/i18n.py")
s = p.read_text(encoding="utf-8")
s = s.replace('"help": "Помощь"', '"help": "Справка"')
s = s.replace('"tab_assist": "Помощь"', '"tab_assist": "Подсказки"')
s = s.replace('"tab_assist": "Yardım"', '"tab_assist": "İpuçları"')
s = s.replace('"tab_assist": "Helfer"', '"tab_assist": "Assistenz"')
p.write_text(s, encoding="utf-8")
print("labels fixed")
