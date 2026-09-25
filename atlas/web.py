"""Local reviewer console. Live and simulated databases never share approvals."""
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .store import connect,candidates,review,verify_ledger
from .engine import load_employees,run_evaluation,source_health
from .workflow import impact_preview,process_jobs,summarize
from .showcase import bootstrap,introduce_correction,DAY,CORRECTION_REVIEWED
from .receipt import build_receipt,verify_receipt
from .scheduler import LiveScheduler
from .triage import enrich_results

STATIC=Path(__file__).with_name('static')

def serve(db_path,employees_path,port,demo_path=None):
    demo_path=demo_path or str(Path(db_path).with_name('reviewer-demo.sqlite3'))
    if Path(demo_path).resolve()==Path(db_path).resolve():raise ValueError('Live and replay databases must differ')
    demo=connect(demo_path)
    try:bootstrap(demo)
    finally:demo.close()
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
            mode=params.get('mode','demo')
            if mode not in ('demo','live'):raise ValueError('Unknown workspace')
            return connect(demo_path if mode=='demo' else db_path),mode=='demo'
        def do_GET(self):
            if not self.valid_host():return self.respond({'error':'Invalid host'},403)
            path=urlparse(self.path);params={k:v[0] for k,v in parse_qs(path.query).items()}
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
                day=params.get('date',DAY if simulated else datetime.now(timezone.utc).date().isoformat())
                employees=load_employees(employees_path)
                operational_day=simulated or day==datetime.now(timezone.utc).date().isoformat()
                if path.path=='/api/state':
                    logical_clock=None
                    if simulated:
                        corrected=next((c for c in candidates(db) if c.get('amount')=='18.50' and c['kind']=='DAILY_RATE'),None)
                        logical_clock=('2026-09-25T09:02:00+00:00' if corrected['state']=='APPROVED' else '2026-09-25T09:00:30+00:00') if corrected else '2026-09-24T10:02:00+00:00'
                    results=run_evaluation(db,employees,day,simulated=simulated,known_at=params.get('known_at'),
                                           evaluated_at=logical_clock,update_flags=operational_day)
                    cutoff=results[0]['knowledge_cutoff'] if results else params.get('known_at')
                    items=[c for c in candidates(db,cutoff) if c['simulated']==simulated]
                    fetches=[dict(r) for r in db.execute('SELECT * FROM fetches WHERE simulated=? ORDER BY id DESC LIMIT 12',(int(simulated),))]
                    events=[dict(r) for r in db.execute('SELECT a.*,l.entry_hash FROM audit a LEFT JOIN ledger l ON l.event_id=a.id ORDER BY a.id DESC LIMIT 120')]
                    for event in events:event['data']=json.loads(event['data'])
                    jobs=[dict(r) for r in db.execute('SELECT * FROM jobs WHERE simulated=? ORDER BY created_at DESC',(int(simulated),))]
                    correction=next((c for c in items if c.get('amount')=='18.50' and c['kind']=='DAILY_RATE'),None) if simulated else None
                    return self.respond({'mode':'demo' if simulated else 'live','simulated':simulated,'date':day,'csrf':token,
                                         'summary':summarize(results),'results':enrich_results(results),'candidates':items,'fetches':fetches,'events':events,
                                         'jobs':jobs,'ledger':verify_ledger(db),'health':source_health(db,day,simulated,cutoff),
                                         'monitor':scheduler.status() if not simulated else None,
                                         'correction_present':bool(correction),'correction_state':correction['state'] if correction else None})
                if path.path=='/api/impact':return self.respond(impact_preview(db,employees,params['id'],day,params.get('supersedes') or None))
                if path.path=='/api/receipt':
                    receipt=build_receipt(db,params['id'])
                    if params.get('verify'):return self.respond(verify_receipt(receipt))
                    return self.respond(receipt,filename='atlas-decision-receipt.json')
                if path.path=='/api/export':return self.respond(enrich_results(run_evaluation(
                    db,employees,day,simulated=simulated,known_at=params.get('known_at'),update_flags=operational_day)),
                    filename='atlas-employee-results.json')
                if path.path=='/api/snapshot':
                    row=db.execute('SELECT raw_html FROM snapshots WHERE id=?',(params.get('id',''),)).fetchone()
                    return self.respond(row['raw_html'] if row else 'Not found',200 if row else 404,'text/plain; charset=utf-8')
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
                day=params.get('date',DAY if simulated else datetime.now(timezone.utc).date().isoformat())
                if self.path=='/api/scenario':
                    if not simulated:raise ValueError('Scenario events only belong in replay workspace')
                    return self.respond(introduce_correction(db))
                if self.path=='/api/review':
                    candidate=next((c for c in candidates(db) if c['id']==params.get('id')),None)
                    if not candidate or candidate['simulated']!=simulated:raise ValueError('Candidate does not belong to this workspace')
                    review(db,params['id'],params['decision'],params.get('actor',''),params.get('reason',''),params.get('supersedes') or None,
                           allow_simulated=simulated,at=CORRECTION_REVIEWED if simulated else None)
                    # The date picker is an evaluation scenario, not the operational clock.
                    # A reviewer viewing a future date must not complete a future activation job early.
                    job_day='2026-09-25' if simulated else datetime.now(timezone.utc).date().isoformat()
                    jobs=process_jobs(db,load_employees(employees_path),job_day,simulated=simulated,
                                      evaluated_at='2026-09-25T09:02:00+00:00' if simulated else None)
                    return self.respond({'reviewed':params['id'],'jobs':jobs})
                if self.path=='/api/fetch':
                    if simulated:raise ValueError('Live source retrieval belongs in the live workspace')
                    return self.respond(scheduler.check_now(db))
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
