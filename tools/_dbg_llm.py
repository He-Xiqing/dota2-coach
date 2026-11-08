"""临时：看单个视频的 LLM 原始输出（跑完即删）。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dota2coach.config import load_dotenv  # noqa: E402
from dota2coach.llm.client import LlmClient  # noqa: E402
from dota2coach.sources.bilibili import BilibiliClient  # noqa: E402
from dota2coach.sources.guides_builder import (  # noqa: E402
    SYSTEM_PROMPT,
    Evidence,
    build_prompt,
)

load_dotenv(ROOT / ".env")
bvid = sys.argv[1]
transcript = (ROOT / "data" / "guides" / "transcripts" / f"{bvid}.txt").read_text(encoding="utf-8")
client = BilibiliClient()
video = client.video_info(bvid)
evidence = Evidence(video=video, transcript=transcript)
hero_names = {}
for raw in json.loads((ROOT / "data" / "heroes.json").read_text(encoding="utf-8-sig")).values():
    hero_names[str(raw["short"])] = str(raw.get("name_loc") or "")
prompt = build_prompt(evidence, hero_names)
print("prompt chars", len(prompt))
data = LlmClient().chat_json(SYSTEM_PROMPT, prompt)
print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
client.close()
