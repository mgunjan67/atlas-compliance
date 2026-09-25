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
- BDL-2026-0121: acknowledge as support for the more-protective-rate precedence policy, not a separate numerical rate.
- BDL-2026-0108: acknowledge as support for work-location applicability, including qualifying remote work.
- BDL-2026-0099: acknowledge/reject as an irrelevant portal announcement.

In the console, enter your own name, inspect the saved source and tick the verification box. Atlas records a source-specific reason; you can add a note, and rejection requires an explanation. The CLI still requires a written reason. Do not use a generated reviewer identity or describe an AI action as a human approval.

For the September 25 live dataset, approving the 12.91 and 16.63 daily rates is not the end of review. `AFWA-2026-0038` corrects an employer-size coverage threshold and still blocks 32 hourly decisions. The console links directly to that blocker and explains the missing employer headcount. An operator may acknowledge the correction only if they deliberately accept the supplied `Covered` field as an upstream coverage determination for this assessment. Otherwise the source review remains open. Twelve salary-conversion cases and four future-start inconsistencies are separate employee-level exceptions. Live review reasons must be at least 25 characters; this guards against placeholders but cannot verify factual quality.

## Review workflow

The console starts in **Live** on today's UTC date. Its Decision readiness panel shows source items that affect today's employee decisions; future, expired and informational items sit under Other publications. Switch to **Replay** for explicitly simulated approvals and the correction demonstration. Keep those activities distinct.

For a numerical candidate, inspect the visible rate, jurisdiction and date against the saved source. Expand Full evidence and impact details when needed. The preview excludes only that candidate for its baseline and hypothetically approves it for comparison. It is not an approval and may still be blocked by other unresolved items. Check both the amount and the number of supported estimates; a changing denominator can make a total misleading.

For a same-date correction, verify and select the exact approved version it supersedes. After review, inspect the re-evaluation job and affected workers. An approval and its job are committed atomically. The command-line workflow requires `process-jobs` or the foreground monitor to execute the queued work.

Use Evidence ledger's earlier-knowledge view to explain historical results; return to current knowledge before reviewing. An old-date check uses stored employee inputs and does not establish a full historical payroll ledger. Keep exported receipts and a digest separately if another operator will verify them.

## Employee assumptions to settle before submission

The default output keeps the 16 annual-salary rows in REVIEW_REQUIRED. Four of those also have Active status with future December start dates. Decide whether to keep that conservative scope or request clarification on the expected salary conversion and status handling. The optional annualization scenario must remain labelled as an assumption.

## Candidate clarification questions (not sent)

1. Should annual salary be converted using 52 times scheduled weekly hours, or should salary records require review without actual-hour/pay-period rules?
2. Should the supplied Covered field be treated as authoritative even though the source includes an employer-size coverage correction and employer headcount is absent?
3. Should daily current-card rates be treated as valid only on the labelled date or until explicitly superseded?
4. Are Active records with future start dates intentional test cases, and should those return REVIEW_REQUIRED?

The prototype already handles these conservatively; answers can refine the policy without blocking basic development.
