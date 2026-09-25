import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from .store import connect, candidates, review, audit, digest
from .monitor import ingest, fetch_source
from .extract import SOURCES
from .engine import load_employees, run_evaluation, export_results

def today(): return datetime.now(timezone.utc).date().isoformat()

def seed(db, directory):
    output=[]
    for source in SOURCES:
        meta=json.loads((Path(directory)/(source+'.json')).read_text(encoding='utf-8'))
        html=(Path(directory)/meta['filename']).read_text(encoding='utf-8')
        if digest(html)!=meta['sha256']: raise ValueError('Saved evidence checksum mismatch')
        output.append(ingest(db,source,html,meta['retrieved_at']))
    return output

def summary(results): return dict(Counter(r['decision_state'] for r in results))

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='Atlas fictional wage compliance prototype')
    p.add_argument('--db',default='data/atlas-v2.sqlite3')
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('seed',help='Import saved public-source evidence; does not approve rules')
    s.add_argument('--directory',default='data/research')
    sub.add_parser('fetch',help='Retrieve both allowlisted source pages')
    sub.add_parser('candidates',help='Print proposed rules and review states')
    r=sub.add_parser('review',help='Record a human operator decision')
    r.add_argument('id'); r.add_argument('decision',choices=['APPROVED','REJECTED','ACKNOWLEDGED'])
    r.add_argument('--actor',required=True); r.add_argument('--reason',required=True); r.add_argument('--supersedes')
    e=sub.add_parser('evaluate')
    e.add_argument('--employees',default='data/employees.csv');e.add_argument('--date',default=today())
    e.add_argument('--annualize-salary',action='store_true',help='Explicit 52-week estimate scenario, not legally validated')
    e.add_argument('--known-at',help='ISO UTC timestamp: evaluate with rules known at this time')
    e.add_argument('--output',default='output/live-results.json')
    w=sub.add_parser('watch',help='Foreground monitor and evaluator; Ctrl+C stops')
    w.add_argument('--employees',default='data/employees.csv');w.add_argument('--interval',type=int,default=900)
    w.add_argument('--output',default='output/live-results.json');w.add_argument('--archive-root',default='output/live-archive')
    poll=sub.add_parser('poll-once',help='Fetch both sources, evaluate today and archive this run')
    poll.add_argument('--employees',default='data/employees.csv')
    poll.add_argument('--output',default='output/live-results.json')
    poll.add_argument('--archive-root',default='output/live-archive')
    d=sub.add_parser('demo');d.add_argument('--output',default='output');
    a=sub.add_parser('audit');a.add_argument('--output',default='output/audit.json')
    s=sub.add_parser('serve');s.add_argument('--port',type=int,default=8787);s.add_argument('--employees',default='data/employees.csv');s.add_argument('--demo-db')
    lab=sub.add_parser('lab');lab.add_argument('--output',default='output/lab-report.json')
    story=sub.add_parser('story');story.add_argument('--output',default='output/reviewer-story')
    rc=sub.add_parser('receipt');rc.add_argument('id');rc.add_argument('--output',default='output/decision-receipt.json')
    v=sub.add_parser('verify');v.add_argument('file');v.add_argument('--expected-digest')
    sub.add_parser('verify-audit')
    jobs=sub.add_parser('process-jobs');jobs.add_argument('--date',default=today());jobs.add_argument('--employees',default='data/employees.csv')
    ai=sub.add_parser('ai-audit');ai.add_argument('snapshot_id')
    args=p.parse_args()
    if args.command=='demo' and args.db=='data/atlas-v2.sqlite3': args.db='data/demo-v2.sqlite3'
    if args.command=='story' and args.db=='data/atlas-v2.sqlite3': args.db='data/story-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.sqlite3'
    # Portable receipt verification and the synthetic lab do not need a database.
    # Keep them runnable from a read-only handoff directory.
    db=None if args.command in ('verify','lab') else connect(args.db)
    try:
        if args.command=='seed': out=seed(db,args.directory)
        elif args.command=='fetch': out=[fetch_source(db,s) for s in SOURCES]
        elif args.command=='candidates': out=candidates(db)
        elif args.command=='review':
            review(db,args.id,args.decision,args.actor,args.reason,args.supersedes)
            out={'reviewed':args.id,'decision':args.decision}
        elif args.command=='evaluate':
            results=run_evaluation(db,load_employees(args.employees),args.date,args.annualize_salary,known_at=args.known_at)
            export_results(results,args.output);out={'results':args.output,'counts':summary(results)}
        elif args.command=='audit':
            out=[dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id')]
            path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(out,indent=2),encoding='utf-8');out={'audit':args.output,'events':len(out)}
        elif args.command=='demo':
            from .demo import run_demo
            out=run_demo(db,args.output)
        elif args.command=='serve':
            from .web import serve
            db.close();serve(args.db,args.employees,args.port,args.demo_db);return
        elif args.command=='lab':
            from .lab import write_report
            result=write_report(args.output)
            out={'output':args.output,'all_pass':result['all_pass'],'golden_cases':len(result['golden_cases']),
                 'oracle_cases':result['oracle']['cases'],'mutations':len(result['mutations'])}
            if not result['all_pass']:raise ValueError('Lab failure; inspect '+args.output)
        elif args.command=='story':
            from .showcase import full_story
            db.close();report=full_story(args.db,args.output)
            out={'database':args.db,'output':args.output,'before':report['before'],'after':report['after'],
                 'historical_knowledge_reproduced':report['historical_knowledge_reproduced'],
                 'case_study':report['case_study'],'receipt_valid':report['original_receipt_after_correction']['valid']}
        elif args.command=='receipt':
            from .receipt import build_receipt
            result=build_receipt(db,args.id);path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(result,indent=2),encoding='utf-8');out={'file':args.output,'sha256':result['sha256']}
        elif args.command=='verify':
            from .receipt import verify_receipt
            out=verify_receipt(json.loads(Path(args.file).read_text(encoding='utf-8')),args.expected_digest)
            if not out['valid']:raise ValueError('Receipt failed verification: '+str(out['errors']))
        elif args.command=='verify-audit':
            from .store import verify_ledger
            out=verify_ledger(db)
            if not out['valid']:raise ValueError('Audit verification failed: '+str(out))
        elif args.command=='process-jobs':
            from .workflow import process_jobs
            out=process_jobs(db,load_employees(args.employees),args.date)
        elif args.command=='ai-audit':
            from .ai import audit_snapshot
            out=audit_snapshot(db,args.snapshot_id)
        elif args.command=='poll-once':
            from .operations import poll_once
            out=poll_once(db,args.employees,args.output,args.archive_root)
        elif args.command=='watch':
            if args.interval<30: raise ValueError('Polling interval must be at least 30 seconds')
            from .operations import poll_once
            print('Monitoring both public sources; rules always require explicit review. Ctrl+C stops.',flush=True)
            while True:
                out=poll_once(db,args.employees,args.output,args.archive_root)
                print(json.dumps(out,ensure_ascii=False),flush=True)
                time.sleep(args.interval)
        print(json.dumps(out,indent=2,ensure_ascii=False))
    except KeyboardInterrupt: print('Stopped.')
    except (ValueError,OSError) as exc:
        print('Atlas error: '+str(exc),file=sys.stderr);sys.exit(1)
    finally:
        if db is not None: db.close()

if __name__=='__main__': main()
