"""Fetch real Crossref metadata. Does not fetch or verify paper full text."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


def make_url(command, query, limit=10):
    if command == 'doi':
        doi = query.strip()
        for prefix in ('https://doi.org/', 'http://doi.org/', 'doi:'):
            if doi.lower().startswith(prefix):
                doi = doi[len(prefix):].strip()
                break
        if not doi.startswith('10.') or '/' not in doi or any(c.isspace() for c in doi):
            raise ValueError('Provide a real DOI beginning with 10. and containing /.')
        return 'https://api.crossref.org/works/' + quote(doi, safe='')
    if not query.strip() or not 1 <= limit <= 100:
        raise ValueError('Query must be nonempty and limit must be 1..100.')
    return 'https://api.crossref.org/works?' + urlencode({'query.bibliographic': query, 'rows': limit})


def fetch(url):
    request = Request(url, headers={'User-Agent': 'graduation-thesis/0.1.0', 'Accept': 'application/json'})
    with urlopen(request, timeout=30) as response:
        raw = response.read(20_000_001)
    if len(raw) > 20_000_000:
        raise ValueError('Response too large; reduce result count.')
    body = json.loads(raw)
    if body.get('status') != 'ok' or not isinstance(body.get('message'), dict):
        raise ValueError('Unexpected Crossref response; not accepted as search evidence.')
    return raw, body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['search', 'doi'])
    parser.add_argument('query')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        url = make_url(args.command, args.query, args.limit)
        out = Path(args.out)
        raw_path = out.with_suffix(out.suffix + '.raw.json')
        if out.exists() or raw_path.exists():
            raise ValueError('Output already exists; use a new search/run filename.')
        raw, body = fetch(url)
        message = body['message']
        items = message.get('items', []) if args.command == 'search' else [message]
        result = {
            'provider': 'Crossref', 'query_url': url,
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'read_scope': 'metadata', 'fulltext_verified': False,
            'raw_sha256': hashlib.sha256(raw).hexdigest(), 'raw_file': raw_path.name,
            'candidates': [{
                'title': item.get('title', []), 'authors': item.get('author', []),
                'doi': item.get('DOI'), 'url': item.get('URL'),
                'published': item.get('published'), 'container_title': item.get('container-title', []),
                'type': item.get('type'), 'update_to': item.get('update-to', []),
                'verification': 'candidate_only',
            } for item in items],
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        with raw_path.open('xb') as stream:
            stream.write(raw)
        with out.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print(f'Saved {len(items)} metadata candidates to {out}; full text NOT verified.')
    except (OSError, ValueError, HTTPError, URLError) as exc:
        print(f'Retrieval failed: {exc}. No substitute results generated.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
