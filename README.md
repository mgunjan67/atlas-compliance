# Atlas — explainable wage compliance

Atlas checks the two assigned fictional wage authorities, preserves changes, proposes rules for human review, and evaluates the supplied 48 employees. Its central demonstration is a correction that changes today's answer while keeping yesterday's decision reproducible.

**Time spent:** approximately 18 hours, confirmed by the candidate on 28 September 2026, including personal reviewing and testing time. The required 5–10 minute recording is still to be supplied. [AI assistance disclosure](docs/disclosure.md)

## Start here

Python 3.10+; standard library only. From this folder:

```powershell
python -m atlas serve
```

Open **http://127.0.0.1:8787**:

1. Click **Check sites** in the shared top bar and wait for completion. Open **Rates & details** for both rates, saved evidence and check history. A fresh installation starts without live approvals.
2. In **Rule review**, inspect both saved sources and review the combined daily-rate update. Resolve any separate coverage clarification after checking its evidence; approving rates does not decide missing coverage facts. The **Publication register** shows upcoming rates, interpretations and other information, with historical records in their own filter.
3. In **Employee decisions**, inspect results and receipts or export JSON. **Results from** opens saved approved inspections. If a coverage review resolves a previously blocked inspection, **Resolved results** is saved alongside the original **At approval** snapshot.
4. In **Scenario lab**, enter hypothetical federal/state rates and run a dummy test. It tests calculations and saves separately; it does not fetch or approve publications.

**Start 15-min checks** in the shared top bar is optional and stays off until selected. The bar stays available on every tab, including Scenario lab, and always controls live website checks. For a repeatable offline demonstration of the complete change/approval loop, use the CLI story:

```powershell
python -m atlas story
python -m atlas verify output/reviewer-story/original-receipt.json
```

## What the example proves

| Supplied 48 employees | Before correction | After simulated review |
|---|---:|---:|
| Below minimum | 21 | 23 |
| Meets minimum | 11 | 9 |
| Requires review | 16 | 16 |
| Supported weekly estimate, AST | 3,148.80 | 3,886.08 |

The CLI story creates a fresh isolated simulation database and writes its evidence to `output/reviewer-story`. The synthetic Bellwether correction is **16.63 → 18.50**, effective September 24. It changes 16 supported hourly results among 24 in-scope workers. AST-0025 earns 17.32/hour: its new estimated gap is **1.18/hour, 47.20/week**. Scheduled hours make this an estimate, not payroll liability. The old receipt still verifies. [Saved change story](output/reviewer-story/story-report.json)

## Decision boundaries

- Bellwether workers use the higher applicable approved federal/state floor, including when federal overtakes state. Equality passes; Decimal comparison happens before cent rounding.
- Future notices wait for their date and approval. Proposals/news do not become rules. Unresolved interpretation, coverage, contradictory content, unknown layouts and current source failures prevent unsupported passes.
- Salary proxies aid investigation; they are not actual hourly wages. Twelve records need a conversion policy and four also have future-start conflicts. CLI `evaluate --annualize-salary` is a read-only scenario, exported separately to `output/salary-what-if.json`; it cannot update live flags or jobs.
- Daily cards are valid for one day by explicit conservative policy. Missing publication dates stay unknown. [Short research memo](docs/research.md)

## Implementation choice

The submitted workflow uses deterministic extraction and classification for these two structured sources. Ambiguous or unsupported publications require human review. AI is optional in the assignment; no runtime model integration is included.

## Verify and hand off

```powershell
python -m unittest discover -s tests -q
python -m atlas lab
python -m atlas story
python -m atlas verify output/reviewer-story/original-receipt.json
python -m scripts.package_submission
```

`story` creates a fresh simulation database. The packager checks a fresh ZIP extraction and excludes local databases, keys and rehearsal approvals. Start with the [recording guide](docs/walkthrough.md); [validation](docs/validation.md) records what was tested. [Architecture](docs/architecture.md) and [requirement map](PLAN.md) provide deeper detail.

This is a loopback-only assessment prototype. It does not provide authenticated legal review, full employee history, actual-hours payroll integration or general legal-language understanding. Review records are immutable; corrections supersede earlier rates. Local hash chains establish consistency, not external notarization. Old receipts require their matching engine version. No repository, recording or interview submission has been published automatically.

Live daily-rate review uses one combined federal/state inspection and one approval action. Results from lists saved combined result sets, including explicitly labelled earlier separately-approved history. Each jurisdiction still retains its own versioned rule and source evidence.
