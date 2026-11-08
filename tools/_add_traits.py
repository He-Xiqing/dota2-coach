"""英雄特点标签的 9 语言映射。"""

from pathlib import Path

CN2KEY = {
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

VALS = {
    "zh-CN": ["核心", "辅助", "爆发", "控制", "先手", "肉盾", "机动", "推塔", "打野"],
    "zh-TW": ["核心", "輔助", "爆發", "控制", "先手", "肉盾", "機動", "推塔", "打野"],
    "en": ["Core", "Support", "Nuker", "Control", "Initiator", "Tanky", "Mobile", "Pusher", "Jungler"],
    "fr": ["Cœur", "Support", "Nukeur", "Contrôle", "Initiateur", "Tanky", "Mobile", "Pusheur", "Jungler"],
    "ru": ["Керри", "Поддержка", "Урон", "Контроль", "Инициатор", "Танк", "Мобильность", "Пушер", "Лесник"],
    "de": ["Core", "Support", "Nuker", "Kontrolle", "Initiator", "Tanky", "Mobil", "Pusher", "Jungler"],
    "pt": ["Core", "Suporte", "Dano", "Controle", "Iniciador", "Tanque", "Móvel", "Push", "Selva"],
    "es": ["Core", "Soporte", "Daño", "Control", "Iniciador", "Tanque", "Móvil", "Push", "Jungla"],
    "tr": ["Core", "Destek", "Patlama", "Kontrol", "Başlatıcı", "Tank", "Mobil", "İtici", "Orman"],
}
KEYS = list(CN2KEY.values())

lines = ["_TRAITS = {"]
for code, values in VALS.items():
    lines.append(f'    "{code}": {{')
    for key, value in zip(KEYS, values):
        lines.append(f'        "{key}": "{value}",')
    lines.append("    },")
lines.append("}")
lines.append("for _lang, _vals in _TRAITS.items():")
lines.append("    _STRINGS.setdefault(_lang, {}).update(_vals)")
lines.append("")
block = "\n".join(lines) + "\n"

p = Path("src/dota2coach/i18n.py")
s = p.read_text(encoding="utf-8")
if "_TRAITS" in s:
    raise SystemExit("already")
anchor = "def normalize_language("
s = s.replace(anchor, block + anchor, 1)
p.write_text(s, encoding="utf-8")

p = Path("src/dota2coach/ui/panel.py")
s = p.read_text(encoding="utf-8")
helper = '''    def _localize_traits(self, text: str) -> str:
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

'''
if "_localize_traits" not in s:
    s = s.replace("    def _header(self) -> QHBoxLayout:", helper + "    def _header(self) -> QHBoxLayout:", 1)
    s = s.replace(
        '            tile.show_hero(',
        '            tile.show_hero(',
        1,
    )
p.write_text(s, encoding="utf-8")
print("traits added")
