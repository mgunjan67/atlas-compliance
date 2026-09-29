# Seven-minute reviewer walkthrough

This guide supports a 5–10 minute live demonstration or recording. Use the live workspace and Scenario lab. Dummy tests demonstrate calculations, not live fetching or human approval.

## 0:00–1:00 — Explain the task and current results

Open Overview. Explain the two source websites, the 48 supplied employees and the higher applicable federal/state minimum for Bellwether workers. Show the result date, employee counts and location breakdown. Open an employee from Wages to investigate to explain a confirmed hourly gap. The shared top bar controls live checks from every tab; open Rates & details for the rates and full check timestamps.

## 1:00–2:30 — Check sources and inspect evidence

Click Check sites in the top bar. Wait for the completed result, then expand Rates & details. Open saved source evidence and compare the amount, date and scope with the extracted facts. If a changed daily pair needs review, inspect both rates together and make your own approval decision only after checking the evidence. If nothing changes, say so; do not present a dummy test as a live source change.

## 2:30–3:30 — Explain an employee result

Open Employee decisions. Inspect an hourly worker: wage, controlling minimum, decision and required shortfall fields. Show the saved evidence and verify the receipt. Explain that annual-salary records need a comparison policy and that future-start conflicts remain review cases.

## 3:30–4:30 — Show preserved approved results

Choose an earlier inspection using Results from. Show that both federal and state rates belong to one saved result set. Expand Approval & source details. Return to Latest results. Older separately approved records are labelled honestly rather than presented as a combined approval.

## 4:30–5:45 — Test a change safely

Open Scenario lab. Keep the test date explicit. Enter federal 19 and state 16 to demonstrate federal taking precedence for Bellwether. Give the test a clear name and click Run & save dummy test. Inspect employee floors and the comparison with the approved baseline. Reopen it from Saved dummy tests. Explain that it uses the supplied employee inputs and synthetic rates, leaves live approvals unchanged, and does not reproduce a historical employee snapshot.

## 5:45–6:30 — Show test evidence

Expand Automated checks: 16 curated scenarios, independent arithmetic checks and deliberate engine bugs caught. The manual-rate form only tests calculations. To demonstrate a repeatable source change, run `python -m atlas story` in the terminal and open `output/reviewer-story/story-report.json`: show the simulated detected correction, approval, before/after counts and AST-0025. Then run `python -m atlas verify output/reviewer-story/original-receipt.json` to show that the old decision still reproduces. Label this sequence simulated; it does not approve live sources.

## 6:30–7:00 — Explain limits and tradeoffs

Extraction and classification are deterministic for the two structured sources. Unknown or ambiguous material needs human review. No runtime model integration is included. Explain the local single-operator scope, salary-policy uncertainty and development assistance.

## Before presenting or recording

Run the tests and story, inspect the artifacts you plan to show, and use your own words. Do not claim a dummy run checks websites or approves published rules. Verify any real source before approving it yourself.
