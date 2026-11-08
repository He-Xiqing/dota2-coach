"""把 minimap 校验接入 validate_config。"""

from pathlib import Path

p = Path("src/dota2coach/config.py")
s = p.read_text(encoding="utf-8")
if "errors.extend(_validate_minimap(cfg))" not in s:
    s = s.replace(
        "    return errors\n\n\ndef save_config",
        "    errors.extend(_validate_minimap(cfg))\n    return errors\n\n\ndef save_config",
        1,
    )
p.write_text(s, encoding="utf-8")
print("wired")
