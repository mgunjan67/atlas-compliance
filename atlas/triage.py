"""Non-decisional context for reviewing incomplete wage evaluations.

This module enriches views and exports; it never changes the engine decision or
turns an annual salary into an actual hourly wage.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal('0.01')


def _positive(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() and 0 < amount <= Decimal('1000000000000') and amount.as_tuple().exponent >= -12 else None


def _money(value):
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def enrich_result(result):
    """Add clearly labelled reference values without changing the result."""
    row = dict(result)
    employee = result.get('employee_input') or {}
    day = result['evaluation_date']
    needed = ['Asteria'] + (['Bellwether'] if result.get('work_jurisdiction') == 'Bellwether' else [])
    rules = [r for r in result.get('candidate_applicable_rules', [])
             if r.get('jurisdiction') in needed and r.get('effective_from') and r['effective_from'] <= day]
    pending = [r for r in rules if r.get('state') == 'REVIEW_REQUIRED'
               and r.get('classification') == 'RATE_REVIEW' and r.get('amount') is not None
               and (not r.get('effective_to') or day < r['effective_to'])]
    approved = [r for r in rules if r.get('state') == 'APPROVED' and r.get('classification') == 'RATE_REVIEW']
    superseded = {r.get('supersedes') for r in approved if r.get('supersedes')}
    approved = [r for r in approved if r.get('id') not in superseded]
    selected = []
    for jurisdiction in needed:
        group = [r for r in approved if r['jurisdiction'] == jurisdiction]
        if not group:
            break
        latest = max(r['effective_from'] for r in group)
        current = [r for r in group if r['effective_from'] == latest]
        if any(r.get('effective_to') and day >= r['effective_to'] for r in current):
            break
        amounts = {(r.get('amount'), r.get('currency'), r.get('unit')) for r in current}
        if len(amounts) != 1 or next(iter(amounts))[1:] != ('AST', 'hour'):
            break
        selected.append(sorted(current, key=lambda r: r['id'])[0])
    reference = (max(selected, key=lambda r: (Decimal(r['amount']), r['jurisdiction'] == 'Bellwether'))
                 if len(selected) == len(needed) else None)

    if reference and pending:
        reference_meaning = 'Last approved floor. A pending rate proposal may change the final controlling floor.'
    elif reference and result.get('source_health_issues'):
        reference_meaning = 'Approved floor in the registry; source health still requires review.'
    elif reference:
        reference_meaning = 'Approved applicable floor for this work location and date; wage comparability may still require review.'
    else:
        reference_meaning = None
    context = {
        'approved_reference_floor': _money(Decimal(reference['amount'])) if reference else None,
        'approved_reference_jurisdiction': reference['jurisdiction'] if reference else None,
        'approved_reference_rule_version': reference['id'] if reference else None,
        'approved_reference_meaning': reference_meaning,
        'pending_rate_candidates': [dict(source_rule_id=r.get('source_rule_id'), jurisdiction=r['jurisdiction'],
                                         amount=r['amount'], effective_from=r['effective_from'],
                                         candidate_id=r['id']) for r in pending],
        'recorded_hourly_gap_to_reference': None,
        'recorded_weekly_gap_to_reference': None,
        'indicative_salary_hourly': None,
        'indicative_hourly_gap_to_reference': None,
        'indicative_weekly_gap_to_reference': None,
        'salary_assumption': None,
        'salary_review_requirements': [],
    }
    if reference and employee.get('pay_basis') == 'Hourly' and result.get('actual_hourly_wage') is not None:
        actual = Decimal(result['actual_hourly_wage'])
        gap = max(Decimal(0), Decimal(reference['amount']) - actual)
        context['recorded_hourly_gap_to_reference'] = _money(gap)
        hours = _positive(employee.get('scheduled_hours_per_week'))
        if hours is not None:
            context['recorded_weekly_gap_to_reference'] = _money(gap * hours)
    if employee.get('pay_basis') == 'Annual Salary':
        context['salary_review_requirements'] = [
            'An approved method for comparing annual salary with an hourly minimum',
            'Actual hours worked and the relevant pay periods',
            'Any applicable salary or exemption treatment',
        ]
        if result.get('reason_code') == 'FUTURE_START_CONFLICT':
            context['salary_review_requirements'].insert(0, 'A confirmed start date and employment status')
    if employee.get('pay_basis') == 'Annual Salary' and employee.get('currency') == 'AST':
        salary = _positive(employee.get('annual_salary_ast'))
        hours = _positive(employee.get('scheduled_hours_per_week'))
        if salary is not None and hours is not None:
            proxy = salary / (Decimal(52) * hours)
            context['indicative_salary_hourly'] = _money(proxy)
            context['salary_assumption'] = 'Annual salary / (52 × scheduled weekly hours). Illustrative only; not actual hourly pay or an approved compliance conversion.'
            if reference:
                gap = max(Decimal(0), Decimal(reference['amount']) - proxy)
                context['indicative_hourly_gap_to_reference'] = _money(gap)
                context['indicative_weekly_gap_to_reference'] = _money(gap * hours)
    row['analysis_context'] = context
    return row


def enrich_results(results):
    return [enrich_result(result) for result in results]
