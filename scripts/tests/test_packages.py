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

    def test_runtime_bundle_excludes_developer_and_private_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout = root / "checkout"
            checkout.mkdir()
            project = checkout / "today-todo"
            project.mkdir()
            source = project / "README.md"
            source.write_text("original", encoding="utf-8")
            (project / "server.js").write_text("runtime", encoding="utf-8")
            (project / "private.txt").write_text("private", encoding="utf-8")
            (project / "test").mkdir()
            (project / "test" / "test.js").write_text("developer", encoding="utf-8")
            with patch.object(packages, "ROOT", checkout):
                output = root / "artifacts"
                packages.build("today-todo", output)
                import zipfile
                with zipfile.ZipFile(output / "today-todo" / "today-todo-windows.zip") as bundle:
                    self.assertIn("today-todo/server.js", bundle.namelist())
                    self.assertNotIn("today-todo/private.txt", bundle.namelist())
                    self.assertNotIn("today-todo/test/test.js", bundle.namelist())
                with self.assertRaisesRegex(ValueError, "outside"):
                    packages.build("today-todo", checkout / "dist")

    def test_source_only_policy_rejects_a_committed_program(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "example"
            project.mkdir()
            (project / "accidental.exe").write_bytes(b"MZfixture")
            with patch.object(packages, "ROOT", root), self.assertRaisesRegex(ValueError, "artifact"):
                packages.verify(project)


if __name__ == "__main__":
    unittest.main()
