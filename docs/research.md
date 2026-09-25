# Atlas research memo

Research date: 24 September 2026. This memo distinguishes observed source facts, prototype policy, and unresolved questions. All legal-looking material below belongs to the fictional assessment; it is not real-world payroll advice.

**25 September follow-up.** A fresh fetch of the two designated pages found the Asterian federal daily card at **12.91 AST/hour**, effective 25 September, source version `2026.09.25.1`; Bellwether's daily card remained **16.63 AST/hour**, effective 25 September. Each page displayed the other's amount as a comparison, so the primary and peer figures agreed on this capture. Atlas stored both as new candidates with raw HTML, retrieval timestamps and SHA-256 digests in `data/research/2026-09-25/`. This verifies what the pages said when fetched and preserves the evidence; it does **not** constitute human approval of an active rule. The packaged pre-review export has both candidates in `REVIEW_REQUIRED` and all 48 employee results in review; subsequent local reviewer actions are separate and not shipped. The 24 September replay below is unchanged.

## Executive findings

The difficult part is not comparing two numbers. It is deciding which source statements constitute approved, applicable rules at a particular time, and whether the employee data supports a defensible calculation.

The two public pages can be retrieved as server-rendered HTML without browser automation or an API. Their rate cards, notice bodies, IDs and date metadata are available in the HTML. Separate notices contain proposals, corrections, interpretive guidance and a future final rate. A page-level hash alone is therefore insufficient to decide whether a wage rule changed.

The actual supplied dataset contains 48 employees: 24 in Federal Territory and 24 in Bellwether; 32 hourly and 16 annual-salary records. Four employees are marked Active despite start dates in December 2026. Salary conversion, employment timing and coverage must be visible product decisions, not hidden preprocessing.

## 1. Authority and retrieval evidence

The assessment itself designates these two fictional sites as authoritative. An official-looking logo, a Vercel domain, or a search result is not independent proof of legal authority. We pin these exact HTTPS origins because the assessment explicitly identifies them:

