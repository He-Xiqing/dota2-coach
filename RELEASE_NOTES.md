# v0.1.0 — 首个公开版本 / First public release

DOTA2 入门教练：面向新手的 Dota 2 实时教练（外部 Overlay）。
DOTA2 GETTING STARTED Coach: a real-time Dota 2 coach overlay for beginners.

## 亮点 / Highlights

- **开局识别 10 个英雄**：截图顶部英雄栏，不需要 Dota Plus。
- **九语言界面 + 九语言朗读**：简体中文 / 繁體中文 / English / Français / Русский / Deutsch / Português / Español / Türkçe，切换后主窗口即时生效。
- **对线教练**：分路、对位强弱、血量/蓝量、6 级、眼位、夜战与符点提醒。
- **单件出装**：每次只推一件，附理由、用法与加点；买完自动换下一件。
- **团战预警**：10 分钟后看小地图，红点消失/聚集/低血时提醒怎么打。
- **赛后复盘**：1–3 条可执行建议 + 一句鼓励，辅助英雄不再被说“补刀少”。
- **小地图自适应**：左下/右下、任意缩放；自动失败可在设置里手动指定位置与大小。

- **All 10 heroes at game start** from a top-bar screenshot — no Dota Plus needed.
- **9 UI + 9 spoken languages**, switching instantly without restart.
- **Lane coaching**: lane, matchup strength, HP/mana, level 6, wards, night, runes.
- **One item at a time** with reason, usage and skill build.
- **Fight alerts** after 10 minutes from the minimap.
- **Post-game review** with 1–3 fixes and encouragement.
- **Adaptive minimap**: any corner and scale, with manual fallback.

## 安装 / Install

1. 下载 `Dota2Coach-v0.1.0-win64.zip` 并解压（或只下载 Card 版）。
2. 双击 `Dota2Coach.exe`；首次运行会在旁边生成 `config.toml`。
3. 按 `docs/install.md` 或 README 的“快速开始”复制 GSI 配置到游戏目录，并下载英雄头像（`scripts/fetch_hero_icons.ps1`，约 9MB）。
4. 重启 Dota 2，进对局即可看到置顶卡片。

## 说明 / Notes

- 只读取官方 GSI 与你自己屏幕的截图；不读内存、不注入、不模拟按键。
- 语音使用在线 edge-tts（可关闭）；离线时退回提示音。
- 非 Valve 官方产品，请遵守 Steam 与 Dota 2 服务条款。
- 这是首个公开版本，欢迎在 Issues 反馈问题与建议。
