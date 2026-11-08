from __future__ import annotations

import shutil
import unittest
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from dota2coach.config import (
    load_config,
    render_config_toml,
    save_config,
    validate_config,
    app_root,
)

ROOT = Path(__file__).resolve().parents[1]


class ConfigWriteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = ROOT / "tests" / "_tmp" / f"config-{uuid4().hex[:8]}"
        self.dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_save_and_reload_roundtrip(self) -> None:
        cfg = load_config(root=self.dir)
        edited = replace(
            cfg,
            overlay=replace(cfg.overlay, opacity=0.75, click_through=False),
            voice=replace(cfg.voice, enabled=False, rate=3, volume=80),
            gsi=replace(cfg.gsi, port=31999),
            assist=replace(cfg.assist, name_strip=False, fight_alerts=False),
        )
        path = save_config(edited)
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("[voice]", text)
        self.assertIn("opacity = 0.75", text)
        self.assertIn("[assist]", text)
        self.assertIn("name_strip = false", text)
        self.assertIn("click_through = false", text)

        again = load_config(root=self.dir)
        self.assertAlmostEqual(again.overlay.opacity, 0.75)
        self.assertFalse(again.overlay.click_through)
        self.assertFalse(again.voice.enabled)
        self.assertEqual(again.voice.rate, 3)
        self.assertEqual(again.gsi.port, 31999)

    def test_second_save_creates_backup(self) -> None:
        cfg = load_config(root=self.dir)
        path = save_config(cfg)
        save_config(replace(cfg, overlay=replace(cfg.overlay, opacity=0.6)))
        backup = path.with_suffix(path.suffix + ".bak")
        self.assertTrue(backup.exists())
        self.assertIn("opacity = 0.9", backup.read_text(encoding="utf-8"))

    def test_invalid_values_rejected(self) -> None:
        cfg = load_config(root=self.dir)
        bad = replace(
            cfg,
            gsi=replace(cfg.gsi, port=70000),
            overlay=replace(cfg.overlay, opacity=0.05),
            voice=replace(cfg.voice, backend="nope"),
        )
        errors = validate_config(bad)
        self.assertGreaterEqual(len(errors), 3)
        with self.assertRaises(ValueError):
            save_config(bad)

    def test_render_keeps_windows_paths_literal(self) -> None:
        cfg = load_config(root=self.dir)
        text = render_config_toml(cfg)
        self.assertIn("dota_path = 'D:\\SteamLibrary", text)

    def test_app_root_is_writable_for_temp(self) -> None:
        base, writable = app_root(self.dir)
        self.assertEqual(base, self.dir.resolve())
        self.assertTrue(writable.exists())

    def test_example_used_when_config_missing(self) -> None:
        example = self.dir / "config.example.toml"
        example.write_text("[gsi]\nport = 32111\n", encoding="utf-8")
        cfg = load_config(root=self.dir)
        self.assertEqual(cfg.gsi.port, 32111)
        self.assertEqual(Path(cfg.config_path).name, "config.toml")

        save_config(cfg)
        self.assertTrue((self.dir / "config.toml").exists())
        self.assertEqual(
            example.read_text(encoding="utf-8"), "[gsi]\nport = 32111\n"
        )


if __name__ == "__main__":
    unittest.main()
