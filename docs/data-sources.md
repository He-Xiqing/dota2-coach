# GSI 字段实测记录

> 这份文档只记录**实测**结果。没测过的字段一律写"待实测"，不要凭印象填。
> 采集方式见 `docs/install.md` 第 4 节；原始数据在 `logs/gsi_raw/*.jsonl`，
> 字段清单在 `logs/gsi_keys.json`。

## 1. 采集记录

| 项 | 值 |
|---|---|
| 采集日期 | 2026-11-07 |
| 客户端 | `-perfectworld` 完美世界国服（Steam 库 `D:\SteamLibrary`） |
| 游戏版本 | 2026-11-07 当天的国服版本（未记录具体 build） |
| 对局类型 | 本地大厅 10 人机（AP） |
| 分辨率 | 未记录（探针只收 GSI，不看屏幕） |
| 报文条数 | 1941 条 / 12.2 MB（对局 9079443351，38 分钟） |

原始文件：`logs/gsi_raw/9079443351-20261107-112141.jsonl`，另有
`9079442839-*.jsonl`（11.7 KB，选人后中止）和 `unknown-*.jsonl`（主菜单心跳）。

## 2. 需要回答的问题

| # | 问题 | 实测结论 |
|---|---|---|
| 1 | 普通匹配（AP）英雄选择阶段有没有 `draft` 段？ | **有键、永远为空**：1941 条报文全部带 `draft`，`draft == {}`；没有 picks/bans。 |
| 2 | 开局后 `draft` 是否残留？ | 一直存在且一直是空对象，不会填充。 |
| 3 | `events` 段什么时候出现？内容有哪些？ | 1566/1941 条报文带 `events`，每条 1–11 个事件；**会累加、跨报文重复**，必须按 `(game_time, data)` 去重。 |
| 4 | `abilities` 有多少槽位？天生技能/魔晶技能怎么表示？ | **在顶层 `abilities`**（不在 `hero` 里），`ability0..ability8` 共 9 槽；字段 `name/level/can_cast/passive/ability_active/cooldown/max_cooldown/ultimate`，带充能的还有 `charges/max_charges/charge_cooldown`。天生技能 `plus_high_five` 和活动技能（如 `seasonal_dark_carnival_*`）也在里面，按 `passive`/`ultimate` 过滤。 |
| 5 | `items` 有哪些前缀？ | `slot0..slot8`（9 格）、`stash0..stash5`、`teleport0`、`neutral0/neutral1`、`preserved_neutral6..10`；空槽是字符串 `"empty"`；物品字段 `name/purchaser/item_level/can_cast/cooldown/max_cooldown/passive`。被动装备没有 `cooldown`（值为 null）。 |
| 6 | `map.game_state` 全流程取值？ | `DOTA_GAMERULES_STATE_INIT → WAIT_FOR_PLAYERS_TO_LOAD → HERO_SELECTION → STRATEGY_TIME → TEAM_SHOWCASE → PRE_GAME → GAME_IN_PROGRESS → POST_GAME`（实测各状态都出现过）。 |
| 7 | 开局倒计时 `game_time` 是负数吗？ | 本局没出现负值：最小 13 秒；`clock_time` 与 `game_time` 在开局前一致，结束后差 183 秒（`game_time=2271, clock_time=2088`）。**用 `clock_time` 做"对线期/比赛时间"判断。** |
| 8 | 暂停/掉线/重连时状态怎么变？ | 待实测。 |
| 9 | `player` 的 `gpm/xpm/net_worth` 是否实时更新？ | `gpm/xpm` 存在且随对局变化；没有 `net_worth` 字段（用 `gold` + 装备自己算）。 |
| 10 | `buildings` 是否每帧都有？ | 每条报文都有，但**只有己方队伍**（`radiant`），看不到敌方塔。 |
| 11 | 结束画面 `game_state` / `win_team`？ | `POST_GAME` 时 `map.win_team` 有值（`radiant`/`dire`）；`map.matchid` 是字符串。 |
| 12 | 报文频率受 `throttle 0.1` 限制吗？ | 本局平均约 0.9 条/秒（记录器自己还有 `min_log_interval=0.2` 节流），**远低于 10 条/秒**；按"变化时推送 + 30 秒心跳"设计即可，不要假设每 100ms 都有报文。 |

## 3. 关键结论（直接影响产品设计）

1. **GSI 永远给不出敌方英雄。** `hero.id` 只在本方英雄确定后非 0（实测只有 `0` 和 `1`=敌法师），`player` 只有自己的 `steamid/player_slot/team_name`。所以"识别双方所选英雄"只能靠**屏幕识别顶部英雄栏**，没有第二条路。
2. **`draft` 在 AP 人机局不可用**（空对象）。选人推荐在 AP 下只能基于"我方已选 + 位置 + 版本数据"；敌方阵容要等揭晓画面截图识别。CM/观战局才有真实 `draft`，这条仍待实测。
3. **击杀事件可用且信息量大**：`CHAT_MESSAGE_HERO_KILL` 带 `playerid1`（击杀者 0–9）、`playerid2`（被击杀者）、`time`。本局 60 个唯一击杀 = 比分 50+10 完全吻合。**团战检测可以直接用"10 秒内 ≥2 个击杀"这类事件规则**，不需要只依赖小地图。
4. **自己的坐标有了**：`hero.xpos/ypos`（实测 t=594s 时 `6450,-3921`；t=1153s 时 `-4981,4014`），配合小地图识别敌方红点可算距离。`hero` 还有 `buyback_cost/buyback_cooldown/respawn_seconds/health/mana/silenced/stunned/hexed/disarmed/magicimmune/smoked/break/permanent_buffs`，足够做"能不能打"的判断。
5. **敌方位置/敌方装备没有任何官方通道**：`map` 只有 `radiant_score/dire_score/daytime/ward_purchase_cooldown` 等，`added` 只推送 `player` 字段。小地图颜色识别是唯一来源。
6. **事件里的 `value` 不是英雄 id**：HERO_KILL 的 `value` 实测 210–522，更像赏金/连杀奖励，不要拿它当英雄编号用。

