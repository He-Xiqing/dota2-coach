"""设置页文案微调：团战时间与偏移单位。"""

from pathlib import Path

p = Path("src/dota2coach/ui/panel.py")
s = p.read_text(encoding="utf-8")
s = s.replace('QCheckBox("20 分钟后团战 / 小地图预警")', 'QCheckBox("10 分钟后团战 / 小地图预警")')
s = s.replace(
    "        self.mm_dx = QSpinBox()\n        self.mm_dx.setRange(-300, 300)",
    '        self.mm_dx = QSpinBox()\n        self.mm_dx.setRange(-300, 300)\n        self.mm_dx.setSuffix("px")',
)
s = s.replace(
    "        self.mm_dy = QSpinBox()\n        self.mm_dy.setRange(-300, 300)",
    '        self.mm_dy = QSpinBox()\n        self.mm_dy.setRange(-300, 300)\n        self.mm_dy.setSuffix("px")',
)
p.write_text(s, encoding="utf-8")
print("tweaked")
