"""On-demand fictional notice tests; no approval or employee database access."""
import threading
import time
import json
from pathlib import Path
from .ai_provider import suggest,AIUnavailable
CASES=json.loads(Path(__file__).with_name('ai_cases.json').read_text(encoding='utf-8'))

def classify(case):
    result=suggest(case['segments'])
    return {**result,'expected':case['expected'],'matches_expected':result['category']==case['expected'],
            'parser':case['parser'],'review_state':'REVIEW_REQUIRED'}

class AISandbox:
    def __init__(self,runner=classify):
        self.runner=runner
        self.lock=threading.Lock()
        self.job={'status':'idle'}
        self.last_started=0

    def status(self):
        with self.lock:return dict(self.job)

    def start(self,case_id):
        case=next((c for c in CASES if c['id']==case_id),None)
        if case is None:raise ValueError('Choose a supplied dummy notice.')
        with self.lock:
            if self.job['status']=='running':raise ValueError('An AI test is already running.')
            if time.monotonic()-self.last_started<8:raise ValueError('Wait a few seconds before running another test.')
            self.last_started=time.monotonic()
            self.job={'status':'running','case_id':case_id}
        threading.Thread(target=self._run,args=(case,),daemon=True).start()
        return self.status()

    def _run(self,case):
        start=time.monotonic()
        try:
            result=self.runner(case)
            job={'status':'done','case_id':case['id'],'result':result,'seconds':round(time.monotonic()-start,2)}
        except (ValueError,AIUnavailable) as exc:job={'status':'error','case_id':case['id'],'error':str(exc)}
        except Exception:job={'status':'error','case_id':case['id'],'error':'AI service unavailable or timed out. Try again later; live results are unchanged.'}
        with self.lock:self.job=job
