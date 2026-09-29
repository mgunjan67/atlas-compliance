# Validation record

Updated locally on 30 September 2026. These are observed results, not guarantees of legal correctness or general AI accuracy.

## Automated verification

The AI additions cover persistent reuse, candidate-version changes, simulation exclusion, pre-inference quarantine, retry limits, missing credentials, invalid categories/references, provider errors and database-lock isolation. These tests use fake providers; the HTTP test explicitly disables model calls.

The final classifier prompt was also run against 12 fictional notices through Groq: **11 matched**, with conflicting dates still misclassified as a final rate. See the [recorded outputs](ai-evaluation.json). The automatic worker completed all 17 existing live publication suggestions in one attempt each; completion does not establish that every classification is correct. Status requests remained responsive (14–34 ms across three checks). A browser inspection of the pending Asteria future notice showed its saved AI suggestion, supporting-evidence disclosure and unchanged human approval form. No live approvals were performed.

`python -m unittest discover -s tests -q`: **121 tests passed**. The suite covers:

- Saved AI differences: normalized parser categories, unknown parser output, exclusion of pending/failed/old-prompt results, and read-only failure handling when suggestion storage is locked. Reading the list makes no model calls and leaves the main database unchanged.

- Precedence in both directions, equality, subcent comparisons, exact weekly arithmetic, missing/invalid inputs and unsupported scope.
- Daily expiry without fallback, future-effective dates, pending review, conflicting versions and explicit supersession.
- Repeated ingestion, A → B → A source reversion, parse failures with preserved evidence, source failures and format drift.
- Actual included dataset integrity and field minimization; salary assumptions and Active/future-start inconsistency.
- Non-decisional salary proxies, approved reference floors and pending-rule gaps in JSON/CSV exports, without changing formal decisions.
- Read-only impact preview, discovery/approval knowledge cutoffs, and historical queries preserving operational flags.
- Atomic review/job writes; recovery after job failure; idempotent flags; historical backfill after an employee changes jurisdiction.
- Modified receipt/source detection, separately trusted receipt digests and altered audit-event detection.
- Hidden content exclusion, a quarantined instruction fixture and cross-source rate disagreement.
- An actual temporary HTTP server: combined inspection exports retain the original evaluation IDs; invalid host and missing mutation token are rejected; removed replay endpoints cannot create demo databases.
- Missing-wage warnings identify the current employee-data problem while preserving previous results and receipts. Retained-result exports carry the same warning.
- Each new retrieval stores its own comparison, including B → A when A's snapshot already exists; unchanged checks have an empty diff. Existing snapshot records remain intact for old receipts.
- A cold browser recovers the complete approved or resolved same-day inspection when a pending update has already replaced operational flags. A newer saved inspection takes precedence over an older display cache.
- Returning final notices, guidance and corrections get fresh review occurrences; repeat checks remain idempotent. Both old and newly approved recurrence receipts replay.
- Unsupported decimal precision, signed/comma-separated amounts and restricted or unfamiliar notice scope cannot become complete numerical proposals. Unchanged supported publications retain their identities across the parser upgrade; historical v3 receipts still use their original parser.
- Partial polls retain failed historical jobs and valid current archives. Retrying completes failed jobs without duplicate approvals or flags.
- A full offline poll cycle: both source checks, 48 re-evaluations, dated JSON/CSV archive, checksum manifest, audit event, and no implicit approval.
- A placeholder live-review reason is rejected before an immutable approval can be written.
- The actual September 25 operator path: approving both rates leaves 32 hourly decisions blocked by the coverage correction; an explicit coverage acknowledgment clears those 32; unchanged guidance is already handled by the implemented policy while 16 employee-data/policy cases stay in review.

## Executable scenario lab

`python -m atlas lab` generates [lab-report.json](../output/lab-report.json).

