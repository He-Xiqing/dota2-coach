"""把反馈对话框按钮/提示换成多语言文案。"""

from pathlib import Path

P = Path("src/dota2coach/ui/panel.py")
s = P.read_text(encoding="utf-8")

repl = [
    ('self.setWindowTitle("意见反馈")', 'self.setWindowTitle(htext("fb_title"))'),
    (
        '''        intro = QLabel(
            "写下遇到的问题或想要的功能。点「邮件发送」会打开你电脑上的邮件程序，"
            f"收件人是 {FEEDBACK_EMAIL}；也可以只保存到本地。"
        )''',
        '''        intro_text = htext("fb_note") if ui_language() != "zh-CN" else (
            "写下遇到的问题或想要的功能。点「邮件发送」会打开你电脑上的邮件程序，"
            f"收件人是 {FEEDBACK_EMAIL}；也可以只保存到本地。"
        )
        intro = QLabel(intro_text)''',
    ),
    ('mail = QLabel(f"反馈邮箱：{FEEDBACK_EMAIL}")', 'mail = QLabel(f"{htext(\'fb_mail\')}{FEEDBACK_EMAIL}")'),
    ('QPushButton("打开目录")', 'QPushButton(htext("fb_open"))'),
    ('QPushButton("复制内容")', 'QPushButton(htext("fb_copy"))'),
    ('QPushButton("取消")', 'QPushButton(htext("cancel"))'),
    ('QPushButton("只保存到本地")', 'QPushButton(htext("fb_save"))'),
    ('QPushButton("邮件发送")', 'QPushButton(htext("fb_send"))'),
]
for old, new in repl:
    if old not in s:
        raise SystemExit("missing: " + old)
    s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8")

H = Path("src/dota2coach/coach/texts_help.py")
h = H.read_text(encoding="utf-8")
h = h.replace(
    '        "fb_save": "只保存到本地",',
    '        "fb_save": "只保存到本地",\n        "fb_title": "意见反馈",\n        "fb_mail": "反馈邮箱：",\n        "fb_open": "打开目录",\n        "cancel": "取消",',
    1,
)
h = h.replace(
    '        "fb_save": "Save locally",',
    '        "fb_save": "Save locally",\n        "fb_title": "Feedback",\n        "fb_mail": "Feedback email: ",\n        "fb_open": "Open folder",\n        "cancel": "Cancel",',
    1,
)
H.write_text(h, encoding="utf-8")
print("feedback patched")
