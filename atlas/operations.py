"""One complete, repeatable live monitoring and results-archive cycle."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .engine import export_results, load_employees, run_evaluation
from .extract import SOURCES
from .monitor import fetch_source
from .store import audit
from .workflow import process_jobs, summarize


def poll_once(db, employees_path='data/employees.csv',
              latest_path='output/live-results.json',
              archive_root='output/live-archive', at=None):
    checked_at = at or datetime.now(timezone.utc)
    if checked_at.tzinfo is None:
        raise ValueError('Poll timestamp needs a timezone')
    checked_at = checked_at.astimezone(timezone.utc)
    day = checked_at.date().isoformat()
    checks = [fetch_source(db, source) for source in SOURCES]
    employees = load_employees(employees_path)
    jobs = process_jobs(db, employees, day)
    results = run_evaluation(db, employees, day)

    latest_path = Path(latest_path)
    export_results(results, latest_path)
    stamp = checked_at.strftime('%Y%m%dT%H%M%S%fZ')
    directory = Path(archive_root) / day
    archive = directory / f'{stamp}.json'
    if archive.exists() or archive.with_suffix('.csv').exists():
        raise FileExistsError('Archive timestamp collision')
    export_results(results, archive)
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (archive, archive.with_suffix('.csv'))}
    manifest = {
        'checked_at': checked_at.isoformat(),
        'evaluation_date': day,
        'source_checks': checks,
        'jobs': jobs,
        'summary': summarize(results),
        'archive_files_sha256': files,
        'meaning': 'Captured and evaluated source state. Proposed rates remain unapproved until human review.',
    }
    manifest_path = archive.with_suffix('.manifest.json')
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    with db:
        audit(db, 'LIVE_POLL_ARCHIVED', {
            'checked_at': manifest['checked_at'], 'evaluation_date': day,
            'archive': str(archive), 'manifest': str(manifest_path),
            'source_checks': checks, 'counts': manifest['summary']['counts'],
            'archive_files_sha256': files,
        })
    return {'checked_at': manifest['checked_at'], 'date': day,
            'checks': checks, 'jobs': jobs, 'summary': manifest['summary'],
            'latest': str(latest_path), 'archive': str(archive),
            'manifest': str(manifest_path)}
