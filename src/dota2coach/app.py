"""应用主循环：GSI 快照 + 决策时间截屏识别 + 置顶卡片。

线程模型：GSI 的 HTTP 回调在服务器线程里，只做"存最新快照"；
所有界面更新都在 Qt 主线程的 QTimer 里完成。
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from .coach.advice import lane_hint
from .coach.fight import FightTracker
from .coach.gameaudio import GameAudioGate
from .coach.item_use import ItemUseTracker
from .coach.guides import GuideStore
from .coach.items_advice import recommend
from .coach.lane import lane_tips
from .coach.lane_items import lane_items
from .coach.roster import Roster, roster_from_matches
from .coach.state import CoachState, HealthTracker, clock_time, format_clock, phase_for
from .coach.texts import language as texts_language, phase_name, set_language, t
from .coach.summary import MatchSummary, encourage, improvements, summarize, summary_lines
from .coach.threats import threat_labels, threat_summary
from .coach.timers import phase_tip, upcoming
from .coach.tp import tp_key, tp_reminder
from .config import Config
from .gsi.recorder import GsiRecorder
from .gsi.server import GsiServer
from .knowledge.builds import load_item_table, load_popularity
from .knowledge.skills import load_hero_skills, skills_file_for
from .knowledge.meta import load_hero_meta
from .knowledge.timing import load_hero_timing
from .ui import voices
from .ui.overlay import OverlayWindow
from .ui.namestrip import NameStrip
from .ui.voice import Speaker
from .vision.capture import ScreenCapture
from .vision.minimap import (
    MINIMAP_FRAC,
    MinimapDots,
    StaticFilter,
    crop_minimap,
    detect_dots,
    locate_minimap,
)
from .vision.heroes import (
    ensure_min_size,
    HeroInfo,
    HeroMatcher,
    identify_panel,
    identify_topbar,
    imread_path,
    imwrite_path,
    load_hero_table,
)

STRATEGY_STATES = {
    "DOTA_GAMERULES_STATE_STRATEGY_TIME",
    "DOTA_GAMERULES_STATE_TEAM_SHOWCASE",
}
CAPTURE_DELAY_S = 1.2
MAX_CAPTURE_ATTEMPTS = 20
MAX_BAR_TRIES = 6
MAX_HUD_TRIES = 6
SUMMARY_SECONDS = 30.0


def _short_name(hero_name: str | None) -> str | None:
    if not hero_name:
        return None
    return hero_name.removeprefix("npc_dota_hero_")


def _port_busy(host: str, port: int) -> bool:
    """31982 已被占用说明已有实例在跑：两个实例的卡片会互相遮挡面板。"""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            return sock.connect_ex((host, int(port))) == 0
    except OSError:
        return False


def _clean_old_binaries() -> None:
    """删除上次替换 exe 时留下的 *.old.exe（文件可能仍被旧进程占用，忽略失败）。"""
    import sys
    from pathlib import Path

    if not getattr(sys, "frozen", False):
        return
    exe = Path(sys.executable)
    for cand in (exe.with_suffix(".old.exe"), exe.parent / f"{exe.stem}-old.exe"):
        try:
            if cand.exists():
                cand.unlink()
        except OSError:
            pass


class CoachApp:
    def __init__(
        self,
        config: Config,
        screenshot: Path | None = None,
        seconds: float | None = None,
        save_overlay: Path | None = None,
        snapshot_path: Path | None = None,
    ) -> None:
        self.config = config
        set_language(config.app.language)
        _clean_old_binaries()
        self.screenshot = screenshot
        self.seconds = seconds
        self.save_overlay = save_overlay
        self.snapshot_path = snapshot_path

        self.state = CoachState()
        self.assist = config.assist
        self.matcher = HeroMatcher(
            load_hero_table(config.vision.heroes_json),
            config.vision.icons_dir,
            config.vision.cards_dir,
        )
        self.popularity = load_popularity(config.data_dir / "popularity.json")
        self.item_by_id, self.item_names = load_item_table(config.data_dir / "items.json")
        self._load_localized_items(config.data_dir)
        self.hero_skills = load_hero_skills(
            skills_file_for(config.data_dir, config.app.language)
        )
        self.matchups = self._load_json(config.data_dir / "matchups.json")
        self.hero_meta = load_hero_meta(config.data_dir / "hero_meta.json")
        self.hero_timing = load_hero_timing(config.data_dir / "hero_timing.json")
        self.guides = (
            GuideStore.load(config.guides.dir, patch=self._current_patch())
            if config.guides.enabled
            else GuideStore()
        )
        self.cost_by_name = {info.name: info.cost for info in self.item_by_id.values()}
        self.health = HealthTracker()
        self._audio_gate = (
            GameAudioGate() if config.voice.wait_game_voice else None
        )
        pack = voices.effective_pack(config.voice.pack, config.app.language)
        edge_voice, rate, volume = voices.resolve(
            pack,
            config.voice.edge_voice,
            config.voice.rate,
            config.voice.volume,
        )
        self.speaker = Speaker(
            enabled=config.voice.enabled,
            speak=config.voice.speak,
            backend=config.voice.backend,
            edge_voice=edge_voice,
            rate=rate,
            volume=volume,
            min_interval=config.voice.min_interval,
            beep=config.voice.beep,
            gate=self._audio_gate,
            wait_max=config.voice.wait_max,
            log_path=config.log_dir / "voice.log",
        )
        detail = ""
        if self.speaker.last_error:
            # 异常文本里可能带控制台编码不了的替换字符，先降级成 GBK 可打印的形式
            detail = " 问题=" + self.speaker.last_error.encode("gbk", "replace").decode("gbk", "replace")
        print(
            f"语音: enabled={self.speaker.enabled} speak={self.speaker.speak} "
            f"beep={self.speaker.beep} backend={self.speaker.backend}{detail}"
        )

        self.recorder = GsiRecorder(config.log_dir / "gsi_raw", min_interval=config.gsi.min_log_interval)
        self.server: GsiServer | None = None
        self.capture: ScreenCapture | None = None
        self.overlay: OverlayWindow | None = None

        self._capture_at: float | None = None
        self._capture_attempts = 0
        self._last_render: tuple | None = None
        self._spoken: set[str] = set()
        self._match_id: str | None = None
        self._last_topmost = 0.0
        self._strip_was_visible = False
        self._refresh_strip_was_visible = False
        self._bar_refresh_at: float | None = None
        self._bar_game_key: str | None = None
        self._bar_tries = 0
        self._bar_failed = False
        self._hud_at: float | None = None
        self._hud_tries = 0
        self._last_payload = 0.0
        self._win_key: tuple | None = None
        self._dpr = 0.0
        self._res_checked_at = 0.0
        # 切出游戏 5 秒后隐藏头像下的名字条，回到游戏再显示
        self._focus_lost_at: float | None = None
        self._strip_hidden_by_focus = False
        # 小地图团战提醒
        self._fight = FightTracker()
        self.item_use = ItemUseTracker()
        self._fight_hints: list = []
        self._mm_at = 0.0
        self._mm_rect = None
        self._mm_misses = 0
        self._mm_debug_saved = False
        self._guides_update_started = False
        self._mm_static: StaticFilter | None = None
        self._mm_since: float | None = None
        self._deadline: float | None = None
        self._last_spoken = ""
        self._region_logged = False
        self._data_warned = False
        self._bar = None  # (截取区域, 顶部栏 10 个 HeroMatch.box, 缩放系数)，给头像下的名字条用
        self.namestrip: NameStrip | None = None
        # 界面模式：idle=主界面问候，game=对局中，summary=赛后小结（自动回 idle）
        self._mode = "idle"
        self._last_summary: MatchSummary | None = None
        self._summary_until = 0.0
        self._summary_spoken = False
        self._summary_hint = ""
        self._greeted = False
        # 面板（ui/panel.py）读取：最近一次卡片内容
        self._last_title = ""
        self._last_hint_parts: list[str] = []
        self._last_build_text = ""
        self._timer: QTimer | None = None
        self._attached = False
        self.panel_mode = False

    _ITEM_NAME_FILES = {
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

    def _current_patch(self) -> str:
        """本地缓存的版本号（scripts/fetch_guides.py 会写 data/patch.json）。"""
        return str(self._load_json(self.config.data_dir / "patch.json").get("patch") or "")

    @staticmethod
    def _load_json(path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return {}
        return raw if isinstance(raw, dict) else {}

    def _matchup_line(self) -> str:
        """我方英雄对敌方阵容的历史胜率（OpenDota 全服数据，不是本局数据）。"""
        roster = self.state.roster
        hero = self._self_hero()
        if roster is None or hero is None or not self.matchups:
            return ""
        table = self.matchups.get(str(hero.hero_id))
        if not isinstance(table, dict):
            return ""
        rates: list[tuple[float, str]] = []
        for enemy in roster.enemies:
            if enemy is None:
                continue
            row = table.get(str(enemy.hero_id))
            if not isinstance(row, list) or len(row) < 2 or int(row[0]) < 80:
                continue
            rates.append((int(row[1]) / int(row[0]), enemy.name_loc))
        if len(rates) < 3:
            return ""
        average = sum(rate for rate, _ in rates) / len(rates)
        worst_rate, worst_name = min(rates, key=lambda item: item[0])
        return t("label_matchup", avg=f"{average * 100:.0f}", name=worst_name, rate=f"{worst_rate * 100:.0f}")

    # ------------------------------------------------------------------
    # GSI
    # ------------------------------------------------------------------
    def _on_snapshot(self, snapshot) -> None:  # 在 HTTP 服务器线程里
        self.recorder.record(snapshot)
        self.state.snapshot = snapshot
        self._last_payload = time.monotonic()
        if self.state.roster is not None and self.state.roster.complete:
            return
        if snapshot.game_state in STRATEGY_STATES:
            if self.state.roster is None or not self.state.roster.complete:
                if self._capture_at is None and self._capture_attempts < MAX_CAPTURE_ATTEMPTS:
                    self._capture_at = time.monotonic() + CAPTURE_DELAY_S

    # ------------------------------------------------------------------
    # 截屏识别
    # ------------------------------------------------------------------

    def _localize_roster(self, roster):
        """非中文界面：把名单中的英雄名替换为对应语言（来自 skills 数据）。"""
        if texts_language() == "zh-CN" or not getattr(self, "hero_skills", None):
            return roster

        def fix(hero):
            if hero is None:
                return None
            info = self.hero_skills.get(int(getattr(hero, "hero_id", 0) or 0))
            if info is None or not info.name:
                return hero
            return replace(hero, name_loc=info.name)

        return replace(
            roster,
            allies=tuple(fix(hero) for hero in roster.allies),
            enemies=tuple(fix(hero) for hero in roster.enemies),
        )

    def _identify(self, image, self_hero: HeroInfo | None, stamp: str):
        """先认顶部英雄栏（不依赖 Dota Plus），不够再用“战友与宿敌”面板兜底。"""
        min_score = self.config.vision.match_min_score
        min_gap = self.config.vision.match_min_gap
        best = None
        # 1) 用自己的英雄卡面当锚点，自适应各种分辨率/HUD 缩放
        if self_hero is not None and self_hero.short and self.matcher is not None:
            for _, boxes in self.matcher.locate_bar_candidates(image, self_hero.short, limit=3):
                matches = [self.matcher.identify(image, box, "card", min_score, min_gap) for box in boxes]
                candidate = roster_from_matches(matches[:5], matches[5:], self_hero, stamp, "topbar")
                if best is None or candidate.known > best[0].known:
                    best = (candidate, [match.box for match in matches])
                if candidate.known >= 9:
                    break
        # 2) 固定比例切栏
        raw = identify_topbar(image, self.matcher, min_score=min_score, min_gap=min_gap)
        candidate = roster_from_matches(raw["ally"], raw["enemy"], self_hero, stamp, "topbar")
        if best is None or candidate.known > best[0].known:
            best = (candidate, [match.box for match in raw["ally"] + raw["enemy"]])
        roster, bar = best
        if roster.known >= 8:
            return self._localize_roster(roster), bar
        # 3) “战友与宿敌”面板兜底（Dota Plus）
        panel = identify_panel(image, self.matcher, min_score=min_score, min_gap=min_gap)
        roster2 = roster_from_matches(panel["ally"], panel["enemy"], self_hero, stamp)
        if roster2.known > roster.known:
            roster = roster2
        return self._localize_roster(roster), bar

    def _capture_roster(self) -> None:
        if self.capture is None or not self.matcher.ready or self.state.snapshot is None:
            self._capture_attempts = MAX_CAPTURE_ATTEMPTS
            return
        self._capture_attempts += 1
        try:
            image = ensure_min_size(self.capture.grab(), 1200)
            used_region = self.capture.last_region
        except Exception as exc:  # noqa: BLE001
            print(f"[识别] 截屏失败：{exc}", file=sys.stderr)
            return

        self_hero = self._self_hero()
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        roster, bar = self._identify(image, self_hero, stamp)
        if roster.known < 3:
            # 窗口识别可能抓错了窗口（比如抓到了 Steam 浏览器）：退回整屏再试一次，取更好的那帧
            monitor = self.capture.monitor()
            region = self.capture.last_region
            if region is not None and region != monitor:
                try:
                    fallback = ensure_min_size(self.capture.grab(monitor), 1200)
                    roster2, bar2 = self._identify(fallback, self_hero, stamp)
                    if roster2.known > roster.known:
                        image, roster, bar = fallback, roster2, bar2
                        used_region = monitor
                except Exception:  # noqa: BLE001
                    pass
        if bar:
            factor = image.shape[1] / used_region.width if used_region else 1.0
            self._bar = (used_region, bar, factor)
        elif roster.known >= 8:
            self._bar = None
        if roster.known == 0:
            print("[识别] 本帧没有识别出英雄，稍后重试", file=sys.stderr)
            return
        if self._region_logged is not True:
            self._region_logged = True
            print(f"[识别] 截取区域：{used_region.as_dict() if used_region else '整屏'}")
        current = self.state.roster
        if current is not None and roster.known < current.known:
            # 这一帧被其他窗口（聊天窗、控制台）挡住了一部分：保留之前更完整的结果
            print(f"[识别] 本帧只认出 {roster.known}/10，保留已有的 {current.known}/10，继续重试")
        else:
            self.state.roster = roster
        allies, enemies = roster.names()
        print(f"[识别] {roster.known}/10  我方 {'、'.join(allies)} | 敌方 {'、'.join(enemies)}")
        if roster.known < 10:
            self._save_debug(image, roster, stamp)

    def _capture_hud_roster(self) -> bool:
        """对局中才启动程序：没有选人界面，按比例切 HUD 顶部栏再逐格认人。"""
        if self.capture is None or self.matcher is None:
            return False
        from .vision.heroes import hud_cell_variants

        try:
            image = ensure_min_size(self.capture.grab(), 1200)
            region = self.capture.last_region
        except Exception as exc:  # noqa: BLE001
            print(f"[识别] 对局中启动截屏失败：{exc}", file=sys.stderr)
            return False
        min_score = min(0.45, self.config.vision.match_min_score)
        layouts: list[list[tuple[int, int, int, int]]] = []
        self_hero = self._self_hero()
        if self_hero is not None and self_hero.short and self.matcher is not None:
            scored: list[tuple[float, list[tuple[int, int, int, int]]]] = []
            for score, boxes in self.matcher.locate_bar_candidates(image, self_hero.short):
                fast = 0.0
                for (x, y, w, h) in boxes:
                    cell = image[max(0, y): y + h, max(0, x): x + w]
                    if cell.size:
                        fast += self.matcher.match_card_fast(cell)
                scored.append((fast / 10.0, boxes))
            scored.sort(key=lambda item: item[0], reverse=True)
            layouts = [boxes for _, boxes in scored[:3]]
        layouts += hud_cell_variants(image)
        best = None  # (known, roster, matches)
        for boxes in layouts:
            matches = [self.matcher.identify(image, box, "card", min_score, 0.0) for box in boxes]
            roster = roster_from_matches(matches[:5], matches[5:], self._self_hero(), "", "hud")
            if best is None or roster.known > best[0]:
                best = (roster.known, roster, matches)
            if roster.known >= 9:
                break
        if best is None:
            return False
        known, roster, matches = best
        if known < 8:
            print(f"[识别] 对局中启动：只认出 {known}/10，稍后再试", file=sys.stderr)
            return False
        self.state.roster = roster
        factor = image.shape[1] / region.width if region else 1.0
        self._bar = (region, [match.box for match in matches], factor)
        print(f"[识别] 对局中启动，已识别 {roster.known}/10：{roster.summary()}")
        return True

    def _save_debug(self, image, roster, stamp: str) -> None:
        """识别不全时存原图 + 标注图，方便排查是格子错了还是模板不对。"""
        try:
            import cv2

            from .vision.heroes import detect_panel_cells

            folder = self.config.log_dir / "screenshots"
            base = stamp.replace(":", "").replace(" ", "-")
            imwrite_path(folder / f"roster-{base}-raw.png", image)

            debug = image.copy()
            for (col, row), (x, y, w, h) in detect_panel_cells(image).items():
                hero = roster.enemies[row] if col else roster.allies[row]
                color = (0, 200, 0) if hero is not None else (0, 0, 220)
                cv2.rectangle(debug, (x, y), (x + w, y + h), color, 2)
                label = hero.short if hero is not None else "?"
                cv2.putText(
                    debug, label, (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1
                )
            name = f"roster-{stamp.replace(':', '').replace(' ', '-')}.png"
            path = self.config.log_dir / "screenshots" / name
            imwrite_path(path, debug)
            print(f"[识别] 标注图：{path}")
        except Exception as exc:  # noqa: BLE001
            print(f"[识别] 标注图保存失败：{exc}", file=sys.stderr)

    def _self_hero(self) -> HeroInfo | None:
        snapshot = self.state.snapshot
        if snapshot is None:
            return None
        hero_id = snapshot.hero_id
        if hero_id and hero_id in self.matcher.heroes:
            return self.matcher.heroes[hero_id]
        short = _short_name(snapshot.hero_name)
        if short:
            return self.matcher.by_short.get(short)
        return None

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    def _render(self) -> None:
        snapshot = self.state.snapshot
        clock = self.state.clock
        phase = phase_for(clock)

        if self._mode == "summary" and self._last_summary is not None:
            if self.namestrip is not None:
                self.namestrip.clear()
            self._render_summary(self._last_summary)
            return
        if snapshot is None or not snapshot.in_match:
            if self.namestrip is not None:
                self.namestrip.clear()
            self._render_idle(snapshot)
            return

        stats: list[str] = []
        if snapshot is not None and snapshot.in_match:
            stats.append(phase_name(phase))
            stats.append(f"{t('stat_networth')} {self._net_worth(snapshot) / 1000:.1f}k")
            stats.append(f"{t('stat_kda')} {snapshot.kda()}")
            player = snapshot.player or {}
            stats.append(f"{t('stat_cs')} {player.get('last_hits', 0)}/{player.get('denies', 0)}")
        elif snapshot is not None and snapshot.game_state:
            stats.append(snapshot.game_state.removeprefix("DOTA_GAMERULES_STATE_"))
        title = " · ".join(stats) if stats else "DOTA2 入门教练 · 等待对局开始"

        # 阵容名字已经画在游戏顶部头像下方，卡片里不再重复
        allies: list[tuple[str, str, bool]] = []
        enemies: list[tuple[str, str, bool]] = []
        info = self._matchup_line()
        build_text = self._item_text(snapshot)

        hint_parts, speak_items = self._collect_hints(snapshot, clock, phase)
        hint_text = "\n".join(hint_parts)
        self._last_title = title
        self._last_hint_parts = hint_parts
        self._last_build_text = build_text

        match_id = str(snapshot.match_id or "") if snapshot is not None else ""
        if match_id != self._match_id:
            self._match_id = match_id
            self._spoken.clear()
            self._fight = FightTracker()
            self.item_use.reset()
            self._fight_hints = []
            self._mm_at = 0.0
            self._mm_rect = None
            self._mm_misses = 0
            self._mm_debug_saved = False
            self._mm_static = None
            self._mm_since = None

        current = (title, info, build_text, hint_text)
        if current != self._last_render:
            if self.overlay is not None:
                self.overlay.render(title, info, build_text, hint_text)
            self._last_render = current
        self._update_name_strip()
        self._speak_new(speak_items)

    def _update_name_strip(self) -> None:
        """对局中在顶部英雄栏的头像下面写名字。"""
        strip = self.namestrip
        if strip is None:
            return
        if not self.assist.name_strip:
            strip.clear()
            strip.hide()
            return
        if self._strip_hidden_by_focus:
            strip.hide()
            return
        bar = self._bar
        if not bar or self.state.roster is None or self.state.snapshot is None:
            strip.clear()
            return
        region, boxes, factor = bar
        if not boxes:
            strip.clear()
            return
        physical = []
        names: list[str] = []
        ally_names, enemy_names = self.state.roster.names()
        all_names = ally_names + enemy_names
        for index, box in enumerate(boxes):
            if box is None:
                continue
            if hasattr(box, "left"):
                left, top, width, height = box.left, box.top, box.width, box.height
            else:
                left, top, width, height = box[0], box[1], box[2], box[3]
            physical.append(
                (
                    int((region.left if region else 0) + left / factor),
                    int((region.top if region else 0) + top / factor),
                    int(width / factor),
                    int(height / factor),
                )
            )
            names.append(all_names[index] if index < len(all_names) else "?")
        if not physical:
            strip.clear()
            return
        strip.show_names(physical, names, ally_count=len(ally_names))

    def _render_idle(self, snapshot) -> None:
        """主界面：只打招呼，不给任何对局建议。"""
        state = ""
        if snapshot is not None and snapshot.game_state:
            state = snapshot.game_state.removeprefix("DOTA_GAMERULES_STATE_")
        if state in ("", "MAIN_MENU", "INIT"):
            title = "DOTA2 入门教练 · 等待对局开始"
        else:
            title = f"DOTA2 入门教练 · {state}"
        lines = [
            "你好，我是你的 DOTA2 入门教练：菜单里不打扰你",
            "进入对局后自动识别双方阵容，对线期提醒分路/眼位/符点",
            "中后期推荐装备与用法，团战前预警",
        ]
        current = ("idle", title, tuple(lines))
        if current == self._last_render:
            return
        if self.overlay is not None:
            self.overlay.render_message(title, lines)
            if self.panel_mode:
                self.overlay.hide()
        self._last_render = current
        if not self._greeted:
            self._greeted = True
            import random

            self.speaker.say(t(f"greet_{random.randint(1, 4)}"), force=True)

    def _render_summary(self, summary: MatchSummary) -> None:
        """赛后：一整块换成上一把的数据、提升建议和鼓励。"""
        lines = summary_lines(summary)
        tips = improvements(summary)
        hint = self._summary_hint or encourage(summary, bool(tips))
        self._summary_hint = hint
        current = ("summary", summary, tuple(lines), hint)
        if current == self._last_render:
            return
        if self.overlay is not None:
            self.overlay.render_message(f"上一局 · {summary.result}", lines, hint)
            if self.panel_mode:
                self.overlay.hide()
        self._last_render = current
        if not self._summary_spoken:
            self._summary_spoken = True
            speech = "；".join(tips)
            lead = f"上一局结束。{speech}。" if speech else "上一局结束。"
            self.speaker.say(f"{lead}{hint}", force=True)

    def _track_match(self, snapshot) -> None:
        """在 idle / game / summary 三种界面状态之间切换。"""
        if snapshot is None:
            return
        if snapshot.in_match:
            if self._mode != "game":
                self._last_render = None
                # 断开 30 秒回来（或重连同一局）时，重新定位一次，否则名字条一直是空的
                if self._bar is None:
                    self._bar_failed = False
                    self._bar_refresh_at = time.monotonic() + 0.5
            self._mode = "game"
            # 决策界面的卡面和游戏内 HUD 的卡面大小/位置不一样：
            # 真正进游戏后重新检测一次顶部栏，名字条才不会错位。
            # 注意 -1:30 的倒计时阶段（PRE_GAME）HUD 已经换成小卡面，也要重定位。
            state = snapshot.game_state or ""
            phase = "in" if snapshot.is_in_game else ("pre" if state.endswith("PRE_GAME") else "")
            if phase:
                key = f"{snapshot.match_id or 'game'}-{phase}"
                if key != self._bar_game_key:
                    self._bar_game_key = key
                    self._hud_tries = 0
                    self._bar_refresh_at = time.monotonic() + 1.5
                    self._bar_failed = False
                    # 进游戏瞬间先别用决策界面的旧坐标画名字，等重新定位完再显示
                    self._bar = None
            if (
                self.state.roster is None
                and self._hud_at is None
                and self._hud_tries < MAX_HUD_TRIES
            ):
                # 对局中才启动程序：没有选人界面，改成按 HUD 比例切顶部栏认人
                self._hud_at = time.monotonic() + 2.0
            return
        if self._mode == "game":
            hero = self._self_hero()
            meta = self.hero_meta.get(snapshot.hero_id)
            summary = summarize(
                snapshot,
                hero.name_loc if hero else "?",
                roles=meta.roles if meta is not None else (),
            )
            if summary is not None:
                self._last_summary = summary
                self._summary_until = time.monotonic() + SUMMARY_SECONDS
                self._summary_spoken = False
                self._summary_hint = ""
                self._mode = "summary"
            else:
                self._mode = "idle"
            self._last_render = None
            return
        if self._mode == "summary" and time.monotonic() >= self._summary_until:
            self._mode = "idle"
            self._last_render = None

    def _collect_hints(self, snapshot, clock: float, phase: str) -> tuple[list[str], list[tuple[str, str, bool]]]:
        """返回 (卡片上显示的提示行, [(去重键, 朗读文本, 是否紧急)])。"""
        lines: list[str] = []
        speak: list[tuple[str, str, bool]] = []
        for hint in upcoming(clock, horizon=25.0) if self.assist.rune_alerts else ():
            remaining = max(0, int(round(hint.at - clock)))
            lines.append(hint.label())
            speak.append((f"rune:{int(hint.at)}:{hint.text}", f"{hint.text}，{remaining} 秒后", True))
        tip = phase_tip(clock)
        if tip:
            lines.append(tip)
            speak.append((f"phase:{tip}", tip, False))
        lane_text = ""
        if snapshot is not None and snapshot.is_in_game:
            hero = snapshot.hero or {}
            lane_text = lane_hint(hero.get("xpos"), hero.get("ypos")) or ""
        if phase == "对线期" and snapshot is not None and snapshot.in_match and self.assist.lane_alerts:
            # 分路只在开局报一次、显示 5 分钟，之后不再占卡片
            lane_raw = lane_text
            if lane_raw and 30 <= clock <= 5 * 60:
                lane_key_guess = "line_mid" if "中路" in lane_raw else (
                    "line_top" if "上路" in lane_raw else "line_bot"
                )
                if not texts_language().startswith("zh"):
                    lane_raw = t("label_lane", line=t(lane_key_guess))
                lines.append(lane_raw)
                speak.append((f"lane:{lane_text}", lane_raw, False))
            hp = snapshot.health_percent
            mp = snapshot.mana_percent
            enemies = self.state.roster.enemies if self.state.roster is not None else ()
            self_hero = self._self_hero()
            if "中路" in lane_text:
                lane_key = "中"
            elif "上路" in lane_text:
                lane_key = "上"
            elif "下路" in lane_text:
                lane_key = "下"
            else:
                lane_key = "任意"
            guide_tips = (
                self.guides.tips_for(self_hero.short, lane_key, "对线期", limit=4)
                if self_hero is not None and not self.guides.empty
                else []
            )
            for tip in lane_tips(
                lane=lane_text,
                clock=clock,
                enemies=enemies,
                meta=self.hero_meta,
                health_percent=None if hp is None else hp / 100.0,
                mana_percent=None if mp is None else mp / 100.0,
                last_hits=snapshot.last_hits,
                level=snapshot.level,
                timing=self.hero_timing,
                faction=(snapshot.player.get("team_name") or "").lower() or None,
                self_hero=self_hero,
                guide_tips=guide_tips,
                limit=4,
            ):
                lines.append(tip.text)
                speak.append((f"lane:{tip.key}", tip.text, tip.urgent))
            if clock < 300 and enemies:
                for item, why in lane_items(enemies, self.hero_meta):
                    text = f"{t('label_supply')}：{item} —— {why}"
                    lines.append(text)
                    speak.append((f"lane:item:{item}", text, False))
        # 20 分钟以后常备 TP：没带就每分钟提醒一次（TP 有独立格子 teleport0）
        if snapshot is not None and snapshot.in_match:
            tp_text = tp_reminder(clock, snapshot.has_tp_scroll())
            if tp_text:
                lines.append(tp_text)
                speak.append((tp_key(clock), tp_text, False))
        if not self.guides.empty and texts_language() == "zh-CN":
            self_hero = self._self_hero()
            lane_key = "任意"
            for word, key in (("中路", "中"), ("上路", "上"), ("下路", "下")):
                if word in lane_text:
                    lane_key = key
                    break
            for guide in self.guides.tips_for(
                self_hero.short if self_hero else "", lane_key, phase, limit=1
            ):
                lines.append(f"{t('label_guide')}：{guide.text}")
                speak.append((f"guide:{guide.id}", guide.text, False))
        # 小地图团战/地图意识（20 分钟后才有内容）
        if self.assist.fight_alerts:
            for hint in self._fight_hints:
                lines.append(hint.text)
                speak.append((hint.key, hint.text, hint.urgent))
        # 物品使用提醒：团战开团队装 / 冷却好了就用
        if snapshot is not None and snapshot.in_match:
            in_fight = any(h.key.startswith("fight:") for h in self._fight_hints)
            for tip in self.item_use.update(snapshot, clock, in_fight):
                lines.append(tip.text)
                speak.append((tip.key, tip.text, tip.urgent))
        return lines, speak

    def guides_summary(self) -> tuple[int, float | None, str]:
        from .sources.updater import guide_stats

        return guide_stats(self.config.guides.dir)

    def maybe_update_guides(self, force: bool = False) -> bool:
        """攻略库过期时后台更新；force=True 立即更新。"""
        from .sources.updater import start_update, update_due

        if self._guides_update_started:
            return False
        if not force and not update_due(self.config.guides.dir, self.config.guides.refresh_days):
            return False
        ok = start_update(self.config.root, self.config.log_dir / "guides_update.log")
        self._guides_update_started = ok
        if ok:
            self._print("攻略库需要更新，已在后台开始（日志 logs\\guides_update.log）")
        return ok

    def _speak_new(self, items: list[tuple[str, str, bool]]) -> None:
        """只朗读新出现的提示；符点这类时间敏感的提示用更明显的提示音。"""
        fresh = [(text, urgent, key) for key, text, urgent in items if key not in self._spoken]
        if not fresh:
            return
        for key, _, _ in items:
            self._spoken.add(key)
        text = "；".join(text for text, _, _ in fresh)
        urgent = any(urgent for _, urgent, _ in fresh)
        alert = any(key.startswith("fight:") for _, _, key in fresh)
        self.speaker.say(text, urgent=urgent, alert=alert)
        # 播报后 10 秒恢复完整透明度，之后自动变淡（尽量不挡视野）
        if self.overlay is not None and self.speaker.enabled:
            self.overlay.highlight(10.0)

    def _net_worth(self, snapshot) -> float:
        """总经济 ≈ 现金 + 已出装备价值（GSI 不给净经济，只能这样近似）。"""
        total = float(snapshot.gold or 0)
        for name in snapshot.item_names():
            cost = self.cost_by_name.get(name)
            if cost:
                total += float(cost)
        return total

    def _item_text(self, snapshot) -> str:
        """推荐装备：给出“为什么出”和“怎么用”。"""
        hero = self._self_hero()
        if snapshot is None or hero is None:
            return ""
        if not self.popularity:
            return "出装数据未就绪：先运行 scripts\\fetch_popularity.py"
        enemies = list(self.state.roster.enemies) if self.state.roster is not None else []
        build = self.guides.build_for(hero.short)
        advices = recommend(
            hero=hero,
            enemies=enemies,
            popularity=self.popularity,
            by_id=self.item_by_id,
            item_names=self.item_names,
            meta=self.hero_meta,
            owned=set(snapshot.item_names()),
            limit=1,
            guide_items=build.items if build is not None else (),
        )
        if not advices:
            return ""
        first = advices[0]
        sep = "：" if texts_language() == "zh-CN" else ": "
        dash = "——" if texts_language() == "zh-CN" else "—"
        lines = [f"{t('label_recommend')}{sep}{first.display} {dash} {first.why}"]
        if first.how:
            lines.append(f"{t('label_usage')}{sep}{first.how}")
        if build is not None and build.skill:
            lines.append(f"{t('label_skill')}{sep}{build.skill}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    def _keep_on_top(self) -> None:
        """有些游戏会抢置顶，定期把窗口重新顶到最前（不抢焦点）。"""
        if sys.platform != "win32" or self.overlay is None:
            return
        if time.monotonic() - self._last_topmost < 2.0:
            return
        self._last_topmost = time.monotonic()
        try:
            import ctypes

            # 卡片和头像下的名字条都要顶住，否则无边框全屏会把名字条压到游戏下面
            for window in (self.overlay, self.namestrip):
                if window is None:
                    continue
                hwnd = int(window.winId())
                # HWND_TOPMOST=-1, SWP_NOSIZE|SWP_NOMOVE|SWP_NOACTIVATE
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        except Exception:  # noqa: BLE001
            pass

    def _watch_resolution(self) -> None:
        """分辨率、窗口大小或 DPI 变了就重新定位顶部栏，否则名字会留在旧坐标。"""
        now = time.monotonic()
        if now - self._res_checked_at < 2.0:
            return
        self._res_checked_at = now
        from PyQt6.QtGui import QGuiApplication

        from .vision.capture import dota_window_rect

        rect = dota_window_rect()
        key = (rect.left, rect.top, rect.width, rect.height) if rect is not None else None
        try:
            ratio = float(QGuiApplication.primaryScreen().devicePixelRatio())
        except Exception:  # noqa: BLE001
            ratio = self._dpr
        if self._win_key is None and self._dpr == 0.0:
            self._win_key, self._dpr = key, ratio
            return
        if key != self._win_key or ratio != self._dpr:
            print(f"[识别] 分辨率/窗口变化：{self._win_key} -> {key}", file=sys.stderr)
            self._win_key, self._dpr = key, ratio
            if self._mode == "game":
                self._bar = None
                self._bar_tries = 0
                self._bar_refresh_at = now + 0.3
            self._last_render = None

    def _watch_focus(self) -> None:
        """切出游戏 5 秒后隐藏名字条；回到游戏焦点时再显示。"""
        from .vision.capture import dota_foreground

        now = time.monotonic()
        if dota_foreground():
            self._focus_lost_at = None
            if self._strip_hidden_by_focus:
                self._strip_hidden_by_focus = False
                print("[焦点] 回到游戏，恢复英雄名字")
                self._last_render = None  # 强制重画一次
                self._update_name_strip()
            return
        if self._focus_lost_at is None:
            self._focus_lost_at = now
            return
        if not self._strip_hidden_by_focus and now - self._focus_lost_at >= 5.0:
            if self.namestrip is not None:
                self.namestrip.hide()
            self._strip_hidden_by_focus = True
            print("[焦点] 已切出游戏 5 秒，隐藏英雄名字")

    def _minimap_region(self):
        from .vision.capture import Region, dota_window_rect

        if self._mm_rect is not None:
            return Region(
                self._mm_rect.left,
                self._mm_rect.top,
                self._mm_rect.width,
                self._mm_rect.height,
            )
        rect = dota_window_rect()
        if rect is None and self.capture is not None:
            rect = self.capture.monitor()
        if rect is None:
            return None
        left = rect.left + int(rect.width * MINIMAP_FRAC[0])
        top = rect.top + int(rect.height * MINIMAP_FRAC[1])
        width = int(rect.width * (MINIMAP_FRAC[2] - MINIMAP_FRAC[0]))
        height = int(rect.height * (MINIMAP_FRAC[3] - MINIMAP_FRAC[1]))
        mm = self.config.minimap
        if mm.side == "left":
            left = rect.left + int(rect.width * 0.002)
        scale = max(0.6, min(1.6, mm.size_percent / 100.0))
        width = max(1, int(width * scale))
        height = max(1, int(height * scale))
        left += int(mm.offset_x)
        top += int(mm.offset_y)
        if width < 40 or height < 40:
            return None
        return Region(left, top, width, height)

    def _auto_minimap(self) -> None:
        """多帧尝试自动定位小地图；失败就留空，走配置兜底。"""
        from .vision.capture import Region

        if self.capture is None:
            return
        frames = []
        for _ in range(5):
            try:
                frames.append(self.capture.grab())
            except Exception:
                break
        if not frames:
            return
        side = self.config.minimap.side
        sides = (side,) if side in ("left", "right") else ("right", "left")
        rect = locate_minimap(frames, sides=sides)
        if rect is None:
            return
        self._mm_rect = Region(rect.left, rect.top, rect.width, rect.height)
        self._mm_misses = 0
        print(
            f"[小地图] 自动定位：({rect.left}, {rect.top}) {rect.width}x{rect.height}"
        )

    def _scan_minimap(self) -> None:
        """20 分钟后每秒看一次小地图，更新团战/地图提示。"""
        if not self.assist.fight_alerts:
            self._fight_hints = []
            return
        snapshot = self.state.snapshot
        if self.capture is None or snapshot is None or not snapshot.in_match:
            self._fight_hints = []
            return
        clock = clock_time(snapshot)
        if clock < 10 * 60:
            self._fight_hints = []
            return
        now = time.monotonic()
        if now < self._mm_at:
            return
        self._mm_at = now + 1.0
        if self._mm_rect is None and self.config.minimap.side == "auto":
            self._auto_minimap()
        region = self._minimap_region()
        if region is None:
            return
        try:
            image = self.capture.grab(region)
        except Exception:  # noqa: BLE001
            return
        crop = crop_minimap(image)
        dots = detect_dots(crop)
        if dots.enemies:
            self._mm_misses = 0
        else:
            self._mm_misses += 1
            if self._mm_misses >= 45:
                self._mm_rect = None
                self._mm_misses = 0
                self._print("[小地图] 连续 45 秒没有红点，重新定位小地图")
        if not dots.enemies and clock >= 20 * 60 and not self._mm_debug_saved:
            # 只存一次，方便按你小地图的显示模式（图标/名字/头像）调阈值
            self._mm_debug_saved = True
            stamp = time.strftime("%Y%m%d-%H%M%S")
            path = self.config.log_dir / "screenshots" / f"minimap-{stamp}.png"
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                imwrite_path(path, crop)
                self._print("小地图没发现敌方红点，已存样本：" + str(path))
            except Exception:  # noqa: BLE001
                pass
        # 过滤长期不动的红点（塔/基地/UI），只留会动的英雄
        now_mono = time.monotonic()
        if self._mm_static is None:
            self._mm_static = StaticFilter()
            self._mm_since = now_mono
        dots = MinimapDots(
            enemies=self._mm_static.update(dots.enemies, now_mono),
            allies=dots.allies,
            self_pos=dots.self_pos,
            creeps=dots.creeps,
        )
        if self._mm_since is not None and now_mono - self._mm_since < 15.0:
            # 前 15 秒先让“静止点”过滤器认识塔的位置，避免开局误报“红点全消失”
            return
        roles: set[str] = set()
        self_hero = self._self_hero()
        if self_hero is not None:
            info = self.hero_meta.get(self_hero.hero_id)
            if info is not None:
                roles = set(info.roles or ())
        faction = str((snapshot.player or {}).get("team_name") or "radiant").lower()
        guide_texts: list[str] = []
        if self_hero is not None and not self.guides.empty:
            guide_texts = [tip.text for tip in self.guides.tips_for(self_hero.short, "任意", "任意", limit=3)]
        self._fight_hints = self._fight.update(
            clock=clock,
            dots=dots,
            roster=self.state.roster,
            meta=self.hero_meta,
            roles=roles,
            side=faction,
            health_percent=snapshot.health_percent,
            self_hero=self_hero,
            guide_tips=guide_texts,
        )

    def _tick(self) -> None:
        self._keep_on_top()
        self._watch_resolution()
        self._watch_focus()
        self._scan_minimap()
        if self.snapshot_path is None and self.state.snapshot is not None:
            # 游戏关掉后 GSI 不再来包：30 秒没新数据就当回到主界面，别把卡片留在桌面上
            if time.monotonic() - self._last_payload > 30.0:
                self.state.snapshot = None
                self._mode = "idle"
                self._last_render = None
        if self._capture_at is not None and time.monotonic() >= self._capture_at:
            self._capture_at = None
            self._start_capture()
        if self._bar_refresh_at is not None and time.monotonic() >= self._bar_refresh_at:
            self._bar_refresh_at = None
            self._refresh_bar()
        self._track_match(self.state.snapshot)
        if self._hud_at is not None and time.monotonic() >= self._hud_at:
            self._hud_at = None
            if self._mode == "game" and self.state.roster is None:
                self._hud_tries += 1
                if not self._capture_hud_roster() and self._hud_tries < MAX_HUD_TRIES:
                    self._hud_at = time.monotonic() + 3.0
        if (
            self._mode == "game"
            and self._bar is None
            and not self._bar_failed
            and self._bar_refresh_at is None
            and self.state.roster is not None
            and self.state.roster.complete
        ):
            # 名字条空着且没在重试（例如刚从菜单回来）——补一次定位
            self._bar_refresh_at = time.monotonic() + 0.5
        self._render()

    def _start_capture(self) -> None:
        """先隐藏卡片和名字条再截屏：它们会盖住顶部栏/面板，干扰识别。"""
        if self.overlay is not None:
            self.overlay.hide()
        self._strip_was_visible = bool(self.namestrip is not None and self.namestrip.isVisible())
        if self.namestrip is not None:
            self.namestrip.hide()
        QTimer.singleShot(120, self._capture_and_restore)

    def _capture_and_restore(self) -> None:
        try:
            self._capture_roster()
        finally:
            if self.overlay is not None:
                self.overlay.show()
            if self.namestrip is not None and self._strip_was_visible:
                self.namestrip.show()
            if self.state.roster is None or not self.state.roster.complete:
                if self._capture_attempts < MAX_CAPTURE_ATTEMPTS:
                    self._capture_at = time.monotonic() + CAPTURE_DELAY_S

    def _refresh_bar(self) -> None:
        """进游戏后重新检测顶部栏：HUD 的卡面比决策界面小，沿用旧坐标会错位。"""
        if self.capture is None:
            return
        self._refresh_strip_was_visible = bool(self.namestrip is not None and self.namestrip.isVisible())
        if self.overlay is not None:
            self.overlay.hide()
        if self.namestrip is not None:
            self.namestrip.hide()
        QTimer.singleShot(120, self._do_refresh_bar)

    def _do_refresh_bar(self) -> None:
        ok = False
        try:
            ok = self._detect_bar()
        finally:
            if self.overlay is not None:
                self.overlay.show()
            if self.namestrip is not None and self._refresh_strip_was_visible:
                self.namestrip.show()
            if ok:
                self._bar_tries = 0
            elif self._bar_tries < MAX_BAR_TRIES:
                self._bar_tries += 1
                self._bar_refresh_at = time.monotonic() + 1.5
            else:
                # 反复定位失败就别用旧坐标画错位的名字了
                self._bar = None
                self._bar_failed = True
            self._update_name_strip()

    def _detect_bar(self) -> bool:
        """重新定位顶部栏。先找游戏窗口，失败再抓整屏；两条路都用已知英雄反查。"""
        if self.capture is None:
            return False
        from .vision.heroes import detect_topbar_cells

        roster = self.state.roster
        heroes = list(roster.allies) + list(roster.enemies) if (roster and roster.complete) else []
        attempts: list[tuple[object, object]] = []
        try:
            attempts.append((self.capture.grab(), self.capture.last_region))
        except Exception:  # noqa: BLE001
            pass
        try:
            monitor = self.capture.monitor()
            attempts.append((self.capture.grab(monitor), monitor))
        except Exception:  # noqa: BLE001
            pass
        last_image = None
        for image, region in attempts:
            image = ensure_min_size(image, 1200)
            last_image = image
            boxes: list | None = None
            # 游戏内顶部栏压在 3D 画面上，颜色检测不可靠；优先用已知的 10 个英雄反查位置
            if heroes and self.matcher is not None:
                located = self.matcher.locate_bar(image, heroes)
                if sum(1 for box in located if box) >= 8:
                    boxes = located
            if not boxes:
                boxes = detect_topbar_cells(image)
            if not boxes:
                continue
            factor = image.shape[1] / region.width if region else 1.0
            self._bar = (region, boxes, factor)
            found = sum(1 for box in boxes if box)
            print(f"[识别] 顶部栏重新定位：{found} 格")
            self._save_bar_debug(image, boxes)
            return True
        print("[识别] 进游戏后没找到顶部栏，名字条暂不显示", file=sys.stderr)
        if last_image is not None:
            try:
                from .vision.heroes import imwrite_path

                target = self.config.log_dir / "screenshots" / "bar-locate-failed.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                imwrite_path(target, last_image)
                print(f"[识别] 已保存定位失败截图：{target}", file=sys.stderr)
            except Exception:  # noqa: BLE001
                pass
        return False

    def _save_bar_debug(self, image, boxes: list) -> None:
        """把定位结果画到图上，方便用户/我核对坐标。"""
        try:
            from .vision.heroes import imwrite_path

            debug = image.copy()
            for index, box in enumerate(boxes):
                if not box:
                    continue
                x, y, w, h = (int(v) for v in box)
                color = (0, 220, 0) if index < 5 else (0, 0, 220)
                debug[max(0, y - 1): y + h + 1, max(0, x - 1): x + 1] = color
                debug[max(0, y - 1): y + h + 1, x + w - 1: x + w + 1] = color
                debug[max(0, y - 1): y + 1, max(0, x - 1): x + w + 1] = color
                debug[y + h - 1: y + h + 1, max(0, x - 1): x + w + 1] = color
            target = self.config.log_dir / "screenshots" / "bar-locate.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            imwrite_path(target, debug)
        except Exception:  # noqa: BLE001
            pass

    def _shutdown(self) -> None:
        if self.server is not None:
            self.server.stop()
            self.server = None
        if self.capture is not None:
            self.capture.close()
            self.capture = None

    def _window_text(self) -> str:
        from .vision.capture import dota_window_rect

        rect = dota_window_rect()
        if rect is None:
            return "未找到（按整屏处理；独占全屏时正常）"
        return f"({rect.left}, {rect.top}, {rect.width}, {rect.height})"

    def _log_startup(self, area) -> None:
        """把启动信息写进 logs/coach.log：控制台被关掉时也能排查。"""
        try:
            self.config.log_dir.mkdir(parents=True, exist_ok=True)
            rect = self.overlay.geometry().getRect() if self.overlay is not None else None
            with (self.config.log_dir / "coach.log").open("a", encoding="utf-8") as handle:
                handle.write(
                    f"[{datetime.now():%Y-%m-%d %H:%M:%S}] start screen={area.size() if area else None} "
                    f"card={rect} click_through={self.config.overlay.click_through} "
                    f"templates={len(self.matcher.cards) if self.matcher else 0} "
                    f"data={self.config.data_dir}\n"
                )
        except OSError:
            pass

    # ------------------------------------------------------------------
    # 生命周期：命令行与面板共用
    # ------------------------------------------------------------------
    def attach(self, qt_app: QApplication | None = None) -> None:
        """创建卡片、名字条、截屏与定时器；不启动 GSI、不进入事件循环。"""
        if self._attached:
            return
        self.overlay = OverlayWindow(
            self.config.overlay.opacity,
            self.config.overlay.click_through,
            self.config.overlay.dim_opacity,
        )
        self.namestrip = NameStrip()
        screen = QApplication.primaryScreen()
        area = screen.availableGeometry() if screen is not None else None
        if area is not None:
            self.overlay.move(area.right() - self.overlay.width() - 24, area.top() + 96)
        self.overlay.show()
        print(f"卡片已显示：{self.overlay.geometry().getRect()}  点击穿透={self.config.overlay.click_through}")
        print(f"攻略库：{len(self.guides.tips)} 条（patch={self.guides.patch or '无'}）")
        print(f"游戏窗口：{self._window_text()}")
        self._log_startup(area)

        if self.snapshot_path is not None:
            try:
                raw = json.loads(self.snapshot_path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as exc:
                print(f"读不到快照：{self.snapshot_path}（{exc}）", file=sys.stderr)
            else:
                if isinstance(raw, dict):
                    from .gsi.models import Snapshot

                    self.state.snapshot = Snapshot(raw)
                    self._mode = "game"
                    print(
                        f"快照已载入：in_game={self.state.snapshot.is_in_game} "
                        f"状态={self.state.snapshot.game_state}"
                    )

        if self.screenshot is not None:
            image = imread_path(self.screenshot)
            if image is None:
                print(f"读不到截图：{self.screenshot}", file=sys.stderr)
            else:
                roster, bar = self._identify(
                    image, self._self_hero(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                self.state.roster = roster
                self._bar = (None, bar, 1.0) if bar else None
                allies, enemies = self.state.roster.names()
                print(
                    f"[截图识别] 来源={self.state.roster.source} "
                    f"我方 {'、'.join(allies)} | 敌方 {'、'.join(enemies)}"
                )
        else:
            self.capture = ScreenCapture(monitor=1)

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(250)
        self._attached = True

    def start(self) -> bool:
        """启动 GSI 监听与卡片；端口被占时返回 False。"""
        if not self._attached:
            self.attach()
        if self.snapshot_path is None and self.server is None:
            if _port_busy(self.config.gsi.host, self.config.gsi.port):
                print(
                    "检测到已有实例在运行（端口被占用）：两个窗口的卡片会互相遮挡，"
                    "识别也会互相干扰。请先关掉旧的教练窗口。",
                    file=sys.stderr,
                )
                return False
            self.server = GsiServer(self.config.gsi.host, self.config.gsi.port, self._on_snapshot)
            self.server.start()
            print(f"GSI 监听：{self.server.url}")
        if self.overlay is not None and self.config.overlay.enabled:
            self.overlay.show()
            if self.panel_mode and not (self.state.snapshot and self.state.snapshot.in_match):
                self.overlay.hide()
        if self._timer is not None:
            self._timer.start(250)
        return True

    def stop(self) -> None:
        """停止监听并隐藏卡片（面板点“停止”时调用）。"""
        if self.server is not None:
            self.server.stop()
            self.server = None
        if self._timer is not None:
            self._timer.stop()
        if self.overlay is not None:
            self.overlay.hide()
        if self.namestrip is not None:
            self.namestrip.hide()

    @property
    def running(self) -> bool:
        return bool(self.server and self.server.is_running)

    ROLE_ZH = {
        "Carry": "核心",
        "Support": "辅助",
        "Nuker": "爆发",
        "Disabler": "控制",
        "Initiator": "先手",
        "Durable": "肉盾",
        "Escape": "机动",
        "Pusher": "推塔",
        "Jungler": "打野",
    }

    def _traits(self, hero) -> str:
        """英雄总体特点（来自 OpenDota 角色标签），最多显示 3 个。"""
        if hero is None:
            return ""
        info = (self.hero_meta or {}).get(hero.hero_id)
        if info is None:
            return ""
        names = [self.ROLE_ZH[role] for role in info.roles if role in self.ROLE_ZH]
        return " · ".join(names[:3])

    def _team_status(self, group) -> list[dict]:
        out: list[dict] = []
        for hero in group or ():
            out.append(
                {
                    "short": hero.short if hero else "",
                    "name": hero.name_loc if hero else "?",
                    "hero_id": hero.hero_id if hero else 0,
                    "known": hero is not None,
                    "traits": self._traits(hero),
                }
            )
        return out

    def status(self) -> dict:
        """给主窗口用的只读状态快照（500ms 轮询）。"""
        snapshot = self.state.snapshot
        roster = self.state.roster
        clock = self.state.clock
        self_hero = self._self_hero()
        return {
            "attached": self._attached,
            "running": self.running,
            "gsi_up": self.running,
            "mode": self._mode,
            "in_match": bool(snapshot and snapshot.in_match),
            "game_state": (snapshot.game_state if snapshot else "") or "",
            "match_id": str(snapshot.match_id or "") if snapshot else "",
            "clock": clock,
            "clock_text": format_clock(clock),
            "phase": phase_for(clock),
            "hero_name": self_hero.name_loc if self_hero else "",
            "hero_short": self_hero.short if self_hero else "",
            "known": roster.known if roster else 0,
            "allies": self._team_status(roster.allies if roster else ()),
            "enemies": self._enemy_status(roster.enemies if roster else ()),
            "threat_counts": threat_summary(
                list(roster.enemies) if roster else [], self.hero_meta
            ),
            "summary": self._summary_status(),
            "title": self._last_title,
            "build": self._last_build_text,
            "hints": list(self._last_hint_parts[-3:]),
        }

    def _enemy_status(self, group) -> list[dict]:
        """敌方 5 人 + 每人的威胁标签（先手/爆发/隐身）。"""
        rows = self._team_status(group)
        for row, hero in zip(rows, group or ()):
            row["threats"] = threat_labels(hero, self.hero_meta)
        return rows

    def _summary_status(self) -> dict | None:
        """赛后复盘数据；不在复盘状态时返回 None。"""
        summary = self._last_summary
        if self._mode != "summary" or summary is None:
            return None
        return {
            "result": summary.result,
            "hero": summary.hero,
            "kda": f"{summary.kills}/{summary.deaths}/{summary.assists}",
            "cs": f"{summary.last_hits}/{summary.denies}",
            "gpm": summary.gpm,
            "duration": format_clock(summary.duration),
            "lines": summary_lines(summary),
            "hint": self._summary_hint
            or encourage(summary, bool(improvements(summary))),
        }

    def apply_settings(self, config: Config) -> list[str]:
        """热应用设置；返回需要重启才能生效的项目。"""
        restart: list[str] = []
        old_port = self.config.gsi.port
        self.config = config
        self.assist = config.assist
        if self.overlay is not None:
            self.overlay.set_opacities(
                config.overlay.opacity, config.overlay.dim_opacity
            )
            self.overlay.set_click_through(config.overlay.click_through)
            self.overlay.setVisible(config.overlay.enabled)
        if self.namestrip is not None:
            if not config.assist.name_strip:
                self.namestrip.hide()
            else:
                self._update_name_strip()
        # 语音重建（SAPI/edge 初始化较慢，但保存设置时不频繁）
        try:
            pack = voices.effective_pack(config.voice.pack, config.app.language)
            edge_voice, rate, volume = voices.resolve(
                pack,
                config.voice.edge_voice,
                config.voice.rate,
                config.voice.volume,
            )
            self.speaker = Speaker(
                enabled=config.voice.enabled,
                speak=config.voice.speak,
                backend=config.voice.backend,
                edge_voice=edge_voice,
                rate=rate,
                volume=volume,
                min_interval=config.voice.min_interval,
                beep=config.voice.beep,
            gate=self._audio_gate,
            wait_max=config.voice.wait_max,
                log_path=config.log_dir / "voice.log",
            )
        except Exception as exc:  # noqa: BLE001 - 语音失败不该让保存失败
            restart.append(f"语音（{exc}）")
        if config.gsi.port != old_port:
            restart.append("GSI 端口")
        if self._attached:
            self._log_startup(None)
        return restart

    def run(self) -> int:
        if self.snapshot_path is None and _port_busy(self.config.gsi.host, self.config.gsi.port):
            print(
                "检测到已有实例在运行（31982 端口被占用）：两个窗口的卡片会互相遮挡，"
                "识别也会互相干扰。\n请先在任务栏关掉旧的“Dota2 Coach”控制台窗口，再启动。",
                file=sys.stderr,
            )
            return 3
        app = QApplication([sys.argv[0] or "dota2coach"])
        self.attach(app)
        if not self.start():
            return 3

        if self.seconds is not None:
            QTimer.singleShot(int(self.seconds * 1000), app.quit)
        if self.save_overlay is not None:
            def save_and_quit() -> None:
                assert self.overlay is not None
                self.save_overlay.parent.mkdir(parents=True, exist_ok=True)
                self.overlay.grab().save(str(self.save_overlay))
                print(f"界面已保存：{self.save_overlay}")
                app.quit()

            QTimer.singleShot(900, save_and_quit)

        try:
            app.aboutToQuit.connect(self._shutdown)
            return app.exec()
        finally:
            self._shutdown()
