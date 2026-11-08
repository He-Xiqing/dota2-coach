"""修正 SettingsDialog：先存 config 再取标题文案。"""

from pathlib import Path

p = Path("src/dota2coach/ui/panel.py")
s = p.read_text(encoding="utf-8")
old = """        super().__init__(parent)
        self.setWindowTitle(self.t("set_title"))
        self.setStyleSheet(theme.STYLE)
        self._applying_pack = False
        self.resize(560, 430)
        self._config = copy.deepcopy(config)"""
new = """        super().__init__(parent)
        self._config = copy.deepcopy(config)
        self.setWindowTitle(self.t("set_title"))
        self.setStyleSheet(theme.STYLE)
        self._applying_pack = False
        self.resize(560, 430)"""
if old in s:
    s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("reordered")
else:
    print("anchor not found")
