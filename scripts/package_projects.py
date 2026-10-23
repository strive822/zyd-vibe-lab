"""Build independently transferable project bundles without installing anything."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = tuple(p.name for p in sorted(ROOT.iterdir())
                 if p.is_dir() and not p.name.startswith(".")
                 and (p / "README.md").is_file() and (p / "INSTALL.md").is_file())
EXCLUDED = {"delivery", ".git", ".venv", "venv", "node_modules", ".next",
            "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
            ".downloads", ".runtime"}


def source_files(project: Path):
    for path in sorted(project.rglob("*")):
        relative = path.relative_to(project)
        if set(relative.parts) & EXCLUDED:
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink is not supported: {relative}")
        if not path.is_file() or path.suffix == ".pyc":
            continue
        if path.name.startswith(".env") and path.name != ".env.example":
            raise ValueError(f"Private environment file must not be packaged: {relative}")
        yield path


def build(name: str) -> None:
    project = ROOT / name
    output = project / "delivery"
    output.mkdir(exist_ok=True)
    archive = output / f"{name}.zip"
    manifest = {}
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in source_files(project):
            relative = path.relative_to(project).as_posix()
            data = path.read_bytes()
            manifest[relative] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo(f"{name}/{relative}", date_time=(2026, 10, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data)
    (output / "FILES.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    verify(project)
    print(f"PASS {name}: {len(manifest)} files, {archive.stat().st_size} bytes")


def verify(project: Path) -> None:
    output = project / "delivery"
    expected, filename = (output / "SHA256SUMS.txt").read_text(encoding="utf-8").split()
    archive = output / filename
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Archive checksum mismatch: {project.name}")
    manifest = json.loads((output / "FILES.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("Archive CRC failure")
        if set(bundle.namelist()) != {f"{project.name}/{name}" for name in manifest}:
            raise ValueError("Unexpected archive entries")
        for relative, digest in manifest.items():
            data = bundle.read(f"{project.name}/{relative}")
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError(f"Packaged file mismatch: {relative}")
            source = (project / relative).read_bytes()
            if hashlib.sha256(source).hexdigest() != digest:
                # Git may convert text checkout line endings across Windows and
                # Linux. Archive hashes remain exact; permit only that change.
                source.decode("utf-8")
                data.decode("utf-8")
                if source.replace(b"\r\n", b"\n") != data.replace(b"\r\n", b"\n"):
                    raise ValueError(f"Source file mismatch: {relative}")


if __name__ == "__main__":
    for name in PROJECTS:
        build(name)
