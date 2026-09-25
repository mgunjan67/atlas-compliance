"""Capture only the two published HTML pages; never inspect site internals."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'federal': 'https://asterian-federal-wage-site.vercel.app/',
    'bellwether': 'https://bellwether-state-wage-site.vercel.app/',
}

if __name__ == '__main__':
    directory = ROOT / 'data' / 'research'
    directory.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        with urlopen(Request(url, headers={'User-Agent': 'AtlasAssessment/0.1'}), timeout=30) as response:
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError('Source too large')
            digest = hashlib.sha256(body).hexdigest()
            filename = name + '-' + digest[:12] + '.html'
            (directory / filename).write_bytes(body)
            metadata = {'source': name, 'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                        'sha256': digest, 'filename': filename, 'http_status': response.status,
                        'content_type': response.headers.get('Content-Type')}
            (directory / (name + '.json')).write_text(json.dumps(metadata, indent=2), encoding='utf-8')
            print(json.dumps(metadata))
