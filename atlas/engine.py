"""Pure deterministic decisions; no HTTP or model calls in this module."""
import csv
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from .store import candidates, now, digest, dumps, audit

ENGINE_VERSION = 'engine-v3.1'
CENT = Decimal('0.01')
RELEVANT_FIELDS = ('employee_id','work_country','work_state','work_location_code','pay_basis','hourly_rate_ast',
                   'annual_salary_ast','scheduled_hours_per_week','currency','employment_status','minimum_wage_coverage','start_date')

# Exact captured guidance supporting the already implemented higher-floor and
# work-location policies. This is not an approval of a numerical wage rule.
# Bind to evidence, not just IDs: a revision to either publication must be reviewed.
IMPLEMENTED_GUIDANCE = {
    'BDL-2026-0121':'47b8d372aef6612dd26353940645bb8f3e2782402418d363d4cdc2342673420d',
    'BDL-2026-0108':'e56bd1f9e5cb641749d95c47390533465ccdb3ce0bf279fbe0cb94f943975b74',
}

def implemented_guidance(rule):
    return (rule.get('classification')=='INTERPRETATION' and rule.get('source')=='bellwether'
            and rule.get('jurisdiction')=='Bellwether' and rule.get('state')!='REJECTED'
            and IMPLEMENTED_GUIDANCE.get(rule.get('source_rule_id'))==digest(rule.get('evidence','')))

def number(value, positive=False):
    try: n = Decimal(str(value))
    except (InvalidOperation, ValueError): raise ValueError('Missing or invalid numeric value')
    if not n.is_finite() or n < 0 or (positive and n == 0): raise ValueError('Invalid nonnegative number')
    if n>Decimal('1000000000000') or n.as_tuple().exponent < -12:
        raise ValueError('Numeric input exceeds supported magnitude or precision')
    return n

def money(value):
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))

def employee_date(value):
    if not value: raise ValueError('Missing employment start date')
    try: return date.fromisoformat(value[:10])
    except ValueError:
        try:
            n = number(value)
            if n != n.to_integral_value(): raise ValueError('Noninteger Excel date')
            return date(1899,12,30)+timedelta(days=int(n))
        except (ValueError,OverflowError): raise ValueError('Invalid employment start date')

