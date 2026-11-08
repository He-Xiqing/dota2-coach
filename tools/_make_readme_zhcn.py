"""把当前中文 README 复制为 README.zh-CN.md，并加上语言导航头。"""

from pathlib import Path

HEAD = """<!-- 语言 / Language -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

"""

base = Path("README.md")
text = base.read_text(encoding="utf-8")
# 首页型 README 尚未生成，先假定它是完整中文版
Path("README.zh-CN.md").write_text(HEAD + text, encoding="utf-8")
print("README.zh-CN.md", len(text))
