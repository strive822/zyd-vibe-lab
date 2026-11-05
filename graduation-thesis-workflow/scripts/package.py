"""Build portable skill ZIP files from the single canonical source."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'skills' / 'graduation-thesis'
WORKBUDDY_VERSION = '0.4.0'
# 固定条目时间戳，使同一源码重复打包得到相同哈希（与 scripts/package_projects.py 一致）。
ENTRY_DATE_TIME = (2026, 10, 23, 0, 0, 0)


def _entry(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=ENTRY_DATE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def workbuddy_skill(source: bytes) -> bytes:
    """Apply the WorkBuddy front-matter transform to canonical SKILL.md bytes."""
    text = source.decode('utf-8').replace('\r\n', '\n')
    text = text.replace(
        '\n---\n',
        '\ndescription_zh: Evidence-based undergraduate thesis workflow\n'
        'description_en: Evidence-based undergraduate thesis workflow\n'
        f'version: {WORKBUDDY_VERSION}\n'
        'author: Graduation Thesis Workflow contributors\n---\n',
        1,
    )
    return text.encode('utf-8')


def build(output):
    output = Path(output).resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Build output must be outside the project source checkout.')
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for platform in ('codex', 'claude-code', 'pi', 'workbuddy'):
        target = output / f'graduation-thesis-{platform}.zip'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(SOURCE.rglob('*')):
                if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
                    continue
                data = path.read_bytes()
                if path.relative_to(SOURCE).as_posix() == 'SKILL.md' and platform == 'workbuddy':
                    data = workbuddy_skill(data)
                archive.writestr(_entry('graduation-thesis/' + path.relative_to(SOURCE).as_posix()), data)
            archive.writestr(_entry('graduation-thesis/LICENSE'), (ROOT / 'LICENSE').read_bytes())
        records.append({'file': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    (output / 'checksums.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=str(Path.home() / '.codex/.tmp/graduation-thesis-release'))
    args = parser.parse_args()
    for record in build(args.out):
        print(record['file'], record['sha256'])
