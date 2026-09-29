"""Impact analysis and durable, jurisdiction-scoped re-evaluation."""
import json
import csv
import io
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


def rate_change_report(db, employee_rows, candidate_id, supersedes=None, known_at=None):
    """Read-only, rate-only comparison; never extends an expired rule for real decisions."""
    all_rules=candidates(db,known_at)
    candidate=next((r for r in all_rules if r['id']==candidate_id),None)
    if not candidate or candidate['classification']!='RATE_REVIEW' or not candidate.get('amount') or not candidate.get('effective_from'):
        raise ValueError('A complete numerical rate candidate is required')
    scoped=[r for r in all_rules if r['simulated']==candidate['simulated']]
    approved=[r for r in scoped if r['state']=='APPROVED' and r['classification']=='RATE_REVIEW']
    replaced={r['supersedes'] for r in approved if r.get('supersedes')}
    predecessor_id=supersedes or candidate.get('supersedes')
    if predecessor_id:
        previous=next((r for r in approved if r['id']==predecessor_id and r['jurisdiction']==candidate['jurisdiction']
                       and r['effective_from']==candidate['effective_from']),None)
        if not previous: raise ValueError('Previous correction rate must be approved for the same date and jurisdiction')
    else:
        eligible=[r for r in approved if r['jurisdiction']==candidate['jurisdiction']
                  and r['effective_from']<candidate['effective_from'] and r['id'] not in replaced]
        latest=max((r['effective_from'] for r in eligible),default=None)
        latest_rules=[r for r in eligible if r['effective_from']==latest]
        conflict=len({(r['amount'],r['currency'],r['unit']) for r in latest_rules})>1
        previous=sorted(latest_rules,key=lambda r:r['id'])[0] if latest_rules and not conflict else None
    people=affected(employee_rows,candidate['jurisdiction'])
    report={'candidate_id':candidate_id,'evaluation_date':candidate['effective_from'],
            'jurisdiction':candidate['jurisdiction'],'approval_state':candidate['state'],
            'previous_rate':({k:previous.get(k) for k in ('id','source_rule_id','amount','effective_from','effective_to','source_url')} if previous else None),
            'new_rate':{k:candidate.get(k) for k in ('id','source_rule_id','amount','effective_from','effective_to','source_url')},
            'rate_delta':money(Decimal(candidate['amount'])-Decimal(previous['amount'])) if previous else None,
            'in_jurisdiction':len(people),'rows':[],'changed_hourly':0,'unresolved_workers':0,
            'potentially_affected_unresolved':0,
            'newly_below':0,'no_longer_below':0,'weekly_estimate_delta':'0.00',
            'basis':'Rate-only comparison at the new effective date. The earlier daily amount is carried forward solely as a counterfactual; it is not an active legal rule. Employee inputs and other approved jurisdiction rates are held fixed. Pending source and policy issues may still block actual decisions.'}
    if not previous:
        report['basis']='Previous approved rates conflict; resolve them before comparing employee impact.' if not predecessor_id and conflict else 'No earlier approved rate exists for this jurisdiction, so a before/after worker comparison is unavailable.'
        report['weekly_estimate_delta']=None
        report['comparison_available']=False
        return report
    # Keep the other jurisdiction's approved rate on the evaluation date, but replace
    # this jurisdiction's rate in both hypothetical branches. No DB rows are written.
    other=[r for r in approved if r['jurisdiction']!=candidate['jurisdiction']]
    comparison=dict(previous,id='comparison:'+previous['id'],effective_from=candidate['effective_from'],
                    effective_to=candidate.get('effective_to'),supersedes=None)
    proposed=dict(candidate,state='APPROVED',supersedes=None)
    def reference_floor(work_state,rules):
        # A canonical hourly input asks the decision engine for the location's
        # controlling rate. Its result is a reference, never an employee finding.
        reference={'employee_id':'RATE-REFERENCE','work_country':'Asteria','work_state':work_state,
                   'currency':'AST','minimum_wage_coverage':'Covered','employment_status':'Active',
                   'start_date':candidate['effective_from'],'scheduled_hours_per_week':'1',
                   'pay_basis':'Hourly','hourly_rate_ast':'0','annual_salary_ast':''}
        return evaluate(reference,rules,candidate['effective_from'])['controlling_minimum_wage']
    references={state:(reference_floor(state,other+[comparison]),reference_floor(state,other+[proposed]))
                for state in {e.get('work_state') for e in people}}
    total_delta=Decimal(0)
    for e in people:
        before=evaluate(e,other+[comparison],candidate['effective_from'])
        after=evaluate(e,other+[proposed],candidate['effective_from'])
        supported=(e.get('pay_basis')=='Hourly' and before['decision_state'] in ('COMPLIANT','NON_COMPLIANT')
                   and after['decision_state'] in ('COMPLIANT','NON_COMPLIANT'))
        changed=supported and (before['controlling_minimum_wage']!=after['controlling_minimum_wage']
                               or before['estimated_weekly_underpayment']!=after['estimated_weekly_underpayment']
                               or before['decision_state']!=after['decision_state'])
        if changed: report['changed_hourly']+=1
        if not supported: report['unresolved_workers']+=1
        previous_floor,new_floor=references[e.get('work_state')]
        reference_changed=previous_floor is not None and new_floor is not None and previous_floor!=new_floor
        if not supported and reference_changed:report['potentially_affected_unresolved']+=1
        if supported and before['decision_state']!='NON_COMPLIANT' and after['decision_state']=='NON_COMPLIANT':report['newly_below']+=1
        if supported and before['decision_state']=='NON_COMPLIANT' and after['decision_state']!='NON_COMPLIANT':report['no_longer_below']+=1
        weekly_before=before['estimated_weekly_underpayment'] if supported else None
        weekly_after=after['estimated_weekly_underpayment'] if supported else None
        weekly_delta=money(Decimal(weekly_after)-Decimal(weekly_before)) if weekly_before is not None and weekly_after is not None else None
        if weekly_delta is not None:total_delta+=Decimal(weekly_delta)
        report['rows'].append({'employee_id':e['employee_id'],'work_state':e.get('work_state'),
                               'pay_basis':e.get('pay_basis'),'recorded_hourly_wage':before['actual_hourly_wage'] if supported else None,
                               'scheduled_hours_per_week':e.get('scheduled_hours_per_week'),
                               'previous_floor':previous_floor,'new_floor':new_floor,
                               'previous_decision':before['decision_state'],'new_decision':after['decision_state'],
                               'previous_weekly_estimate':weekly_before,'new_weekly_estimate':weekly_after,
                               'weekly_estimate_delta':weekly_delta,'changed':changed,
                               'reference_floor_changed':reference_changed,
                               'note':None if supported else 'Floor is a location reference only; actual wage impact requires separate employee or policy review.'})
    report['weekly_estimate_delta']=money(total_delta)
    return report


