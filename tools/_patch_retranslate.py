"""主窗口即时 retranslate：绑定静态文案 + 语言切换后刷新。"""

from pathlib import Path

root = Path("src/dota2coach")

# ---------------------------------------------------------------- i18n 补键
i18n = root / "i18n.py"
s = i18n.read_text(encoding="utf-8")
if "_EXTRA_UI" not in s:
    extra = '''

_EXTRA_UI: dict[str, dict[str, str]] = {
    "zh-CN": {"summary_last": "上一局", "show_card": "显示卡片", "tray_show": "显示主界面", "tray_quit": "退出"},
    "zh-TW": {"summary_last": "上一局", "show_card": "顯示卡片", "tray_show": "顯示主畫面", "tray_quit": "結束"},
    "en": {"summary_last": "Last game", "show_card": "Show card", "tray_show": "Show window", "tray_quit": "Quit"},
    "fr": {"summary_last": "Partie précédente", "show_card": "Afficher la carte", "tray_show": "Afficher la fenêtre", "tray_quit": "Quitter"},
    "de": {"summary_last": "Letztes Spiel", "show_card": "Karte zeigen", "tray_show": "Fenster zeigen", "tray_quit": "Beenden"},
    "ru": {"summary_last": "Прошлая игра", "show_card": "Показать карту", "tray_show": "Показать окно", "tray_quit": "Выход"},
    "pt": {"summary_last": "Última partida", "show_card": "Mostrar cartão", "tray_show": "Mostrar janela", "tray_quit": "Sair"},
    "es": {"summary_last": "Última partida", "show_card": "Mostrar tarjeta", "tray_show": "Mostrar ventana", "tray_quit": "Salir"},
    "tr": {"summary_last": "Son maç", "show_card": "Kartı göster", "tray_show": "Pencereyi göster", "tray_quit": "Çıkış"},
}
for _lang, _extra in _EXTRA_UI.items():
    _STRINGS.setdefault(_lang, {}).update(_extra)
'''
    s = s.rstrip() + "\n" + extra
    i18n.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------- panel
p = root / "ui" / "panel.py"
s = p.read_text(encoding="utf-8")


