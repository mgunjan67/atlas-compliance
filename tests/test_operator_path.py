"""The live review path shown to an operator must have a clear outcome."""
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from atlas.__main__ import seed
from atlas.engine import load_employees, run_evaluation
from atlas.store import candidates, connect, review


ROOT = Path(__file__).resolve().parents[1]
DAY = '2026-09-25'


class OperatorPathTests(unittest.TestCase):
    def test_rate_approvals_do_not_hide_a_coverage_blocker(self):
        with tempfile.TemporaryDirectory() as folder:
            db = connect(Path(folder) / 'live.db')
            try:
                seed(db, ROOT / 'data/research' / DAY)
                people = load_employees(ROOT / 'data/employees.csv')
                by_rule = {c['source_rule_id']: c for c in candidates(db)}
                for rule_id in ('AFWA-MW-2026.1', 'BDL-MW-2026.1'):
                    review(db, by_rule[rule_id]['id'], 'APPROVED', 'Test reviewer',
                           'Checked captured amount, effective date and covered scope.')
                before = run_evaluation(db, people, DAY)
                reasons = Counter(r['reason_code'] for r in before)
                self.assertEqual(reasons['PENDING_SOURCE_REVIEW'], 32)
                self.assertEqual(reasons['SALARY_CONVERSION_UNAPPROVED'], 12)
                self.assertEqual(reasons['FUTURE_START_CONFLICT'], 4)

                review(db, by_rule['AFWA-2026-0038']['id'], 'ACKNOWLEDGED', 'Test reviewer',
                       'For this assessment, accept the supplied Covered field as the upstream coverage determination.')
                after = run_evaluation(db, people, DAY)
                states = Counter(r['decision_state'] for r in after)
                self.assertEqual(states['COMPLIANT'] + states['NON_COMPLIANT'], 32)
                self.assertEqual(states['REVIEW_REQUIRED'], 16)
                self.assertNotIn('PENDING_SOURCE_REVIEW', {r['reason_code'] for r in after})
            finally:
                db.close()


if __name__ == '__main__':
    unittest.main()
