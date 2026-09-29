# Atlas architecture: assignment blueprint and implemented prototype

These diagrams separate **the system requested in the assessment** from **the local Atlas implementation**. Arrows show the flow of evidence and decisions, not a claim that every component needs its own service.

## 1. Blueprint requested by the assignment

```mermaid
flowchart TB
  F["Asteria federal site"] --> M["Monitor both sources"]
  B["Bellwether state site"] --> M
  M --> S["Preserve source snapshots<br/>Detect meaningful changes and failures"]
  S --> X["Classify content and extract proposed rule<br/>Amount, scope, dates, source, evidence"]
  AI["Optional AI assistance"] -. "Advisory only" .-> X
  X --> P["Proposed rule<br/>Visible uncertainty and status"]
  P --> H{"Human reviews evidence"}
  H -->|Reject| R["Retain rejected proposal and reason"]
  H -->|Approve| V["Versioned, effective-dated rule registry<br/>Corrections preserve history"]
  V -->|"New approval or effective date"| A["Select affected employees"]
  E["Employee wages, work location and hours"] --> A
  A --> D["Deterministic rule precedence and wage calculation"]
  V --> D
  D --> O["Per-employee result<br/>Compliant / non-compliant / insufficient data / review required"]
  O --> U["Underpayment flags and export"]
  S --> T["Evidence and audit trail"]
  H --> T
  O --> T
  T --> Q["Another operator can reproduce the decision"]
```

The key gate is **human approval before a proposed publication becomes a controlling rule**. A page edit, future notice, proposal or ambiguous statement must not silently change an employee's compliance result. Bellwether employees may be subject to both federal and state rules; the higher approved applicable floor controls.

## 2. Architecture actually built in Atlas

```mermaid
flowchart TB
  F["Two allowlisted fictional sites"] --> W["atlas.monitor<br/>HTTP fetch; foreground watch command"]
  W --> DB1[("SQLite live database<br/>fetch logs + raw snapshots + semantic diffs")]
  W --> X["atlas.extract<br/>Visible-page parsing; relevance and field evidence"]
  X --> C[("Candidate records<br/>Pending, approved or rejected")]
  UI["Local web UI / CLI<br/>atlas.web; atlas.__main__"] --> H["Impact preview + human review"]
  C --> H
  H -->|"Approved rule and job committed together"| V[("Effective-dated reviews<br/>and re-evaluation jobs in SQLite")]
  V --> J["atlas.workflow<br/>Affected-worker selection and retryable jobs"]
  CSV["48 supplied employees<br/>data/employees.csv"] --> J
  J --> D["atlas.engine<br/>Approved-rule selection; higher floor; Decimal arithmetic"]
  V --> D
  D --> O[("Stored evaluations + deduplicated flag states")]
  O --> OUT["JSON/CSV results; local web views"]
  O --> REC["atlas.receipt<br/>Portable verification bundle"]
  DB1 --> LED[("Local audit events and hash chain")]
  H --> LED
  O --> LED
  REP["Saved 24 Sep pages + synthetic correction"] --> DEMO[("Separate replay SQLite database")]
  DEMO --> CLI["CLI correction story<br/>Explicitly simulated approvals"]
  DB1 --> UI
```

**Live and test boundaries:** The web console captures the designated pages and leaves new rates pending until a person approves them. Scenario lab saves custom-rate calculation tests separately. The CLI correction story uses an isolated database, explicitly simulated approvals and a synthetic correction to test the complete change loop. It is not a second browser workspace.

**Implementation boundary:** `watch` is an optional foreground 15-minute process; the browser console can start the same interval while its server is open. Both schedules are stopped by default, and the earlier Codex freshness task was stopped at the candidate's request. Each completed watcher cycle archives all 48 results, including pending decisions. SQLite provides the local version, job and audit stores; there is no production identity system or full payroll integration. The wage calculation and final state always come from `atlas.engine`, not an LLM.
