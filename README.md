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

## Run the tests

From the project folder:

```bash
python -m unittest discover -s tests -q
```

Use `python3` on macOS or Linux if required.
