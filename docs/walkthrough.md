# Seven-minute reviewer walkthrough

Use a fresh replay DB: `python -m atlas serve --port 8788 --demo-db data/recording-1.sqlite3`. If the filename was used before, choose another. Open http://127.0.0.1:8788 and switch **Workspace** to **Replay · supplied dataset** before beginning the demonstration. Keep the terminal available for the lab and receipt verification. This script is preparation for a recording or live demo; no recording is included.

## 0:00–0:45 — Frame the operator problem

“The number comparison is deterministic. The operational problem is whether the rule is authoritative, effective, approved and relevant to the employee—and whether that answer can be explained after a correction.”

Show the simulation banner. Explain that the two sources and employee data come from the assessment. Baseline approvals are simulated; the injected 18.50 correction is synthetic. The live workspace remains separate.

## 0:45–1:45 — Show the actual data and an honest baseline

Overview: 48 supplied employees, 21 below the approved floor, 11 compliant, 16 requiring review. Known weekly estimate is 3,148.80 AST for 32 records. Explain that scheduled hours do not establish wages owed.

Open Employee decisions. Inspect a salary record and AST-0012. Explain the missing conversion policy and Active/future-start contradiction. Show the next action instead of claiming complete automation.

## 1:45–3:15 — Discover a correction and preview impact

Return to Overview and click Introduce correction. Open the new 18.50 Bellwether candidate. Read its evidence and date. Show that it is pending and that a same-date old version exists.

Preview: 24 affected, 24 outside the jurisdiction; Bellwether below-floor count 11 → 13; +737.28 AST weekly estimate across 16 supported hourly records. Other uncertainty remains unresolved.

Check the saved source, enter a reviewer name, tick the verification box and add a note if needed. Atlas records a source-specific reason in the audit trail. Explain the selected supersession link before approving. This is an explicit test decision, not a live human approval.

## 3:15–4:15 — Follow the impact to a worker

Overview becomes 23 below-floor, 9 compliant, 16 review; 3,886.08 AST supported weekly estimate. Search AST-0025: 17.32 actual versus 18.50 required; 1.18 hourly difference, 47.20 at 40 scheduled hours. Inspect the controlling source and next action.

Click Verify replay now. Explain that the receipt binds the stored input, rule version, preserved HTML and matching engine. Export is available for another reviewer.

## 4:15–5:15 — Preserve the past and recover work

Open Evidence ledger. Show the completed correction job and future jobs waiting for January. Approval and the work item are one database transaction. A failed job is retried without creating duplicate flags.

Click Before correction. Go to Employee decisions and inspect AST-0025 again: the old result is COMPLIANT using 16.63. The historical query does not reopen current flags. Return to current knowledge.

Explain the limit: historical re-evaluation uses stored employee snapshots, not today's wage projected backward. The test suite includes an employee who moves jurisdiction after the original work date.

## 5:15–6:15 — Challenge the implementation

Open Scenario lab: 16 curated cases, 1,000 independent fraction-based arithmetic checks, five actual engine bugs caught. Mention the missing-state fallback and premature future-rate mutants. These are reproducible synthetic checks; there is no claim of a measured LLM accuracy score.

Optionally run `python -m unittest discover -s tests -v` in the terminal. Keep output focused on the final result.

## 6:15–7:00 — Explain AI scope and tradeoffs

“The optional AI integration provides a structured second opinion on public source items. Its output is validated and cannot approve a rule or calculate a wage. I have not run the live model integration, so I am not claiming measured model quality or cost.”

Explain why local SQLite and a single operator are sufficient for this bounded assessment. Name the next two priorities: authenticated reviewer identity and effective-dated employee history. Close on the preserved old receipt and the concrete correction impact.

## Before recording

- Run the full tests, lab and `story` once; keep the output files accessible.
- Read the code paths you will explain; replace this script's wording with your own understanding.
- Use an unused replay filename and the September 24 date.
- Include actual preparation time and disclose development assistance.
- If using live source approvals in the recording, make those decisions yourself after reading the evidence. The simulated demonstration already establishes the workflow without misrepresenting approval.
