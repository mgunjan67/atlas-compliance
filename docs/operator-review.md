# Concrete operator review

No live source-backed candidate has been approved by the AI assistant. The local operator interface contains the actual fetched evidence and the following items.

## Numerical rule candidates

| Publisher ID | Jurisdiction | Amount | Effective date | Review focus |
|---|---|---|---|---|
| AFWA-MW-2026.1 | Asteria | 12.73 AST/hour | 2026-09-24 | Current card; covered nonexempt employees; publication date unavailable; one-day interval assumption |
| BDL-MW-2026.1 | Bellwether | 16.63 AST/hour | 2026-09-24 | Current state card; physical work location; one-day interval assumption |
| AFWA-2026-0042 | Asteria | 13.25 AST/hour | 2027-01-01 | Final notice published 2026-08-05; must remain inactive before January |
| BDL-2026-0117 | Bellwether | 17.50 AST/hour | 2027-01-01 | Final state order published 2026-08-05; future-effective |

These are proposals in Atlas until you compare them with the preserved source excerpts and record your decision. Rates may have changed since the research snapshot: fetch current sources for a current-date decision.

## Non-rate items

- AFWA-2026-0038: coverage threshold changed from 24 to 25 employees. No employer headcount/full coverage table exists in the supplied dataset. Acknowledge only if you accept the explicit assessment assumption that the supplied Covered field has already resolved this issue. Otherwise leave it unresolved. This is a substantive review, not a routine dismiss action.
- AFWA-2026-0031: proposed federal contract-work rule, not effective law. Reject as an active minimum-wage rule, or acknowledge it as a nonbinding proposal.
- BDL-2026-0121: unchanged evidence supports the implemented higher-applicable-rate policy; no extra acknowledgment is needed.
- BDL-2026-0108: unchanged evidence supports physical work-location applicability, including qualifying remote work; no extra acknowledgment is needed.
- BDL-2026-0099: acknowledge/reject as an irrelevant portal announcement.

In the console, enter your own name, inspect the saved source and tick the verification box. Atlas records a source-specific reason; you can add a note, and rejection requires an explanation. The CLI still requires a written reason. Do not use a generated reviewer identity or describe an AI action as a human approval.

For the September 25 live dataset, approving the 12.91 and 16.63 daily rates is not the end of review. `AFWA-2026-0038` corrects an employer-size coverage threshold and still blocks 32 hourly decisions. The console links directly to that blocker and explains the missing employer headcount. An operator may acknowledge the correction only if they deliberately accept the supplied `Covered` field as an upstream coverage determination for this assessment. Otherwise the source review remains open. Twelve salary-conversion cases and four future-start inconsistencies are separate employee-level exceptions. Live review reasons must be at least 25 characters; this guards against placeholders but cannot verify factual quality.

## Review workflow

The console starts on today's UTC date. Overview shows result counts, outcomes by work location and the four largest confirmed hourly wage gaps. **View review cases** opens unresolved employees. Open **Rule review** for pending inspections and the visible **Publication register**; filter future rates, interpretations, other information or history. Each record shows its effect, status and an evidence link. **Scenario lab** tests custom rates separately from live results. The complete simulated correction demonstration is available through `python -m atlas story`; there is no separate Replay workspace in the browser.

For daily updates, inspect the federal and state rates together against both saved sources, even when only one amount changed. The compact dialog shows previous/new amounts, the effective date and a worker-impact count. One approval records the pair. Expand **Evidence and affected employees** for the combined comparison and CSV. This preview is hypothetical; salary, coverage and other unresolved cases still need their own resolution. Future final notices and numerical corrections are reviewed separately against their own effective dates and evidence.

For a same-date non-daily correction, verify and select the exact approved version it supersedes. Approval and its job are committed atomically. If re-evaluation fails, the website-check panel reports the failed work and offers **Retry check**; successful saved results remain available. The command-line workflow uses `process-jobs` or the monitor to execute queued work. Future jobs wait for their effective date.

Use Employee decisions → Results from to inspect saved results and expand Approval & source details for their provenance. An old-date check uses stored employee inputs and does not establish a full historical payroll ledger. Keep exported receipts and a digest separately if another operator will verify them.

While a new update is pending, the main screen keeps the latest complete source-cleared result set with its original date and a warning about the current problem. This also works when the approval was created before the browser was opened. It does not extend an expired rule or establish current compliance. A changed employee population cannot inherit an unrelated saved result set.

