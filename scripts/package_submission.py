"""Create a curated source/evidence ZIP and smoke-test the extracted handoff."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    build_stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    files={ROOT/name for name in ('README.md','PLAN.md','pyproject.toml','.gitignore','.env.example','data/employees.csv')}
    for directory in ('atlas','tests','scripts','docs','data/research','output/reviewer-story'):
        files.update(p for p in (ROOT/directory).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    files.discard(ROOT/'docs/rebuild-review.md')  # Internal review notes, not submission copy.
    files.add(ROOT/'output/lab-report.json')
    # Ship one verified, pre-review live poll. Later local rehearsal approvals
    # are operator history, not part of the portable assessment handoff.
    example=ROOT/'output/live-archive/2026-09-25/20260925T070809477519Z'
    for suffix in ('.json','.csv','.manifest.json'):
        artifact=example.with_suffix(suffix)
        if not artifact.is_file():raise FileNotFoundError('Missing curated live poll: '+str(artifact))
        files.add(artifact)
    entries={p.relative_to(ROOT).as_posix():p.read_bytes() for p in sorted(files)}
    # The archived poll is preserved byte-for-byte. Re-evaluate its saved source
    # pages separately so the convenient pre-review export matches current code.
    from atlas.__main__ import seed
    from atlas.engine import export_results, load_employees, run_evaluation
    from atlas.store import connect
    with tempfile.TemporaryDirectory(prefix='atlas-pre-review-') as temp:
        db=connect(Path(temp)/'pre-review.sqlite3')
        try:
            seed(db,ROOT/'data/research/2026-09-25')
            results=run_evaluation(db,load_employees(ROOT/'data/employees.csv'),'2026-09-25')
            export_results(results,Path(temp)/'live-results.json')
        finally:
            db.close()
        entries['output/live-results.json']=(Path(temp)/'live-results.json').read_bytes()
        entries['output/live-results.csv']=(Path(temp)/'live-results.csv').read_bytes()
    entries['output/live-results.provenance.json']=json.dumps({
        'kind':'offline pre-review evaluation',
        'evaluation_date':'2026-09-25',
        'source':'Preserved 2026-09-25 HTML snapshots in data/research/2026-09-25',
        'not_a_new_poll':True,
        'note':'The original live poll and its checksum manifest remain unchanged under output/live-archive.'
    },indent=2).encode('utf-8')
    manifest={'format':'atlas-submission-v2','created_at':datetime.now(timezone.utc).isoformat(),
              'files':{name:sha(raw) for name,raw in entries.items()},
              'exclusions':'Local databases, rehearsal approvals, keys, caches, earlier demo exports and internal rebuild notes.'}
    archive=ROOT/'output'/f'atlas-submission-{build_stamp}.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as bundle:
        for name,raw in entries.items():bundle.writestr('atlas-compliance/'+name,raw)
        bundle.writestr('atlas-compliance/SUBMISSION-MANIFEST.json',json.dumps(manifest,indent=2))

    commands=[['verify','output/reviewer-story/original-receipt.json'],
              ['seed'],['evaluate','--date','2026-09-24'],['lab'],['story'],
              ['verify','output/reviewer-story/original-receipt.json'],
              ['seed','--directory','data/research/2026-09-25'],
              ['evaluate','--date','2026-09-25']]
    checks=[]
    with tempfile.TemporaryDirectory(prefix='atlas-package-') as temp:
        destination=Path(temp).resolve()
        # Confirm the cleanup/extraction target is the generated temporary directory.
        if destination.parent!=Path(tempfile.gettempdir()).resolve():
            raise ValueError('Unexpected temporary directory')
        with zipfile.ZipFile(archive) as bundle:
            if bundle.testzip():raise ValueError('ZIP integrity failed')
            for member in bundle.namelist():
                if not (destination/member).resolve().is_relative_to(destination):
                    raise ValueError('Unsafe archive member')
            bundle.extractall(destination)
        project=destination/'atlas-compliance'
        for name,expected in manifest['files'].items():
            if sha((project/name).read_bytes())!=expected:raise ValueError('Packaged file mismatch: '+name)
        live=json.loads((project/'output/live-results.json').read_text(encoding='utf-8'))
        if len(live)!=48 or any(r['decision_state']!='REVIEW_REQUIRED' for r in live):
            raise ValueError('Packaged live example is not the clean pre-review capture')
        if any(c.get('actor') for r in live for c in r['candidate_applicable_rules']):
            raise ValueError('Local rehearsal approval leaked into the packaged live example')
        salary=[r for r in live if r['employee_input']['pay_basis']=='Annual Salary']
        if len(salary)!=16 or any(len(r['analysis_context']['salary_review_requirements'])<3 for r in salary):
            raise ValueError('Packaged salary review context is missing or incomplete')
        for arguments in commands:
            result=subprocess.run([sys.executable,'-m','atlas',*arguments],cwd=project,
                                  capture_output=True,text=True,encoding='utf-8',timeout=30)
            if result.returncode:raise RuntimeError(result.stderr or result.stdout)
            summary=json.loads(result.stdout)
            checks.append({'command':'python -m atlas '+' '.join(arguments),'exit_code':result.returncode})
            if arguments[0]=='evaluate' and summary['counts']!={'REVIEW_REQUIRED':48}:
                raise ValueError('Fresh live database unexpectedly bypassed review')
            if arguments[0]=='verify' and not summary['valid']:raise ValueError('Receipt did not replay')
        test_result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-q'],cwd=project,
                                   capture_output=True,text=True,encoding='utf-8',timeout=90)
        if test_result.returncode:raise RuntimeError(test_result.stderr or test_result.stdout)
        checks.append({'command':'python -m unittest discover -s tests -q','exit_code':0})
    verification={'archive':archive.name,'sha256':sha(archive.read_bytes()),'packaged_files':len(entries),
                  'bytes':archive.stat().st_size,'clean_extraction_verified':True,'commands':checks,
                  'note':'Offline smoke check in a fresh temporary directory; no model API call or source approval.'}
    (ROOT/'output'/f'submission-manifest-{build_stamp}.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (ROOT/'output'/f'package-verification-{build_stamp}.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
    shutil.copyfile(archive,ROOT/'output/atlas-submission.zip')
    if sha((ROOT/'output/atlas-submission.zip').read_bytes())!=verification['sha256']:
        raise ValueError('Stable submission ZIP does not match verified archive')
    print(json.dumps(verification,indent=2))


if __name__=='__main__':main()
