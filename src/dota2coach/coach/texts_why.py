"""出装理由 / 强势期说明的多语言文本（与 coach.texts 分开维护，避免巨型文件）。"""

from __future__ import annotations

from .texts import language as current_language

WHY: dict[str, dict[str, str]] = {
    "zh-CN": {
        "silence": "对面有沉默（{names}）",
        "cc": "对面控制多（{names}），先手易被秒",
        "magic": "对面法系爆发高（{names}）",
        "heal": "对面回复强（{names}）",
        "escape": "对面机动性高（{names}），需要硬控",
        "physical": "对面物理核心多，需要减伤",
        "mainstream": "{hero} 主流出装（OpenDota 热度）",
    },
    "zh-TW": {
        "silence": "對面有沉默（{names}）",
        "cc": "對面控制多（{names}），先手易被秒",
        "magic": "對面法系爆發高（{names}）",
        "heal": "對面回復強（{names}）",
        "escape": "對面機動性高（{names}），需要硬控",
        "physical": "對面物理核心多，需要減傷",
        "mainstream": "{hero} 主流出裝（OpenDota 熱度）",
    },
    "en": {
        "silence": "Enemy silence ({names})",
        "cc": "Heavy enemy control ({names}) — easy to get bursted",
        "magic": "Enemy magic burst ({names})",
        "heal": "Enemy sustain ({names})",
        "escape": "Enemy mobility ({names}) — you need hard control",
        "physical": "Enemy physical cores — reduce damage",
        "mainstream": "Standard {hero} build (OpenDota)",
    },
    "fr": {
        "silence": "Silence ennemi ({names})",
        "cc": "Contrôle ennemi ({names}) — risque d'être tué vite",
        "magic": "Burst magique ennemi ({names})",
        "heal": "Soins ennemis ({names})",
        "escape": "Mobilité ennemie ({names}) — il faut du contrôle dur",
        "physical": "Cores physiques ennemis — réduire les dégâts",
        "mainstream": "Build standard de {hero} (OpenDota)",
    },
    "de": {
        "silence": "Silence beim Gegner ({names})",
        "cc": "Viel Kontrolle beim Gegner ({names}) — schnell tot",
        "magic": "Magischer Burst beim Gegner ({names})",
        "heal": "Heilung beim Gegner ({names})",
        "escape": "Mobilität beim Gegner ({names}) — harter Kontrollzauber nötig",
        "physical": "Viele physische Cores — Schaden reduzieren",
        "mainstream": "Standard-Build von {hero} (OpenDota)",
    },
    "ru": {
        "silence": "Молчание у врагов ({names})",
        "cc": "Много контроля у врагов ({names}) — легко убить",
        "magic": "Магический бурст у врагов ({names})",
        "heal": "Лечение у врагов ({names})",
        "escape": "Мобильность у врагов ({names}) — нужен жёсткий контроль",
        "physical": "Много физических коров — снизить урон",
        "mainstream": "Стандартная сборка {hero} (OpenDota)",
    },
    "pt": {
        "silence": "Silêncio inimigo ({names})",
        "cc": "Muito controle inimigo ({names}) — fácil de morrer",
        "magic": "Burst mágico inimigo ({names})",
        "heal": "Cura inimiga ({names})",
        "escape": "Mobilidade inimiga ({names}) — precisa de controle duro",
        "physical": "Muitos cores físicos — reduzir dano",
        "mainstream": "Build padrão de {hero} (OpenDota)",
    },
    "es": {
        "silence": "Silencio enemigo ({names})",
        "cc": "Mucho control enemigo ({names}) — te matan rápido",
        "magic": "Burst mágico enemigo ({names})",
        "heal": "Curación enemiga ({names})",
        "escape": "Movilidad enemiga ({names}) — necesitas control duro",
        "physical": "Muchos cores físicos — reduce el daño",
        "mainstream": "Build estándar de {hero} (OpenDota)",
    },
    "tr": {
        "silence": "Düşmanda sessizlik ({names})",
        "cc": "Düşmanda çok kontrol ({names}) — hızlı ölürsün",
        "magic": "Düşmanda büyü burstü ({names})",
        "heal": "Düşmanda iyileştirme ({names})",
        "escape": "Düşmanda hareketlilik ({names}) — sert kontrol gerek",
        "physical": "Çok fazla fiziksel core — hasarı azalt",
        "mainstream": "{hero} standart dizilişi (OpenDota)",
    },
}

NOTE: dict[str, dict[str, str]] = {
    "zh-CN": {
        "前期": "前期强，别和他硬换血",
        "中期": "中期发力，别让他舒服到 6 级",
        "后期": "后期强，对线期要压住他",
        "均衡": "前后期差别不大",
    },
    "zh-TW": {
        "前期": "前期強，別和他硬換血",
        "中期": "中期發力，別讓他舒服到 6 級",
        "后期": "後期強，對線期要壓住他",
        "均衡": "前後期差別不大",
    },
    "en": {
        "前期": "Strong early — don't trade hits with him",
        "中期": "Powers up mid — don't let him reach 6 comfortably",
        "后期": "Strong late — pressure him in lane",
        "均衡": "Similar early and late",
    },
    "fr": {
        "前期": "Fort tôt — évite les échanges",
        "中期": "Fort au mid — ne le laisse pas passer 6 tranquillement",
        "后期": "Fort tard — pressionne-le en lane",
        "均衡": "Équivalent tôt et tard",
    },
    "de": {
        "前期": "Stark früh — keine Trades mit ihm",
        "中期": "Stark im Midgame — lass ihn nicht entspannt Level 6 erreichen",
        "后期": "Stark spät — setz ihn in der Lane unter Druck",
        "均衡": "Früh und spät ähnlich",
    },
    "ru": {
        "前期": "Силён в начале — не меняйся ударами",
        "中期": "Силён в мидгейме — не дай спокойно взять 6 уровень",
        "后期": "Силён в лейте — дави его на линии",
        "均衡": "Одинаков на всех стадиях",
    },
    "pt": {
        "前期": "Forte no início — não troque dano com ele",
        "中期": "Forte no meio — não deixe ele pegar nível 6 tranquilo",
        "后期": "Forte no fim — pressione ele na lane",
        "均衡": "Parecido no início e no fim",
    },
    "es": {
        "前期": "Fuerte al inicio — no intercambies golpes",
        "中期": "Fuerte en medio — no lo dejes llegar a nivel 6 tranquilo",
        "后期": "Fuerte al final — presiónalo en la línea",
        "均衡": "Similar al inicio y al final",
    },
    "tr": {
        "前期": "Erken oyunda güçlü — vuruş alışverişi yapma",
        "中期": "Orta oyunda güçlenir — 6. seviyeye rahat ulaşmasın",
        "后期": "Geç oyunda güçlü — hatta baskı kur",
        "均衡": "Erken ve geç oyunda benzer",
    },
}


def why(key: str, **fmt: str) -> str:
    lang = current_language()
    table = WHY.get(lang) or WHY["zh-CN"]
    text = table.get(key) or WHY["zh-CN"][key]
    try:
        return text.format(**fmt)
    except (KeyError, IndexError):
        return text


def note(label: str) -> str:
    lang = current_language()
    table = NOTE.get(lang) or NOTE["zh-CN"]
    return table.get(label) or NOTE["zh-CN"].get(label, label)
