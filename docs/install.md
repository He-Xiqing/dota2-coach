# 安装与首次运行（M0：先把数据打通）

> 目标：30 分钟内让程序收到 Dota 2 的实时报文，并把它们存成日志。
> 这一步不涉及任何界面，也不写游戏目录以外的系统位置。

## 0. 前置条件

- Windows 10 / 11，Dota 2 已安装。
- 本机 Dota 2 路径（已写进 `config.toml`）：
  `D:\SteamLibrary\steamapps\common\dota 2 beta`
- 游戏显示模式：**无边框窗口**（Borderless Windowed），不要独占全屏。

## 1. 安装 Python 3.12

1. 打开 https://www.python.org/downloads/windows/ ，下载 **Python 3.12.x** 的 Windows installer（64-bit）。
   - 不要用 Microsoft Store 版（本机现在 `python` 指向的就是 0 字节的商店占位符）。
   - 不要用 3.13：后面截屏用的 `bettercam` / `opencv` 轮子在 3.12 最稳。
2. 安装第一页勾选 **Add python.exe to PATH**。
3. 新开一个 PowerShell 验证：

   ```powershell
   python --version
   ```

   应输出 `Python 3.12.x`。

## 2. 安装依赖

在项目根目录执行：

```powershell
cd C:\Users\、\Documents\deepseek-harness\default-workspace\dota2-coach
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

脚本会：

1. 在项目下创建 `.venv`；
2. 用清华镜像装 `requirements-core.txt`（探针只需要这一组）；
3. 再尝试装视觉组 `requirements-vision.txt` 和界面组 `requirements-ui.txt`，失败只警告、不中断。

如果镜像装不上，可以手动换源：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-core.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 3. 装 GSI 配置（唯一的"游戏内插件"）

GSI 是 Valve 官方给第三方程序的接口，配置就是一个文本文件，不修改游戏本体、不需要 Mod 工具。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1
```

它会复制 `docs\gsi.cfg` 到：

```
D:\SteamLibrary\steamapps\common\dota 2 beta\game\dota\cfg\gamestate_integration\gamestate_integration_coach.cfg
```

放好后 **完全退出并重启 Dota 2**（配置只在启动时读取）。

> 想手动来：新建上面那个目录，把 `docs\gsi.cfg` 复制进去并改名即可。
> 想停用：删掉这个 .cfg 文件，重启游戏。

## 4. 启动探针，打一局人机

**先启动探针**（它要占着端口等游戏来连）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -Probe
```

看到下面几行就说明在监听：

```
监听地址 : http://127.0.0.1:31982/
原始报文 : ...\logs\gsi_raw
```

然后进游戏，开一局 **本地大厅 + 9 个 bot**（可以开作弊快速推进）。以下时刻各停 10~20 秒：

1. 英雄选择 / 策略时间；
2. 刚开局（0:00 前后）；
3. 对线期（有兵线、有眼）；
4. 中期一次团战；
5. 比赛结束画面。

控制台每秒会打印一行，形如：

```
[10:04:49] GAME_IN_PROGRESS t= 05:12 hero=nevermore  lvl= 9 hp= 66% ab= 4 it= 6 kda=4/1/5 gold=  812
```

第一帧还会额外打印：

```
[已接通] 顶层字段: abilities, buildings, events, game, hero, items, map, player, provider
         有 draft 字段 / 无 draft 字段（当前情境不下发）
```

这两行就是我们要的结论。

打完后在控制台按 **Ctrl+C**，会输出收到的报文总数，并写出 `logs\gsi_keys.json`。

## 5. 把结果给我

把整个 `logs\` 目录发给我（压缩成 zip 也行），我会：

- 用 `logs\gsi_keys.json` 确认 `draft`、`events`、`abilities`、`items` 到底有没有、长什么样；
- 用 `logs\gsi_raw\*.jsonl` 做离线回放，开发后面的识别和提示，不用你反复开游戏；
- 把结论写进 `docs\data-sources.md`。

## 6. 排错

| 现象 | 原因 / 处理 |
|---|---|
| 45 秒内没有任何报文 | ① cfg 是否放到了 `game\dota\cfg\gamestate_integration\`；② 放好游戏**重启**了吗；③ 文件名是否以 `.cfg` 结尾；④ 内容是否被保存成了 UTF-16（用 UTF-8 保存） |
| `[错误] 无法监听 127.0.0.1:31982` | 端口被占用：`netstat -ano \| findstr 31982`，结束占用进程，或改 `config.toml` 里的 `port`（同时改 `docs\gsi.cfg` 的 `uri`） |
| 有报文但 `hero` 一直是 `-` | 正常：还在主菜单/英雄选择阶段，进游戏后才会有 `hero` 段 |
| 控制台中文是乱码 | Windows 控制台编码问题，不影响日志文件；用 VS Code 打开 `logs\*.jsonl` 即可 |
| `python` 打开了应用商店 | PATH 里还是商店占位符：重装 Python 并勾选 Add to PATH，或直接用 `scripts\run.ps1`（它优先用 `.venv`） |
| `pip` 下载超时 | 换镜像：`-i https://pypi.tuna.tsinghua.edu.cn/simple`（阿里云 `https://mirrors.aliyun.com/pypi/simple/` 也可） |

