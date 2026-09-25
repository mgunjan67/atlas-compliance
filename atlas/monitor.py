import difflib
import time
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .extract import extract, SOURCES, PARSER_VERSION, candidate_identity
from .store import now, digest, dumps, audit

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect requires operator investigation: '+newurl)

def ingest(db, source, html, retrieved_at=None, simulated=False):
    retrieved_at = retrieved_at or now()
    raw_hash = digest(html)
    snapshot_id = digest([source,raw_hash,simulated,PARSER_VERSION])
    parsed, observations, warnings = extract(html, source)
    semantic_text = '\n'.join(x['text'] for x in observations)
    semantic_hash = digest(semantic_text)
    previous = db.execute('''SELECT s.* FROM fetches f JOIN snapshots s ON s.id=f.snapshot_id
                             WHERE f.source=? AND f.simulated=? AND f.status!='ERROR'
                             ORDER BY f.id DESC LIMIT 1''',(source,int(simulated))).fetchone()
    difference = '\n'.join(difflib.unified_diff((previous['semantic_text'] if previous else '').splitlines(),semantic_text.splitlines(),fromfile='previous',tofile='current',lineterm=''))
    status = 'INITIAL' if previous is None else ('UNCHANGED' if previous['semantic_hash']==semantic_hash else 'CHANGED')
    new_ids = []
    with db:
        db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                   (snapshot_id,source,SOURCES[source],retrieved_at,html,raw_hash,semantic_hash,semantic_text,difference,PARSER_VERSION,int(simulated)))
        for c in parsed:
            candidate_id = candidate_identity(c,simulated)
            changed = db.execute('INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?)',
                                 (candidate_id,snapshot_id,dumps(c),retrieved_at,int(simulated))).rowcount
            if changed: new_ids.append(candidate_id)
            db.execute('INSERT OR IGNORE INTO evidence_links VALUES(?,?)',(candidate_id,snapshot_id))
        db.execute('INSERT OR IGNORE INTO observations VALUES(?,?)',(snapshot_id,dumps(observations)))
        db.execute('INSERT INTO fetches(source,fetched_at,status,snapshot_id,detail,simulated) VALUES(?,?,?,?,?,?)',
                   (source,retrieved_at,status,snapshot_id,dumps(warnings),int(simulated)))
        audit(db,'SOURCE_'+status,dict(source=source,snapshot_id=snapshot_id,new_candidates=new_ids,simulated=simulated),retrieved_at)
    return dict(source=source,status=status,snapshot_id=snapshot_id,new_candidates=new_ids)

def fetch_source(db, source, attempts=3):
    if source not in SOURCES: raise ValueError('Unknown source')
    error = None
    for attempt in range(attempts):
        try:
            request = Request(SOURCES[source],headers={'User-Agent':'AtlasAssessment/0.1','Accept':'text/html'})
            with build_opener(NoRedirect).open(request, timeout=15) as response:
                if 'text/html' not in response.headers.get('Content-Type',''):
                    raise ValueError('Unexpected content type')
                body = response.read(2_000_001)
                if len(body)>2_000_000: raise ValueError('Response exceeds 2MB limit')
                html = body.decode('utf-8',errors='strict')
            try:
                return ingest(db,source,html)
            except ValueError as e:
                # Keep failed extraction evidence without creating proposed rules.
                sid = digest([source,digest(html),'parse-error',now()])
                with db:
                    db.execute('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                               (sid,source,SOURCES[source],now(),html,digest(html),'','','',PARSER_VERSION,0))
                    db.execute('INSERT INTO fetches(source,fetched_at,status,snapshot_id,detail) VALUES(?,?,?,?,?)',
                               (source,now(),'ERROR',sid,str(e)))
                    audit(db,'EXTRACTION_FAILED',dict(source=source,snapshot_id=sid,error=str(e)))
                return dict(source=source,status='ERROR',error=str(e))
        except Exception as e:
            error = str(e)
            if attempt+1<attempts: time.sleep(min(2**attempt,4))
    with db:
        db.execute('INSERT INTO fetches(source,fetched_at,status,detail) VALUES(?,?,?,?)',(source,now(),'ERROR',error))
        audit(db,'FETCH_FAILED',dict(source=source,error=error,attempts=attempts))
    return dict(source=source,status='ERROR',error=error)
