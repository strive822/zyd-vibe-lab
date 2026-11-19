"""Offline checks of Git-visible files and all intentional delivery ZIPs.

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
import sys
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_KEY_PATTERN = r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
SECRET_PATTERNS = (
    PRIVATE_KEY_PATTERN,
    r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b",
    r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}\b",
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    r"https?://[^\s/@:]+:[^\s/@]+@",
)

# 上游安全测试自带的 user:pass@ 形状假样本 URL（非真实凭据），整文件豁免并注明理由。
SECRET_SCAN_EXEMPT = {
    "flyingmouse-format/tests/electron-security.test.js": "upstream security-test fixtures",
}
# Exact dummy URL userinfo used by endpoint validation and proxy parser fixtures.
SECRET_FIXTURE_HASHES = {
    "daozai/src/calendar.rs": {
        "288a54939d6ba40b4826b0549aa6a2067e121a9d442ab22486ea3611af155091",
    },
    "daozai/src/relay_quota.rs": {
        "7ddcba9e3e77c3b73ed526aa78b7b1219560d13715c1c1bfa6e4556b15e7096b",
    },
    "daozai/src/relay_script.rs": {
        "fbddae166ead16d1dd67736b19403ab1ac0095e344f663573848af911a7ce273",
    },
    "daozai/vendor/ureq/src/proxy.rs": {
        "77e530809b2c35131e1104f8851b8d501687febfe4135b58b2cfd11a72170d83",
    },
    "codegraph/source/__tests__/config-secret-redaction.test.ts": {
        "bd1bd021fd29d467adea4e03ad2d5a8340a16b5b9c82e645c9d83578f3be1523",
    },
    "agent-desktop/source/scripts/jev/run.test.mjs": {
        "ec25b8fa54a9d7a878a86e6f38233af24d5d27d184b396136d6d7f0251d33c19",
        "7f8183fd094a7b10753ce6a5f1a4388aa1afeda990c4134417045c78fcec9a2d",
    },
}
# Synthetic TLS keys are allowed only in exact upstream test files, across checkout line endings.
PRIVATE_KEY_FIXTURE_FILES = {
    "daozai/src/calendar/tls_test_certificates.json": "f1c8428c30047f8c29ea3887ea41d6cc815d85280821322a9513d8d9be17534a",
    "daozai/vendor/ureq/tests/https-agent.rs": "886100aed5e2603e50b6582d09dff2dce1f5c5cda2beb9481fb716bdf5697686",
}


CODEGRAPH_SITE_DOCS = "codegraph/source/site/src/content/docs/"
# Keep the pinned upstream Markdown byte-for-byte. These are a repo-relative
# self-link and a regex fragment mistaken for a link in multiline inline code.
UPSTREAM_MARKDOWN_EXCEPTIONS = {
    "codegraph/source/docs/benchmarks/residual-context-occupancy.md": {
        "docs/benchmarks/residual-context-occupancy.md",
    },
    "codegraph/source/docs/design/callback-edge-synthesis.md": {"""[^'"]+"""},
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def visible_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, check=True, capture_output=True,
    )
    return [ROOT / name for name in sorted(set(result.stdout.decode("utf-8").split("\0"))) if name and (ROOT / name).exists()]


def secret_check(data: bytes, label: str, errors: list[str]) -> None:
    text = data.decode("utf-8", errors="replace")
    allowed_fixtures = SECRET_FIXTURE_HASHES.get(label, ())
    fixture_hash = PRIVATE_KEY_FIXTURE_FILES.get(label)
    for pattern in SECRET_PATTERNS:
        if fixture_hash and pattern == PRIVATE_KEY_PATTERN and fixture_hash == digest(data.replace(b"\r\n", b"\n")):
            continue
        for match in re.finditer(pattern, text):
            if allowed_fixtures and digest(match.group().encode("utf-8")) in allowed_fixtures:
                continue
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f"{label}:{line}: possible secret (value suppressed)")


def zip_check(path: Path, errors: list[str]) -> None:
    with zipfile.ZipFile(path) as archive:
        seen: set[str] = set()
        for info in archive.infolist():
            name = PurePosixPath(info.orig_filename)
            if (name.is_absolute() or ".." in name.parts or "\\" in info.orig_filename
                    or ":" in info.orig_filename or stat.S_ISLNK(info.external_attr >> 16)):
                errors.append(f"{path.name}: unsafe ZIP entry {info.filename}")
            if info.filename.casefold() in seen:
                errors.append(f"{path.name}: duplicate ZIP entry {info.filename}")
            seen.add(info.filename.casefold())
            if not info.is_dir() and name.suffix in {".py", ".md", ".json", ".txt", ".ps1"}:
                secret_check(archive.read(info), f"{path.name}/{info.filename}", errors)
        if archive.testzip() is not None:
            errors.append(f"{path.name}: ZIP CRC failure")


