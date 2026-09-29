import hashlib
import json
import sqlite3
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path

def now():
    return datetime.now(timezone.utc).isoformat()

def dumps(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',',':'))

def digest(value):
    return hashlib.sha256((value if isinstance(value, str) else dumps(value)).encode()).hexdigest()

def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS snapshots (
        id TEXT PRIMARY KEY, source TEXT NOT NULL, url TEXT NOT NULL, retrieved_at TEXT NOT NULL,
        raw_html TEXT NOT NULL, raw_hash TEXT NOT NULL, semantic_hash TEXT NOT NULL,
        semantic_text TEXT NOT NULL, diff TEXT NOT NULL, parser_version TEXT NOT NULL, simulated INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS fetches (
        id INTEGER PRIMARY KEY, source TEXT NOT NULL, fetched_at TEXT NOT NULL, status TEXT NOT NULL,
        snapshot_id TEXT, detail TEXT NOT NULL, simulated INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS fetch_diffs (
        fetch_id INTEGER PRIMARY KEY REFERENCES fetches(id),
        previous_snapshot_id TEXT REFERENCES snapshots(id), diff TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS candidates (
        id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
        data TEXT NOT NULL, discovered_at TEXT NOT NULL, simulated INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY, candidate_id TEXT NOT NULL UNIQUE REFERENCES candidates(id),
        decision TEXT NOT NULL CHECK(decision IN ('APPROVED','REJECTED','ACKNOWLEDGED')),
        actor TEXT NOT NULL, reason TEXT NOT NULL, reviewed_at TEXT NOT NULL,
        supersedes TEXT REFERENCES candidates(id));
    CREATE TABLE IF NOT EXISTS evaluations (
        id TEXT PRIMARY KEY, employee_id TEXT NOT NULL, evaluation_date TEXT NOT NULL,
        created_at TEXT NOT NULL, data TEXT NOT NULL, simulated INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS result_views (
        evaluation_date TEXT PRIMARY KEY, saved_at TEXT NOT NULL, data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS review_batches (
        id TEXT PRIMARY KEY, evaluation_date TEXT NOT NULL, data TEXT NOT NULL,
        state TEXT NOT NULL, reviewed_at TEXT, actor TEXT, results TEXT);
    CREATE TABLE IF NOT EXISTS legacy_result_sets (
        id TEXT PRIMARY KEY, data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS batch_result_versions (
        id TEXT PRIMARY KEY, batch_id TEXT NOT NULL REFERENCES review_batches(id),
        saved_at TEXT NOT NULL, results TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS dummy_runs (
        id TEXT PRIMARY KEY, data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS evaluation_observations (
        id INTEGER PRIMARY KEY, evaluation_id TEXT NOT NULL REFERENCES evaluations(id), observed_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY, event TEXT NOT NULL, at TEXT NOT NULL, data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ledger (
        event_id INTEGER PRIMARY KEY REFERENCES audit(id), previous_hash TEXT NOT NULL, entry_hash TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS observations (
        snapshot_id TEXT NOT NULL REFERENCES snapshots(id), data TEXT NOT NULL, PRIMARY KEY(snapshot_id));
    CREATE TABLE IF NOT EXISTS evidence_links (
        candidate_id TEXT NOT NULL REFERENCES candidates(id), snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
        PRIMARY KEY(candidate_id,snapshot_id));
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL REFERENCES candidates(id), jurisdiction TEXT NOT NULL,
        effective_from TEXT, effective_to TEXT, due_date TEXT NOT NULL, reason TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'PENDING', attempts INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL, finished_at TEXT, error TEXT, result TEXT, simulated INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS flags (
        id TEXT PRIMARY KEY, employee_id TEXT NOT NULL, evaluation_date TEXT NOT NULL,
        status TEXT NOT NULL, evaluation_id TEXT NOT NULL REFERENCES evaluations(id),
        updated_at TEXT NOT NULL, simulated INTEGER NOT NULL,
        UNIQUE(employee_id,evaluation_date,simulated));
    CREATE TABLE IF NOT EXISTS ai_runs (
        id TEXT PRIMARY KEY, at TEXT NOT NULL, snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
        provider TEXT NOT NULL, model TEXT NOT NULL, response TEXT NOT NULL, validation TEXT NOT NULL);
    ''')
    return db

def audit(db, event, data, at=None):
    timestamp=at or now()
    row=db.execute('INSERT INTO audit(event,at,data) VALUES (?,?,?)',(event,timestamp,dumps(data)))
    event_id=row.lastrowid
    previous=db.execute('SELECT entry_hash FROM ledger ORDER BY event_id DESC LIMIT 1').fetchone()
    previous_hash=previous[0] if previous else '0'*64
    entry_hash=digest({'id':event_id,'event':event,'at':timestamp,'data':data,'previous_hash':previous_hash})
    db.execute('INSERT INTO ledger VALUES(?,?,?)',(event_id,previous_hash,entry_hash))
    return entry_hash

def candidates(db, known_at=None):
    rows = db.execute('''SELECT c.*, r.decision, r.actor, r.reason review_reason, r.reviewed_at, r.supersedes
                        FROM candidates c LEFT JOIN reviews r ON c.id=r.candidate_id ORDER BY c.rowid''')
    items=[]
    for r in rows:
        if known_at and r['discovered_at']>known_at: continue
        reviewed=bool(r['decision']) and (not known_at or r['reviewed_at']<=known_at)
        items.append(dict(json.loads(r['data']),id=r['id'],snapshot_id=r['snapshot_id'],discovered_at=r['discovered_at'],
                          state=r['decision'] if reviewed else 'REVIEW_REQUIRED',actor=r['actor'] if reviewed else None,
                          review_reason=r['review_reason'] if reviewed else None,reviewed_at=r['reviewed_at'] if reviewed else None,
                          supersedes=r['supersedes'] if reviewed else None,simulated=bool(r['simulated'])))
    return items

def review(db, candidate_id, decision, actor, reason, supersedes=None, allow_simulated=False, at=None, commit=True):
    if not actor.strip() or not reason.strip():
        raise ValueError('Reviewer name and reason are required')
    items = {c['id']:c for c in candidates(db)}
    c = items.get(candidate_id)
    if c is None: raise ValueError('Unknown candidate ID')
    if decision not in ('APPROVED','REJECTED','ACKNOWLEDGED'): raise ValueError('Invalid review decision')
    if c['state'] != 'REVIEW_REQUIRED':
        if c['state'] == decision and c['actor'] == actor and c['review_reason'] == reason and c['supersedes'] == supersedes: return
        raise ValueError('Reviews are immutable; ingest a correction rather than rewriting history')
    if not c['simulated'] and len(reason.strip()) < 25:
        raise ValueError('Live review reason must describe checked evidence or an explicit assumption (at least 25 characters)')
    if c['simulated'] and not allow_simulated:
        raise ValueError('Synthetic candidate: use the explicitly simulated demo workflow')
    if decision == 'APPROVED':
        if c['classification'] != 'RATE_REVIEW' or not c['amount'] or not c['effective_from']:
            raise ValueError('Only complete numerical rate candidates can be approved')
        if c.get('correction_required') and not supersedes:
            raise ValueError('A numerical correction must explicitly supersede an approved rule version')
        if supersedes:
            old = items.get(supersedes)
            if not old or old['state'] != 'APPROVED' or old['jurisdiction'] != c['jurisdiction'] or old['effective_from'] != c['effective_from'] or old['simulated'] != c['simulated']:
                raise ValueError('Correction must identify an approved same-jurisdiction, same-effective-date rule')
            if any(x['supersedes']==supersedes for x in items.values()):
                raise ValueError('Supersession already exists; supersede its replacement instead')
    elif supersedes:
        raise ValueError('Only approved corrections may supersede a rule')
    if decision == 'ACKNOWLEDGED' and c['classification'] == 'RATE_REVIEW':
        raise ValueError('Approve or reject numerical rules explicitly')
    if decision == 'ACKNOWLEDGED' and c['classification']=='SECURITY_REVIEW':
        raise ValueError('Quarantined content must be rejected; acknowledgment cannot activate it')
    if decision == 'ACKNOWLEDGED' and c.get('kind')=='UNKNOWN':
        raise ValueError('Unknown publication cannot be cleared by acknowledgment; investigate and explicitly reject unsupported evidence')
    timestamp=at or now()
    if timestamp<c['discovered_at']: raise ValueError('Review cannot precede discovery')
    with db if commit else nullcontext():
        db.execute('INSERT INTO reviews(candidate_id,decision,actor,reason,reviewed_at,supersedes) VALUES(?,?,?,?,?,?)',
                   (candidate_id,decision,actor,reason,timestamp,supersedes))
        audit(db,'RULE_'+decision,dict(candidate_id=candidate_id,actor=actor,reason=reason,supersedes=supersedes,simulated=c['simulated']),timestamp)
        # Review and its durable work item commit atomically. Future dates remain queued.
        due=max(timestamp[:10],c.get('effective_from') or timestamp[:10])
        db.execute('INSERT OR IGNORE INTO jobs(id,candidate_id,jurisdiction,effective_from,effective_to,due_date,reason,created_at,simulated) VALUES(?,?,?,?,?,?,?,?,?)',
                   (digest([candidate_id,decision]),candidate_id,c['jurisdiction'],c.get('effective_from'),c.get('effective_to'),due,
                    'CORRECTION' if supersedes else decision,timestamp,int(c['simulated'])))

def verify_ledger(db):
    previous='0'*64
    count=0
    for row in db.execute('SELECT a.*,l.previous_hash,l.entry_hash FROM audit a LEFT JOIN ledger l ON a.id=l.event_id ORDER BY a.id'):
        expected=digest({'id':row['id'],'event':row['event'],'at':row['at'],'data':json.loads(row['data']),'previous_hash':previous})
        if row['previous_hash']!=previous or row['entry_hash']!=expected:
            return {'valid':False,'events_checked':count,'failed_event':row['id'],'reason':'Unchained legacy event or modified audit record'}
        previous=row['entry_hash'];count+=1
    return {'valid':True,'events_checked':count,'head':previous,
            'limitation':'Local hash chain detects changes relative to a trusted checkpoint; it is not a signature or external notarization.'}
