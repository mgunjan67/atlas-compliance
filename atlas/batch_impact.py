"""Read-only comparison of two complete federal/state rate pairs."""
import csv
import io
import json
from .engine import evaluate


def batch_impact(db, batch_id, employees):
    row=db.execute('SELECT * FROM review_batches WHERE id=?',(batch_id,)).fetchone()
    if not row:raise ValueError('Unknown combined update')
    proposed=json.loads(row['data'])['rules']
    previous=[]
    for old in db.execute("SELECT * FROM review_batches WHERE state='APPROVED' AND id!=? AND evaluation_date<=? ORDER BY evaluation_date DESC,rowid DESC",(batch_id,row['evaluation_date'])):
        previous.append(dict(date=old['evaluation_date'],at=old['reviewed_at'],rules=json.loads(old['data'])['rules']))
    for old in db.execute('SELECT data FROM legacy_result_sets'):
        old=json.loads(old[0])
        if old['evaluation_date']<=row['evaluation_date']:
            previous.append(dict(date=old['evaluation_date'],at=old.get('reviewed_at') or '',rules=old['rules']))
    baseline=max(previous,key=lambda b:(b['date'],b['at']),default=None)
    report=dict(batch_id=batch_id,evaluation_date=row['evaluation_date'],proposed_rates=proposed,
                previous_rates=baseline['rules'] if baseline else [],previous_date=baseline['date'] if baseline else None,
                comparison_available=baseline is not None,changed_hourly=None,newly_below=None,no_longer_below=None,
                unresolved_workers=len(employees),rows=[],preview_only=True,
                basis='Rate-only comparison of both pairs using the same employee inputs and test date. Earlier rates are comparison assumptions, not active rules. Final results follow review.')
    if not baseline:
        report['basis']='Comparison unavailable: no complete previous approved federal/state pair is saved.'
        return report
    def calculate(pair):
        rules=[dict(r,state='APPROVED',effective_from=row['evaluation_date'],effective_to=None,supersedes=None) for r in pair]
        return [evaluate(e,rules,row['evaluation_date']) for e in employees]
    before,after=calculate(baseline['rules']),calculate(proposed)
    report.update(changed_hourly=0,newly_below=0,no_longer_below=0,unresolved_workers=0)
    for b,a in zip(before,after):
        supported=all(r['decision_state'] in ('COMPLIANT','NON_COMPLIANT') for r in (b,a))
        changed=supported and any(b[k]!=a[k] for k in ('controlling_minimum_wage','decision_state','hourly_shortfall'))
        report['changed_hourly']+=int(changed)
        report['unresolved_workers']+=int(not supported)
        report['newly_below']+=int(supported and b['decision_state']=='COMPLIANT' and a['decision_state']=='NON_COMPLIANT')
        report['no_longer_below']+=int(supported and b['decision_state']=='NON_COMPLIANT' and a['decision_state']=='COMPLIANT')
        report['rows'].append(dict(employee_id=a['employee_id'],work_jurisdiction=a['work_jurisdiction'],
            hourly_wage=a['actual_hourly_wage'],previous_floor=b['controlling_minimum_wage'],new_floor=a['controlling_minimum_wage'],
            previous_decision=b['decision_state'],new_decision=a['decision_state'],changed=changed,
            comparison_available=supported))
    return report


def batch_impact_csv(report):
    output=io.StringIO(newline='')
    fields=['batch_id','evaluation_date','preview_only','employee_id','work_jurisdiction','hourly_wage',
            'previous_floor','new_floor','previous_decision','new_decision','changed','comparison_available']
    writer=csv.DictWriter(output,fieldnames=fields)
    writer.writeheader()
    for row in report['rows']:
        writer.writerow(dict(batch_id=report['batch_id'],evaluation_date=report['evaluation_date'],preview_only=True,**row))
    return output.getvalue()
