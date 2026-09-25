"""Reproducible reviewer workspace. Every approval here is explicitly simulated."""
import json
from pathlib import Path
from .store import candidates,review,audit,connect,verify_ledger
from .monitor import ingest
from .engine import load_employees,run_evaluation,export_results
from .workflow import process_jobs,impact_preview,summarize
from .receipt import build_receipt,verify_receipt

DAY='2026-09-24'
DISCOVERED='2026-09-24T10:00:00+00:00'
REVIEWED='2026-09-24T10:01:00+00:00'
CORRECTION_DISCOVERED='2026-09-25T09:00:00+00:00'
CORRECTION_REVIEWED='2026-09-25T09:01:00+00:00'
ROOT=Path(__file__).resolve().parents[1]

def research_html(source):
    meta=json.loads((ROOT/'data/research'/f'{source}.json').read_text(encoding='utf-8'))
    return (ROOT/'data/research'/meta['filename']).read_text(encoding='utf-8')

def bootstrap(db):
    """Idempotent baseline creation; never called with the live database by the app."""
    if any(not c['simulated'] for c in candidates(db)):
        raise ValueError('Refusing to seed simulated approvals into a live-source database')
    if any(c['simulated'] for c in candidates(db)): return {'status':'existing simulated workspace'}
    for source in ('federal','bellwether'):
        ingest(db,source,research_html(source),DISCOVERED,simulated=True)
    for c in candidates(db):
        if c['classification']=='RATE_REVIEW':
            decision='APPROVED';reason='SIMULATED reviewer: accept published rate for this replay; one-day card interval explicitly assumed.'
        elif c['classification']=='NOT_LAW':
            decision='REJECTED';reason='SIMULATED reviewer: proposal is not effective law.'
        else:
            decision='ACKNOWLEDGED'
            reason='SIMULATED reviewer: evidence reviewed; supplied Covered field treated as upstream coverage determination for this assessment.' if c['kind']=='CORRECTION' else 'SIMULATED reviewer: interpretive/informational evidence; not a numerical rule.'
        review(db,c['id'],decision,'SIMULATED assessment operator',reason,allow_simulated=True,at=REVIEWED)
    rows=load_employees(ROOT/'data/employees.csv')
    process_jobs(db,rows,DAY,simulated=True,evaluated_at='2026-09-24T10:02:00+00:00')
    results=run_evaluation(db,rows,DAY,simulated=True,evaluated_at='2026-09-24T10:02:00+00:00')
    return summarize(results)

def introduce_correction(db):
    if any(not c['simulated'] for c in candidates(db)): raise ValueError('Scenario injection is restricted to a simulated database')
    previous=next(c for c in candidates(db) if c['simulated'] and c['kind']=='DAILY_RATE' and c['source']=='bellwether' and c['amount']=='16.63')
    # Literal fixture mutation of captured public evidence; never a predicted publication.
    changed=research_html('bellwether').replace('16.63','18.50').replace('3.90','5.77')
    changed=changed.replace('State minimum wage', 'SIMULATED corrected state minimum wage',1)
    result=ingest(db,'bellwether',changed,CORRECTION_DISCOVERED,simulated=True)
    proposal=next(c for c in candidates(db) if c['simulated'] and c['kind']=='DAILY_RATE' and c['source']=='bellwether' and c['amount']=='18.50')
    return {'candidate_id':proposal['id'],'supersedes':previous['id'],'ingestion':result,'simulated':True,
            'description':'Synthetic next-day correction to the September 24 state rate; not an observed publication.'}

def full_story(path,output):
    """Use a fresh path so the pending-review stage cannot be skipped on repeat."""
    db=connect(path)
    if db.execute('SELECT count(*) FROM candidates').fetchone()[0]:
        db.close();raise ValueError('Story export requires a fresh database path; existing history is preserved')
    directory=Path(output);directory.mkdir(parents=True,exist_ok=True)
    try:
        bootstrap(db)
        employees=load_employees(ROOT/'data/employees.csv')
        before=run_evaluation(db,employees,DAY,simulated=True,evaluated_at='2026-09-24T10:02:00+00:00')
        chosen=next(r for r in before if r['employee_id']=='AST-0025')
        original_receipt=build_receipt(db,chosen['evaluation_id'])
        change=introduce_correction(db)
        preview=impact_preview(db,employees,change['candidate_id'],DAY,change['supersedes'])
        pending=run_evaluation(db,employees,DAY,simulated=True,evaluated_at='2026-09-25T09:00:30+00:00')
        review(db,change['candidate_id'],'APPROVED','SIMULATED assessment operator',
               'SIMULATED correction: source fixture changes the September 24 state floor to 18.50 AST/hour.',
               change['supersedes'],allow_simulated=True,at=CORRECTION_REVIEWED)
        jobs=process_jobs(db,employees,'2026-09-25',simulated=True,evaluated_at='2026-09-25T09:02:00+00:00')
        after=run_evaluation(db,employees,DAY,simulated=True,evaluated_at='2026-09-25T09:02:00+00:00')
        known_before=run_evaluation(db,employees,DAY,simulated=True,known_at='2026-09-24T10:02:00+00:00',evaluated_at='2026-09-25T09:03:00+00:00')
        new_chosen=next(r for r in after if r['employee_id']=='AST-0025')
        new_receipt=build_receipt(db,new_chosen['evaluation_id'])
        for name,rows in [('before',before),('pending',pending),('after',after),('known-before-correction',known_before)]:
            export_results(rows,directory/f'{name}.json')
        for name,receipt in [('original-receipt',original_receipt),('corrected-receipt',new_receipt)]:
            (directory/f'{name}.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
            (directory/f'{name}.sha256').write_text(receipt['sha256']+'\n',encoding='utf-8')
        report={'simulated':True,'before':summarize(before),'pending':summarize(pending),'after':summarize(after),
                'impact_preview':preview,'jobs':jobs,'original_receipt_after_correction':verify_receipt(original_receipt),
                'corrected_receipt':verify_receipt(new_receipt),'historical_knowledge_reproduced':
                [r['decision_state'] for r in before]==[r['decision_state'] for r in known_before],
                'audit_integrity':verify_ledger(db),'case_study':{'employee_id':'AST-0025','before':chosen['decision_state'],
                'after':new_chosen['decision_state'],'weekly_shortfall':new_chosen['estimated_weekly_underpayment']},
                'disclosure':'Captured source pages + synthetic correction + simulated approvals. Employee dataset is the supplied fictional dataset.'}
        (directory/'story-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (directory/'audit.json').write_text(json.dumps([dict(r) for r in db.execute('SELECT a.*,l.entry_hash,l.previous_hash FROM audit a JOIN ledger l ON l.event_id=a.id ORDER BY a.id')],indent=2),encoding='utf-8')
        return report
    finally: db.close()
