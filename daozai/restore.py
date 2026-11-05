"""Verify fixed artifacts and copy this source snapshot to a new directory only."""
# Copyright (c) 2026 zhongyudi. SPDX-License-Identifier: MIT
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
def restore(destination: Path) -> None:
    root = ROOT.resolve()
    destination = destination.resolve()
    if destination.exists() or destination.is_relative_to(root):
        raise ValueError("Destination must be new and outside the source directory")
    manifest = json.loads((root / "assets.json").read_text(encoding="utf-8"))
    files = []
    for name in manifest["source_files"]:
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
            raise ValueError("Invalid snapshot path")
        source = root
        for part in relative.parts:
            source = source / part
            if source.is_symlink() or getattr(source.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError("Linked snapshot entries are not supported")
        if not source.is_file():
            raise ValueError("Missing snapshot file: " + name)
        files.append(source)
    for asset in manifest["artifacts"]:
        path = root / asset["file"]
        if path.stat().st_size != asset["bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError("Artifact checksum mismatch: " + asset["file"])
    destination.mkdir(parents=True, exist_ok=False)
    for source in files:
        if source.is_file():
            target = destination / source.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    restore(parser.parse_args().destination)
    print("PASS: source and fixed artifacts copied; nothing installed or started")
