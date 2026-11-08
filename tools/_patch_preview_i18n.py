"""把试听示例句换成 i18n。"""

from pathlib import Path

p = Path("src/dota2coach/ui/panel.py")
s = p.read_text(encoding="utf-8")
old = 'preview.say("这是当前语音效果，可以在设置里换语音包。", force=True)'
new = 'preview.say(self.t("set_preview_text"), force=True)'
if old in s:
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("preview:", "patched" if old in s else "not found")
