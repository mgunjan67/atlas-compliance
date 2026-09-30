# Validation record

Reviewed 30 September 2026. This report records the checks performed and their limits.

## Automated checks

`python -m unittest discover -s tests -q`: **121 tests passed**. The suite covers:

- Federal/state precedence in both directions, equality, comparisons before rounding, weekly estimates, missing inputs and unsupported scope.
- Daily expiry, future effective dates, conflicting versions, pending review and explicit rule replacement.
- Repeated ingestion and A → B → A source changes, including a separate comparison for each retrieval and fresh review when a publication returns.
- Preserved evidence after fetch or parsing failures, changed page formats, hidden content, instruction-like source text and cross-source disagreement.
- The supplied 48-row dataset, salary uncertainty, future-start conflicts and reference estimates kept separate from formal compliance results.
- Combined federal/state approval, unchanged counterpart rates, complete impact previews and rollback when part of a review fails.
- Approval and re-evaluation jobs committed together, retry after failure, deduplicated flags and historical calculations using saved employee inputs.
- Saved inspection results and receipts, current-data warnings beside retained results, and consistent exports for historical selections.
- Modified source or receipt detection, checks against a separately trusted receipt digest and audit-chain consistency.
- HTTP request boundaries, invalid hosts, mutation tokens and missing AI credentials.
- AI suggestion persistence, version changes, simulation exclusion, quarantine, retries, invalid responses and worker/database isolation.
- Read-only AI difference summaries, including unknown parser output, old-prompt exclusion and optional failure handling when suggestion storage is locked.

Unit and integration tests use fake AI providers; the HTTP test disables model calls.

## Arithmetic and safety scenarios

`python -m atlas lab` produces [lab-report.json](../output/lab-report.json).

| Check | Observed result | Scope |
|---|---:|---|
| Curated decision cases | 16 / 16 passed | Missing data, corrections, future rules, salary uncertainty and source outage |
| Independent arithmetic comparison | 1,000 / 1,000 passed | Seeded hourly cases; exact fractions; 40 scheduled hours; reversed rule order |
| Deliberately introduced engine bugs | 5 / 5 detected | Lower floor, failed equality, early future activation, ignored expiry and missing-state fallback |
| Instruction-like source fixture | Quarantined | A specific triage pattern, not complete injection detection |

The arithmetic comparison uses exact fractions rather than the engine's rounding helper. Mutation checks modify copies of the actual engine in memory. These synthetic checks overlap with the unit suite and should not be counted as independent coverage.

## Supplied-dataset correction test

`python -m atlas story` produces [story-report.json](../output/reviewer-story/story-report.json), before/after JSON and CSV results, audit events and two receipts.

| Stage | NON_COMPLIANT | COMPLIANT | REVIEW_REQUIRED | Estimated weekly gap |
|---|---:|---:|---:|---:|
| Approved simulated baseline | 21 | 11 | 16 | 3,148.80 AST |
| Approved simulated correction | 23 | 9 | 16 | 3,886.08 AST |

The injected Bellwether correction affects 24 workers and makes two newly below the floor. The supported weekly estimate rises by 737.28 AST. Before approval, affected hourly decisions remain in review. The preview writes no approvals or results.

The original receipt still verifies after the correction. Reconstructing the rules known before the correction reproduces the baseline. AST-0025 changes from `COMPLIANT` to `NON_COMPLIANT`, with a 47.20 AST weekly estimate. The local audit chain is consistent. All approvals in this story are explicitly simulated.

## AI evaluation

The current classifier prompt matched **11 of 12** fictional notices in a recorded September 29 Groq run. It misclassified conflicting dates as a final rate. [ai-evaluation.json](ai-evaluation.json) preserves the answers and prompt version.

The automatic worker completed suggestions for 17 existing publications in one attempt each. That confirms processing, not classification accuracy. Three status requests took 14–34 ms. A browser inspection showed the saved suggestion, supporting evidence and human review form.

An isolated September 30 UI check used model calls disabled and a deliberately mismatched saved response: parser News, synthetic AI Final rate. The list showed **AI differs**, the **AI review** filter selected the publication, and Inspect showed both readings and the parser-correction guidance. Its parser category stayed unchanged. No review was submitted and no browser errors appeared.

Earlier experiments used different prompts and tasks. Their results are described in [AI review](ai-review.md); they are not accuracy claims for the current classifier.

## Browser checks

The current desktop pages were visually inspected: Overview, Rule review, Employee decisions, Scenario lab and AI sandbox. The expanded notice selector stayed in the page flow without covering the notice. An actual future-rule inspection showed its saved automatic AI suggestion and existing approval controls. No console warnings or errors appeared during these checks.

Other focused checks verified:

- Removing AST-0001's wage in an isolated copy showed the exact current data problem beside its preserved earlier wage and receipt.
- Selecting a historical inspection made the sidebar and employee-page exports target the same saved result set.
- Unsaved Scenario lab values and focus survived the one-minute refresh.
- A complete pair update showed 32 changed hourly workers, with separate **At approval** and **Resolved results** history entries.
- Salary records retained `REVIEW_REQUIRED`, with annual pay, an illustrative hourly value and the information needed to resolve the case. Future-start records also showed the date conflict.
- A manual website check completed in the browser, updated both retrieval times, archived 48 results and re-enabled the button without a page refresh.

These were focused manual checks. They do not constitute a full accessibility or cross-browser audit. A 390-pixel viewport was checked on September 25, before the later UI revisions; the latest layout has not had a full mobile audit.

## Live retrieval evidence

Both configured pages were retrieved through the implemented monitor. September 25 polls at 07:08 and 07:16 UTC re-evaluated all 48 employees and wrote JSON/CSV archives with checksum manifests. The preserved pre-review poll contains 48 `REVIEW_REQUIRED` results.

A separate fresh audit at 14:31–14:32 UTC that day retrieved both sites twice. The first pass extracted federal 12.91 and state 16.63 AST/hour, future final notices, the coverage correction, guidance and unrelated news. The second pass reported `UNCHANGED` for both sources with no new candidates. No reviews were recorded in that audit database.

## Package verification

`python -m scripts.package_submission` builds a dated ZIP and refreshes `output/atlas-submission.zip`. It checks member hashes and runs the extracted project in a fresh temporary directory: receipt verification, database seeding, 48 pending live-review results, arithmetic scenarios, a fresh correction story and the full test suite.

The package preserves one pre-review live poll byte for byte. A separate offline evaluation of saved pages includes the current salary-review context and is labelled in `output/live-results.provenance.json`. Local databases, rehearsal approvals, credentials and caches are excluded. `output/package-verification.json` records the archive checksum and command results.

The September 30 rebuild passed these checks and included the AI modules. A clean copy of the GitHub commit also passed the suite and correction story during the preceding readiness audit.

## Validation limits

The tests cover the two supported source layouts and selected synthetic cases. They do not establish general AI accuracy, legal correctness or production readiness. Production identity, concurrent review, externally protected audit history, full payroll history, actual-hour liabilities and complete prompt-injection defence remain unverified.

Receipt replay requires the matching engine and parser versions. Historical reconstruction is limited to source versions and employee inputs actually captured.
