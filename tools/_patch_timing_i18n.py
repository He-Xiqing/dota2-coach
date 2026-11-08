"""一次性补丁：强势期说明按语言输出。"""

from pathlib import Path

P = Path("src/dota2coach/knowledge/timing.py")
s = P.read_text(encoding="utf-8")
s = s.replace(
    "from dataclasses import dataclass\nfrom pathlib import Path",
    "from dataclasses import dataclass\nfrom pathlib import Path\n\nfrom ..coach.texts_why import note as note_text",
    1,
)
old = '''    @property
    def note(self) -> str:
        if self.label == "前期":
            return "前期强，别和他硬换血"
        if self.label == "后期":
            return "后期强，对线期要压住他"
        if self.label == "中期":
            return "中期发力，别让他舒服到 6 级"
        return "前后期差别不大"'''
new = '''    @property
    def note(self) -> str:
        return note_text(self.label)'''
if old not in s:
    raise SystemExit("note anchor missing")
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8")
print("timing patched")
