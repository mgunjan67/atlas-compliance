"""Impact analysis and durable, jurisdiction-scoped re-evaluation."""
import json
from collections import Counter
from decimal import Decimal
from .engine import evaluate, run_evaluation, money, source_health
from .store import candidates, now, audit, dumps

def affected(employees, jurisdiction):
    if jurisdiction=='Asteria': return [e for e in employees if e.get('work_country')=='Asteria']
    return [e for e in employees if e.get('work_country')=='Asteria' and e.get('work_state')==jurisdiction]

def summarize(results):
    values=[Decimal(r['estimated_weekly_underpayment']) for r in results if r.get('estimated_weekly_underpayment') is not None]
    return {'counts':dict(Counter(r['decision_state'] for r in results)),
            'estimated_weekly_shortfall':money(sum(values,Decimal(0))),
            'employees_with_weekly_estimate':len(values),'total':len(results)}

def impact_preview(db, employee_rows, candidate_id, day, supersedes=None, annualize_salary=False):
    all_rules=candidates(db)
    candidate=next((r for r in all_rules if r['id']==candidate_id),None)
    if not candidate: raise ValueError('Unknown rule candidate')
    if candidate['classification']!='RATE_REVIEW': raise ValueError('Impact preview requires a numerical candidate')
    all_rules=[r for r in all_rules if r['simulated']==candidate['simulated']]
    before_rules=[r for r in all_rules if r['id']!=candidate_id]
    hypothetical=dict(candidate,state='APPROVED',supersedes=supersedes,actor='PREVIEW ONLY',review_reason='Not an approval')
    after_rules=before_rules+[hypothetical]
    employees=affected(employee_rows,candidate['jurisdiction'])
    issues=source_health(db,day,candidate['simulated'])
    def check(e,rules):
        sources=['federal']+(['bellwether'] if e.get('work_state')=='Bellwether' else [])
        return evaluate(e,rules,day,annualize_salary,[s+': '+issues[s] for s in sources if s in issues])
    before=[check(e,before_rules) for e in employees]
    after=[check(e,after_rules) for e in employees]
    current=[check(e,all_rules) for e in employees]
    changes=[]
    for b,a in zip(before,after):
        if any(b.get(k)!=a.get(k) for k in ('decision_state','controlling_minimum_wage','estimated_weekly_underpayment')):
            changes.append({'employee_id':a['employee_id'],'before':b['decision_state'],'after':a['decision_state'],
                            'floor_before':b['controlling_minimum_wage'],'floor_after':a['controlling_minimum_wage'],
                            'weekly_before':b['estimated_weekly_underpayment'],'weekly_after':a['estimated_weekly_underpayment']})
    bs,as_=summarize(before),summarize(after)
    return {'candidate_id':candidate_id,'evaluation_date':day,'preview_only':True,
            'basis':'Before excludes only this proposal; after hypothetically approves it. Other unresolved cases stay blocked.',
            'affected_employees':len(employees),'unaffected_employees':len(employee_rows)-len(employees),
            'before':bs,'after':as_,'current_with_pending':summarize(current),
            'weekly_shortfall_delta':money(Decimal(as_['estimated_weekly_shortfall'])-Decimal(bs['estimated_weekly_shortfall'])),
            'comparability_note':'Delta covers supported estimates only; compare coverage counts as well as totals.',
            'changes':changes,'simulated':candidate['simulated']}

def process_jobs(db, employee_rows, day, simulated=False, annualize_salary=False, evaluated_at=None):
    """Restart-safe at-least-once work. Result and flag identities make retries safe."""
    jobs=[dict(r) for r in db.execute("SELECT * FROM jobs WHERE state IN ('PENDING','RUNNING','FAILED') AND due_date<=? AND simulated=? ORDER BY created_at,id",(day,int(simulated)))]
    completed=[]
    for job in jobs:
        with db:
            db.execute("UPDATE jobs SET state='RUNNING',attempts=attempts+1,error=NULL WHERE id=?",(job['id'],))
        try:
            selected=affected(employee_rows,job['jurisdiction'])
            ids={e['employee_id'] for e in selected}
            def covers(d): return (not job['effective_from'] or job['effective_from']<=d) and (not job['effective_to'] or d<job['effective_to'])
            batches={day:selected} if covers(day) else {}
            # Replay existing historical employee snapshots, not today's wages at old dates.
            history={}
            for row in db.execute('SELECT * FROM evaluations WHERE simulated=? AND evaluation_date<? ORDER BY created_at,id',(int(simulated),day)):
                old_input=json.loads(row['data'])['employee_input']
                if affected([old_input],job['jurisdiction']) and covers(row['evaluation_date']):
                    history.setdefault(row['evaluation_date'],{})[row['employee_id']]=old_input
                    ids.add(row['employee_id'])
            for d,inputs in history.items(): batches[d]=list(inputs.values())
            output=[]
            for d,employees in sorted(batches.items()):
                output.extend(run_evaluation(db,employees,d,annualize_salary,simulated,evaluated_at=evaluated_at))
            details={'employee_population':len(ids),'evaluations':len(output),'dates':sorted(batches),
                     'evaluation_ids':[r['evaluation_id'] for r in output],
                     'limitation':'Historical backfill covers stored evaluations only; unobserved employee history is not invented.'}
            with db:
                db.execute("UPDATE jobs SET state='DONE',finished_at=?,result=? WHERE id=?",(evaluated_at or now(),dumps(details),job['id']))
                audit(db,'REEVALUATION_COMPLETED',{'job_id':job['id'],**details,'simulated':simulated},evaluated_at)
            completed.append({'job_id':job['id'],'state':'DONE',**details})
        except Exception as exc:
            with db:
                db.execute("UPDATE jobs SET state='FAILED',error=? WHERE id=?",(str(exc),job['id']))
                audit(db,'REEVALUATION_FAILED',{'job_id':job['id'],'error':str(exc),'simulated':simulated})
            completed.append({'job_id':job['id'],'state':'FAILED','error':str(exc)})
    return completed
