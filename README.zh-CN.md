<!-- 语言 / Language -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

# DOTA2 入门教练（DOTA2 GETTING STARTED Coach）

Dota 2 实时教练（外部 Overlay）。通过 **Valve 官方 GSI** + **自己屏幕的截屏识别**工作：
不读内存、不注入、不模拟按键、不需要任何游戏 Mod。

<p>
  <a href="https://github.com/OWNER/REPO/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/OWNER/REPO/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

## 截图

<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>

## 这是给谁用的

**面向刚接触 DOTA2 的新手**：认不全英雄、不知道对线该站哪、出装靠抄、团战不知道该做什么的玩家。

设计上刻意做了这些取舍：

- **不替你操作**：只在你需要的时候说一句话，不给一堆数据面板；
- **不需要 Dota Plus**：顶部英雄栏截图识别，普通账号也能用；
- **不读游戏内存**：只收官方 GSI 报文 + 截自己屏幕，封号风险为零；
- **九语言界面 + 九语言朗读**：界面、提示、朗读一起切换；听一句就能上手，看得懂再细看；
- **打完有复盘**：输赢都给 1–3 条能立刻改的建议，不用自己复盘录像。

## 现在能做什么

- 接收 Dota 2 的 GSI 报文：自己的英雄/等级/血量/蓝量/技能/装备/金钱/KDA、比赛时间、比分；
- **决策时间自动截屏**，识别双方 10 个英雄：默认认**顶部英雄栏**（不需要 Dota Plus），有 Dota Plus 时再用“战友与宿敌”面板兜底；实测 2560×1600 截图 10/10 认对；
- 对局中在**顶部英雄栏每张头像下面写名字**（队友浅绿、对手浅红，不挡鼠标）；
- 右上角半透明**置顶卡片**：阶段与时间、双方阵容、下一件装备、赏金符/神符提醒；
- **对线教练**：判你在哪条路，按敌方威胁（先手/爆发/推线/隐身）给站位与血线提示，另有 4 分钟眼位、5 分钟天黑、6 级游走、补刀落后提醒；
- **提示音 + 九语言朗读**：刷符、对线、出装、物品使用与团战建议都会“叮”一声再念出来；朗读用在线 edge-tts（系统语音坏了也能用，失败自动降级），**语音包会跟着界面语言自动切换**，物品名与技能名不会中英混排；
- **B 站攻略库**：定时抓同版本攻略视频（标题/评论/弹幕，可选转写），LLM 提炼成 1 句话，局内按英雄/分路/阶段提示；每周自动检查更新，并清理过旧/重复/垃圾提示；
- **界面三态**：主界面只打招呼、不给建议；对局中显示教练信息；结束后整卡换成上一把数据、1–3 条提升建议与一句鼓励，30 秒后回到主界面；
- **主题**：主界面可换背景图（设置 → 主题，带白色蒙层保证可读）；
- **语音包**：内置 13 个 edge 音色（中文 5 个 + 繁中/英/法/俄/德/葡/西/土各 1 个），也可自定义音色；界面换语言时语音包自动换成该语言，自定义包保持不动；游戏正在出声时会等它说完再朗读；
- **应用图标**：窗口标题栏、任务栏、托盘与两个 exe 共用同一枚原创 “D2” 图标（data/app.ico，缺失时回退占位图）；
- **主窗口**：空闲时是功能介绍，进对局后自动换成双方 10 个英雄（每个英雄两条关键技能 + 一句话定位），右侧是状态灯、当前对局与最近 3 条提示；
- **团战提醒**：10 分钟后扫小地图红/绿点，敌方消失、我方集结、团战爆发时给 1–2 条建议，并按你的英雄定位（肉盾/控制/法师/刺客/辅助）说明该顶、该盯谁、该切谁；小地图位置/大小可在设置里手动指定；

