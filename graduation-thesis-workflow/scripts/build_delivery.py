"""Build the standalone delivery ZIP, its SHA256SUMS.txt and FILES.json.

Reproducible: entries are sorted, and ZIP metadata is pinned, so the same
checked-out bytes always produce the same archive hash. .gitattributes marks
this project `-text`, which keeps the working tree byte-identical to the
committed blobs; without that, a CRLF checkout silently changes FILES.json.

Excluded from the archive: delivery/ itself, .tmp/, __pycache__ and .pyc.
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / 'delivery'
PREFIX = 'graduation-thesis-workflow/'
# Fixed so rebuilds are byte-stable; the value only has to be valid and constant.
ZIP_DATE = (2026, 10, 23, 0, 0, 0)


def source_files():
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {'delivery', '.tmp'}:
            continue
        if '__pycache__' in relative.parts or path.suffix == '.pyc':
            continue
        yield relative.as_posix(), path.read_bytes()


def build():
    DELIVERY.mkdir(exist_ok=True)
    target = DELIVERY / 'graduation-thesis-workflow.zip'
    files = {}
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for relative, data in source_files():
            files[relative] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(PREFIX + relative, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Pin so Windows and POSIX builds agree.
            archive.writestr(info, data)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (DELIVERY / 'SHA256SUMS.txt').write_text(f'{digest}  {target.name}\n', encoding='utf-8', newline='\n')
    (DELIVERY / 'FILES.json').write_text(json.dumps(files, indent=2) + '\n', encoding='utf-8', newline='\n')
    return target, digest, files


if __name__ == '__main__':
    target, digest, files = build()
    print(f'{target.name}: {len(files)} files')
    print(f'sha256 {digest}')
    sys.exit(0)
