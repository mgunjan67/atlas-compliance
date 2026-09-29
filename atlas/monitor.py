import difflib
import json
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
    previous = db.execute('''SELECT s.*,f.id AS fetch_id FROM fetches f JOIN snapshots s ON s.id=f.snapshot_id
                             WHERE f.source=? AND f.simulated=? AND f.status!='ERROR'
                             ORDER BY f.id DESC LIMIT 1''',(source,int(simulated))).fetchone()
    if previous and previous['raw_hash']!=raw_hash:
        _, prior_observations, _ = extract(previous['raw_html'],source)
        unmapped=lambda items: next((x['text'] for x in items if x['kind']=='unmapped_text'),'')
        if unmapped(prior_observations)!=unmapped(observations) and not any(c['extraction_method']=='visible-content-guard' for c in parsed):
            raise ValueError('Visible content changed outside recognized publications; extraction review required')
    difference = '\n'.join(difflib.unified_diff((previous['semantic_text'] if previous else '').splitlines(),semantic_text.splitlines(),fromfile='previous',tofile='current',lineterm=''))
    status = 'INITIAL' if previous is None else ('UNCHANGED' if previous['semantic_hash']==semantic_hash else 'CHANGED')
    prior_identities = set()
    if previous:
        prior_rules, _, _ = extract(previous['raw_html'], source)
        prior_identities = {candidate_identity(c, simulated) for c in prior_rules}
    existing = [(r['id'], json.loads(r['data'])) for r in db.execute(
        'SELECT id,data FROM candidates WHERE simulated=? ORDER BY rowid', (int(simulated),))]
    new_ids = []
    with db:
        # Snapshot.diff remains the original capture's comparison for old receipts.
        # The authoritative comparison for each new check lives in fetch_diffs.
        db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                   (snapshot_id,source,SOURCES[source],retrieved_at,html,raw_hash,semantic_hash,semantic_text,difference,PARSER_VERSION,int(simulated)))
        for c in parsed:
            candidate_id = candidate_identity(c,simulated)
            matching = [(rid, data) for rid, data in existing
                        if data.get('source_candidate_id', rid)==candidate_id]
            if matching and previous and candidate_id not in prior_identities:
                # Returning content is a new occurrence for notices as well as
                # daily cards. A previous approval cannot approve its return.
                c = dict(c, source_candidate_id=candidate_id, recurrence_after_fetch=previous['fetch_id'])
                candidate_id = digest([candidate_id, 'recurrence', previous['fetch_id']])
            elif matching:
                candidate_id, c = matching[-1]
            changed = db.execute('INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?)',
                                 (candidate_id,snapshot_id,dumps(c),retrieved_at,int(simulated))).rowcount
            if changed: new_ids.append(candidate_id)
            db.execute('INSERT OR IGNORE INTO evidence_links VALUES(?,?)',(candidate_id,snapshot_id))
        db.execute('INSERT OR IGNORE INTO observations VALUES(?,?)',(snapshot_id,dumps(observations)))
        fetch_id = db.execute('INSERT INTO fetches(source,fetched_at,status,snapshot_id,detail,simulated) VALUES(?,?,?,?,?,?)',
                   (source,retrieved_at,status,snapshot_id,dumps(warnings),int(simulated))).lastrowid
        db.execute('INSERT INTO fetch_diffs VALUES(?,?,?)',
                   (fetch_id,previous['id'] if previous else None,difference))
        audit(db,'SOURCE_'+status,dict(source=source,snapshot_id=snapshot_id,fetch_id=fetch_id,
              previous_snapshot_id=previous['id'] if previous else None,diff_hash=digest(difference),
              new_candidates=new_ids,simulated=simulated),retrieved_at)
    return dict(source=source,status=status,snapshot_id=snapshot_id,fetch_id=fetch_id,new_candidates=new_ids)

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
