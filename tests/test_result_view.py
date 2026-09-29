import json
import tempfile
import unittest
from pathlib import Path
from atlas.store import connect
from atlas.result_view import retained_results, retention_context, export_results
from atlas.engine import evaluate
from test_atlas import employee, rule


def rows(day, pending=False):
    return [dict(employee_id='A', evaluation_date=day, evaluation_id='receipt-'+day,
                 decision_state='REVIEW_REQUIRED' if pending else 'NON_COMPLIANT',
                 reason_code='PENDING_SOURCE_REVIEW' if pending else 'BELOW_APPROVED_FLOOR'),
            dict(employee_id='B', evaluation_date=day, decision_state='REVIEW_REQUIRED',
                 reason_code='SALARY_CONVERSION_UNAPPROVED')]


class RetainedResultsTests(unittest.TestCase):
    def test_missing_wage_explained_without_changing_saved_decision(self):
        day='2026-09-24'
        old=[evaluate(employee(),[rule()],day)]
        current=[evaluate(employee(hourly_rate_ast=''),[rule()],day)]
        with tempfile.TemporaryDirectory() as folder:
            db=connect(Path(folder)/'test.db')
            retained_results(db,old,day)
            displayed,saved_date=retained_results(db,current,day)
            context=retention_context(current,displayed,saved_date)
            self.assertEqual(displayed,old)
            self.assertEqual((context['employee_count'],context['source_count']),(1,0))
            self.assertIn('Pay input',context['issues'][0]['explanation'])
            exported=export_results(current,displayed,saved_date)
            self.assertEqual(exported[0]['actual_hourly_wage'],'10.00')
            self.assertEqual(exported[0]['saved_result_notice']['current_issue']['decision_state'],'INSUFFICIENT_DATA')
            self.assertNotIn('saved_result_notice',old[0])
            db.close()

    def test_mixed_blockers_and_expired_rule_are_distinguished(self):
        old=rows('2026-09-27')
        current=rows('2026-09-28',True)
        current[1].update(reason_code='MISSING_INPUT_OR_RULE',decision_state='INSUFFICIENT_DATA',explanation=['Pay input: missing value'])
        context=retention_context(current,old,'2026-09-27')
        self.assertEqual((context['source_count'],context['employee_count']),(1,1))
        expired=[evaluate(employee(),[rule()],'2026-09-25')]
        context=retention_context(expired,[evaluate(employee(),[rule()],'2026-09-24')],'2026-09-24')
        self.assertEqual(context['source_count'],1)
        self.assertIn('expired',context['issues'][0]['explanation'])

    def test_pending_preserves_complete_set_then_approval_replaces_it(self):
        with tempfile.TemporaryDirectory() as folder:
            db=connect(Path(folder)/'test.db')
            old=rows('2026-09-27')
            self.assertEqual(retained_results(db,old,'2026-09-27'),(old,None))
            pending=rows('2026-09-28',True)
            self.assertEqual(retained_results(db,pending,'2026-09-28'),(old,'2026-09-27'))
            # Repeated checks do not publish the pending result or change receipts.
            self.assertEqual(retained_results(db,pending,'2026-09-28')[0],old)
            approved=rows('2026-09-28')
            self.assertEqual(retained_results(db,approved,'2026-09-28'),(approved,None))
            # Same-day correction also preserves the last source-cleared set.
            self.assertEqual(retained_results(db,pending,'2026-09-28'),(approved,'2026-09-28'))
            db.close()

    def test_no_baseline_or_different_population_cannot_invent_results(self):
        with tempfile.TemporaryDirectory() as folder:
            db=connect(Path(folder)/'test.db')
            pending=rows('2026-09-28',True)
            self.assertEqual(retained_results(db,pending,'2026-09-28'),(pending,None))
            retained_results(db,rows('2026-09-27'),'2026-09-27')
            pending[0]['employee_id']='new employee'
            self.assertEqual(retained_results(db,pending,'2026-09-28'),(pending,None))
            db.close()

    def test_upgrade_recovers_whole_historical_flag_set(self):
        with tempfile.TemporaryDirectory() as folder:
            db=connect(Path(folder)/'test.db')
            old=rows('2026-09-27')
            for i,row in enumerate(old):
                db.execute('INSERT INTO evaluations VALUES(?,?,?,?,?,0)',(str(i),row['employee_id'],'2026-09-27','2026-09-27T12:00:00Z',json.dumps(row)))
                db.execute('INSERT INTO flags VALUES(?,?,?,?,?,?,0)',(str(i),row['employee_id'],'2026-09-27','OPEN',str(i),'2026-09-27T12:00:00Z'))
            db.commit()
            self.assertEqual(retained_results(db,rows('2026-09-28',True),'2026-09-28'),(old,'2026-09-27'))
            db.close()
