"""补齐 texts_help 的 7 种语言缺口键。"""

from pathlib import Path

EXTRA = {
    "zh-TW": {
        "title": "DOTA2 入門教練",
        "open_logs": "開啟日誌目錄",
        "open_config": "開啟設定檔",
        "close": "關閉",
        "fb_title": "意見回饋",
        "fb_ph": "例如：1920x1080 視窗模式下辨識只有 7/10；希望加一個「敵方買活」提醒…",
        "tray_min": "已最小化到系統匣，雙擊圖示可恢復。",
        "fb_mail": "回饋信箱：",
        "fb_open": "開啟目錄",
        "cancel": "取消",
    },
    "fr": {
        "title": "DOTA2 Coach",
        "open_logs": "Ouvrir les logs",
        "open_config": "Ouvrir la config",
        "close": "Fermer",
        "fb_title": "Retour",
        "fb_ph": "ex. seulement 7/10 héros reconnus en fenêtre 1920x1080 ; ajouter un rappel d'achat…",
        "tray_min": "Réduit dans la zone de notification — double-cliquez pour restaurer.",
        "fb_mail": "E-mail de retour : ",
        "fb_open": "Ouvrir le dossier",
        "cancel": "Annuler",
    },
    "de": {
        "title": "DOTA2 Coach",
        "open_logs": "Logs öffnen",
        "open_config": "Konfiguration öffnen",
        "close": "Schließen",
        "fb_title": "Feedback",
        "fb_ph": "z. B. im 1920x1080-Fenstermodus nur 7/10 Helden erkannt; bitte Buyback-Erinnerung hinzufügen…",
        "tray_min": "Ins Infobereich minimiert – Doppelklick zum Wiederherstellen.",
        "fb_mail": "Feedback-E-Mail: ",
        "fb_open": "Ordner öffnen",
        "cancel": "Abbrechen",
    },
    "ru": {
        "title": "Тренер DOTA2",
        "open_logs": "Открыть логи",
        "open_config": "Открыть конфиг",
        "close": "Закрыть",
        "fb_title": "Отзыв",
        "fb_ph": "напр., в оконном режиме 1920x1080 распознано только 7/10 героев; добавьте напоминание о выкупе…",
        "tray_min": "Свёрнуто в трей — двойной клик по значку, чтобы восстановить.",
        "fb_mail": "Почта для отзывов: ",
        "fb_open": "Открыть папку",
        "cancel": "Отмена",
    },
    "pt": {
        "title": "Treinador DOTA2",
        "open_logs": "Abrir logs",
        "open_config": "Abrir configuração",
        "close": "Fechar",
        "fb_title": "Feedback",
        "fb_ph": "ex.: apenas 7/10 heróis reconhecidos no modo janela 1920x1080; adicione um lembrete de recompra…",
        "tray_min": "Minimizado para a bandeja — clique duplo no ícone para restaurar.",
        "fb_mail": "E-mail de feedback: ",
        "fb_open": "Abrir pasta",
        "cancel": "Cancelar",
    },
    "es": {
        "title": "Entrenador DOTA2",
        "open_logs": "Abrir registros",
        "open_config": "Abrir configuración",
        "close": "Cerrar",
        "fb_title": "Comentarios",
        "fb_ph": "p. ej., solo 7/10 héroes reconocidos en ventana 1920x1080; añade un recordatorio de recompra…",
        "tray_min": "Minimizado en la bandeja: doble clic para restaurar.",
        "fb_mail": "Correo de comentarios: ",
        "fb_open": "Abrir carpeta",
        "cancel": "Cancelar",
    },
    "tr": {
        "title": "DOTA2 Koçu",
        "open_logs": "Günlükleri aç",
        "open_config": "Yapılandırmayı aç",
        "close": "Kapat",
        "fb_title": "Geri bildirim",
        "fb_ph": "ör. 1920x1080 pencere modunda yalnızca 7/10 kahraman tanındı; bir geri satın alma hatırlatıcısı ekleyin…",
        "tray_min": "Tepsiye küçültüldü — geri yüklemek için simgeye çift tıklayın.",
        "fb_mail": "Geri bildirim e-postası: ",
        "fb_open": "Klasörü aç",
        "cancel": "İptal",
    },
}

path = Path("src/dota2coach/coach/texts_help.py")
text = path.read_text(encoding="utf-8")
marker = "\n\ndef htext("
extra_src = "\n\n_MISSING: dict[str, dict[str, str]] = " + repr(EXTRA) + "\n"
if "_MISSING" not in text:
    text = text.replace(marker, extra_src + marker, 1)
    text += '''

for _lang, _vals in _MISSING.items():
    HELP.setdefault(_lang, {}).update(_vals)
'''
    path.write_text(text, encoding="utf-8")
print("help languages filled")
