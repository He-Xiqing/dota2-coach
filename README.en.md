<!-- Language / 语言 -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

# DOTA2 GETTING STARTED Coach

A real-time Dota 2 coach that runs as an external overlay. It uses only the **official Valve GSI** and **screen capture of your own display**:
no memory reading, no injection, no simulated keystrokes, no game mods.

<p>
  <a href="https://github.com/OWNER/REPO/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/OWNER/REPO/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

## Screenshots

<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>

## Who is it for

**Players who just started Dota 2**: you don't know every hero, you're not sure where to stand in lane, you copy builds, and in teamfights you don't know what to do.

Deliberate trade-offs:

- **It never plays for you**: one short line when it matters, not a wall of stats;
- **No Dota Plus needed**: heroes are recognized from the top hero bar, so normal accounts work;
- **No memory reading**: official GSI plus screenshots of your own screen;
- **9 UI languages + 9 spoken languages**: UI, tips and speech switch together;
- **A review after every game**: 1–3 fixes you can apply next game, win or lose.

## What it does

- Reads GSI: your hero/level/HP/mana/abilities/items/gold/KDA, game time, score;
- **Screenshots the strategy screen** and recognizes all 10 heroes from the top bar (no Dota Plus); 10/10 on a 2560×1600 capture;
- Draws **community names under each top-bar portrait** (allies green, enemies red, click-through);
- A semi-transparent **always-on-top card**: phase and clock, both lineups, next item, rune timers;
- **Lane coach**: tells your lane, gives positioning/HP advice based on enemy threats (initiation/burst/push/invisibility), plus 4-min ward, 5-min night, level-6 roam and last-hit warnings;
- **Chime + speech in 9 languages**: runes, lane, items, item usage and fight tips are spoken; speech uses online edge-tts, so it still works when the system voice engine is broken; **the voice pack follows the UI language**;
- **Guide library (Bilibili)**: periodic crawl of same-patch guides (title/comments/danmaku, optional transcription), distilled to one line by an LLM; weekly refresh with stale/duplicate cleanup;
- **Three UI states**: idle greeting, in-game coaching, and a post-game summary (stats, 1–3 tips, one encouragement) that returns to idle after 30 s;
- **Theme**: replaceable background image for the main window (Settings → Theme);
- **Voice packs**: 13 built-in edge voices (5 Chinese + one each for zh-TW/en/fr/ru/de/pt/es/tr), plus custom voices;
- **Teamfight alerts**: from minute 10 it watches minimap dots, alerts when enemies vanish, allies group up or a fight starts, and tells you what to do based on your role (tank/control/mage/assassin/support); minimap position and size are configurable;
- **F8** shows/hides the card, **F9** previews the voice; the card is click-through by default.

## Recent highlights

- **Nine languages**: 简体中文, 繁體中文, English, Français, Русский, Deutsch, Português, Español, Türkçe. Main window, settings, help, post-game review, build guide page and voice packs all follow the language; the main window switches instantly, no restart.
- **Nine-language speech**: item reminders (Pipe/Crimson Guard/Greaves/Mekansm/Glimmer/Lotus/Solar/Pavise, Midas/Arcane/Soul Ring/Wand/Bottle/Helm), lane consumables (Dust/Magic Stick/Stout Shield/Tango), rune and fight tips are all spoken in the current language; no Chinese skill names leak into other languages.
- **Build guide page**: generated per language as `data/ingame_guide.<lang>.html`.
- **Adaptive minimap**: finds the minimap in either bottom corner and adapts to its size; if unsure, set position/size/X-Y offset in Settings → Assist → Minimap; scanning starts at minute 10 and re-locates after a long stretch with no red dots.
- **Better speech**: text is normalized (`·`, `——`, `（）`, `7:00`, `6.8k`), and playback uses the real audio duration, so lines are not cut off.
- **Smarter review**: support heroes are no longer told "low last hits / low GPM"; greetings and encouragements are randomized.
- **One item at a time**: the card recommends the single item to buy now, with reason, usage and skill build, then moves on.
- **Two exes**: `Dota2Coach.exe` opens the main window, `Dota2Coach-Card.exe` only the card; stale `*.old.exe` files are cleaned on startup.

## Quick start

```powershell
cd <project folder>

# 1) environment + dependencies (Python 3.12 required)
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) copy the GSI config into the game folder
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1

# 3) download templates and data (once)
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py

# 3.5) optional: online speech (one dependency for all 9 languages)
.\.venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4) restart Dota 2, then start the coach
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

Full setup and troubleshooting: [docs/install.md](docs/install.md) (Chinese).

## Language and voice

Settings → Language: pick one of the nine languages and save; the main window switches immediately, no restart. The voice pack switches to that language automatically; a custom voice stays as-is.
Settings → Voice: toggle speech, adjust rate/volume, and click "Preview this voice". If speech fails it falls back to the chime; logs go to `logs\voice.log`.

## Data boundaries

| Data | Source | Notes |
|---|---|---|
| Your hero/abilities/items/gold | GSI | official, real-time |
| Clock/score/towers | GSI | official, real-time |
| Both lineups | strategy-screen capture | GSI gives only "you" in normal matches |
| Enemy positions / fights | minimap capture | color segmentation + clustering |
| Builds | OpenDota item popularity | offline cache |
| Roles / win rates | OpenDota heroStats | current patch |
| Guide tips | Bilibili videos + DeepSeek | same-patch guides |
| Speech | online edge-tts (optional) | 9 languages, falls back to chime |

**Red lines**: no memory reading, no injection, no synthetic input, no automation.

## Roadmap

| Phase | Content | Status |
|---|---|---|
| M0 | GSI pipeline, logging, setup scripts | done |
| M1 | lineup recognition + overlay card | 10/10 from the top bar |
| M2 | knowledge base + draft advice | not started |
| M3 | lane coach | done |
| M4 | item advice | single item + reason/usage/build |
| M5 | teamfight alerts | minimap dots + role advice (after 10 min) |
| M6 | packaging and docs | main window, settings/help, two exes |
| M7 | Bilibili guide library | working |

## Build and test

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Output: `dist\Dota2Coach\Dota2Coach.exe` (main window) and `dist\Dota2Coach-Card\Dota2Coach-Card.exe` (card only).

## Download

- Portable build (Windows x64): [Releases](https://github.com/OWNER/REPO/releases/latest) — unzip and run `Dota2Coach.exe`
- Run from source: see Quick start above

## Compliance & disclaimer

- Not an official Valve product; not affiliated with Valve.
- Reads only official GSI and screenshots of your own screen; no memory reading, no injection, no simulated input.
- Follow the Steam and Dota 2 terms of service; use at your own risk.

## Credits

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

## More

- The most complete documentation (folder layout, data sources, git workflow) is [README.zh-CN.md](README.zh-CN.md).
- Dataset and script details: [docs/data-sources.md](docs/data-sources.md).
