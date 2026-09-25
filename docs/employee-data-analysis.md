# Employee-result data audit and review triage

Source: the 48-row `atlas-employee-results.json` exported from the **24 September 2026 replay while the synthetic 18.50 Bellwether correction is pending**. This is a fictional assessment dataset. Counts describe that snapshot, not the 25 September live review or real payroll liability.

## What the original export obscured

| Group | Employees | Formal result | Why fields were blank |
|---|---:|---|---|
| Federal Territory, hourly | 16 | 10 `NON_COMPLIANT`, 6 `COMPLIANT` | No key wage fields missing |
| Bellwether, hourly | 16 | 16 `REVIEW_REQUIRED` | Pending synthetic correction blocked the final floor, even though 16.63 was already approved in replay |
| Annual salary, currently started | 12 | 12 `REVIEW_REQUIRED` | No authorized annual-salary-to-hourly compliance conversion |
| Annual salary, future start conflict | 4 | 4 `REVIEW_REQUIRED` | Marked Active although start date is after the evaluation date; salary conversion is also unresolved |

The export had **16 null `actual_hourly_wage` values** (all salaried) and **32 null `controlling_minimum_wage` values** (all review cases). Null is appropriate when the formal value cannot be established, but the original view failed to show useful context alongside it.

## Insights the review queue should not hide

- **11 of the 16 Bellwether hourly employees** have a recorded rate below the **last approved 16.63 AST/hour floor**. Their scheduled-hours gaps sum to **2,213.50 AST/week** against that approved reference. They remain `REVIEW_REQUIRED` because the pending 18.50 correction may alter the final effective rule; they should nevertheless be surfaced for investigation. This 2,213.50 plus the 935.30 supported federal estimate equals the baseline 3,148.80 weekly estimate in the completed replay story.
- For the **12 currently started salaried employees**, annual salary ÷ (52 × scheduled weekly hours) gives an *illustrative* hourly equivalent. **8 of 12** are below the approved reference floor under that assumption: 3 Federal Territory and 5 Bellwether. Their illustrative scheduled-hours gap totals **1,229.93 AST/week**. This is a triage scenario, **not** a legal underpayment estimate or an additional compliance flag. The four future-start conflicts are excluded from this count.
- Highest illustrative salary-review priorities by weekly gap are **AST-0030 (350.01)**, **AST-0033 (256.90)**, **AST-0039 (169.49)** and **AST-0003 (158.90)** AST/week. These values rely on the 52-week assumption and do not account for actual hours, pay periods, exemptions or salary treatment.

## Product decision

Atlas now adds a separate `analysis_context` to the web view and JSON/CSV exports. It shows an approved floor **as a reference**, any pending proposed rate, an explicitly labelled salary proxy, and the corresponding review-priority gap. For a recorded hourly wage under a still-approved reference floor, it shows that gap even while the formal decision awaits correction review. The deterministic decision, `actual_hourly_wage`, `controlling_minimum_wage` and official underpayment fields remain unchanged when their values are unresolved. The overview calls out the review queue rather than making those cases disappear from attention.

The next human questions are specific: verify the pending correction and its effective date; investigate recorded wages already below the currently approved reference; obtain the employer's salary conversion/pay-period and actual-hours policy; and resolve the four future-start records. Until then, `REVIEW_REQUIRED` is the defensible decision state.
