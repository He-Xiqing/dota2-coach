"""把设置页标签接入 i18n，并按语言加载技能资料。"""

from pathlib import Path

p = Path("src/dota2coach/knowledge/skills.py")
s = p.read_text(encoding="utf-8")
if "SKILL_FILES" not in s:
    addition = '''

SKILL_FILES = {
    "zh-CN": "hero_skills.json",
    "zh-TW": "hero_skills.tchinese.json",
    "en": "hero_skills.english.json",
    "fr": "hero_skills.french.json",
    "ru": "hero_skills.russian.json",
    "de": "hero_skills.german.json",
    "pt": "hero_skills.brazilian.json",
    "es": "hero_skills.spanish.json",
    "tr": "hero_skills.turkish.json",
}


def skills_file_for(data_dir: Path, language: str) -> Path:
    """按界面语言选技能资料，缺文件时回落中文。"""
    name = SKILL_FILES.get(language or "", "")
    path = data_dir / name if name else None
    if path is not None and path.exists():
        return path
    return data_dir / "hero_skills.json"
'''
    s = s.rstrip() + addition
p.write_text(s, encoding="utf-8")

p = Path("src/dota2coach/ui/panel.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
    "from ..knowledge.skills import HeroSkills, load_hero_skills",
    "from ..knowledge.skills import HeroSkills, load_hero_skills, skills_file_for",
)
s = s.replace(
    '        self.skills: dict[int, HeroSkills] = load_hero_skills(config.data_dir / "hero_skills.json")',
    '        self.skills: dict[int, HeroSkills] = load_hero_skills(\n'
    '            skills_file_for(config.data_dir, self.language)\n'
    '        )',
)

# 设置页：t() + 标签
s = s.replace(
    "    # ---- 主题 ----",
    '    def t(self, name: str, **fmt: object) -> str:\n'
    '        return tr(self._config.app.language, name, **fmt)\n\n'
    "    # ---- 主题 ----",
    1,
)
for old, new in (
    ('tabs.addTab(self._language_tab(), "语言")', 'tabs.addTab(self._language_tab(), self.t("tab_language"))'),
    ('tabs.addTab(self._theme_tab(), "主题")', 'tabs.addTab(self._theme_tab(), self.t("tab_theme"))'),
    ('tabs.addTab(self._overlay_tab(), "覆盖层")', 'tabs.addTab(self._overlay_tab(), self.t("tab_overlay"))'),
    ('tabs.addTab(self._voice_tab(), "语音")', 'tabs.addTab(self._voice_tab(), self.t("tab_voice"))'),
    ('tabs.addTab(self._assist_tab(), "辅助")', 'tabs.addTab(self._assist_tab(), self.t("tab_assist"))'),
    ('tabs.addTab(self._hotkey_tab(), "快捷键")', 'tabs.addTab(self._hotkey_tab(), self.t("tab_hotkey"))'),
    ('buttons.button(QDialogButtonBox.StandardButton.Save).setText("保存")', 'buttons.button(QDialogButtonBox.StandardButton.Save).setText(self.t("save"))'),
    ('buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")', 'buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.t("cancel"))'),
    ('note = QLabel("保存后立即生效；GSI 端口等少数项需要重启程序。")', 'note = QLabel(self.t("settings_note"))'),
):
    if old not in s:
        raise SystemExit(f"missing: {old}")
    s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")
print("settings i18n + skills loader patched")
