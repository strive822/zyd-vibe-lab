import importlib.util
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "package_projects", Path(__file__).resolve().parents[1] / "package_projects.py"
)
packages = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packages)


class DeliveryCompletenessTests(unittest.TestCase):
    def test_git_ignored_user_data_does_not_enter_delivery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            project = root / "example"
            project.mkdir()
            (root / ".gitignore").write_text("data/\n", encoding="utf-8")
            (project / "README.md").write_text("public", encoding="utf-8")
            (project / "data").mkdir()
            (project / "data/private.json").write_text("private", encoding="utf-8")
            with patch.object(packages, "ROOT", root):
                self.assertEqual(
                    [p.relative_to(project).as_posix() for p in packages.source_files(project)],
                    ["README.md"],
                )

    def test_new_or_removed_source_requires_rebuild(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "example"
            project.mkdir()
            source = project / "README.md"
            source.write_text("original", encoding="utf-8")
            with patch.object(packages, "ROOT", root):
                packages.build("example")
                added = project / "new.py"
                added.write_text("print('new')", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "current sources"):
                    packages.verify(project)
                added.unlink()
                source.unlink()
                with self.assertRaisesRegex(ValueError, "current sources"):
                    packages.verify(project)


if __name__ == "__main__":
    unittest.main()