## 4. 报文骨架（真实报文节选）

```jsonc
{
  "provider": {"name": "Dota 2", "appid": 570, "version": 47, "timestamp": 1794024301},
  "map": {
    "name": "start", "matchid": "9079443351",
    "game_state": "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
    "game_time": 1175, "clock_time": 992,
    "daytime": true, "nightstalker_night": false, "paused": false,
    "radiant_score": 50, "dire_score": 10, "win_team": null,
    "ward_purchase_cooldown": 0
  },
  "player": {"steamid": "76561199447190425", "name": "Frog.Quack",
             "team_name": "radiant", "player_slot": 0, "team_slot": 0},
  "hero": {"id": 1, "name": "npc_dota_hero_antimage", "level": 12,
           "health": 1000, "mana": 400, "alive": true,
           "xpos": -4981, "ypos": 4014, "buyback_cost": 2606, "respawn_seconds": 0},
  "abilities": {"ability0": {"name": "antimage_mana_break", "level": 4,
                              "passive": true, "can_cast": false}},
  "items": {"slot0": {"name": "item_bfury", "cooldown": 0, "max_cooldown": 4,
                       "can_cast": true}},
  "buildings": {"radiant": {"dota_goodguys_tower1_top": {...}}},
  "events": [{"game_time": 85, "event_type": "generic_event",
              "data": "{\"type\":\"CHAT_MESSAGE_ITEM_PURCHASE\",\"value\":43,\"playerid1\":4}"}]
}
```

## 5. 事件类型清单（本局出现过的）

| 类型 | 次数（含重复） | 用途 |
|---|---|---|
| `CHAT_MESSAGE_HERO_KILL` | 1576 | 团战/击杀播报，去重后 60 条 |
| `CHAT_MESSAGE_ITEM_PURCHASE` | 1519 | 敌方出装线索（只有 playerid，没有英雄 id） |
| `CHAT_MESSAGE_STREAK_KILL` | 945 | 连杀 |
| `bounty_rune_pickup` | 287 | 赏金符（对线期计时） |
| `CHAT_MESSAGE_TOWER_KILL` | 261 | 推塔 |
| `CHAT_MESSAGE_OBSERVER_WARD_KILLED` | 132 | 假眼被反 |
| `CHAT_MESSAGE_GLYPH_USED` | 131 | 塔防 |
| `CHAT_MESSAGE_SENTRY_WARD_KILLED` | 78 | 真眼被反 |
| `CHAT_MESSAGE_BARRACKS_KILL` | 52 | 兵营 |
| `CHAT_MESSAGE_FIRSTBLOOD` | 26 | 一血 |
| `aegis_picked_up` | 26 | 肉山盾 |

## 6. 附录：如何快速查字段

```powershell
# 用项目自带的检查工具（推荐）
.\.venv\Scripts\python.exe tools\inspect_capture.py logs\gsi_raw\9079443351-20261107-112141.jsonl

# 看看有没有 draft / events 相关字段
Select-String -Path .\logs\gsi_keys.json -Pattern 'draft|events'
```

## 7. 地图机制时间表（7.41f）

来源：Valve 补丁说明（7.29–7.41f），并逐条核对 senseos.gg 的 objective timers 页面
（https://senseos.gg/guides/dota-2/objective-timers/ ，2026-10-23 更新）。

| 机制 | 时间 | 实现常量（`src/dota2coach/coach/timers.py`） |
|---|---|---|
| 赏金符 | 0:00 四个，之后每 **4 分钟**（7.38 改） | `BOUNTY_PERIOD=240` |
| 水符 | 只在 2:00 / 4:00 | `WATER_TIMES=(120,240)` |
| 强化神符 | 6:00 起每 2 分钟 | `POWER_FIRST=360`, `POWER_PERIOD=120` |
| 智慧神龛 | 7:00 起每 7 分钟（取代经验神符） | `WISDOM_FIRST=420`, `WISDOM_PERIOD=420` |
| 莲花池 | 3:00 起每 3 分钟一朵（最多 6） | `LOTUS_FIRST=180`, `LOTUS_PERIOD=180` |
| 痛苦魔方 | 20:00 首现 | `TORMENTOR_FIRST=1200` |

卡片只在**刷新前 25 秒**提醒（`upcoming(clock, horizon=25.0)`），同一时刻多个机制会各占一行；
朗读文本与卡片行一致，紧急度由 `Hint` 的先后顺序决定。版本更新后只需改上面的常量与 `tests/test_coach.py`。