"""补 guide_missing 文案（9 语言）。"""

from pathlib import Path

p = Path("src/dota2coach/i18n.py")
s = p.read_text(encoding="utf-8")
extra = {
    "zh-CN": "说明文件生成失败：请检查 data 目录是否可写。",
    "zh-TW": "說明文件產生失敗：請檢查 data 目錄是否可寫。",
    "en": "Could not write the guide page: check that the data folder is writable.",
    "fr": "Impossible d’écrire la page d’aide : vérifie que le dossier data est accessible en écriture.",
    "de": "Die Hilfeseite konnte nicht geschrieben werden: Prüfe, ob der data-Ordner beschreibbar ist.",
    "ru": "Не удалось записать страницу справки: проверьте, доступна ли папка data для записи.",
    "pt": "Não foi possível gravar a página de ajuda: verifique se a pasta data é gravável.",
    "es": "No se pudo escribir la página de ayuda: comprueba que la carpeta data sea escribible.",
    "tr": "Yardım sayfası yazılamadı: data klasörünün yazılabilir olduğunu kontrol et.",
}
for code, text in extra.items():
    if f'"guide_missing"' in s:
        break
    marker = f'"{code}": {{"summary_last"'
    idx = s.find(marker)
    if idx < 0:
        continue
    end = s.find("}", idx)
    s = s[:end] + f', "guide_missing": "{text}"' + s[end:]
p.write_text(s, encoding="utf-8")
print("guide_missing added")
