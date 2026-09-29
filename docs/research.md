# Atlas research memo

Evidence: captured September 24–25, 2026; implementation reviewed September 28. All authorities and employees are fictional assessment material. Source facts, implementation policies and unresolved inputs are distinguished below.

## Source findings

The assignment designates the [Asterian federal page](https://asterian-federal-wage-site.vercel.app/) and [Bellwether state page](https://bellwether-state-wage-site.vercel.app/). Atlas retrieves only those HTTPS origins. Their server-rendered HTML contains rate cards, publications and metadata. Raw copies, retrieval times and SHA-256 manifests are in `data/research/`. Extraction ignores scripts and hidden elements; it does not read internal databases or publication schedules.

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

## Decisions and assumptions

**Precedence.** Select the latest applicable approved version per jurisdiction, then the higher federal/state amount for Bellwether work. Use work location, not home address. Same-date conflicting approved versions need review. Corrections explicitly identify the version they replace.

**Time.** Keep publication, effective, discovery and review timestamps separate. Cards do not separately state their original publication date: it remains null. Daily cards use `[effective date, next day)` as a conservative freshness policy, not a legal sunset inferred from the source. A missed day cannot be reconstructed from today's rate. Future final notices remain inactive before their effective date.

**Discovery.** Compare visible page text as well as supported publication structures. Unfamiliar wage blocks become review candidates; other changed unmapped content fails extraction for investigation with the failed page preserved. Cosmetic HTML changes alone do not create rules. Contradictory labels, negated proposals, restricted coverage and changed guidance must not silently pass. The adapter is deliberately bounded and may abstain unnecessarily when pages change.

The amount parser validates the entire numeric token; unsupported precision is not truncated or rounded into a proposed rate. Numerical notices must use supported general-rate wording. Additional scope conditions or unfamiliar sentences remain unresolved rather than becoming general rules. A publication returning after a different version or absence is a new occurrence requiring review where relevant; unchanged repeat checks reuse the existing occurrence. Parser versions are retained so old receipts still reproduce the original extraction.

**Coverage.** The supplied file marks all workers Covered but has no employer headcount. A reviewer must explicitly decide whether to rely on that upstream field after reading the threshold correction. Interpretation acknowledgment records a policy assumption, not a new rate. Unknown and quarantined content cannot be cleared by generic acknowledgment.

## Employee findings and arithmetic

The supplied dataset has 48 employees: 24 in each location, 32 hourly and 16 annual-salary records. Four are Active with December start dates. The minimized CSV retains the 12 fields needed for decisions; unrelated personal, demographic and bank fields are excluded.

Hourly shortfall is `max(0, approved floor − recorded hourly wage)`. Compare exact Decimal amounts first, then round reported money half-up to two decimals. Weekly shortfall uses scheduled weekly hours and is only an estimate. Equality passes.

No source authorizes converting annual pay into an actual hourly compliance wage. Atlas displays `salary ÷ (52 × scheduled weekly hours)` as an illustration, keeps salary cases in review, and requests an approved comparison method plus actual hours/pay-period evidence. Salary scenario exports cannot change operational flags or stored evaluation history.

## Re-evaluation, history and failures

A federal change selects Asteria employees, including those working in Bellwether. A state change selects employees working in Bellwether. Date bounds determine which current or previously observed work dates are affected. Historical re-evaluation uses the stored employee inputs for those dates, not today's wages or location. An unchanged higher state floor may mean a federal change produces no different decision for a Bellwether employee.

Each employee/date has one current flag per live or simulated workspace. Identical calculations reuse an evaluation identity; transitions update that flag and append an observation, preserving previous evaluations and audit events. Returning to an earlier input therefore records a new observation without inventing another active flag. Saved inspections and their resolved versions remain immutable. Pending updates preserve the last complete source-cleared display, with the saved date and current uncertainty shown separately.

Every check records success, change or error for both sources. Failed fetches, unsupported page structure, unmapped changes and cross-source inconsistencies prevent unsupported current decisions. Daily-card expiry is the freshness boundary: an old daily amount cannot be carried into a new day's legal calculation. The last-check time is visible; automatic polling is optional and stops when the server stops. Failed re-evaluation jobs remain stored and retryable. A successful current archive does not hide those failures: the UI reports partial completion and offers a retry. No old source or evaluation is erased to make the status look successful.

## Implementation choice and remaining limits

The submitted workflow uses deterministic extraction and classification for these two structured sources. Ambiguous or unsupported publications require human review. AI is optional in the assignment; no runtime model integration is included.

The project tests one complete correction using the real supplied records and clearly simulated approvals. Repeated calculations are deduplicated, while new input transitions retain their observation time. Historical backfill covers only inputs previously recorded. Broader document layouts, employer coverage, salary policy and production identity/history require further work with the domain owner. Authentication and full payroll integration are outside this assessment slice.
