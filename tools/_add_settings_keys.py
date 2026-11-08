"""给 i18n 追加设置页标签（9 语言）。"""

from pathlib import Path

EXTRA = {
    "zh-CN": {
        "tab_language": "语言",
        "tab_theme": "主题",
        "tab_overlay": "覆盖层",
        "tab_voice": "语音",
        "tab_assist": "辅助",
        "tab_hotkey": "快捷键",
        "save": "保存",
        "cancel": "取消",
        "settings_note": "保存后立即生效；GSI 端口等少数项需要重启程序。",
    },
    "zh-TW": {
        "tab_language": "語言",
        "tab_theme": "主題",
        "tab_overlay": "覆蓋層",
        "tab_voice": "語音",
        "tab_assist": "輔助",
        "tab_hotkey": "快速鍵",
        "save": "儲存",
        "cancel": "取消",
        "settings_note": "儲存後立即生效；GSI 連接埠等少數項目需要重新啟動程式。",
    },
    "en": {
        "tab_language": "Language",
        "tab_theme": "Theme",
        "tab_overlay": "Overlay",
        "tab_voice": "Voice",
        "tab_assist": "Assist",
        "tab_hotkey": "Hotkeys",
        "save": "Save",
        "cancel": "Cancel",
        "settings_note": "Applies immediately; a few items (GSI port) need a restart.",
    },
    "fr": {
        "tab_language": "Langue",
        "tab_theme": "Thème",
        "tab_overlay": "Overlay",
        "tab_voice": "Voix",
        "tab_assist": "Assistance",
        "tab_hotkey": "Raccourcis",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "settings_note": "Appliqué immédiatement ; le port GSI nécessite un redémarrage.",
    },
    "ru": {
        "tab_language": "Язык",
        "tab_theme": "Тема",
        "tab_overlay": "Оверлей",
        "tab_voice": "Голос",
        "tab_assist": "Помощь",
        "tab_hotkey": "Горячие клавиши",
        "save": "Сохранить",
        "cancel": "Отмена",
        "settings_note": "Применяется сразу; для порта GSI нужен перезапуск.",
    },
    "de": {
        "tab_language": "Sprache",
        "tab_theme": "Design",
        "tab_overlay": "Overlay",
        "tab_voice": "Stimme",
        "tab_assist": "Helfer",
        "tab_hotkey": "Tasten",
        "save": "Speichern",
        "cancel": "Abbrechen",
        "settings_note": "Gilt sofort; GSI-Port braucht einen Neustart.",
    },
    "pt": {
        "tab_language": "Idioma",
        "tab_theme": "Tema",
        "tab_overlay": "Sobreposição",
        "tab_voice": "Voz",
        "tab_assist": "Assistência",
        "tab_hotkey": "Atalhos",
        "save": "Salvar",
        "cancel": "Cancelar",
        "settings_note": "Aplica na hora; a porta GSI exige reiniciar.",
    },
    "es": {
        "tab_language": "Idioma",
        "tab_theme": "Tema",
        "tab_overlay": "Superposición",
        "tab_voice": "Voz",
        "tab_assist": "Asistencia",
        "tab_hotkey": "Atajos",
        "save": "Guardar",
        "cancel": "Cancelar",
        "settings_note": "Se aplica al momento; el puerto GSI requiere reinicio.",
    },
    "tr": {
        "tab_language": "Dil",
        "tab_theme": "Tema",
        "tab_overlay": "Katman",
        "tab_voice": "Ses",
        "tab_assist": "Yardım",
        "tab_hotkey": "Kısayollar",
        "save": "Kaydet",
        "cancel": "İptal",
        "settings_note": "Hemen uygulanır; GSI bağlantı noktası yeniden başlatma ister.",
    },
}

lines = ["_SETTINGS = {"]
for code, values in EXTRA.items():
    lines.append(f'    "{code}": {{')
    for key, value in values.items():
        lines.append(f'        "{key}": "{value}",')
    lines.append("    },")
lines.append("}")
lines.append("for _lang, _vals in _SETTINGS.items():")
lines.append("    _STRINGS.setdefault(_lang, {}).update(_vals)")
lines.append("")

block = "\n".join(lines) + "\n"

p = Path("src/dota2coach/i18n.py")
s = p.read_text(encoding="utf-8")
if "_SETTINGS" in s:
    raise SystemExit("already patched")
anchor = "def normalize_language("
if anchor not in s:
    raise SystemExit("anchor missing")
s = s.replace(anchor, block + anchor, 1)
p.write_text(s, encoding="utf-8")
print("added settings keys")
