"""Explicitly simulated change replay, isolated from live review decisions."""
import json
from pathlib import Path
from .monitor import ingest
from .store import candidates, review, now, audit
from .engine import run_evaluation, export_results

def page(amount, effective='September 24, 2026', source='federal', extra=''):
    rule_id='SIM-FEDERAL' if source=='federal' else 'SIM-BELLWETHER'
    return f'''<!doctype html><html><body><h1>SIMULATED TEST PUBLICATION</h1>
    <aside class="rate-card" id="rate"><div class="rate">{amount}</div><p>AST per hour</p>
    <dl><dt>Effective</dt><dd>{effective} (daily rate)</dd><dt>Coverage</dt><dd>Covered, nonexempt employees</dd>
    <dt>Rule ID</dt><dd>{rule_id}</dd></dl></aside>
    <article class="notice news"><div class="meta"><span>News</span><span>September 1, 2026</span></div>
    <h3>SIMULATED administrative update</h3><p>No wage rate change.</p><details id="SIM-NEWS"></details></article>{extra}</body></html>'''

def simulated_reviews(db):
    for c in candidates(db):
        if c['simulated'] and c['state']=='REVIEW_REQUIRED':
            decision='APPROVED' if c['classification']=='RATE_REVIEW' else 'ACKNOWLEDGED'
            review(db,c['id'],decision,'SIMULATED reviewer','Test fixture only: not a human approval of a live source.',allow_simulated=True)

def run_demo(db, directory):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    employees=[dict(employee_id='SIM-001',work_country='Asteria',work_state='Bellwether',pay_basis='Hourly',
                    hourly_rate_ast='15.00',currency='AST',scheduled_hours_per_week='40',employment_status='Active',
                    minimum_wage_coverage='Covered',start_date='2020-01-01')]
    for source, amount in [('federal','10.00'),('bellwether','14.00')]:
        ingest(db,source,page(amount,source=source),simulated=True)
    simulated_reviews(db)
    before=run_evaluation(db,employees,'2026-09-24',simulated=True)
    for source, amount in [('federal','10.00'),('bellwether','16.00')]:
        ingest(db,source,page(amount,'September 25, 2026',source),simulated=True)
    pending=run_evaluation(db,employees,'2026-09-25',simulated=True)
    simulated_reviews(db)
    after=run_evaluation(db,employees,'2026-09-25',simulated=True)
    for name, result in [('before',before),('pending',pending),('after',after)]:
        export_results(result,directory/f'demo-{name}.json')
    events=[dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id')]
    (directory/'demo-audit.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
    return {'simulated':True,'before':before[0]['decision_state'],'pending':pending[0]['decision_state'],
            'after':after[0]['decision_state'],'weekly_shortfall':after[0]['estimated_weekly_underpayment']}