- **敌方威胁徽章**：主窗口阵容里给每个敌人标「先手 / 爆发 / 隐身」，右上角汇总人数；
- **赛后复盘页**：识别到对局结束，阵容区整页换成上一把数据、改进建议与鼓励；
- **辅助开关**：设置 → 辅助，可单独关掉「刷新播报 / 名字显示 / 团战提醒 / 对线提醒」；
- **F8 呼出卡片**：主页有醒目提示，任意时刻 F8 显示/隐藏置顶卡片，F9 试听语音；
- 卡片默认**点击穿透**，不挡鼠标；对局中 GSI 继续驱动卡片更新；
- 原始报文和字段清单落到 `logs/`，可离线回放开发。

## 近期新增要点

- **九语言**：简体中文、繁體中文、English、Français、Русский、Deutsch、Português、Español、Türkçe；主窗口、设置、帮助、复盘、出装说明页与语音包都会跟随切换，主窗口语言即时生效，不用重启。
- **九语言朗读**：物品提醒（笛子/赤红甲/卫士胫甲/梅肯/微光/莲花/炎阳/铁意、点金手/秘法/灵魂之戒/魔杖/瓶子/支配）、对线补给（粉/魔棒/圆盾/吃树）、刷符与团战提示都会用当前语言念出来；界面语言一换，语音包自动换成对应语言的音色；非中文界面不再混入中文技能名。
- **出装说明页**：主窗口「出装顺序」按当前界面语言生成 `data/ingame_guide.<lang>.html`，写明出门装、核心装、加点与节奏提示。
- **小地图自适应**：自动在左下/右下寻找小地图并适配缩放；认不准时可在 设置 → 辅助 → 小地图 手动选位置、大小与 X/Y 偏移。团战扫描从 20 分钟提前到 10 分钟，长时间没有红点会自动重新定位。
- **朗读更自然**：提示文本会先清洗（`·`、`——`、`（）`、`7:00`、`6.8k` 等符号与缩写），播放按音频真实时长，不会怪停顿或说到一半被截断；旧配置里的音色显示名（如“晓伊”）会自动换算成 edge 音色 ID。
- **复盘更懂定位**：赛后建议按英雄定位给出，辅助不会再被提醒“补刀少 / 打钱慢”；开局招呼与赛后鼓励每次随机，不再千篇一律。
- **出装仍是一次一件**：卡片只推当前最该买的那件，附理由、用法与加点，买完自动换下一件。
- **攻略来源**：以 B 站为主，可选接入 YouTube（`[youtube] enabled = true`，需要能访问 YouTube 的网络或代理）；每周自动更新，并清理过旧/重复/垃圾提示。
- **双击即用**：`Dota2Coach.exe` 打开主窗口，`Dota2Coach-Card.exe` 只要置顶卡片；升级替换时启动会自动清掉残留的 `*.old.exe`。

M1 识别、M3 对线教练、M4 单件出装、M5 团战提醒均已验证；设置页可改覆盖层与语音并写回 `config.toml`。

## 快速开始（4 步）

```powershell
cd C:\Users\、\Documents\deepseek-harness\default-workspace\dota2-coach

# 1) 建环境、装依赖（需要先装 Python 3.12）
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) 把 GSI 配置复制进游戏目录
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1

# 3) 下载模板与数据（只需一次）
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py

# 3.5) 可选：在线朗读（系统语音引擎坏掉时用它；九种语言共用这一个依赖）
.\.venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3.6) 可选：抓一次攻略库（需要 .env 里的 DEEPSEEK_API_KEY）
.\.venv\Scripts\python.exe scripts\fetch_guides.py --limit 4 --asr base --asr-max-videos 2
# 想覆盖全部英雄：逐个英雄搜一个攻略视频，可断点续跑
.\.venv\Scripts\python.exe scripts\fetch_guides.py --all-heroes

# 4) 重启 Dota 2，启动教练，开一局
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

启动后会打开**主窗口**：点“开始”即可（默认启动时自动开始一次）。
想只要置顶卡片、不要主窗口，用 `.\scripts\run.ps1 -Card` 或 `python -m dota2coach --legacy`。

只想要数据、不要界面时用探针模式：`.\scripts\run.ps1 -Probe`。
详细步骤、验收点和排错见 [docs/install.md](docs/install.md)。

没有装 Python 也想先看数据格式？`tests/fixtures/gsi/playing.json` 是一份完整样例，
`python tools/replay_gsi.py tests/fixtures/gsi/playing.json` 可以在不开游戏的情况下驱动服务。

## 换语言与朗读

设置 → 语言：九种语言任选，保存后主窗口立即切换（不用重启）；语音包会自动换成该语言的音色，自定义音色包保持不动。
设置 → 语音：可开关朗读、调语速/音量、点“试听当前语音”；朗读失败时会自动退回提示音，日志在 `logs\voice.log`。
物品与补给提醒、刷符、对线、团战提示都会用当前语言念出来，不需要额外配置。

## 打包成 exe

```powershell
# 一次装好打包依赖（PyInstaller）
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 打包两个 exe：主窗口版 + 只要卡片版
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

