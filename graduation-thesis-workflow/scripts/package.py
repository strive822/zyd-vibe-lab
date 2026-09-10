"""Build portable skill ZIP files from the single canonical source."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'skills' / 'graduation-thesis'


def build(output):
    output = Path(output).resolve()
    if output.is_relative_to(SOURCE):
        raise ValueError('Build output cannot be inside the skill source.')
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for platform in ('codex', 'claude-code', 'workbuddy'):
        target = output / f'graduation-thesis-{platform}.zip'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(SOURCE.rglob('*')):
                if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
                    continue
                data = path.read_bytes()
                if path.relative_to(SOURCE).as_posix() == 'SKILL.md' and platform == 'workbuddy':
                    text = data.decode('utf-8').replace('\r\n', '\n')
                    text = text.replace('\n---\n', '\ndescription_zh: Evidence-based undergraduate thesis workflow\ndescription_en: Evidence-based undergraduate thesis workflow\nversion: 0.3.0\nauthor: Graduation Thesis Workflow contributors\n---\n', 1)
                    data = text.encode('utf-8')
                archive.writestr('graduation-thesis/' + path.relative_to(SOURCE).as_posix(), data)
            archive.write(ROOT / 'LICENSE', 'graduation-thesis/LICENSE')
        records.append({'file': target.name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    (output / 'checksums.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    return records


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=str(ROOT / 'dist'))
    args = parser.parse_args()
    for record in build(args.out):
        print(record['file'], record['sha256'])
