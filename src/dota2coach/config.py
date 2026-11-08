"""从 config.toml / .env 读取配置，并支持写回（面板设置页用）。"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parents[2]
)

DEFAULT_DOTA_PATH = Path(r"D:\SteamLibrary\steamapps\common\dota 2 beta")
DEFAULT_STEAM_PATH = Path(r"C:\Program Files (x86)\Steam")


def _fallback_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Dota2Coach"


def _is_writable(path: Path) -> bool:
    """探测目录是否可写（安装到 Program Files 时会失败，需要回退）。"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def app_root(root: Path | None = None) -> tuple[Path, Path]:
    """返回 (安装根目录, 可写目录)。不可写时把配置/日志放到 %LOCALAPPDATA%。"""
    base = (root or PROJECT_ROOT).resolve()
    if _is_writable(base):
        return base, base
    fallback = _fallback_root()
    try:
        fallback.mkdir(parents=True, exist_ok=True)
    except OSError:
        return base, base
    return base, fallback



def load_dotenv(path: Path) -> None:
    """极简 .env 读取：KEY=VALUE，忽略 # 注释，不覆盖已存在的环境变量。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _path(value: Any, root: Path, default: Path) -> Path:
    if value is None:
        return default
    p = Path(str(value)).expanduser()
    return p if p.is_absolute() else (root / p).resolve()


@dataclass
class AppConfig:
    language: str = "zh-CN"
    data_dir: Path = Path("data")
    log_dir: Path = Path("logs")


@dataclass
class GsiConfig:
    host: str = "127.0.0.1"
    port: int = 31982
    log_raw: bool = True
    min_log_interval: float = 0.2


@dataclass
class GameConfig:
    dota_path: Path = field(default_factory=lambda: DEFAULT_DOTA_PATH)
    steam_path: Path = field(default_factory=lambda: DEFAULT_STEAM_PATH)


@dataclass
class OverlayConfig:
    enabled: bool = True
    opacity: float = 0.9  # 清晰状态（语音播报后 10 秒内）
    dim_opacity: float = 0.45  # 模糊状态（平时）
    click_through: bool = True


@dataclass
class ThemeConfig:
    wallpaper: str = ""  # 主界面背景图（空 = 默认浅色）
    wallpaper_dim: float = 0.55  # 白色蒙层强度，保证文字可读


@dataclass
class VoiceConfig:
    enabled: bool = True
    speak: bool = True
    backend: str = "auto"  # auto / sapi / edge / beep
    edge_voice: str = "zh-CN-XiaoxiaoNeural"
    rate: int = 0
    volume: int = 100
    min_interval: float = 8.0
    beep: bool = True
    pack: str = "xiaoxiao"  # 语音包 id，见 ui/voices.py
    wait_game_voice: bool = True  # 游戏正在出声时等它说完
    wait_max: float = 4.0


@dataclass
class LlmConfig:
    enabled: bool = False
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com/v1"


@dataclass
class VisionConfig:
    icons_dir: Path = Path("data/hero_icons")
    cards_dir: Path = Path("data/hero_cards")
    heroes_json: Path = Path("data/heroes.json")
    match_min_score: float = 0.55
    match_min_gap: float = 0.02


@dataclass
class GuidesConfig:
    enabled: bool = True
    dir: Path = Path("data/guides")
    max_tips: int = 12
    refresh_days: int = 7
    asr: str = "off"  # off / base / small
    asr_max_videos: int = 3


@dataclass
class YouTubeConfig:
    """YouTube 攻略源（需要能访问 YouTube 的网络或代理）。"""

    enabled: bool = False
    proxy: str = ""
    languages: tuple[str, ...] = ("en",)
    min_views: int = 5000


@dataclass
class MinimapConfig:
    """小地图位置/大小：自动定位失败时用这里的值兜底。"""

    side: str = "auto"  # auto / left / right
    size_percent: int = 100
    offset_x: int = 0
    offset_y: int = 0


@dataclass
class AssistConfig:
    """辅助开关：设置页“辅助功能”。"""

    rune_alerts: bool = True  # 刷新播报（符/莲花/神龛）
    name_strip: bool = True  # 头像下英雄名字
    fight_alerts: bool = True  # 团战 / 小地图预警
    lane_alerts: bool = True  # 对线期提醒


@dataclass
class HotkeyConfig:
    """全局快捷键（F1–F12）。"""

    toggle_card: str = "F8"  # 显示 / 隐藏教练卡片
    test_voice: str = "F9"  # 试听语音


@dataclass(frozen=True)
class Config:
    root: Path
    app: AppConfig
    gsi: GsiConfig
    game: GameConfig
    overlay: OverlayConfig
    llm: LlmConfig
    vision: VisionConfig
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    guides: GuidesConfig = field(default_factory=GuidesConfig)
    minimap: MinimapConfig = field(default_factory=MinimapConfig)
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)
    assist: AssistConfig = field(default_factory=AssistConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    raw: dict[str, Any] = field(default_factory=dict)
    writable_root: Path = field(default_factory=lambda: Path("."))
    config_path: Path = field(default_factory=lambda: Path("config.toml"))

    @property
    def log_dir(self) -> Path:
        return self.app.log_dir

    @property
    def data_dir(self) -> Path:
        return self.app.data_dir

    @property
    def gsi_cfg_dir(self) -> Path:
        """Dota 2 读取 GSI 配置的目录。"""
        return self.game.dota_path / "game" / "dota" / "cfg" / "gamestate_integration"

    def ensure_dirs(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


def load_config(path: Path | None = None, root: Path | None = None) -> Config:
    root = (root or PROJECT_ROOT).resolve()
    base, writable = app_root(root)
    root = base
    if path:
        cfg_path = Path(path).expanduser()
        if not cfg_path.is_absolute():
            cfg_path = (root / cfg_path).resolve()
    else:
        cfg_path = root / "config.toml"
        if not cfg_path.exists() and (writable / "config.toml").exists():
            cfg_path = writable / "config.toml"

    raw: dict[str, Any] = {}
    read_path = cfg_path
    if not read_path.exists():
        # 源码分发只带 config.example.toml，先把示例当默认值读入；
        # config_path 仍指向可写的 config.toml，设置页保存时不会覆盖示例。
        example = root / "config.example.toml"
        if example.exists():
            read_path = example
    if read_path.exists():
        with read_path.open("rb") as fh:
            raw = tomllib.load(fh)

    load_dotenv(root / ".env")
    if writable != root:
        load_dotenv(writable / ".env")

    data_default = root / "data"
    if not data_default.exists():
        data_default = writable / "data"

    app_raw = raw.get("app") or {}
    gsi_raw = raw.get("gsi") or {}
    game_raw = raw.get("game") or {}
    overlay_raw = raw.get("overlay") or {}
    llm_raw = raw.get("llm") or {}
    vision_raw = raw.get("vision") or {}
    voice_raw = raw.get("voice") or {}
    theme_raw = raw.get("theme") or {}
    guides_raw = raw.get("guides") or {}
    mm = raw.get("minimap") or {}
    youtube_raw = raw.get("youtube") or {}
    assist_raw = raw.get("assist") or {}

    app = AppConfig(
        language=str(app_raw.get("language", "zh-CN")),
        data_dir=_path(app_raw.get("data_dir"), root, data_default),
        log_dir=_path(app_raw.get("log_dir"), root, writable / "logs"),
    )
    gsi = GsiConfig(
        host=str(gsi_raw.get("host", "127.0.0.1")),
        port=int(gsi_raw.get("port", 31982)),
        log_raw=bool(gsi_raw.get("log_raw", True)),
        min_log_interval=float(gsi_raw.get("min_log_interval", 0.2)),
    )
    game = GameConfig(
        dota_path=_path(game_raw.get("dota_path"), root, DEFAULT_DOTA_PATH),
        steam_path=_path(game_raw.get("steam_path"), root, DEFAULT_STEAM_PATH),
    )
    overlay = OverlayConfig(
        enabled=bool(overlay_raw.get("enabled", True)),
        opacity=float(overlay_raw.get("opacity", 0.9)),
        dim_opacity=float(overlay_raw.get("dim_opacity", 0.45)),
        click_through=bool(overlay_raw.get("click_through", True)),
    )
    llm = LlmConfig(
        enabled=bool(llm_raw.get("enabled", False)),
        model=str(llm_raw.get("model", "deepseek-chat")),
        base_url=str(llm_raw.get("base_url", "https://api.deepseek.com/v1")),
    )
    vision = VisionConfig(
        icons_dir=_path(vision_raw.get("icons_dir"), root, data_default / "hero_icons"),
        cards_dir=_path(vision_raw.get("cards_dir"), root, data_default / "hero_cards"),
        heroes_json=_path(vision_raw.get("heroes_json"), root, data_default / "heroes.json"),
        match_min_score=float(vision_raw.get("match_min_score", 0.55)),
        match_min_gap=float(vision_raw.get("match_min_gap", 0.02)),
    )
    voice = VoiceConfig(
        enabled=bool(voice_raw.get("enabled", True)),
        speak=bool(voice_raw.get("speak", True)),
        backend=str(voice_raw.get("backend", "auto")),
        edge_voice=str(voice_raw.get("edge_voice", "zh-CN-XiaoxiaoNeural")),
        rate=int(voice_raw.get("rate", 0)),
        volume=int(voice_raw.get("volume", 100)),
        min_interval=float(voice_raw.get("min_interval", 8.0)),
        beep=bool(voice_raw.get("beep", True)),
        pack=str(voice_raw.get("pack", "xiaoxiao")),
        wait_game_voice=bool(voice_raw.get("wait_game_voice", True)),
        wait_max=float(voice_raw.get("wait_max", 4.0)),
    )
    theme = ThemeConfig(
        wallpaper=str(theme_raw.get("wallpaper", "")),
        wallpaper_dim=float(theme_raw.get("wallpaper_dim", 0.55)),
    )
    guides = GuidesConfig(
        enabled=bool(guides_raw.get("enabled", True)),
        dir=_path(guides_raw.get("dir"), root, data_default / "guides"),
        max_tips=int(guides_raw.get("max_tips", 12)),
        refresh_days=int(guides_raw.get("refresh_days", 7)),
        asr=str(guides_raw.get("asr", "off")),
        asr_max_videos=int(guides_raw.get("asr_max_videos", 3)),
    )
    youtube = YouTubeConfig(
        enabled=bool(youtube_raw.get("enabled", False)),
        proxy=str(youtube_raw.get("proxy", "")),
        languages=tuple(youtube_raw.get("languages") or ("en",)),
        min_views=int(youtube_raw.get("min_views", 5000)),
    )
    assist = AssistConfig(
        rune_alerts=bool(assist_raw.get("rune_alerts", True)),
        name_strip=bool(assist_raw.get("name_strip", True)),
        fight_alerts=bool(assist_raw.get("fight_alerts", True)),
        lane_alerts=bool(assist_raw.get("lane_alerts", True)),
    )
    hotkey_raw = raw.get("hotkeys") or {}
    hotkeys = HotkeyConfig(
        toggle_card=str(hotkey_raw.get("toggle_card", "F8")).upper(),
        test_voice=str(hotkey_raw.get("test_voice", "F9")).upper(),
    )
    return Config(
        root=root,
        app=app,
        gsi=gsi,
        game=game,
        overlay=overlay,
        llm=llm,
        vision=vision,
        voice=voice,
        theme=theme,
        guides=guides,
        youtube=youtube,
        assist=assist,
        hotkeys=hotkeys,
        raw=raw,
        writable_root=writable,
        config_path=cfg_path,
    )


# ---------- 写回 ----------


def _quote(value: str) -> str:
    """TOML 字符串：Windows 路径优先用单引号字面量，避免反斜杠转义。"""
    if "'" not in value and "\\" in value:
        return f"'{value}'"
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    return _quote(str(value))


def _fmt_path(path: Path, root: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
        return rel.as_posix()
    except (ValueError, OSError):
        return str(path)


def render_config_toml(cfg: Config) -> str:
    """生成带注释的 config.toml；路径尽量写成相对安装目录。"""
    root = cfg.root
    lines = [
        "# dota2-coach 配置（由设置界面自动生成，可手动改）",
        "# 字符串用单引号时反斜杠不会被转义（Windows 路径推荐这样写）",
        "",
        "[app]",
        f"language = {_toml_value(cfg.app.language)}",
        f"data_dir = {_toml_value(_fmt_path(cfg.app.data_dir, root))}",
        f"log_dir = {_toml_value(_fmt_path(cfg.log_dir, root))}",
        "",
        "[gsi]",
        f"host = {_toml_value(cfg.gsi.host)}",
        f"port = {_toml_value(cfg.gsi.port)}",
        "# 把原始报文写进 logs/gsi_raw/<matchid>-<session>.jsonl，用于离线回放与排错",
        f"log_raw = {_toml_value(cfg.gsi.log_raw)}",
        f"min_log_interval = {_toml_value(cfg.gsi.min_log_interval)}",
        "",
        "[game]",
        f"dota_path = {_toml_value(str(cfg.game.dota_path))}",
        f"steam_path = {_toml_value(str(cfg.game.steam_path))}",
        "",
        "[overlay]",
        f"enabled = {_toml_value(cfg.overlay.enabled)}",
        "# 清晰状态：语音播报后 10 秒内的不透明度",
        f"opacity = {_toml_value(cfg.overlay.opacity)}",
        "# 模糊状态：平时的不透明度",
        f"dim_opacity = {_toml_value(cfg.overlay.dim_opacity)}",
        "# 点击穿透：卡片不挡鼠标；想拖动卡片就改成 false",
        f"click_through = {_toml_value(cfg.overlay.click_through)}",
        "",
        "[hotkeys]",
        "# 全局快捷键，只支持 F1–F12",
        f"toggle_card = {_toml_value(cfg.hotkeys.toggle_card)}",
        f"test_voice = {_toml_value(cfg.hotkeys.test_voice)}",
        "",
        "[theme]",
        "# 主界面背景图：绝对路径，或相对程序目录的路径；留空使用默认浅色",
        f"wallpaper = {_toml_value(cfg.theme.wallpaper)}",
        f"wallpaper_dim = {_toml_value(cfg.theme.wallpaper_dim)}",
        "",
        "[llm]",
        "# 没有 DeepSeek key 时保持 false，全部走本地模板",
        f"enabled = {_toml_value(cfg.llm.enabled)}",
        f"model = {_toml_value(cfg.llm.model)}",
        f"base_url = {_toml_value(cfg.llm.base_url)}",
        "",
        "[vision]",
        f"icons_dir = {_toml_value(_fmt_path(cfg.vision.icons_dir, root))}",
        f"cards_dir = {_toml_value(_fmt_path(cfg.vision.cards_dir, root))}",
        f"heroes_json = {_toml_value(_fmt_path(cfg.vision.heroes_json, root))}",
        f"match_min_score = {_toml_value(cfg.vision.match_min_score)}",
        f"match_min_gap = {_toml_value(cfg.vision.match_min_gap)}",
        "",
        "[voice]",
        "# auto = 先试系统 SAPI，失败再用在线 edge-tts；也可强制 sapi / edge / beep",
        f"backend = {_toml_value(cfg.voice.backend)}",
        f"edge_voice = {_toml_value(cfg.voice.edge_voice)}",
        f"enabled = {_toml_value(cfg.voice.enabled)}",
        f"speak = {_toml_value(cfg.voice.speak)}",
        f"rate = {_toml_value(cfg.voice.rate)}",
        f"volume = {_toml_value(cfg.voice.volume)}",
        f"min_interval = {_toml_value(cfg.voice.min_interval)}",
        f"beep = {_toml_value(cfg.voice.beep)}",
        f"pack = {_toml_value(cfg.voice.pack)}",
        "# 游戏正在出声时，等它说完再朗读（最多等 wait_max 秒）",
        f"wait_game_voice = {_toml_value(cfg.voice.wait_game_voice)}",
        f"wait_max = {_toml_value(cfg.voice.wait_max)}",
        "",
        "[youtube]",
        f"enabled = {_toml_value(cfg.youtube.enabled)}",
        f"proxy = {_toml_value(cfg.youtube.proxy)}",
        f"languages = {_toml_value(list(cfg.youtube.languages))}",
        f"min_views = {_toml_value(cfg.youtube.min_views)}",
        "",
        "[guides]",
        f"enabled = {_toml_value(cfg.guides.enabled)}",
        f"dir = {_toml_value(_fmt_path(cfg.guides.dir, root))}",
        f"max_tips = {_toml_value(cfg.guides.max_tips)}",
        f"refresh_days = {_toml_value(cfg.guides.refresh_days)}",
        f'asr = {_toml_value(cfg.guides.asr)}',
        f"asr_max_videos = {_toml_value(cfg.guides.asr_max_videos)}",
        "",
        "[assist]",
        "# 辅助功能开关（设置页可改）",
        f"rune_alerts = {_toml_value(cfg.assist.rune_alerts)}",
        f"name_strip = {_toml_value(cfg.assist.name_strip)}",
        f"fight_alerts = {_toml_value(cfg.assist.fight_alerts)}",
        f"lane_alerts = {_toml_value(cfg.assist.lane_alerts)}",
        "",
    ]
    return "\n".join(lines)


def _validate_minimap(cfg: Config) -> list[str]:
    problems: list[str] = []
    mm = cfg.minimap
    if mm.side not in {"auto", "left", "right"}:
        problems.append("小地图位置只能是 auto/left/right")
    if not 60 <= int(mm.size_percent) <= 160:
        problems.append("小地图大小需在 60%–160% 之间")
    if abs(int(mm.offset_x)) > 300 or abs(int(mm.offset_y)) > 300:
        problems.append("小地图偏移需在 ±300 像素内")
    return problems


def validate_config(cfg: Config) -> list[str]:
    """返回错误列表；空列表表示可以保存。"""
    errors: list[str] = []
    if not (1 <= cfg.gsi.port <= 65535):
        errors.append("GSI 端口必须在 1–65535 之间")
    if not (0.2 <= cfg.overlay.opacity <= 1.0):
        errors.append("清晰状态透明度必须在 0.2–1.0 之间")
    if not (0.2 <= cfg.overlay.dim_opacity <= 1.0):
        errors.append("模糊状态透明度必须在 0.2–1.0 之间")
    if cfg.overlay.dim_opacity > cfg.overlay.opacity:
        errors.append("模糊状态不能比清晰状态更不透明")
    for name, value in (
        ("呼出卡片", cfg.hotkeys.toggle_card),
        ("试听语音", cfg.hotkeys.test_voice),
    ):
        if not re.fullmatch(r"F([1-9]|1[0-2])", value or ""):
            errors.append(f"{name}快捷键必须是 F1–F12")
    if cfg.hotkeys.toggle_card == cfg.hotkeys.test_voice:
        errors.append("两个快捷键不能相同")
    if cfg.voice.backend not in {"auto", "sapi", "edge", "beep"}:
        errors.append("语音后端只能是 auto/sapi/edge/beep")
    if not (-10 <= cfg.voice.rate <= 10):
        errors.append("语速必须在 -10–10 之间")
    if not (0 <= cfg.voice.volume <= 100):
        errors.append("音量必须在 0–100 之间")
    if not (0 <= cfg.voice.min_interval <= 60):
        errors.append("语音间隔必须在 0–60 秒之间")
    if not (0.0 <= cfg.vision.match_min_score <= 1.0):
        errors.append("识别阈值必须在 0–1 之间")
    if cfg.guides.asr not in {"off", "base", "small"}:
        errors.append("转写模型只能是 off/base/small")
    if not cfg.game.dota_path:
        errors.append("Dota 2 路径不能为空")
    errors.extend(_validate_minimap(cfg))
    return errors


def save_config(cfg: Config, path: Path | None = None) -> Path:
    """原子写回 config.toml（写前备份 .bak）。返回实际路径。"""
    errors = validate_config(cfg)
    if errors:
        raise ValueError("；".join(errors))
    target = Path(path) if path else Path(cfg.config_path)
    if not target.is_absolute():
        target = (cfg.root / target).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            shutil.copy2(target, target.with_suffix(target.suffix + ".bak"))
        except OSError:
            pass
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(render_config_toml(cfg), encoding="utf-8")
    os.replace(tmp, target)
    return target

