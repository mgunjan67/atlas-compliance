import threading
import unittest
from atlas.ai_sandbox import AISandbox

class AISandboxTests(unittest.TestCase):
    def test_background_and_duplicate_protection(self):
        release=threading.Event()
        def runner(case):
            release.wait(2)
            return {'category':'final_rate'}
        service=AISandbox(runner)
        self.assertEqual(service.start('standard-final')['status'],'running')
        with self.assertRaises(ValueError):service.start('standard-final')
        release.set()

    def test_unknown_input_never_calls_model(self):
        service=AISandbox(lambda case:self.fail('Unexpected inference'))
        with self.assertRaises(ValueError):service.start('not-a-fixture')
        self.assertEqual(service.status()['status'],'idle')

    def test_service_failure_does_not_expose_exception(self):
        def fail(case):raise RuntimeError('secret diagnostic')
        service=AISandbox(fail)
        service._run({'id':'standard-final'})
        self.assertEqual(service.status()['status'],'error')
        self.assertNotIn('secret',service.status()['error'])

if __name__=='__main__':unittest.main()
