"""Build an isolated, replaceable-DLL Windows candidate without a packager dependency."""
from __future__ import annotations

from _paths import ROOT, SOURCE, EVIDENCE

import argparse
import hashlib
import importlib.metadata
import json
import os
import shutil
import struct
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path


PYTHON_SHA256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"
PYTHON_URL = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def imports(path: Path) -> list[str]:
    """Read PE import names; never load or execute DLLs while resolving the bundle."""
    data = path.read_bytes()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError(f"Not a PE file: {path.name}")
    count = struct.unpack_from("<H", data, pe + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe + 20)[0]
    optional = pe + 24
    directory = optional + (112 if struct.unpack_from("<H", data, optional)[0] == 0x20B else 96)
    import_rva = struct.unpack_from("<I", data, directory + 8)[0]
    if not import_rva:
        return []
    sections = []
    for index in range(count):
        header = optional + optional_size + index * 40
        size, rva, raw_size, offset = struct.unpack_from("<IIII", data, header + 8)
        sections.append((rva, max(size, raw_size), offset))
    def position(rva: int) -> int:
        for start, size, offset in sections:
            if start <= rva < start + size:
                return rva - start + offset
        raise ValueError(f"Unmapped PE address: {path.name}")
    offset, names = position(import_rva), []
    while any(data[offset:offset + 20]):
        name = position(struct.unpack_from("<I", data, offset + 12)[0])
        names.append(data[name:data.index(b"\0", name)].decode("ascii"))
        offset += 20
    return names


