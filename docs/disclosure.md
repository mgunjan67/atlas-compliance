# Development disclosure

This document describes development assistance and distinguishes observed source evidence from simulated test data.

## Time spent

Total time reported by the project author: **18 hours**, including review and testing.

## AI assistance

OpenAI Codex assisted with project planning, source and dataset research, identifying ambiguities, designing the workflow, implementing Python/SQLite and the local browser UI, writing and running tests, debugging, and preparing documentation and test artifacts.

Atlas uses deterministic extraction and classification for its rule pipeline. Groq GPT-OSS 120B supplies automatic category suggestions in publication inspection. These are saved separately from the parser's output. Human review controls approval, and deterministic code calculates employee results. The AI sandbox tests generated fictional notices.

Live source approvals are made by the operator. Scripted approvals are labelled as simulations.

## Evidence and simulations

- Both authorities and the sample employee dataset are fictional sample data.
- Baseline replay uses the captured September 24 HTML and the actual 48 sample employee records.
- Replay approvals are explicitly simulated and stored separately from live approvals.
- The 16.63 → 18.50 Bellwether correction is an injected test fixture, not an observed source publication.
- The simulated scenario uses September 24/25 timestamps to establish its sequence; these are separate from actual retrieval times.
- The legacy `demo` command retains a smaller synthetic 14 → 16 case. The complete correction test is `story`, using the included dataset.
- Optional salary annualization and one-day daily-card validity are declared policies, not facts invented from the sources.
- Test fixtures and deliberate engine mutations are synthetic. Passing them is not an end-to-end model benchmark.

