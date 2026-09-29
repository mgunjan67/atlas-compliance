"""HTTP boundary regression: historical exports must match the selected knowledge."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode
from urllib.request import urlopen,Request
from urllib.error import HTTPError,URLError
from atlas.__main__ import seed
from atlas.showcase import ROOT
from atlas.batches import capture_batch,approve_batch
from atlas.engine import load_employees
from atlas.store import connect,candidates
from atlas.monitor import ingest


class WebTests(unittest.TestCase):
    def test_historical_export_and_request_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            live_db=folder/'live.db'
            db=connect(live_db)
            try:
                seed(db,ROOT/'data/research/2026-09-25')
                checks=[dict(r) for r in db.execute('SELECT source,status,snapshot_id FROM fetches')]
                first_batch=capture_batch(db,checks,'2026-09-25')
                with patch('atlas.batches.source_health',return_value={}):
                    saved=approve_batch(db,first_batch,'APPROVED','Test reviewer','Inspected both saved sources.',load_employees(ROOT/'data/employees.csv'),'2026-09-25')
                # Cosmetic HTML creates a new snapshot but retains the candidate.
                old=db.execute("SELECT raw_html FROM snapshots WHERE source='federal' LIMIT 1").fetchone()[0]
                ingest(db,'federal',old+'<!-- harmless layout revision -->')
                future_id=next(c['id'] for c in candidates(db) if c['source_rule_id']=='AFWA-2026-0042')
            finally:
                db.close()
            with socket.socket() as probe:
                probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
            process=subprocess.Popen([sys.executable,'-m','atlas','--db',str(folder/'live.db'),
                                      'serve','--port',str(port)],
                                     cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                     env={**os.environ,'ATLAS_AI_DISABLED':'1'})
            base=f'http://127.0.0.1:{port}'
            try:
                deadline=time.monotonic()+8
                while True:
                    try:
                        with urlopen(base,timeout=1) as response:self.assertEqual(response.status,200)
                        break
                    except URLError:
                        if time.monotonic()>deadline:raise
                        time.sleep(.05)
                with urlopen(base+'/api/saved-results?'+urlencode({'id':first_batch,'download':'1'})) as response:
                    exported=json.load(response)
                self.assertEqual([r['evaluation_id'] for r in exported['results']],[r['evaluation_id'] for r in saved['results']])
                self.assertEqual(exported['id'],first_batch)
                self.assertEqual(len(exported['results']),48)
                with self.assertRaises(HTTPError) as caught:
                    urlopen(base+'/api/state?mode=demo')
                self.assertEqual(caught.exception.code,400)
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base+'/api/scenario',data=b'{"mode":"demo"}',method='POST'))
                self.assertEqual(caught.exception.code,403)
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base,headers={'Host':'untrusted.example'}))
                self.assertEqual(caught.exception.code,403)
                with urlopen(base+'/api/state?mode=live&date=2026-09-25') as response:
                    live=json.load(response)
                self.assertFalse(live['monitor']['running'])
                daily=next(c for c in live['candidates'] if c['source']=='federal' and c['kind']=='DAILY_RATE')
                latest=next(f for f in live['fetches'] if f['source']=='federal')
                self.assertNotEqual(daily['snapshot_id'],latest['snapshot_id'])
                self.assertTrue(daily['seen_in_latest_check'])
                with urlopen(base+'/api/monitor/status') as response:
                    self.assertFalse(json.load(response)['checking'])
                with urlopen(base+'/api/ai-review?'+urlencode({'id':daily['id']})) as response:
                    self.assertEqual(json.load(response)['status'],'unavailable')
                headers={'Content-Type':'application/json','X-Atlas-CSRF':live['csrf']}
                with urlopen(Request(base+'/api/monitor/stop',data=b'{"mode":"live"}',headers=headers,method='POST')) as response:
                    self.assertFalse(json.load(response)['running'])
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base+'/api/monitor/start',data=b'{"mode":"demo"}',headers=headers,method='POST'))
                self.assertEqual(caught.exception.code,400)
                future_review=json.dumps({'mode':'live','date':'2027-01-01','id':future_id,'decision':'APPROVED',
                                          'actor':'Test reviewer','reason':'Checked the saved final notice, future effective date and covered scope.'}).encode()
                with urlopen(Request(base+'/api/review',data=future_review,headers=headers,method='POST')) as response:
                    self.assertTrue(all('2027-01-01' not in job.get('dates',[]) for job in json.load(response)['jobs']))
                with urlopen(base+'/api/state?mode=live&date=2027-01-01') as response:
                    self.assertEqual(json.load(response)['summary']['total'],48)
                db=connect(live_db)
                try:
                    job=db.execute('SELECT state,due_date FROM jobs WHERE candidate_id=?',(future_id,)).fetchone()
                    self.assertEqual((job['state'],job['due_date']),('PENDING','2027-01-01'))
                    self.assertEqual(db.execute("SELECT count(*) FROM flags WHERE evaluation_date='2027-01-01'").fetchone()[0],0)
                finally:
                    db.close()
                for route in ('/api/replay/start','/api/scenario'):
                    with self.assertRaises(HTTPError) as caught:
                        urlopen(Request(base+route,data=b'{"mode":"live"}',headers=headers,method='POST'))
                    self.assertEqual(caught.exception.code,404)
                with self.assertRaises(HTTPError) as caught:
                    urlopen(base+'/api/rule-results?id=removed')
                self.assertEqual(caught.exception.code,404)
                self.assertEqual(len(list(folder.glob('*demo*'))),0)
                self.assertEqual(len(list(folder.glob('replay-session-*'))),0)
                db=connect(live_db)
                try:
                    self.assertFalse(any(c['simulated'] for c in candidates(db)))
                    self.assertEqual(db.execute('SELECT count(*) FROM reviews').fetchone()[0],3)
                finally:db.close()
            finally:
                process.terminate();process.wait(timeout=5)


if __name__=='__main__':unittest.main()
