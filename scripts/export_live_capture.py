"""Preserve the latest successful live fetches as an offline, seedable evidence set."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from atlas.extract import SOURCES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='data/atlas-v2.sqlite3')
    parser.add_argument('--date', required=True, help='UTC retrieval date, YYYY-MM-DD')
    parser.add_argument('--output', default=None)
    args = parser.parse_args()
    destination = Path(args.output or f'data/research/{args.date}')
    db = sqlite3.connect(f'file:{Path(args.db).resolve().as_posix()}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    exports = []
    for source in SOURCES:
        row = db.execute('''SELECT s.url, s.retrieved_at, s.raw_html, s.raw_hash
            FROM fetches f JOIN snapshots s ON s.id=f.snapshot_id
            WHERE f.source=? AND f.simulated=0 AND f.status!='ERROR'
              AND substr(f.fetched_at,1,10)=?
            ORDER BY f.id DESC LIMIT 1''', (source, args.date)).fetchone()
        if row is None:
            raise ValueError(f'No successful {source} fetch on {args.date}')
        if row['url'] != SOURCES[source]:
            raise ValueError(f'Unexpected {source} URL')
        digest = hashlib.sha256(row['raw_html'].encode('utf-8')).hexdigest()
        if digest != row['raw_hash']:
            raise ValueError(f'{source} snapshot hash mismatch')
        filename = f'{source}-{digest[:12]}.html'
        exports.append((source, filename, dict(
            source=source, url=row['url'], retrieved_at=row['retrieved_at'],
            sha256=digest, filename=filename, http_status=200,
            content_type='text/html; charset=utf-8'), row['raw_html']))
    destination.mkdir(parents=True, exist_ok=True)
    for source, filename, manifest, html in exports:
        (destination / filename).write_text(html, encoding='utf-8')
        (destination / f'{source}.json').write_text(
            json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'directory': str(destination), 'sources': [x[0] for x in exports]}))


if __name__ == '__main__':
    main()
