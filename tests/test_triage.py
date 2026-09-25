import unittest
import csv
import json
import tempfile
from pathlib import Path

from atlas.engine import evaluate, export_results
from atlas.triage import enrich_result


def employee(**changes):
    row = dict(employee_id='E1', work_country='Asteria', work_state='Federal Territory',
               pay_basis='Annual Salary', hourly_rate_ast='', annual_salary_ast='20800',
               scheduled_hours_per_week='40', currency='AST', employment_status='Active',
               minimum_wage_coverage='Covered', start_date='2020-01-01')
    row.update(changes)
    return row


def rule(id, jurisdiction, amount, **changes):
    row = dict(id=id, source_rule_id=id, jurisdiction=jurisdiction, amount=amount,
               effective_from='2026-09-24', effective_to='2026-09-25', state='APPROVED',
               classification='RATE_REVIEW', currency='AST', unit='hour',
               source_url='https://example.invalid', evidence='Synthetic evidence', supersedes=None)
    row.update(changes)
    return row


class TriageTests(unittest.TestCase):
    def test_salary_proxy_and_approved_floor_do_not_change_decision(self):
        original = evaluate(employee(), [rule('F', 'Asteria', '12.73')], '2026-09-24')
        enriched = enrich_result(original)
        context = enriched['analysis_context']
        self.assertEqual(original['decision_state'], 'REVIEW_REQUIRED')
        self.assertIsNone(original['actual_hourly_wage'])
        self.assertIsNone(original['controlling_minimum_wage'])
        self.assertEqual((context['indicative_salary_hourly'], context['approved_reference_floor']), ('10.00', '12.73'))
        self.assertEqual((context['indicative_hourly_gap_to_reference'], context['indicative_weekly_gap_to_reference']), ('2.73', '109.20'))
        self.assertEqual(len(context['salary_review_requirements']), 3)
        self.assertIn('Actual hours worked', context['salary_review_requirements'][1])
        self.assertNotIn('analysis_context', original)

    def test_future_start_salary_review_calls_out_both_blockers(self):
        original = evaluate(employee(start_date='2026-10-01'), [rule('F', 'Asteria', '12.73')], '2026-09-24')
        context = enrich_result(original)['analysis_context']
        self.assertEqual(original['reason_code'], 'FUTURE_START_CONFLICT')
        self.assertIsNone(original['actual_hourly_wage'])
        self.assertIn('start date', context['salary_review_requirements'][0])
        self.assertTrue(any('annual salary' in item for item in context['salary_review_requirements']))

    def test_pending_correction_keeps_final_floor_unresolved(self):
        hourly = employee(work_state='Bellwether', pay_basis='Hourly', hourly_rate_ast='17.32', annual_salary_ast='')
        rules = [rule('F', 'Asteria', '12.73'), rule('S', 'Bellwether', '16.63'),
                 rule('P', 'Bellwether', '18.50', state='REVIEW_REQUIRED')]
        result = enrich_result(evaluate(hourly, rules, '2026-09-24'))
        self.assertEqual(result['decision_state'], 'REVIEW_REQUIRED')
        self.assertIsNone(result['controlling_minimum_wage'])
        self.assertEqual(result['analysis_context']['approved_reference_floor'], '16.63')
        self.assertEqual([p['amount'] for p in result['analysis_context']['pending_rate_candidates']], ['18.50'])

    def test_pending_rule_does_not_hide_recorded_gap_to_approved_floor(self):
        hourly = employee(work_state='Bellwether', pay_basis='Hourly', hourly_rate_ast='15.00', annual_salary_ast='')
        rules = [rule('F', 'Asteria', '12.73'), rule('S', 'Bellwether', '16.63'),
                 rule('P', 'Bellwether', '18.50', state='REVIEW_REQUIRED')]
        result = enrich_result(evaluate(hourly, rules, '2026-09-24'))
        self.assertEqual(result['decision_state'], 'REVIEW_REQUIRED')
        self.assertEqual(result['analysis_context']['recorded_hourly_gap_to_reference'], '1.63')
        self.assertEqual(result['analysis_context']['recorded_weekly_gap_to_reference'], '65.20')

    def test_incomplete_or_conflicting_rules_have_no_reference_floor(self):
        for rules in ([rule('F', 'Asteria', '12.73')],
                      [rule('F', 'Asteria', '12.73'), rule('S', 'Bellwether', '16.63'),
                       rule('S2', 'Bellwether', '18.50')]):
            with self.subTest(rules=len(rules)):
                result = enrich_result(evaluate(employee(work_state='Bellwether'), rules, '2026-09-24'))
                self.assertIsNone(result['analysis_context']['approved_reference_floor'])

    def test_future_rule_and_invalid_salary_do_not_create_false_values(self):
        rules = [rule('F', 'Asteria', '12.73'),
                 rule('Future', 'Asteria', '20.00', effective_from='2027-01-01', effective_to=None)]
        result = enrich_result(evaluate(employee(annual_salary_ast='NaN'), rules, '2026-09-24'))
        self.assertIsNone(result['analysis_context']['indicative_salary_hourly'])
        self.assertEqual(result['analysis_context']['approved_reference_floor'], '12.73')

    def test_json_and_csv_exports_keep_analysis_separate_from_decision(self):
        result = evaluate(employee(), [rule('F', 'Asteria', '12.73')], '2026-09-24')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'results.json'
            export_results([result], path)
            saved = json.loads(path.read_text(encoding='utf-8'))[0]
            with path.with_suffix('.csv').open(encoding='utf-8', newline='') as stream:
                row = next(csv.DictReader(stream))
        self.assertEqual(saved['decision_state'], 'REVIEW_REQUIRED')
        self.assertIsNone(saved['actual_hourly_wage'])
        self.assertEqual(saved['analysis_context']['indicative_salary_hourly'], '10.00')
        self.assertEqual(row['indicative_salary_hourly'], '10.00')
        self.assertEqual(row['approved_reference_floor'], '12.73')


if __name__ == '__main__':
    unittest.main()
