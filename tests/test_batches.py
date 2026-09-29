import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from atlas.batches import capture_batch, approve_batch, batches, saved_sets, inspection_details, save_resolved_results
from atlas.monitor import ingest
from atlas.store import connect, candidates, review, verify_ledger, now
from atlas.engine import load_employees,run_evaluation
from atlas.batch_impact import batch_impact,batch_impact_csv
from atlas.receipt import build_receipt,verify_receipt
from atlas.workflow import process_jobs
from atlas.result_view import retained_results, source_cleared

ROOT=Path(__file__).resolve().parents[1]
DAY='2026-09-25'


class CombinedReviewTests(unittest.TestCase):
    def test_retrieval_diffs_survive_a_b_a_and_unchanged_checks(self):
        first=self.checks[0]
        changed=ingest(self.db,'federal',self.html['federal'].replace('12.91','13.01'))
        reverted=ingest(self.db,'federal',self.html['federal'])
        unchanged=ingest(self.db,'federal',self.html['federal'])
        self.assertEqual(reverted['snapshot_id'],first['snapshot_id'])
        self.assertEqual(reverted['status'],'CHANGED')
        diff=self.db.execute('SELECT * FROM fetch_diffs WHERE fetch_id=?',(reverted['fetch_id'],)).fetchone()
        self.assertEqual(diff['previous_snapshot_id'],changed['snapshot_id'])
        self.assertTrue(any(line.startswith('-') and '13.01' in line for line in diff['diff'].splitlines()))
        self.assertTrue(any(line.startswith('+') and '12.91' in line for line in diff['diff'].splitlines()))
        self.assertEqual(self.db.execute('SELECT diff FROM fetch_diffs WHERE fetch_id=?',(unchanged['fetch_id'],)).fetchone()[0],'')
        self.assertTrue(verify_ledger(self.db)['valid'])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=connect(Path(self.temp.name)/'test.db')
        self.html={}
        self.checks=[]
        for source in ('federal','bellwether'):
            folder=ROOT/'data/research'/DAY
            meta=json.loads((folder/(source+'.json')).read_text())
            self.html[source]=(folder/meta['filename']).read_text(encoding='utf-8')
            self.checks.append(ingest(self.db,source,self.html[source]))
        self.people=load_employees(ROOT/'data/employees.csv')
    def tearDown(self):
        self.db.close();self.temp.cleanup()
    def approve(self,batch):
        with patch('atlas.batches.source_health',return_value={}):
            return approve_batch(self.db,batch,'APPROVED','Test operator','Checked both source pages.',self.people,DAY)
    def test_two_rates_one_approval_and_one_frozen_employee_set(self):
        batch=capture_batch(self.db,self.checks,DAY)
        self.assertEqual(batch,capture_batch(self.db,self.checks,DAY))
        result=self.approve(batch)
        self.assertEqual(result['state'],'APPROVED')
        self.assertEqual(len(result['results']),48)
        self.assertEqual(len(saved_sets(self.db)),1)
        details=inspection_details(self.db,saved_sets(self.db)[0])
        self.assertEqual(details['actor'],'Test operator')
        self.assertIn('Reviewed both saved sources',details['reason'])
        self.assertEqual(len(details['sources']),2)
        self.assertTrue(all(s['snapshot_id'] and s['approval'] for s in details['sources']))
        self.assertEqual(self.db.execute('SELECT count(*) FROM reviews').fetchone()[0],2)
        original=result['results']
        self.assertEqual(self.approve(batch)['results'],original)
        self.assertTrue(verify_ledger(self.db)['valid'])
    def test_only_federal_changes_state_is_included_without_duplicate_review(self):
        first=capture_batch(self.db,self.checks,DAY);self.approve(first)
        updated=ingest(self.db,'federal',self.html['federal'].replace('12.91','13.01'))
        unchanged=ingest(self.db,'bellwether',self.html['bellwether'])
        second=capture_batch(self.db,[updated,unchanged],DAY)
        self.assertNotEqual(first,second)
        result=self.approve(second)
        self.assertEqual(len(result['rules']),2)
        self.assertEqual(len(result['results']),48)
        self.assertEqual(len(saved_sets(self.db)),2)
        self.assertEqual(self.db.execute('SELECT count(*) FROM reviews').fetchone()[0],3)
    def test_second_review_failure_rolls_back_first(self):
        batch=capture_batch(self.db,self.checks,DAY)
        from atlas.store import review as real_review
        calls=[]
        def fail_second(*args,**kwargs):
            calls.append(1)
            if len(calls)==2:raise ValueError('Injected second-rule failure')
            return real_review(*args,**kwargs)
        with patch('atlas.batches.review',side_effect=fail_second):
            with self.assertRaises(ValueError):self.approve(batch)
        self.assertEqual(self.db.execute('SELECT count(*) FROM reviews').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM jobs').fetchone()[0],0)
        self.assertEqual(batches(self.db)[0]['state'],'REVIEW_REQUIRED')
    def test_failed_source_or_stale_inspection_cannot_approve(self):
        self.assertIsNone(capture_batch(self.db,[self.checks[0],dict(source='bellwether',status='ERROR')],DAY))
        batch=capture_batch(self.db,self.checks,DAY)
        ingest(self.db,'federal',self.html['federal'].replace('12.91','13.01'))
        with self.assertRaisesRegex(ValueError,'Source changed'):self.approve(batch)
        self.assertEqual(self.db.execute('SELECT count(*) FROM reviews').fetchone()[0],0)
    def test_newer_pair_replaces_unapproved_pair_without_leaving_rate_blocker(self):
        first=capture_batch(self.db,self.checks,DAY)
        updated=ingest(self.db,'federal',self.html['federal'].replace('12.91','13.01'))
        second=capture_batch(self.db,[updated,self.checks[1]],DAY)
        self.assertEqual(next(b for b in batches(self.db) if b['id']==first)['state'],'SUPERSEDED')
        self.approve(second)
        daily=[c for c in candidates(self.db) if c['kind']=='DAILY_RATE']
        self.assertEqual(sum(c['state']=='APPROVED' for c in daily),2)
        self.assertEqual(sum(c['state']=='REJECTED' for c in daily),1)
    def test_rejection_keeps_unchanged_approved_rate_and_original_results(self):
        first=capture_batch(self.db,self.checks,DAY);old=self.approve(first)['results']
        updated=ingest(self.db,'federal',self.html['federal'].replace('12.91','13.01'))
        second=capture_batch(self.db,[updated,self.checks[1]],DAY)
        with patch('atlas.batches.source_health',return_value={}):
            approve_batch(self.db,second,'REJECTED','Test operator','Rejected this synthetic changed proposal after checking both sources.',self.people,DAY)
        self.assertEqual(saved_sets(self.db)[0]['results'],old)
        self.assertEqual(sum(c['state']=='APPROVED' for c in candidates(self.db) if c['kind']=='DAILY_RATE'),2)

    def capture_pair(self,federal='12.91',state='16.63',day=DAY):
        checks=[]
        for source in ('federal','bellwether'):
            html=self.html[source].replace('12.91',federal).replace('16.63',state)
            if day!=DAY:html=html.replace('September 25, 2026','September 26, 2026').replace('2026.09.25.1','2026.09.26.1')
            checks.append(ingest(self.db,source,html))
        return capture_batch(self.db,checks,day)

    def acknowledge_coverage(self):
        c=next(c for c in candidates(self.db) if c['source_rule_id']=='AFWA-2026-0038')
        review(self.db,c['id'],'ACKNOWLEDGED','Test operator','Accept supplied Covered field for this isolated assessment fixture.')

    def test_pending_reversion_creates_reviewable_occurrence_and_is_idempotent(self):
        first=self.capture_pair();middle=self.capture_pair('13.01');returned=self.capture_pair()
        self.assertNotIn(returned,(first,middle))
        self.assertEqual(self.capture_pair(),returned)
        self.assertEqual(sum(b['state']=='REVIEW_REQUIRED' for b in batches(self.db)),1)
        self.approve(returned)
        self.assertEqual(next(b['state'] for b in batches(self.db) if b['id']==returned),'APPROVED')

    def test_approved_reversion_requires_review_and_preserves_receipts(self):
        self.acknowledge_coverage()
        first=self.capture_pair();old=self.approve(first)['results']
        receipt=build_receipt(self.db,old[0]['evaluation_id'])
        middle=self.capture_pair('13.01');self.approve(middle)
        returned=self.capture_pair()
        pending=run_evaluation(self.db,self.people,DAY)
        self.assertEqual(pending[0]['decision_state'],'REVIEW_REQUIRED')
        latest=self.approve(returned)['results']
        self.assertEqual(latest[0]['controlling_minimum_wage'],'12.91')
        self.assertEqual(next(b['results'] for b in batches(self.db) if b['id']==first),old)
        self.assertTrue(verify_receipt(receipt)['valid'])
        verified=verify_receipt(build_receipt(self.db,latest[0]['evaluation_id']))
        self.assertTrue(verified['valid'],verified['errors'])
        self.assertEqual(self.capture_pair(),returned)

    def test_rejected_publication_reappearing_after_another_version_needs_new_review(self):
        first=self.capture_pair()
        with patch('atlas.batches.source_health',return_value={}):
            approve_batch(self.db,first,'REJECTED','Test operator','Rejected this isolated publication after examining the captured evidence.',self.people,DAY)
        self.capture_pair('13.01')
        returned=self.capture_pair()
        self.assertNotEqual(returned,first)
        self.assertEqual(next(b['state'] for b in batches(self.db) if b['id']==returned),'REVIEW_REQUIRED')

    def test_combined_preview_compares_both_next_day_rates_without_writes(self):
        self.approve(self.capture_pair())
        pending=self.capture_pair('13.50','18.50','2026-09-26')
        changes=self.db.total_changes
        report=batch_impact(self.db,pending,self.people)
        self.assertEqual(self.db.total_changes,changes)
        self.assertEqual(report['changed_hourly'],32)
        self.assertEqual(report['unresolved_workers'],16)
        worker=next(r for r in report['rows'] if r['employee_id']=='AST-0025')
        self.assertEqual((worker['previous_floor'],worker['new_floor']),('16.63','18.50'))
        self.assertEqual((worker['previous_decision'],worker['new_decision']),('COMPLIANT','NON_COMPLIANT'))
        self.assertIn('AST-0025',batch_impact_csv(report))

    def test_combined_preview_federal_overtakes_unchanged_state(self):
        self.approve(self.capture_pair())
        pending=self.capture_pair('19.00')
        report=batch_impact(self.db,pending,self.people)
        worker=next(r for r in report['rows'] if r['employee_id']=='AST-0025')
        self.assertEqual(worker['new_floor'],'19.00')
        self.assertEqual(report['changed_hourly'],32)

    def test_combined_preview_without_baseline_is_unavailable_not_zero(self):
        report=batch_impact(self.db,self.capture_pair(),self.people)
        self.assertFalse(report['comparison_available'])
        self.assertIsNone(report['changed_hourly'])

    def test_resolved_results_append_a_linked_version_without_overwriting_approval(self):
        batch=self.capture_pair();original=self.approve(batch)['results']
        self.assertTrue(all(r['decision_state']=='REVIEW_REQUIRED' for r in original))
        self.acknowledge_coverage()
        process_jobs(self.db,self.people,now()[:10])
        self.assertEqual(self.db.execute('SELECT count(*) FROM batch_result_versions').fetchone()[0],1)
        current=run_evaluation(self.db,self.people,DAY)
        version=save_resolved_results(self.db,current,DAY)
        self.assertEqual(save_resolved_results(self.db,current,DAY),version)
        saved=saved_sets(self.db)
        self.assertEqual(len(saved),2)
        self.assertEqual(saved[0]['parent_batch_id'],batch)
        self.assertEqual(saved[0]['result_label'],'Resolved results')
        self.assertEqual(sum(r['decision_state']=='REVIEW_REQUIRED' for r in saved[0]['results']),16)
        self.assertEqual(next(b['results'] for b in saved if b['id']==batch),original)
        self.assertEqual(inspection_details(self.db,saved[0])['actor'],'Test operator')
        self.assertIn('Reviewed both saved sources',inspection_details(self.db,saved[0])['reason'])

    def test_cold_browser_recovers_approved_same_day_results(self):
        self.acknowledge_coverage()
        old=self.approve(self.capture_pair())['results']
        self.assertTrue(source_cleared(old))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM result_views').fetchone()[0],0)
        self.capture_pair('13.50')
        pending=run_evaluation(self.db,self.people,DAY)
        self.assertTrue(all(r['decision_state']=='REVIEW_REQUIRED' for r in pending))
        displayed,date=retained_results(self.db,pending,DAY)
        self.assertEqual((displayed,date),(old,DAY))
        self.assertTrue(verify_receipt(build_receipt(self.db,displayed[0]['evaluation_id']))['valid'])

    def test_retention_uses_newer_inspection_instead_of_stale_same_day_cache(self):
        self.acknowledge_coverage()
        old=self.approve(self.capture_pair())['results']
        retained_results(self.db,old,DAY)
        newer=self.approve(self.capture_pair('13.50'))['results']
        self.assertTrue(source_cleared(newer))
        self.capture_pair('14.00')
        pending=run_evaluation(self.db,self.people,DAY)
        self.assertEqual(retained_results(self.db,pending,DAY),(newer,DAY))
        self.assertNotEqual(newer[0]['evaluation_id'],old[0]['evaluation_id'])

    def test_cold_browser_recovers_resolved_set_not_blocked_approval_snapshot(self):
        batch=self.capture_pair()
        blocked=self.approve(batch)['results']
        self.assertFalse(source_cleared(blocked))
        self.acknowledge_coverage()
        resolved=run_evaluation(self.db,self.people,DAY)
        save_resolved_results(self.db,resolved,DAY)
        self.capture_pair('13.50')
        pending=run_evaluation(self.db,self.people,DAY)
        self.assertEqual(retained_results(self.db,pending,DAY),(resolved,DAY))
