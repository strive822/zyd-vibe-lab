"""Download every independent bundle at one Git ref and verify its public files.

Uses memory and disposable downloads only; never installs or starts a project.
Run: python scripts/verify_published.py --ref <published commit SHA>
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import stat
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import PurePosixPath
import zipfile

from package_projects import PROJECTS


def get(url: str) -> bytes:
    for attempt in range(3):
        # A request made while a push is still arriving can cache a 404 at the
        # edge. Retry the same official file with a fresh cache key, twice only.
        candidate = url if attempt == 0 else f"{url}?verification={time.time_ns()}"
        try:
            with urlopen(Request(candidate, headers={"User-Agent": "zyd-vibe-lab-verification/1"}), timeout=120) as response:
                return response.read()
        except HTTPError as error:
            if attempt == 2 or error.code not in {404, 429, 500, 502, 503, 504}:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(attempt + 1)
    raise RuntimeError("Download did not complete")


def verify(project: str, ref: str) -> str:
    base = f"https://raw.githubusercontent.com/strive822/zyd-vibe-lab/{ref}/{project}"
    checksum = get(base + "/delivery/SHA256SUMS.txt").decode("utf-8-sig").split()
    expected, filename = checksum
    if filename != project + ".zip":
        raise ValueError(f"{project}: unexpected download filename")
    data = get(base + "/delivery/" + filename)
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"{project}: published ZIP hash mismatch")
    manifest = json.loads(get(base + "/delivery/FILES.json"))
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = [entry.filename for entry in archive.infolist()]
        if len(names) != len(set(name.casefold() for name in names)):
            raise ValueError(f"{project}: duplicate archive entry")
        if set(names) != {f"{project}/{name}" for name in manifest}:
            raise ValueError(f"{project}: published manifest coverage mismatch")
        for entry in archive.infolist():
            path = PurePosixPath(entry.orig_filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in entry.orig_filename
                    or ":" in entry.orig_filename or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError(f"{project}: unsafe archive path")
        for name, digest in manifest.items():
            if hashlib.sha256(archive.read(f"{project}/{name}")).hexdigest() != digest:
                raise ValueError(f"{project}: published file hash mismatch: {name}")
        for name in ("README.md", "INSTALL.md"):
            if archive.read(f"{project}/{name}") != get(base + "/" + name):
                raise ValueError(f"{project}: bundled {name} differs from published source")
        if archive.testzip() is not None:
            raise ValueError(f"{project}: corrupt ZIP")
    return f"PASS {project}: downloaded {len(data)} bytes; {len(manifest)} files verified"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="main", help="Prefer an immutable published commit SHA")
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(lambda name: verify(name, args.ref), PROJECTS):
            print(result, flush=True)


if __name__ == "__main__":
    main()
