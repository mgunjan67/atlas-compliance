"""One operator decision for a captured federal/state daily-rate pair."""
import json
from .store import candidates, digest, dumps, now, review, audit
from .engine import run_evaluation, source_health
from .result_view import source_cleared


def capture_batch(db, checks, day):
    if len(checks)!=2 or {c['source'] for c in checks}!={'federal','bellwether'} or any(c['status']=='ERROR' for c in checks):
        return None
    items=candidates(db)
    pair=[]
    for check in sorted(checks,key=lambda c:c['source'],reverse=True):
        linked={r[0] for r in db.execute('SELECT candidate_id FROM evidence_links WHERE snapshot_id=?',(check.get('snapshot_id'),))}
        found=[c for c in items if c['id'] in linked and not c['simulated'] and c['source']==check['source'] and c['kind']=='DAILY_RATE' and c['classification']=='RATE_REVIEW' and c['effective_from']==day]
        if not found:return None
        # One snapshot can support multiple occurrences of the same publication.
        roots={c.get('source_candidate_id',c['id']) for c in found}
        if len(roots)!=1:return None
        pair.append(dict(found[-1],captured_snapshot_id=check['snapshot_id']))
    identity=digest([day,[c['id'] for c in pair]])
    existing=db.execute('SELECT id FROM review_batches WHERE id=?',(identity,)).fetchone()
    if existing:return identity
    if all(c['state']=='APPROVED' for c in pair):return None
    if any(c['state']=='REJECTED' for c in pair):return None
    with db:
        db.execute("UPDATE review_batches SET state='SUPERSEDED' WHERE evaluation_date=? AND state='REVIEW_REQUIRED'",(day,))
        db.execute('INSERT INTO review_batches VALUES(?,?,?,\'REVIEW_REQUIRED\',NULL,NULL,NULL)',(identity,day,dumps({'rules':pair,'captured_at':now()})))
        audit(db,'COMBINED_UPDATE_DISCOVERED',{'batch_id':identity,'rules':[c['id'] for c in pair],'evaluation_date':day})
    return identity


def batches(db):
    return [dict(r,**json.loads(r['data']),results=json.loads(r['results']) if r['results'] else None) for r in db.execute('SELECT * FROM review_batches ORDER BY evaluation_date DESC,rowid DESC')]


