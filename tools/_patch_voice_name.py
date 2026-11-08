"""修复在线音色被保存成中文显示名（如“晓伊”）导致 edge-tts 报 Invalid voice。"""

from __future__ import annotations

import re
from pathlib import Path

root = Path("src/dota2coach")

# ---------------------------------------------------------------- voices.py
p = root / "ui" / "voices.py"
s = p.read_text(encoding="utf-8")
if "def normalize_edge_voice" not in s:
    s = s.replace(
        'DEFAULT_PACK = "xiaoxiao"\n',
        'DEFAULT_PACK = "xiaoxiao"\nDEFAULT_EDGE = "zh-CN-XiaoxiaoNeural"\n'
        '_EDGE_ID = re.compile(r"^[a-z]{2,3}-[A-Za-z]{2,4}-[A-Za-z0-9]+Neural$")\n'
        '\n'
        '\n'
        'def normalize_edge_voice(raw: str) -> str:\n'
        '    """把“晓伊”“云健 · 激昂男声”这类显示名还原成 edge 音色 id。"""\n'
        '    text = (raw or "").strip()\n'
        '    if not text:\n'
        '        return DEFAULT_EDGE\n'
        '    if _EDGE_ID.match(text):\n'
        '        return text\n'
        '    head = text.split("·")[0].strip()\n'
        '    for pack in PACKS:\n'
        '        if not pack.edge:\n'
        '            continue\n'
        '        if head and (head in pack.name or text.startswith(pack.name)):\n'
        '            return pack.edge\n'
        '    return DEFAULT_EDGE\n',
    )
    if "import re" not in s.split("\n")[0:20][0]:
        s = s.replace("from dataclasses import dataclass", "import re\n\nfrom dataclasses import dataclass")
    p.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------- voice.py
p = root / "ui" / "voice.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "        self.edge_voice = edge_voice\n",
    "        try:\n"
    "            from .voices import normalize_edge_voice\n"
    "\n"
    "            self.edge_voice = normalize_edge_voice(edge_voice)\n"
    "        except Exception:  # noqa: BLE001 - 音色名修复失败不该影响启动\n"
    "            self.edge_voice = edge_voice\n",
)
p.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------- config.py
p = root / "config.py"
s = p.read_text(encoding="utf-8")
marker = "    config = Config(\n"
idx = s.find(marker)
if idx >= 0 and "_normalize_voice" not in s:
    # 在构造 Config 之前修正 edge_voice（兼容旧配置里存成中文显示名的情况）
    s = s.replace(
        marker,
        "    try:\n"
        "        from .ui.voices import normalize_edge_voice\n"
        "\n"
        "        voice = replace(voice, edge_voice=normalize_edge_voice(voice.edge_voice))\n"
        "    except Exception:  # noqa: BLE001\n"
        "        pass\n"
        + marker,
        1,
    )
    if "from dataclasses import dataclass, field" in s:
        s = s.replace(
            "from dataclasses import dataclass, field",
            "from dataclasses import dataclass, field, replace",
            1,
        )
    else:
        s = s.replace(
            "from dataclasses import dataclass",
            "from dataclasses import dataclass, replace",
            1,
        )
    p.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------- panel.py
p = root / "ui" / "panel.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    '        cfg.voice.edge_voice = self.edge_voice.currentText().strip() or cfg.voice.edge_voice\n',
    '        cfg.voice.edge_voice = voices.normalize_edge_voice(self.edge_voice.currentText())\n',
)
s = s.replace(
    '        edge, rate, volume = voices.resolve(\n'
    '            self.pack.currentData() or "custom",\n'
    '            self.edge_voice.currentText().strip() or "zh-CN-XiaoxiaoNeural",\n',
    '        raw_voice = self.edge_voice.currentText().strip()\n'
    '        fixed = voices.normalize_edge_voice(raw_voice)\n'
    '        if raw_voice and fixed != raw_voice.strip():\n'
    '            self.edge_voice.setCurrentText(fixed)\n'
    '        edge, rate, volume = voices.resolve(\n'
    '            self.pack.currentData() or "custom",\n'
    '            fixed,\n',
)
p.write_text(s, encoding="utf-8")
print("voice name patched")
