"""Regression cases found by the submission audit, not just happy-path examples."""
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from atlas.demo import page
from atlas.extract import extract
from atlas.monitor import ingest
from atlas.store import connect,candidates,review
from atlas.engine import evaluate,run_evaluation
from atlas.workflow import rate_change_report,process_jobs
from atlas.lab import worker,rate
from atlas.scheduler import LiveScheduler
from atlas.receipt import build_receipt, verify_receipt

def notice(text,cls='final',sid='NEW'):
    return f'<article class="notice {cls}"><div class="meta"><span>Publication</span><span>September 1, 2026</span></div><p>{text}</p><details id="{sid}"></details></article>'

class ImprovementTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=connect(Path(self.temp.name)/'test.db')
    def tearDown(self):
        self.db.close();self.temp.cleanup()
    def approve_daily(self,amount,day='September 24, 2026',at='2026-09-24T10:00:00+00:00'):
        ingest(self.db,'federal',page(amount,day),retrieved_at=at,simulated=True)
        c=next(c for c in candidates(self.db) if c['amount']==amount and c['state']=='REVIEW_REQUIRED')
        review(self.db,c['id'],'APPROVED','TEST','Synthetic fixture only',allow_simulated=True,at=at)
        return c
    def test_unfamiliar_container_is_changed_and_blocks(self):
        self.approve_daily('10.00')
        extra='<section class="bulletin">Final wage: 19.00 AST per hour effective September 24, 2026.</section>'
        result=ingest(self.db,'federal',page('10.00',extra=extra),simulated=True)
        self.assertEqual(result['status'],'CHANGED')
        rules=candidates(self.db)
        self.assertTrue(any(r['kind']=='UNKNOWN' for r in rules))
        self.assertEqual(evaluate(worker(),rules,'2026-09-24')['reason_code'],'PENDING_SOURCE_REVIEW')
    def test_contradictory_labels_and_scope_are_not_general_rules(self):
        cases=[('This is not a proposal: final rate 19.00 AST per hour effective September 24, 2026.','final'),
               ('Final rate 19.00 AST per hour effective September 24, 2026.','news'),
               ('Final rate 19.00 AST per hour effective September 24, 2026, only for retail employers with 25 employees.','final')]
        for text,cls in cases:
            with self.subTest(text=text):
                parsed,_,_=extract(page('10.00',extra=notice(text,cls)),'federal')
                self.assertEqual(parsed[-1]['classification'],'REVIEW_REQUIRED')
                self.assertIsNone(parsed[-1]['amount'])
    def test_card_coverage_extension_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'coverage'):
            extract(page('10.00').replace('Covered, nonexempt employees','Covered, nonexempt employees in retail only'),'federal')

    def test_notice_amounts_must_be_complete_supported_tokens(self):
        for amount in ('13.255','1,234.00','-13.25','+13.25','NaN','13.25.00'):
            with self.subTest(amount=amount):
                text=f'The Asterian federal minimum wage for covered, nonexempt employees will increase to {amount} AST per hour effective January 1, 2027.'
                c=extract(page('10.00',extra=notice(text)),'federal')[0][-1]
                self.assertEqual(c['classification'],'REVIEW_REQUIRED')
                self.assertIsNone(c['amount'])
                self.assertEqual(c['coverage'],'unknown')

    def test_notice_scope_requires_supported_general_wording(self):
        base='The Asterian federal minimum wage for covered, nonexempt employees will increase to 19.00 AST per hour effective January 1, 2027'
        for suffix in (', only for tipped workers.',', only for employees under 18 years of age.',
                       '. Seasonal workers qualify; others remain at the old rate.',', for apprentices.'):
            with self.subTest(suffix=suffix):
                c=extract(page('10.00',extra=notice(base+suffix)),'federal')[0][-1]
                self.assertEqual((c['classification'],c['coverage']),('REVIEW_REQUIRED','unknown'))
                self.assertIsNone(c['amount'])

    def test_supported_publications_keep_their_identity_after_parser_upgrade(self):
        from atlas.showcase import research_html
        from atlas.extract import candidate_identity
        from atlas.extract_v3 import extract as old_extract
        for source in ('federal','bellwether'):
            html=research_html(source)
            old=old_extract(html,source)[0];new=extract(html,source)[0]
            self.assertEqual(old,new)
            self.assertEqual([candidate_identity(c,False) for c in old],[candidate_identity(c,False) for c in new])

    def test_returning_final_notice_requires_new_review_and_preserves_receipts(self):
        def html(amount):
            return page('10.00',extra=notice(f'The Asterian federal minimum wage for covered, nonexempt employees will increase to {amount} AST per hour effective January 1, 2027.'))
        ingest(self.db,'federal',html('15.00'),simulated=True)
        first=next(c for c in candidates(self.db) if c['kind']=='FINAL_NOTICE')
        review(self.db,first['id'],'APPROVED','TEST','Synthetic fixture only',allow_simulated=True)
        person=worker(work_state='Federal Territory');person['hourly_rate_ast']='15.50'
        old=run_evaluation(self.db,[person],'2027-01-01',simulated=True)[0]
        receipt=build_receipt(self.db,old['evaluation_id'])
        self.assertEqual(old['decision_state'],'COMPLIANT')
        ingest(self.db,'federal',html('16.00'),simulated=True)
        middle=next(c for c in candidates(self.db) if c['kind']=='FINAL_NOTICE' and c['amount']=='16.00')
        review(self.db,middle['id'],'APPROVED','TEST','Synthetic fixture only',first['id'],allow_simulated=True)
        returned=ingest(self.db,'federal',html('15.00'),simulated=True)
        self.assertEqual(len(returned['new_candidates']),1)
        latest=next(c for c in candidates(self.db) if c['id']==returned['new_candidates'][0])
        self.assertEqual(latest['state'],'REVIEW_REQUIRED')
        pending=run_evaluation(self.db,[person],'2027-01-01',simulated=True)[0]
        self.assertEqual(pending['reason_code'],'PENDING_SOURCE_REVIEW')
        self.assertEqual(ingest(self.db,'federal',html('15.00'),simulated=True)['new_candidates'],[])
        review(self.db,latest['id'],'APPROVED','TEST','Synthetic fixture only',middle['id'],allow_simulated=True)
        current=run_evaluation(self.db,[person],'2027-01-01',simulated=True)[0]
        self.assertEqual(current['controlling_minimum_wage'],'15.00')
        for bundle in (receipt,build_receipt(self.db,current['evaluation_id'])):
            self.assertTrue(verify_receipt(bundle)['valid'],verify_receipt(bundle)['errors'])

    def test_returning_non_rate_notice_does_not_inherit_acknowledgment(self):
        for kind in ('guidance','correction'):
            with self.subTest(kind=kind):
                first_page=page('10.00',extra=notice('Coverage for seasonal work requires confirmation.',kind,sid=kind))
                ingest(self.db,'federal',first_page,simulated=True)
                c=next(c for c in candidates(self.db) if c['source_rule_id']==kind)
                review(self.db,c['id'],'ACKNOWLEDGED','TEST','Synthetic fixture only',allow_simulated=True)
                ingest(self.db,'federal',page('10.00',extra=notice('Coverage for seasonal work has changed.',kind,sid=kind)),simulated=True)
                result=ingest(self.db,'federal',first_page,simulated=True)
                returned=next(c for c in candidates(self.db) if c['id'] in result['new_candidates'])
                self.assertEqual(returned['state'],'REVIEW_REQUIRED')
                self.assertEqual(ingest(self.db,'federal',first_page,simulated=True)['new_candidates'],[])

    def test_historical_v3_extraction_still_replays_after_validation_fix(self):
        from atlas.extract_v3 import extract as old_extract
        text='The Asterian federal minimum wage for covered, nonexempt employees will increase to 13.255 AST per hour effective January 1, 2027.'
        with patch('atlas.monitor.extract',side_effect=old_extract),patch('atlas.monitor.PARSER_VERSION','html-v3'):
            ingest(self.db,'federal',page('10.00',extra=notice(text)),simulated=True)
        legacy=next(c for c in candidates(self.db) if c['kind']=='FINAL_NOTICE')
        self.assertEqual(legacy['amount'],'255.00')
        review(self.db,legacy['id'],'APPROVED','TEST','Historical synthetic fixture; retain what the old parser produced.',allow_simulated=True)
        result=run_evaluation(self.db,[worker(work_state='Federal Territory')],'2027-01-01',simulated=True)[0]
        verified=verify_receipt(build_receipt(self.db,result['evaluation_id']))
        self.assertTrue(verified['valid'],verified['errors'])
    def test_unmapped_prose_change_cannot_be_unchanged(self):
        ingest(self.db,'federal',page('10.00'),simulated=True)
        with self.assertRaisesRegex(ValueError,'Visible content changed'):
            ingest(self.db,'federal',page('10.00',extra='<div>Former coverage guidance is withdrawn.</div>'),simulated=True)
    def test_pending_interpretation_blocks_then_acknowledgment_resolves(self):
        self.approve_daily('10.00')
        ingest(self.db,'federal',page('10.00',extra=notice('Precedence is withdrawn; verify headcount before applying either floor.','guidance')),simulated=True)
        self.assertEqual(evaluate(worker(),candidates(self.db),'2026-09-24')['reason_code'],'PENDING_SOURCE_REVIEW')
    def test_existing_guidance_does_not_block_either_precedence_direction(self):
        from atlas.showcase import research_html
        guidance=[dict(c,id=c['source_rule_id'],state='REVIEW_REQUIRED') for c in extract(research_html('bellwether'),'bellwether')[0] if c['classification']=='INTERPRETATION']
        for federal,state_rate,expected in [('10.00','14.00','Bellwether'),('16.00','14.00','Asteria')]:
            rules=[rate('fed','Asteria',federal),rate('state','Bellwether',state_rate)]+guidance
            result=evaluate(worker(),rules,'2026-09-24')
            self.assertEqual(result['controlling_jurisdiction'],expected)
            self.assertIn(result['decision_state'],('COMPLIANT','NON_COMPLIANT'))
    def test_changed_guidance_with_same_id_requires_review(self):
        from atlas.showcase import research_html
        guidance=next(c for c in extract(research_html('bellwether'),'bellwether')[0] if c['source_rule_id']=='BDL-2026-0121')
        guidance.update(id='changed',state='REVIEW_REQUIRED',evidence=guidance['evidence']+' Previous precedence is withdrawn.')
        result=evaluate(worker(),[rate('fed','Asteria','10.00'),rate('state','Bellwether','14.00'),guidance],'2026-09-24')
        self.assertEqual(result['reason_code'],'PENDING_SOURCE_REVIEW')
    def test_unknown_cannot_be_generically_acknowledged(self):
        ingest(self.db,'federal',page('10.00',extra=notice('Unrecognized legal change.')),simulated=True)
        c=next(c for c in candidates(self.db) if c['kind']=='UNKNOWN')
        with self.assertRaisesRegex(ValueError,'Unknown publication'):
            review(self.db,c['id'],'ACKNOWLEDGED','TEST','Generic note',allow_simulated=True)
    def test_salary_scenario_does_not_mutate_database(self):
        self.approve_daily('10.00')
        e=worker();e.update(pay_basis='Annual Salary',annual_salary_ast='20800',hourly_rate_ast='')
        before=self.db.total_changes
        result=run_evaluation(self.db,[e],'2026-09-24',annualize_salary=True,simulated=True)[0]
        self.assertTrue(result['scenario_only'])
        self.assertEqual(result['evaluation_mode'],'SALARY_WHAT_IF_ONLY')
        self.assertEqual(self.db.total_changes,before)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM flags').fetchone()[0],0)
    def test_conflicting_previous_rates_have_no_monetary_comparison(self):
        self.approve_daily('10.00');self.approve_daily('11.00')
        current=self.approve_daily('12.00','September 25, 2026','2026-09-25T10:00:00+00:00')
        result=rate_change_report(self.db,[worker()],current['id'])
        self.assertIsNone(result['previous_rate'])
        self.assertIsNone(result['rate_delta'])
        self.assertIsNone(result['weekly_estimate_delta'])
        self.assertIn('conflict',result['basis'])
    def test_input_reversion_records_new_observation_time(self):
        self.approve_daily('10.00')
        for wage,hour in [('10.00','12'),('9.00','13'),('10.00','14')]:
            e=worker(work_state='Federal Territory');e['hourly_rate_ast']=wage
            run_evaluation(self.db,[e],'2026-09-24',simulated=True,evaluated_at=f'2026-09-24T{hour}:00:00+00:00')
        flag=self.db.execute('SELECT * FROM flags').fetchone()
        self.assertEqual(flag['status'],'CLEAR')
        self.assertIn('T14:',flag['updated_at'])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM evaluations').fetchone()[0],2)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM evaluation_observations').fetchone()[0],3)
        # A subsequent correction must use the most recently observed input (10).
        c=self.approve_daily('11.00',at='2026-09-25T10:00:00+00:00')
        process_jobs(self.db,[],'2026-09-25',simulated=True,evaluated_at='2026-09-25T11:00:00+00:00')
        row=self.db.execute('SELECT e.data FROM flags f JOIN evaluations e ON e.id=f.evaluation_id').fetchone()
        self.assertEqual(json.loads(row['data'])['employee_input']['hourly_rate_ast'],'10.00')
    def test_manual_check_returns_while_network_is_busy(self):
        entered=threading.Event();release=threading.Event()
        def poll(db,path):
            entered.set();release.wait(3);return {'summary':{'total':48}}
        scheduler=LiveScheduler(Path(self.temp.name)/'worker.db','employees.csv')
        with patch('atlas.scheduler.poll_once',side_effect=poll):
            try:
                self.assertTrue(scheduler.request_check()['checking'])
                self.assertTrue(entered.wait(1))
                self.assertFalse(scheduler.status()['running'])
                with self.assertRaisesRegex(ValueError,'already in progress'):scheduler.request_check()
            finally:
                release.set();scheduler.close()
        self.assertEqual(scheduler.status()['last_result']['summary']['total'],48)
