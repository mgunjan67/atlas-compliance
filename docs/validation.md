# Validation record

Verified locally on 24–25 September 2026. These are observed results, not guarantees of legal correctness or general AI accuracy.

## Automated verification

`python -m unittest discover -s tests -v`: **62 tests passed**. The suite covers:

- Precedence in both directions, equality, subcent comparisons, exact weekly arithmetic, missing/invalid inputs and unsupported scope.
- Daily expiry without fallback, future-effective dates, pending review, conflicting versions and explicit supersession.
- Repeated ingestion, A → B → A source reversion, parse failures with preserved evidence, source failures and format drift.
- Actual supplied dataset integrity and field minimization; salary assumptions and Active/future-start inconsistency.
- Non-decisional salary proxies, approved reference floors and pending-rule gaps in JSON/CSV exports, without changing formal decisions.
- Read-only impact preview, discovery/approval knowledge cutoffs, and historical queries preserving operational flags.
- Atomic review/job writes; recovery after job failure; idempotent flags; historical backfill after an employee changes jurisdiction.
- Modified receipt/source detection, separately trusted receipt digests and altered audit-event detection.
- Hidden content exclusion, a quarantined instruction fixture and cross-source rate disagreement.
- Optional model-output validation: wrong amounts, invented quotes, added approval fields and omitted items are rejected. Request contains no employee input or tools.
- An actual temporary HTTP server: historical export matches earlier knowledge; invalid host and missing mutation token are rejected.
- A full offline poll cycle: both source checks, 48 re-evaluations, dated JSON/CSV archive, checksum manifest, audit event, and no implicit approval.
- A placeholder live-review reason is rejected before an immutable approval can be written.
- The actual September 25 operator path: approving both rates leaves 32 hourly decisions blocked by the coverage correction; an explicit coverage acknowledgment clears those 32 while 16 employee-data/policy cases stay in review.

## Executable scenario lab

`python -m atlas lab` generates [lab-report.json](../output/lab-report.json).

| Check | Observed result | Scope |
|---|---:|---|
| Curated decision cases | 16 / 16 pass | Includes missing data, corrections, future rules, salary uncertainty and source outage |
| Independent arithmetic oracle | 1,000 / 1,000 pass | Seeded cent-denominated hourly cases; exact Fraction oracle; 40 scheduled hours; rule-order reversal |
| Actual engine mutations | 5 / 5 caught | Lower floor, equality failure, future activation, ignored expiry, missing-state fallback |
| Instruction-like source fixture | Quarantined | Specific triage pattern; not complete injection detection |

The oracle uses an independent arithmetic representation rather than calling the engine's rounding helper. Mutation checks compile intentionally modified copies of this project's own engine in memory; they never execute source-page instructions. The generated tests are bounded and synthetic, not a broad regulatory benchmark or an LLM evaluation dataset. Some of these checks are also exercised by the 62-test suite; their counts should not be added as independent coverage claims.

## Supplied-dataset replay

`python -m atlas story` produces [story-report.json](../output/reviewer-story/story-report.json), four sets of JSON/CSV results, audit events and two receipts. Observed results:

- Baseline: 21 NON_COMPLIANT, 11 COMPLIANT, 16 REVIEW_REQUIRED; 3,148.80 AST supported weekly estimate.
- Pending correction: Bellwether hourly decisions wait for review; the unresolved state is preserved in its own export.
- Approved simulated correction: 23 NON_COMPLIANT, 9 COMPLIANT, 16 REVIEW_REQUIRED; 3,886.08 AST supported weekly estimate.
- Impact preview: 24 affected workers, +737.28 AST, two newly below the floor; no preview writes.
- Original receipt verifies after correction; earlier-knowledge states reproduce the baseline; audit chain is consistent.

## Browser verification

The local console was exercised through actual browser controls: correction discovery, impact preview, named simulated review with supersession, resulting 23/9/16 counts, AST-0025's 47.20 weekly estimate, receipt verification, and earlier-knowledge restoration of its COMPLIANT state. The review-form check found and fixed a real DOM issue: a named `id` input shadowed the form's `id` property. The retest completed the approval through the UI.

The overview was visually checked in the in-app browser. This is a focused manual browser check, not an automated cross-browser or full accessibility audit. JavaScript syntax was also checked with Node.

On 25 September, the console received a Niural-inspired visual theme. The overview and impact-review dialog were checked in the browser, including a 390-pixel mobile viewport. Both bundled font families loaded successfully. The existing HTTP integration check passed after adding allowlisted binary font routes. The compliance engine was unchanged.

The live operator path was checked again after the decision-readiness redesign. With both daily rates already approved, the overview and employee table visibly show the one coverage correction blocking 32 hourly decisions, plus the 12 salary-policy and four future-start cases. Rule review puts the blocker first and moves ten other publications into a secondary disclosure. The blocker dialog explains the corrected threshold, missing employer headcount, and the assumption required to acknowledge it. No live coverage decision was made during this check.

The annual-salary flow was also checked in the browser: the overview link filters to 16 records, and AST-0003's receipt displays its annual amount, a clearly non-decisional hourly illustration, the approved reference floor, and three requirements for a final review. A future-start salary record has a fourth requirement to confirm employment timing. The formal result stays REVIEW_REQUIRED and actual hourly pay stays null.

## Packaged handoff

`python -m scripts.package_submission` builds a dated curated ZIP and refreshes `output/atlas-submission.zip` to the same verified bytes. It checks member hashes and extracts into a fresh temporary directory. The extracted copy verifies the included original receipt, seeds a new database, produces 48 pending live-review results, runs the lab, creates a fresh story, verifies the newly generated receipt and passes the full test suite. The archive includes one byte-preserved pre-review live poll plus a separate offline evaluation from saved source pages that carries the current salary-review context. `output/live-results.provenance.json` labels that distinction. It excludes local rehearsal approvals, databases, environment secrets, caches and superseded demonstration exports. The generated dated `output/package-verification-*.json` records the archive digest and command outcomes.

## Live retrieval and limits

Both allowlisted public pages were fetched through the implemented monitor and reported UNCHANGED with no duplicate candidates. Complete live polls on 25 September at 07:08 and 07:16 UTC each re-evaluated all 48 employees and wrote latest JSON/CSV results plus a dated JSON/CSV archive and SHA-256 manifest. All 48 were REVIEW_REQUIRED in the preserved pre-review poll. Later local operator actions are not included in the ZIP. The foreground 15-minute watcher and Codex freshness task were stopped at the candidate's request; the app's schedule starts off by default.

An isolated fresh audit on 25 September at 14:31–14:32 UTC fetched both designated sites twice. The first pass extracted federal 12.91 and Bellwether 16.63 AST/hour for that date, the 2027 final notices, the coverage correction, guidance and irrelevant news. The second pass returned UNCHANGED for both sources with zero new candidates. The isolated audit database recorded zero reviews and is excluded from the submission.

No live model request was made. Optional API quality, response compatibility with a particular chosen model, latency and cost remain unverified. Production identity, concurrency, external audit anchoring, full payroll history, actual-hour liability, complete prompt-injection defense and arbitrary legal-language interpretation were not tested or claimed.
