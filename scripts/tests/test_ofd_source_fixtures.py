import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location('fixture_checker',Path(__file__).resolve().parents[1] / 'check_repository.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class OfdSourceFixtureTests(unittest.TestCase):
    def test_synthetic_ofd_is_a_checked_source_document_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / 'synthetic.ofd'
            with zipfile.ZipFile(fixture,'w') as archive:
                archive.writestr('OFD.xml','<OFD/>')
            errors = []
            with patch.object(checker,'ROOT',root):
                checker.check_file(fixture,{fixture},errors)
            self.assertEqual(errors,[])

    def test_ofd_fixture_cannot_hide_an_unsafe_archive_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / 'synthetic.ofd'
            with zipfile.ZipFile(fixture,'w') as archive:
                archive.writestr('../escape.txt','fixture')
            errors = []
            with patch.object(checker,'ROOT',root):
                checker.check_file(fixture,{fixture},errors)
            self.assertTrue(any('unsafe ZIP entry' in error for error in errors))

if __name__ == '__main__':
    unittest.main()
