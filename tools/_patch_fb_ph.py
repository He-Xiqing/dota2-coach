"""补丁：反馈占位符与托盘气泡本地化。"""

from pathlib import Path

P = Path("src/dota2coach/ui/panel.py")
s = P.read_text(encoding="utf-8")
s = s.replace(
    'self.text.setPlaceholderText("例如：1920x1080 窗口模式下识别只有 7/10；希望加一个“敌方买活”提醒…")',
    'self.text.setPlaceholderText(htext("fb_ph"))',
    1,
)
s = s.replace(
    'self._tray.showMessage("DOTA2 入门教练", "已最小化到托盘，双击图标可恢复。", QSystemTrayIcon.MessageIcon.Information, 2000)',
    'self._tray.showMessage(htext("title"), htext("tray_min"), QSystemTrayIcon.MessageIcon.Information, 2000)',
    1,
)
P.write_text(s, encoding="utf-8")

H = Path("src/dota2coach/coach/texts_help.py")
h = H.read_text(encoding="utf-8")
h = h.replace(
    '        "fb_title": "意见反馈",',
    '        "fb_title": "意见反馈",\n        "fb_ph": "例如：1920x1080 窗口模式下识别只有 7/10；希望加一个“敌方买活”提醒…",\n        "tray_min": "已最小化到托盘，双击图标可恢复。",',
    1,
)
h = h.replace(
    '        "fb_title": "Feedback",',
    '        "fb_title": "Feedback",\n        "fb_ph": "e.g. only 7/10 heroes recognized in 1920x1080 windowed mode; please add a buyback reminder…",\n        "tray_min": "Minimized to tray — double-click the icon to restore.",',
    1,
)
H.write_text(h, encoding="utf-8")
print("placeholder+tray patched")
