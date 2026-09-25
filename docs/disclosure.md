# Development and submission disclosure

Candidate: verify this disclosure, describe any additional work in your own words, and retain it with the submission.

## AI assistance

OpenAI Codex assisted with reading the take-home brief, source and dataset research, identifying ambiguities, designing the workflow, implementing Python/SQLite and the local browser UI, writing and running tests, debugging, and preparing documentation and demonstration materials.

The compliance engine and primary source extraction are deterministic. An optional OpenAI Responses API integration produces a structured second opinion on extracted public source items. It has not been run against a live model. Tests validate its request and output boundary using fixtures; no live accuracy, cost or latency result is claimed. No employee inputs are included in that optional API request.

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

The candidate reports approximately **18 hours** spent so far, including reading, implementation review and testing with Codex. This is candidate-reported time, not a machine-measured duration. Add recording and any further preparation time before final submission if the total changes.

## Submission actions still owned by the candidate

- Read and understand the source assumptions, implementation and validation limits.
- Personalize the explanation and update the 18-hour estimate if further work changes it.
- Make any live operator review decisions personally, with source evidence and reasons.
- Record a 5–10 minute walkthrough or present the live demo.
- Publish/share the intended repository and provide its link through the employer's requested channel.

No external repository, recording, email or interview submission was published by this workflow. The provided ZIP is a local handoff artifact.
