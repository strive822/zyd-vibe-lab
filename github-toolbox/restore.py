from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import stat
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def checked_file(path: Path, record: dict) -> bool:
    return (path.is_file() and path.stat().st_size == record["bytes"]
            and sha256(path) == record["sha256"])


def download(record: dict, cache: Path) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / record["sha256"]
    if checked_file(destination, record):
        return destination
    request = urllib.request.Request(record["url"], headers={
        "User-Agent": "zyd-personal-toolbox/1", "Accept": "application/octet-stream",
    })
    with tempfile.NamedTemporaryFile(dir=cache, delete=False) as output:
        temporary = Path(output.name)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                shutil.copyfileobj(response, output)
        except BaseException:
            output.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        if not checked_file(temporary, record):
            raise ValueError("Download checksum/size mismatch: " + record["id"])
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def extract_zip(archive: Path, destination: Path, strip_root: bool = False) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        entries = []
        seen = set()
        for info in bundle.infolist():
            relative = PurePosixPath(info.filename)
            if (relative.is_absolute() or ".." in relative.parts
                    or "\\" in info.filename or ":" in info.filename
                    or stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError("Unsafe archive entry")
            entries.append((info, relative))
        if strip_root and len({relative.parts[0] for _, relative in entries}) != 1:
            raise ValueError("Expected one archive root")
        planned = []
        for info, relative in entries:
            parts = relative.parts[1:] if strip_root else relative.parts
            if not parts or info.is_dir():
                continue
            target = destination.joinpath(*parts)
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError("Archive path escapes destination")
            key = str(target).casefold()
            if key in seen or target.exists():
                raise ValueError("Archive entry collision")
            seen.add(key)
            planned.append((info, target))
        for info, target in planned:
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(info) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True, env={
        **os.environ, "NEXT_TELEMETRY_DISABLED": "1",
    })


def install(tool: str, destination: Path, assets: dict, cache: Path) -> None:
    def asset(name: str) -> Path:
        return download(assets[name], cache)

    if tool == "LibreTV":
        snapshot = ROOT / "packages" / "libretv-source.zip"
        if not checked_file(snapshot, assets["libretv-source"]):
            raise ValueError("Local source snapshot checksum mismatch")
        extract_zip(snapshot, destination / "source")
        shutil.copytree(ROOT / "profiles" / "LibreTV", destination, dirs_exist_ok=True)
        extract_zip(asset("node"), destination / "runtime", strip_root=True)
        defaults = json.loads((destination / "defaults.json").read_text(encoding="utf-8"))
        with (destination / "source" / ".env.local").open("x", encoding="utf-8") as stream:
            stream.write("PASSWORD=" + secrets.token_urlsafe(32) + "\n")
            stream.write("DEFAULT_SOURCES=" + json.dumps(defaults, ensure_ascii=False) + "\n")
        node = destination / "runtime" / "node.exe"
        npm_cli = destination / "runtime" / "node_modules" / "npm" / "bin" / "npm-cli.js"
        previous_path = os.environ.get("PATH", "")
        os.environ["PATH"] = str(node.parent) + os.pathsep + previous_path
        try:
            run([str(node), str(npm_cli), "ci", "--no-audit", "--no-fund"], destination / "source")
            for task in ("typecheck", "lint", "test", "build"):
                run([str(node), str(npm_cli), "run", task], destination / "source")
        finally:
            os.environ["PATH"] = previous_path
    elif tool == "yt-dlp":
        shutil.copy2(asset("yt-dlp"), destination / "yt-dlp.exe")
        extract_zip(asset("deno"), destination / "deno-package")
        shutil.copy2(destination / "deno-package" / "deno.exe", destination / "deno.exe")
        extract_zip(asset("ffmpeg"), destination / "ffmpeg-package", strip_root=True)
        for binary in (destination / "ffmpeg-package" / "bin").iterdir():
            if binary.is_file():
                shutil.copy2(binary, destination / binary.name)
        shutil.copytree(ROOT / "profiles" / "yt-dlp", destination, dirs_exist_ok=True)
        config = (f'--paths "{destination.as_posix()}/xiazai"\n'
                  f'--ffmpeg-location "{destination.as_posix()}"\n'
                  f'--js-runtimes "deno:{destination.as_posix()}/deno.exe"\n'
                  '--no-playlist\n--windows-filenames\n')
        (destination / "yt-dlp.conf").write_text(config, encoding="utf-8-sig")
        (destination / "xiazai").mkdir()
        run([str(destination / "yt-dlp.exe"), "--version"], destination)
        run([str(destination / "ffprobe.exe"), "-version"], destination)
        run([str(destination / "deno.exe"), "--version"], destination)
    elif tool == "rea":
        shutil.copy2(asset("rea-package"), destination / "rea-agents-6.7.0.tgz")
        shutil.copytree(ROOT / "profiles" / "rea", destination, dirs_exist_ok=True)
    elif tool == "Winhance":
        shutil.copy2(asset("winhance"), destination / "Winhance.Installer.exe")
        shutil.copytree(ROOT / "profiles" / "Winhance", destination, dirs_exist_ok=True)
    elif tool == "Windows-MCP":
        extract_zip(asset("windows-mcp-source"), destination / "source", strip_root=True)
        shutil.copytree(ROOT / "profiles" / "Windows-MCP", destination, dirs_exist_ok=True)
    else:
        raise ValueError("Unknown tool")


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore the personal Windows toolbox into a NEW directory.")
    parser.add_argument("tool", choices=["LibreTV", "yt-dlp", "rea", "Winhance", "Windows-MCP"])
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--cache", type=Path, default=ROOT / ".downloads")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("Run with Windows Python in PowerShell or CMD.")
    destination = args.destination.resolve()
    if destination.exists():
        parser.error("Destination already exists; choose a new directory. Existing data is never overwritten.")
    assets = {record["id"]: record for record in json.loads((ROOT / "assets.json").read_text(encoding="utf-8"))}
    destination.mkdir(parents=True)
    install(args.tool, destination, assets, args.cache.resolve())
    print("RESTORED:", args.tool, destination)
    print("No service, desktop shortcut, global Agent configuration or system optimization was started.")


if __name__ == "__main__":
    main()
