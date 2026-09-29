# Assessment plan and completion map

Objective: deliver a reviewable minimum-wage operating slice for the two fictional authorities and included employee dataset.

## Work completed

1. Preserve source HTML, hashes and retrieval metadata; inspect the supplied 48 employee records. Separate observed facts from policy choices.
2. Implement bounded source retrieval, meaningful diffs, visible-content extraction and versioned review candidates. Do not inspect a hidden publication schedule.
3. Require review; select dated approved federal/state rules deterministically; return all four decision states with evidence and next action.
4. Add impact preview, transactionally queued re-evaluation, explicit corrections and historical-knowledge queries. Replay stored employee inputs for historical dates.
5. Export portable receipts and verify source binding and calculations. Add a local audit hash chain with an honest trust boundary.
6. Build the reviewer console and a correction story using all 48 supplied employees. Keep simulated and live review data separate.
7. Verify engine and workflow tests, an independent arithmetic oracle, deliberate code mutations, and the actual browser review flow. Prepare research, handoff and demo documentation.

## Requirement-to-evidence map

| Assessment requirement | Concrete evidence |
|---|---|
| Runnable code and setup | README.md; Python standard-library package |
| Research and source interpretation | docs/research.md; data/research/*.html and manifests |
| Monitoring and diffs | atlas/monitor.py; persisted snapshots/fetch logs |
| Relevance and dated rule extraction | atlas/extract.py; candidate quote spans and source IDs |
| Human approval and rule history | CLI/UI; immutable review events; explicit supersession |
| Four outcomes and overlap precedence | atlas/engine.py; tests/test_atlas.py |
| Employee outputs and traceability | output/live-results.*; output/reviewer-story/*.json and *.csv |
| Change-driven employee re-evaluation | atlas/workflow.py; story report and audit export |
| Reproducibility and historical explanation | before/after/as-known outputs; two verifiable receipts |
| Tests and failure cases | 103 unit/integration tests; lab report; docs/validation.md |
| Implementation choice and development disclosure | README.md; docs/disclosure.md |
| Five-to-ten-minute walkthrough | docs/walkthrough.md; candidate records or presents |

## Demonstration preparation

Rehearse the live review path and the isolated CLI correction story, inspect source evidence, and understand the salary, coverage and date assumptions. The walkthrough guide supports a 5–10 minute live demonstration or recording. Clearly distinguish saved simulations from live source checks and human approvals.
