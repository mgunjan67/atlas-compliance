"""Vendor the open-license Inter families used for the Niural-inspired theme."""
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CSS_URL = 'https://fonts.googleapis.com/css2?family=Inter:wght@400..700&family=Inter+Tight:wght@400..700&display=swap'


def fetch(url):
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
    with urlopen(request, timeout=30) as response:
        return response.read()


if __name__ == '__main__':
    directory = ROOT / 'atlas/static/fonts'
    directory.mkdir(parents=True, exist_ok=True)
    stylesheet = fetch(CSS_URL).decode('utf-8')
    blocks = re.findall(r'/\* latin \*/\s*(@font-face\s*\{.*?\})', stylesheet, re.S)
    sources = []
    for family, slug in [('Inter', 'inter'), ('Inter Tight', 'intertight')]:
        block = next(b for b in blocks if "font-family: '" + family + "';" in b)
        url = re.search(r'url\((https://fonts.gstatic.com/[^)]+)\)', block).group(1)
        body = fetch(url)
        if body[:4] != b'wOF2':
            raise ValueError('Expected a WOFF2 font')
        (directory / (slug + '-latin.woff2')).write_bytes(body)
        license_url = f'https://raw.githubusercontent.com/google/fonts/main/ofl/{slug}/OFL.txt'
        (directory / (slug + '-OFL.txt')).write_bytes(fetch(license_url))
        sources.append({'family': family, 'url': url, 'license': license_url})
    (directory / 'sources.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')
    print(json.dumps(sources, indent=2))
