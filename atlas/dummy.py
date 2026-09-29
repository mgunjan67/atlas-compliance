"""User-entered rate tests, stored separately from all operational records."""
import json
from datetime import date
from uuid import uuid4
from .engine import evaluate, number
from .lab import rate
from .store import dumps, now
from .batches import saved_sets
from .workflow import summarize


def list_runs(db):
    return [json.loads(r[0]) for r in db.execute('SELECT data FROM dummy_runs ORDER BY rowid DESC')]


def run_dummy(db, employees, federal, state, day, name=''):
    date.fromisoformat(day)
    amounts=[str(number(v,positive=True)) for v in (federal,state)]
    if len(name)>100:raise ValueError('Test name must be at most 100 characters')
    run_id='dummy-'+uuid4().hex
    def calculate(values, label):
        rules=[rate(run_id+'-'+label+'-'+str(i),jur,v,effective_from=day,effective_to=None,
                    simulated=True,source_url='dummy://manual-test',evidence='Manually entered dummy rate; not an approved source rule.')
               for i,(jur,v) in enumerate(zip(('Asteria','Bellwether'),values))]
        return [dict(evaluate(e,rules,day),simulated=True,scenario_only=True,operational_decision=False,evaluation_mode='DUMMY_TEST') for e in employees]
    results=calculate(amounts,'new')
    baseline=next((b for b in saved_sets(db) if b['evaluation_date']<=day),None)
    previous=[]
    old_values=None
    if baseline:
        old_values=[next(r['amount'] for r in baseline['rules'] if r['jurisdiction']==jur) for jur in ('Asteria','Bellwether')]
        previous=calculate(old_values,'baseline')
    by_id={r['employee_id']:r for r in previous}
    changes=[]
    for r in results:
        old=by_id.get(r['employee_id'])
        if old and any(old.get(k)!=r.get(k) for k in ('decision_state','controlling_minimum_wage','hourly_shortfall')):
            changes.append(dict(employee_id=r['employee_id'],before_state=old['decision_state'],after_state=r['decision_state'],before_floor=old['controlling_minimum_wage'],after_floor=r['controlling_minimum_wage']))
    output=dict(id=run_id,name=name.strip() or 'Manual rate test',created_at=now(),evaluation_date=day,
                simulated=True,scenario_only=True,kind='DUMMY_TEST',federal=amounts[0],state=amounts[1],
                baseline_date=baseline['evaluation_date'] if baseline else None,baseline_rates=old_values,
                comparison='Same employee inputs and evaluation date; prior approved amounts are used only as a dummy comparison. No live rules, source checks or approvals are changed.',
                summary=summarize(results),changes=changes,results=results)
    with db:db.execute('INSERT INTO dummy_runs VALUES(?,?)',(run_id,dumps(output)))
    return output
