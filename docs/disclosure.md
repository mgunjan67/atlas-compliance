# Development disclosure

This document describes development assistance and distinguishes observed source evidence from simulated test data.

## AI assistance

OpenAI Codex assisted with reading the take-home brief, source and dataset research, identifying ambiguities, designing the workflow, implementing Python/SQLite and the local browser UI, writing and running tests, debugging, and preparing documentation and demonstration materials.

The submitted workflow uses deterministic extraction and classification for these two structured sources. Ambiguous or unsupported publications require human review. AI is optional in the assignment; no runtime model integration is included.

The assistant has not represented itself as a human reviewer or approved live source-backed rules. Live review remains an operator responsibility.

## Evidence and simulations

- Both authorities and the supplied employee dataset are fictional assessment material.
- Baseline replay uses the captured September 24 HTML and the actual 48 supplied employee records.
- Replay approvals are explicitly simulated and stored separately from live approvals.
- The 16.63 → 18.50 Bellwether correction is an injected test fixture, not an observed source publication.
- Logical September 24/25 timestamps establish the scenario sequence. They are not claims that the assistant observed a future publication.
- The legacy `demo` command retains a smaller synthetic 14 → 16 case. The submission's main evidence is `story` using the supplied dataset.
- Optional salary annualization and one-day daily-card validity are declared policies, not facts invented from the sources.
- Test fixtures and deliberate engine mutations are synthetic. Passing them is not an end-to-end model benchmark.

## Operator responsibilities

- Understand the source assumptions, implementation and validation limits.
- Make live review decisions using the preserved evidence and a justified reason.
- Clearly label simulated changes and approvals when demonstrating the system.
