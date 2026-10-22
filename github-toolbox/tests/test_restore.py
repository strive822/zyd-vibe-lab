import hashlib
import importlib.util
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("toolbox_restore", ROOT / "restore.py")
restore = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(restore)


class RestoreBoundaryTests(unittest.TestCase):
    def test_source_snapshot_is_complete_and_excludes_local_state(self):
        assets = json.loads((ROOT / "assets.json").read_text(encoding="utf-8"))
        record = next(entry for entry in assets if entry["id"] == "libretv-source")
        snapshot = ROOT / record["file"]
        self.assertTrue(restore.checked_file(snapshot, record))
        inventory = json.loads((ROOT / "packages/libretv-files.json").read_text(encoding="utf-8"))
        with zipfile.ZipFile(snapshot) as bundle:
            self.assertEqual(set(bundle.namelist()), set(inventory))
            self.assertIn("LICENSE", inventory)
            self.assertIn("package-lock.json", inventory)
            self.assertIn(".env.example", inventory)
            for name, digest in inventory.items():
                self.assertEqual(hashlib.sha256(bundle.read(name)).hexdigest(), digest)
                self.assertFalse(set(Path(name).parts) & {"node_modules", ".next", ".git"})
                self.assertNotIn(".env.local", name)

    def test_unsafe_zip_is_rejected_before_writing_any_files(self):
        for name in ("../outside.txt", "/absolute.txt", "C:/drive.txt", "folder\\file.txt"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                archive = directory / "bad.zip"
                with zipfile.ZipFile(archive, "w") as bundle:
                    bundle.writestr("valid.txt", "valid")
                    bundle.writestr(name, "escape")
                with self.assertRaises(ValueError):
                    restore.extract_zip(archive, directory / "output")
                self.assertFalse((directory / "output/valid.txt").exists())

    def test_symlink_zip_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archive = directory / "bad.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                info = zipfile.ZipInfo("link")
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                bundle.writestr(info, "../../outside")
            with self.assertRaises(ValueError):
                restore.extract_zip(archive, directory / "output")

    def test_case_collisions_and_existing_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archive = directory / "bad.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("README", "first")
                bundle.writestr("readme", "second")
            with self.assertRaises(ValueError):
                restore.extract_zip(archive, directory / "output")
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("keep.txt", "replacement")
            (directory / "output/keep.txt").write_text("original")
            with self.assertRaises(ValueError):
                restore.extract_zip(archive, directory / "output")
            self.assertEqual((directory / "output/keep.txt").read_text(), "original")

    def test_download_checks_hash_before_accepting_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "input.txt"
            source.write_bytes(b"expected bytes")
            record = {"id": "fixture", "url": source.as_uri(), "bytes": source.stat().st_size,
                      "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
            result = restore.download(record, directory / "cache")
            self.assertEqual(result.read_bytes(), source.read_bytes())
            source.write_bytes(b"modified bytes")
            record["sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                restore.download(record, directory / "bad-cache")
            self.assertEqual(list((directory / "bad-cache").iterdir()), [])

    def test_new_libretv_install_gets_private_unique_password(self):
        passwords = []
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            node_archive = directory / "node.zip"
            with zipfile.ZipFile(node_archive, "w") as bundle:
                bundle.writestr("node/runtime-placeholder.txt", "fixture")
            assets = {entry["id"]: entry for entry in json.loads((ROOT / "assets.json").read_text())}
            for count in range(2):
                target = directory / str(count)
                target.mkdir()
                with patch.object(restore, "download", return_value=node_archive), patch.object(restore, "run"):
                    restore.install("LibreTV", target, assets, directory / "cache")
                configuration = (target / "source/.env.local").read_text(encoding="utf-8")
                password_line = configuration.splitlines()[0]
                self.assertTrue(password_line.startswith("PASSWORD="))
                passwords.append(password_line)
                self.assertIn("DEFAULT_SOURCES=", configuration)
                self.assertGreater(len(password_line), 40)
            self.assertNotEqual(*passwords)

    def test_export_does_not_copy_password_or_modify_origin(self):
        export_spec = importlib.util.spec_from_file_location("profile_export", ROOT / "scripts/export_profile.py")
        exporter = importlib.util.module_from_spec(export_spec)
        export_spec.loader.exec_module(exporter)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            origin = directory / "original"
            source = origin / "LibreTV/source"
            source.mkdir(parents=True)
            (source / ".env.local").write_text("PASSWORD=private-sentinel-value\nDEFAULT_SOURCES=[]\n")
            (source / ".env.example").write_text("PASSWORD=change-me\n")
            (source / "package.json").write_text("{}")
            for name in ("launcher.mjs", "open-browser.ps1", "notify.vbs", "start.vbs", "stop.vbs", "stop.mjs", "rebuild.cmd"):
                (origin / "LibreTV" / name).write_text("fixture")
            for name in ("LibreTV/source/LICENSE", "rea/source/LICENSE", "Windows-MCP/LICENSE.md"):
                destination = origin / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("fixture license")
            output = directory / "export"
            output.mkdir()
            with patch.object(exporter, "ROOT", output), patch.object(sys, "argv", ["export", "--source", str(origin)]):
                exporter.main()
            self.assertIn("private-sentinel-value", (source / ".env.local").read_text())
            with zipfile.ZipFile(output / "packages/libretv-source.zip") as bundle:
                self.assertNotIn(".env.local", bundle.namelist())
                self.assertFalse(any(b"private-sentinel-value" in bundle.read(name) for name in bundle.namelist()))


if __name__ == "__main__":
    unittest.main()
