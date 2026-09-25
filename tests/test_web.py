"""HTTP boundary regression: historical exports must match the selected knowledge."""
import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen,Request
from urllib.error import HTTPError,URLError
from atlas.__main__ import seed
from atlas.showcase import full_story,ROOT
from atlas.store import connect,candidates


class WebTests(unittest.TestCase):
    def test_historical_export_and_request_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            demo=folder/'demo.db'
            full_story(demo,folder/'evidence')
            live_db=folder/'live.db'
            db=connect(live_db)
            try:
                seed(db,ROOT/'data/research/2026-09-25')
                future_id=next(c['id'] for c in candidates(db) if c['source_rule_id']=='AFWA-2026-0042')
            finally:
                db.close()
            with socket.socket() as probe:
                probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
            process=subprocess.Popen([sys.executable,'-m','atlas','--db',str(folder/'live.db'),
                                      'serve','--port',str(port),'--demo-db',str(demo)],
                                     cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
                query=urlencode({'mode':'demo','date':'2026-09-24','known_at':'2026-09-24T10:02:00+00:00'})
                with urlopen(base+'/api/export?'+query) as response:old=json.load(response)
                with urlopen(base+'/api/export?mode=demo&date=2026-09-24') as response:current=json.load(response)
                self.assertEqual(next(r for r in old if r['employee_id']=='AST-0025')['decision_state'],'COMPLIANT')
                self.assertEqual(next(r for r in current if r['employee_id']=='AST-0025')['decision_state'],'NON_COMPLIANT')
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base+'/api/scenario',data=b'{"mode":"demo"}',method='POST'))
                self.assertEqual(caught.exception.code,403)
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base,headers={'Host':'untrusted.example'}))
                self.assertEqual(caught.exception.code,403)
                with urlopen(base+'/api/state?mode=live&date=2026-09-25') as response:
                    live=json.load(response)
                self.assertFalse(live['monitor']['running'])
                headers={'Content-Type':'application/json','X-Atlas-CSRF':live['csrf']}
                with urlopen(Request(base+'/api/monitor/stop',data=b'{"mode":"live"}',headers=headers,method='POST')) as response:
                    self.assertFalse(json.load(response)['running'])
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base+'/api/monitor/start',data=b'{"mode":"demo"}',headers=headers,method='POST'))
                self.assertEqual(caught.exception.code,400)
                future_review=json.dumps({'mode':'live','date':'2027-01-01','id':future_id,'decision':'APPROVED',
                                          'actor':'Test reviewer','reason':'Checked the saved final notice, future effective date and covered scope.'}).encode()
                with urlopen(Request(base+'/api/review',data=future_review,headers=headers,method='POST')) as response:
                    self.assertEqual(json.load(response)['jobs'],[])
                with urlopen(base+'/api/state?mode=live&date=2027-01-01') as response:
                    self.assertEqual(json.load(response)['summary']['total'],48)
                db=connect(live_db)
                try:
                    job=db.execute('SELECT state,due_date FROM jobs WHERE candidate_id=?',(future_id,)).fetchone()
                    self.assertEqual((job['state'],job['due_date']),('PENDING','2027-01-01'))
                    self.assertEqual(db.execute("SELECT count(*) FROM flags WHERE evaluation_date='2027-01-01'").fetchone()[0],0)
                finally:
                    db.close()
            finally:
                process.terminate();process.wait(timeout=5)


if __name__=='__main__':unittest.main()