产物在 `dist\`：

- `dist\Dota2Coach\Dota2Coach.exe`：主窗口版（推荐，双击即用）；
- `dist\Dota2Coach-Card\Dota2Coach-Card.exe`：只显示置顶卡片。

打包是 `--onedir`，`data\`、`config.toml`、`docs\` 会一起放进 exe 旁边；
第一次运行会把日志写到 `logs\`，设置页保存会写回 exe 旁的 `config.toml`。
安装目录不可写时（比如放在 Program Files），会自动改用 `%LOCALAPPDATA%\Dota2Coach`。

## 目录

```
config.toml              全局配置（Dota 路径、端口、日志开关、卡片/语音）
docs/gsi.cfg             Valve GSI 配置模板
docs/install.md          装机与首次运行
docs/data-sources.md     GSI 字段实测记录
scripts/                 setup / run / build / copy_gsi / update_data / fetch_* / schedule_guides
packaging/               两个 exe 的入口脚本
src/dota2coach/          gsi 接收与录制、vision 截屏识别、coach 状态与规则、sources 攻略抓取
  ui/panel.py            主窗口（空闲介绍 / 对局阵容 / 状态 / 设置 / 帮助）
  ui/overlay.py          置顶卡片；ui/namestrip.py 头像下名字条
  ui/theme.py            颜色与控件样式；ui/hotkeys.py F8/F9
  knowledge/skills.py    英雄技能简介（data/hero_skills.json）
  knowledge/ingame_guide.py 出装说明页（九语言 HTML 模板）
  coach/texts_items.py   物品/补给的九语言文案（朗读用）
