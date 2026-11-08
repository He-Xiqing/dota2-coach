"""主窗口：空闲介绍 / 对局阵容 / 状态 / 设置 / 帮助。

面板只读 `CoachApp.status()`，所有游戏逻辑仍在 app.py 里，
这样界面可以随时替换而不动核心。
"""

from __future__ import annotations

import copy
import os
import sys
from datetime import datetime
from urllib.parse import quote
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QFont, QFontMetrics, QGuiApplication, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..config import (
    Config,
    save_config,
    validate_config,
)
from ..knowledge.nicknames import load_nicknames
from ..knowledge.skills import HeroSkills, load_hero_skills, skills_file_for
from . import theme
from . import voices
from ..coach.texts import language as ui_language, phase_name
from ..coach.texts_help import htext
from ..i18n import LANGUAGES, normalize_language, tr
from ..knowledge.ingame_guide import ensure_guide
from .branding import app_icon, fallback_icon
from .hotkeys import Hotkeys
from .links import official_guide_url

TILE_W = 190
TILE_H = 396
BADGE_COLORS = {
    "先手": ("#B45309", "#FEF3C7"),
    "爆发": ("#B91C1C", "#FEE2E2"),
    "隐身": ("#6D28D9", "#EDE9FE"),
}


class Dot(QWidget):
    """10px 状态灯。"""

    def __init__(self, color: str) -> None:
        super().__init__()
        self._color = color
        self.setFixedSize(QSize(10, 10))

    def set_color(self, color: str) -> None:
        if color != self._color:
            self._color = color
            self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt 命名
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 10, 10)


