"""Portable evidence bundle. Verification never executes code from a receipt."""
import json
from pathlib import Path
from .engine import evaluate, ENGINE_VERSION
from .store import digest, verify_ledger

DECISION_FIELDS=('employee_id','evaluation_date','work_jurisdiction','actual_hourly_wage','currency',
                 'controlling_minimum_wage','controlling_jurisdiction','controlling_rule_version','decision_state',
                 'hourly_shortfall','estimated_weekly_underpayment','source_url','supporting_evidence','reason_code','explanation')

def build_receipt(db,evaluation_id):
    row=db.execute('SELECT data FROM evaluations WHERE id=?',(evaluation_id,)).fetchone()
    if not row: raise ValueError('Evaluation not found')
    result=json.loads(row['data'])
    rules=result['candidate_applicable_rules']
    snapshots={}
    for rule in rules:
        snapshot=db.execute('SELECT * FROM snapshots WHERE id=?',(rule['snapshot_id'],)).fetchone()
        if snapshot: snapshots[rule['snapshot_id']]=dict(snapshot)
    body={'receipt_version':'atlas-receipt-v2','engine_version':ENGINE_VERSION,
          'engine_sha256':digest(Path(__file__).with_name('engine.py').read_text(encoding='utf-8')),
          'result':result,'rules_as_used':rules,'source_snapshots':snapshots,'ledger_checkpoint':verify_ledger(db),
          'trust_boundary':'Checksums establish consistency, not legal authority. Keep the receipt digest separately to detect replacement.'}
    return {'sha256':digest(body),'body':body}

def verify_receipt(receipt,expected_digest=None):
    errors=[]
    body=receipt.get('body',{})
    computed=digest(body)
    if computed!=receipt.get('sha256'): errors.append('Receipt checksum mismatch')
    if expected_digest and computed!=expected_digest: errors.append('Receipt differs from the external digest')
    if body.get('engine_version')!=ENGINE_VERSION: errors.append('Unsupported engine version')
    if body.get('engine_sha256')!=digest(Path(__file__).with_name('engine.py').read_text(encoding='utf-8')):
        errors.append('Engine source differs; use the matching committed implementation')
    for sid,snapshot in body.get('source_snapshots',{}).items():
        if digest(snapshot['raw_html'])!=snapshot['raw_hash']: errors.append('Source snapshot modified: '+sid)
    # Check each stored rule is exactly the candidate extracted from its bound source.
    from .extract import extract,PARSER_VERSION,candidate_identity
    for rule in body.get('rules_as_used',[]):
        snapshot=body.get('source_snapshots',{}).get(rule['snapshot_id'])
        if not snapshot:
            errors.append('Missing source for rule '+rule['id']);continue
        try:
            extracted,_,_=extract(snapshot['raw_html'],snapshot['source'])
            if not any(candidate_identity(c,rule['simulated'])==rule['id'] for c in extracted):
                errors.append('Rule is not bound to its source: '+rule['id'])
            original=next((c for c in extracted if candidate_identity(c,rule['simulated'])==rule['id']),None)
            if original and any(rule.get(k)!=v for k,v in original.items()): errors.append('Rule fields were changed after extraction')
        except ValueError as exc: errors.append('Source re-extraction failed: '+str(exc))
    try:
        stored=body['result']
        replay=evaluate(stored['employee_input'],body['rules_as_used'],stored['evaluation_date'],
                        stored['policy']['annual_salary_estimate'],stored.get('source_health_issues',[]))
        for field in DECISION_FIELDS:
            if replay.get(field)!=stored.get(field): errors.append('Replayed decision differs: '+field)
    except (KeyError,ValueError,TypeError) as exc: errors.append('Malformed receipt: '+str(exc))
    return {'valid':not errors,'errors':errors,'receipt_sha256':computed,'external_digest_checked':expected_digest is not None,
            'checks':['bundle checksum','source hashes','rule-to-source binding','matching engine','deterministic decision replay']}
