"""Offline checks of Git-visible files and the four intentional delivery ZIPs.

Run from any directory with Python 3.11+. No dependency installation, account
queries or application launches. --inventory writes a per-file check summary.
Secret patterns are limited checks, not a guarantee of absence of secrets.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import stat
import subprocess
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = (
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b",
    r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}\b",
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    r"https?://[^\s/@:]+:[^\s/@]+@",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def visible_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True,
    )
    return [ROOT / name for name in sorted(set(result.stdout.decode("utf-8").split("\0"))) if name]


def secret_check(data: bytes, label: str, errors: list[str]) -> None:
    text = data.decode("utf-8", errors="replace")
    for pattern in SECRET_PATTERNS:
        for match in re.finditer(pattern, text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{label}:{line}: possible secret (value suppressed)")


def zip_check(path: Path, errors: list[str]) -> None:
    with zipfile.ZipFile(path) as archive:
        seen: set[str] = set()
        for info in archive.infolist():
            name = PurePosixPath(info.filename)
            if (name.is_absolute() or ".." in name.parts or "\\" in info.filename
                    or ":" in info.filename or stat.S_ISLNK(info.external_attr >> 16)):
                errors.append(f"{path.name}: unsafe ZIP entry {info.filename}")
            if info.filename.casefold() in seen:
                errors.append(f"{path.name}: duplicate ZIP entry {info.filename}")
            seen.add(info.filename.casefold())
            if not info.is_dir() and name.suffix in {".py", ".md", ".json", ".txt", ".ps1"}:
                secret_check(archive.read(info), f"{path.name}/{info.filename}", errors)
        if archive.testzip() is not None:
            errors.append(f"{path.name}: ZIP CRC failure")


def check_packages(errors: list[str]) -> None:
    usage = ROOT / "codex-usage"
    name = "usage-0.1.0-windows-x64.zip"
    expected, filename = (usage / "packages/SHA256SUMS.txt").read_text().strip().split()
    if filename != name or digest((usage / "packages" / name).read_bytes()) != expected:
        errors.append("codex-usage: archive SHA-256 mismatch")
    with zipfile.ZipFile(usage / "packages" / name) as archive:
        prefix = next(n.removesuffix("build-manifest.json") for n in archive.namelist()
                      if n.endswith("/build-manifest.json"))
        manifest = json.loads(archive.read(prefix + "build-manifest.json"))
        for relative, sha in json.loads(archive.read(prefix + "SHA256SUMS.json")).items():
            if digest(archive.read(prefix + relative)) != sha:
                errors.append(f"codex-usage: packaged file mismatch {relative}")
        for relative, sha in manifest["sources"].items():
            path = usage / "src" / relative
            if not path.is_file() or digest(path.read_bytes()) != sha:
                errors.append(f"codex-usage: portable/source mismatch {relative}; rebuild before publishing")

    thesis = ROOT / "graduation-thesis-workflow"
    for record in json.loads((thesis / "packages/checksums.json").read_text()):
        path = thesis / "packages" / record["file"]
        if digest(path.read_bytes()) != record["sha256"]:
            errors.append(f"{path.name}: archive SHA-256 mismatch")
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                source = thesis / "skills" / name if name != "graduation-thesis/LICENSE" else thesis / "LICENSE"
                expected_bytes = source.read_bytes()
                if name == "graduation-thesis/SKILL.md" and "workbuddy" in path.name:
                    text = expected_bytes.decode("utf-8").replace("\r\n", "\n")
                    extra = ("\ndescription_zh: Evidence-based undergraduate thesis workflow"
                             "\ndescription_en: Evidence-based undergraduate thesis workflow"
                             "\nversion: 0.3.0\nauthor: Graduation Thesis Workflow contributors\n---\n")
                    expected_bytes = text.replace("\n---\n", extra, 1).encode("utf-8")
                if archive.read(name) != expected_bytes:
                    errors.append(f"{path.name}: bundle/source mismatch {name}")


def check_file(path: Path, known: set[Path], errors: list[str]) -> list[str]:
    label = path.relative_to(ROOT).as_posix()
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing file or unsupported symlink")
    data = path.read_bytes()
    checks = ["secret patterns"]
    secret_check(data, label, errors)
    if path.suffix == ".zip":
        zip_check(path, errors)
        return checks + ["ZIP CRC/paths", "package/source SHA-256"]
    if path.suffix in {".png", ".gif"}:
        signatures = {".png": (b"\x89PNG\r\n\x1a\n",), ".gif": (b"GIF87a", b"GIF89a")}
        if not data.startswith(signatures[path.suffix]):
            errors.append(f"{label}: invalid image signature")
        return checks + ["image signature"]
    text = data.decode("utf-8-sig")
    checks.append("UTF-8")
    if path.suffix in {".py", ".spec"}:
        ast.parse(text, filename=label)
        checks.append("Python syntax")
    elif path.suffix == ".json":
        json.loads(text)
        checks.append("JSON")
    elif path.suffix == ".toml":
        tomllib.loads(text)
        checks.append("TOML")
    elif path.suffix == ".svg":
        ET.fromstring(text)
        checks.append("SVG XML")
    elif path.suffix == ".md":
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        for url in re.findall(r"\]\(([^)]+)\)", text):
            url = unquote(url.split(' "')[0].strip("<>").split("#")[0])
            if not url or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", url):
                continue
            target = (path.parent / url).resolve()
            if not target.is_relative_to(ROOT) or (target.is_file() and target not in known):
                errors.append(f"{label}: link depends on a file outside public checkout: {url}")
            elif not target.exists():
                errors.append(f"{label}: missing link {url}")
        checks.append("local Markdown links")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, help="Write a Markdown inventory after successful checks")
    args = parser.parse_args()
    files = visible_files()
    known = {p.resolve() for p in files}
    errors: list[str] = []
    rows = []
    for path in files:
        try:
            checks = check_file(path, known, errors)
            rows.append((path.relative_to(ROOT).as_posix(), checks))
        except (OSError, ValueError, SyntaxError, zipfile.BadZipFile, ET.ParseError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}")
    try:
        check_packages(errors)
    except (OSError, ValueError, KeyError, StopIteration, zipfile.BadZipFile) as exc:
        errors.append(f"delivery packages: {type(exc).__name__}")
    for error in errors:
        print("FAIL", error)
    if errors:
        return 1
    if args.inventory:
        lines = ["# 逐文件检查清单", "", "由 `python scripts/check_repository.py --inventory docs/FILE_AUDIT.md` 生成。",
                 "列出静态检查覆盖，不表示已逐行证明所有业务逻辑无缺陷；项目验证与边界见 REPOSITORY_CLEANUP_REPORT.md。",
                 "", "| 文件（相对仓库根目录） | 已执行静态检查 |", "| --- | --- |"]
        lines += [f"| `{name}` | {', '.join(checks)} |" for name, checks in rows]
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS: {len(files)} Git-visible files; local links, syntax, secret patterns and delivery packages.")
    print("Projects:", dict(Counter(p.relative_to(ROOT).parts[0] for p in files)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
