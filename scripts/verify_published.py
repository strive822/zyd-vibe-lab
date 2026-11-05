"""Verify pinned, publicly downloadable Release programs at a published source ref."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import PurePosixPath
import stat
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import zipfile

def get(url: str) -> bytes:
    for attempt in range(3):
        candidate = url if attempt == 0 else url + ('&' if '?' in url else '?') + f'verification={time.time_ns()}'
        try:
            with urlopen(Request(candidate, headers={'User-Agent':'zyd-release-verification/2'}), timeout=120) as response:
                return response.read()
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError('Download did not complete')

def verify(name: str, release: dict, repository: str, ref: str) -> str:
    base = f'https://github.com/{repository}/releases/download/' + quote(release['tag'], safe='')
    downloaded = {}
    for asset in release['assets']:
        data = get(base + '/' + quote(asset['name'], safe=''))
        if len(data) != asset['bytes'] or hashlib.sha256(data).hexdigest() != asset['sha256']:
            raise ValueError(f"{name}: Release size/hash mismatch: {asset['name']}")
        downloaded[asset['name']] = data
    checksums = {}
    for line in downloaded['SHA256SUMS.txt'].decode('utf-8-sig').splitlines():
        digest, filename = line.split()
        if filename in checksums:
            raise ValueError(f'{name}: duplicate checksum row')
        checksums[filename] = digest
    programs = set(downloaded) - {'SHA256SUMS.txt'}
    if set(checksums) != programs:
        raise ValueError(f'{name}: incomplete checksum coverage')
    for filename in programs:
        data = downloaded[filename]
        if hashlib.sha256(data).hexdigest() != checksums[filename]:
            raise ValueError(f'{name}: checksums file mismatch')
        if filename.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                seen = set()
                for info in archive.infolist():
                    path = PurePosixPath(info.orig_filename)
                    if (path.is_absolute() or '..' in path.parts or '\\' in info.orig_filename or ':' in info.orig_filename
                            or stat.S_ISLNK(info.external_attr >> 16) or info.filename.casefold() in seen):
                        raise ValueError(f'{name}: unsafe or duplicate Release path')
                    seen.add(info.filename.casefold())
                if archive.testzip() is not None:
                    raise ValueError(f'{name}: ZIP CRC failure')
                for document in ('README.md', 'INSTALL.md'):
                    entry = name + '/' + document
                    if entry in archive.namelist():
                        raw = f'https://raw.githubusercontent.com/{repository}/{ref}/{name}/{document}'
                        if archive.read(entry) != get(raw):
                            raise ValueError(f'{name}: bundled {document} differs from released source')
        elif filename.endswith('.exe') and not data.startswith(b'MZ'):
            raise ValueError(f'{name}: installer is not PE')
    return f'PASS {name}: {len(programs)} program/installer package(s); all public sizes, hashes and ZIP paths verified'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='main')
    args = parser.parse_args()
    repository = 'strive822/zyd-vibe-lab'
    catalog = json.loads(get(f'https://raw.githubusercontent.com/{repository}/{args.ref}/releases.json'))
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(lambda item: verify(item[0], item[1], repository, args.ref), catalog['projects'].items()):
            print(result, flush=True)

if __name__ == '__main__':
    main()
