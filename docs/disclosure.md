# Development and submission disclosure

Candidate: verify this disclosure, describe any additional work in your own words, and retain it with the submission.

## AI assistance

OpenAI Codex assisted with reading the take-home brief, source and dataset research, identifying ambiguities, designing the workflow, implementing Python/SQLite and the local browser UI, writing and running tests, debugging, and preparing documentation and demonstration materials.

The submitted workflow uses deterministic extraction and classification for these two structured sources. Ambiguous or unsupported publications require human review. AI is optional in the assignment; no runtime model integration is included.

The assistant has not represented itself as a human reviewer or approved live source-backed rules. The candidate must understand and be able to defend the implementation and assumptions.

## Evidence and simulations

- Both authorities and the supplied employee dataset are fictional assessment material.
- Baseline replay uses the captured September 24 HTML and the actual 48 supplied employee records.
- Replay approvals are explicitly simulated and stored separately from live approvals.
- The 16.63 → 18.50 Bellwether correction is an injected test fixture, not an observed source publication.
- Logical September 24/25 timestamps establish the scenario sequence. They are not claims that the assistant observed a future publication.
- The legacy `demo` command retains a smaller synthetic 14 → 16 case. The submission's main evidence is `story` using the supplied dataset.
- Optional salary annualization and one-day daily-card validity are declared policies, not facts invented from the sources.
- Test fixtures and deliberate engine mutations are synthetic. Passing them is not an end-to-end model benchmark.

## Time

The candidate confirmed approximately **18 hours** on 28 September 2026, including reading, implementation review and testing with Codex. This is candidate-reported personal time, not a machine-measured duration. The recording is still pending; update the total if recording or further preparation changes it.

## Submission actions still owned by the candidate

- Read and understand the source assumptions, implementation and validation limits.
- Personalize the explanation and update the 18-hour estimate if further work changes it.
- Make any live operator review decisions personally, with source evidence and reasons.
- Record a 5–10 minute walkthrough or present the live demo.
- Publish/share the intended repository and provide its link through the employer's requested channel.

No external repository, recording, email or interview submission was published by this workflow. The provided ZIP is a local handoff artifact.