def approve_batch(db, batch_id, decision, actor, note, employees, day):
    if decision not in ('APPROVED','REJECTED'):raise ValueError('Choose approve or reject update')
    if not actor.strip():raise ValueError('Reviewer name is required')
    if decision=='REJECTED' and len(note.strip())<25:raise ValueError('Explain rejection in at least 25 characters')
    # Lock before checking current evidence so a poll cannot change the pair mid-approval.
    db.execute('BEGIN IMMEDIATE')
    try:
        row=db.execute('SELECT * FROM review_batches WHERE id=?',(batch_id,)).fetchone()
        if not row:raise ValueError('Unknown combined update')
        if row['state']!='REVIEW_REQUIRED':
            if row['state']!=decision:raise ValueError('This update has already been reviewed')
            db.rollback()
            return finish_batch(db,batch_id,employees)
        if row['evaluation_date']!=day:raise ValueError('This update is no longer current; check both websites again')
        if source_health(db,day):raise ValueError('Both sources must pass their checks before reviewing the update')
        pair=json.loads(row['data'])['rules']
        current={c['id']:c for c in candidates(db)}
        for c in pair:
            latest=db.execute('SELECT * FROM fetches WHERE source=? AND simulated=0 ORDER BY id DESC LIMIT 1',(c['source'],)).fetchone()
            if not latest or latest['status']=='ERROR' or not db.execute('SELECT 1 FROM evidence_links WHERE candidate_id=? AND snapshot_id=?',(c['id'],latest['snapshot_id'])).fetchone():
                raise ValueError('Source changed since this inspection; reload and review the latest pair')
        stamp=now()
        reason='Reviewed both saved sources together: '+ '; '.join(f"{c['jurisdiction']} {c['amount']} {c['currency']}/{c['unit']} effective {c['effective_from']}" for c in pair)+'. '+note
        for c in pair:
            candidate=current[c['id']]
            if candidate['state']=='APPROVED':continue
            replacements=[r for r in current.values() if r['state']=='APPROVED' and r['jurisdiction']==c['jurisdiction'] and r['effective_from']==c['effective_from'] and not any(x.get('supersedes')==r['id'] for x in current.values())]
            if len(replacements)>1:raise ValueError('Conflicting approved versions need explicit resolution')
            review(db,c['id'],decision,actor,reason,replacements[0]['id'] if replacements and decision=='APPROVED' else None,at=stamp,commit=False)
        if decision=='APPROVED':
            for obsolete in current.values():
                if obsolete['kind']=='DAILY_RATE' and not obsolete['simulated'] and obsolete['effective_from']==day and obsolete['state']=='REVIEW_REQUIRED' and obsolete['id'] not in {c['id'] for c in pair}:
                    review(db,obsolete['id'],'REJECTED',actor,'Replaced unapproved daily proposal while reviewing the latest captured federal and state update. '+reason,at=stamp,commit=False)
        payload=json.loads(row['data'])
        payload['employee_inputs']=employees
        db.execute('UPDATE review_batches SET data=? WHERE id=?',(dumps(payload),batch_id))
        db.execute('UPDATE review_batches SET state=?,reviewed_at=?,actor=? WHERE id=?',(decision,stamp,actor,batch_id))
        audit(db,'COMBINED_UPDATE_'+decision,{'batch_id':batch_id,'rules':[c['id'] for c in pair],'actor':actor,'reason':reason},stamp)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return finish_batch(db,batch_id,employees)


def finish_batch(db,batch_id,employees):
    row=db.execute('SELECT * FROM review_batches WHERE id=?',(batch_id,)).fetchone()
    if row['state']=='APPROVED' and not row['results']:
        from .workflow import process_jobs
        employees=json.loads(row['data']).get('employee_inputs',employees)
        process_jobs(db,employees,row['evaluation_date'])
        results=run_evaluation(db,employees,row['evaluation_date'])
        with db:
            db.execute('UPDATE review_batches SET results=? WHERE id=? AND results IS NULL',(dumps(results),batch_id))
            audit(db,'COMBINED_RESULTS_SAVED',{'batch_id':batch_id,'evaluation_ids':[r['evaluation_id'] for r in results]})
    return next(b for b in batches(db) if b['id']==batch_id)


def saved_sets(db):
    saved=[dict(id=b['id'],evaluation_date=b['evaluation_date'],reviewed_at=b['reviewed_at'],actor=b['actor'],rules=b['rules'],results=b['results'],legacy=False) for b in batches(db) if b['state']=='APPROVED' and b['results'] is not None]
    originals={b['id']:b for b in saved}
    for version in db.execute('SELECT * FROM batch_result_versions ORDER BY rowid'):
        original=originals.get(version['batch_id'])
        if original:
            original['result_label']='At approval'
            saved.append(dict(original,id=version['id'],parent_batch_id=original['id'],
                              result_label='Resolved results',result_saved_at=version['saved_at'],results=json.loads(version['results'])))
    legacy=[json.loads(r[0]) for r in db.execute('SELECT data FROM legacy_result_sets')]
    # Preserve earlier separately-approved history honestly; do not invent a joint approval.
    for date in db.execute('SELECT DISTINCT evaluation_date FROM flags WHERE simulated=0 ORDER BY evaluation_date DESC'):
        if any(b['evaluation_date']==date[0] for b in saved+legacy):continue
        rows=[json.loads(r[0]) for r in db.execute('SELECT e.data FROM flags f JOIN evaluations e ON e.id=f.evaluation_id WHERE f.simulated=0 AND f.evaluation_date=? ORDER BY f.employee_id',(date[0],))]
        if not source_cleared(rows):continue
        rulemap={r['id']:r for e in rows for r in e.get('candidate_applicable_rules',[]) if r.get('state')=='APPROVED' and r.get('kind')=='DAILY_RATE' and r.get('effective_from')==date[0]}
        superseded={r.get('supersedes') for r in rulemap.values()}
        rulemap={k:v for k,v in rulemap.items() if k not in superseded}
        if len(rulemap)!=2:continue
        if {r['jurisdiction'] for r in rulemap.values()}!={'Asteria','Bellwether'}:continue
        entry=dict(id='legacy-'+date[0],evaluation_date=date[0],reviewed_at=None,actor=None,rules=list(rulemap.values()),results=rows,legacy=True)
        with db:db.execute('INSERT OR IGNORE INTO legacy_result_sets VALUES(?,?)',(entry['id'],dumps(entry)))
        legacy.append(entry)
    return sorted(saved+legacy,key=lambda b:(b['evaluation_date'],b['reviewed_at'] or '',b.get('result_saved_at','')),reverse=True)


