# Atlas operator guide

Use Atlas to check both wage sources, inspect proposed changes and review employee results. Live evaluations use today's UTC date. The examples below come from saved September 2026 pages; check the websites for current rates.

## Check the sources

The top bar is available on every tab. **Check sites** retrieves both websites. **Start 15-min checks** enables polling while the server runs; **Stop 15-min checks** turns it off. Open **Rates & details** to see rates, retrieval times, saved evidence and errors. These controls check live websites even while Scenario lab or AI sandbox is open.

Overview shows result counts, outcomes by work location and the four largest confirmed hourly wage gaps. **View review cases** opens employees with unresolved decisions.

## Review a daily update

1. Open **Rule review** and inspect the pending federal/state update.
2. Compare both rates with both saved sources, including the unchanged rate when only one amount has changed.
3. Check the effective date and employee-impact preview. Expand the evidence section for the full comparison and CSV.
4. Enter your name, tick the source-verification box, and approve or reject the update. Rejection requires a reason; an approval note is optional.

One decision records the pair. Atlas preserves the earlier approval of an unchanged rate and commits new approvals together with the work needed to re-evaluate employees. A failed source check or a newer source version prevents approval of an outdated inspection. Repeated unchanged checks reuse the same inspection.

The preview compares rates. Salary, coverage and employee-data questions may still keep individual results in review after approval. Future final notices and non-daily corrections have their own review and effective-date checks.

## Inspect publications and AI suggestions

The **Publication register** groups ongoing rates, future rates, interpretations, other information and history. Each record shows its wage effect, status and an **Inspect** link.

Inside an inspection, the automatic AI suggestion appears beside the parser's classification. An **AI differs** badge and the **AI review** filter help you find differing readings. Compare both with the saved evidence. If the parser is wrong, leave its proposed rule unapproved until the adapter is corrected and the source reprocessed. The interface has no AI category override.

A queued or unavailable suggestion does not prevent manual review. **AI sandbox** provides fictional notices for testing suggestions separately.

## Saved source examples

| Publisher ID | Jurisdiction | Amount | Effective date | Review focus |
|---|---|---|---|---|
| AFWA-MW-2026.1 | Asteria | 12.73 AST/hour | 2026-09-24 | Covered nonexempt employees; publication date unavailable; one-day validity assumption |
| BDL-MW-2026.1 | Bellwether | 16.63 AST/hour | 2026-09-24 | State rate; physical work location; one-day validity assumption |
| AFWA-2026-0042 | Asteria | 13.25 AST/hour | 2027-01-01 | Final notice published 2026-08-05; inactive before January |
| BDL-2026-0117 | Bellwether | 17.50 AST/hour | 2027-01-01 | Final state order published 2026-08-05; inactive before January |

These captured amounts require review before becoming approved rules in a new workspace.

## Coverage and supporting information

- **AFWA-2026-0038:** the employer-size threshold changed from 24 to 25. The employee file has no employer headcount. Acknowledge this correction only if you accept that the supplied `Covered` field already reflects a valid coverage determination. Otherwise leave it unresolved.
- **AFWA-2026-0031:** a proposed contract-work rule. It may be acknowledged as a proposal or rejected as an active wage rule.
- **BDL-2026-0121 and BDL-2026-0108:** unchanged notices supporting the implemented higher-floor and work-location policies. They need no extra acknowledgment. Revised text is reviewed again.
- **BDL-2026-0099:** a claims-portal announcement with no minimum-wage effect.

In the September 25 example, approving the 12.91 and 16.63 daily rates still leaves 32 hourly decisions blocked by the coverage correction. A deliberate coverage acknowledgment clears that source question. Twelve salary-conversion cases and four future-start conflicts remain separate employee exceptions. Unknown or quarantined content cannot be cleared by a generic acknowledgment.

Atlas records your name, checked evidence and decision. Browser reviews generate a source-specific reason; you can add your own note. Live CLI reviews require a written reason of at least 25 characters. A reviewer name is an audit label, not a verified identity.

## Corrections and failed re-evaluation

For a non-daily numerical correction, select the exact approved version it replaces. A same-date daily correction is handled by the combined inspection. Previous versions and results remain available.

If re-evaluation fails, check details show the failed work and offer **Retry check**. Successful saved results remain available. The CLI executes queued work through `process-jobs` or the monitor. Future jobs wait until their effective date.

## View current and earlier results

In **Employee decisions**, use **Results from** to select a saved inspection containing both rates and the employee results. Expand **Approval & source details** for its provenance. Saved evaluation IDs and receipts are retained. Select **Latest results** to return. Earlier records from separate approvals are labelled as earlier approved result sets.

While a source update or error is unresolved, the screen keeps the last complete result set whose source reviews were resolved. Its original date and the current problem are shown. Current evaluations and check archives still record the unresolved status. The saved view does not extend an expired daily rule or establish compliance for a new date. A different employee population cannot inherit an unrelated result set.

Historical re-evaluation uses employee inputs captured for that date. Keep exported receipts and their checksums separately if another operator will verify them.

## Employee policy questions

All 16 annual-salary records remain `REVIEW_REQUIRED` until there is an approved hourly comparison method and sufficient pay-period and actual-hours evidence. Four also have Active status with December start dates after the example evaluation date. Any salary-to-hourly illustration is labelled as an assumption.

The data or compliance owner needs to confirm:

1. The authorized method for comparing annual salary with an hourly minimum.
2. Whether the supplied `Covered` field resolves employer-size coverage despite the missing headcount.
3. Whether daily-card rates should remain valid beyond their labelled date. Atlas currently uses one-day validity as a conservative policy.
4. The correct start dates and employment status for the four future-start records.

## Run a dummy test

In **Scenario lab**, enter federal and state rates, a test date and an optional name. Click **Run & save dummy test** to evaluate the sample employees and save a separate `DUMMY_TEST` record. Reopen saved tests or export their labelled JSON.

Dummy tests use the deterministic engine and keep salary conversion unresolved. They do not create live rules, approvals, flags, jobs or evaluation receipts. Saved historical results remain in Employee decisions.

For a complete simulated source-change workflow, run `python -m atlas story`. It uses saved pages, a separate database and explicitly simulated approvals. Audit events, jobs and portable receipts remain available without a separate Evidence ledger screen.
