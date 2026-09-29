import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from atlas.dummy import run_dummy,list_runs
from atlas.store import connect
from atlas.lab import worker


class DummyTests(unittest.TestCase):
    def test_saved_test_uses_higher_rate_and_never_changes_live_tables(self):
        with tempfile.TemporaryDirectory() as folder:
            db=connect(Path(folder)/'db')
            result=run_dummy(db,[worker(hourly_rate_ast='18')],'19','16','2026-09-28','Federal higher')
            self.assertEqual(result['results'][0]['controlling_minimum_wage'],'19.00')
            self.assertEqual(result['results'][0]['decision_state'],'NON_COMPLIANT')
            self.assertTrue(result['results'][0]['scenario_only'])
            self.assertEqual(list_runs(db)[0],result)
            for table in ('reviews','candidates','evaluations','flags','jobs','audit','review_batches'):
                self.assertEqual(db.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
            db.close()
    def test_comparison_equality_and_salary_abstention(self):
        with tempfile.TemporaryDirectory() as folder:
            db=connect(Path(folder)/'db')
            baseline=dict(evaluation_date='2026-09-27',rules=[dict(jurisdiction='Asteria',amount='12'),dict(jurisdiction='Bellwether',amount='16')])
            people=[worker(hourly_rate_ast='18'),worker(employee_id='SALARY',pay_basis='Annual Salary',hourly_rate_ast='',annual_salary_ast='40000')]
            with patch('atlas.dummy.saved_sets',return_value=[baseline]):
                result=run_dummy(db,people,'18','16','2026-09-28')
            self.assertEqual(result['results'][0]['decision_state'],'COMPLIANT')
            self.assertEqual(result['results'][1]['reason_code'],'SALARY_CONVERSION_UNAPPROVED')
            self.assertEqual(len(result['changes']),1)
            db.close()
    def test_invalid_input_is_not_saved(self):
        with tempfile.TemporaryDirectory() as folder:
            db=connect(Path(folder)/'db')
            for value in ('','NaN','-1','0'):
                with self.assertRaises(ValueError):run_dummy(db,[worker()],value,'16','2026-09-28')
            self.assertEqual(list_runs(db),[])
            db.close()
