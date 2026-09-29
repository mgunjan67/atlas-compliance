"""Preserve the last source-cleared result set without extending a wage rule."""
import json
from .store import dumps, now


def retention_context(current, displayed, retained_date):
    """Explain current blockers separately from immutable saved decisions."""
    if not retained_date:
        return None
    previous = {r['employee_id']: r for r in displayed}
    issues = []
    source_codes = {'PENDING_SOURCE_REVIEW', 'SOURCE_HEALTH_REVIEW', 'CONFLICTING_APPROVED_RULES'}
    ordinary_exceptions = {'SALARY_CONVERSION_UNAPPROVED', 'FUTURE_START_CONFLICT'}
    for row in current:
        old = previous.get(row['employee_id'], {})
        changed_input = row.get('employee_input') != old.get('employee_input')
        unresolved = row['decision_state'] not in ('COMPLIANT', 'NON_COMPLIANT')
        if not changed_input and (not unresolved or row.get('reason_code') in ordinary_exceptions):
            continue
        source = row.get('reason_code') in source_codes or (
            unresolved and row.get('actual_hourly_wage') is not None)
        issues.append(dict(employee_id=row['employee_id'], category='source' if source and not changed_input else 'employee_data',
                           decision_state=row['decision_state'], reason_code=row.get('reason_code'),
                           input_changed=changed_input,
                           explanation=(row.get('explanation') or ['Current evaluation needs attention.'])[-1],
                           evaluation_id=row.get('evaluation_id')))
    source_count = sum(i['category']=='source' for i in issues)
    employee_count = sum(i['category']=='employee_data' for i in issues)
    parts = []
    if employee_count:
        parts.append(f'Employee data needs attention for {employee_count} '+('worker.' if employee_count==1 else 'workers.'))
    if source_count:
        parts.append(f'Current source rules or checks block {source_count} '+('worker.' if source_count==1 else 'workers.'))
    return dict(saved_date=retained_date, current_date=current[0]['evaluation_date'] if current else None,
                message=' '.join(parts) or 'Current evaluation is unresolved.',
                employee_count=employee_count, source_count=source_count, issues=issues)


def export_results(current, displayed, retained_date):
    """Attach a view warning without altering the saved decision or receipt."""
    context = retention_context(current, displayed, retained_date)
    if not context:
        return displayed
    issues = {i['employee_id']: i for i in context['issues']}
    return [dict(row, saved_result_notice=dict(saved_date=retained_date,
                 current_date=context['current_date'], message=context['message'],
                 current_issue=issues.get(row['employee_id']))) for row in displayed]


def source_cleared(rows):
    # Employee-specific exceptions can remain; source uncertainty cannot publish
    # a replacement for the last reviewed result set.
    return bool(rows) and any(r['decision_state'] in ('COMPLIANT', 'NON_COMPLIANT') for r in rows) and all(
        r['decision_state'] in ('COMPLIANT', 'NON_COMPLIANT') or
        r.get('reason_code') in ('SALARY_CONVERSION_UNAPPROVED', 'FUTURE_START_CONFLICT') for r in rows)


def retained_results(db, rows, day):
    """Return an intact dated baseline; never relabel its receipts as current."""
    ids = {r['employee_id'] for r in rows}
    if source_cleared(rows):
        with db:
            db.execute('INSERT OR REPLACE INTO result_views VALUES(?,?,?)', (day, now(), dumps(rows)))
        return rows, None
    # The browser cache is optional. Approvals and resolved inspections save
    # complete result sets even when no operator has opened the results screen.
    from .batches import saved_sets
    options = []
    def consider(previous, saved_at):
        if (source_cleared(previous) and {r['employee_id'] for r in previous} == ids
                and len(previous) == len(rows)
                and all(r['evaluation_date'] == previous[0]['evaluation_date'] for r in previous)
                and previous[0]['evaluation_date'] <= day):
            evaluated_at = max((r.get('evaluation_timestamp', '') for r in previous), default='')
            options.append(((previous[0]['evaluation_date'], evaluated_at or saved_at, saved_at), previous))
    for record in db.execute('SELECT data,saved_at FROM result_views WHERE evaluation_date<=?', (day,)):
        consider(json.loads(record['data']), record['saved_at'])
    for inspection in saved_sets(db):
        consider(inspection['results'], inspection.get('result_saved_at') or inspection.get('reviewed_at') or '')
    if options:
        previous = max(options, key=lambda option: option[0])[1]
        return previous, previous[0]['evaluation_date']
    # Upgrade existing installations from complete historical flag sets. Do not
    # cherry-pick individual successful employees or recalculate old decisions.
    dates = db.execute('SELECT DISTINCT evaluation_date FROM flags WHERE simulated=0 AND evaluation_date<? ORDER BY evaluation_date DESC', (day,))
    for date in dates:
        previous = [json.loads(r[0]) for r in db.execute('SELECT e.data FROM flags f JOIN evaluations e ON e.id=f.evaluation_id WHERE f.simulated=0 AND f.evaluation_date=? ORDER BY f.employee_id', (date[0],))]
        if {r['employee_id'] for r in previous} == ids and source_cleared(previous):
            with db:
                db.execute('INSERT OR IGNORE INTO result_views VALUES(?,?,?)', (date[0], now(), dumps(previous)))
            return previous, date[0]
    return rows, None
