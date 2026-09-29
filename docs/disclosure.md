# Development disclosure

This document describes development assistance and distinguishes observed source evidence from simulated test data.

## Time spent

Total time reported by the project author: **18 hours**, including review and testing.

## AI assistance

OpenAI Codex assisted with project planning, source and dataset research, identifying ambiguities, designing the workflow, implementing Python/SQLite and the local browser UI, writing and running tests, debugging, and preparing documentation and test artifacts.

Atlas uses deterministic extraction and classification for its rule pipeline. Groq GPT-OSS 120B now supplies separate, automatic classification suggestions in publication inspection. Suggestions do not alter the parser's output or activate rules. Human review and deterministic calculations remain authoritative. The AI sandbox uses generated fictional notices; its outputs are suggestions, not approvals.

The assistant has not represented itself as a human reviewer or approved live source-backed rules. Live review remains an operator responsibility.

## Evidence and simulations

- Both authorities and the sample employee dataset are fictional sample data.
- Baseline replay uses the captured September 24 HTML and the actual 48 sample employee records.
- Replay approvals are explicitly simulated and stored separately from live approvals.
- The 16.63 → 18.50 Bellwether correction is an injected test fixture, not an observed source publication.
- Logical September 24/25 timestamps establish the scenario sequence. They are not claims that the assistant observed a future publication.
- The legacy `demo` command retains a smaller synthetic 14 → 16 case. The complete correction test is `story`, using the included dataset.
- Optional salary annualization and one-day daily-card validity are declared policies, not facts invented from the sources.
- Test fixtures and deliberate engine mutations are synthetic. Passing them is not an end-to-end model benchmark.

## Operator responsibilities

- Understand the source assumptions, implementation and validation limits.
- Make live review decisions using the preserved evidence and a justified reason.
- Clearly label simulated changes and approvals in test artifacts.