def rep(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit(f"missing: {old[:60]!r}")
    s = s.replace(old, new, 1)


rep(
    "        self._last_in_match: bool | None = None\n",
    "        self._last_in_match: bool | None = None\n"
    "        self._i18n: list[tuple[object, str, str, dict]] = []\n"
    "        self._tray_actions: list[tuple[object, str]] = []\n",
)

rep(
    '    def t(self, name: str, **fmt: object) -> str:\n        return tr(self.language, name, **fmt)\n',
    '    def t(self, name: str, **fmt: object) -> str:\n        return tr(self.language, name, **fmt)\n'
    '\n'
    '    def _bind(self, widget, key: str, **fmt: object):\n'
    '        self._i18n.append((widget, "setText", key, fmt))\n'
    '        widget.setText(self.t(key, **fmt))\n'
    '        return widget\n'
    '\n'
    '    def _retranslate_ui(self) -> None:\n'
    '        self.language = normalize_language(self.config.app.language)\n'
    '        self.skills = load_hero_skills(\n'
    '            skills_file_for(self.config.data_dir, self.language)\n'
    '        )\n'
    '        self.setWindowTitle(self.t("app_name"))\n'
    '        for widget, method, key, fmt in self._i18n:\n'
    '            getattr(widget, method)(self.t(key, **fmt))\n'
    '        for action, key in self._tray_actions:\n'
    '            action.setText(self.t(key))\n'
    '        self._last_in_match = None\n'
    '        self.refresh()\n',
)

# header
rep('        title = QLabel(self.t("app_name"))', '        title = self._bind(QLabel(), "app_name")')
rep('        tag = QLabel(self.t("tag"))', '        tag = self._bind(QLabel(), "tag")')
rep('        game_guide = QPushButton(self.t("guide"))', '        game_guide = self._bind(QPushButton(), "guide")')
rep('        build_guide = QPushButton(self.t("build"))', '        build_guide = self._bind(QPushButton(), "build")')
rep('        settings = QPushButton(self.t("settings"))', '        settings = self._bind(QPushButton(), "settings")')
rep('        feedback = QPushButton(self.t("feedback"))', '        feedback = self._bind(QPushButton(), "feedback")')
rep('        help_button = QPushButton(self.t("help"))', '        help_button = self._bind(QPushButton(), "help")')

# idle
rep('        headline = QLabel(self.t("idle_head"))', '        headline = self._bind(QLabel(), "idle_head")')
rep('        sub = QLabel(self.t("idle_sub"))', '        sub = self._bind(QLabel(), "idle_sub")')
rep(
    '        f8 = QLabel(self.t("f8", key=self.config.hotkeys.toggle_card))\n'
    '        self.f8_label = f8\n',
    '        f8 = self._bind(QLabel(), "f8", key=self.config.hotkeys.toggle_card)\n'
    '        self.f8_label = f8\n',
)
rep(
    '        for line in (\n'
    '            self.t("idle_1"),\n'
    '            self.t("idle_2"),\n'
    '            self.t("idle_3"),\n'
    '            self.t("idle_4"),\n'
    '        ):\n'
    '            label = QLabel(line)\n',
    '        for key in ("idle_1", "idle_2", "idle_3", "idle_4"):\n'
    '            label = self._bind(QLabel(), key)\n',
)
rep('        start = QPushButton(self.t("start"))', '        start = self._bind(QPushButton(), "start")')

# roster
rep('        title = QLabel(self.t("roster"))', '        title = self._bind(QLabel(), "roster")')
rep('        self.roster_hint = QLabel(self.t("roster_sub"))', '        self.roster_hint = self._bind(QLabel(), "roster_sub")')
rep(
    '        for team, label in (("ally", self.t("allies")), ("enemy", self.t("enemies"))):\n'
    '            row = QHBoxLayout()\n'
    '            row.setSpacing(10)\n'
    '            tag = QLabel(label)\n',
    '        for team, key in (("ally", "allies"), ("enemy", "enemies")):\n'
    '            row = QHBoxLayout()\n'
    '            row.setSpacing(10)\n'
    '            tag = self._bind(QLabel(), key)\n',
)

# sidebar
rep('        status_title = QLabel(self.t("status"))', '        status_title = self._bind(QLabel(), "status")')
rep(
    '        self.dot_gsi, row_gsi, _ = self._status_row(self.t("gsi"), theme.MUTED)',
    '        self.dot_gsi, row_gsi, self.gsi_label = self._status_row("", theme.MUTED)\n'
    '        self._i18n.append((self.gsi_label, "setText", "gsi", {}))',
)
rep(
    '        self.dot_match, row_match, _ = self._status_row(self.t("in_match"), theme.MUTED)',
    '        self.dot_match, row_match, self.match_label = self._status_row("", theme.MUTED)\n'
    '        self._i18n.append((self.match_label, "setText", "in_match", {}))',
)
rep('        match_title = QLabel(self.t("current_match"))', '        match_title = self._bind(QLabel(), "current_match")')
rep('        self.match_hero = QLabel(self.t("not_started"))', '        self.match_hero = self._bind(QLabel(), "not_started")')
rep('        hints_title = QLabel(self.t("recent"))', '        hints_title = self._bind(QLabel(), "recent")')
rep('        self.primary = QPushButton(self.t("start"))', '        self.primary = QPushButton(self.t("start"))')
rep('        self.card_button = QPushButton(self.t("hide_card"))', '        self.card_button = QPushButton(self.t("hide_card"))')
rep(
    '        self.footer = QLabel(f"v{__version__} · " + self.t("local_run"))',
    '        self.footer = QLabel(f"v{__version__} · " + self.t("local_run"))\n'
    '        self.footer_key = "local_run"',
)

# summary
rep('        self.summary_title = QLabel("涓婁竴灞€")', '        self.summary_title = self._bind(QLabel(), "summary_last")') if "涓婁竴灞€" in s else None
rep('        self.summary_title = QLabel("上一局")', '        self.summary_title = self._bind(QLabel(), "summary_last")')
rep('        back = QPushButton(self.t("back_home"))', '        back = self._bind(QPushButton(), "back_home")')

# tray
rep(
    '        tray.setToolTip("DOTA2 入门教练")',
    '        tray.setToolTip(self.t("app_name"))',
)
rep(
    '        menu.addAction("显示主界面", self.showNormal)',
    '        self._tray_actions = []\n'
    '        show_action = menu.addAction(self.t("tray_show"), self.showNormal)\n'
    '        self._tray_actions.append((show_action, "tray_show"))',
)
rep(
    '        menu.addAction(self.t("hide_card"), self._toggle_card)',
    '        hide_action = menu.addAction(self.t("hide_card"), self._toggle_card)\n'
    '        self._tray_actions.append((hide_action, "hide_card"))',
)
rep(
    '        menu.addAction(self.t("help"), self._open_help)',
    '        help_action = menu.addAction(self.t("help"), self._open_help)\n'
    '        self._tray_actions.append((help_action, "help"))',
)
rep(
    '        menu.addSeparator()\n        menu.addAction("退出", self._quit)',
    '        menu.addSeparator()\n'
    '        quit_action = menu.addAction(self.t("tray_quit"), self._quit)\n'
    '        self._tray_actions.append((quit_action, "tray_quit"))',
)

# settings: retranslate after save
rep(
    '        self.config = cfg\n',
    '        changed_language = normalize_language(cfg.app.language) != self.language\n'
    '        self.config = cfg\n'
    '        if changed_language:\n'
    '            self._retranslate_ui()\n',
)

p.write_text(s, encoding="utf-8")
print("panel patched")
