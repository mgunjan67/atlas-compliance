# Atlas research memo

Evidence: captured September 24–25, 2026; implementation reviewed September 28. All authorities and employees are fictional sample data. Source facts, implementation policies and unresolved inputs are distinguished below.

## Source findings

Atlas monitors the [Asterian federal page](https://asterian-federal-wage-site.vercel.app/) and [Bellwether state page](https://bellwether-state-wage-site.vercel.app/). Atlas retrieves only those HTTPS origins. Their server-rendered HTML contains rate cards, publications and metadata. Raw copies, retrieval times and SHA-256 manifests are in `data/research/`. Extraction ignores scripts and hidden elements; it does not read internal databases or publication schedules.

| Publication | Observed content | Treatment |
|---|---|---|
| Federal daily card | 12.73 AST/hour September 24; 12.91 September 25 | Separate effective-dated review candidates |
| State daily card | 16.63 AST/hour on both captured dates | Primary state source; federal comparison is corroboration |
| AFWA-2026-0042 | 13.25 AST/hour from January 1, 2027 | Future numerical rule; approval alone does not activate it early |
| BDL-2026-0117 | 17.50 AST/hour from January 1, 2027 | Same future-date gate |
| AFWA-2026-0038 | Employer threshold corrected from 24 to 25 | Coverage review; no new wage amount |
| BDL-2026-0121 / 0108 | Higher applicable protection; physical work location | Existing policy evidence; no extra review for unchanged text |
| AFWA-2026-0031 | Proposed contract-work rate | Proposal, not active law |
| BDL-2026-0099 | Claims portal announcement | Retained evidence, unrelated to wages |

These are dated observations, not claims about today's rates. Use the live check to retrieve current publications. A captured rate is not an approved rule. Peer figures never supply duplicate rules; current cross-source disagreement blocks unsupported decisions.

## Why these sources are trusted

The two designated websites are treated as the primary publishers for their fictional jurisdictions. Asteria supplies the federal rule; Bellwether supplies the state rule. A state figure repeated on the federal page is a cross-check, not a replacement for the state publication.

Atlas restricts fetching to these HTTPS origins and refuses redirects. That keeps retrieval within the configured sources; it does not establish their legal authority. For a real jurisdiction, a compliance owner would first verify the publisher through an official government directory or statutory reference, confirm its authority over the relevant workers, and record that decision before adding the source. Each proposed rule would still need its publication status, scope and effective date checked against the saved evidence.

## Decisions and assumptions

**Precedence.** Select the latest applicable approved version per jurisdiction, then the higher federal/state amount for Bellwether work. Use work location, not home address. Same-date conflicting approved versions need review. Corrections explicitly identify the version they replace.

**Time.** Keep publication, effective, discovery and review timestamps separate. Cards do not separately state their original publication date: it remains null. Daily cards use `[effective date, next day)` as a conservative freshness policy, not a legal sunset inferred from the source. A missed day cannot be reconstructed from today's rate. Future final notices remain inactive before their effective date.

**Discovery.** Compare visible page text as well as supported publication structures. Unfamiliar wage blocks become review candidates; other changed unmapped content fails extraction for investigation with the failed page preserved. Cosmetic HTML changes alone do not create rules. Contradictory labels, negated proposals, restricted coverage and changed guidance must not silently pass. The adapter is deliberately bounded and may abstain unnecessarily when pages change.

The amount parser validates the entire numeric token; unsupported precision is not truncated or rounded into a proposed rate. Numerical notices must use supported general-rate wording. Additional scope conditions or unfamiliar sentences remain unresolved rather than becoming general rules. A publication returning after a different version or absence is a new occurrence requiring review where relevant; unchanged repeat checks reuse the existing occurrence. Parser versions are retained so old receipts still reproduce the original extraction.

**Coverage.** The supplied file marks all workers Covered but has no employer headcount. A reviewer must explicitly decide whether to rely on that upstream field after reading the threshold correction. Interpretation acknowledgment records a policy assumption, not a new rate. Unknown and quarantined content cannot be cleared by generic acknowledgment.

## Employee findings and arithmetic

The included dataset has 48 employees: 24 in each location, 32 hourly and 16 annual-salary records. Four are Active with December start dates. The minimized CSV retains the 12 fields needed for decisions; unrelated personal, demographic and bank fields are excluded.

Hourly shortfall is `max(0, approved floor − recorded hourly wage)`. Compare exact Decimal amounts first, then round reported money half-up to two decimals. Weekly shortfall uses scheduled weekly hours and is only an estimate. Equality passes.

No source authorizes converting annual pay into an actual hourly compliance wage. Atlas displays `salary ÷ (52 × scheduled weekly hours)` as an illustration, keeps salary cases in review, and requests an approved comparison method plus actual hours/pay-period evidence. Salary scenario exports cannot change operational flags or stored evaluation history.

## Re-evaluation, history and failures

A federal change selects Asteria employees, including those working in Bellwether. A state change selects employees working in Bellwether. Date bounds determine which current or previously observed work dates are affected. Historical re-evaluation uses the stored employee inputs for those dates, not today's wages or location. An unchanged higher state floor may mean a federal change produces no different decision for a Bellwether employee.

Each employee/date has one current flag per live or simulated workspace. Identical calculations reuse an evaluation identity; transitions update that flag and append an observation, preserving previous evaluations and audit events. Returning to an earlier input therefore records a new observation without inventing another active flag. Saved inspections and their resolved versions remain immutable. Pending updates preserve the last complete source-cleared display, with the saved date and current uncertainty shown separately.

Every check records success, change or error for both sources. Failed fetches, unsupported page structure, unmapped changes and cross-source inconsistencies prevent unsupported current decisions. Daily-card expiry is the freshness boundary: an old daily amount cannot be carried into a new day's legal calculation. The last-check time is visible; automatic polling is optional and stops when the server stops. Failed re-evaluation jobs remain stored and retryable. A successful current archive does not hide those failures: the UI reports partial completion and offers a retry. No old source or evaluation is erased to make the status look successful.

## Where AI helps, and where it does not

Both pages expose labelled rate cards and publication details in their HTML. Explicit parsing remains the source of proposed rule fields. The same content produces the same extracted values and classification; unfamiliar wording or unsupported layouts still require investigation.

AI supplies an independent category suggestion from saved publication text. It helps reviewers interpret unfamiliar wording, but it does not repair the parser, extract approved amounts or clear warnings. A separate background worker saves suggestions and their evidence references. The inspection view shows disagreement without changing the existing human approval process.

The initial hosted extraction screen classified 17 of 17 familiar/development examples correctly, but only 12 passed both field and exact-quotation checks. A later 12-case classification experiment matched 10 categories and supplied useful suggestions on five unfamiliar examples. It mishandled conflicting dates and a withdrawn order; the parser safely requested review for both. These small selected tests justify an advisory role, not autonomous decisions. They are separate runs with different prompts; see [AI review](ai-review.md).

Rule selection, jurisdiction precedence, effective-date checks, arithmetic and the final compliance state must remain deterministic and testable. A model should neither approve a rule nor decide whether an employee is compliant.

## What would need to change for real payroll

Atlas currently runs locally with fictional data. A typed reviewer name is an audit label, not a verified identity, and a scheduled-hours estimate is not a payroll adjustment. Before using real employee records, the following work would be needed:

- **Verify the policies and inputs.** Have a compliance owner validate source authority, coverage, exemptions, salary treatment and date rules. Connect effective-dated wage and work-location records, actual hours and pay periods, then reconcile results against known payroll cases.
- **Control access to employee data and approvals.** Add authenticated users, reviewer permissions and employer separation. Limit stored personal data, protect it in transit and at rest, and define retention and deletion rules.
- **Make monitoring independent of an open local server.** Run checks and retries through a managed service. Alert an owner when a source is overdue, extraction fails, a page layout changes or re-evaluation jobs remain unfinished. Record who investigates and resolves each failure.
- **Protect and recover history.** Use controlled database access, tested backups and an independently protected audit record. The current local hash chain can expose inconsistencies, but someone with full database access could rewrite both records and hashes.
- **Validate before connecting payroll actions.** Test concurrent reviews, interrupted jobs and recovery on representative data. Have operators check the results alongside the existing payroll process before allowing any downstream payment changes. Atlas currently calculates and exports findings; it does not change payroll.

The existing tests cover a complete correction with simulated approvals, repeat processing and historical re-evaluation. They do not establish production readiness. Historical backfill remains limited to employee inputs and source versions actually captured.
