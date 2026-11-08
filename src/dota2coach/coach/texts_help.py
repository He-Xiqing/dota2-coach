"""帮助/反馈对话框的多语言文案。"""

from __future__ import annotations

HELP: dict[str, dict[str, str]] = {
    "zh-CN": {
        "redline": "红线：不读内存、不注入、不模拟按键、不改包、不代打。只做两件事：接收官方 GSI 报文、截自己屏幕做图像识别。",
        "hot": "快捷键：{toggle} 显示/隐藏卡片；{voice} 试听语音。",
        "logs": "排错：先看 logs\\console.log 与 logs\\screenshots\\ 下的标注图；识别 0/10 多半是 data\\hero_cards 缺失或游戏窗口被别的窗口挡住。",
        "fb_note": "写下遇到的问题或想要的功能。保存后存到 logs/feedback/（纯本地）。",
        "fb_send": "邮件发送",
        "fb_copy": "复制内容",
        "fb_save": "只保存到本地",
        "fb_title": "意见反馈",
        "fb_ph": "例如：1920x1080 窗口模式下识别只有 7/10；希望加一个“敌方买活”提醒…",
        "tray_min": "已最小化到托盘，双击图标可恢复。",
        "fb_mail": "反馈邮箱：",
        "fb_open": "打开目录",
        "cancel": "取消",
        "title": "DOTA2 入门教练",
        "open_logs": "打开日志目录",
        "open_config": "打开配置文件",
        "close": "关闭",
    },
    "zh-TW": {
        "redline": "紅線：不讀記憶體、不注入、不模擬按鍵、不改封包、不代打。只做兩件事：接收官方 GSI 封包、截自己的螢幕做影像辨識。",
        "hot": "快捷鍵：{toggle} 顯示/隱藏卡片；{voice} 試聽語音。",
        "logs": "排錯：先看 logs\\console.log 與 logs\\screenshots\\ 的標註圖；辨識 0/10 多半是 data\\hero_cards 缺失或遊戲視窗被其他視窗擋住。",
        "fb_note": "寫下遇到的問題或想要的功能。儲存後放在 logs/feedback/（純本機）。",
        "fb_send": "郵件寄送",
        "fb_copy": "複製內容",
        "fb_save": "只存到本機",
    },
    "en": {
        "redline": "Red lines: no memory reading, no injection, no simulated keys, no packet editing, no automation. Only official GSI data and screenshots of your own screen.",
        "hot": "Hotkeys: {toggle} show/hide the card; {voice} preview the voice.",
        "logs": "Troubleshooting: check logs\\console.log and the annotated images in logs\\screenshots\\. 0/10 usually means data\\hero_cards is missing or the game window is covered.",
        "fb_note": "Describe the problem or feature you want. Saved locally under logs/feedback/.",
        "fb_send": "Send by email",
        "fb_copy": "Copy text",
        "fb_save": "Save locally",
        "fb_title": "Feedback",
        "fb_ph": "e.g. only 7/10 heroes recognized in 1920x1080 windowed mode; please add a buyback reminder…",
        "tray_min": "Minimized to tray — double-click the icon to restore.",
        "fb_mail": "Feedback email: ",
        "fb_open": "Open folder",
        "cancel": "Cancel",
        "title": "DOTA2 Coach",
        "open_logs": "Open logs",
        "open_config": "Open config",
        "close": "Close",
    },
    "fr": {
        "redline": "Règles : pas de lecture mémoire, pas d'injection, pas de touches simulées, pas de paquets modifiés, pas d'automatisation. Uniquement GSI officiel et captures de votre écran.",
        "hot": "Raccourcis : {toggle} afficher/masquer la carte ; {voice} écouter la voix.",
        "logs": "Dépannage : voir logs\\console.log et les images annotées dans logs\\screenshots\\. 0/10 = data\\hero_cards manquant ou fenêtre masquée.",
        "fb_note": "Décrivez le problème ou la fonction souhaitée. Enregistré localement dans logs/feedback/.",
        "fb_send": "Envoyer par e-mail",
        "fb_copy": "Copier",
        "fb_save": "Enregistrer en local",
    },
    "de": {
        "redline": "Regeln: kein Speicherlesen, keine Injection, keine simulierten Tasten, keine Paketmanipulation, keine Automatisierung. Nur offizielle GSI-Daten und Screenshots deines Bildschirms.",
        "hot": "Tasten: {toggle} Karte zeigen/verstecken; {voice} Stimme testen.",
        "logs": "Fehlersuche: logs\\console.log und die markierten Bilder in logs\\screenshots\\. 0/10 heißt meist data\\hero_cards fehlt oder das Fenster ist verdeckt.",
        "fb_note": "Problem oder Wunsch beschreiben. Wird lokal unter logs/feedback/ gespeichert.",
        "fb_send": "Per E-Mail senden",
        "fb_copy": "Kopieren",
        "fb_save": "Nur lokal speichern",
    },
    "ru": {
        "redline": "Правила: без чтения памяти, без инъекций, без эмуляции клавиш, без правки пакетов и автоматизации. Только официальный GSI и снимки своего экрана.",
        "hot": "Горячие клавиши: {toggle} показать/скрыть карточку; {voice} проверить голос.",
        "logs": "Диагностика: смотрите logs\\console.log и размеченные снимки в logs\\screenshots\\. 0/10 обычно значит нет data\\hero_cards или окно перекрыто.",
        "fb_note": "Опишите проблему или пожелание. Сохраняется локально в logs/feedback/.",
        "fb_send": "Отправить письмом",
        "fb_copy": "Копировать",
        "fb_save": "Сохранить локально",
    },
    "pt": {
        "redline": "Regras: sem leitura de memória, sem injeção, sem teclas simuladas, sem editar pacotes, sem automação. Só GSI oficial e capturas da sua tela.",
        "hot": "Atalhos: {toggle} mostrar/ocultar o cartão; {voice} ouvir a voz.",
        "logs": "Diagnóstico: veja logs\\console.log e as imagens anotadas em logs\\screenshots\\. 0/10 geralmente é data\\hero_cards ausente ou janela coberta.",
        "fb_note": "Descreva o problema ou o recurso desejado. Salvo localmente em logs/feedback/.",
        "fb_send": "Enviar por e-mail",
        "fb_copy": "Copiar texto",
        "fb_save": "Salvar localmente",
    },
    "es": {
        "redline": "Reglas: sin lectura de memoria, sin inyección, sin teclas simuladas, sin editar paquetes, sin automatización. Solo GSI oficial y capturas de tu pantalla.",
        "hot": "Atajos: {toggle} mostrar/ocultar la tarjeta; {voice} escuchar la voz.",
        "logs": "Diagnóstico: revisa logs\\console.log y las imágenes anotadas en logs\\screenshots\\. 0/10 suele ser data\\hero_cards ausente o ventana tapada.",
        "fb_note": "Describe el problema o la función que quieres. Se guarda localmente en logs/feedback/.",
        "fb_send": "Enviar por correo",
        "fb_copy": "Copiar texto",
        "fb_save": "Guardar en local",
    },
    "tr": {
        "redline": "Kurallar: bellek okuma yok, enjeksiyon yok, tuş simülasyonu yok, paket düzenleme yok, otomasyon yok. Sadece resmi GSI ve kendi ekranının görüntüsü.",
        "hot": "Kısayollar: {toggle} kartı göster/gizle; {voice} sesi dinle.",
        "logs": "Sorun giderme: logs\\console.log ve logs\\screenshots\\. 0/10 genelde data\\hero_cards eksik veya pencere kapalı demektir.",
        "fb_note": "Sorunu veya istediğin özelliği yaz. logs/feedback/ altında yerel olarak saklanır.",
        "fb_send": "E-posta ile gönder",
        "fb_copy": "Metni kopyala",
        "fb_save": "Yalnızca yerel kaydet",
    },
}