| Check | Observed result | Scope |
|---|---:|---|
| Curated decision cases | 16 / 16 pass | Includes missing data, corrections, future rules, salary uncertainty and source outage |
| Independent arithmetic oracle | 1,000 / 1,000 pass | Seeded cent-denominated hourly cases; exact Fraction oracle; 40 scheduled hours; rule-order reversal |
| Actual engine mutations | 5 / 5 caught | Lower floor, equality failure, future activation, ignored expiry, missing-state fallback |
| Instruction-like source fixture | Quarantined | Specific triage pattern; not complete injection detection |

The oracle uses an independent arithmetic representation rather than calling the engine's rounding helper. Mutation checks compile intentionally modified copies of this project's own engine in memory; they never execute source-page instructions. The generated tests are bounded and synthetic, not a broad regulatory benchmark or an LLM evaluation dataset. Some of these checks are also exercised by the unit/integration suite; their counts should not be added as independent coverage claims.

## Supplied-dataset replay

`python -m atlas story` produces [story-report.json](../output/reviewer-story/story-report.json), four sets of JSON/CSV results, audit events and two receipts. Observed results:

- Baseline: 21 NON_COMPLIANT, 11 COMPLIANT, 16 REVIEW_REQUIRED; 3,148.80 AST supported weekly estimate.
- Pending correction: Bellwether hourly decisions wait for review; the unresolved state is preserved in its own export.
- Approved simulated correction: 23 NON_COMPLIANT, 9 COMPLIANT, 16 REVIEW_REQUIRED; 3,886.08 AST supported weekly estimate.
- Impact preview: 24 affected workers, +737.28 AST, two newly below the floor; no preview writes.
- Original receipt verifies after correction; earlier-knowledge states reproduce the baseline; audit chain is consistent.

## Browser verification

On 30 September, an isolated server with model calls disabled used a deliberately mismatched saved suggestion: parser News, synthetic AI Final rate. The publication list showed an AI differs badge, the AI review filter selected that record, and Inspect showed both readings and the parser-correction guidance. The news classification stayed unchanged. No review was submitted, no real inference ran, and no browser warnings or errors appeared. This verifies presentation and routing of a disagreement, not model accuracy.

On 28 September, an isolated copy with AST-0001's hourly wage removed showed an employee-data warning, its exact current error, and the unchanged saved wage/receipt in the employee dialog. Selecting the September 25 inspection made both sidebar and employee-page export links target the same saved inspection. The simplified live Overview showed 21 below minimum, 11 meeting minimum and 16 review cases; automatic checks remained off and no browser console errors were observed. The Overview now presents results, source checks and any pending inspection; detailed salary analysis remains in employee records. The old web replay and per-rule history routes were removed; the tested CLI story remains available.

Earlier browser checks below describe the UI at the time of each check; removed replay controls are no longer part of the current console.

The local console was exercised through actual browser controls: correction discovery, impact preview, named simulated review with supersession, resulting 23/9/16 counts, AST-0025's 47.20 weekly estimate, receipt verification, and earlier-knowledge restoration of its COMPLIANT state. The review-form check found and fixed a real DOM issue: a named `id` input shadowed the form's `id` property. The retest completed the approval through the UI.

The overview was visually checked in the in-app browser. This is a focused manual browser check, not an automated cross-browser or full accessibility audit. JavaScript syntax was also checked with Node.

On 25 September, the console received a Niural-inspired visual theme. The overview and impact-review dialog were checked in the browser, including a 390-pixel mobile viewport. Both bundled font families loaded successfully. The existing HTTP integration check passed after adding allowlisted binary font routes. The compliance engine was unchanged.

The live operator path was checked again after the decision-readiness redesign. With both daily rates already approved, the overview and employee table visibly show the one coverage correction blocking 32 hourly decisions, plus the 12 salary-policy and four future-start cases. Rule review puts the blocker first and moves ten other publications into a secondary disclosure. The blocker dialog explains the corrected threshold, missing employer headcount, and the assumption required to acknowledge it. No live coverage decision was made during this check.

The annual-salary flow was also checked in the browser: the overview link filters to 16 records, and AST-0003's receipt displays its annual amount, a clearly non-decisional hourly illustration, the approved reference floor, and three requirements for a final review. A future-start salary record has a fourth requirement to confirm employment timing. The formal result stays REVIEW_REQUIRED and actual hourly pay stays null.