def check_packages(errors: list[str]) -> None:
    from package_projects import PROJECTS, SOURCE_PROJECTS, verify
    for name in SOURCE_PROJECTS:
        verify(ROOT / name)
    catalog = json.loads((ROOT / 'releases.json').read_text(encoding='utf-8'))
    if set(catalog['projects']) != set(PROJECTS):
        errors.append('releases.json: project coverage mismatch')
    for name, release in catalog['projects'].items():
        if not release['tag'].startswith(name + '-v') or not release['assets']:
            errors.append(f'{name}: missing pinned Release assets')
        names = set()
        for asset in release['assets']:
            filename = asset['name']
            if Path(filename).name != filename or ':' in filename or '\\' in filename or filename.casefold() in names:
                errors.append(f'{name}: unsafe or duplicate asset name')
            names.add(filename.casefold())
            if not re.fullmatch('[0-9a-f]{64}', asset['sha256']) or asset['bytes'] <= 0:
                errors.append(f'{name}: invalid asset checksum/size')
        if 'sha256sums.txt' not in names:
            errors.append(f'{name}: missing downloadable checksums')


def check_file(path: Path, known: set[Path], errors: list[str]) -> list[str]:
    label = path.relative_to(ROOT).as_posix()
    if label == "agent-desktop/source/.claude":
        from package_projects import verify_agent_desktop_source_alias
        verify_agent_desktop_source_alias(path)
        return ["upstream source alias"]
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing file or unsupported symlink")
    data = path.read_bytes()
    checks = ["secret patterns"]
    if label not in SECRET_SCAN_EXEMPT:
        secret_check(data, label, errors)
    if path.suffix in {".zip", ".ofd"}:
        zip_check(path, errors)
        return checks + ["ZIP CRC/paths", "package/source SHA-256"]
    if path.suffix == ".webp":
        if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
            errors.append(f"{label}: invalid WebP signature")
        return checks + ["image signature"]
    if path.suffix in {".png", ".gif", ".jpg", ".jpeg"}:
        signatures = {".png": (b"\x89PNG\r\n\x1a\n",), ".gif": (b"GIF87a", b"GIF89a"),
                      ".jpg": (b"\xff\xd8\xff",), ".jpeg": (b"\xff\xd8\xff",)}
        if not data.startswith(signatures[path.suffix]):
            errors.append(f"{label}: invalid image signature")
        return checks + ["image signature"]
    if path.suffix in {".exe", ".bin", ".dll"}:
        if path.suffix in {".exe", ".dll"} and not data.startswith(b"MZ"):
            errors.append(f"{label}: invalid PE signature")
        return checks + ["binary blob"]
    if path.suffix == ".ico":
        if not data.startswith(b"\x00\x00\x01\x00"):
            errors.append(f"{label}: invalid ICO signature")
        return checks + ["ICO signature"]
    if path.suffix == ".mp4":
        if len(data) < 12 or data[4:8] != b"ftyp":
            errors.append(f"{label}: invalid MP4 signature")
        return checks + ["MP4 signature"]
    if path.suffix in {".ttf", ".otf", ".wav"}:
        valid = (data.startswith((b"\x00\x01\x00\x00", b"true", b"OTTO")) if path.suffix in {".ttf", ".otf"}
                 else len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE")
        if not valid:
            errors.append(f"{label}: invalid font/audio signature")
        return checks + ["font/audio signature"]
    if label.startswith("codegraph/source/src/extraction/wasm/") and path.suffix == ".wasm":
        if not data.startswith(b"\x00asm\x01\x00\x00\x00"):
            errors.append(f"{label}: invalid WebAssembly signature")
        return checks + ["WebAssembly signature"]
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
        text = re.sub(r"`[^`\n]*`", "", text)
        for url in re.findall(r"\]\(([^)]+)\)", text):
            url = unquote(url.split(' "')[0].strip("<>").split("#")[0])
            if not url or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", url):
                continue
            if url in UPSTREAM_MARKDOWN_EXCEPTIONS.get(label, ()):
                continue
            if label.startswith(CODEGRAPH_SITE_DOCS) and url.startswith("/codegraph/"):
                route = url.removeprefix("/codegraph/").rstrip("/")
                target = (ROOT / CODEGRAPH_SITE_DOCS / (route + ".md")).resolve()
            else:
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
        args.inventory.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"PASS: {len(files)} Git-visible files; local links, syntax, secret patterns and source/Release separation.")
    print("Projects:", dict(Counter(p.relative_to(ROOT).parts[0] for p in files)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