_MISSING: dict[str, dict[str, str]] = {'zh-TW': {'title': 'DOTA2 入門教練', 'open_logs': '開啟日誌目錄', 'open_config': '開啟設定檔', 'close': '關閉', 'fb_title': '意見回饋', 'fb_ph': '例如：1920x1080 視窗模式下辨識只有 7/10；希望加一個「敵方買活」提醒…', 'tray_min': '已最小化到系統匣，雙擊圖示可恢復。', 'fb_mail': '回饋信箱：', 'fb_open': '開啟目錄', 'cancel': '取消'}, 'fr': {'title': 'Coach DOTA2', 'open_logs': 'Ouvrir les logs', 'open_config': 'Ouvrir la config', 'close': 'Fermer', 'fb_title': 'Retour', 'fb_ph': "ex. seulement 7/10 héros reconnus en fenêtre 1920x1080 ; ajouter un rappel d'achat…", 'tray_min': 'Réduit dans la zone de notification — double-cliquez pour restaurer.', 'fb_mail': 'E-mail de retour : ', 'fb_open': 'Ouvrir le dossier', 'cancel': 'Annuler'}, 'de': {'title': 'DOTA2-Trainer', 'open_logs': 'Logs öffnen', 'open_config': 'Konfiguration öffnen', 'close': 'Schließen', 'fb_title': 'Feedback', 'fb_ph': 'z. B. im 1920x1080-Fenstermodus nur 7/10 Helden erkannt; bitte Buyback-Erinnerung hinzufügen…', 'tray_min': 'Ins Infobereich minimiert – Doppelklick zum Wiederherstellen.', 'fb_mail': 'Feedback-E-Mail: ', 'fb_open': 'Ordner öffnen', 'cancel': 'Abbrechen'}, 'ru': {'title': 'Тренер DOTA2', 'open_logs': 'Открыть логи', 'open_config': 'Открыть конфиг', 'close': 'Закрыть', 'fb_title': 'Отзыв', 'fb_ph': 'напр., в оконном режиме 1920x1080 распознано только 7/10 героев; добавьте напоминание о выкупе…', 'tray_min': 'Свёрнуто в трей — двойной клик по значку, чтобы восстановить.', 'fb_mail': 'Почта для отзывов: ', 'fb_open': 'Открыть папку', 'cancel': 'Отмена'}, 'pt': {'title': 'Treinador DOTA2', 'open_logs': 'Abrir logs', 'open_config': 'Abrir configuração', 'close': 'Fechar', 'fb_title': 'Feedback', 'fb_ph': 'ex.: apenas 7/10 heróis reconhecidos no modo janela 1920x1080; adicione um lembrete de recompra…', 'tray_min': 'Minimizado para a bandeja — clique duplo no ícone para restaurar.', 'fb_mail': 'E-mail de feedback: ', 'fb_open': 'Abrir pasta', 'cancel': 'Cancelar'}, 'es': {'title': 'Entrenador DOTA2', 'open_logs': 'Abrir registros', 'open_config': 'Abrir configuración', 'close': 'Cerrar', 'fb_title': 'Comentarios', 'fb_ph': 'p. ej., solo 7/10 héroes reconocidos en ventana 1920x1080; añade un recordatorio de recompra…', 'tray_min': 'Minimizado en la bandeja: doble clic para restaurar.', 'fb_mail': 'Correo de comentarios: ', 'fb_open': 'Abrir carpeta', 'cancel': 'Cancelar'}, 'tr': {'title': 'DOTA2 Koçu', 'open_logs': 'Günlükleri aç', 'open_config': 'Yapılandırmayı aç', 'close': 'Kapat', 'fb_title': 'Geri bildirim', 'fb_ph': 'ör. 1920x1080 pencere modunda yalnızca 7/10 kahraman tanındı; bir geri satın alma hatırlatıcısı ekleyin…', 'tray_min': 'Tepsiye küçültüldü — geri yüklemek için simgeye çift tıklayın.', 'fb_mail': 'Geri bildirim e-postası: ', 'fb_open': 'Klasörü aç', 'cancel': 'İptal'}}


def htext(name: str, **fmt: object) -> str:
    from .texts import language

    table = HELP.get(language()) or HELP["en"]
    text = table.get(name) or HELP["en"].get(name, "")
    try:
        return text.format(**fmt)
    except (KeyError, IndexError):
        return text


for _lang, _vals in _MISSING.items():
    HELP.setdefault(_lang, {}).update(_vals)

_CFG_LOGS = {
    "zh-CN": "\u914d\u7f6e\u4e0e\u65e5\u5fd7",
    "zh-TW": "\u8a2d\u5b9a\u8207\u65e5\u8a8c",
    "en": "Config / logs",
    "fr": "Configuration / logs",
    "de": "Konfiguration / Logs",
    "ru": "\u041a\u043e\u043d\u0444\u0438\u0433\u0443\u0440\u0430\u0446\u0438\u044f / \u043b\u043e\u0433\u0438",
    "pt": "Configura\u00e7\u00e3o / logs",
    "es": "Configuraci\u00f3n / registros",
    "tr": "Yap\u0131land\u0131rma / g\u00fcnl\u00fckler",
}
for _lang, _value in _CFG_LOGS.items():
    HELP.setdefault(_lang, {})["cfg_logs"] = _value
