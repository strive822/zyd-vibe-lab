from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"node_modules", ".next", ".git", "__pycache__", ".pytest_cache"}


def source_files(source: Path):
    for directory in sorted(source.iterdir()):
        if directory.name in EXCLUDED:
            continue
        if directory.is_symlink():
            raise ValueError("Source symlinks are not supported")
        if directory.is_dir():
            yield from source_files(directory)
        elif (not directory.name.startswith(".env") or directory.name == ".env.example"):
            if directory.suffix != ".tsbuildinfo" and directory.name != "next-env.d.ts":
                yield directory


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only export of the personal profile; never exports PASSWORD.")
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    local = args.source.resolve()
    profiles = ROOT / "profiles"
    libretv = profiles / "LibreTV"
    libretv.mkdir(parents=True, exist_ok=True)
    for name in ("launcher.mjs", "open-browser.ps1", "notify.vbs", "start.vbs", "stop.vbs", "stop.mjs", "rebuild.cmd"):
        shutil.copy2(local / "LibreTV" / name, libretv / name)
    values = {}
    for line in (local / "LibreTV" / "source" / ".env.local").read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "DEFAULT_SOURCES":
            values = json.loads(value.strip().strip("'"))
    (libretv / "defaults.json").write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source = local / "LibreTV" / "source"
    packages = ROOT / "packages"
    packages.mkdir(exist_ok=True)
    snapshot = packages / "libretv-source.zip"
    inventory = {}
    with zipfile.ZipFile(snapshot, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in source_files(source):
            name = path.relative_to(source).as_posix()
            content = path.read_bytes()
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, content)
            inventory[name] = hashlib.sha256(content).hexdigest()
    (packages / "libretv-files.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    for tool, filename in (("LibreTV", "LICENSE"), ("rea", "LICENSE"), ("Windows-MCP", "LICENSE.md")):
        origin = local / tool / ("source" if tool != "Windows-MCP" else "") / filename
        target = profiles / tool / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
    print("Exported", len(inventory), "LibreTV source files and personal launchers; no password exported.")


if __name__ == "__main__":
    main()
