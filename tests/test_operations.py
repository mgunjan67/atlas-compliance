import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from atlas.monitor import ingest
from atlas.operations import poll_once
from atlas.store import connect, candidates, review
from atlas.demo import page
from atlas.engine import load_employees, run_evaluation

ROOT = Path(__file__).resolve().parents[1]


class PollArchiveTests(unittest.TestCase):
    def test_partial_poll_preserves_failed_jobs_and_retry_completes_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);db=connect(root/'atlas.sqlite3')
            try:
                people=load_employees(ROOT/'data/employees.csv')
                for source,amount in (('federal','10.00'),('bellwether','14.00')):
                    ingest(db,source,page(amount,source=source),retrieved_at='2026-09-24T10:00:00+00:00')
                for c in candidates(db):
                    if c['kind']=='DAILY_RATE':
                        review(db,c['id'],'APPROVED','Test reviewer','Isolated fixture: checked amount, date and source.',at='2026-09-24T11:00:00+00:00')
                run_evaluation(db,people,'2026-09-24')
                def unchanged(db,source):
                    return ingest(db,source,page('10.00' if source=='federal' else '14.00',source=source))
                with patch('atlas.operations.fetch_source',side_effect=unchanged):
                    with patch('atlas.workflow.run_evaluation',side_effect=OSError('Injected historical failure')):
                        outcome=poll_once(db,ROOT/'data/employees.csv',root/'latest.json',root/'archive',at=datetime(2026,9,25,12,tzinfo=timezone.utc))
                    self.assertEqual([c['status'] for c in outcome['checks']],['UNCHANGED','UNCHANGED'])
                    self.assertEqual([j['state'] for j in outcome['jobs']],['FAILED','FAILED'])
                    manifest=json.loads(Path(outcome['manifest']).read_text())
                    self.assertEqual(manifest['jobs'],outcome['jobs'])
                    self.assertEqual(len(json.loads(Path(outcome['archive']).read_text())),48)
                    retry=poll_once(db,ROOT/'data/employees.csv',root/'latest.json',root/'archive',at=datetime(2026,9,25,12,1,tzinfo=timezone.utc))
                self.assertEqual([j['state'] for j in retry['jobs']],['DONE','DONE'])
                self.assertEqual(db.execute("SELECT count(*) FROM jobs WHERE state='FAILED'").fetchone()[0],0)
                self.assertEqual(db.execute('SELECT count(*) FROM reviews').fetchone()[0],2)
                self.assertEqual(db.execute('SELECT count(*) FROM flags').fetchone()[0],96)
            finally:
                db.close()

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
