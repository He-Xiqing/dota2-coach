"""局内只读的攻略库：从 data/guides/<patch>.json 里按英雄/分路/阶段取 1 条。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class GuideTip:
    id: str
    hero: str
    lane: str
    phase: str
    text: str
    why: str = ""
    sources: tuple[str, ...] = ()
    score: float = 1.0
    evidence: str = "comments"


def _parse_tips(raw: list) -> list[GuideTip]:
    tips: list[GuideTip] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        tips.append(
            GuideTip(
                id=str(item.get("id") or "") or f"tip-{len(tips)}",
                hero=str(item.get("hero") or ""),
                lane=str(item.get("lane") or "任意"),
                phase=str(item.get("phase") or "任意"),
                text=text,
                why=str(item.get("why") or ""),
                sources=tuple(str(s) for s in item.get("sources") or [] if s),
                score=float(item.get("score") or 1.0),
                evidence=str(item.get("evidence") or "comments"),
            )
        )
    return tips


@dataclass(frozen=True)
class GuideBuild:
    hero: str
    items: tuple[str, ...] = ()
    skill: str = ""
    sources: tuple[str, ...] = ()


def _parse_builds(raw: list) -> dict[str, GuideBuild]:
    builds: dict[str, GuideBuild] = {}
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        hero = str(item.get("hero") or "").strip()
        if not hero:
            continue
        items = tuple(str(name) for name in item.get("items") or [] if str(name).strip())
        skill = str(item.get("skill") or "").strip()
        if not items and not skill:
            continue
        builds[hero] = GuideBuild(
            hero=hero,
            items=items,
            skill=skill,
            sources=tuple(str(s) for s in item.get("sources") or [] if s),
        )
    return builds


@dataclass
class GuideStore:
    patch: str = ""
    tips: list[GuideTip] = field(default_factory=list)
    builds: dict[str, GuideBuild] = field(default_factory=dict)

    @property
    def empty(self) -> bool:
        return not self.tips and not self.builds

    def build_for(self, hero_short: str | None) -> GuideBuild | None:
        if not hero_short:
            return None
        return self.builds.get(hero_short)

    @classmethod
    def load(cls, directory: Path, patch: str | None = None) -> "GuideStore":
        """按 patch 精确找；找不到就用 index.json 里最新的一期。"""
        directory = Path(directory)
        if not directory.is_dir():
            return cls()
        candidates: list[Path] = []
        if patch:
            exact = directory / f"{patch}.json"
            if exact.exists():
                candidates.append(exact)
        if not candidates:
            index = directory / "index.json"
            latest = ""
            if index.exists():
                try:
                    raw = json.loads(index.read_text(encoding="utf-8-sig"))
                    latest = str((raw or {}).get("latest") or "")
                except (OSError, json.JSONDecodeError):
                    latest = ""
            if latest:
                candidate = directory / f"{latest}.json"
                if candidate.exists():
                    candidates.append(candidate)
        if not candidates:
            files = sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            files = [p for p in files if p.name != "index.json"]
            candidates = files[:1]
        for path in candidates:
            try:
                raw = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(raw, dict):
                return cls(
                    patch=str(raw.get("patch") or ""),
                    tips=_parse_tips(raw.get("tips") or []),
                    builds=_parse_builds(raw.get("builds") or []),
                )
        return cls()

    def tips_for(
        self,
        hero_short: str | None,
        lane: str,
        phase: str,
        limit: int = 1,
        *,
        include_generic: bool = False,
    ) -> list[GuideTip]:
        hero = (hero_short or "").lower()
        candidates: list[GuideTip] = []
        for tip in self.tips:
            if tip.hero and tip.hero.lower() != hero:
                continue
            if not tip.hero and not include_generic:
                # 通用条（如“对线潮汐别选小黑”）属于选人阶段建议，局内按英雄播报会让玩家误会。
                continue
            if tip.lane not in ("任意", lane):
                continue
            candidates.append(tip)
        exact = [tip for tip in candidates if tip.phase in ("任意", phase)]
        # 没有正好对得上的阶段提示时，退回该英雄的其他提示，总比卡片空着强。
        pool = exact or candidates
        ranked = [((tip.score + (0.5 if tip.hero else 0.0)), tip) for tip in pool]
        ranked.sort(key=lambda pair: (-pair[0], pair[1].text))
        return [tip for _, tip in ranked[:limit]]
