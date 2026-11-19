import importlib.util
import json
import tempfile
import subprocess
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "package_projects", Path(__file__).resolve().parents[1] / "package_projects.py"
)
packages = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packages)


class DeliveryCompletenessTests(unittest.TestCase):
    def test_codegraph_source_is_checked_and_uses_its_upstream_release(self):
        self.assertIn("codegraph", packages.SOURCE_PROJECTS)
        self.assertNotIn("codegraph", packages.PROJECTS)
        packages.verify(packages.ROOT / "codegraph")

    def test_agent_desktop_source_alias_is_validated_and_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            alias = root / packages.AGENT_DESKTOP_SOURCE_ALIAS
            alias.parent.mkdir(parents=True)
            alias.with_name('.agents').mkdir()
            project = alias.parent.parent
            alias.write_bytes(b'.agents')
            with patch.object(packages, 'ROOT', root):
                self.assertEqual(list(packages.source_files(project)), [])
                alias.write_bytes(b'../.agents')
                with self.assertRaisesRegex(ValueError, 'source alias'):
                    list(packages.source_files(project))

    def test_agent_desktop_source_symlink_accepts_only_the_sibling_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            alias = root / packages.AGENT_DESKTOP_SOURCE_ALIAS
            alias.parent.mkdir(parents=True)
            alias.with_name('.agents').mkdir()
            try:
                alias.symlink_to('.agents', target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'Native symlinks are unavailable: {error}')
            with patch.object(packages, 'ROOT', root):
                self.assertEqual(list(packages.source_files(alias.parent.parent)), [])
            alias.unlink()
            alias.symlink_to('..', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'source alias'):
                packages.verify_agent_desktop_source_alias(alias)

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
                with zipfile.ZipFile(output / "today-todo" / "today-todo-windows.zip") as bundle:
                    self.assertIn("today-todo/server.js", bundle.namelist())
                    self.assertNotIn("today-todo/private.txt", bundle.namelist())
                    self.assertNotIn("today-todo/test/test.js", bundle.namelist())
                with self.assertRaisesRegex(ValueError, "outside"):
                    packages.build("today-todo", checkout / "dist")

    def test_agent_desktop_bundle_contains_only_hash_verified_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout = root / "checkout"
            project = checkout / "agent-desktop"
            source = project / "source"
            source.mkdir(parents=True)
            (source / "LICENSE").write_bytes(b"upstream license")
            (source / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            (project / "INSTALL.md").write_bytes(b"Windows setup")
            prepared = root / "prepared"
            binary = prepared / "agent-desktop" / "agent-desktop.exe"
            binary.parent.mkdir(parents=True)
            expected = b"MZofficial fixture"
            binary.write_bytes(expected)
            lock = {"windows_x64": {"executable_sha256": packages.sha256(expected)}}
            (project / "upstream.json").write_text(json.dumps(lock), encoding="utf-8")
            output = root / "release"

            with patch.object(packages, "ROOT", checkout):
                packages.build("agent-desktop", output, prepared)
                archive = output / "agent-desktop" / "agent-desktop-windows.zip"
                with zipfile.ZipFile(archive) as bundle:
                    self.assertEqual(set(bundle.namelist()), {
                        "agent-desktop/agent-desktop.exe", "agent-desktop/INSTALL.md", "agent-desktop/LICENSE",
                    })
                    self.assertEqual(bundle.read("agent-desktop/agent-desktop.exe"), expected)
                binary.write_bytes(b"MZmodified fixture")
                with self.assertRaisesRegex(ValueError, "upstream lock"):
                    packages.build("agent-desktop", output, prepared)
                with zipfile.ZipFile(archive) as bundle:
                    self.assertEqual(bundle.read("agent-desktop/agent-desktop.exe"), expected)

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
