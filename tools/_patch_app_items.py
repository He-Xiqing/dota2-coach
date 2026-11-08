"""一次性补丁：按界面语言加载物品名；非中文不显示中文攻略正文。"""

from pathlib import Path

P = Path("src/dota2coach/app.py")
s = P.read_text(encoding="utf-8")

s = s.replace(
    '        self._load_chinese_items(config.data_dir / "item_names_zh.json")',
    "        self._load_localized_items(config.data_dir)",
    1,
)

old = '''    def _load_chinese_items(self, path: Path) -> None:
        """物品中文名来自游戏本地化文件（scripts/build_item_names.py 生成）。"""
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(raw, dict):
            self.item_names = {**self.item_names, **{str(k): str(v) for k, v in raw.items()}}
'''
new = '''    _ITEM_NAME_FILES = {
        "zh-CN": "item_names_zh.json",
        "zh-TW": "item_names.zh-TW.json",
        "en": "item_names.en.json",
        "fr": "item_names.fr.json",
        "ru": "item_names.ru.json",
        "de": "item_names.de.json",
        "pt": "item_names.pt.json",
        "es": "item_names.es.json",
        "tr": "item_names.tr.json",
    }

    def _load_localized_items(self, data_dir: Path) -> None:
        """物品名按界面语言加载；缺文件时用 items.json 自带的英文名。"""
        language = getattr(self.config.app, "language", "zh-CN")
        filename = self._ITEM_NAME_FILES.get(language, "item_names_zh.json")
        path = data_dir / filename
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(raw, dict):
            self.item_names = {**self.item_names, **{str(k): str(v) for k, v in raw.items()}}
'''
if old not in s:
    raise SystemExit("loader anchor missing")
s = s.replace(old, new, 1)

# 非中文：B 站攻略正文是中文，先不显示
old_guide = '''        guide = self.guides.tips_for(self_short, lane_key, phase_name(phase), limit=1) if self_short else []'''
if old_guide in s:
    s = s.replace(
        old_guide,
        '''        guide = (
            self.guides.tips_for(self_short, lane_key, phase_name(phase), limit=1)
            if self_short and texts_language() == "zh-CN"
            else []
        )''',
        1,
    )
P.write_text(s, encoding="utf-8")
print("app patched")
