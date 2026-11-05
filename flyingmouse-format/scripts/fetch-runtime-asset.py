"""Fetch the pinned upstream AVS3 helper into an explicit development build copy."""
import argparse
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--destination', type=Path, required=True)
args = parser.parse_args()
target = args.destination.resolve()
if target.exists():
    raise SystemExit('Destination already exists; existing work preserved')
url = 'https://raw.githubusercontent.com/LaoFeng-mouse/flyingmouse-format/e8d0827016192f980893b08c09920305ef089dab/bin/avs3/avs3RM0Decoder.exe'
with urlopen(Request(url, headers={'User-Agent':'zyd-pinned-runtime/1'}), timeout=60) as response:
    data = response.read()
if hashlib.sha256(data).hexdigest() != 'a38546b45ef82219533c0e18478764a334f8287395b0d590dcd6c876976edb84':
    raise SystemExit('Official asset SHA-256 mismatch')
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('xb') as output:
    output.write(data)
print('Verified AVS3 helper saved; nothing executed. Preserve bin/avs3/THIRD_PARTY_NOTICE.txt.')
