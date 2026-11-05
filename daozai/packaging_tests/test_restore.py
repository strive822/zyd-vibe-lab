# Copyright (c) 2026 zhongyudi. SPDX-License-Identifier: MIT
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("daozai_restore", ROOT / "restore.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SnapshotRestoreTests(unittest.TestCase):
    def test_restore_is_independent_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "assets.json").write_text(json.dumps({
                "artifacts": [], "source_files": ["assets.json", "Cargo.toml"]}))
            (source / "Cargo.toml").write_text("fixture")
            (source / "target").mkdir()
            (source / "target/private").write_text("do not copy")
            (source / ".env").write_text("PRIVATE_FIXTURE=true")
            (source / "private-backup.txt").write_text("do not copy")
            target = root / "new"
            with patch.object(module, "ROOT", source):
                module.restore(target)
                self.assertEqual((target / "Cargo.toml").read_text(), "fixture")
                self.assertFalse((target / "target").exists())
                self.assertFalse((target / ".env").exists())
                self.assertFalse((target / "private-backup.txt").exists())
                with self.assertRaises(ValueError):
                    module.restore(target)
                with self.assertRaises(ValueError):
                    module.restore(source / "nested")

    def test_bad_artifact_is_rejected_before_target_is_created(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "artifact.exe").write_bytes(b"changed")
            (source / "assets.json").write_text(json.dumps({"source_files": [], "artifacts": [
                {"file": "artifact.exe", "bytes": 7, "sha256": "0" * 64}]}))
            target = root / "new"
            with patch.object(module, "ROOT", source), self.assertRaises(ValueError):
                module.restore(target)
            self.assertFalse(target.exists())

    def test_manifest_cannot_copy_outside_the_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (root / "private.txt").write_text("do not copy")
            (source / "assets.json").write_text(json.dumps({
                "artifacts": [], "source_files": ["../private.txt"]}))
            target = root / "new"
            with patch.object(module, "ROOT", source), self.assertRaises(ValueError):
                module.restore(target)
            self.assertFalse(target.exists())

    def test_source_alias_cannot_hide_a_nested_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "assets.json").write_text(json.dumps({
                "artifacts": [], "source_files": ["assets.json"]}))
            target = source / "nested"
            with patch.object(module, "ROOT", source / ".." / "source"), self.assertRaises(ValueError):
                module.restore(target)
            self.assertFalse(target.exists())