def save_resolved_results(db, rows, day):
    """Append a resolved version without rewriting the original approval snapshot."""
    if not source_cleared(rows):return None
    row=db.execute("SELECT * FROM review_batches WHERE state='APPROVED' AND evaluation_date=? ORDER BY rowid DESC LIMIT 1",(day,)).fetchone()
    if not row or not row['results']:return None
    original=json.loads(row['results'])
    if source_cleared(original):return None
    payload=json.loads(row['data'])
    if sorted(payload.get('employee_inputs',[]),key=lambda e:e['employee_id'])!=sorted([r['employee_input'] for r in rows],key=lambda e:e['employee_id']):return None
    # Attach only results still based on this inspection's approved numerical pair.
    rules={c['id']:c for r in rows for c in r['candidate_applicable_rules']}
    superseded={c.get('supersedes') for c in rules.values() if c['state']=='APPROVED'}
    if any(c['id'] not in rules or rules[c['id']]['state']!='APPROVED' or c['id'] in superseded for c in payload['rules']):return None
    identity=digest([row['id'],[r['evaluation_id'] for r in rows]])
    with db:
        inserted=db.execute('INSERT OR IGNORE INTO batch_result_versions VALUES(?,?,?,?)',(identity,row['id'],now(),dumps(rows))).rowcount
        if inserted:audit(db,'COMBINED_RESULTS_RESOLVED',{'batch_id':row['id'],'result_version_id':identity,'evaluation_ids':[r['evaluation_id'] for r in rows]})
    return identity


def inspection_details(db, saved):
    """Read original approval and capture metadata without rewriting history."""
    reason=None
    if not saved['legacy']:
        for event in db.execute("SELECT data FROM audit WHERE event='COMBINED_UPDATE_APPROVED' ORDER BY id DESC"):
            data=json.loads(event[0])
            if data.get('batch_id')==saved.get('parent_batch_id',saved['id']):
                reason=data.get('reason');break
    sources=[]
    for rule in saved['rules']:
        approval=db.execute('SELECT actor,reviewed_at,reason FROM reviews WHERE candidate_id=?',(rule['id'],)).fetchone()
        snapshot_id=rule.get('captured_snapshot_id') or rule.get('snapshot_id')
        snapshot=db.execute('SELECT retrieved_at FROM snapshots WHERE id=?',(snapshot_id,)).fetchone()
        sources.append(dict(jurisdiction=rule['jurisdiction'],amount=rule['amount'],version=rule['id'],
                            snapshot_id=snapshot_id,source_url=rule.get('source_url'),
                            captured_at=snapshot[0] if snapshot else None,
                            approval=dict(approval) if approval else None))
    return dict(actor=saved['actor'],reviewed_at=saved['reviewed_at'],reason=reason,sources=sources,
                employees_evaluated=len(saved['results']))
