"""威胁标签与副标题的本地化。"""

from pathlib import Path

p = Path("src/dota2coach/i18n.py")
s = p.read_text(encoding="utf-8")
if "threat_stealth" not in s:
    extra = {
        "zh-CN": ("识别自游戏顶部英雄栏", "隐身"),
        "zh-TW": ("識別自遊戲頂部英雄欄", "隱身"),
        "en": ("Detected from the top hero bar", "Invisible"),
        "fr": ("Détecté depuis la barre d'hero", "Invisible"),
        "ru": ("Определение по верхней панели", "Невидимость"),
        "de": ("Aus der oberen Heldenleiste erkannt", "Unsichtbar"),
        "pt": ("Detectado pela barra de heróis", "Invisível"),
        "es": ("Detectado desde la barra de héroes", "Invisible"),
        "tr": ("Üst şeritten algılanır", "Görünmez"),
    }
    block = ["_THREAT = {"]
    for code, (sub, stealth) in extra.items():
        block.append(f'    "{code}": {{"roster_sub": "{sub}", "threat_stealth": "{stealth}"}},')
    block.append("}")
    block.append("for _lang, _vals in _THREAT.items():")
    block.append("    _STRINGS.setdefault(_lang, {}).update(_vals)")
    block.append("")
    s = s.replace("_TRAITS = {", "\n".join(block) + "\n_TRAITS = {", 1)
    p.write_text(s, encoding="utf-8")

p = Path("src/dota2coach/ui/panel.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    '        self.roster_hint = QLabel("识别自游戏顶部英雄栏")',
    '        self.roster_hint = QLabel(self.t("roster_sub"))',
)
s = s.replace(
    '            parts = [f"{label}{counts.get(label, 0)}" for label in ("先手", "爆发", "隐身") if counts.get(label)]',
    '            label_map = {\n'
    '                "先手": self.t("trait_initiator"),\n'
    '                "爆发": self.t("trait_nuker"),\n'
    '                "隐身": self.t("threat_stealth"),\n'
    '            }\n'
    '            parts = [\n'
    '                f"{label_map[label]}{counts.get(label, 0)}"\n'
    '                for label in ("先手", "爆发", "隐身")\n'
    '                if counts.get(label)\n'
    '            ]',
)
s = s.replace(
    '                    threats=hero.get("threats") or (),',
    '                    threats=self._localize_threats(hero.get("threats") or ()),',
)
helper = '''    def _localize_threats(self, threats) -> tuple[str, ...]:
        label_map = {
            "先手": "trait_initiator",
            "爆发": "trait_nuker",
            "隐身": "threat_stealth",
        }
        return tuple(self.t(label_map[t]) if t in label_map else t for t in threats)

'''
if "def _localize_threats" not in s:
    s = s.replace("    def _localize_traits(", helper + "    def _localize_traits(", 1)
p.write_text(s, encoding="utf-8")
print("threats localized")
