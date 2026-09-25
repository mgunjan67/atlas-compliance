import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from atlas.monitor import ingest
from atlas.operations import poll_once
from atlas.store import connect

ROOT = Path(__file__).resolve().parents[1]


class PollArchiveTests(unittest.TestCase):
    def test_poll_archives_results_and_provenance_without_approving_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = connect(root / 'atlas.sqlite3')
            try:
                for source in ('federal', 'bellwether'):
                    meta = json.loads((ROOT / 'data/research' / f'{source}.json').read_text(encoding='utf-8'))
                    html = (ROOT / 'data/research' / meta['filename']).read_text(encoding='utf-8')
                    ingest(db, source, html, meta['retrieved_at'])
                with patch('atlas.operations.fetch_source', side_effect=lambda db, source: {
                    'source': source, 'status': 'UNCHANGED', 'snapshot_id': 'saved-test-snapshot'}):
                    outcome = poll_once(db, ROOT / 'data/employees.csv', root / 'latest.json', root / 'archive',
                                        at=datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc))
                archive = Path(outcome['archive'])
                manifest = json.loads(Path(outcome['manifest']).read_text(encoding='utf-8'))
                results = json.loads(archive.read_text(encoding='utf-8'))
                self.assertEqual(len(results), 48)
                self.assertEqual(outcome['date'], '2026-09-24')
                self.assertEqual(outcome['summary']['counts'], {'REVIEW_REQUIRED': 48})
                self.assertEqual(manifest['archive_files_sha256'][archive.name], hashlib.sha256(archive.read_bytes()).hexdigest())
                self.assertTrue(archive.with_suffix('.csv').exists())
                self.assertTrue((root / 'latest.json').exists())
                self.assertEqual(db.execute("SELECT count(*) FROM audit WHERE event='LIVE_POLL_ARCHIVED'").fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT count(*) FROM reviews').fetchone()[0], 0)
            finally:
                db.close()


if __name__ == '__main__':
    unittest.main()
