# Atlas — explainable wage compliance

**Can an operator defend yesterday's decision after today's correction?**

Atlas is a runnable minimum-wage operations prototype for the fictional Asteria assessment. It monitors the two assigned authorities, proposes evidence-backed rules, requires review, evaluates the supplied 48 employees, and preserves the decisions that a correction changes.

Start with the [two-minute reviewer brief](docs/reviewer-brief.md), then try the replay. All replay approvals and the injected correction are explicitly simulated. Fresh live source candidates require a human reviewer.

**Time spent:** approximately 18 hours, candidate-reported, including reading, review and testing with Codex. A 5–10 minute recording is planned but is not included in this ZIP.

## Run locally

Python 3.10+; the core uses only the standard library. No installation, API key or network connection is needed for the preserved-evidence replay. Run from this directory (`py` may replace `python` on Windows):

```powershell
python -m atlas seed
python -m atlas seed --directory data/research/2026-09-25
python -m atlas serve
```

Open **http://127.0.0.1:8787**. The console opens on **Live · source review** and today's UTC date. Use **Check both websites now** for one immediate source check, employee evaluation and archive. Use **Start 15-minute checks** to run that same cycle immediately and every 15 minutes while the server remains open; **Stop 15-minute checks** ends the schedule after any current check finishes. The schedule starts off when the server starts. A page refresh only reads saved state. For the isolated interview scenario, switch Workspace to **Replay · supplied dataset**, choose **Introduce correction**, inspect its impact, record an explicitly simulated review, then open **Evidence ledger**. Inspect employee **AST-0025** and verify its receipt.

The live workspace uses `data/atlas-v2.sqlite3`; replay uses `data/reviewer-demo.sqlite3`. An existing replay retains its history. To rehearse again without deleting anything:

```powershell
python -m atlas serve --port 8788 --demo-db data/rehearsal-2.sqlite3
```

As of the 25 September 2026 capture, Atlas found **12.91 AST/hour federal** and **16.63 AST/hour Bellwether**. Each live rate card shows when its page was checked and opens the saved evidence. In a freshly seeded workspace, those rates require human review. The console now shows a **Decision readiness** panel with the source item actually blocking today's hourly decisions, plus separate counts for salary and future-start exceptions. Older rates, future notices and informational material are available under **Other publications** instead of crowding the current queue. The dated HTML and checksum manifests in `data/research/2026-09-25/` preserve the initial capture; replay deliberately remains on the 24 September dataset.

This is a loopback-only local assessment app. It has request-token and host checks, but no user authentication or production authorization.

