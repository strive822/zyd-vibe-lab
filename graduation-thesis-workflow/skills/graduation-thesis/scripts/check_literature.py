"""Check literature verification records offline before thesis delivery."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


def source_url(value):
    if not isinstance(value, str) or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    try:
        url = urlsplit(value)
        host = (url.hostname or '').removesuffix('.').encode('idna').decode('ascii').lower()
        labels = host.split('.')
        return (
            url.scheme in ('http', 'https')
            and url.username is None
            and url.port != 0
            and len(labels) >= 2
            and labels[-1] not in ('example', 'invalid', 'localhost', 'local', 'test')
            and any(char.isalpha() for char in labels[-1])
            and '.'.join(labels[-2:]) not in ('example.com', 'example.net', 'example.org')
            and all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) for label in labels)
        )
    except ValueError:
        return False


def check_date(value):
    try:
        return date.fromisoformat(value).isoformat() == value
    except (TypeError, ValueError):
        return False


def check_search_log(root, value):
    if not isinstance(value, str) or not value.strip() or Path(value).is_absolute():
        return False
    path = (root / value).resolve()
    return path.is_relative_to(root) and path.is_file() and path.stat().st_size > 0


def audit(root):
    root = Path(root).resolve()
    evidence = json.loads((root / 'evidence.json').read_text(encoding='utf-8-sig'))
    if not isinstance(evidence, list) or any(not isinstance(item, dict) for item in evidence):
        raise ValueError('evidence.json must contain a list of evidence objects')
    papers = [item for item in evidence if item.get('kind') == 'literature']
    if not papers:
        return ['No literature evidence recorded']

    errors = []
    for paper in papers:
        label = f"Literature {paper.get('id', '?')}"
        check = paper.get('source_check')
        if not isinstance(check, dict):
            errors.append(f'{label}: missing source_check')
            continue

        provider = check.get('provider')
        checks = (
            (paper.get('verification') == 'checked', 'verification must be checked'),
            (source_url(paper.get('url')), 'invalid evidence URL'),
            (isinstance(provider, str) and provider.strip(), 'missing verification provider'),
            (source_url(check.get('record_url')), 'invalid record_url'),
            (check_date(check.get('checked_on')), 'invalid checked_on (YYYY-MM-DD required)'),
            (check.get('publication_status') in ('no_notice_found', 'corrected'),
             'publication status blocks citation as evidence'),
            (source_url(check.get('status_url')), 'invalid status_url'),
            (check_search_log(root, check.get('search_log_path')),
             'search log must be a nonempty file inside the project'),
        )
        errors.extend(f'{label}: {message}' for passed, message in checks if not passed)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    args = parser.parse_args()
    try:
        errors = audit(args.project)
    except (OSError, RuntimeError, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print('PASS: literature verification records are present. Check sources and claims separately.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
