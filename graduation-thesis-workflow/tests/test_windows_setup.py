"""Windows installer tests use temporary directories, never actual skill homes."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which('powershell.exe')


@unittest.skipUnless(POWERSHELL, 'Windows PowerShell not available')
class WindowsSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def run_script(self, relative, *args):
        return subprocess.run([POWERSHELL, '-NoProfile', '-NonInteractive', '-File', str(ROOT / relative), *map(str, args)],
                              capture_output=True, timeout=120)

    def test_three_clients_install_and_repeat(self):
        packages = self.base / 'packages'
        subprocess.run([sys.executable, str(ROOT / 'scripts/package.py'), '--out', str(packages)],
                       check=True, capture_output=True)
        for client in ('codex', 'claude-code', 'workbuddy'):
            target = self.base / '中文 带空格路径' / client
            args = ('-Client', client, '-SkillsDir', target)
            result = self.run_script('scripts/install.ps1', *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / 'graduation-thesis/references/00-setup.md').is_file())
            self.assertTrue((target / 'graduation-thesis/scripts/bootstrap-windows.ps1').is_file())
            repeated = self.run_script('scripts/install.ps1', *args)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertIn(b'already_installed', repeated.stdout)
            with zipfile.ZipFile(packages / f'graduation-thesis-{client}.zip') as archive:
                for name in archive.namelist():
                    self.assertEqual((target / name).read_bytes(), archive.read(name), name)
            project = self.base / f'{client}-论文项目'
            entry = target / 'graduation-thesis/scripts/project.py'
            initialized = subprocess.run([sys.executable, str(entry), 'init', str(project)], capture_output=True)
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            checked = subprocess.run([sys.executable, str(entry), 'audit', str(project)], capture_output=True)
            self.assertEqual(checked.returncode, 1, checked.stderr)
            self.assertIn(b'FAIL', checked.stdout)

    def test_existing_different_skill_is_preserved(self):
        target = self.base / 'skills/graduation-thesis'
        target.mkdir(parents=True)
        original = target / 'SKILL.md'
        original.write_text('USER CONTENT', encoding='utf-8')
        result = self.run_script('scripts/install.ps1', '-Client', 'codex', '-SkillsDir', target.parent)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'existing different/incomplete', result.stderr)
        self.assertEqual(original.read_text(), 'USER CONTENT')

    def test_install_plan_does_not_create_files(self):
        target = self.base / 'skills'
        result = self.run_script('scripts/install.ps1', '-Client', 'codex', '-SkillsDir', target, '-Plan')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())

    def test_bootstrap_core_and_reuse_without_download(self):
        target = self.base / 'tools with spaces'
        script = 'skills/graduation-thesis/scripts/bootstrap-windows.ps1'
        result = self.run_script(script, '-ToolsDir', target, '-PythonExe', sys.executable, '-NoDownload')
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads((target / 'runtime.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(receipt['status'], 'ready')
        self.assertTrue(Path(receipt['python']).is_file())
        again = self.run_script(script, '-ToolsDir', target, '-IgnoreSystemPython', '-NoDownload')
        self.assertEqual(again.returncode, 0, again.stderr)

    def test_missing_python_no_download_fails_honestly(self):
        target = self.base / 'absent'
        result = self.run_script('skills/graduation-thesis/scripts/bootstrap-windows.ps1',
                                 '-ToolsDir', target, '-IgnoreSystemPython', '-NoDownload')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'No compatible Python', result.stderr)
        self.assertFalse(target.exists())

    def test_missing_python_plan_is_non_mutating(self):
        target = self.base / 'absent'
        result = self.run_script('skills/graduation-thesis/scripts/bootstrap-windows.ps1',
                                 '-ToolsDir', target, '-IgnoreSystemPython', '-Plan')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b'installer_url', result.stdout)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
