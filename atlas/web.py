"""Local reviewer console with isolated dummy-rate tests."""
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .store import connect,candidates,review,verify_ledger
from .engine import load_employees,run_evaluation,source_health,implemented_guidance
from .workflow import impact_preview,rate_change_report,rate_change_csv,process_jobs,summarize
from .receipt import build_receipt,verify_receipt
from .scheduler import LiveScheduler
from .triage import enrich_results
from .result_view import retained_results, retention_context, export_results
from .snapshot_view import snapshot_page
from .batches import batches, capture_batch, approve_batch, saved_sets, inspection_details, save_resolved_results
from .batch_impact import batch_impact, batch_impact_csv
from .dummy import list_runs, run_dummy

STATIC=Path(__file__).with_name('static')

def serve(db_path,employees_path,port):
    token=secrets.token_urlsafe(32)
    scheduler=LiveScheduler(db_path,employees_path)
    class Handler(BaseHTTPRequestHandler):
        def respond(self,body,status=200,content_type='application/json; charset=utf-8',filename=None):
            raw=body if isinstance(body,bytes) else (body if isinstance(body,str) else json.dumps(body,ensure_ascii=False)).encode()
            self.send_response(status);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(raw)))
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'")
            if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
            self.end_headers();self.wfile.write(raw)
        def valid_host(self):return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
        def context(self,params):
            if params.get('mode','live')!='live':raise ValueError('Only the live workspace is available; use Scenario lab for dummy tests')
            return connect(db_path),False
        def do_GET(self):
            if not self.valid_host():return self.respond({'error':'Invalid host'},403)
            path=urlparse(self.path);params={k:v[0] for k,v in parse_qs(path.query).items()}
            if path.path=='/api/monitor/status':
                return self.respond(scheduler.status())
            if path.path in ('/','/app.js','/style.css'):
                file={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[path.path]
                typ={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[path.path]
                return self.respond((STATIC/file).read_text(encoding='utf-8'),content_type=typ)
            # Explicit asset allowlist: no user-controlled filesystem paths.
            if path.path in ('/fonts/inter-latin.woff2','/fonts/intertight-latin.woff2'):
                return self.respond((STATIC/path.path.lstrip('/')).read_bytes(),content_type='font/woff2')
            if path.path=='/favicon.svg':
                return self.respond((STATIC/'favicon.svg').read_text(encoding='utf-8'),content_type='image/svg+xml')
            db=None
            try:
                db,simulated=self.context(params)
                day=params.get('date',datetime.now(timezone.utc).date().isoformat())
                employees=load_employees(employees_path)
                operational_day=simulated or day==datetime.now(timezone.utc).date().isoformat()
                if path.path=='/api/dummy-tests':
                    runs=list_runs(db)
                    if params.get('id'):
                        run=next((r for r in runs if r['id']==params['id']),None)
                        if not run:raise ValueError('Dummy test not found')
                        return self.respond(run,filename='atlas-dummy-results.json' if params.get('download') else None)
                    return self.respond([{k:v for k,v in r.items() if k not in ('results','changes')} for r in runs])
                if path.path=='/api/saved-results':
                    if simulated:raise ValueError('Combined saved results belong to the live workspace')
                    saved=next((s for s in saved_sets(db) if s['id']==params['id']),None)
                    if not saved:raise ValueError('Saved inspection result not found')
                    saved['inspection']=inspection_details(db,saved)
                    saved['results']=enrich_results(saved['results'])
                    saved['basis']='Saved combined employee results. Original dates and receipts are preserved; nothing is recalculated.'
                    return self.respond(saved,filename='atlas-inspection-results.json' if params.get('download') else None)
                if path.path=='/api/state':
                    if not simulated and not params.get('known_at'):
                        poll=db.execute("SELECT data FROM audit WHERE event='LIVE_POLL_ARCHIVED' ORDER BY id DESC LIMIT 1").fetchone()
                        if poll:
                            recorded=json.loads(poll[0])
                            capture_batch(db,recorded['source_checks'],recorded['evaluation_date'])
                    results=run_evaluation(db,employees,day,simulated=simulated,known_at=params.get('known_at'),
                                           update_flags=operational_day)
                    if not simulated and not params.get('known_at'):save_resolved_results(db,results,day)
                    cutoff=results[0]['knowledge_cutoff'] if results else params.get('known_at')
                    items=[c for c in candidates(db,cutoff) if c['simulated']==simulated]
                    items=[dict(c,policy_applied=implemented_guidance(c)) for c in items]
                    fetches=[dict(r) for r in db.execute('SELECT f.*,d.previous_snapshot_id,d.diff AS retrieval_diff FROM fetches f LEFT JOIN fetch_diffs d ON d.fetch_id=f.id WHERE f.simulated=? ORDER BY f.id DESC LIMIT 12',(int(simulated),))]
                    for c in items:
                        latest=next((f for f in fetches if f['source']==c['source']),None)
                        c['seen_in_latest_check']=bool(latest and latest['status']!='ERROR' and db.execute(
                            'SELECT 1 FROM evidence_links WHERE candidate_id=? AND snapshot_id=?',
                            (c['id'],latest['snapshot_id'])).fetchone())
                    events=[dict(r) for r in db.execute('SELECT a.*,l.entry_hash FROM audit a LEFT JOIN ledger l ON l.event_id=a.id ORDER BY a.id DESC LIMIT 120')]
                    for event in events:event['data']=json.loads(event['data'])
                    jobs=[dict(r) for r in db.execute('SELECT * FROM jobs WHERE simulated=? ORDER BY created_at DESC',(int(simulated),))]
                    displayed, retained_date = (results, None) if simulated or params.get('known_at') or not operational_day else retained_results(db, results, day)
                    return self.respond({'mode':'demo' if simulated else 'live','simulated':simulated,'date':day,'csrf':token,
                                         'summary':summarize(displayed),'results':enrich_results(displayed),
                                         'retained_results_date':retained_date,'retention':retention_context(results,displayed,retained_date),'current_summary':summarize(results),
                                         'review_batches':[{k:v for k,v in b.items() if k not in ('results','data','employee_inputs')} for b in batches(db)] if not simulated else [],
                                         'saved_result_sets':[{k:v for k,v in s.items() if k!='results'} for s in saved_sets(db)] if not simulated else [],
                                         'candidates':items,'fetches':fetches,'events':events,
                                         'jobs':jobs,'ledger':verify_ledger(db),'health':source_health(db,day,simulated,cutoff),
                                         'monitor':scheduler.status()})
                if path.path=='/api/batch-impact':
                    if simulated:raise ValueError('Combined inspections belong to the live workspace')
                    report=batch_impact(db,params['id'],employees)
                    if params.get('format')=='csv':return self.respond(batch_impact_csv(report),content_type='text/csv; charset=utf-8',filename='atlas-combined-impact.csv')
                    return self.respond(report)
                if path.path=='/api/impact':return self.respond(impact_preview(db,employees,params['id'],day,params.get('supersedes') or None))
                if path.path=='/api/rate-change':
                    if params['id'] not in {c['id'] for c in candidates(db,params.get('known_at')) if c['simulated']==simulated}:
                        raise ValueError('Candidate does not belong to this workspace')
                    report=rate_change_report(db,employees,params['id'],params.get('supersedes') or None,params.get('known_at'))
                    if params.get('format')=='csv':
                        return self.respond(rate_change_csv(report),content_type='text/csv; charset=utf-8',
                                            filename='atlas-rate-change-'+report['evaluation_date']+'.csv')
                    return self.respond(report)
                if path.path=='/api/receipt':
                    receipt=build_receipt(db,params['id'])
                    if params.get('verify'):return self.respond(verify_receipt(receipt))
                    return self.respond(receipt,filename='atlas-decision-receipt.json')
                if path.path=='/api/export':
                    results=run_evaluation(db,employees,day,simulated=simulated,known_at=params.get('known_at'),update_flags=operational_day)
                    if not simulated and not params.get('known_at') and operational_day:
                        displayed,retained_date=retained_results(db,results,day)
                        results=export_results(results,displayed,retained_date)
                    return self.respond(enrich_results(results),filename='atlas-employee-results.json')
                if path.path=='/api/snapshot':
                    row=db.execute('SELECT * FROM snapshots WHERE id=? AND simulated=?',(params.get('id',''),int(simulated))).fetchone()
                    if not row:return self.respond('Not found',404,'text/plain; charset=utf-8')
                    if params.get('format')=='raw':
                        return self.respond(row['raw_html'],content_type='text/plain; charset=utf-8',filename='atlas-saved-source.html')
                    return self.respond(snapshot_page(row,'demo' if simulated else 'live'),content_type='text/html; charset=utf-8')
                if path.path=='/api/lab':
                    from .lab import report
                    return self.respond(report())
                return self.respond({'error':'Not found'},404)
            except (ValueError,KeyError,sqlite3.Error) as exc:return self.respond({'error':str(exc)},400)
            finally:
                if db:db.close()
        def do_POST(self):
            if not self.valid_host():return self.respond({'error':'Invalid host'},403)
            if not secrets.compare_digest(self.headers.get('X-Atlas-CSRF',''),token):return self.respond({'error':'Invalid request token'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<20000:raise ValueError('Invalid request size')
                params=json.loads(self.rfile.read(size))
                if not isinstance(params,dict):raise ValueError('Expected JSON object')
            except (ValueError,json.JSONDecodeError):return self.respond({'error':'Invalid request'},400)
            db=None
            try:
                db,simulated=self.context(params)
                day=params.get('date',datetime.now(timezone.utc).date().isoformat())
                if self.path=='/api/dummy-test':
                    return self.respond(run_dummy(db,load_employees(employees_path),params.get('federal',''),params.get('state',''),params.get('test_date',day),params.get('name','')))
                if self.path=='/api/review':
                    candidate=next((c for c in candidates(db) if c['id']==params.get('id')),None)
                    if not candidate or candidate['simulated']!=simulated:raise ValueError('Candidate does not belong to this workspace')
                    if not simulated and candidate['kind']=='DAILY_RATE':raise ValueError('Review federal and state daily rates together using the combined update')
                    review(db,params['id'],params['decision'],params.get('actor',''),params.get('reason',''),params.get('supersedes') or None,
                           allow_simulated=False)
                    # The date picker is an evaluation scenario, not the operational clock.
                    # A reviewer viewing a future date must not complete a future activation job early.
                    job_day=datetime.now(timezone.utc).date().isoformat()
                    jobs=process_jobs(db,load_employees(employees_path),job_day,simulated=False)
                    return self.respond({'reviewed':params['id'],'jobs':jobs})
                if self.path=='/api/review-batch':
                    if simulated:raise ValueError('Combined updates belong to the live workspace')
                    if params.get('checked') is not True:raise ValueError('Confirm that you inspected both saved sources')
                    result=approve_batch(db,params['id'],params['decision'],params.get('actor',''),params.get('note',''),load_employees(employees_path),datetime.now(timezone.utc).date().isoformat())
                    return self.respond({'reviewed':result['id'],'state':result['state']})
                if self.path=='/api/fetch':
                    if simulated:raise ValueError('Live source retrieval belongs in the live workspace')
                    return self.respond(scheduler.request_check(),202)
                if self.path=='/api/monitor/start':
                    if simulated:raise ValueError('Scheduled checks belong in the live workspace')
                    return self.respond(scheduler.start())
                if self.path=='/api/monitor/stop':
                    if simulated:raise ValueError('Scheduled checks belong in the live workspace')
                    return self.respond(scheduler.stop())
                return self.respond({'error':'Not found'},404)
            except (ValueError,KeyError,sqlite3.Error) as exc:return self.respond({'error':str(exc)},400)
            finally:
                if db:db.close()
    server=HTTPServer(('127.0.0.1',port),Handler)
    print(f'Atlas reviewer console: http://127.0.0.1:{port} | live workspace opens by default',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        scheduler.close()
        server.server_close()
