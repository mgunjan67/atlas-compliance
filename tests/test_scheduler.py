"""The UI-owned monitor starts immediately, stops, and prevents overlapping polls."""
import threading
import time
import unittest
from unittest.mock import patch

from atlas.scheduler import LiveScheduler


class SchedulerTests(unittest.TestCase):
    def test_failed_manual_check_clears_busy_and_does_not_show_old_success(self):
        with patch('atlas.scheduler.connect',return_value=FakeConnection()),patch('atlas.scheduler.poll_once',side_effect=OSError('Archive write failed')):
            scheduler=LiveScheduler('unused.db','employees.csv')
            scheduler._last_result={'summary':{'total':48}}
            scheduler.request_check()
            scheduler._manual_thread.join(2)
            state=scheduler.status()
            self.assertFalse(state['checking'])
            self.assertIsNone(state['last_result'])
            self.assertEqual(state['last_error'],'Archive write failed')
            self.assertIsNotNone(state['started_at'])
    def test_start_runs_one_poll_and_stop_prevents_repeat(self):
        checked = threading.Event()
        calls = []

        def fake_poll(db, employees):
            calls.append(employees)
            checked.set()
            return {'checked_at': '2026-09-25T09:00:00+00:00', 'checks': [], 'summary': {'total': 48}}

        with patch('atlas.scheduler.connect', return_value=FakeConnection()), patch('atlas.scheduler.poll_once', side_effect=fake_poll):
            scheduler = LiveScheduler('unused.db', 'employees.csv', interval=0.1)
            try:
                self.assertTrue(scheduler.start()['running'])
                self.assertTrue(checked.wait(2))
                self.assertTrue(scheduler.status()['running'])
                scheduler.stop()
                scheduler.close()
                time.sleep(0.15)
                self.assertEqual(calls, ['employees.csv'])
                self.assertFalse(scheduler.status()['running'])
                self.assertEqual(scheduler.status()['last_result']['summary']['total'], 48)
            finally:
                scheduler.close()

    def test_manual_check_rejects_overlap(self):
        entered = threading.Event()
        release = threading.Event()

        def fake_poll(db, employees):
            entered.set()
            release.wait(2)
            return {'summary': {'total': 48}}

        with patch('atlas.scheduler.poll_once', side_effect=fake_poll):
            scheduler = LiveScheduler('unused.db', 'employees.csv')
            worker = threading.Thread(target=lambda: scheduler.check_now(object()))
            worker.start()
            try:
                self.assertTrue(entered.wait(2))
                with self.assertRaisesRegex(ValueError, 'already in progress'):
                    scheduler.check_now(object())
            finally:
                release.set()
                worker.join(2)


class FakeConnection:
    def close(self):
        pass