The live Rule review archive was visually checked after grouping its 13 records by effect. The September 27 daily rates appear as active; January 2027 notices appear as pending and inactive; the acknowledged coverage clarification appears under interpretations without a new rate; proposals, news and expired daily cards have their own concise groups. Opening Bellwether guidance shows its type as Interpretation while its human review remains open.

## Packaged handoff

September 28 priority fixes add seven regression cases: pending/approved/rejected daily-publication reversions; complete next-day pair impact; federal overtaking an unchanged state rate; unavailable baseline handling; and linked resolved result snapshots after coverage review. Recurring publication receipts verify against the original source text and the new occurrence identity. Original approvals and result snapshots remain immutable. A real browser check confirmed that unsaved Scenario lab values and focus survive the one-minute refresh. An isolated QA server showed 32 changed hourly workers for a complete pair update and separate At approval / Resolved results history entries. No live source approvals were made during these checks. README and reviewer instructions now use the actual UI plus the CLI story for offline change tests.

`python -m scripts.package_submission` builds a dated curated ZIP and refreshes `output/atlas-submission.zip` to the same verified bytes. It checks member hashes and extracts into a fresh temporary directory. The extracted copy verifies the included original receipt, seeds a new database, produces 48 pending live-review results, runs the lab, creates a fresh story, verifies the newly generated receipt and passes the full test suite. The archive includes one byte-preserved pre-review live poll plus a separate offline evaluation from saved source pages that carries the current salary-review context. `output/live-results.provenance.json` labels that distinction. It excludes local rehearsal approvals, databases, environment secrets, caches and superseded test exports. The generated dated `output/package-verification-*.json` records the archive digest and command outcomes.

## Live retrieval and limits

Both allowlisted public pages were fetched through the implemented monitor and reported UNCHANGED with no duplicate candidates. Complete live polls on 25 September at 07:08 and 07:16 UTC each re-evaluated all 48 employees and wrote latest JSON/CSV results plus a dated JSON/CSV archive and SHA-256 manifest. All 48 were REVIEW_REQUIRED in the preserved pre-review poll. Later local operator actions are not included in the ZIP. The foreground watcher is optional; the app schedule starts off by default.

An isolated fresh audit on 25 September at 14:31–14:32 UTC fetched both designated sites twice. The first pass extracted federal 12.91 and Bellwether 16.63 AST/hour for that date, the 2027 final notices, the coverage correction, guidance and irrelevant news. The second pass returned UNCHANGED for both sources with zero new candidates. The isolated audit database recorded zero reviews and is excluded from the repository.

Production identity, concurrency, external audit anchoring, full payroll history, actual-hour liability, complete prompt-injection defense and arbitrary legal-language interpretation were not tested or claimed.

## September 27 audit regressions

The expanded suite reproduces and guards against unseen publication containers, changed unmapped prose, negated proposal labels, numerical rules under news, narrowed card/notice coverage, pending interpretation, generic acknowledgment of unknown content, salary scenarios mutating live history, conflicting prior floors, and input reversion chronology. Manual checks return while a mocked slow fetch is running.

The fresh browser replay was tested after these changes: guided entry, 16.63 → 18.50 review, simulated approval, AST-0025's 47.20 weekly estimate and receipt verification. The employee view now has four options: Actual results (32 hourly records), All decisions (48 including salary proxies), Approved results (completed decisions) and Review required (including missing-data cases). Browser checks verified salary proxies appear only in All decisions. Live source fetching were not exercised during this offline verification.

Unfamiliar prose can require adapter repair; the text guard is deliberately conservative, not a universal legal classifier. Old engine receipts require the matching historical implementation; regenerated example receipts match this release.

Manual-check completion was subsequently tested against both configured source websites on September 27. The browser automatically showed No changes found, updated both source timestamps, confirmed 48 archived results and re-enabled the button without a page refresh. A regression check covers unchanged candidates linked to newer snapshots; another covers failed archiving clearing the busy state and suppressing stale success. No approvals were made.