class HeroTile(QFrame):
    """一个英雄：头像 + 名字 + 两条技能简介。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.placeholder = "识别中…"
        self.setObjectName("Card")
        self.setFixedSize(TILE_W, TILE_H)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)
        self.icon = QLabel()
        self.icon.setFixedSize(40, 40)
        self.icon.setStyleSheet(f"background: {theme.BG}; border-radius: 8px;")
        self.name = QLabel("?")
        self.alias = QLabel("")
        self.alias.setFont(theme.font(9))
        self.alias.setStyleSheet(f"color: {theme.MUTED};")
        self.name.setObjectName("H3")
        top.addWidget(self.icon)
        top.addWidget(self.name)
        top.addStretch(1)
        layout.addLayout(top)

        self.alias.setFixedWidth(TILE_W - 32)
        layout.addWidget(self.alias)

        self.badge_row = QHBoxLayout()
        self.badge_row.setSpacing(4)
        self.badges: list[QLabel] = []
        for _ in range(3):
            badge = QLabel("")
            badge.setFont(theme.font(8))
            badge.hide()
            self.badge_row.addWidget(badge)
            self.badges.append(badge)
        self.badge_row.addStretch(1)
        layout.addLayout(self.badge_row)

        self.traits = QLabel("")
        self.traits.setFont(theme.font(9))
        self.traits.setStyleSheet(f"color: {theme.PRIMARY};")
        self.traits.setWordWrap(True)
        self.traits.setFixedWidth(TILE_W - 32)
        layout.addWidget(self.traits)

        self.skill_rows: list[tuple[QLabel, QLabel]] = []
        for _ in range(2):
            name_label = QLabel("")
            name_label.setFont(theme.font(10))
            name_label.setStyleSheet(f"color: {theme.TEXT}; font-weight: 600;")
            desc_label = QLabel("")
            desc_label.setFont(theme.font(9))
            desc_label.setStyleSheet(f"color: {theme.MUTED};")
            desc_label.setWordWrap(True)
            desc_label.setFixedWidth(TILE_W - 32)
            desc_label.setMinimumHeight(90)
            layout.addWidget(name_label)
            layout.addWidget(desc_label)
            self.skill_rows.append((name_label, desc_label))

    def show_hero(
        self,
        name: str,
        icon: QPixmap | None,
        skills: list[str],
        *,
        team: str = "ally",
        known: bool = True,
        threats: list[str] | tuple[str, ...] = (),
        traits: str = "",
        alias: str = "",
    ) -> None:
        self.name.setText(name or "?")
        self.alias.setText(alias)
        for index, badge in enumerate(self.badges):
            if index < len(threats):
                label = threats[index]
                fg, bg = BADGE_COLORS.get(label, (theme.TEXT, theme.BG))
                badge.setText(label)
                badge.setStyleSheet(
                    f"color: {fg}; background: {bg}; border-radius: 5px; padding: 1px 5px;"
                )
                badge.show()
            else:
                badge.hide()
        if icon is not None and not icon.isNull():
            self.icon.setPixmap(
                icon.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        else:
            self.icon.setPixmap(QPixmap())
            self.icon.setText("?" if known else "·")
            self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = theme.SUCCESS if team == "ally" else theme.DANGER
        self.name.setStyleSheet(f"color: {theme.TEXT if known else theme.MUTED};")
        self.traits.setText(traits)
        self.traits.setVisible(bool(traits))
        pairs = []
        for text in skills[:2]:
            head, _, tail = text.partition("·")
            pairs.append((head, tail or "—"))
        for index, (name_label, desc_label) in enumerate(self.skill_rows):
            if index < len(pairs):
                name_label.setText(pairs[index][0])
                desc_label.setText(pairs[index][1])
            else:
                name_label.setText(self.placeholder if not known else "")
                desc_label.setText("")
        self.setStyleSheet(
            f"QFrame#Card {{ background: {theme.SURFACE}; border: 1px solid {theme.BORDER};"
            f" border-left: 3px solid {color}; border-radius: {theme.RADIUS}px; }}"
        )


class SettingsDialog(QDialog):
    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = copy.deepcopy(config)
        self.setWindowTitle(self.t("set_title"))
        self.setStyleSheet(theme.STYLE)
        self._applying_pack = False
        self.resize(560, 430)

        tabs = QTabWidget()
        tabs.addTab(self._language_tab(), self.t("tab_language"))
        tabs.addTab(self._theme_tab(), self.t("tab_theme"))
        tabs.addTab(self._overlay_tab(), self.t("tab_overlay"))
        tabs.addTab(self._voice_tab(), self.t("tab_voice"))
        tabs.addTab(self._assist_tab(), self.t("tab_assist"))
        tabs.addTab(self._hotkey_tab(), self.t("tab_hotkey"))
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self.t("save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.t("cancel"))
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("Primary")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        note = QLabel(self.t("settings_note"))
        note.setObjectName("Muted")
        layout.addWidget(note)

    def t(self, name: str, **fmt: object) -> str:
        return tr(self._config.app.language, name, **fmt)

    # ---- 主题 ----
    def _language_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.lang_combo = QComboBox()
        current = normalize_language(self._config.app.language)
        for code, label in LANGUAGES.items():
            self.lang_combo.addItem(f"{label}（{code}）", code)
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(current)))
        form.addRow(self.t("set_language"), self.lang_combo)
        hint = QLabel(tr(current, "lang_hint"))
        hint.setWordWrap(True)
        hint.setObjectName("Muted")
        form.addRow(hint)
        return page

    def _theme_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self._wallpaper_path = self._config.theme.wallpaper
        self.wallpaper_label = QLabel(self._wallpaper_path or self.t("set_wallpaper_default"))
        self.wallpaper_label.setObjectName("Muted")
        self.wallpaper_label.setWordWrap(True)
        form.addRow(self.t("set_wallpaper"), self.wallpaper_label)
        row = QHBoxLayout()
        choose = QPushButton(self.t("set_choose_image"))
        choose.clicked.connect(self._choose_wallpaper)
        clear = QPushButton(self.t("set_clear"))
        clear.clicked.connect(self._clear_wallpaper)
        row.addWidget(choose)
        row.addWidget(clear)
        row.addStretch(1)
        form.addRow("", row)

        self.wallpaper_dim = QSlider(Qt.Orientation.Horizontal)
        self.wallpaper_dim.setRange(0, 90)
        self.wallpaper_dim.setValue(int(round(self._config.theme.wallpaper_dim * 100)))
        self.dim_value = QLabel(f"{self.wallpaper_dim.value()}%")
        self.wallpaper_dim.valueChanged.connect(lambda v: self.dim_value.setText(f"{v}%"))
        row2 = QHBoxLayout()
        row2.addWidget(self.wallpaper_dim, 1)
        row2.addWidget(self.dim_value)
        form.addRow(self.t("set_wallpaper_dim"), row2)
        note = QLabel(self.t("set_wallpaper_note"))
        note.setObjectName("Muted")
        note.setWordWrap(True)
        form.addRow("", note)
        return page

    def _choose_wallpaper(self) -> None:
        start = self._wallpaper_path or str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, self.t("set_choose_title"), start, "图片 (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self._wallpaper_path = path
            self.wallpaper_label.setText(path)

    def _clear_wallpaper(self) -> None:
        self._wallpaper_path = ""
        self.wallpaper_label.setText(self.t("set_wallpaper_default"))

    def _apply_pack(self) -> None:
        pack = voices.PACK_BY_ID.get(self.pack.currentData())
        if pack is None or pack.id == "custom" or not pack.edge:
            return
        self._applying_pack = True
        try:
            # 选了语音包就切到在线 edge 音色，否则 SAPI 会一直用系统音色，看起来“改了没反应”
            edge_index = self.backend.findData("edge")
            if edge_index >= 0:
                self.backend.setCurrentIndex(edge_index)
            self.edge_voice.setCurrentText(pack.edge)
            self.rate.setValue(pack.rate)
            self.volume.setValue(pack.volume)
        finally:
            self._applying_pack = False

    def _voice_touched(self, *_args) -> None:
        """手动改了音色/语速/音量，就切到“自定义”，避免被语音包预设覆盖。"""
        if self._applying_pack:
            return
        custom = self.pack.findData("custom")
        if custom >= 0 and self.pack.currentIndex() != custom:
            self._applying_pack = True
            try:
                self.pack.setCurrentIndex(custom)
            finally:
                self._applying_pack = False

    def _preview_voice(self) -> None:
        raw_voice = self.edge_voice.currentText().strip()
        fixed = voices.normalize_edge_voice(raw_voice)
        if raw_voice and fixed != raw_voice.strip():
            self.edge_voice.setCurrentText(fixed)
        edge, rate, volume = voices.resolve(
            self.pack.currentData() or "custom",
            fixed,
            self.rate.value(),
            self.volume.value(),
        )
        try:
            from ..ui.voice import Speaker

            preview = Speaker(
                enabled=True,
                speak=True,
                backend=self.backend.currentData() or "auto",
                edge_voice=edge,
                rate=rate,
                volume=volume,
                min_interval=0.0,
                beep=False,
                log_path=self._config.log_dir / "voice.log",
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, self.t("set_test_failed"), str(exc))
            return
        preview.say(self.t("set_preview_text"), force=True)

    # ---- 覆盖层 ----
    def _overlay_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        self.enabled = QCheckBox(self.t("set_overlay_cards"))
        self.enabled.setChecked(self._config.overlay.enabled)
        form.addRow(self.t("set_enable"), self.enabled)

        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(20, 100)
        self.opacity.setValue(int(round(self._config.overlay.opacity * 100)))
        self.opacity_value = QLabel(f"{self.opacity.value()}%")
        self.opacity.valueChanged.connect(lambda v: self.opacity_value.setText(f"{v}%"))
        row = QHBoxLayout()
        row.addWidget(self.opacity, 1)
        row.addWidget(self.opacity_value)
        form.addRow(self.t("set_clear_state"), row)

        self.dim_opacity = QSlider(Qt.Orientation.Horizontal)
        self.dim_opacity.setRange(20, 100)
        self.dim_opacity.setValue(int(round(self._config.overlay.dim_opacity * 100)))
        self.dim_value = QLabel(f"{self.dim_opacity.value()}%")
        self.dim_opacity.valueChanged.connect(lambda v: self.dim_value.setText(f"{v}%"))
        row2 = QHBoxLayout()
        row2.addWidget(self.dim_opacity, 1)
        row2.addWidget(self.dim_value)
        form.addRow(self.t("set_dim_state"), row2)

        dim_tip = QLabel(self.t("set_overlay_note"))
        dim_tip.setObjectName("Muted")
        dim_tip.setWordWrap(True)
        form.addRow("", dim_tip)

        self.click_through = QCheckBox(self.t("set_click_through"))
        self.click_through.setChecked(self._config.overlay.click_through)
        form.addRow("", self.click_through)

        tip = QLabel(self.t("set_click_hint"))
        tip.setObjectName("Muted")
        form.addRow("", tip)
        return page

    # ---- 语音 ----
    def _voice_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        voice = self._config.voice
        self.voice_enabled = QCheckBox(self.t("set_voice_enable"))
        self.voice_enabled.setChecked(voice.enabled)
        form.addRow(self.t("set_enable"), self.voice_enabled)

        self.voice_speak = QCheckBox(self.t("set_voice_speak"))
        self.voice_speak.setChecked(voice.speak)
        form.addRow(self.t("set_row_speak"), self.voice_speak)

        self.pack = QComboBox()
        for pack in voices.packs_for_language(normalize_language(self._config.app.language)):
            if pack.id == "custom":
                label = pack.name
            else:
                voice_name = pack.name.split(" · ")[0]
                lang_name = LANGUAGES.get(pack.lang, pack.lang)
                label = f"{voice_name} · {lang_name}"
            self.pack.addItem(label, pack.id)
        self.pack.setCurrentIndex(max(0, self.pack.findData(voice.pack)))
        self.pack.currentIndexChanged.connect(self._apply_pack)
        form.addRow(self.t("set_voice_pack"), self.pack)

        self.wait_voice = QCheckBox(self.t("set_wait_voice"))
        self.wait_voice.setChecked(voice.wait_game_voice)
        form.addRow(self.t("set_row_wait"), self.wait_voice)

        self.backend = QComboBox()
        for label, value in (
            (self.t("set_backend_auto"), "auto"),
            (self.t("set_backend_sapi"), "sapi"),
            (self.t("set_backend_edge"), "edge"),
            (self.t("set_backend_beep"), "beep"),
            (self.t("set_backend_none"), "none"),
        ):
            self.backend.addItem(label, value)
        index = max(0, self.backend.findData(voice.backend))
        self.backend.setCurrentIndex(index)
        form.addRow(self.t("set_backend"), self.backend)

        self.edge_voice = QComboBox()
        for label, value in (
            (self.t("set_voice_xiaoxiao"), "zh-CN-XiaoxiaoNeural"),
            (self.t("set_voice_yunxi"), "zh-CN-YunxiNeural"),
            (self.t("set_voice_xiaoyi"), "zh-CN-XiaoyiNeural"),
            (self.t("set_voice_yunjian"), "zh-CN-YunjianNeural"),
        ):
            self.edge_voice.addItem(label, value)
        self.edge_voice.setEditable(True)
        self.edge_voice.setCurrentText(voice.edge_voice)
        self.edge_voice.currentTextChanged.connect(self._voice_touched)
        form.addRow(self.t("set_edge_voice"), self.edge_voice)

        self.rate = QSpinBox()
        self.rate.setRange(-10, 10)
        self.rate.setValue(int(voice.rate))
        self.rate.valueChanged.connect(self._voice_touched)
        form.addRow(self.t("set_rate"), self.rate)

        self.volume = QSpinBox()
        self.volume.setRange(0, 100)
        self.volume.setValue(int(voice.volume))
        self.volume.valueChanged.connect(self._voice_touched)
        form.addRow(self.t("set_volume"), self.volume)

        self.interval = QDoubleSpinBox()
        self.interval.setRange(0.0, 60.0)
        self.interval.setSingleStep(1.0)
        self.interval.setValue(float(voice.min_interval))
        form.addRow(self.t("set_interval"), self.interval)

        preview_row = QHBoxLayout()
        preview = QPushButton(self.t("set_test_voice"))
        preview.clicked.connect(self._preview_voice)
        preview_row.addWidget(preview)
        preview_row.addStretch(1)
        form.addRow("", preview_row)
        return page

    # ---- 辅助 ----
    def _assist_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        assist = self._config.assist
        self.assist_rune = QCheckBox(self.t("set_assist_rune"))
        self.assist_rune.setChecked(assist.rune_alerts)
        form.addRow(self.t("set_row_rune"), self.assist_rune)
        self.assist_names = QCheckBox(self.t("set_assist_names"))
        self.assist_names.setChecked(assist.name_strip)
        form.addRow(self.t("set_row_names"), self.assist_names)
        self.assist_fight = QCheckBox(self.t("set_assist_fight"))
        self.assist_fight.setChecked(assist.fight_alerts)
        form.addRow(self.t("set_row_fight"), self.assist_fight)
        self.assist_lane = QCheckBox(self.t("set_assist_lane"))
        self.assist_lane.setChecked(assist.lane_alerts)
        form.addRow(self.t("set_row_lane"), self.assist_lane)
        mm = self._config.minimap
        mm_row = QHBoxLayout()
        self.mm_side = QComboBox()
        self.mm_side.addItem(self.t("set_mm_auto"), "auto")
        self.mm_side.addItem(self.t("set_mm_left"), "left")
        self.mm_side.addItem(self.t("set_mm_right"), "right")
        idx = self.mm_side.findData(mm.side)
        self.mm_side.setCurrentIndex(max(0, idx))
        self.mm_size = QSpinBox()
        self.mm_size.setRange(60, 160)
        self.mm_size.setSuffix("%")
        self.mm_size.setValue(int(mm.size_percent))
        self.mm_dx = QSpinBox()
        self.mm_dx.setRange(-300, 300)
        self.mm_dx.setSuffix("px")
        self.mm_dx.setValue(int(mm.offset_x))
        self.mm_dy = QSpinBox()
        self.mm_dy.setRange(-300, 300)
        self.mm_dy.setSuffix("px")
        self.mm_dy.setValue(int(mm.offset_y))
        for widget in (self.mm_side, self.mm_size, self.mm_dx, self.mm_dy):
            mm_row.addWidget(widget)
        form.addRow(self.t("set_mm"), mm_row)
        mm_tip = QLabel(self.t("set_mm_hint"))
        mm_tip.setObjectName("Muted")
        form.addRow("", mm_tip)

        tip = QLabel(self.t("set_assist_note"))
        tip.setObjectName("Muted")
        form.addRow("", tip)

        from ..sources.updater import guide_stats

        count, age, patch = guide_stats(self._config.guides.dir)
        text = self.t("set_guides_count").format(count=count)
        if age is None:
            text += " · " + self.t("set_guides_never")
        elif age < 1:
            text += " · " + self.t("set_guides_today")
        else:
            text += " · " + self.t("set_guides_days").format(days=f"{age:.0f}")
        if patch:
            text += f"（{patch}）"
        guide_row = QHBoxLayout()
        guide_label = QLabel(text)
        guide_label.setObjectName("Muted")
        guide_row.addWidget(guide_label)
        guide_row.addStretch(1)
        update_btn = QPushButton(self.t("set_guides_update"))
        update_btn.clicked.connect(self._update_guides_now)
        guide_row.addWidget(update_btn)
        holder = QWidget()
        holder.setLayout(guide_row)
        form.addRow(self.t("set_guides"), holder)
        return page

    # ---- 快捷键 ----
    def _update_guides_now(self) -> None:
        parent = self.parent()
        app = getattr(parent, "app", None)
        if app is None or not hasattr(app, "maybe_update_guides"):
            QMessageBox.information(self, self.t("set_update_no_main"), self.t("set_update_no_main_body"))
            return
        ok = app.maybe_update_guides(force=True)
        if ok:
            QMessageBox.information(
                self, self.t("set_update_started"), self.t("set_update_started_body")
            )
        else:
            QMessageBox.information(self, self.t("set_not_started"), self.t("set_not_started_body"))

    def _hotkey_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        keys = [f"F{index}" for index in range(1, 13)]
        self.hotkey_toggle = QComboBox()
        self.hotkey_toggle.addItems(keys)
        self.hotkey_toggle.setCurrentText(self._config.hotkeys.toggle_card)
        form.addRow(self.t("set_hotkey_toggle"), self.hotkey_toggle)
        self.hotkey_voice = QComboBox()
        self.hotkey_voice.addItems(keys)
        self.hotkey_voice.setCurrentText(self._config.hotkeys.test_voice)
        form.addRow(self.t("set_hotkey_voice"), self.hotkey_voice)
        tip = QLabel(self.t("set_hotkey_note"))
        tip.setObjectName("Muted")
        tip.setWordWrap(True)
        form.addRow("", tip)
        return page

    def _save(self) -> None:
        cfg = self._config
        cfg.overlay.enabled = self.enabled.isChecked()
        cfg.overlay.opacity = self.opacity.value() / 100.0
        cfg.overlay.dim_opacity = self.dim_opacity.value() / 100.0
        cfg.overlay.click_through = self.click_through.isChecked()
        cfg.voice.enabled = self.voice_enabled.isChecked()
        cfg.voice.speak = self.voice_speak.isChecked()
        cfg.voice.backend = self.backend.currentData()
        cfg.voice.edge_voice = voices.normalize_edge_voice(self.edge_voice.currentText())
        cfg.voice.rate = self.rate.value()
        cfg.voice.volume = self.volume.value()
        cfg.voice.min_interval = float(self.interval.value())
        cfg.app.language = self.lang_combo.currentData()
        cfg.voice.pack = self.pack.currentData()
        cfg.voice.wait_game_voice = self.wait_voice.isChecked()
        pack = voices.PACK_BY_ID.get(cfg.voice.pack)
        if pack is not None and pack.id != "custom" and pack.lang != cfg.app.language:
            cfg.voice.pack = voices.pack_for_language(cfg.app.language)
            edge, rate, volume = voices.resolve(
                cfg.voice.pack, cfg.voice.edge_voice, cfg.voice.rate, cfg.voice.volume
            )
            cfg.voice.edge_voice, cfg.voice.rate, cfg.voice.volume = edge, rate, volume
        if cfg.voice.pack != "custom" and cfg.voice.backend == "auto":
            cfg.voice.backend = "edge"
        cfg.theme.wallpaper = self._wallpaper_path
        cfg.theme.wallpaper_dim = self.wallpaper_dim.value() / 100.0
        cfg.assist.rune_alerts = self.assist_rune.isChecked()
        cfg.assist.name_strip = self.assist_names.isChecked()
        cfg.assist.fight_alerts = self.assist_fight.isChecked()
        cfg.assist.lane_alerts = self.assist_lane.isChecked()
        cfg.minimap.side = self.mm_side.currentData() or "auto"
        cfg.minimap.size_percent = self.mm_size.value()
        cfg.minimap.offset_x = self.mm_dx.value()
        cfg.minimap.offset_y = self.mm_dy.value()
        cfg.hotkeys.toggle_card = self.hotkey_toggle.currentText()
        cfg.hotkeys.test_voice = self.hotkey_voice.currentText()
        problems = validate_config(cfg)
        if problems:
            QMessageBox.warning(self, "配置有问题", "\n".join(problems))
            return
        try:
            path = save_config(cfg)
        except OSError as exc:
            QMessageBox.critical(self, "保存失败", f"写不了配置文件：\n{exc}")
            return
        self.saved_config = cfg
        self.saved_path = path
        self.accept()


class HelpDialog(QDialog):
    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(htext("title"))
        self.setStyleSheet(theme.STYLE)
        self.setMinimumSize(560, 460)
        layout = QVBoxLayout(self)
        text = QLabel()
        text.setWordWrap(True)
        text.setTextFormat(Qt.TextFormat.RichText)
        if ui_language() == "zh-CN":
            body = f"""
            <p><b>红线</b>：不读内存、不注入、不模拟按键、不改包、不代打。
            只做两件事：接收官方 GSI 报文、截自己屏幕做图像识别。</p>
            <p><b>快捷键</b>：{config.hotkeys.toggle_card} 显示/隐藏卡片；{config.hotkeys.test_voice} 试听语音。</p>
            <p><b>排错</b>：</p>
            <ul>
              <li>状态灯“GSI 监听”不亮：检查 31982 端口是否被旧实例占用。</li>
              <li>“对局中”不亮：游戏里确认启用了 GSI 配置
                  <code>gamestate_integration_coach.cfg</code>。</li>
              <li>“识别 n/10”偏低：确认游戏是窗口/无边框模式，且卡片没挡住顶部英雄栏。</li>
              <li>没有声音：先在设置里把后端改成“在线 edge-tts”，或检查系统音量。</li>
            </ul>
            """
        else:
            body = (
                f"<p>{htext('redline')}</p>"
                f"<p>{htext('hot', toggle=config.hotkeys.toggle_card, voice=config.hotkeys.test_voice)}</p>"
                f"<p>{htext('logs')}</p>"
            )
        text.setText(
            f"""
            <h2>{htext('title')} v{__version__}</h2>
            <p style="color:#6b7280;margin-top:-6px">DOTA2 GETTING STARTED Coach</p>
            {body}
            <p><b>{htext('cfg_logs')}</b>：<br>{config.config_path}<br>{config.log_dir}</p>
            """
        )
        layout.addWidget(text, 1)

        row = QHBoxLayout()
        open_logs = QPushButton(htext("open_logs"))
        open_logs.clicked.connect(lambda: self._open(config.log_dir))
        open_cfg = QPushButton(htext("open_config"))
        open_cfg.clicked.connect(lambda: self._open(config.config_path))
        row.addWidget(open_logs)
        row.addWidget(open_cfg)
        row.addStretch(1)
        close = QPushButton(htext("close"))
        close.setObjectName("Primary")
        close.clicked.connect(self.accept)
        row.addWidget(close)
        layout.addLayout(row)

    @staticmethod
    def _open(path: Path) -> None:
        try:
            if path.exists():
                os.startfile(str(path))  # type: ignore[attr-defined]
        except OSError:
            pass


FEEDBACK_EMAIL = "he-xiqing@qq.com"


class FeedbackDialog(QDialog):
    """意见反馈：用本机邮件客户端发到 FEEDBACK_EMAIL，或只保存到本地。"""

    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle(htext("fb_title"))
        self.setStyleSheet(theme.STYLE)
        self.resize(580, 460)
        layout = QVBoxLayout(self)
        intro_text = htext("fb_note") if ui_language() != "zh-CN" else (
            "写下遇到的问题或想要的功能。点「邮件发送」会打开你电脑上的邮件程序，"
            f"收件人是 {FEEDBACK_EMAIL}；也可以只保存到本地。"
        )
        intro = QLabel(intro_text)
        intro.setObjectName("Muted")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        mail = QLabel(f"{htext('fb_mail')}{FEEDBACK_EMAIL}")
        mail.setObjectName("Muted")
        mail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(mail)
        self.text = QTextEdit()
        self.text.setPlaceholderText(htext("fb_ph"))
        layout.addWidget(self.text, 1)
        row = QHBoxLayout()
        open_dir = QPushButton(htext("fb_open"))
        open_dir.clicked.connect(lambda: self._open_dir())
        row.addWidget(open_dir)
        copy_btn = QPushButton(htext("fb_copy"))
        copy_btn.clicked.connect(self._copy)
        row.addWidget(copy_btn)
        row.addStretch(1)
        cancel = QPushButton(htext("cancel"))
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        save = QPushButton(htext("fb_save"))
        save.clicked.connect(self._save)
        row.addWidget(save)
        send = QPushButton(htext("fb_send"))
        send.setObjectName("Primary")
        send.clicked.connect(self._send)
        row.addWidget(send)
        layout.addLayout(row)

    def _content(self) -> str:
        content = self.text.toPlainText().strip()
        if not content:
            QMessageBox.information(self, "没有内容", "先写点内容再发送。")
        return content

    def _save_path(self, content: str) -> Path:
        folder = self._config.log_dir / "feedback"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"feedback-{datetime.now():%Y%m%d-%H%M%S}.txt"
        path.write_text(content + "\n", encoding="utf-8")
        return path

    def _save(self) -> None:
        content = self._content()
        if not content:
            return
        try:
            path = self._save_path(content)
        except OSError as exc:
            QMessageBox.critical(self, "保存失败", f"写不了文件：\n{exc}")
            return
        QMessageBox.information(self, "已保存", f"反馈已保存到：\n{path}")
        self.accept()

    def _copy(self) -> None:
        content = self._content()
        if not content:
            return
        QGuiApplication.clipboard().setText(content)
        QMessageBox.information(self, "已复制", "内容已复制到剪贴板。")

    def _send(self) -> None:
        content = self._content()
        if not content:
            return
        subject = "DOTA2 入门教练反馈"
        body = content
        if len(body) > 1500:
            body = body[:1500] + "\n…（内容过长已截断，完整版可先保存到本地）"
        url = QUrl(
            f"mailto:{FEEDBACK_EMAIL}?subject={quote(subject)}&body={quote(body)}"
        )
        if QDesktopServices.openUrl(url):
            self.accept()
            return
        fallback = ""
        try:
            fallback = str(self._save_path(content))
        except OSError:
            pass
        QGuiApplication.clipboard().setText(content)
        QMessageBox.information(
            self,
            "没有找到邮件程序",
            f"内容已复制到剪贴板" + (f"，并保存到：\n{fallback}\n" if fallback else "。\n")
            + f"请手动发送到 {FEEDBACK_EMAIL}。",
        )
        self.accept()

    def _open_dir(self) -> None:
        folder = self._config.log_dir / "feedback"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            os.startfile(str(folder))  # type: ignore[attr-defined]
        except OSError:
            pass


class CoachPanel(QMainWindow):
    def __init__(self, app, config: Config) -> None:
        super().__init__()
        self.app = app
        self.config = config
        self.language = normalize_language(config.app.language)
        self.skills: dict[int, HeroSkills] = load_hero_skills(
            skills_file_for(config.data_dir, self.language)
        )
        self.nicknames = load_nicknames(config.data_dir / "hero_nicknames.json")
        self._icons: dict[str, QPixmap] = {}
        self._tiles: list[HeroTile] = []
        self._last_in_match: bool | None = None
        self._i18n: list[tuple[object, str, str, dict]] = []
        self._tray_actions: list[tuple[object, str]] = []
        self._step_boxes: list[QWidget] = []

        self.setWindowTitle(self.t("app_name"))
        self.resize(1460, 860)
        self._guides_timer = QTimer(self)
        self._guides_timer.setInterval(30 * 60 * 1000)
        self._guides_timer.timeout.connect(self._maybe_update_guides)
        self._guides_timer.start()
        QTimer.singleShot(5000, self._maybe_update_guides)
        app_instance = QApplication.instance()
        if app_instance is not None:
            app_instance.setStyleSheet(theme.STYLE)

        central = QWidget()
        central.setObjectName("Backdrop")
        self.setCentralWidget(central)
        self._wallpaper_pix = QPixmap()
        self.set_wallpaper(config.theme.wallpaper)
        root = QHBoxLayout(central)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(18)

        left = QVBoxLayout()
        left.setSpacing(14)
        left.addLayout(self._header())
        self.stack = QStackedWidget()
        self.stack.addWidget(self._idle_page())
        self.stack.addWidget(self._roster_page())
        self.stack.addWidget(self._summary_page())
        left.addWidget(self.stack, 1)
        root.addLayout(left, 1)
        root.addWidget(self._sidebar())

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(500)
        self.refresh()

        self.hotkeys = Hotkeys(
            self._toggle_card,
            self._test_voice,
            toggle_key=config.hotkeys.toggle_card,
            voice_key=config.hotkeys.test_voice,
        )
        problems = self.hotkeys.register(QApplication.instance())
        if problems:
            print(f"[快捷键] 注册失败：{', '.join(problems)}（可能被其它软件占用）")

        self._tray: QSystemTrayIcon | None = None
        self._build_tray()

        QTimer.singleShot(600, self._auto_start)

    def t(self, name: str, **fmt: object) -> str:
        return tr(self.language, name, **fmt)

    def _bind(self, widget, name: str, **fmt: object):
        self._i18n.append((widget, "setText", name, fmt))
        widget.setText(self.t(name, **fmt))
        return widget

    def _retranslate_ui(self) -> None:
        self.language = normalize_language(self.config.app.language)
        from ..coach.texts import set_language as set_texts_language

        set_texts_language(self.language)
        self.skills = load_hero_skills(
            skills_file_for(self.config.data_dir, self.language)
        )
        self.setWindowTitle(self.t("app_name"))
        for widget, method, key, fmt in self._i18n:
            getattr(widget, method)(self.t(key, **fmt))
        for action, key in self._tray_actions:
            action.setText(self.t(key))
        for tile in self._tiles:
            tile.placeholder = self.t("recognizing")
        for box in self._step_boxes:
            box.setVisible(self.language.startswith("zh"))
        self.footer.setText(f"v{__version__} · " + self.t("local_run"))
        self._last_in_match = None
        self.refresh()

    # ------------------------------------------------------------------
    # 布局
    # ------------------------------------------------------------------
    def _header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        title = self._bind(QLabel(), "app_name")
        title.setObjectName("H1")
        tag = self._bind(QLabel(), "tag")
        tag.setObjectName("Tag")
        row.addWidget(title)
        row.addWidget(tag)
        row.addStretch(1)
        game_guide = self._bind(QPushButton(), "guide")
        game_guide.setToolTip("打开 Dota2 官方英雄攻略页")
        game_guide.clicked.connect(self._open_game_guide)
        build_guide = self._bind(QPushButton(), "build")
        build_guide.setToolTip("游戏内攻略/出装顺序怎么用")
        build_guide.clicked.connect(self._open_build_guide)
        row.addWidget(game_guide)
        row.addWidget(build_guide)
        settings = self._bind(QPushButton(), "settings")
        settings.clicked.connect(self._open_settings)
        feedback = self._bind(QPushButton(), "feedback")
        feedback.clicked.connect(self._open_feedback)
        help_button = self._bind(QPushButton(), "help")
        help_button.clicked.connect(self._open_help)
        row.addWidget(settings)
        row.addWidget(feedback)
        row.addWidget(help_button)
        return row

    def _idle_page(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(12)
        headline = self._bind(QLabel(), "idle_head")
        headline.setObjectName("H1")
        sub = self._bind(QLabel(), "idle_sub")
        sub.setObjectName("Muted")
        sub.setWordWrap(True)
        layout.addWidget(headline)
        layout.addWidget(sub)
        f8 = self._bind(QLabel(), "f8", key=self.config.hotkeys.toggle_card)
        self.f8_label = f8
        f8.setStyleSheet(
            f"background: #EAF1FF; color: {theme.PRIMARY}; border: 1px solid #C7DBFF;"
            " border-radius: 10px; padding: 12px 16px; font-weight: 700;"
        )
        f8.setFont(theme.font(16, bold=True))
        layout.addWidget(f8)
        for key in ("idle_1", "idle_2", "idle_3", "idle_4"):
            label = self._bind(QLabel(), key)
            label.setObjectName("Muted")
            layout.addWidget(label)
        layout.addSpacing(10)
        steps = QHBoxLayout()
        steps.setSpacing(12)
        feature_cards = (
            ("开局", "识别 10 人阵容，标注每个英雄的两条关键技能"),
            ("对线", "分路、眼位、符点、对位强弱与出门补给"),
            ("团战", "该打谁、该绕开谁、小心哪个技能"),
        )
        for title, body_text in (feature_cards if self.language.startswith("zh") else ()):
            box = QFrame()
            box.setStyleSheet(
                f"QFrame {{ background: {theme.BG}; border: 1px solid {theme.BORDER};"
                f" border-radius: 8px; }}"
            )
            inner = QVBoxLayout(box)
            inner.setContentsMargins(14, 12, 14, 12)
            inner.setSpacing(4)
            head = QLabel(title)
            head.setStyleSheet(f"font-weight: 700; color: {theme.PRIMARY}; background: transparent;")
            text_label = QLabel(body_text)
            text_label.setObjectName("Muted")
            text_label.setWordWrap(True)
            text_label.setStyleSheet(f"color: {theme.MUTED}; background: transparent;")
            inner.addWidget(head)
            inner.addWidget(text_label)
            steps.addWidget(box, 1)
            self._step_boxes.append(box)
        layout.addLayout(steps)
        layout.addStretch(1)
        start = self._bind(QPushButton(), "start")
        start.setObjectName("Primary")
        start.setFixedWidth(120)
        start.clicked.connect(self._start)
        layout.addWidget(start)
        return card

    def _summary_page(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(10)
        self.summary_title = self._bind(QLabel(), "summary_last")
        self.summary_title.setObjectName("H1")
        self.summary_stats = QLabel("—")
        self.summary_stats.setObjectName("Muted")
        self.summary_lines = QLabel("")
        self.summary_lines.setWordWrap(True)
        self.summary_lines.setStyleSheet(f"color: {theme.TEXT}; font-size: 13px;")
        self.summary_hint = QLabel("")
        self.summary_hint.setWordWrap(True)
        self.summary_hint.setStyleSheet(
            f"color: {theme.PRIMARY}; font-weight: 700; font-size: 14px;"
        )
        layout.addWidget(self.summary_title)
        layout.addWidget(self.summary_stats)
        layout.addSpacing(6)
        layout.addWidget(self.summary_lines)
        layout.addSpacing(8)
        layout.addWidget(self.summary_hint)
        layout.addStretch(1)
        back = self._bind(QPushButton(), "back_home")
        back.setFixedWidth(120)
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back)
        return card

    def _roster_page(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(10)

        head = QHBoxLayout()
        title = self._bind(QLabel(), "roster")
        title.setObjectName("H2")
        self.roster_hint = self._bind(QLabel(), "roster_sub")
        self.roster_hint.setObjectName("Muted")
        head.addWidget(title)
        head.addWidget(self.roster_hint)
        head.addStretch(1)
        self.threat_label = QLabel("")
        self.threat_label.setObjectName("Muted")
        head.addWidget(self.threat_label)
        outer.addLayout(head)

        for team, key in (("ally", "allies"), ("enemy", "enemies")):
            row = QHBoxLayout()
            row.setSpacing(10)
            tag = self._bind(QLabel(), key)
            tag.setFixedWidth(30)
            tag.setStyleSheet(
                f"color: {theme.SUCCESS if team == 'ally' else theme.DANGER}; font-weight: 700;"
            )
            row.addWidget(tag, 0, Qt.AlignmentFlag.AlignTop)
            grid = QGridLayout()
            grid.setSpacing(10)
            for index in range(5):
                tile = HeroTile()
                tile.placeholder = self.t("recognizing")
                self._tiles.append(tile)
                grid.addWidget(tile, 0, index)
            row.addLayout(grid, 1)
            outer.addLayout(row)
        outer.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        scroll.setWidget(card)
        return scroll

    def _sidebar(self) -> QWidget:
        side = QFrame()
        side.setObjectName("Side")
        side.setFixedWidth(330)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        status_title = self._bind(QLabel(), "status")
        status_title.setObjectName("H3")
        layout.addWidget(status_title)

        self.dot_gsi, row_gsi, self.gsi_label = self._status_row("", theme.MUTED)
        self._i18n.append((self.gsi_label, "setText", "gsi", {}))
        layout.addLayout(row_gsi)
        self.dot_match, row_match, self.match_label = self._status_row("", theme.MUTED)
        self._i18n.append((self.match_label, "setText", "in_match", {}))
        layout.addLayout(row_match)
        self.dot_known, row_known, self.known_label = self._status_row(self.t("identify") + " 0/10", theme.MUTED)
        layout.addLayout(row_known)

        layout.addSpacing(6)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {theme.BORDER};")
        layout.addWidget(line)

        match_title = self._bind(QLabel(), "current_match")
        match_title.setObjectName("H3")
        layout.addWidget(match_title)
        self.match_hero = self._bind(QLabel(), "not_started")
        self.match_hero.setObjectName("H2")
        layout.addWidget(self.match_hero)
        self.match_meta = QLabel("—")
        self.match_meta.setObjectName("Muted")
        layout.addWidget(self.match_meta)

        hints_title = self._bind(QLabel(), "recent")
        hints_title.setObjectName("Muted")
        layout.addWidget(hints_title)
        self.hints = QLabel("—")
        self.hints.setWordWrap(True)
        self.hints.setStyleSheet(f"color: {theme.TEXT}; font-size: 12px;")
        layout.addWidget(self.hints)

        layout.addStretch(1)
        self.primary = QPushButton(self.t("start"))
        self.primary.setObjectName("Primary")
        self.primary.clicked.connect(self._toggle_run)
        layout.addWidget(self.primary)
        self.card_button = QPushButton(self.t("hide_card"))
        self._i18n.append((self.card_button, "setText", "hide_card", {}))
        self.card_button.clicked.connect(self._toggle_card)
        layout.addWidget(self.card_button)

        self.footer = QLabel(f"v{__version__} · " + self.t("local_run"))
        self.footer_key = "local_run"
        self.footer.setObjectName("Muted")
        layout.addWidget(self.footer)
        return side

    def _status_row(self, text: str, color: str):
        row = QHBoxLayout()
        dot = Dot(color)
        label = QLabel(text)
        row.addWidget(dot)
        row.addWidget(label)
        row.addStretch(1)
        return dot, row, label

    # ------------------------------------------------------------------
    # 刷新
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        try:
            status = self.app.status()
        except Exception as exc:  # noqa: BLE001 - 状态读取失败不该拖垮界面
            print(f"[面板] 读取状态失败：{exc}", file=sys.stderr)
            return
        running = bool(status.get("running"))
        in_match = bool(status.get("in_match"))
        known = int(status.get("known") or 0)

        self.dot_gsi.set_color(theme.SUCCESS if running else theme.MUTED)
        self.dot_match.set_color(theme.WARNING if in_match else theme.MUTED)
        self.dot_known.set_color(theme.SUCCESS if known >= 8 else (theme.WARNING if known else theme.MUTED))
        self.known_label.setText(f"{self.t('identify')} {known}/10")
        self.primary.setText(self.t("stop") if running else self.t("start"))

        hero = status.get("hero_name") or self.t("not_started")
        self.match_hero.setText(hero if (in_match or known) else self.t("not_started"))
        if in_match or known:
            clock = status.get("clock_text") or "0:00"
            phase = status.get("phase") or "—"
            self.match_meta.setText(f"{clock} · {phase_name(phase)}")
        else:
            self.match_meta.setText("—")

        hints = [h for h in (status.get("hints") or []) if h]
        self.hints.setText("\n".join(f"· {h}" for h in hints[-3:]) if hints else "—")

        summary = status.get("summary")
        if summary:
            self.stack.setCurrentIndex(2)
            self._fill_summary(summary)
            return
        show_roster = bool(in_match or known >= 5)
        self.stack.setCurrentIndex(1 if show_roster else 0)
        if show_roster and known:
            self._fill_roster(status)
            counts = status.get("threat_counts") or {}
            label_map = {
                "先手": self.t("trait_initiator"),
                "爆发": self.t("trait_nuker"),
                "隐身": self.t("threat_stealth"),
            }
            parts = [
                f"{label_map[label]}{counts.get(label, 0)}"
                for label in ("先手", "爆发", "隐身")
                if counts.get(label)
            ]
            self.threat_label.setText(self.t("threat") + "：" + " · ".join(parts) if parts else "")

    def _alias(self, short: str) -> str:
        text = self.nicknames.get(short) or ""
        if not text or self.language.startswith("zh"):
            return text
        parts = [part.strip() for part in text.split("·") if part.strip()]
        return parts[-1] if parts else text

    def _localize_threats(self, threats) -> tuple[str, ...]:
        label_map = {
            "先手": "threat_init_short",
            "爆发": "threat_nuke_short",
            "隐身": "threat_invis_short",
        }
        return tuple(self.t(label_map[t]) if t in label_map else t for t in threats)

    def _localize_traits(self, text: str) -> str:
        if not text:
            return text
        mapping = {
            "核心": "trait_core",
            "辅助": "trait_support",
            "爆发": "trait_nuker",
            "控制": "trait_control",
            "先手": "trait_initiator",
            "肉盾": "trait_durable",
            "机动": "trait_escape",
            "推塔": "trait_pusher",
            "打野": "trait_jungle",
        }
        parts = [part.strip() for part in text.split("·") if part.strip()]
        return " · ".join(self.t(mapping[p]) if p in mapping else p for p in parts)

    def _fill_roster(self, status: dict) -> None:
        teams = [(status.get("allies") or []), (status.get("enemies") or [])]
        index = 0
        for team, heroes in zip(("ally", "enemy"), teams):
            for slot in range(5):
                tile = self._tiles[index]
                index += 1
                hero = heroes[slot] if slot < len(heroes) else None
                if not hero or not hero.get("known"):
                    tile.show_hero(
                        hero.get("name") if hero else "?", None, [], team=team, known=False
                    )
                    continue
                tips = self.skills.get(int(hero.get("hero_id") or 0))
                display_name = hero.get("name") or "?"
                if tips is not None and not self.language.startswith("zh-CN"):
                    display_name = tips.name or display_name
                tile.show_hero(
                    display_name,
                    self._icon(hero.get("short") or ""),
                    tips.tips(2) if tips else [],
                    team=team,
                    threats=self._localize_threats(hero.get("threats") or ()),
                    traits=self._localize_traits(hero.get("traits") or ""),
                    alias=self._alias(hero.get("short") or ""),
                )

    def _fill_summary(self, summary: dict) -> None:
        result = summary.get("result") or "—"
        self.summary_title.setText(f"上一局 · {result}")
        hero = summary.get("hero") or "—"
        kda = summary.get("kda") or "—"
        cs = summary.get("cs") or "—"
        gpm = summary.get("gpm") or 0
        duration = summary.get("duration") or "—"
        self.summary_stats.setText(
            f"{hero} · KDA {kda} · 正反补 {cs} · {gpm} GPM · {duration}"
        )
        lines = [
            line
            for line in (summary.get("lines") or [])
            if not line.startswith("结果：") and "正反补" not in line
        ]
        self.summary_lines.setText("\n".join(f"· {line}" for line in lines))
        self.summary_hint.setText(summary.get("hint") or "")

    def _icon(self, short: str) -> QPixmap | None:
        if not short:
            return None
        if short in self._icons:
            return self._icons[short]
        path = self.config.vision.icons_dir / f"{short}.png"
        pixmap = QPixmap(str(path)) if path.exists() else QPixmap()
        self._icons[short] = pixmap
        return pixmap

    # ------------------------------------------------------------------
    # 动作
    # ------------------------------------------------------------------
    def _auto_start(self) -> None:
        if not self.app.running:
            self._start()

    def _start(self) -> None:
        ok = self.app.start()
        if not ok:
            QMessageBox.warning(
                self,
                "启动失败",
                "端口 31982 被占用，可能已有一个教练实例在运行。\n请先关掉旧窗口再点开始。",
            )
        self.refresh()

    def _toggle_run(self) -> None:
        if self.app.running:
            self.app.stop()
        else:
            self._start()
        self.refresh()

    def _toggle_card(self) -> None:
        overlay = getattr(self.app, "overlay", None)
        if overlay is None:
            return
        overlay.setVisible(not overlay.isVisible())
        self.card_button.setText(self.t("hide_card") if overlay.isVisible() else self.t("show_card"))

    def _test_voice(self) -> None:
        speaker = getattr(self.app, "speaker", None)
        if speaker is None:
            return
        speaker.say("语音测试：听到这句话说明朗读正常", force=True)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.app.config, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        cfg = getattr(dialog, "saved_config", None)
        if cfg is None:
            return
        changed_language = normalize_language(cfg.app.language) != self.language
        self.config = cfg
        if changed_language:
            self._retranslate_ui()
        problems = self.hotkeys.rebind(cfg.hotkeys.toggle_card, cfg.hotkeys.test_voice)
        if problems:
            QMessageBox.warning(
                self,
                "快捷键被占用",
                "以下快捷键注册失败（可能被其它软件占用）：\n" + "\n".join(problems),
            )
        self.f8_label.setText(self.t("f8", key=cfg.hotkeys.toggle_card))
        self.set_wallpaper(cfg.theme.wallpaper)
        restart = self.app.apply_settings(cfg)
        if restart:
            QMessageBox.information(
                self, "已保存", "以下设置需要重启程序后生效：\n" + "、".join(restart)
            )
        else:
            QMessageBox.information(self, "已保存", "设置已生效。")
        self.refresh()

    def _open_help(self) -> None:
        HelpDialog(self.app.config, self).exec()

    def _open_game_guide(self) -> None:
        short = (self.app.status().get("hero_short") or "").strip()
        url = official_guide_url(short)
        QDesktopServices.openUrl(QUrl(url))

    def _open_build_guide(self) -> None:
        path = ensure_guide(self.app.config.data_dir, self.language)
        if not path.exists():
            QMessageBox.information(
                self, self.t("build"), self.t("guide_missing")
            )
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def set_wallpaper(self, path: str) -> None:
        pix = QPixmap()
        if path:
            candidate = Path(path)
            if not candidate.is_absolute():
                candidate = self.config.root / path
            if candidate.exists():
                pix = QPixmap(str(candidate))
        self._wallpaper_pix = pix
        self._wallpaper_dim = float(getattr(self.config.theme, "wallpaper_dim", 0.55))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._wallpaper_pix.isNull():
            return
        painter = QPainter(self)
        target = self.rect()
        scaled = self._wallpaper_pix.scaled(
            target.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (scaled.width() - target.width()) // 2
        y = (scaled.height() - target.height()) // 2
        painter.drawPixmap(-x, -y, scaled)
        alpha = int(max(0.0, min(1.0, self._wallpaper_dim)) * 255)
        painter.fillRect(target, QColor(255, 255, 255, alpha))
        painter.end()

    def _maybe_update_guides(self) -> None:
        try:
            self.app.maybe_update_guides()
        except Exception:  # noqa: BLE001
            pass

    def _open_feedback(self) -> None:
        FeedbackDialog(self.config, self).exec()

    # ------------------------------------------------------------------
    # 托盘
    # ------------------------------------------------------------------
    def _build_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = app_icon(self.config.data_dir)
        if icon.isNull():
            icon = fallback_icon()
        tray = QSystemTrayIcon(icon, self)
        tray.setToolTip(self.t("app_name"))
        from PyQt6.QtWidgets import QMenu

        menu = QMenu()
        self._tray_actions = []
        show_action = menu.addAction(self.t("tray_show"), self.showNormal)
        self._tray_actions.append((show_action, "tray_show"))
        hide_action = menu.addAction(self.t("hide_card"), self._toggle_card)
        self._tray_actions.append((hide_action, "hide_card"))
        menu.addAction(self.t("guide"), self._open_game_guide)
        menu.addAction(self.t("build"), self._open_build_guide)
        help_action = menu.addAction(self.t("help"), self._open_help)
        self._tray_actions.append((help_action, "help"))
        menu.addSeparator()
        quit_action = menu.addAction(self.t("tray_quit"), self._quit)
        self._tray_actions.append((quit_action, "tray_quit"))
        tray.setContextMenu(menu)
        tray.activated.connect(lambda reason: self.showNormal() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        tray.show()
        self._tray = tray

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt 命名
        if self._tray is not None:
            event.ignore()
            self.hide()
            self._tray.showMessage(htext("title"), htext("tray_min"), QSystemTrayIcon.MessageIcon.Information, 2000)
            return
        self._quit()

    def _quit(self) -> None:
        self.hotkeys.unregister()
        try:
            self.app._shutdown()
        finally:
            QApplication.instance().quit()


def run_panel(qt_app: QApplication, coach, config: Config) -> int:
    coach.panel_mode = True
    panel = CoachPanel(coach, config)
    icon = app_icon(config.data_dir)
    if not icon.isNull():
        panel.setWindowIcon(icon)
    coach.overlay.hide()
    panel.show()
    return qt_app.exec()
