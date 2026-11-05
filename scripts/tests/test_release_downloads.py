import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
downloads = load('get_release')
published = load('verify_published')

class ReleaseBoundaryTests(unittest.TestCase):
    def catalog(self, data=b'valid'):
        return {'repository':'example/project', 'projects':{'example':{
            'tag':'example-v1', 'assets':[{'name':'program.zip', 'bytes':len(data),
                                          'sha256':hashlib.sha256(data).hexdigest()}]}}}

    def test_existing_different_file_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'downloads'
            output.mkdir()
            target = output / 'program.zip'
            target.write_bytes(b'private user file')
            with patch.object(downloads, 'urlopen') as network, self.assertRaises(ValueError):
                downloads.fetch('example', output, self.catalog())
            network.assert_not_called()
            self.assertEqual(target.read_bytes(), b'private user file')

    def test_corrupt_download_is_rejected_and_only_own_partial_is_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'downloads'
            with patch.object(downloads, 'urlopen', return_value=io.BytesIO(b'wrong')), self.assertRaises(ValueError):
                downloads.fetch('example', output, self.catalog())
            self.assertEqual(list(output.iterdir()), [])

    def test_existing_partial_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            partial = output / 'program.zip.download'
            partial.write_bytes(b'previous user work')
            with patch.object(downloads, 'urlopen') as network, self.assertRaises(ValueError):
                downloads.fetch('example', output, self.catalog())
            network.assert_not_called()
            self.assertEqual(partial.read_bytes(), b'previous user work')

    def test_published_zip_with_traversal_fails_even_with_matching_hash(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            archive.writestr('../private.txt', b'fixture')
        data = stream.getvalue()
        checksum = (hashlib.sha256(data).hexdigest() + '  program.zip\n').encode()
        release = {'tag':'example-v1','assets':[
            {'name':name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
            for name, content in [('program.zip',data),('SHA256SUMS.txt',checksum)]]}
        with patch.object(published,'get',side_effect=[data,checksum]), self.assertRaisesRegex(ValueError,'unsafe'):
            published.verify('example',release,'example/project','commit')

if __name__ == '__main__':
    unittest.main()
