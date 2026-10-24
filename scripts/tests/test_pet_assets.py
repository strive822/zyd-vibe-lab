import importlib.util
import tempfile
import unittest
import zipfile
import shutil
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / "codex-bailong-desktop-pet/tools/prepare_assets.py"
SPEC = importlib.util.spec_from_file_location("prepare_assets", SCRIPT)
assets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assets)
PREFIX = "root/outputs/白龙桌宠素材/"


class AssetExtractionTests(unittest.TestCase):
    def test_official_installer_wrapper_is_read_as_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / "payload.zip"
            with zipfile.ZipFile(payload, "w") as bundle:
                bundle.writestr(PREFIX + "素材清单.json", "{}")
                bundle.writestr(PREFIX + "animation.webp", b"fixture")
            archive = root / "official.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("release/installer.exe", b"installer fixture, never executed")
            with patch.object(assets, "embedded_payload", side_effect=lambda exe, out: shutil.copy2(payload, out)), \
                    patch.object(assets, "active_files", return_value=["animation.webp"]):
                self.assertEqual(assets.extract_container(archive, root / "output"), 2)
            self.assertEqual((root / "output/animation.webp").read_bytes(), b"fixture")

    def test_matching_source_manifest_is_kept_while_assets_are_filled(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "source"
            destination.mkdir()
            manifest = destination / "素材清单.json"
            manifest.write_bytes(b"{}")
            stamp = manifest.stat().st_mtime_ns
            archive = root / "assets.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr(PREFIX + "素材清单.json", b"{}")
                bundle.writestr(PREFIX + "animation.webp", b"fixture")
            with patch.object(assets, "active_files", return_value=["animation.webp"]):
                self.assertEqual(assets.extract_assets(archive, destination), 2)
            self.assertEqual(manifest.stat().st_mtime_ns, stamp)
            self.assertEqual((destination / "animation.webp").read_bytes(), b"fixture")

    def test_existing_manifest_is_preserved_before_any_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "assets.zip"
            destination = root / "destination"
            destination.mkdir()
            existing = destination / "素材清单.json"
            existing.write_bytes(b"original")
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr(PREFIX + "素材清单.json", "{}")
                bundle.writestr(PREFIX + "animation.webp", b"fixture")
            with patch.object(assets, "active_files", return_value=["animation.webp"]):
                with self.assertRaisesRegex(ValueError, "preserved"):
                    assets.extract_assets(archive, destination)
            self.assertEqual(existing.read_bytes(), b"original")
            self.assertFalse((destination / "animation.webp").exists())

    def test_case_collisions_and_backslash_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "assets.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr(PREFIX + "素材清单.json", "{}")
                bundle.writestr(PREFIX + "Action.webp", b"a")
                bundle.writestr(PREFIX + "action.webp", b"b")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                assets.extract_assets(archive, root / "case")
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("folder/file.txt", "fixture")
            archive.write_bytes(archive.read_bytes().replace(b"folder/file.txt", b"folder\\file.txt"))
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                assets.extract_assets(archive, root / "backslash")


if __name__ == "__main__":
    unittest.main()
