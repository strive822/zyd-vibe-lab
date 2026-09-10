"""Compare protected tokens in UTF-8 source drafts. Heuristic, not a semantic review."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def tokens(text):
    return {
        'numbers': Counter(re.findall(r'(?<!\w)[+-]?\d+(?:[.,]\d+)*(?:\s*[%％])?', text)),
        'citations': Counter(re.findall(r'\[[^\]\n]+\]|\\(?:cite\w*|ref|eqref)\{[^}]+\}', text)),
        'math': Counter(re.findall(r'\$\$[\s\S]*?\$\$|(?<!\$)\$[^$\n]+\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]', text)),
    }


def compare(before, after):
    a, b = tokens(before), tokens(after)
    return {key: {'removed': dict(a[key] - b[key]), 'added': dict(b[key] - a[key])}
            for key in a if a[key] != b[key]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before')
    parser.add_argument('after')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    before, after = Path(args.before), Path(args.after)
    if before.resolve() == after.resolve():
        parser.error('Preserve a separate original draft.')
    if before.suffix.lower() not in ('.md', '.txt', '.tex') or after.suffix.lower() not in ('.md', '.txt', '.tex'):
        parser.error('Use UTF-8 .md/.txt/.tex sources, not binary Word/PDF files.')
    a, b = before.read_bytes(), after.read_bytes()
    differences = compare(a.decode('utf-8-sig'), b.decode('utf-8-sig'))
    record = {'status': 'needs_review' if differences else 'no_token_changes',
              'before_sha256': hashlib.sha256(a).hexdigest(), 'after_sha256': hashlib.sha256(b).hexdigest(),
              'differences': differences,
              'notice': 'Heuristic only. Check meaning, units, attribution, negation and claim strength manually.'}
    with Path(args.out).open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(record['status'])
    return 1 if differences else 0


if __name__ == '__main__':
    raise SystemExit(main())
