<!-- 語言 / Language -->
[简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [English](README.en.md) · [Français](README.fr.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [Português](README.pt.md) · [Español](README.es.md) · [Türkçe](README.tr.md)

# DOTA2 入門教練（DOTA2 GETTING STARTED Coach）

Dota 2 即時教練（外部 Overlay）。只靠 **Valve 官方 GSI** 加 **自己螢幕的截圖辨識**：
不讀記憶體、不注入、不模擬按鍵、不需要任何遊戲 Mod。

<p>
  <a href="https://github.com/He-Xiqing/dota2-coach/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/He-Xiqing/dota2-coach/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-3776AB">
</p>

## 截圖

<p align="center">
  <img src="docs/img/panel-roster.png" width="32%" alt="lineup">
  <img src="docs/img/card.png" width="32%" alt="lane card">
  <img src="docs/img/summary.png" width="32%" alt="post-game summary">
</p>

## 這是給誰用的

**給剛接觸 DOTA2 的新手**：認不全英雄、不知道對線該站哪、出裝靠抄、團戰不知道該做什麼的玩家。

設計上刻意做了這些取捨：

- **不替你操作**：只在需要時說一句話，不給一堆數據面板；
- **不需要 Dota Plus**：截頂部英雄欄就能認人，普通帳號也能用；
- **不讀遊戲記憶體**：只收官方 GSI 與截自己的螢幕；
- **九語言介面＋九語言朗讀**：介面、提示、朗讀一起切換；
- **打完有復盤**：輸贏都給 1–3 條能立刻改的建議。

## 現在能做什麼

- 接收 GSI：自己的英雄/等級/血量/魔力/技能/裝備/金錢/KDA、比賽時間、比分；
- **決策時間自動截圖**，辨識雙方 10 個英雄（預設頂部英雄欄，不需要 Dota Plus）；實測 2560×1600 截圖 10/10；
- 對局中在**頭像下方寫名字**（隊友淺綠、對手淺紅，不擋滑鼠）；
- 右上角半透明**置頂卡片**：階段與時間、雙方陣容、下一件裝備、符點提醒；
- **對線教練**：判斷你在哪條路，依敵方威脅（先手/爆發/推線/隱身）給站位與血線提示，另有 4 分鐘眼位、5 分鐘天黑、6 級遊走、補刀落後提醒；
- **提示音＋九語言朗讀**：符點、對線、出裝、物品使用與團戰建議都會「叮」一聲再念出來；朗讀用線上 edge-tts，系統語音壞掉也能用；**語音包跟著介面語言自動切換**；
- **B 站攻略庫**：定時抓同版本攻略（標題/評論/彈幕，可選轉寫），LLM 提煉成一句話，局內提示；每週自動更新並清理過舊/重複提示；
- **介面三態**：主介面只打招呼；對局中顯示教練資訊；結束後換成上一把數據、1–3 條建議與一句鼓勵，30 秒後回主介面；
- **主題**：主介面可換背景圖（設定 → 主題）；
- **語音包**：內建 13 個 edge 音色（中文 5 個＋繁中/英/法/俄/德/葡/西/土各 1 個），也可自訂；
- **團戰提醒**：10 分鐘後掃小地圖紅/綠點，敵方消失、我方集結、團戰爆發時給建議，並依你的定位（肉盾/控制/法師/刺客/輔助）說明該頂、該盯誰、該切誰；小地圖位置/大小可手動指定；
- **F8 呼出卡片**：任意時刻顯示/隱藏置頂卡片，F9 試聽語音；卡片預設點擊穿透。

## 近期新增

- **九語言**：简体中文、繁體中文、English、Français、Русский、Deutsch、Português、Español、Türkçe；主介面、設定、說明、復盤、出裝說明頁與語音包都會跟隨切換，主介面即時生效、不用重啟。
- **九語言朗讀**：物品提醒（笛子/赤紅甲/衛士脛甲/梅肯/微光/蓮花/炎陽/鐵意、點金手/秘法/靈魂之戒/魔杖/瓶子/支配）、對線補給（粉/魔棒/圓盾/吃樹）、符點與團戰提示都會用當前語言念出來；非中文介面不再混入中文技能名。
- **出裝說明頁**：依當前語言生成 `data/ingame_guide.<lang>.html`。
- **小地圖自適應**：自動在左下/右下尋找並適配縮放；認不準時可在 設定 → 輔助 → 小地圖 手動指定位置、大小與 X/Y 偏移；掃描提前到 10 分鐘，長時間沒有紅點會自動重新定位。
- **朗讀更自然**：提示文本先清洗（`·`、`——`、`（）`、`7:00`、`6.8k`），按音訊真實長度播放；舊設定裡的音色顯示名會自動換算成 edge 音色 ID。
- **復盤更懂定位**：輔助不會再被提醒「補刀少／打錢慢」；開局招呼與賽後鼓勵每次隨機。
- **出裝一次一件**：只推現在最該買的那件，附理由、用法與加點，買完自動換下一件。
- **雙擊即用**：`Dota2Coach.exe` 開主視窗，`Dota2Coach-Card.exe` 只要置頂卡片；升級時啟動會自動清掉殘留的 `*.old.exe`。

## 快速開始

```powershell
cd <專案目錄>

# 1) 建環境、裝依賴（需要 Python 3.12）
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

# 2) 把 GSI 設定複製進遊戲目錄
powershell -ExecutionPolicy Bypass -File .\scripts\copy_gsi.ps1

# 3) 下載模板與資料（只需一次）
powershell -ExecutionPolicy Bypass -File .\scripts\fetch_hero_icons.ps1
.\.venv\Scripts\python.exe scripts\fetch_popularity.py
.\.venv\Scripts\python.exe scripts\build_item_table.py

# 3.5) 可選：線上朗讀（九種語言共用這一個依賴）
.\.venv\Scripts\pip.exe install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4) 重啟 Dota 2，啟動教練
powershell -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

詳細步驟與排錯見 [docs/install.md](docs/install.md)（英文版說明在 `docs/install.en.md` 逐步補齊）。

## 換語言與朗讀

設定 → 語言：九種語言任選，儲存後主視窗立即切換（不用重啟）；語音包會自動換成該語言，自訂音色包保持不動。
設定 → 語音：可開關朗讀、調語速/音量、點「試聽當前語音」；朗讀失敗會自動退回提示音，日誌在 `logs\voice.log`。

## 資料邊界

| 資料 | 來源 | 說明 |
|---|---|---|
| 自己的英雄/技能/裝備/金錢 | GSI | 官方介面，即時 |
| 比賽時間/比分/防禦塔 | GSI | 官方介面，即時 |
| 雙方陣容 | 決策時間截圖 | 一般對局 GSI 只給「你自己」 |
| 敵方位置/團戰聚集 | 小地圖截圖 | 顏色分割＋聚類 |
| 出裝 | OpenDota 物品熱度 | 離線快取 |
| 陣容角色/勝率 | OpenDota heroStats | 目前版本統計 |
| 攻略提示 | B 站影片＋DeepSeek 提煉 | 同版本攻略 |
| 朗讀 | 線上 edge-tts（可關） | 九語言音色，失敗退回提示音 |

**紅線**：不讀遊戲記憶體、不注入、不送出任何輸入、不代打。

## 路線圖

| 階段 | 內容 | 狀態 |
|---|---|---|
| M0 | GSI 打通、報文落盤、安裝腳本 | 完成 |
| M1 | 截圖辨識雙方陣容＋置頂卡片 | 頂部英雄欄 10/10 |
| M2 | 知識庫＋選人推薦 | 未開始 |
| M3 | 對線教練 | 完成 |
| M4 | 出裝推薦 | 單件推薦＋理由/用法/加點 |
| M5 | 團戰提醒 | 小地圖紅/綠點＋定位建議（10 分鐘後） |
| M6 | 打包與文件 | 主視窗＋設定/說明＋雙 exe |
| M7 | B 站攻略庫 | 已跑通 |

## 打包與測試

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

產物：`dist\Dota2Coach\Dota2Coach.exe`（主視窗）與 `dist\Dota2Coach-Card\Dota2Coach-Card.exe`（只要卡片）。

## 下載

- 免安裝版（Windows x64）：[Releases](https://github.com/He-Xiqing/dota2-coach/releases/latest) — 下載 zip 解壓後雙擊 `Dota2Coach.exe`
- 從原始碼執行：見上方「快速開始」

## 合規與免責

- 非 Valve 官方產品，與 Valve 無關聯。
- 只讀取官方 GSI 與你自己螢幕的截圖；不讀記憶體、不注入、不模擬按鍵。
- 請遵守 Steam 與 Dota 2 服務條款，使用風險自負。

## 致謝

[OpenDota](https://www.opendota.com/) · [Bilibili](https://www.bilibili.com/) · [edge-tts](https://github.com/rany2/edge-tts) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

## 更多

- 最完整的說明（含目錄、資料來源與版本管理）見 [README.zh-CN.md](README.zh-CN.md)。
- 資料集與腳本細節見 [docs/data-sources.md](docs/data-sources.md)。
