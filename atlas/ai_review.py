"""Durable advisory queue, isolated from the rule and employee database."""
import hashlib
import json
import sqlite3
import threading
import time
from contextlib import contextmanager,closing
from datetime import datetime,timezone
from pathlib import Path
from .ai_provider import VERSION,MODEL,AIUnavailable,api_key,suggest
from .extract import suspicious

def stamp():return datetime.now(timezone.utc).isoformat()

class AIReview:
    def __init__(self,db_path,runner=suggest,key_check=api_key):
        self.source=Path(db_path).resolve()
        self.path=self.source.with_name(self.source.stem+'-ai.sqlite3')
        self.runner=runner
        self.key_check=key_check
        self.stop=threading.Event()
        self.thread=None
        self.error=None

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=2)
        db.row_factory=sqlite3.Row
        try:
            with db:
                db.execute('CREATE TABLE IF NOT EXISTS suggestions (id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, version TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL, next_at REAL NOT NULL, data TEXT NOT NULL)')
                yield db
        finally:db.close()

    def scan(self):
        # Read-only URI prevents accidental migration or writes to live decisions.
        with closing(sqlite3.connect(self.source.as_uri()+'?mode=ro',uri=True,timeout=2)) as source:
            rows=source.execute('SELECT id,snapshot_id,data FROM candidates WHERE simulated=0 ORDER BY rowid DESC').fetchall()
        with self.connect() as db:
            for candidate_id,snapshot_id,raw in rows:
                candidate=json.loads(raw)
                text=candidate.get('evidence','')
                identity=hashlib.sha256((candidate_id+VERSION).encode()).hexdigest()
                blocked=suspicious(text) or candidate.get('classification')=='SECURITY_REVIEW'
                data={'candidate_id':candidate_id,'snapshot_id':snapshot_id,'source_url':candidate.get('source_url'),
                      'evidence_sha256':hashlib.sha256(text.encode()).hexdigest(),'segments':[{'id':1,'text':text}],
                      'parser_kind':candidate.get('kind'),'parser_classification':candidate.get('classification'),
                      'model':MODEL,'prompt_version':VERSION,'created_at':stamp()}
                if blocked:data['error']='Instruction-like content quarantined; inspect the source. AI was not called.'
                db.execute('INSERT OR IGNORE INTO suggestions VALUES(?,?,?,?,?,?,?)',
                    (identity,candidate_id,VERSION,'quarantined' if blocked else 'queued',0,0,json.dumps(data)))

    def process_one(self):
        with self.connect() as db:
            row=db.execute("SELECT * FROM suggestions WHERE version=? AND status IN ('queued','retrying') AND next_at<=? ORDER BY rowid LIMIT 1",(VERSION,time.time())).fetchone()
            if not row:return False
            data=json.loads(row['data'])
            attempts=row['attempts']+1
            db.execute("UPDATE suggestions SET status='running',attempts=? WHERE id=?",(attempts,row['id']))
        started=time.monotonic()
        try:
            result=self.runner(data['segments'])
            data.update(result=result,finished_at=stamp(),seconds=round(time.monotonic()-started,2))
            data.pop('error',None)
            status,next_at='done',0
        except Exception as exc:
            retry=isinstance(exc,AIUnavailable) and exc.retryable and attempts<3
            status='retrying' if retry else 'unavailable'
            next_at=time.time()+60*attempts if retry else 0
            data.update(error=str(exc) if isinstance(exc,AIUnavailable) else 'AI unavailable; inspect the source evidence.',finished_at=stamp())
        with self.connect() as db:
            db.execute('UPDATE suggestions SET status=?,next_at=?,data=? WHERE id=?',(status,next_at,json.dumps(data),row['id']))
        return True

    def status(self,candidate_id):
        if self.error:return {'status':'unavailable','error':'AI suggestion storage unavailable; source review is still available.'}
        if not self.path.exists():return {'status':'unavailable','error':'AI unavailable; source review is still available.'}
        try:
            with self.connect() as db:
                row=db.execute('SELECT status,attempts,data FROM suggestions WHERE candidate_id=? AND version=?',(candidate_id,VERSION)).fetchone()
            if not row:return {'status':'queued' if self.key_check() else 'unavailable','error':'AI unavailable: configure GROQ_API_KEY on the server.' if not self.key_check() else ''}
            status=row['status'];data=json.loads(row['data'])
            if status in ('queued','retrying') and not self.key_check():
                return {**data,'status':'unavailable','error':'AI unavailable: configure GROQ_API_KEY on the server.'}
            return {**data,'status':status,'attempts':row['attempts']}
        except sqlite3.Error:return {'status':'unavailable','error':'AI suggestion storage unavailable; source review is still available.'}

    def start(self):
        self.thread=threading.Thread(target=self._run,name='atlas-ai-review',daemon=True)
        self.thread.start()

    def _run(self):
        try:
            with self.connect() as db:
                db.execute("UPDATE suggestions SET status=CASE WHEN attempts<3 THEN 'queued' ELSE 'unavailable' END WHERE status='running'")
        except sqlite3.Error:self.error='AI storage unavailable'
        while not self.stop.is_set():
            try:
                self.scan()
                if self.key_check():self.process_one()
                self.error=None
            except (sqlite3.Error,OSError,ValueError):self.error='AI storage unavailable'
            self.stop.wait(5)

    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=.2)
