"""设置页：小地图位置/大小/偏移。"""

from pathlib import Path

P = Path("src/dota2coach/ui/panel.py")
s = P.read_text(encoding="utf-8")

anchor = """        tip = QLabel("关掉的项目不会显示、也不会朗读；保存后立即生效。")
        tip.setObjectName("Muted")
        form.addRow("", tip)
"""
insert = """        mm = self._config.minimap
        mm_row = QHBoxLayout()
        self.mm_side = QComboBox()
        self.mm_side.addItem("自动", "auto")
        self.mm_side.addItem("左下角", "left")
        self.mm_side.addItem("右下角", "right")
        idx = self.mm_side.findData(mm.side)
        self.mm_side.setCurrentIndex(max(0, idx))
        self.mm_size = QSpinBox()
        self.mm_size.setRange(60, 160)
        self.mm_size.setSuffix("%")
        self.mm_size.setValue(int(mm.size_percent))
        self.mm_dx = QSpinBox()
        self.mm_dx.setRange(-300, 300)
        self.mm_dx.setValue(int(mm.offset_x))
        self.mm_dy = QSpinBox()
        self.mm_dy.setRange(-300, 300)
        self.mm_dy.setValue(int(mm.offset_y))
        for widget in (self.mm_side, self.mm_size, self.mm_dx, self.mm_dy):
            mm_row.addWidget(widget)
        form.addRow("小地图", mm_row)
        mm_tip = QLabel("位置/大小用于自动识别失败时兜底；X/Y 是额外像素偏移。")
        mm_tip.setObjectName("Muted")
        form.addRow("", mm_tip)

        tip = QLabel("关掉的项目不会显示、也不会朗读；保存后立即生效。")
        tip.setObjectName("Muted")
        form.addRow("", tip)
"""
if anchor in s and "self.mm_side" not in s:
    s = s.replace(anchor, insert, 1)

save_anchor = "        cfg.assist.lane_alerts = self.assist_lane.isChecked()\n"
save_add = (
    "        cfg.assist.lane_alerts = self.assist_lane.isChecked()\n"
    "        cfg.minimap.side = self.mm_side.currentData() or \"auto\"\n"
    "        cfg.minimap.size_percent = self.mm_size.value()\n"
    "        cfg.minimap.offset_x = self.mm_dx.value()\n"
    "        cfg.minimap.offset_y = self.mm_dy.value()\n"
)
if save_anchor in s and "cfg.minimap.side" not in s:
    s = s.replace(save_anchor, save_add, 1)
P.write_text(s, encoding="utf-8")

# 确保 QComboBox / QSpinBox / QHBoxLayout 已导入
head = P.read_text(encoding="utf-8")
for name in ("QComboBox", "QSpinBox"):
    if name not in head:
        head = head.replace(
            "from PyQt6.QtWidgets import (",
            "from PyQt6.QtWidgets import (" + name + ", ",
            1,
        )
P.write_text(head, encoding="utf-8")
print("panel patched")
