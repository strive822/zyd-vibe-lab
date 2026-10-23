from __future__ import annotations

import argparse
import functools
import http.cookiejar
import http.server
import json
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


def verify_libretv(root: Path) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    node = root / "runtime/node.exe"
    command = [str(node), str(root / "source/node_modules/next/dist/bin/next"),
               "start", "--hostname", "127.0.0.1", "--port", str(port)]
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(command, cwd=root / "source", stdout=log, stderr=log)
        try:
            for attempt in range(90):
                if process.poll() is not None:
                    raise RuntimeError("Verification server exited early")
                try:
                    with urllib.request.urlopen(base + "/api/status", timeout=2) as response:
                        status = json.load(response)
                    break
                except (OSError, urllib.error.URLError):
                    time.sleep(1)
            else:
                raise RuntimeError("Verification server timed out")
            assert status["version"] == "2.19.7" and status["passwordRequired"]
            assert len(status["defaultSources"]) == 2
            with urllib.request.urlopen(base, timeout=10) as response:
                assert response.status == 200
            try:
                urllib.request.urlopen(base + "/.env.local", timeout=10)
            except urllib.error.HTTPError as error:
                assert error.code == 404
            else:
                raise AssertionError("Local environment file is publicly accessible")
            password = next(line.partition("=")[2] for line in
                            (root / "source/.env.local").read_text(encoding="utf-8").splitlines()
                            if line.startswith("PASSWORD="))
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            request = urllib.request.Request(base + "/api/auth",
                                             data=json.dumps({"password": password}).encode(),
                                             headers={"Content-Type": "application/json"})
            with opener.open(request, timeout=10) as response:
                assert json.load(response)["success"]
            with opener.open(base + "/api/auth", timeout=10) as response:
                assert json.load(response)["verified"]
            print("PASS LibreTV: isolated server, status, home, private env 404, password login and session")
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


def verify_download(root: Path) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        media = directory / "toolbox-verification.wav"
        subprocess.run([str(root / "ffmpeg.exe"), "-v", "error", "-f", "lavfi", "-i",
                        "sine=frequency=440:duration=1", str(media)], check=True)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            command = [str(root / "yt-dlp.exe"), "--config-locations", str(root / "yt-dlp.conf"),
                       "-x", "--audio-format", "mp3", "--output", "toolbox-verification.%(ext)s",
                       f"http://127.0.0.1:{server.server_port}/{media.name}"]
            output = root / "xiazai/toolbox-verification.mp3"
            if output.exists():
                raise ValueError("Verification output already exists; use a fresh restore")
            subprocess.run(command, cwd=root, check=True)
            result = subprocess.run([str(root / "ffprobe.exe"), "-v", "error", "-show_entries",
                                     "format=duration", "-of", "json", str(output)],
                                    check=True, capture_output=True, text=True)
            assert float(json.loads(result.stdout)["format"]["duration"]) > 0
            print("PASS yt-dlp: synthetic local HTTP media, default xiazai path, FFmpeg MP3 and ffprobe")
            output.unlink()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a freshly restored disposable copy, never the daily instance.")
    parser.add_argument("--libretv", type=Path)
    parser.add_argument("--yt-dlp", type=Path)
    args = parser.parse_args()
    if args.libretv:
        verify_libretv(args.libretv.resolve())
    if args.yt_dlp:
        verify_download(args.yt_dlp.resolve())


if __name__ == "__main__":
    main()
