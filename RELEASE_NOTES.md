# v0.1.1 — 更轻、更准 / Leaner and more accurate

DOTA2 入门教练：面向新手的 Dota 2 实时教练（外部 Overlay）。
DOTA2 GETTING STARTED Coach: a real-time Dota 2 coach overlay for beginners.

## 这一版 / In this release

- **体积缩小**：安装包从 106 MB 降到 88 MB，解压后目录也明显变小；功能一项没少。
  OpenCV 改用 headless 构建，去掉未使用的 ffmpeg/Qt 换行库、Qt 翻译与 QML 等。
  Packages dropped from 106 MB to 88 MB with no feature removed.
- **1080p 识别修复**：顶部英雄栏改为按“队伍色条”定位，不再依赖写死的比例或“自己是第 1 张卡”的假设；
  1024–2560 宽度下同一张截图均能认满 10 个英雄。
  Hero bar is now located by the team color strips, independent of DPI/HUD scaling.
- **打包更干净**：安装包里只带 `config.example.toml`（不再带本机 `config.toml`）、LICENSE 与说明；
  运行时不再携带 Valve 原始文本。
- 其余功能与 v0.1.0 一致：九语言界面与朗读、对线教练、单件出装、团战预警、赛后复盘、小地图自适应。

## 安装 / Install

1. 下载 `Dota2Coach-v0.1.1-win64.zip` 并解压（或只下载 Card 版）。
2. 双击 `Dota2Coach.exe`；首次运行会在旁边生成 `config.toml`。
3. 按 `docs/install.md` 或 README 的“快速开始”复制 GSI 配置到游戏目录，并下载英雄头像（`scripts/fetch_hero_icons.ps1`，约 9MB）。
4. 重启 Dota 2，进对局即可看到置顶卡片。

## 校验 / Checksums

见 `SHA256SUMS.txt`。 / See `SHA256SUMS.txt`.

## 旧版本 / Previous

- v0.1.0：首个公开版本（九语言、对线/出装/团战/复盘、小地图自适应）。
