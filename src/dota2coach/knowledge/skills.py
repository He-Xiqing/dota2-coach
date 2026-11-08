"""英雄技能简介（来自官方 datafeed，离线缓存在 data/hero_skills.json）。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

MAX_DESC = 80


@dataclass(frozen=True)
class Skill:
    name: str
    desc: str

    @property
    def brief(self) -> str:
        text = self.desc.strip()
        for mark in ("。", "；", "，"):
            head = text.split(mark, 1)[0]
            if 3 <= len(head) <= MAX_DESC:
                return head
        return text if len(text) <= MAX_DESC else text[: MAX_DESC - 1] + "…"


@dataclass(frozen=True)
class HeroSkills:
    hero_id: int
    name: str
    bio: str
    abilities: tuple[Skill, ...] = field(default_factory=tuple)

    @property
    def short_bio(self) -> str:
        text = self.bio.strip()
        return text if len(text) <= 46 else text[:45] + "…"

    def tips(self, limit: int = 2) -> list[str]:
        out: list[str] = []
        for skill in self.abilities[:limit]:
            out.append(f"{skill.name}·{skill.brief}")
        return out


def load_hero_skills(path: Path) -> dict[int, HeroSkills]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[int, HeroSkills] = {}
    for key, value in raw.items():
        try:
            hero_id = int(key)
        except (TypeError, ValueError):
            continue
        abilities = tuple(
            Skill(name=str(item.get("name") or ""), desc=str(item.get("desc") or ""))
            for item in (value.get("abilities") or [])
            if item.get("name")
        )
        out[hero_id] = HeroSkills(
            hero_id=hero_id,
            name=str(value.get("name") or ""),
            bio=str(value.get("bio") or ""),
            abilities=abilities,
        )
    return out


def skill_tips(skills: dict[int, HeroSkills], hero_id: int, limit: int = 2) -> list[str]:
    info = skills.get(int(hero_id)) if hero_id else None
    return info.tips(limit) if info else []

SKILL_FILES = {
    "zh-CN": "hero_skills.json",
    "zh-TW": "hero_skills.tchinese.json",
    "en": "hero_skills.english.json",
    "fr": "hero_skills.french.json",
    "ru": "hero_skills.russian.json",
    "de": "hero_skills.german.json",
    "pt": "hero_skills.brazilian.json",
    "es": "hero_skills.spanish.json",
    "tr": "hero_skills.turkish.json",
}


def skills_file_for(data_dir: Path, language: str) -> Path:
    """按界面语言选技能资料，缺文件时回落中文。"""
    name = SKILL_FILES.get(language or "", "")
    path = data_dir / name if name else None
    if path is not None and path.exists():
        return path
    return data_dir / "hero_skills.json"