def load_employees(path):
    with open(path,encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if 'employee_id' not in (reader.fieldnames or []): raise ValueError('Employee identifier column missing')
        rows=[{k:(r.get(k) or '').strip() for k in RELEVANT_FIELDS} for r in reader]
    ids=[r['employee_id'] for r in rows]
    if any(not x for x in ids) or len(set(ids)) != len(ids): raise ValueError('Missing or duplicate employee identifiers')
    return rows

def evaluate(employee, rules, evaluation_date, annualize_salary=False, health_issues=()):
    day = date.fromisoformat(evaluation_date)
    e = employee
    result = dict(employee_id=e.get('employee_id'), evaluation_date=evaluation_date,work_jurisdiction=e.get('work_state'),
                  actual_hourly_wage=None,currency=e.get('currency'),candidate_applicable_rules=[],controlling_minimum_wage=None,
                  controlling_jurisdiction=None,controlling_rule_version=None,decision_state='INSUFFICIENT_DATA',hourly_shortfall=None,
                  estimated_weekly_underpayment=None,source_url=None,supporting_evidence=None,explanation=[],
                  evaluation_timestamp=now(),engine_version=ENGINE_VERSION,employee_input=e,
                  policy={'annual_salary_estimate':annualize_salary,'rounding':'ROUND_HALF_UP; compare before rounding','weeks_per_year':52 if annualize_salary else None})
    jurisdictions=['Asteria']+(['Bellwether'] if e.get('work_state')=='Bellwether' else [])
    applicable=[r for r in rules if r['jurisdiction'] in jurisdictions and (not r.get('effective_from') or r['effective_from']<=evaluation_date)]
    result['candidate_applicable_rules']=applicable
    result['source_health_issues']=list(health_issues)
    def stop(state, reason, code=None):
        result['decision_state']=state
        result['explanation'].append(reason)
        result['reason_code']=code or {'COMPLIANT':'MEETS_APPROVED_FLOOR','NON_COMPLIANT':'BELOW_APPROVED_FLOOR',
                                      'INSUFFICIENT_DATA':'MISSING_INPUT_OR_RULE','REVIEW_REQUIRED':'OPERATOR_REVIEW'}[state]
        result['next_action']={
            'COMPLIANT':'Retain receipt; re-evaluate when inputs or approved rules change.',
            'NON_COMPLIANT':'Investigate the flagged wage and verify actual hours before payroll remediation.',
            'INSUFFICIENT_DATA':'Supply the missing input or recover and approve source evidence for this date.',
            'REVIEW_REQUIRED':'Resolve the stated ambiguity with evidence; no automatic compliance pass.',
        }[state]
        if result['reason_code']=='SALARY_CONVERSION_UNAPPROVED':
            result['next_action']='Obtain an approved salary-to-hourly comparison method, actual hours and pay-period information before deciding compliance.'
        elif result['reason_code']=='FUTURE_START_CONFLICT':
            result['next_action']='Confirm the start date and Active status before evaluating wages.'
        return result
    if not e.get('employee_id') or not e.get('work_country') or not e.get('work_state') or not e.get('currency'):
        return stop('INSUFFICIENT_DATA','Required identity, work location or currency missing.')
    if e['work_country'] != 'Asteria' or e['work_state'] not in ('Federal Territory','Bellwether'):
        return stop('REVIEW_REQUIRED','Unsupported work jurisdiction; no jurisdiction inferred from home address.')
    if e['currency'] != 'AST': return stop('REVIEW_REQUIRED','Unsupported currency; FX conversion is not authorized.')
    if e.get('minimum_wage_coverage') != 'Covered': return stop('REVIEW_REQUIRED','Coverage must be explicitly Covered; exemptions are not inferred.')
    if e.get('employment_status') != 'Active': return stop('REVIEW_REQUIRED','Employment status is missing or outside supported active-worker scope.')
    try: start = employee_date(e.get('start_date',''))
    except ValueError as err: return stop('INSUFFICIENT_DATA',str(err))
    if start>day: return stop('REVIEW_REQUIRED','Active status conflicts with start date after evaluation date: '+start.isoformat(),'FUTURE_START_CONFLICT')
    hours = None
    try:
        if e.get('scheduled_hours_per_week'): hours=number(e['scheduled_hours_per_week'],positive=True)
    except ValueError as err: return stop('INSUFFICIENT_DATA','Weekly hours: '+str(err))
    try:
        if e.get('pay_basis')=='Hourly':
            hourly=number(e.get('hourly_rate_ast',''))
            if e.get('annual_salary_ast'): return stop('REVIEW_REQUIRED','Conflicting hourly and annual salary values.')
        elif e.get('pay_basis')=='Annual Salary':
            salary=number(e.get('annual_salary_ast',''))
            if e.get('hourly_rate_ast'): return stop('REVIEW_REQUIRED','Conflicting annual and hourly pay values.')
            if not annualize_salary: return stop('REVIEW_REQUIRED','No authority supplied for converting annual salary to an hourly compliance wage.','SALARY_CONVERSION_UNAPPROVED')
            if hours is None: return stop('INSUFFICIENT_DATA','Annual salary estimate requires weekly hours.')
            hourly=salary/(Decimal(52)*hours)
            result['explanation'].append('SCENARIO ASSUMPTION: hourly equivalent = annual salary / (52 * scheduled weekly hours); not a legally validated conversion.')
        else: return stop('REVIEW_REQUIRED','Unsupported or missing pay basis.')
    except ValueError as err: return stop('INSUFFICIENT_DATA','Pay input: '+str(err))
    result['actual_hourly_wage']=str(hourly)
    if health_issues: return stop('REVIEW_REQUIRED','Source freshness/availability: '+'; '.join(health_issues),'SOURCE_HEALTH_REVIEW')
    pending=[r for r in applicable if r['state']=='REVIEW_REQUIRED' and r['classification'] in ('RATE_REVIEW','REVIEW_REQUIRED','SECURITY_REVIEW','INTERPRETATION')
             and not implemented_guidance(r)
             and (not r.get('effective_to') or evaluation_date<r['effective_to'])]
    if pending: return stop('REVIEW_REQUIRED','Unresolved relevant source content: '+', '.join(r['id'][:12] for r in pending),'PENDING_SOURCE_REVIEW')
    approved=[r for r in applicable if r['state']=='APPROVED']
    superseded={r.get('supersedes') for r in approved if r.get('supersedes')}
    selected=[]
    for jurisdiction in jurisdictions:
        jr=[r for r in approved if r['jurisdiction']==jurisdiction and r['id'] not in superseded]
        if not jr: return stop('INSUFFICIENT_DATA','No approved rule for '+jurisdiction+' on this date.')
        latest=max(r['effective_from'] for r in jr)
        latest_rules=[r for r in jr if r['effective_from']==latest]
        if any(r.get('effective_to') and evaluation_date>=r['effective_to'] for r in latest_rules):
            return stop('INSUFFICIENT_DATA','Latest '+jurisdiction+' rate expired; do not extrapolate a daily rate or fall back to an older rule.')
        amounts={(r['amount'],r['currency'],r['unit']) for r in latest_rules}
        if len(amounts)!=1: return stop('REVIEW_REQUIRED','Conflicting approved rules for '+jurisdiction+' with the same effective date.','CONFLICTING_APPROVED_RULES')
        rule=sorted(latest_rules,key=lambda r:r['id'])[0]
        if rule['currency']!='AST' or rule['unit']!='hour': return stop('REVIEW_REQUIRED','Rule currency or unit is unsupported.')
        selected.append(rule)
    controlling=max(selected,key=lambda r:(number(r['amount']),r['jurisdiction']=='Bellwether'))
    minimum=number(controlling['amount'])
    shortfall=max(Decimal(0),minimum-hourly)
    result.update(controlling_minimum_wage=money(minimum),controlling_jurisdiction=controlling['jurisdiction'],
                  controlling_rule_version=controlling['id'],source_url=controlling['source_url'],supporting_evidence=controlling['evidence'],
                  hourly_shortfall=money(shortfall),hourly_shortfall_unrounded=str(shortfall),
                  estimated_weekly_underpayment=money(shortfall*hours) if hours is not None else None)
    result['explanation'].append('Select latest approved effective rule per jurisdiction; apply highest floor. Equality passes. Amounts compared before rounding.')
    result['explanation'].append('Weekly estimate uses scheduled hours, not actual historical hours; not a payroll liability total.')
    return stop('NON_COMPLIANT' if hourly<minimum else 'COMPLIANT',f'Hourly wage {hourly} AST compared with {minimum} AST/hour.')

def source_health(db, evaluation_date, simulated=False, known_at=None):
    # Historical reconstruction and future scenarios do not claim real-time freshness.
    clock=datetime.fromisoformat(known_at) if known_at else datetime.now(timezone.utc)
    if simulated or evaluation_date != clock.date().isoformat(): return {}
    issues={}
    for source in ('federal','bellwether'):
        row=db.execute('SELECT * FROM fetches WHERE source=? AND simulated=0 AND fetched_at<=? ORDER BY id DESC LIMIT 1',(source,clock.isoformat())).fetchone()
        if row is None: issues[source]='Source has never been retrieved'
        elif row['status']=='ERROR': issues[source]='Latest fetch/extraction failed'
        elif (clock-datetime.fromisoformat(row['fetched_at'])).total_seconds()>86400:
            issues[source]='Source last checked more than 24 hours ago'
    # Corroboration never supplies a controlling rule, but disagreement merits review.
    cards={}
    observations=[]
    for source in ('federal','bellwether'):
        row=db.execute('''SELECT o.data,s.id,s.raw_html,s.source FROM fetches f JOIN snapshots s ON s.id=f.snapshot_id
                          JOIN observations o ON o.snapshot_id=s.id WHERE f.source=? AND f.simulated=0
                          AND f.fetched_at<=? AND f.status!='ERROR' ORDER BY f.id DESC LIMIT 1''',(source,clock.isoformat())).fetchone()
        if row:
            observations.extend((source,o) for o in json.loads(row['data']) if o['kind']=='corroboration')
            from .extract import extract
            try: source_rules,_,_=extract(row['raw_html'],row['source'])
            except ValueError:
                issues[source]='Saved source needs review under the current extraction checks'
                continue
            for r in source_rules:
                if r['kind']=='DAILY_RATE':cards[r['jurisdiction']]=(r['effective_from'],r['amount'])
    for source,o in observations:
        primary=cards.get(o['jurisdiction'])
        if primary and primary[0]==o['effective_date'] and number(primary[1])!=number(o['amount']):
            issues[source]='Cross-source amount disagrees with primary authority for '+o['jurisdiction']
    return issues

def run_evaluation(db, employees, day, annualize_salary=False, simulated=False, known_at=None, evaluated_at=None,
                   update_flags=True):
    if evaluated_at and not simulated: raise ValueError('Only simulated evaluations may set a logical clock')
    if known_at:
        parsed=datetime.fromisoformat(known_at)
        if parsed.tzinfo is None: raise ValueError('Knowledge time must include a UTC offset')
        known_at=parsed.astimezone(timezone.utc).isoformat()
    rules=[r for r in candidates(db,known_at) if r['simulated']==simulated]
    issues=source_health(db,day,simulated,known_at)
    if annualize_salary:
        # What-if outputs never enter the operational result/flag/history tables.
        output=[]
        for employee in employees:
            relevant=['federal']+(['bellwether'] if employee.get('work_state')=='Bellwether' else [])
            result=evaluate(employee,rules,day,True,[s+': '+issues[s] for s in relevant if s in issues])
            result.update(simulated=True,evaluation_mode='SALARY_WHAT_IF_ONLY',knowledge_cutoff=known_at,
                          scenario_only=True,operational_decision=False)
            if employee.get('pay_basis')=='Annual Salary':
                result.update(scenario_hourly_equivalent=result['actual_hourly_wage'],
                              scenario_decision=result['decision_state'],
                              scenario_hourly_shortfall=result['hourly_shortfall'],
                              scenario_weekly_shortfall=result['estimated_weekly_underpayment'],
                              actual_hourly_wage=None,hourly_shortfall=None,estimated_weekly_underpayment=None,
                              decision_state='REVIEW_REQUIRED',reason_code='SALARY_CONVERSION_UNAPPROVED',
                              next_action='Illustration only. Obtain an approved comparison method and actual hours before a compliance decision.')
            result['evaluation_id']=digest({k:v for k,v in result.items() if k!='evaluation_timestamp'})
            output.append(result)
        return output
    output=[]
    with db:
        for employee in employees:
            relevant=['federal']+(['bellwether'] if employee.get('work_state')=='Bellwether' else [])
            result=evaluate(employee,rules,day,annualize_salary,[s+': '+issues[s] for s in relevant if s in issues])
            if evaluated_at: result['evaluation_timestamp']=evaluated_at
            result['simulated']=simulated
            result['evaluation_mode']='CURRENT' if day==datetime.now(timezone.utc).date().isoformat() else 'HISTORICAL_OR_FORECAST_SCENARIO'
            result['knowledge_cutoff']=known_at
            identity={k:v for k,v in result.items() if k!='evaluation_timestamp'}
            result['evaluation_id']=digest(identity)
            observed_at=result['evaluation_timestamp']
            prior=db.execute('SELECT data FROM evaluations WHERE id=?',(result['evaluation_id'],)).fetchone()
            if prior: result=json.loads(prior['data'])
            else:
                db.execute('INSERT INTO evaluations VALUES(?,?,?,?,?,?)',
                           (result['evaluation_id'],employee['employee_id'],day,result['evaluation_timestamp'],dumps(result),int(simulated)))
                audit(db,'EMPLOYEE_EVALUATED',dict(employee_id=employee['employee_id'],evaluation_id=result['evaluation_id'],decision=result['decision_state'],simulated=simulated),result['evaluation_timestamp'])
            # A historical knowledge-time query must not change today's operational flags.
            if not known_at and update_flags:
                flag_id=digest([employee['employee_id'],day,simulated])
                existing=db.execute('SELECT status,evaluation_id FROM flags WHERE id=?',(flag_id,)).fetchone()
                state={'NON_COMPLIANT':'OPEN','COMPLIANT':'CLEAR'}.get(result['decision_state'],'REVIEW')
                if not existing or existing['evaluation_id']!=result['evaluation_id']:
                    db.execute('INSERT INTO evaluation_observations(evaluation_id,observed_at) VALUES(?,?)',
                               (result['evaluation_id'],observed_at))
                    db.execute('''INSERT INTO flags VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                                  status=excluded.status,evaluation_id=excluded.evaluation_id,updated_at=excluded.updated_at''',
                               (flag_id,employee['employee_id'],day,state,result['evaluation_id'],observed_at,int(simulated)))
                    audit(db,'FLAG_TRANSITION',{'flag_id':flag_id,'from':existing['status'] if existing else None,'to':state,
                                              'evaluation_id':result['evaluation_id'],'simulated':simulated},observed_at)
            output.append(result)
    return output

def export_results(results, path):
    from pathlib import Path
    from .triage import enrich_results
    results=enrich_results(results)
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    columns=['employee_id','evaluation_date','work_jurisdiction','actual_hourly_wage','currency','controlling_minimum_wage',
             'controlling_jurisdiction','controlling_rule_version','decision_state','hourly_shortfall','estimated_weekly_underpayment',
             'source_url','evaluation_id','evaluation_timestamp','simulated','explanation',
             'indicative_salary_hourly','approved_reference_floor','pending_rate_candidates',
             'indicative_hourly_gap_to_reference','indicative_weekly_gap_to_reference',
             'recorded_hourly_gap_to_reference','recorded_weekly_gap_to_reference']
    with p.with_suffix('.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns); writer.writeheader()
        for row in results:
            flat={**row,**row['analysis_context']}
            writer.writerow({k:json.dumps(flat[k]) if isinstance(flat.get(k),list) else flat.get(k) for k in columns})