The interface follows [Niural's website](https://www.niural.com/) with violet accents, white surfaces, and locally bundled Inter / Inter Tight fonts. See the [visual reference and asset notes](docs/visual-theme.md). It is labelled as an interview prototype.

## The observable case

The baseline uses captured **24 September 2026** publications: federal **12.73 AST/hour**, Bellwether **16.63**. An explicitly synthetic next-day correction changes the September 24 state floor to **18.50**. These amounts are source evidence or fixtures, never engine constants.

| Same 48 supplied employee records | Baseline, simulated review | After simulated correction |
|---|---:|---:|
| Below approved floor | 21 | 23 |
| Meets approved floor | 11 | 9 |
| Needs review | 16 | 16 |
| Supported weekly estimate, AST | 3,148.80 | 3,886.08 |
| Employees represented in estimate | 32 of 48 | 32 of 48 |

The correction targets **24 Bellwether workers**, changes 16 supported hourly results, identifies two newly below the floor, and increases the weekly estimate by **737.28 AST**. Scheduled hours make this an estimate, not accrued payroll liability. Twelve salary-conversion cases and four future-start inconsistencies remain unresolved; all 16 are salaried records.

AST-0025 earns **17.32/hour** for 40 scheduled hours: previously compliant; after correction, **1.18/hour** below the floor and **47.20/week** estimated shortfall. The original decision remains reproducible. [Machine-readable story](output/reviewer-story/story-report.json)

The [employee-result data audit](docs/employee-data-analysis.md) explains why 32 cases enter review during the pending-correction replay and identifies 11 recorded hourly wages below the last approved Bellwether floor. Exports and the console now show approved reference floors, pending proposals and clearly labelled salary proxies alongside unresolved decisions. The overview links directly to all 16 annual-salary cases; each salary receipt shows the illustrative calculation and the specific evidence needed for a final review. A salary proxy is a triage scenario, not actual hourly pay or a legal compliance determination.

The submitted `data/employees.csv` is a 12-field derivative of the supplied fictional dataset. Names, contact details, demographic fields, and bank tokens are omitted because the wage decision does not use them.

## Reproduce the evidence

```powershell
python -m unittest discover -s tests -v
python -m atlas lab
python -m atlas story
python -m atlas verify output/reviewer-story/original-receipt.json
```

`story` creates a fresh, timestamped simulation database and exports before, pending, after, and historical-knowledge results, audit events, and two portable receipts. Re-running it replaces those output files while preserving older databases. `lab` runs 16 curated scenarios, 1,000 exact-fraction arithmetic checks, and five deliberate mutations of the real engine. See [validation and its limits](docs/validation.md).

Keep a receipt's `.sha256` file separately. To check against that trusted digest:

```powershell
python -m atlas verify output/reviewer-story/original-receipt.json --expected-digest DIGEST_FROM_SAVED_SHA256_FILE
```

The verifier checks the bundle checksum, source hashes, source-to-rule binding, matching engine source, and deterministic decision replay. It never executes code embedded in a receipt. A local hash is evidence of consistency, not an external signature or proof of legal authority.

## Live monitoring and human review

```powershell
python -m atlas fetch
python -m atlas candidates
python -m scripts.export_live_capture --date 2026-09-25
python -m atlas review CANDIDATE_ID APPROVED --actor "Your name" --reason "Checked authority, amount, dates, scope and evidence"
python -m atlas process-jobs --date 2026-09-24
python -m atlas evaluate --date 2026-09-24
python -m atlas poll-once
python -m atlas watch --interval 900
```

Use the complete ID printed by `candidates`. Numerical candidates support APPROVED/REJECTED. Interpretive items support ACKNOWLEDGED/REJECTED; acknowledgment does not create a numerical rate. Inspect the coverage correction and [operator checklist](docs/operator-review.md) before making a decision. A correction uses `--supersedes OLD_APPROVED_ID`. App review records are immutable.

Review and its re-evaluation job commit together. The UI processes jobs immediately; the CLI separates `review` and `process-jobs`, and `watch` drains due jobs on each poll. Failed/interrupted jobs can be retried without duplicate results or flags. Future rules wait until their effective date. Historical backfill uses previously stored employee inputs, including old work locations.

`poll-once` fetches both sources, processes due re-evaluations, evaluates all 48 employees for today's UTC date, and writes `output/live-results.json`/CSV plus a timestamped JSON/CSV archive and SHA-256 manifest under `output/live-archive/YYYY-MM-DD/`. It archives each check even when the pages are unchanged or all decisions still need review. The console's manual and scheduled buttons run this cycle. The separate `watch --interval 900` command offers the same foreground cycle for CLI use; do not run both schedules at once. The earlier foreground watcher and Codex freshness automation have been stopped at the user's request. No source candidate is approved automatically. Fetching uses only the two assigned URLs; no hidden publication schedule, internal wage database or bundled script is inspected.

## Architecture and decisions

See the [assignment blueprint and implemented architecture diagrams](docs/architecture.md) for the two flows side by side.

```text
Allowlisted public HTML → immutable snapshots + diff + provenance
  → visible source extraction + corroboration + optional AI second opinion
  → candidate review + impact preview
  → approved dated versions + transactional re-evaluation job
  → deterministic jurisdiction/date selection + Decimal arithmetic
  → immutable decisions + flags + portable receipts + audit chain
```

| Responsibility | Implementation |
|---|---|
| Evidence, visible fields and exact quote spans | `atlas/monitor.py`, `atlas/extract.py` |
| Versions, reviews, knowledge time and audit chain | `atlas/store.py` |
| Four decision states, precedence and arithmetic | `atlas/engine.py` |
| Impact preview, durable jobs and historical replay | `atlas/workflow.py` |
| Portable decision verification | `atlas/receipt.py` |
| Optional model proposal validation | `atlas/ai.py` |
| Operator console and supplied-dataset scenario | `atlas/web.py`, `atlas/showcase.py` |
| Curated cases, independent oracle and mutation checks | `atlas/lab.py`, `tests/` |

Policies are explicit: choose the latest applicable approved rule per jurisdiction, then the highest federal/state floor; equality passes; compare before rounding. Missing data, expired rates, conflicting rules, unsupported salary conversion, unresolved relevant source content and current source failures cannot silently pass. Status is one of COMPLIANT, NON_COMPLIANT, INSUFFICIENT_DATA or REVIEW_REQUIRED.

Daily cards receive one-day validity as a conservative assumption, not a discovered sunset law. Card publication dates remain null where no separate date exists. Coverage relies on the supplied Covered field only after an operator accepts that assumption. `--annualize-salary` is an explicit 52-week estimate scenario, never an authoritative conversion rule.

Knowledge-time queries are available independently of the wage evaluation date:

```powershell
python -m atlas evaluate --date 2026-09-24 --known-at 2026-09-24T10:02:00+00:00 --output output/as-known.json
```

This uses the selected database's actual discovery/review history. A cutoff before human approval will correctly show pending review. Historical queries do not overwrite operational flags.

## What AI does here

The core remains usable offline. `ai-audit SNAPSHOT_ID` optionally calls the OpenAI Responses API for a structured second opinion on public source items. Set `OPENAI_API_KEY` and an explicitly chosen `ATLAS_OPENAI_MODEL` in your environment; `.env.example` is a guide, not an automatically loaded file.

The model receives extracted public source text only, no employee payload, tools or approval permission. Schema, source IDs, exact quotes, fields and omitted items are checked against the deterministic extraction. Disagreement is saved for review. This is a shadow check of supported source structures, not a general-purpose legal extractor.

**No live model call was made for this submission.** Boundary validation is tested; model quality, latency and cost are unmeasured. AI assistance during development is [disclosed separately](docs/disclosure.md).

## Scope and handoff

The [research memo](docs/research.md) explains source findings and assumptions; the [walkthrough](docs/walkthrough.md) gives a seven-minute demonstration; [PLAN.md](PLAN.md) maps assessment requirements to evidence.

This local slice does not implement a complete employee/pay history, actual-hours liability, independently verified employer coverage, authenticated reviewers, externally notarized storage, distributed job leases, production scheduling or arbitrary legal-language interpretation. Backfill covers stored evaluations only. Source-format changes and ambiguous notices require review.

The deliverable is built and locally verified. The candidate still needs to understand and personalize it, make their own live review decisions if used, and record the required walkthrough. The ZIP includes the original checked live poll under `output/live-archive/` and a separate offline pre-review export under `output/live-results.*`; `output/live-results.provenance.json` explains that distinction. No GitHub repository, recording, email or submission has been published by this workflow.
