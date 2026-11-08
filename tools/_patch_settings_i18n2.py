"""把设置对话框的文案换成 i18n key。"""

from pathlib import Path

P = Path("src/dota2coach/ui/panel.py")
s = P.read_text(encoding="utf-8")

pairs = [
    ('self.setWindowTitle("设置")', 'self.setWindowTitle(self.t("set_title"))'),
    ('form.addRow("界面语言", self.lang_combo)', 'form.addRow(self.t("set_language"), self.lang_combo)'),
    ('self._wallpaper_path or "（默认浅色背景）"', 'self._wallpaper_path or self.t("set_wallpaper_default")'),
    ('self.wallpaper_label.setText("（默认浅色背景）")', 'self.wallpaper_label.setText(self.t("set_wallpaper_default"))'),
    ('form.addRow("背景图", self.wallpaper_label)', 'form.addRow(self.t("set_wallpaper"), self.wallpaper_label)'),
    ('QPushButton("选择图片…")', 'QPushButton(self.t("set_choose_image"))'),
    ('QPushButton("清除")', 'QPushButton(self.t("set_clear"))'),
    ('form.addRow("白色蒙层", row2)', 'form.addRow(self.t("set_wallpaper_dim"), row2)'),
    ('QLabel("蒙层越高，文字越清楚；建议用深色、图案不抢眼的图片（jpg/png/webp）。")', 'QLabel(self.t("set_wallpaper_note"))'),
    ('self, "选择背景图", start,', 'self, self.t("set_choose_title"), start,'),
    ('QMessageBox.warning(self, "试听失败", str(exc))', 'QMessageBox.warning(self, self.t("set_test_failed"), str(exc))'),
    ('QCheckBox("显示覆盖层卡片")', 'QCheckBox(self.t("set_overlay_cards"))'),
    ('form.addRow("启用", self.enabled)', 'form.addRow(self.t("set_enable"), self.enabled)'),
    ('form.addRow("清晰状态", row)', 'form.addRow(self.t("set_clear_state"), row)'),
    ('form.addRow("模糊状态", row2)', 'form.addRow(self.t("set_dim_state"), row2)'),
    ('QLabel("清晰状态 = 语音播报后 10 秒；模糊状态 = 平时。清晰不能比模糊更淡。")', 'QLabel(self.t("set_overlay_note"))'),
    ('QCheckBox("卡片不挡鼠标（点击穿透）")', 'QCheckBox(self.t("set_click_through"))'),
    ('QLabel("提示：想拖动卡片时先关闭点击穿透。")', 'QLabel(self.t("set_click_hint"))'),
    ('QCheckBox("启用提示音与朗读")', 'QCheckBox(self.t("set_voice_enable"))'),
    ('form.addRow("启用", self.voice_enabled)', 'form.addRow(self.t("set_enable"), self.voice_enabled)'),
    ('QCheckBox("朗读提示文字（关闭后只响提示音）")', 'QCheckBox(self.t("set_voice_speak"))'),
    ('form.addRow("朗读", self.voice_speak)', 'form.addRow(self.t("set_row_speak"), self.voice_speak)'),
    ('form.addRow("语音包", self.pack)', 'form.addRow(self.t("set_voice_pack"), self.pack)'),
    ('QCheckBox("游戏正在出声时，等它说完再朗读（最多 4 秒）")', 'QCheckBox(self.t("set_wait_voice"))'),
    ('form.addRow("避让", self.wait_voice)', 'form.addRow(self.t("set_row_wait"), self.wait_voice)'),
    ('("自动（SAPI 失败转在线）", "auto")', '(self.t("set_backend_auto"), "auto")'),
    ('("系统语音 SAPI", "sapi")', '(self.t("set_backend_sapi"), "sapi")'),
    ('("在线 edge-tts", "edge")', '(self.t("set_backend_edge"), "edge")'),
    ('("只响提示音", "beep")', '(self.t("set_backend_beep"), "beep")'),
    ('("静音", "none")', '(self.t("set_backend_none"), "none")'),
    ('form.addRow("后端", self.backend)', 'form.addRow(self.t("set_backend"), self.backend)'),
    ('("晓晓（女声）", "zh-CN-XiaoxiaoNeural")', '(self.t("set_voice_xiaoxiao"), "zh-CN-XiaoxiaoNeural")'),
    ('("云希（男声）", "zh-CN-YunxiNeural")', '(self.t("set_voice_yunxi"), "zh-CN-YunxiNeural")'),
    ('("晓伊", "zh-CN-XiaoyiNeural")', '(self.t("set_voice_xiaoyi"), "zh-CN-XiaoyiNeural")'),
    ('("云健", "zh-CN-YunjianNeural")', '(self.t("set_voice_yunjian"), "zh-CN-YunjianNeural")'),
    ('form.addRow("在线音色", self.edge_voice)', 'form.addRow(self.t("set_edge_voice"), self.edge_voice)'),
    ('form.addRow("语速", self.rate)', 'form.addRow(self.t("set_rate"), self.rate)'),
    ('form.addRow("音量", self.volume)', 'form.addRow(self.t("set_volume"), self.volume)'),
    ('form.addRow("同句最短间隔（秒）", self.interval)', 'form.addRow(self.t("set_interval"), self.interval)'),
    ('QPushButton("试听当前语音")', 'QPushButton(self.t("set_test_voice"))'),
    ('QCheckBox("符点/神龛/莲花刷新前播报")', 'QCheckBox(self.t("set_assist_rune"))'),
    ('form.addRow("刷新播报", self.assist_rune)', 'form.addRow(self.t("set_row_rune"), self.assist_rune)'),
    ('QCheckBox("在对局顶部头像下显示英雄名字")', 'QCheckBox(self.t("set_assist_names"))'),
    ('form.addRow("名字显示", self.assist_names)', 'form.addRow(self.t("set_row_names"), self.assist_names)'),
    ('QCheckBox("10 分钟后团战 / 小地图预警")', 'QCheckBox(self.t("set_assist_fight"))'),
    ('form.addRow("团战提醒", self.assist_fight)', 'form.addRow(self.t("set_row_fight"), self.assist_fight)'),
    ('QCheckBox("对线期分路/对位/补给提醒")', 'QCheckBox(self.t("set_assist_lane"))'),
    ('form.addRow("对线提醒", self.assist_lane)', 'form.addRow(self.t("set_row_lane"), self.assist_lane)'),
    ('self.mm_side.addItem("自动", "auto")', 'self.mm_side.addItem(self.t("set_mm_auto"), "auto")'),
    ('self.mm_side.addItem("左下角", "left")', 'self.mm_side.addItem(self.t("set_mm_left"), "left")'),
    ('self.mm_side.addItem("右下角", "right")', 'self.mm_side.addItem(self.t("set_mm_right"), "right")'),
    ('form.addRow("小地图", mm_row)', 'form.addRow(self.t("set_mm"), mm_row)'),
    ('QLabel("位置/大小用于自动识别失败时兜底；X/Y 是额外像素偏移。")', 'QLabel(self.t("set_mm_hint"))'),
    ('QLabel("关掉的项目不会显示、也不会朗读；保存后立即生效。")', 'QLabel(self.t("set_assist_note"))'),
    ('text = f"{count} 条"', 'text = self.t("set_guides_count").format(count=count)'),
    ('text += " · 尚未更新"', 'text += " · " + self.t("set_guides_never")'),
    ('text += " · 今天更新"', 'text += " · " + self.t("set_guides_today")'),
    ('text += f" · 更新于 {age:.0f} 天前"', 'text += " · " + self.t("set_guides_days").format(days=f"{age:.0f}")'),
    ('QPushButton("立即更新")', 'QPushButton(self.t("set_guides_update"))'),
    ('form.addRow("攻略库", holder)', 'form.addRow(self.t("set_guides"), holder)'),
    ('form.addRow("呼出 / 隐藏卡片", self.hotkey_toggle)', 'form.addRow(self.t("set_hotkey_toggle"), self.hotkey_toggle)'),
    ('form.addRow("试听语音", self.hotkey_voice)', 'form.addRow(self.t("set_hotkey_voice"), self.hotkey_voice)'),
    ('QLabel("只支持 F1–F12；被其它软件占用时会提示注册失败，换一个即可。保存后立即生效。")', 'QLabel(self.t("set_hotkey_note"))'),
    ('QMessageBox.information(self, "无法更新", "请从主窗口的设置进入。")', 'QMessageBox.information(self, self.t("set_update_no_main"), self.t("set_update_no_main_body"))'),
    ('"已开始更新", "攻略库正在后台更新，完成后重启程序生效。\\n日志：logs\\\\guides_update.log"', 'self.t("set_update_started"), self.t("set_update_started_body")'),
    ('QMessageBox.information(self, "未启动", "可能已经在更新中，稍后再试。")', 'QMessageBox.information(self, self.t("set_not_started"), self.t("set_not_started_body"))'),
]

missing = []
for old, new in pairs:
    if old in s:
        s = s.replace(old, new)
    else:
        missing.append(old[:40])

P.write_text(s, encoding="utf-8")
print("missing:", missing)