## 7. 卸载

1. 删除游戏目录里的 `gamestate_integration_coach.cfg`；
2. 删除项目下的 `.venv` 和 `logs`（可选）。

## 8. 图形界面模式（教练卡片）

数据准备只需做一次：

```powershell
# 英雄图标 + 卡面 + 中文英雄表（需要外网）
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1

# 出装热度（OpenDota，明文 HTTP）
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py
```

然后启动教练（**不要**加 `-Probe`）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

启动后右上角会出现半透明卡片。在 **决策时间**（选完人、出兵前的分路界面）停留 1~2 秒，
程序会自动截屏识别双方阵容，卡片上应显示：

```
对线期 · 总经济 7.5k · 战绩 4/1/5 · 正反补 88/6
我方：★兽王、卓尔游侠、瘟疫法师、复仇之魂、水晶室女
敌方：帕吉、影魔、莱恩、露娜、沙王
对位胜率：均 49%（最难 帕吉 48%）
下一件：魔龙枪
后续：夜叉 → 幻影斧 → 疯狂面具
你在下路（天辉优势路 / 夜魔劣势路）
攻略：优先做A杖，强攻变群体技能
```

排查：

| 现象 | 处理 |
|---|---|
| 卡片不出现 | 确认没有加 `-Probe`；控制台应打印 `GSI 监听：http://127.0.0.1:31982/` |
| 卡片一直是"英雄未识别" | 截图识别失败。看控制台 `[识别]` 行：模板缺失就先跑 `fetch_hero_icons.ps1`；若提示"本帧没有识别出英雄"，确认游戏是**无边框窗口**且停在决策时间界面 |
| 阵容全是"?" | 同上；也检查 `data/hero_icons` 里是否有 png（应为 127 张） |
| 出装行显示"出装数据未就绪" | 还没跑 `fetch_popularity.py`（或它在后台没跑完） |
| 卡片挡住了鼠标 | `config.toml` 里 `[overlay] click_through = true`（默认开启，点击穿透） |
| 想拖动卡片 | 把 `click_through` 改成 `false`，重启程序后可以拖动 |

离线自检（不启动 GSI、不进游戏）：

```powershell
.\.venv\Scripts\python.exe -m dota2coach --screenshot logs\screenshots\draft-121216.png `
    --snapshot tests\fixtures\gsi\playing.json --save-overlay logs\screenshots\overlay.png --seconds 3
```

## 9. 攻略库（B 站 → 局内提示）

需要项目根 `.env` 里的 `DEEPSEEK_API_KEY`（没有也能跑，但只能得到元数据、提炼不出提示）。

```powershell
# 先确认 key 可用
.\.venv\Scripts\python.exe scripts\fetch_guides.py --check-key

# 抓 4 个视频、用 base 模型转写 2 个（更慢，但能拿到口播内容）
.\.venv\Scripts\python.exe scripts\fetch_guides.py --limit 4 --asr base --asr-max-videos 2

# 或者用包装脚本（日志写 logs\guides.log）
powershell -ExecutionPolicy Bypass -File .\scripts\update_guides.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\update_guides.ps1 -Asr -Limit 4

# 覆盖全部英雄（每个英雄搜一个攻略视频；中断后重跑会从没覆盖的英雄继续）
.\.venv\Scripts\python.exe scripts\fetch_guides.py --all-heroes
# 只补几个英雄，或调试
.\.venv\Scripts\python.exe scripts\fetch_guides.py --all-heroes --heroes axe,lion --per-hero-tips 2
```

第一次用转写要先装依赖和模型（约 150 MB，走 hf-mirror）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_asr.ps1
```

产物在 `data/guides/`：`<版本>.json`（局内读取）、`<版本>.md`（人看的）、`index.json`、`transcripts/`（转写稿）。
局内只在自己英雄 + 分路/阶段匹配时才显示 `攻略：…`，没有匹配就不显示，不会乱说。

每周自动更新（Windows 计划任务，周日 03:00）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\schedule_guides.ps1
# 删除：.\scripts\schedule_guides.ps1 -Remove
```

排错：

| 现象 | 处理 |
|---|---|
| `--check-key` 返回 401 | `.env` 里的 key 无效或没保存成功；用记事本打开确认只有一行 `DEEPSEEK_API_KEY=...` |
| 搜索返回 0 条 / `v_voucher` | B 站临时风控；等 1 分钟重跑，或加 `--bvid BV号` 直接抓指定视频 |
| 转写很慢 | `--asr base` 已是最小模型；先用 `--asr-max-videos 1` 试 |
| 卡片没有“攻略：…” | 1) `data/guides/` 有没有当前版本文件；2) 控制台应打印 `攻略库：N 条（patch=…）`；3) 该英雄/分路是否真有提示 |

## 10. 主窗口（推荐入口）

`scripts\run.ps1` 现在打开主窗口：

- **空闲**：功能介绍（开局/对线/团战三张说明卡），点“开始”；
- **对局中**：介绍语收起，换成双方 10 个英雄；每个英雄给两条关键技能简介；
- **右侧**：状态灯（GSI 监听 / 对局中 / 识别 n/10）、“当前对局”（英雄、时间、阶段、最近 3 条提示）、开始/停止按钮；
- **设置**：覆盖层（启用、透明度、点击穿透）与语音（启用、朗读、后端、音色、语速、音量、间隔），保存即写回 `config.toml`；
- **帮助**：版本、红线、F8/F9、日志与配置入口；
- 关闭窗口会最小化到托盘，托盘菜单可退出。

快捷键：**F8** 显示/隐藏卡片，**F9** 试听语音（被其它软件占用时控制台会提示）。

只想开卡片、不要主窗口：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1 -Card
# 或
.\.venv\Scripts\python.exe -m dota2coach --legacy
```