- [Asterian Federal Wage Authority](https://asterian-federal-wage-site.vercel.app/)
- [Bellwether Department of Labor](https://bellwether-state-wage-site.vercel.app/)

Retrieved copies are preserved under `data/research/`. The adjacent JSON manifests record URL, timestamp, raw SHA-256, HTTP status and content type. Evidence was refreshed at approximately 09:42 UTC on 24 September 2026; the captured bytes matched the earlier retrieval. Full HTML is preserved as evidence, while extraction reads visible rate cards and notices and ignores scripts. No internal routes, JavaScript bundles, wage database or future publication schedule were explored or used.

The prototype only requests the two allowlisted URLs. Redirects require investigation rather than silently expanding the trust boundary. A source error is an operational event, not evidence that no regulation changed.

## 2. What each source actually says

| Item | Observed content | Interpretation |
|---|---|---|
| Federal current card, AFWA-MW-2026.1 | 12.73 AST/hour, effective 24 Sep 2026, source version 2026.09.24.1; covered nonexempt employees | Numerical candidate requiring review; do not bake the amount into code |
| Federal AFWA-2026-0042 | Published 5 Aug 2026; final notice sets 13.25 AST/hour effective 1 Jan 2027 | Future-effective candidate; publication date does not make it active in September |
| Federal AFWA-2026-0038 | Published 22 Jul 2026; corrects employee-count threshold from 24 to 25; wage unchanged | Coverage issue requiring review, not a new hourly rate |
| Federal AFWA-2026-0031 | Proposed federal contract-work rate; comment period open | Not effective law; never approve as a general wage rate |
| Bellwether current card, BDL-MW-2026.1 | 16.63 AST/hour, effective 24 Sep 2026, daily rate; covered nonexempt employees | State numerical candidate requiring review |
| Bellwether BDL-2026-0121 | Published 6 Aug 2026; higher state requirement controls covered work in Bellwether | Precedence evidence, not another rate |
| Bellwether BDL-2026-0117 | Published 5 Aug 2026; 17.50 AST/hour effective 1 Jan 2027 | Separate future state rule; do not activate early |
| Bellwether BDL-2026-0108 | Published 14 Jul 2026; state rate covers hours physically worked in Bellwether, including qualifying remote work | Use work location, not home address or employer location |
| Bellwether BDL-2026-0099 | Published 30 Jun 2026; new claims portal; no wage/coverage/effective-date change | Irrelevant operational announcement |

Both pages display cross-jurisdiction comparison amounts. The federal card supplies the primary federal rule and the state card the primary state rule. Comparison figures are stored as corroborating observations, not duplicate rules. For current live evaluation, disagreement between a page's peer figure and the other authority's primary figure becomes a source-health review issue. A changed peer amount alone does not create a new primary federal candidate. This is a bounded numerical consistency check, not general semantic contradiction detection.

### The publication-date gap

Notices have explicit publication dates. The rate cards have effective dates and a retrieval timestamp, but no separately labelled original publication date. Atlas retains `publication_date: null` for a card with an explanation; it does not pretend the effective date or retrieval date is the publication date. This is an explicit exception to the requested output completeness and should be explained in the interview. A human may still approve the direct authoritative current card, documenting the limitation.

### Daily validity is an assumption

The state card describes a daily rate, and the federal card describes a rate keyed to the current date. The prototype conservatively gives daily cards the interval `[effective date, next day)`. This prevents yesterday's observed amount from silently becoming today's source of truth after a missed fetch. It does not assert a legal sunset clause that the page never published. Final notices remain effective from their stated date until replaced by a newer applicable approved rule.

Consequence: Atlas cannot reconstruct an unobserved historical day's daily rate. It returns INSUFFICIENT_DATA. This is safer than inventing history from today's card. If the employer confirms that a rate persists until superseded, this interval policy can be changed with an explicit policy version and regression tests.

## 3. Employee data research

Source: [supplied synthetic employee system of record](https://docs.google.com/spreadsheets/d/1aveGUtubVqVQjMbtRdnOmW9iNRnxwadi7QFHUctB6Wc/edit?usp=sharing). `data/employees.csv` is a minimized, readable derivative of that export, not a byte-for-byte copy of the original workbook.

Observed schema includes work country/state, pay basis, hourly AST wage, annual AST salary, scheduled weekly hours, currency, employment status, minimum-wage coverage and start date. The supplied export also contained synthetic personal, bank, contact and demographic fields unrelated to minimum-wage evaluation. The submitted CSV retains only the 12 fields used by Atlas, and the importer selects that same allowlist before creating evaluation evidence.

All supplied records are marked Active and Covered. That permits a documented MVP assumption that the supplied coverage field has been verified upstream. It does not prove the employer meets the corrected small-employer threshold. That unresolved correction starts in REVIEW_REQUIRED; a human must explicitly acknowledge the upstream-coverage assumption or keep the case blocked. Atlas cannot independently calculate coverage because employer headcount and the full coverage table are absent.

Start dates in the connector export are Excel serial dates. Convert with the conventional 1899-12-30 epoch, never interpret them as Unix timestamps. On the research date, AST-0012, AST-0024, AST-0036 and AST-0048 have future start dates (12, 4, 16 and 8 December respectively) despite Active status. Return REVIEW_REQUIRED for these contradictions.

### Annual salary policy

Sixteen rows have annual salary instead of hourly wages. Neither fictional authority supplies a conversion rule or work-period accounting method. Default output is REVIEW_REQUIRED, not an invented hourly wage. The explicit `--annualize-salary` scenario estimates `annual salary / (52 * scheduled weekly hours)` and labels that assumption in every affected trace. Actual compliance for salaried employees would need an approved method, hours worked, pay-period rules and any applicable exemptions. The estimate should not be submitted as legally confirmed arithmetic.

Scheduled hours support an estimated weekly shortfall, not a statement of wages actually owed. Unknown hours do not block an otherwise valid hourly comparison; they leave the weekly estimate null. Invalid or negative hours do block it.

Historical evaluations use the employee input snapshot supplied to that run. The dataset is not a historical wage ledger; therefore an old-date evaluation is a scenario unless an appropriate historical employee snapshot is supplied.

## 4. Rule selection and money policy

For a Federal Territory employee, require an applicable approved Asterian rule. For a Bellwether employee, require both federal and state rules. Select the latest effective approved version within each jurisdiction, then take the higher applicable floor. Do not encode “state always wins”: a future federal floor could be higher.

Same-jurisdiction, same-date approved amounts that disagree are a conflict, not an invitation to choose the last inserted record. A reviewer must approve an explicit supersession link for a correction. Existing rule, review and evaluation records stay intact. A rejected proposal never enters approved rule selection. Future-effective pending proposals do not block today's otherwise valid evaluation.

Money is parsed from strings into Python Decimal, which supports decimal arithmetic and explicit rounding. Equality with the controlling floor is COMPLIANT. Compare unrounded values; only round reported monetary estimates to 0.01 AST with ROUND_HALF_UP. Weekly shortfall is computed from the unrounded hourly difference, then rounded once. Rounding is a documented prototype policy, not a rule discovered in these sources. [Python Decimal documentation](https://docs.python.org/3/library/decimal.html)

Statuses:

- COMPLIANT: supported complete input and approved rules; wage meets or exceeds the floor.
- NON_COMPLIANT: supported complete input and approved rules; wage is below the floor.
- INSUFFICIENT_DATA: missing required inputs or no rule covering the evaluation date.
- REVIEW_REQUIRED: ambiguity, unsupported cases, inconsistent employee information, unresolved relevant source content, conflicting rules or source-health concerns.

## 5. Monitoring, evidence and changes

Store the raw response and its content hash, normalized relevant text and its hash, a unified semantic diff, retrieval time and parser version. Build semantic text from the current card and each notice. Changes in script bundles or unrelated footer formatting may alter raw bytes without creating new candidates. Exact repeated candidate content is deduplicated by its identity hash; repeated evaluation of identical inputs and rules reuses the original result.

Primary daily-rule identity excludes the other jurisdiction's comparison amount, preventing a state-only change from duplicating the federal rule. Every observed source version remains linked to its candidates. Near-duplicate notices with changed wording or IDs are not automatically adjudicated as equivalent. Other cosmetic edits inside a rate card can still create a review candidate. Exact evidence spans are included for extracted fields; no numerical confidence score is invented.

Network retrieval has bounded retries, a timeout, a response-size limit and content-type checks. Unexpected page structure fails extraction and preserves the failed response. The most recent fetch error blocks current-day compliance. A configurable future enhancement is a risk-based freshness threshold; the MVP uses 24 hours plus daily rate expiry. The monitor runs as a foreground command. It has no service-installation or external scheduler dependency and stops when its process stops.

An approval transaction also queues a durable re-evaluation job. Federal changes target both populations; Bellwether changes target its workers. Due jobs use the affected jurisdiction and effective interval, including stored historical employee snapshots. An employee who has since moved is assessed using the work location in that historical input. Jobs have PENDING/RUNNING/FAILED/DONE states; retries reuse evaluation identities and current flag records. Future approvals remain queued until effective. On each poll the monitor also checks all 48 current records for freshness failures and day changes. It is a single-worker queue without distributed leases. Missed source dates cannot be reconstructed from a current-only website.

SQLite transactions group each ingestion and review write so partial operations are rolled back. Hash-derived unique keys and database constraints enforce idempotency. This is a single-operator local prototype, not a distributed ingestion queue. [SQLite transaction documentation](https://www.sqlite.org/lang_transaction.html)

## 6. AI boundary and untrusted content

Runtime AI is optional in the brief. Primary extraction is deterministic because the observed HTML exposes structured fields. Unsupported wording becomes a review item. An optional `ai-audit` command implements a second opinion using the OpenAI Responses API with strict structured output. The model is explicitly configured, sees only extracted public source items, has no tools or approval authority, and cannot change a wage calculation. No live model request has been made, so model quality, latency and cost remain unmeasured. [OpenAI structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs)

The second opinion proposes relevance labels and structured fields with exact evidence quotes. Validation checks allowed fields, known source IDs, quoted text, omitted items and agreement with the deterministic extraction; disagreements remain recorded for review. This checks supported structures rather than replacing the primary parser with a general legal-language model. Tests reject hallucinated rates, invented quotes and approval fields. Retrieved content is untrusted data even on an allowlisted site. Scripts are not executed, hidden content is excluded and the UI escapes source content. A small instruction-pattern triage can quarantine suspicious visible text; it is explicitly incomplete. These boundaries follow the separation of instructions/data, least privilege, validation and human review discussed in the [OWASP prompt-injection prevention guidance](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).

This is not a claim to detect every malicious text pattern. A source can still publish misleading facts; provenance and human review are needed. Regex keyword blacklists alone would not solve that problem.

## 7. Corrections, retroactivity and historical evidence

A numerical correction with a supported final-rate structure creates another reviewable candidate. Same-effective-date corrections can explicitly supersede the prior approved candidate. Correction notices whose wording cannot be interpreted confidently are review-only; arbitrary legal correction language is not automatically supported.

Original evaluations remain available by evaluation ID. A correction produces a new result under current approved knowledge. The `--known-at` query independently filters discovery and review timestamps, allowing the same wage date to be evaluated with knowledge from before the correction. Future discoveries are excluded; later approvals remain pending at the earlier cutoff. Such queries do not update operational flags.

The durable job automatically revisits stored historical evaluation dates within the affected interval using saved employee inputs. It does not backfill arbitrary unobserved payroll periods or claim a complete effective-dated employee ledger. Multiple historical input versions for an employee/date are resolved to the latest stored input; production use would need an authoritative payroll snapshot/version contract.

Portable receipts contain the input, rules as used, raw source snapshots, engine hash and a local audit checkpoint. Verification re-extracts the rules, checks their binding and recalculates the decision without executing receipt-supplied code. An exported receipt digest retained separately detects replacement. A database hash chain detects inconsistency relative to its local history; someone controlling all files could rewrite both data and hashes. This is not notarized or tamper-proof storage.

## 8. Demonstrated employee impact

The supplied-dataset replay uses simulated reviews of the captured source, then injects a clearly labelled next-day correction to September 24's state rate: 16.63 → 18.50. It does not predict or claim an actual future publication. The preview targets 24 Bellwether records; 16 hourly results change and two workers newly fall below the floor. The supported weekly estimate increases by 737.28 AST, from 3,148.80 to 3,886.08, across 32 of 48 employees. Salary and employment-date uncertainty remains visible in 16 records.

For AST-0025, 17.32/hour was sufficient under 16.63 but is 1.18 below 18.50, giving 47.20 at 40 scheduled hours. The earlier receipt verifies after correction and the earlier knowledge query reproduces its original COMPLIANT state. The [story report](../output/reviewer-story/story-report.json) contains machine-readable evidence. This demonstrates the workflow; it is not an observed payroll loss or measured operational ROI.

## 9. Before real payroll use

Required changes include legally validated coverage and salary-conversion rules; actual hours and effective-dated employee wage/location histories; authenticated reviewers and permissions; durable service scheduling and outbound alerting; secure storage and retention; access-controlled evidence; broader legal-correction handling and review revocation; multi-worker job leasing; and operational monitoring. The local correction/replay workflow is implemented, while externally anchored audit evidence and complete employee history remain outside scope.

## Interview decisions worth defending

1. Why refusing to guess salaried hourly pay is preferable to a superficially complete green dashboard.
2. Why a coverage correction can matter even when the numerical rate stays the same.
3. Why publication date, effective date, retrieval time and approval time are separate concepts.
4. Why the comparison uses the highest approved applicable floor rather than a fixed state override.
5. Why the daily-card interval is an explicit conservative assumption and what operational tradeoff it creates.
6. Why a functioning, tested non-LLM extraction path is reasonable, and where AI could improve it.
