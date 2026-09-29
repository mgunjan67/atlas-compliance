"""Run the current classifier on fictional cases. Requires GROQ_API_KEY."""
import json
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from atlas.ai_sandbox import CASES
from atlas.ai_provider import suggest,VERSION,MODEL

def main():
    rows=[]
    folder=Path(__file__).resolve().parents[1]/'output'/'ai-evaluation'
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    for case in CASES:
        start=time.monotonic()
        try:
            result=suggest(case['segments'])
            row={'id':case['id'],'expected':case['expected'],'result':result,'matched':result['category']==case['expected']}
        except Exception as exc:
            row={'id':case['id'],'error':type(exc).__name__,'matched':False}
        row['seconds_including_pacing']=round(time.monotonic()-start,2)
        rows.append(row)
        report={'model':MODEL,'prompt_version':VERSION,'cases':rows,'matched':sum(r['matched'] for r in rows),'total':len(rows)}
        path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in row.items() if k!='result'}),flush=True)
        if 'error' in row:break
    print('Saved '+str(path))

if __name__=='__main__':main()