tests/                   单元测试（合成报文与合成图像，不依赖游戏）
tools/                   replay_gsi / screenshot / identify_heroes / inspect_capture / voice_probe
data/                    英雄表、图标模板、出装热度、物品表、技能简介、攻略库（data/guides/）
logs/                    运行产物（原始报文、摘要、字段清单、截图、语音日志）
```

## 设计边界

| 数据 | 来源 | 说明 |
|---|---|---|
| 自己的英雄/技能/装备/金钱 | GSI | 官方接口，实时 |
| 比赛时间/比分/防御塔 | GSI | 官方接口，实时 |
| 双方阵容 | 决策时间面板截屏 | 普通匹配里 GSI 只给"你自己"（draft 恒为空，已实测） |
| 敌方位置/团战聚集 | 小地图截屏 | 颜色分割 + 聚类（M3/M5） |
| 出装 | OpenDota 物品热度 | 离线缓存，跳过散件与消耗品 |
| 阵容角色/胜率 | OpenDota heroStats | 当前版本统计，脚本刷新（无 key） |
| 攻略提示 | B 站视频 + DeepSeek 提炼 | 同版本攻略，可选 whisper 转写，脚本刷新 |
| 朗读 | 在线 edge-tts（可关） | 九语言音色；系统语音引擎坏掉也能用，失败时退回提示音 |

**红线**：不读游戏内存、不注入进程、不发送任何输入、不代打。工具定位是"个人训练/复盘辅助"，
在官方赛事中使用请遵守赛事规则；天梯使用请自行评估风险。

## 路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| M0 | GSI 打通、报文落盘、装机脚本 | 完成（真实对局 1941 条报文验证） |
| M1 | 截屏识别双方阵容 + 置顶卡片 | 顶部英雄栏 10/10（不依赖 Dota Plus）；头像下名字条 |
| M2 | 知识库 + 选人推荐 | 未开始 |
| M3 | 对线教练（判路、站位/血线、眼位、补刀、6 级节奏） | 完成（`coach/lane.py`，12 例单测） |
| M4 | 出装推荐 | 单件推荐 + 理由/用法/加点；买完自动换下一件 |
| M5 | 团战提醒 | 小地图红/绿点 + 英雄定位建议（10 分钟后，位置/大小可配） |
| M6 | 打包与文档 | 主窗口 + 设置/帮助 + PyInstaller 双 exe |
| M7 | B 站攻略库（抓取→提炼→局内提示 + 出装/加点） | 已跑通；builds 随抓取逐步补齐 |

## 可选：YouTube 攻略源

需要**能访问 YouTube 的网络**（国内直连不通时用代理）：

```powershell
python scripts\fetch_youtube_guides.py --heroes slark --per-hero 1 --proxy "http://127.0.0.1:7890"
```

有官方字幕时直接读字幕，没有字幕则需要 `faster-whisper`（见 `scripts\setup_asr.ps1`）。
本程序不会自动翻墙；`[youtube] enabled=false` 时该功能完全关闭。

## 数据来源

| 数据 | 文件 | 来源 | 怎么更新 |
|---|---|---|---|
| 英雄中文名 | `data/heroes.json` | dota2.com 官方 datafeed（中文） | `scripts/fetch_hero_icons.ps1` |
| 英雄图标/卡面 | `data/hero_icons/`、`data/hero_cards/` | Valve CDN 的 `dota_react` 图集 | 同上 |
| 英雄角色 + 胜率 | `data/hero_meta.json` | OpenDota `/api/heroStats`（当前版本公开对局，免费） | `scripts/fetch_hero_stats.py` |
| 出装热度 | `data/popularity.json` | OpenDota `itemPopularity`（当前版本） | `scripts/fetch_popularity.py` |
| 对位胜率 | `data/matchups.json` | OpenDota `heroes/{id}/matchups`（免费，不需要 key） | `scripts/fetch_matchups.py` |
| 物品表/中文名 | `data/items.json`、`item_names_zh.json` | OpenDota 常量 + 游戏本地化 VPK | `build_item_table.py`、`build_item_names.py` |
| 提示文案 | `src/dota2coach/coach/advice.py` | 模板句 + 角色标签（不再维护英雄清单） | 改代码 |
| GSI 规范 | — | Valve Developer Community | — |

原则：**能实时统计就不写死**。角色/胜率/出装/对位全部来自 OpenDota 当前版本数据；
只有"隐身、回复"这类非角色标签的事实和提示文案是内置的，并且有静态兜底表，
`hero_meta.json` 缺失时也能离线工作（只是分类会退回过期清单）。

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

离线渲染一次卡片（不启动 GSI、不进游戏）：

```powershell
.\.venv\Scripts\python.exe -m dota2coach --screenshot logs\screenshots\draft-121216.png `
    --snapshot tests\fixtures\gsi\playing.json --save-overlay logs\screenshots\overlay.png --seconds 3
```

## 版本管理

本目录已经是 git 仓库（分支 `main`），`.venv/`、`dist/`、`build/`、`logs/`、`.env`、`*.spec` 都在 `.gitignore` 里。

```powershell
git status                 # 看改了什么
git diff                   # 看具体改动
git add -A; git commit -m "说明"   # 存一个还原点
git log --oneline -10      # 看历史
git restore <文件>          # 撤销未提交的改动
git checkout <commit> -- <文件>    # 把某个文件恢复到某个版本
```

改坏了想整体回到上一个提交：`git reset --hard HEAD`（会丢弃未提交改动，慎用）。

## 下载

- 免安装版（Windows x64）：[Releases](https://github.com/OWNER/REPO/releases/latest) — 下载 zip 解压后双击 `Dota2Coach.exe`
- 从源码运行：见上方「快速开始」

## 合规与免责

- 非 Valve 官方产品，与 Valve 无关联。
- 只读取官方 GSI 与你自己屏幕的截图；不读内存、不注入、不模拟按键。
- 请遵守 Steam 与 Dota 2 服务条款，使用风险自负。

## 致谢

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

