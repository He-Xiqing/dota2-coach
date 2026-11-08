"""语音包下拉：显示“声音名 · 语言”，避免中文描述出现在英文界面。"""

from pathlib import Path

p = Path("src/dota2coach/ui/panel.py")
s = p.read_text(encoding="utf-8")
old = """        for pack in voices.packs_for_language(normalize_language(self._config.app.language)):
            self.pack.addItem(f"{pack.name} · {pack.desc}", pack.id)"""
new = """        for pack in voices.packs_for_language(normalize_language(self._config.app.language)):
            if pack.id == "custom":
                label = pack.name
            else:
                voice_name = pack.name.split(" · ")[0]
                lang_name = LANGUAGES.get(pack.lang, pack.lang)
                label = f"{voice_name} · {lang_name}"
            self.pack.addItem(label, pack.id)"""
if old in s:
    s = s.replace(old, new, 1)
if "LANGUAGES," not in s:
    s = s.replace(
        "from ..i18n import tr",
        "from ..i18n import LANGUAGES, tr",
        1,
    )
p.write_text(s, encoding="utf-8")
print("pack label patched")
