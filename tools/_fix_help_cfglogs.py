"""修复 texts_help.py 尾部的 cfg_logs 块（此前被 PowerShell 写坏）。"""

from pathlib import Path

path = Path("src/dota2coach/coach/texts_help.py")
text = path.read_text(encoding="utf-8", errors="replace")
marker = "for _lang, _val in {"
index = text.find(marker)
if index >= 0:
    text = text[:index].rstrip() + "\n"

block = '''
_CFG_LOGS = {
    "zh-CN": "\\u914d\\u7f6e\\u4e0e\\u65e5\\u5fd7",
    "zh-TW": "\\u8a2d\\u5b9a\\u8207\\u65e5\\u8a8c",
    "en": "Config / logs",
    "fr": "Configuration / logs",
    "de": "Konfiguration / Logs",
    "ru": "\\u041a\\u043e\\u043d\\u0444\\u0438\\u0433\\u0443\\u0440\\u0430\\u0446\\u0438\\u044f / \\u043b\\u043e\\u0433\\u0438",
    "pt": "Configura\\u00e7\\u00e3o / logs",
    "es": "Configuraci\\u00f3n / registros",
    "tr": "Yap\\u0131land\\u0131rma / g\\u00fcnl\\u00fckler",
}
for _lang, _value in _CFG_LOGS.items():
    HELP.setdefault(_lang, {})["cfg_logs"] = _value
'''
path.write_text(text + block, encoding="utf-8")
print("help cfg_logs fixed")