def copy_qt(packages: Path, site: Path) -> None:
    qt, shiboken = site / "PySide6", site / "shiboken6"
    available = {path.name.casefold(): path for parent in (qt, shiboken) for path in parent.glob("*.dll")}
    selected = [qt / f"{name}.pyd" for name in ("QtCore", "QtGui", "QtWidgets", "QtNetwork", "QtSvg")]
    selected += [qt / "plugins" / category / name for category, name in (
        ("platforms", "qwindows.dll"), ("imageformats", "qsvg.dll"),
        ("imageformats", "qico.dll"), ("tls", "qschannelbackend.dll"),
        ("styles", "qmodernwindowsstyle.dll"))]
    selected += list(shiboken.glob("*.pyd"))
    queue, visited = list(selected), set()
    while queue:
        path = queue.pop()
        if path in visited:
            continue
        visited.add(path)
        target = packages / path.relative_to(site)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        for name in imports(path):
            dependency = available.get(name.casefold())
            if dependency:
                queue.append(dependency)
            elif name.lower().startswith(("qt6", "pyside6", "shiboken6")):
                raise RuntimeError(f"Unresolved application dependency: {name}")
    for parent in (qt, shiboken):
        for path in parent.glob("*.py"):
            target = packages / path.relative_to(site)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    translations = packages / "PySide6" / "translations"
    translations.mkdir(exist_ok=True)
    shutil.copy2(qt / "translations" / "qtbase_zh_CN.qm", translations)
    shutil.copytree(site / "tzdata", packages / "tzdata", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("PySide6", "PySide6_Essentials", "shiboken6", "tzdata"):
        distribution = importlib.metadata.distribution(name)
        metadata = next(distribution.locate_file(path).parent for path in distribution.files if path.name == "METADATA")
        shutil.copytree(metadata, packages / metadata.name, ignore=shutil.ignore_patterns("RECORD", "INSTALLER"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path, default=EVIDENCE / "m6" / "portable-build.json")
    args = parser.parse_args()
    if os.name != "nt" or sys.version_info[:3] != (3, 12, 10):
        raise RuntimeError("Use the verified Windows Python 3.12.10 build environment")
    archive = ROOT / "packaging" / "cache" / "python-3.12.10-embed-amd64.zip"
    if not archive.exists() or digest(archive) != PYTHON_SHA256:
        raise RuntimeError("Download the official embedded runtime and verify its published digest first")
    files = [SOURCE / name for name in ("main.py", "countdown.py", "quota_visual.py", "palette_visual.py", "run_app.py", "repair_config.py")]
    files += sorted(path for path in (SOURCE / "usage_app").rglob("*") if path.is_file() and path.suffix in (".py", ".svg") and "__pycache__" not in path.parts)
    source = {path.relative_to(SOURCE).as_posix(): digest(path) for path in files}
    dependencies = {name: importlib.metadata.version(name) for name in ("PySide6", "PySide6_Essentials", "shiboken6", "tzdata")}
    build_inputs = {"sources": source, "pythonSha256": PYTHON_SHA256, "dependencies": dependencies,
                    "launcherSourceSha256": digest(ROOT / "packaging" / "Launcher.cs"),
                    "builderSha256": digest(Path(__file__)),
                    "documents": {name: digest(path) for name, path in (
                        ("README.md", ROOT / "packaging" / "README.md"),
                        ("SOP.md", ROOT / "docs" / "guides" / "SOP.md"), ("THIRD_PARTY.md", ROOT / "docs" / "guides" / "THIRD_PARTY.md"))}}
    candidate_hash = hashlib.sha256(json.dumps(build_inputs, sort_keys=True).encode()).hexdigest()
    output = args.out or ROOT / "dist" / f"usage-0.1.0-candidate-{candidate_hash[:12]}"
    output.mkdir(parents=True, exist_ok=False)  # Never replace another candidate.
    runtime, packages, application = output / "runtime", output / "packages", output / "app"
    runtime.mkdir()
    with zipfile.ZipFile(archive) as zip_file:
        zip_file.extractall(runtime)
    (runtime / "python312._pth").write_text("python312.zip\n.\n../packages\n../app\n", encoding="utf-8")
    (runtime / "qt.conf").write_text("[Paths]\nPrefix=../packages/PySide6\nPlugins=plugins\nTranslations=translations\n", encoding="utf-8")
    packages.mkdir()
    site = Path(importlib.metadata.distribution("PySide6").locate_file(""))
    copy_qt(packages, site)
    for path in files:
        target = application / path.relative_to(SOURCE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    shutil.copy2(ROOT / "packaging" / "README.md", output / "README.md")
    for name in ("SOP.md", "THIRD_PARTY.md"):
        shutil.copy2(ROOT / "docs" / "guides" / name, output / name)
    licenses = output / "licenses"
    shutil.copytree(ROOT / "packaging" / "cache" / "pyside-licenses", licenses / "Qt-for-Python")
    shutil.copy2(runtime / "LICENSE.txt", licenses / "Python-LICENSE.txt")
    from PySide6.QtWidgets import QApplication
    from PIL import Image
    from usage_app.desktop import tray_icon
    app = QApplication([])
    icon_path = output / "leaf.ico"
    png = output / "leaf.png"
    tray_icon().pixmap(48, 48).save(str(png))
    with Image.open(png) as icon:
        icon.save(icon_path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48)])
    png.unlink()
    compiler = Path(os.environ["WINDIR"]) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe"
    subprocess.run([str(compiler), "/nologo", "/target:winexe", "/platform:x64", "/reference:System.Windows.Forms.dll",
                    f"/win32icon:{icon_path}", f"/out:{output / 'usage.exe'}", str(ROOT / "packaging" / "Launcher.cs")], check=True)
    app.quit()
    manifest = {"builtAt": datetime.now(UTC).isoformat(), "candidateHash": candidate_hash,
                "python": {"version": "3.12.10", "url": PYTHON_URL, "sha256": PYTHON_SHA256,
                           "verification": "SHA-256 matches the official HTTPS-published Sigstore message digest; signature not independently verified"},
                "dependencies": dependencies, "buildInputs": build_inputs,
                "sources": source, "launcherSourceSha256": build_inputs["launcherSourceSha256"],
                "boundary": "Private candidate, not a release. Clean Windows, device and long-duration gates remain open; current reference-account checks are documented separately."}
    (output / "build-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    binary_hashes = {path.relative_to(output).as_posix(): digest(path) for path in sorted(output.rglob("*")) if path.is_file()}
    (output / "SHA256SUMS.json").write_text(json.dumps(binary_hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = Path(shutil.make_archive(str(output), "zip", output.parent, output.name))
    report = {"directory": str(output), "archive": str(zip_path), "sha256": digest(zip_path), "bytes": zip_path.stat().st_size,
              "candidateHash": candidate_hash, "files": len(binary_hashes)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
