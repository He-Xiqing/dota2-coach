"""临时：验证 DeepSeek key 可用（跑完即删）。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dota2coach.config import load_dotenv  # noqa: E402
from dota2coach.llm.client import LlmClient  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = LlmClient()
print("available", client.available)
if client.available:
    try:
        print("reply", json.dumps(client.chat_json("只回 JSON", '回 {"ok": true}'), ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001
        print("error", type(exc).__name__, exc)
