"""Build typed Release artifacts OUTSIDE the source checkout; never install or publish."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = tuple(p.name for p in sorted(ROOT.iterdir()) if p.is_dir()
                 and not p.name.startswith('.') and (p / 'README.md').is_file()
                 and (p / 'INSTALL.md').is_file())
EXCLUDED = {'delivery', 'packages', '.git', '.venv', 'venv', 'node_modules', '.next',
            '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.downloads',
            '.runtime', '.npm-cache', 'target', 'dist'}
ARTIFACT_SUFFIXES = {'.exe', '.dll', '.zip', '.tgz', '.whl', '.pyc'}
COMMON = {'INSTALL.md', 'LICENSE', 'LICENSE.md', 'THIRD_PARTY.md', 'THIRD_PARTY_NOTICES.md'}
RUNTIME = {
    'today-todo': ('server.js', 'package.json', 'public/', 'start.bat', 'assets/app.ico'),
    'pi-task-notify': ('package.json', 'extensions/'),
    'dca-calculator': ('backend/app/', 'backend/requirements.txt', 'backend/requirements-runtime.txt', 'runtime/'),
    'libretv': ('runtime/', 'profile/defaults.json'),
    'flyingmouse-format': ('release-installer/',),
    'yt-dlp': ('restore.py', 'assets.json', 'profile/', 'prepare.cmd'),
    'windows-mcp': ('restore.py', 'assets.json', 'profile/', 'prepare.cmd'),
    'rea': ('restore.py', 'assets.json', 'profile/', 'prepare.cmd'),
}
DATE = (2026, 11, 5, 0, 0, 0)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def source_files(project: Path):
    if (ROOT / '.git').exists():
        result = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z', '--', project.name],
                                cwd=ROOT, check=True, capture_output=True)
        paths = sorted({ROOT / name for name in result.stdout.decode('utf-8').split('\0') if name})
    else:
        paths = sorted(project.rglob('*'))
    for path in paths:
        relative = path.relative_to(project)
        if set(relative.parts) & EXCLUDED or relative.parts[:2] == ('frontend', 'out'):
            continue
        if path.is_symlink() or (path.exists() and getattr(path.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError(f'Linked source entry: {relative}')
        if not path.is_file() or path.suffix in {'.pyc', '.tsbuildinfo'} or path.name == 'next-env.d.ts':
            continue
        if path.name.startswith('.env') and path.name != '.env.example':
            raise ValueError(f'Private environment file: {relative}')
        yield path

def verify(project: Path) -> None:
    """Enforce source-only Git contents without requiring local build output."""
    for path in source_files(project):
        if path.suffix.lower() in ARTIFACT_SUFFIXES:
            raise ValueError(f'Build artifact in source checkout: {path.relative_to(ROOT)}')
    if (ROOT / '.git').exists():
        result = subprocess.run(['git', 'ls-files', '-z', '--', project.name],
                                cwd=ROOT, capture_output=True, check=True)
        for name in result.stdout.decode('utf-8').split('\0'):
            if name and (ROOT / name).exists() and set(Path(name).parts) & {'delivery', 'packages', 'target', 'dist'}:
                raise ValueError(f'Generated artifact directory still tracked: {name}')

def runtime_entries(name: str) -> dict[str, bytes]:
    entries = {}
    for path in source_files(ROOT / name):
        relative = path.relative_to(ROOT / name).as_posix()
        if relative not in COMMON and not any(relative == rule or (rule.endswith('/') and relative.startswith(rule))
                                               for rule in RUNTIME[name]):
            continue
        if '/tests/' in '/' + relative or '/test/' in '/' + relative:
            continue
        output = relative.removeprefix('runtime/').removeprefix('release-installer/')
        if name == 'libretv' and relative == 'profile/defaults.json':
            output = 'defaults.json'
        entries[output] = path.read_bytes()
    return entries

def add_prepared(entries: dict[str, bytes], directory: Path, prefix: str = '') -> None:
    if not directory.is_dir():
        raise ValueError(f'Prepared production build missing: {directory}')
    for path in sorted(directory.rglob('*')):
        if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Linked production entry')
        if path.is_file():
            relative = path.relative_to(directory)
            if any(part in {'cache', '__pycache__'} for part in relative.parts) or path.name.startswith('.env'):
                continue
            key = prefix + relative.as_posix()
            if key in entries:
                raise ValueError(f'Duplicate runtime entry: {key}')
            entries[key] = path.read_bytes()

def write_zip(path: Path, name: str, entries: dict[str, bytes]) -> None:
    if len({key.casefold() for key in entries}) != len(entries):
        raise ValueError('Case-colliding runtime paths')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for relative, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name + '/' + relative, DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)

def build(name: str, output: Path, prepared: Path | None = None, installer: Path | None = None) -> list[dict]:
    output = output.resolve()
    if output.is_relative_to(ROOT.resolve()):
        raise ValueError('Release output must be outside the source checkout')
    destination = output / name
    destination.mkdir(parents=True, exist_ok=True)
    if name == 'daozai':
        if installer is None or sha256(installer.read_bytes()) != 'af0224109265681fd1371414587e1b536f1a1083b72b4bac667cdf826a485934':
            raise ValueError('Pass --installer with the verified personal installer')
        target = destination / 'Daozai-Setup-v0.6.50-x64.exe'
        target.write_bytes(installer.read_bytes())
        artifacts = [target]
    elif name == 'graduation-thesis-workflow':
        spec = importlib.util.spec_from_file_location('thesis_packaging', ROOT / name / 'scripts/package.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        records = module.build(destination)
        artifacts = [destination / record['file'] for record in records]
        (destination / 'checksums.json').unlink()
    else:
        entries = runtime_entries(name)
        if name in {'dca-calculator', 'libretv'} and prepared is None:
            raise ValueError('Pass --prepared with the production web builds')
        if name == 'dca-calculator':
            add_prepared(entries, prepared / name / 'frontend/out', 'frontend/out/')
        if name == 'libretv':
            add_prepared(entries, prepared / name / '.next/standalone')
            add_prepared(entries, prepared / name / '.next/static', '.next/static/')
            add_prepared(entries, ROOT / name / 'source/public', 'public/')
            entries['LICENSE'] = (ROOT / name / 'source/LICENSE').read_bytes()
        target = destination / (name + '-windows.zip')
        write_zip(target, name, entries)
        artifacts = [target]
    records = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha256(p.read_bytes())} for p in artifacts]
    (destination / 'SHA256SUMS.txt').write_text(''.join(f"{r['sha256']}  {r['name']}\n" for r in records),
                                              encoding='utf-8', newline='\n')
    print(f'PASS {name}: {len(artifacts)} runtime artifact(s), outside checkout')
    return records

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', choices=PROJECTS, action='append')
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--installer', type=Path)
    parser.add_argument('--update-catalog', action='store_true')
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'releases.json').read_text(encoding='utf-8'))
    for name in args.project or PROJECTS:
        records = build(name, args.output, args.prepared, args.installer)
        if args.update_catalog:
            checksum = args.output / name / 'SHA256SUMS.txt'
            records.append({'name': checksum.name, 'bytes': checksum.stat().st_size, 'sha256': sha256(checksum.read_bytes())})
            catalog['projects'][name]['assets'] = records
    if args.update_catalog:
        (ROOT / 'releases.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n',
                                           encoding='utf-8', newline='\n')

if __name__ == '__main__':
    main()