## Employee assumptions to settle before submission

The default output keeps the 16 annual-salary rows in REVIEW_REQUIRED. Four of those also have Active status with future December start dates. Decide whether to keep that conservative scope or request clarification on the expected salary conversion and status handling. The optional annualization scenario must remain labelled as an assumption.

## Candidate clarification questions (not sent)

1. Should annual salary be converted using 52 times scheduled weekly hours, or should salary records require review without actual-hour/pay-period rules?
2. Should the supplied Covered field be treated as authoritative even though the source includes an employer-size coverage correction and employer headcount is absent?
3. Should daily current-card rates be treated as valid only on the labelled date or until explicitly superseded?
4. Are Active records with future start dates intentional test cases, and should those return REVIEW_REQUIRED?

The prototype already handles these conservatively; answers can refine the policy without blocking basic development.

New or changed interpretation blocks relevant hourly decisions until resolved. The two unchanged Bellwether notices supporting the implemented higher-floor and work-location policies are informational and need no additional acknowledgment. Exact evidence matching prevents revised notices from inheriting that treatment. Unknown publication formats cannot be cleared by generic acknowledgment.

## Review-screen constraint

Keep the primary dialog compact: previous/new rate, jurisdiction/effective date, one hourly-worker impact count, source links and review controls. Optional notes start collapsed. Put detailed comparisons, salary-reference statistics, explanatory paragraphs and full evidence under the single additional-details disclosure. Do not expand this primary screen again when adding supporting evidence. Layout changes must not change approval or evaluation behavior.

The live browser view follows today's UTC date automatically. Use Employee decisions → Results from for saved historical inspections and Scenario lab for hypothetical rates and test dates. The date-aware evaluation engine and CLI remain available. A single sticky top bar provides Check sites, Start/Stop 15-min checks, and Rates & details on every tab. These controls always operate on live websites, including when Scenario lab is open. Rates, saved evidence and expandable check details live in that shared dropdown instead of repeated page panels. Errors appear in the bar status with details in the dropdown. The redundant workspace header and source-clear banner are omitted; pending inspections and retained-result warnings remain beside their relevant results.

## Preserve results while updates await review

Live Overview, Employee decisions and their JSON export keep the last complete source-cleared result set visible, with its original date and receipt IDs. New pending sources and source errors do not replace this saved view with zero totals. The current evaluation and poll archive still record unresolved current status; old daily rates are never extended into today. When current source issues are resolved, the new complete result set replaces the saved view. Salary and employee-data exceptions remain visible. Replay and explicit historical queries keep their original behavior.

## Combined inspection and saved results

The live console groups the captured federal and state daily rates into one inspection. Inspect both saved sources, enter your name once, and approve or reject the update once. If only one rate changes, the unchanged approved counterpart remains part of the recorded inspection; its earlier rule approval is preserved rather than rewritten. Both new approvals and their jobs commit atomically. Same-date numerical corrections supersede their preceding approved versions. Older unapproved daily proposals replaced by the inspected pair are rejected with the combined review reason.

A failed source check or a changed source version prevents approval of a stale pair. Repeated unchanged checks reuse the existing inspection. Future notices and non-rate interpretation/coverage items retain their own effective-date and review handling; the daily approval does not silently approve unrelated publications.

In Employee decisions, Results from selects a combined inspection containing both rates and the whole employee dataset. Results are frozen with original evaluation IDs and receipts. Select Latest results to return. Earlier separately approved history is preserved as explicitly labelled earlier approved result sets, not invented joint approvals.

## Manual dummy tests

Scenario lab → Dummy rate test accepts federal and state amounts, a date and an optional name. Run & save evaluates the supplied employees with the same deterministic engine and saves a DUMMY_TEST record in a separate table. It does not create operational rules, approvals, flags, jobs or evaluation receipts. Previous approved amounts can be used as a simulated comparison at the same date with the same employee inputs. Salary conversion remains unapproved. Reopen saved dummy tests or export their clearly labelled JSON.

The standalone Evidence ledger screen has been removed. Approval/source details live inside saved inspection results; the underlying audit chain, job records and portable employee receipts remain preserved.

## One testing destination

Scenario lab has one rate-test form. Enter hypothetical federal and state rates manually. The test date remains explicit. Runs are saved separately as dummy tests. The separate website-replay option is removed from the UI. Automated checks start collapsed. Saved historical employee results remain in Employee decisions.
