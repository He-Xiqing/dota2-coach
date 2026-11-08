"""一次性补丁：把 coach/texts.t() 接到各提示模块（九语言）。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXTRA = {
    "zh-CN": {
        "hint_line_end": "对线期快结束：准备抱团推塔/控符，别再单独压线",
        "hint_20min": "20 分钟：魔晶/肉山节奏，注意对方开雾",
        "hint_stealth": "对面有隐身（{names}）：4 分钟前带粉，河道补哨兵",
        "hint_opp": "对位：{names}",
        "hint_opp_hard": "历史对位偏难（胜率 {rate}）：先稳住补刀，等队友",
        "hint_late": "对面后期英雄多（{names}）：对线期要压，别拖",
        "stat_networth": "总经济",
        "stat_kda": "战绩",
        "stat_cs": "正反补",
        "summary_stats": "{hero} · {kda} · 正反补 {cs}/{denies} · {gpm} GPM · {minutes} 分钟",
    },
    "zh-TW": {
        "hint_line_end": "對線期快結束：準備抱團推塔/控符，別再單獨壓線",
        "hint_20min": "20 分鐘：魔晶/肉山節奏，注意對方開霧",
        "hint_stealth": "對面有隱身（{names}）：4 分鐘前帶粉，河道補哨兵",
        "hint_opp": "對位：{names}",
        "hint_opp_hard": "歷史對位偏難（勝率 {rate}）：先穩住補刀，等隊友",
        "hint_late": "對面後期英雄多（{names}）：對線期要壓，別拖",
        "stat_networth": "總經濟",
        "stat_kda": "戰績",
        "stat_cs": "正反補",
        "summary_stats": "{hero} · {kda} · 正反補 {cs}/{denies} · {gpm} GPM · {minutes} 分鐘",
    },
    "en": {
        "hint_line_end": "Laning is ending: group up for towers or runes, stop solo pushing",
        "hint_20min": "20 min: shard/Rosh timing, watch for smoke ganks",
        "hint_stealth": "They have invisibility ({names}): bring dust by 4 min, ward the river",
        "hint_opp": "Lane opponent: {names}",
        "hint_opp_hard": "Hard matchup historically ({rate}): secure farm, wait for your team",
        "hint_late": "Many late-game heroes ({names}): pressure the lane, don't stall",
        "stat_networth": "Net worth",
        "stat_kda": "KDA",
        "stat_cs": "CS",
        "summary_stats": "{hero} · {kda} · CS {cs}/{denies} · {gpm} GPM · {minutes} min",
    },
    "fr": {
        "hint_line_end": "Fin de la phase de ligne : groupe pour les tours ou les runes, arrête de push seul",
        "hint_20min": "20 min : timing shard/Rosh, attention aux smokes",
        "hint_stealth": "Invisibilité en face ({names}) : dust avant 4 min, ward rivière",
        "hint_opp": "Adversaire de ligne : {names}",
        "hint_opp_hard": "Matchup difficile ({rate}) : sécurise le farm, attends ton équipe",
        "hint_late": "Beaucoup de héros late ({names}) : pression en ligne, ne traîne pas",
        "stat_networth": "Net worth",
        "stat_kda": "KDA",
        "stat_cs": "CS",
        "summary_stats": "{hero} · {kda} · CS {cs}/{denies} · {gpm} GPM · {minutes} min",
    },
    "ru": {
        "hint_line_end": "Лейнинг кончается: собирайтесь на башни или руны, не пушьте в одиночку",
        "hint_20min": "20 минут: тайминг шарда/Рошана, следите за смоками",
        "hint_stealth": "У них невидимость ({names}): пыль к 4-й минуте, вард на реке",
        "hint_opp": "Соперник по линии: {names}",
        "hint_opp_hard": "Тяжёлый матчап ({rate}): фармите безопасно, ждите команду",
        "hint_late": "Много поздних героев ({names}): давите линию, не тяните",
        "stat_networth": "Нетворс",
        "stat_kda": "KDA",
        "stat_cs": "CS",
        "summary_stats": "{hero} · {kda} · CS {cs}/{denies} · {gpm} GPM · {minutes} мин",
    },
    "de": {
        "hint_line_end": "Laning endet: sammeln für Türme oder Runen, nicht mehr allein pushen",
        "hint_20min": "20 Min: Shard/Rosh-Timing, auf Smokes achten",
        "hint_stealth": "Gegner mit Unsichtbarkeit ({names}): Dust bis Minute 4, River warden",
        "hint_opp": "Lane-Gegner: {names}",
        "hint_opp_hard": "Schweres Matchup ({rate}): sicher farmen, aufs Team warten",
        "hint_late": "Viele Late-Heroes ({names}): Lane unter Druck setzen, nicht trödeln",
        "stat_networth": "Networth",
        "stat_kda": "KDA",
        "stat_cs": "CS",
        "summary_stats": "{hero} · {kda} · CS {cs}/{denies} · {gpm} GPM · {minutes} Min",
    },
    "pt": {
        "hint_line_end": "Fase de rotas acabando: agrupe para torres ou runas, pare de pushar sozinho",
        "hint_20min": "20 min: timing de shard/Rosh, cuidado com smokes",
        "hint_stealth": "Invisibilidade no time inimigo ({names}): dust antes dos 4 min, ward no rio",
        "hint_opp": "Oponente da rota: {names}",
        "hint_opp_hard": "Confronto difícil ({rate}): garanta o farm, espere o time",
        "hint_late": "Muitos heróis de late ({names}): pressione a rota, não arraste",
        "stat_networth": "Net worth",
        "stat_kda": "KDA",
        "stat_cs": "CS",
        "summary_stats": "{hero} · {kda} · CS {cs}/{denies} · {gpm} GPM · {minutes} min",
    },
    "es": {
        "hint_line_end": "Termina la fase de líneas: agrupaos para torres o runas, deja de pushear solo",
        "hint_20min": "20 min: timing de shard/Rosh, cuidado con los smokes",
        "hint_stealth": "Tienen invisibilidad ({names}): lleva dust antes del minuto 4, ward en el río",
        "hint_opp": "Rival de línea: {names}",
        "hint_opp_hard": "Emparejamiento difícil ({rate}): asegura el farm, espera al equipo",
        "hint_late": "Muchos héroes de late ({names}): presiona la línea, no te demores",
        "stat_networth": "Net worth",
        "stat_kda": "KDA",
        "stat_cs": "CS",
        "summary_stats": "{hero} · {kda} · CS {cs}/{denies} · {gpm} GPM · {minutes} min",
    },
    "tr": {
        "hint_line_end": "Lane evresi bitiyor: kule veya rune için toplan, tek başına pushlama",
        "hint_20min": "20. dakika: shard/Rosh zamanı, smoke ganklere dikkat",
        "hint_stealth": "Rakipte görünmezlik var ({names}): 4. dakikada dust al, nehirde ward",
        "hint_opp": "Lane rakibi: {names}",
        "hint_opp_hard": "Zor eşleşme ({rate}): güvenli farm yap, takımı bekle",
        "hint_late": "Çok fazla geç oyun kahramanı ({names}): hatta baskı kur, oyalanma",
        "stat_networth": "Net worth",
        "stat_kda": "KDA",
        "stat_cs": "CS",
        "summary_stats": "{hero} · {kda} · CS {cs}/{denies} · {gpm} GPM · {minutes} dk",
    },
}


def _edit(path: Path, pairs: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"anchor missing in {path.name}: {old[:60]}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("patched", path.name)


def main() -> None:
    # 1) texts.py: append EXTRA merge
    texts = ROOT / "src/dota2coach/coach/texts.py"
    body = texts.read_text(encoding="utf-8")
    if "_EXTRA" not in body:
        marker = '\n_language = "zh-CN"\n'
        extra_src = "\n_EXTRA = {\n" + "".join(
            f"    {lang!r}: {table!r},\n" for lang, table in EXTRA.items()
        ) + "}\nfor _lang, _extra in _EXTRA.items():\n    TEXTS.setdefault(_lang, {}).update(_extra)\n"
        body = body.replace(marker, extra_src + marker, 1)
        texts.write_text(body, encoding="utf-8")
        print("texts.py extra keys")

    # 2) timers.py
    _edit(
        ROOT / "src/dota2coach/coach/timers.py",
        [
            ("from .state import format_clock", "from .state import format_clock\nfrom .texts import t"),
            ('hints.append(Hint(bounty, "赏金符：去符点，顺手补眼"))', 'hints.append(Hint(bounty, t("timer_bounty")))'),
            ('hints.append(Hint(water, "水符：回血回蓝"))', 'hints.append(Hint(water, t("timer_water")))'),
            ('hints.append(Hint(power, "神符：中单控符"))', 'hints.append(Hint(power, t("timer_power")))'),
            ('hints.append(Hint(wisdom, "智慧神龛：去拿经验"))', 'hints.append(Hint(wisdom, t("timer_wisdom")))'),
            ('hints.append(Hint(lotus, "莲花：顺路采一朵"))', 'hints.append(Hint(lotus, t("timer_lotus")))'),
            ('hints.append(Hint(TORMENTOR_FIRST, "痛苦魔方出现：注意开雾/抢先手"))', 'hints.append(Hint(TORMENTOR_FIRST, t("timer_tormentor")))'),
            ('return "开局：买眼和补给、先抢符点；对线先看对方一级技能"', 'return t("hint_start")'),
            ('return "对线期快结束：准备抱团推塔/控符，别再单独压线"', 'return t("hint_line_end")'),
            ('return "20 分钟：魔晶/肉山节奏，注意对方开雾"', 'return t("hint_20min")'),
        ],
    )

    # 3) tp.py
    _edit(
        ROOT / "src/dota2coach/coach/tp.py",
        [("from __future__ import annotations", "from __future__ import annotations\n\nfrom .texts import t")],
    )
    tp = ROOT / "src/dota2coach/coach/tp.py"
    body = tp.read_text(encoding="utf-8")
    body = body.replace("    return TP_TEXT", '    return t("tp_missing")')
    tp.write_text(body, encoding="utf-8")

    # 4) lane.py
    _edit(
        ROOT / "src/dota2coach/coach/lane.py",
        [
            ("from .lane_style import plan_for", "from .lane_style import plan_for\nfrom .texts import t"),
            ('LaneTip(f"lane:hp:{minute}", "血量低：先吃树/回城，别在线上硬撑", urgent=True)', 'LaneTip(f"lane:hp:{minute}", t("hint_hp"), urgent=True)'),
            ('LaneTip(f"lane:mana:{minute}", "蓝量见底：留技能保命，别乱放")', 'LaneTip(f"lane:mana:{minute}", t("hint_mana"))'),
            ('LaneTip("lane:six", "到 6 级：可以喊队友开雾/游走")', 'LaneTip("lane:six", t("hint_level6"))'),
            ('LaneTip("lane:ward", "买组眼：河道和野区入口各插一个")', 'LaneTip("lane:ward", t("hint_ward"))'),
            ('LaneTip("lane:night", "天黑了：中路容易游走，河道视野补起来")', 'LaneTip("lane:night", t("hint_night"))'),
            ('f"对面有隐身（{_names(stealth)}）：4 分钟前带粉，河道补哨兵",', 't("hint_stealth", names=_names(stealth)),'),
            ('tips.append(LaneTip(f"lane:opp:{labels}", f"对位：{labels}"))', 'tips.append(LaneTip(f"lane:opp:{labels}", t("hint_opp", names=labels)))'),
            ('f"历史对位偏难（胜率 {matchup_winrate:.0%}）：先稳住补刀，等队友",', 't("hint_opp_hard", rate=f"{matchup_winrate:.0%}"),'),
            ('f"对面后期英雄多（{_names(late)}）：对线期要压，别拖",', 't("hint_late", names=_names(late)),'),
            ('f"可能对位：{labels}（对面{side}，推测）",', 't("possible_opp", names=labels, side=t("possible_side_safe" if not safe else "possible_side_off")),'),
            ('LaneTip("lane:cs", "补刀偏少：先专注正补，别追残血")', 'LaneTip("lane:cs", t("hint_cs"))'),
        ],
    )

    # 5) summary.py
    _edit(
        ROOT / "src/dota2coach/coach/summary.py",
        [
            ("from ..gsi.models import Snapshot", "from ..gsi.models import Snapshot\nfrom .texts import t"),
            (
                '''            f"死亡偏多（{summary.deaths} 次）：团战前先看小地图，"
            "没视野别第一个上，残血先撤"''',
                '''            t(
                "improve_deaths",
                n=summary.deaths,
            )''',
            ),
            (
                '''            f"补刀偏少（{summary.last_hits} 个，约 {lh_per_min:.1f}/分钟）："
            "对线期以补刀为主，别为了消耗漏刀"''',
                '''            t(
                "improve_cs",
                n=summary.last_hits,
                rate=f"{lh_per_min:.1f}",
            )''',
            ),
            (
                '''            f"打钱效率一般（{summary.gpm} GPM）：中期多利用野区，"
            "兵线推过去再刷野，别在地图中间干等"''',
                '''            t(
                "improve_gpm",
                gpm=summary.gpm,
            )''',
            ),
            ('tips.append("这局整体数据不差，输在关键团：下一把提前沟通集火目标")', 'tips.append(t("encourage_loss"))'),
            ('tips.append("数据很稳：保持这个补刀和参团节奏")', 'tips.append(t("encourage_win"))'),
            ('return "这局打得不错，保持手感，继续上分！"', 'return t("encourage_win")'),
            ('return "输一局没关系，把上面的点做到，下一把就能赢回来！"', 'return t("encourage_loss")'),
            ('return "休息一下，下一把继续加油！"', 'return t("summary_draw")'),
            (
                '''        f"{summary.hero} · {summary.kda} · 正反补 {summary.last_hits}/{summary.denies}"
        f" · {summary.gpm} GPM · {minutes} 分钟",
        f"结果：{summary.result}",''',
                '''        t(
            "summary_stats",
            hero=summary.hero,
            kda=summary.kda,
            cs=summary.last_hits,
            denies=summary.denies,
            gpm=summary.gpm,
            minutes=minutes,
        ),
        t("result", result=_result_text(summary)),''',
            ),
        ],
    )

    # summary: helper for localized result
    sm = ROOT / "src/dota2coach/coach/summary.py"
    body = sm.read_text(encoding="utf-8")
    if "_result_text" not in body:
        body = body.replace(
            "def summary_lines(",
            '''def _result_text(summary: MatchSummary) -> str:
    if summary.win is None:
        return t("summary_draw")
    return t("win") if summary.win else t("loss")


def summary_lines(''',
            1,
        )
    sm.write_text(body, encoding="utf-8")

    # 6) app.py
    _edit(
        ROOT / "src/dota2coach/app.py",
        [
            ('return f"对位胜率：均 {average * 100:.0f}%（最难 {worst_name} {worst_rate * 100:.0f}%）"',
             'return t("label_matchup", avg=f"{average * 100:.0f}", name=worst_name, rate=f"{worst_rate * 100:.0f}")'),
            ('text = f"补给：{item}——{why}"', 'text = f"{t(\'label_supply\')}：{item} —— {why}"'),
            ('lines.append(f"攻略：{guide.text}")', 'lines.append(f"{t(\'label_guide\')}：{guide.text}")'),
            ('lines = [f"推荐：{first.display} —— {first.why}", f"用法：{first.how}"]',
             'lines = [f"{t(\'label_recommend\')}：{first.display} —— {first.why}", f"{t(\'label_usage\')}：{first.how}"]'),
            ('lines.append(f"加点：{build.skill}")', 'lines.append(f"{t(\'label_skill\')}：{build.skill}")'),
            ('from .coach.state import CoachState, HealthTracker, clock_time, format_clock, phase_for',
             'from .coach.state import CoachState, HealthTracker, clock_time, format_clock, phase_for\nfrom .coach.texts import phase_name, set_language, t'),
        ],
    )

    # 7) app: set language at init + apply_settings
    ap = ROOT / "src/dota2coach/app.py"
    body = ap.read_text(encoding="utf-8")
    if "set_language(config.app.language)" not in body:
        body = body.replace(
            "        self.config = config\n",
            "        self.config = config\n        set_language(config.app.language)\n",
            1,
        )
    if "set_language(cfg.app.language)" not in body:
        body = body.replace(
            "        self.config = cfg\n",
            "        self.config = cfg\n        set_language(cfg.app.language)\n",
            1,
        )
    ap.write_text(body, encoding="utf-8")

    # 8) panel: phase name localized
    _edit(
        ROOT / "src/dota2coach/ui/panel.py",
        [
            ("from ..i18n import LANGUAGES, normalize_language, tr", "from ..coach.texts import phase_name\nfrom ..i18n import LANGUAGES, normalize_language, tr"),
            ('f"{format_clock(clock)} · {phase}"', 'f"{format_clock(clock)} · {phase_name(phase)}"'),
        ],
    )


if __name__ == "__main__":
    main()