def rate_change_csv(report):
    fields=('comparison_date','candidate_id','approval_state','previous_rule_id','new_rule_id',
            'previous_rate','new_rate','employee_id','work_state','pay_basis','recorded_hourly_wage','scheduled_hours_per_week',
            'previous_floor','new_floor','previous_decision','new_decision','previous_weekly_estimate',
            'new_weekly_estimate','weekly_estimate_delta','changed','reference_floor_changed','note')
    output=io.StringIO(newline='')
    writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore')
    writer.writeheader()
    for row in report['rows']:
        writer.writerow({'comparison_date':report['evaluation_date'],'candidate_id':report['candidate_id'],
                         'approval_state':report['approval_state'],
                         'previous_rule_id':report['previous_rate']['id'] if report['previous_rate'] else None,
                         'new_rule_id':report['new_rate']['id'],
                         'previous_rate':report['previous_rate']['amount'] if report['previous_rate'] else None,
                         'new_rate':report['new_rate']['amount'],**row})
    return output.getvalue()

def process_jobs(db, employee_rows, day, simulated=False, annualize_salary=False, evaluated_at=None):
    """Restart-safe at-least-once work. Result and flag identities make retries safe."""
    if annualize_salary: raise ValueError('Salary what-if cannot process operational jobs')
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
            for row in db.execute('''SELECT e.*,COALESCE((SELECT MAX(o.observed_at) FROM evaluation_observations o WHERE o.evaluation_id=e.id),e.created_at) AS last_observed
                                    FROM evaluations e WHERE simulated=? AND evaluation_date<? ORDER BY last_observed,e.rowid''',(int(simulated),day)):
                old_input=json.loads(row['data'])['employee_input']
                if affected([old_input],job['jurisdiction']) and covers(row['evaluation_date']):
                    history.setdefault(row['evaluation_date'],{})[row['employee_id']]=old_input
                    ids.add(row['employee_id'])
            for d,inputs in history.items(): batches[d]=list(inputs.values())
            output=[]
            for d,employees in sorted(batches.items()):
                rows=run_evaluation(db,employees,d,annualize_salary,simulated,evaluated_at=evaluated_at)
                output.extend(rows)
                if not simulated:
                    from .batches import save_resolved_results
                    save_resolved_results(db,rows,d)
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
