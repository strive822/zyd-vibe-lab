"""Compatibility entry: build four installable skill ZIPs outside the checkout."""
import argparse
from pathlib import Path
from package import build

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path.home() / '.codex/.tmp/graduation-thesis-release')
    for record in build(parser.parse_args().out):
        print(record['file'], record['sha256'])