主窗口排错：

| 现象 | 处理 |
|---|---|
| 点“开始”弹“端口被占用” | 已有一个实例在跑；关掉旧窗口/旧控制台再试 |
| “GSI 监听”灯不亮 | 同上；也可能 GSI 配置没复制（见第 3 节） |
| “识别 n/10”一直很低 | 游戏要窗口/无边框；进对局 1.5 秒后会自动重定位顶部栏，控制台有 `[识别] 顶部栏重新定位：N 格` |
| 设置保存后没变化 | 覆盖层/语音立即生效；GSI 端口需重启程序 |
| F8/F9 没反应 | 被其它软件占用（会打印注册失败）；先关掉冲突软件再重启教练 |

## 11. 打包成 exe

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

产物：

- `dist\Dota2Coach\Dota2Coach.exe`：主窗口版（推荐）；
- `dist\Dota2Coach-Card\Dota2Coach-Card.exe`：只显示置顶卡片。

说明：

- `data\`、`config.toml`、`docs\` 会被复制到 exe 旁边；`logs\` 首次运行时生成；
- 如果放在不可写目录（如 `Program Files`），自动改用 `%LOCALAPPDATA%\Dota2Coach` 存配置和日志；
- 换电脑/发给朋友：整个 `dist\Dota2Coach\` 目录一起拷走即可，不需要装 Python。

## 12. 主窗口的威胁标记 / 赛后复盘 / 辅助开关

- 威胁徽章：敌人头像下显示「先手 / 爆发 / 隐身」。先手 = OpenDota 角色含 Initiator/Disabler，爆发 = Nuker，隐身 = 常见隐身英雄名单；阵容标题右侧给出人数汇总。
- 赛后复盘：识别到对局结束，阵容区整页换成上一局数据（KDA / 正反补 / GPM / 时长）、1–3 条改进建议与一句鼓励；30 秒后或点「回到主页」返回。
- 辅助开关（设置 → 辅助）：
  - 刷新播报：符点 / 神龛 / 莲花刷新前的卡片与朗读；
  - 名字显示：对局中顶部头像下的英雄名字条；
  - 团战提醒：20 分钟后的团战 / 小地图预警；
  - 对线提醒：分路、对位、补给与对线期提示。
  关闭后不显示也不朗读，保存立即生效（写入 config.toml 的 [assist] 段）。
- F8 / F9：F8 显示/隐藏置顶卡片，F9 试听语音；主页有醒目提示。

## 13. 应用图标

- 图标资源：data/app.ico（16/24/32/48/64/128/256 多尺寸）与 data/app.png（512），随 data\ 目录一起分发。
- 生效位置：主窗口标题栏与任务栏、系统托盘、两个 exe 文件图标；主窗口缺失图标时回退到蓝底 “D” 占位图，不会报错。
- 想换图标：替换 data/app.ico 与 data/app.png 即可（无需改代码）；或修改 scripts/make_icon.py 的颜色/字标后运行
  python scripts\make_icon.py 重新生成。
- 打包时 scripts/build.ps1 会加 --icon data\app.ico 写进 exe 资源；覆盖 exe 后如果资源管理器仍显示旧图标，
  重启资源管理器（	askkill /f /im explorer.exe 后重新打开）或把 exe 改名一次，这是 Windows 的图标缓存。
- 任务栏分组：Windows 下设置了 AppUserModelID = Dota2Coach.App，任务栏会按本程序而不是 python.exe 分组。

## 13. 可选：YouTube 攻略源

前提：当前网络能访问 `www.youtube.com`（国内需自备代理）。

```powershell
# 单个英雄试跑（有代理时加 --proxy）
python scripts\fetch_youtube_guides.py --heroes slark --per-hero 1 --proxy "http://127.0.0.1:7890"

# 全英雄（较慢，建议先小范围验证）
python scripts\fetch_youtube_guides.py --all-heroes --per-hero 2
```

- 有官方字幕：直接读字幕；没字幕：自动下载音频并用 `faster-whisper` 转写（需先跑 `scripts\setup_asr.ps1`）。
- 需要 LLM 提炼时，`.env` 里要有 `DEEPSEEK_API_KEY`（同 B 站攻略）。
- 抓到的提示会合并进 `data/guides/<patch>.json`，与 B 站来源共用。
