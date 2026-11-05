"""Download and hash-verify a project's pinned Release; never install or launch it."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

def fetch(project: str, destination: Path, catalog: dict) -> dict:
    record = catalog['projects'][project]
    destination = destination.resolve()
    if destination.is_relative_to(ROOT.resolve()):
        raise ValueError('Download programs outside the source checkout')
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    for asset in record['assets']:
        name = asset['name']
        if Path(name).name != name or ':' in name or '\\' in name:
            raise ValueError('Invalid asset name')
        target = destination / name
        if target.is_symlink() or (target.exists() and getattr(target.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Linked download target')
        def matches(path):
            return path.is_file() and path.stat().st_size == asset['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest() == asset['sha256']
        if target.exists() and not matches(target):
            raise ValueError('Existing different file preserved: ' + name)
        if not target.exists():
            url = 'https://github.com/' + catalog['repository'] + '/releases/download/' + quote(record['tag'], safe='') + '/' + quote(name, safe='')
            temporary = destination / (name + '.download')
            if temporary.exists():
                raise ValueError('Existing partial download preserved: ' + temporary.name)
            for attempt in range(3):
                try:
                    with urlopen(Request(url, headers={'User-Agent':'zyd-release/1'}), timeout=60) as response, temporary.open('xb') as output:
                        while block := response.read(1024 * 1024):
                            output.write(block)
                    if not matches(temporary):
                        raise ValueError('Release checksum or size mismatch: ' + name)
                    temporary.rename(target)
                    break
                except (OSError, URLError):
                    if attempt == 2:
                        raise
                    time.sleep(attempt + 1)
                finally:
                    temporary.unlink(missing_ok=True)
        results.append({'path': str(target), 'sha256':asset['sha256'], 'verified':True})
    return {'project':project, 'tag':record['tag'], 'files':results, 'installed':False, 'started':False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'releases.json').read_text(encoding='utf-8'))
    print(json.dumps(fetch(args.project, args.destination, catalog), ensure_ascii=False, indent=2))
