# Atlas — wage compliance dashboard

Atlas checks federal and state wage publications, saves source evidence, and compares employee wages with approved rules. It keeps previous results available and supports separate dummy tests with custom rates.

The included websites, currency and employee records are fictional sample data.

## Requirements

- Python 3.10 or later
- Git
- Internet access to check the source websites
- Access to this GitHub repository if it is private

Atlas uses the Python standard library. No extra packages or API keys are required.

## Clone the project

```bash
git clone https://github.com/mgunjan67/atlas-compliance.git
cd atlas-compliance
```

## Run locally

On Windows:

```powershell
python -m atlas serve
```

On macOS or Linux:

```bash
python3 -m atlas serve
```

Open **http://127.0.0.1:8787** in your browser. Keep the terminal open while using Atlas. Press **Ctrl+C** in the terminal to stop the server.

If port 8787 is already in use, run `python -m atlas serve --port 8788` and open **http://127.0.0.1:8788**. Use `python3` instead of `python` where needed.

## Employee CSV

The [employee dataset](data/employees.csv) is included in the repository and contains 48 sample records. Atlas loads it automatically; no separate download or browser upload is needed.

To use another CSV with the same column names and supported values, provide its path when starting the server:

```bash
python -m atlas serve --employees "path/to/employees.csv"
```

## Use the dashboard

1. Click **Check sites** in the top bar. Open **Rates & details** to see the captured rates and saved evidence.
2. Open **Rule review** to inspect and approve a federal/state update together. Other publications show their type, effect and review status.
3. View the dashboard summary or open **Employee decisions** for individual results, evidence receipts and JSON exports. Use **Results from** to view earlier approved results.
4. Use **Scenario lab** to enter hypothetical rates and save a dummy test separately from live results.

A new installation has no live approvals. Check the sources and review their evidence before expecting approved employee results. Annual-salary records and incomplete or conflicting employee data may still require review.

For Bellwether employees, Atlas applies the higher applicable approved federal or state rate. Future rules require approval and their effective date before they apply.

**Start 15-min checks** enables automatic checks while the server runs. It is off by default. Live evaluations use today's UTC date.

## Local storage

Atlas creates its SQLite database at `data/atlas-v2.sqlite3`. Checks and exports are saved under `output/`, including dated archives in `output/live-archive/`. Restarting the server keeps the local data. Local databases and personal review history are not included when cloning the repository.

## Architecture and data flow

Atlas is a local Python application with a browser interface and a SQLite database. The calculation engine is separate from fetching and review, so its decisions can be tested and reproduced without accessing the websites.

| Component | Responsibility |
|---|---|
| Source monitor and extractor | Fetch both websites, preserve HTML and retrieval history, compare changes, classify publications and extract proposed rules |
| Review and rule registry | Store evidence, effective dates and immutable review decisions; approve daily federal/state updates together |
| Evaluation engine | Read the employee CSV, select applicable approved rules and calculate decisions with decimal arithmetic |
| Workflow and evidence storage | Re-evaluate affected employees, preserve earlier results, retry failed jobs and produce JSON/CSV exports and decision receipts |
| Browser dashboard and CLI | Check sources, inspect evidence, review updates, explore employee results and run separate simulations |

The operating sequence is:

1. Fetch both sources and save their content, timestamps and checksums.
2. Compare each retrieval with the previous one. Classify rate notices, future rules, interpretations, proposals and unrelated information.
3. Record new candidates as `REVIEW_REQUIRED`, with their discovery timestamps. A person inspects the evidence and approves or rejects numerical rules; supporting interpretations may be acknowledged separately.
4. Store approved versions with their effective dates. New approvals and effective dates trigger re-evaluation work.
5. Select the applicable approved federal/state rules for each employee's work location and evaluation date. Return `COMPLIANT`, `NON_COMPLIANT`, `INSUFFICIENT_DATA` or `REVIEW_REQUIRED`.
6. Save results, review history and source evidence. Previous approved results remain visible with their original date while new changes await review.

Extraction, classification and final calculations are deterministic. No runtime AI service is required. See the [architecture document](docs/architecture.md) for diagrams and implementation details.

## Assumptions

- **Jurisdiction:** use the employee's work location. Bellwether workers receive the higher applicable approved federal/state minimum.
- **Dates:** a rule must be approved and effective before it controls a result. Daily rate cards have one-day validity as an explicit conservative policy; yesterday's amount is not assumed to apply today.
- **Pay and coverage:** annual salary is not treated as an actual hourly wage without an approved conversion method. Optional salary estimates are for investigation only. The coverage correction requires an explicit decision because employer headcount is absent from the employee file.
- **Money:** compare exact decimal amounts before rounding; equality meets the minimum. Report monetary amounts to two decimals using half-up rounding. Hourly shortfall is `max(0, floor − wage)`; the weekly estimate multiplies it by scheduled weekly hours when available.
- **Uncertainty:** missing required inputs or rules, conflicting information and unresolved relevant source changes cannot silently produce a compliant result. Each unresolved result explains its reason and next action.

## Known limitations

- The source adapters support the two specified websites. Unfamiliar layouts or ambiguous language require investigation; this is not a general-purpose regulatory parser.
- The server is intended for local, single-operator use. It has no production user authentication or reviewer identity verification.
- Scheduled hours support an estimated weekly gap, not a final payroll liability. Salary-conversion and employer-coverage questions need additional authority or information.
- Historical reconstruction covers employee inputs and source versions already captured. It cannot reconstruct unobserved changes or missed daily rates.
- Receipt verification depends on the matching engine/parser versions. Local hashes detect inconsistency but are not independent signatures or external notarization.

The [research memo](docs/research.md) explains how sources are trusted, why the current pipeline uses explicit parsing instead of AI, and what would need to change before processing real payroll data.

## Run the tests

From the project folder:

```bash
python -m unittest discover -s tests -q
```

Use `python3` on macOS or Linux if required.

To test a complete change workflow without waiting for a website update:

```bash
python -m atlas story
python -m atlas verify output/reviewer-story/original-receipt.json
```

The story uses saved source pages and the included employees in an isolated simulation database. It injects a Bellwether correction, records a simulated review, re-evaluates employees and verifies the original receipt. It writes to `output/reviewer-story/` and does not approve live sources.

## Documentation and example outputs

| Document | Contents |
|---|---|
| [Project brief](docs/reviewer-brief.md) | Summary, key decisions and tradeoffs |
| [Architecture](docs/architecture.md) | Components, data flow and storage boundaries |
| [Research memo](docs/research.md) | Interpretation of both sources, precedence, effective dates and edge cases |
| [Employee data analysis](docs/employee-data-analysis.md) | Dataset findings and salary/data exceptions |
| [Operator guide](docs/operator-review.md) | Evidence inspection, review decisions and result history |
| [Validation report](docs/validation.md) | Automated checks, observed results and testing limits |
| [Development disclosure](docs/disclosure.md) | Development assistance and simulation provenance |
| [Implementation map](PLAN.md) | Capabilities mapped to implementation evidence |

The repository includes the [employee CSV](data/employees.csv), [captured source pages](data/research/), [a preserved pre-review live check](output/live-archive/2026-09-25/), and [simulated before/after results, audit events and receipts](output/reviewer-story/). Simulated outputs are labelled; they are not evidence of live approvals. The [scenario report](output/lab-report.json) records the automated lab checks.
