"""Offline regression tests. Fixtures are synthetic, never research evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr
import io
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'graduation-thesis'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


project = load('project', SKILL / 'scripts' / 'project.py')
literature = load('literature', SKILL / 'scripts' / 'literature.py')
package = load('package', ROOT / 'scripts' / 'package.py')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = project.init(Path(self.temp.name) / 'project')

    def read(self, name):
        return json.loads((self.root / name).read_text(encoding='utf-8'))

    def write(self, name, data):
        project.write_json(self.root / name, data)

    def fixture(self):
        # A structurally complete synthetic fixture, not a real thesis or real approval.
        for name in ('confirmation.md', 'school.md', 'policy.md', 'evidence.txt', 'thesis.md', 'review.md'):
            (self.root / name).write_text('SYNTHETIC TEST FIXTURE ONLY\n', encoding='utf-8')
        review_hash = project.digest(self.root / 'review.md')
        req = self.read('requirements.json')
        req.update(confirmed=True, confirmation_path='confirmation.md', discipline='TEST', topic='TEST',
                   methods=['literature'], school_requirements_path='school.md',
                   ai_policy={'status': 'checked', 'source_path': 'policy.md'},
                   deliverables=[{'id': 'thesis', 'path': 'thesis.md'}],
                   acceptance_criteria=[{'id': 'a', 'requirement': 'TEST', 'status': 'met',
                                         'review_path': 'review.md', 'review_sha256': review_hash}])
        self.write('requirements.json', req)
        state = self.read('state.json')
        state.update(status='delivery', blockers=[])
        self.write('state.json', state)
        self.write('evidence.json', [{'id': 'e1', 'kind': 'literature', 'path': 'evidence.txt',
                    'sha256': project.digest(self.root / 'evidence.txt'), 'provenance': 'SYNTHETIC',
                    'retrieved_at': 'TEST', 'verification': 'checked', 'read_scope': 'abstract',
                    'url': 'https://example.invalid/synthetic'}])
        self.write('claims.json', [{'id': 'c1', 'text': 'TEST', 'location': 'TEST section',
                    'status': 'supported', 'evidence_ids': ['e1'], 'required_scope': 'abstract',
                    'locator': 'TEST abstract', 'rationale': 'TEST only'}])
        self.write('artifacts.json', [{'id': 'thesis', 'path': 'thesis.md', 'status': 'reviewed',
                    'sha256': project.digest(self.root / 'thesis.md'),
                    'review_path': 'review.md', 'review_sha256': review_hash}])

    def test_empty_project_cannot_pass(self):
        self.assertTrue(project.audit(self.root))

    def test_init_never_overwrites(self):
        with self.assertRaises(ValueError):
            project.init(self.root)

    def test_complete_records_pass_structure_only(self):
        self.fixture()
        self.assertEqual(project.audit(self.root), [])

    def test_changed_evidence_fails(self):
        self.fixture()
        (self.root / 'evidence.txt').write_text('CHANGED TEST', encoding='utf-8')
        self.assertTrue(any('SHA256' in e for e in project.audit(self.root)))

    def test_abstract_cannot_support_fulltext(self):
        self.fixture()
        claims = self.read('claims.json')
        claims[0]['required_scope'] = 'fulltext'
        self.write('claims.json', claims)
        self.assertTrue(any('scope insufficient' in e for e in project.audit(self.root)))

    def test_unknown_evidence_fails(self):
        self.fixture()
        claims = self.read('claims.json')
        claims[0]['evidence_ids'] = ['missing']
        self.write('claims.json', claims)
        self.assertTrue(any('unknown evidence' in e for e in project.audit(self.root)))

    def test_path_escape_fails(self):
        self.fixture()
        evidence = self.read('evidence.json')
        evidence[0]['path'] = '../outside.txt'
        self.write('evidence.json', evidence)
        self.assertTrue(any('inside project' in e for e in project.audit(self.root)))

    def test_missing_delivery_fails(self):
        self.fixture()
        (self.root / 'thesis.md').unlink()
        self.assertTrue(any('missing or empty' in e for e in project.audit(self.root)))

    def test_blocked_cannot_pass(self):
        self.fixture()
        state = self.read('state.json')
        state['blockers'] = ['Missing actual survey data']
        self.write('state.json', state)
        self.assertTrue(any('blockers' in e for e in project.audit(self.root)))

    def test_unverified_data_requires_disclosure(self):
        self.fixture()
        evidence = self.read('evidence.json')
        evidence[0]['verification'] = 'user_supplied_unverified'
        self.write('evidence.json', evidence)
        self.assertTrue(any('disclose' in e for e in project.audit(self.root)))

    def test_invalid_json_fails(self):
        (self.root / 'claims.json').write_text('{', encoding='utf-8')
        self.assertTrue(project.audit(self.root))

    def test_duplicate_ids_fail(self):
        self.fixture()
        claims = self.read('claims.json')
        self.write('claims.json', claims + claims)
        self.assertTrue(any('duplicate' in e for e in project.audit(self.root)))

    def test_doi_url_and_query_encoding(self):
        self.assertEqual(literature.make_url('doi', 'https://doi.org/10.1000/test'),
                         'https://api.crossref.org/works/10.1000%2Ftest')
        self.assertIn('query.bibliographic=', literature.make_url('search', '教育 & test'))
        with self.assertRaises(ValueError):
            literature.make_url('doi', 'https://untrusted.invalid/')

    def test_packages_are_self_contained(self):
        output = Path(self.temp.name) / 'dist'
        package.build(output)
        for target in output.glob('*.zip'):
            with zipfile.ZipFile(target) as archive:
                names = archive.namelist()
                self.assertIn('graduation-thesis/SKILL.md', names)
                self.assertIn('graduation-thesis/scripts/project.py', names)
                self.assertIn('graduation-thesis/references/contract.md', names)
                self.assertIn('graduation-thesis/LICENSE', names)
                self.assertFalse(any('__pycache__' in name for name in names))
                text = archive.read('graduation-thesis/SKILL.md').decode('utf-8')
                if 'workbuddy' in target.name:
                    self.assertIn('description_zh:', text)

    def test_network_failure_writes_no_fake_results(self):
        output = self.root / 'literature' / 'failed.json'
        argv = ['literature.py', 'search', 'TEST', '--out', str(output)]
        with patch('sys.argv', argv), patch.object(literature, 'fetch', side_effect=OSError('TEST network failure')):
            with redirect_stderr(io.StringIO()):
                self.assertEqual(literature.main(), 1)
        self.assertFalse(output.exists())
        self.assertFalse(output.with_suffix('.json.raw.json').exists())

    def test_retrieval_does_not_promote_to_fulltext(self):
        output = self.root / 'literature' / 'test.json'
        body = {'status': 'ok', 'message': {'items': [{'title': ['SYNTHETIC TEST'], 'DOI': '10.1000/test'}]}}
        raw = json.dumps(body).encode()
        argv = ['literature.py', 'search', 'TEST', '--out', str(output)]
        with patch('sys.argv', argv), patch.object(literature, 'fetch', return_value=(raw, body)):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(literature.main(), 0)
        result = json.loads(output.read_text(encoding='utf-8'))
        self.assertFalse(result['fulltext_verified'])
        self.assertEqual(result['candidates'][0]['verification'], 'candidate_only')

    def test_existing_search_not_overwritten(self):
        output = self.root / 'literature' / 'existing.json'
        output.write_text('ORIGINAL', encoding='utf-8')
        with patch('sys.argv', ['literature.py', 'search', 'TEST', '--out', str(output)]):
            with redirect_stderr(io.StringIO()):
                self.assertEqual(literature.main(), 1)
        self.assertEqual(output.read_text(encoding='utf-8'), 'ORIGINAL')

    def test_skill_local_links_resolve(self):
        for source in SKILL.rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((source.parent / link.split('#')[0]).is_file(), f'{source}: {link}')


if __name__ == '__main__':
    unittest.main()
