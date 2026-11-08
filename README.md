# DOTA2 GETTING STARTED Coach · DOTA2 入门教练

**Dota 2 实时教练（外部 Overlay）** / Real-time Dota 2 coach as an external overlay.
只读官方 GSI + 截自己屏幕；不读内存、不注入、不模拟按键。
Official GSI + screenshots of your own screen; no memory reading, no injection, no simulated input.

<p>
  <a href="https://github.com/He-Xiqing/dota2-coach/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/He-Xiqing/dota2-coach/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

![Lineup](docs/img/panel-roster.png)

面向刚接触 DOTA2 的玩家：认不全英雄、不知道站哪、出装靠抄、团战迷茫。
Built for players new to Dota 2: you don't know every hero, where to stand, which item to buy, or what to do in a fight.

- **九语言界面 + 九语言朗读** / 9 UI + 9 spoken languages — 简体中文, 繁體中文, English, Français, Русский, Deutsch, Português, Español, Türkçe
- 开局识别 10 英雄（不需要 Dota Plus）/ recognizes all 10 heroes from the top bar
- 对线思路、下一件装备与理由、符点提醒 / lane coaching, next-item advice, rune timers
- 10 分钟后团战预警 / fight alerts after 10 minutes
- 赛后复盘：1–3 条可执行建议 + 一句鼓励 / post-game review with 1–3 fixes

<p align="center">
  <img src="docs/img/card.png" width="46%" alt="lane card">
  <img src="docs/img/summary.png" width="46%" alt="post-game summary">
</p>

## 下载 / Download

- 免安装版（Windows x64）：[Releases](https://github.com/He-Xiqing/dota2-coach/releases/latest) — 解压后双击 `Dota2Coach.exe`
- Portable build: [Releases](https://github.com/He-Xiqing/dota2-coach/releases/latest) — unzip and run `Dota2Coach.exe`
- 从源码运行 / from source：见各语言 README 的“快速开始 / Quick start”

## 选择语言 / Choose your language

| 语言 | Language | README |
|---|---|---|
| 简体中文 | Simplified Chinese | [README.zh-CN.md](README.zh-CN.md) ← 内容最完整 / most detailed |
| 繁體中文 | Traditional Chinese | [README.zh-TW.md](README.zh-TW.md) |
| English | English | [README.en.md](README.en.md) |
| Français | French | [README.fr.md](README.fr.md) |
| Русский | Russian | [README.ru.md](README.ru.md) |
| Deutsch | German | [README.de.md](README.de.md) |
| Português | Portuguese | [README.pt.md](README.pt.md) |
| Español | Spanish | [README.es.md](README.es.md) |
| Türkçe | Turkish | [README.tr.md](README.tr.md) |

除简体中文版外其余为“精华版”，省略目录结构、逐文件数据来源与 git 工作流，这些在 [README.zh-CN.md](README.zh-CN.md) 中。
Except for Simplified Chinese, the files are condensed editions; folder layout, per-file data sources and git workflow live in [README.zh-CN.md](README.zh-CN.md).

## 合规与免责 / Compliance & disclaimer

- 非 Valve 官方产品，与 Valve 无关联。 / Not an official Valve product; not affiliated with Valve.
- 只读取官方 GSI 与你自己屏幕的截图。 / Reads only official GSI and screenshots of your own screen.
- 请遵守 Steam 与 Dota 2 服务条款，使用风险自负。 / Follow the Steam and Dota 2 terms of service; use at your own risk.
- 仓库不包含 Valve 素材（英雄头像/本地化文本），首次运行按 README 下载。 / No Valve assets are bundled; the README explains the one-time download.

## 致谢 / Credits

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
