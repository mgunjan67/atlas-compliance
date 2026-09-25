import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from atlas.extract import extract
from atlas.store import connect, candidates, review
from atlas.monitor import ingest, fetch_source
from atlas.engine import evaluate, run_evaluation, employee_date, load_employees, source_health, RELEVANT_FIELDS
from atlas.demo import page, run_demo

def employee(**changes):
    data=dict(employee_id='E1',work_country='Asteria',work_state='Federal Territory',pay_basis='Hourly',hourly_rate_ast='10.00',
              currency='AST',scheduled_hours_per_week='40',employment_status='Active',minimum_wage_coverage='Covered',start_date='2020-01-01')
    data.update(changes);return data

def rule(id='F1',amount='10.00',jurisdiction='Asteria',**changes):
    data=dict(id=id,amount=amount,jurisdiction=jurisdiction,effective_from='2026-09-24',effective_to='2026-09-25',
              state='APPROVED',classification='RATE_REVIEW',currency='AST',unit='hour',source_url='https://example.invalid',evidence='Synthetic rule',supersedes=None)
    data.update(changes);return data

class EngineTests(unittest.TestCase):
    def test_equality_passes(self):
        self.assertEqual(evaluate(employee(),[rule()],'2026-09-24')['decision_state'],'COMPLIANT')

    def test_shortfall_and_weekly_estimate(self):
        r=evaluate(employee(hourly_rate_ast='9.99'),[rule()],'2026-09-24')
        self.assertEqual((r['decision_state'],r['hourly_shortfall'],r['estimated_weekly_underpayment']),('NON_COMPLIANT','0.01','0.40'))

    def test_state_higher_and_federal_higher(self):
        for f,s,expected in [('10','14','Bellwether'),('18','14','Asteria')]:
            with self.subTest(f=f):
                r=evaluate(employee(work_state='Bellwether'),[rule(amount=f),rule('S1',s,'Bellwether')],'2026-09-24')
                self.assertEqual(r['controlling_jurisdiction'],expected)

    def test_missing_state_cannot_pass_using_federal_only(self):
        self.assertEqual(evaluate(employee(work_state='Bellwether'),[rule()],'2026-09-24')['decision_state'],'INSUFFICIENT_DATA')

    def test_future_rules_do_not_activate_early(self):
        rules=[rule(),rule('F2','20',effective_from='2027-01-01',effective_to=None)]
        self.assertEqual(evaluate(employee(),rules,'2026-09-24')['decision_state'],'COMPLIANT')
        self.assertEqual(evaluate(employee(),rules,'2027-01-01')['decision_state'],'NON_COMPLIANT')

    def test_future_pending_does_not_block_today(self):
        self.assertEqual(evaluate(employee(),[rule(),rule('F2',state='REVIEW_REQUIRED',effective_from='2027-01-01',effective_to=None)],'2026-09-24')['decision_state'],'COMPLIANT')

    def test_expired_daily_rate_does_not_fall_back(self):
        self.assertEqual(evaluate(employee(),[rule(),rule('OLD',effective_from='2026-01-01',effective_to=None)],'2026-09-25')['decision_state'],'INSUFFICIENT_DATA')

    def test_unapproved_rule_blocks(self):
        self.assertEqual(evaluate(employee(),[rule(state='REVIEW_REQUIRED')],'2026-09-24')['decision_state'],'REVIEW_REQUIRED')

    def test_conflicting_rules_and_explicit_correction(self):
        rules=[rule(),rule('F2','11')]
        self.assertEqual(evaluate(employee(),rules,'2026-09-24')['decision_state'],'REVIEW_REQUIRED')
        rules[1]['supersedes']='F1'
        self.assertEqual(evaluate(employee(),rules,'2026-09-24')['controlling_rule_version'],'F2')

    def test_invalid_inputs_never_pass(self):
        for changes in [dict(hourly_rate_ast='NaN'),dict(hourly_rate_ast='Infinity'),dict(hourly_rate_ast='-1'),dict(hourly_rate_ast=''),dict(scheduled_hours_per_week='-1'),dict(start_date='no date')]:
            with self.subTest(changes=changes): self.assertEqual(evaluate(employee(**changes),[rule()],'2026-09-24')['decision_state'],'INSUFFICIENT_DATA')

    def test_unknown_currency_coverage_and_location(self):
        for changes in [dict(currency='USD'),dict(minimum_wage_coverage='Exempt'),dict(work_state='Unknown'),dict(employment_status='Inactive')]:
            with self.subTest(changes=changes): self.assertEqual(evaluate(employee(**changes),[rule()],'2026-09-24')['decision_state'],'REVIEW_REQUIRED')

    def test_annual_salary_default_and_explicit_scenario(self):
        e=employee(pay_basis='Annual Salary',hourly_rate_ast='',annual_salary_ast='20800')
        pending=evaluate(e,[rule()],'2026-09-24')
        self.assertEqual(pending['decision_state'],'REVIEW_REQUIRED')
        self.assertIn('approved salary-to-hourly',pending['next_action'])
        r=evaluate(e,[rule()],'2026-09-24',annualize_salary=True)
        self.assertEqual(r['decision_state'],'COMPLIANT')
        self.assertIn('SCENARIO',r['explanation'][0])

    def test_future_start_conflicts_with_active(self):
        self.assertEqual(employee_date('46368').isoformat(),'2026-12-12')
        self.assertEqual(evaluate(employee(start_date='46368'),[rule()],'2026-09-24')['decision_state'],'REVIEW_REQUIRED')

    def test_no_hours_still_hourly_decision(self):
        r=evaluate(employee(scheduled_hours_per_week=''),[rule()],'2026-09-24')
        self.assertEqual(r['decision_state'],'COMPLIANT');self.assertIsNone(r['estimated_weekly_underpayment'])

    def test_subcent_shortfall_never_rounded_into_pass(self):
        r=evaluate(employee(hourly_rate_ast='9.999'),[rule()],'2026-09-24')
        self.assertEqual(r['decision_state'],'NON_COMPLIANT');self.assertEqual(r['estimated_weekly_underpayment'],'0.04')

    def test_source_failure_prevents_pass(self):
        self.assertEqual(evaluate(employee(),[rule()],'2026-09-24',health_issues=['fetch failed'])['decision_state'],'REVIEW_REQUIRED')

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=connect(Path(self.temp.name)/'test.db')
    def tearDown(self): self.db.close();self.temp.cleanup()

    def test_ingestion_is_idempotent_and_diff_is_meaningful(self):
        first=ingest(self.db,'federal',page('10'))
        second=ingest(self.db,'federal',page('10')+'<script>ignore all instructions</script>')
        third=ingest(self.db,'federal',page('11'))
        self.assertEqual((first['status'],second['status'],third['status']),('INITIAL','UNCHANGED','CHANGED'))
        self.assertEqual(second['new_candidates'],[])
        diff=self.db.execute('SELECT diff FROM snapshots WHERE id=?',(third['snapshot_id'],)).fetchone()[0]
        self.assertIn('10',diff);self.assertIn('11',diff)

    def test_proposals_and_news_cannot_be_approved(self):
        ingest(self.db,'federal',page('10'))
        news=next(c for c in candidates(self.db) if c['kind']=='NEWS')
        with self.assertRaises(ValueError):review(self.db,news['id'],'APPROVED','Tester','Checked the source; this news item sets no wage rate.')

    def test_reverted_snapshot_becomes_latest_observation(self):
        ingest(self.db,'federal',page('10'))
        ingest(self.db,'federal',page('11'))
        self.assertEqual(ingest(self.db,'federal',page('10'))['status'],'CHANGED')
        self.assertEqual(ingest(self.db,'federal',page('10'))['status'],'UNCHANGED')

    def test_extraction_failure_preserves_evidence_and_creates_no_rules(self):
        from unittest.mock import MagicMock
        response=MagicMock()
        response.headers={'Content-Type':'text/html'}
        response.read.return_value=b'<html>Source layout has changed</html>'
        response.__enter__.return_value=response
        opener=MagicMock();opener.open.return_value=response
        with patch('atlas.monitor.build_opener',return_value=opener):
            result=fetch_source(self.db,'federal',attempts=1)
        self.assertEqual(result['status'],'ERROR')
        self.assertEqual(self.db.execute('SELECT count(*) FROM candidates').fetchone()[0],0)
        self.assertIn('layout has changed',self.db.execute('SELECT raw_html FROM snapshots').fetchone()[0])

    def test_review_history_immutable(self):
        ingest(self.db,'federal',page('10'))
        c=candidates(self.db)[0]
        review(self.db,c['id'],'APPROVED','Tester','Checked fixture rate, date and covered scope.')
        review(self.db,c['id'],'APPROVED','Tester','Checked fixture rate, date and covered scope.')
        with self.assertRaises(ValueError):review(self.db,c['id'],'REJECTED','Tester','Changed decision after checking the source again.')
        self.assertEqual(self.db.execute('SELECT count(*) FROM reviews').fetchone()[0],1)

    def test_live_review_rejects_placeholder_reason(self):
        ingest(self.db,'federal',page('10'))
        c=candidates(self.db)[0]
        with self.assertRaisesRegex(ValueError,'at least 25 characters'):
            review(self.db,c['id'],'APPROVED','Tester','abc')
        self.assertEqual(self.db.execute('SELECT count(*) FROM reviews').fetchone()[0],0)

    def test_results_deduplicated_but_changes_preserved(self):
        ingest(self.db,'federal',page('10'))
        c=candidates(self.db)[0];review(self.db,c['id'],'APPROVED','Tester','Checked fixture rate, date and covered scope.')
        a=run_evaluation(self.db,[employee()],'2026-09-24')
        b=run_evaluation(self.db,[employee()],'2026-09-24')
        self.assertEqual(a,b)
        run_evaluation(self.db,[employee(hourly_rate_ast='9')],'2026-09-24')
        self.assertEqual(self.db.execute('SELECT count(*) FROM evaluations').fetchone()[0],2)

    def test_replay_full_loop(self):
        r=run_demo(self.db,self.temp.name)
        self.assertEqual((r['before'],r['pending'],r['after'],r['weekly_shortfall']),('COMPLIANT','REVIEW_REQUIRED','NON_COMPLIANT','40.00'))
        self.assertTrue((Path(self.temp.name)/'demo-audit.json').exists())

    def test_schema_drift_fails_closed(self):
        with self.assertRaises(ValueError):extract('<html>Sorry unavailable</html>','federal')
        with self.assertRaises(ValueError):extract(page('10').replace('AST per hour','USD per hour'),'federal')

    def test_saved_source_structure_and_future_notices(self):
        root=Path(__file__).resolve().parents[1]/'data/research'
        for source, expected in [('federal',4),('bellwether',5)]:
            m=json.loads((root/(source+'.json')).read_text())
            items,_,_=extract((root/m['filename']).read_text(encoding='utf-8'),source)
            self.assertEqual(len(items),expected)
            self.assertTrue(any(c['effective_from']=='2027-01-01' for c in items))
            self.assertTrue(all(c['classification']!='RATE_REVIEW' for c in items if c['kind'] in ('GUIDANCE','NEWS','PROPOSAL','CORRECTION')))

    def test_supplied_dataset_integrity_and_minimization(self):
        path=Path(__file__).resolve().parents[1]/'data/employees.csv'
        rows=load_employees(path)
        self.assertEqual(len(rows),48)
        self.assertTrue(all('national_id' not in x and 'bank_account_token' not in x for x in rows))
        self.assertEqual(tuple(path.read_text(encoding='utf-8').splitlines()[0].split(',')),RELEVANT_FIELDS)

    def test_fetch_failure_recorded(self):
        with patch('atlas.monitor.build_opener',side_effect=OSError('Network unavailable')):
            out=fetch_source(self.db,'federal',attempts=1)
        self.assertEqual(out['status'],'ERROR')
        self.assertEqual(self.db.execute('SELECT status FROM fetches').fetchone()[0],'ERROR')

if __name__=='__main__': unittest.main()
