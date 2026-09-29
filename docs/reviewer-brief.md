# Atlas project overview

**Product question:** When a wage authority corrects yesterday's rule, can an operator see the affected employees, make a justified decision, and still explain the original result?

Atlas implements that complete loop for the two fictional authorities and the included 48 employees. It treats approval, uncertainty and historical evidence as product behavior that a reviewer can inspect.

## Three things to try

1. **Inspect a live update.** In Overview, check both websites. In Rule review, inspect the saved sources, both rates and the combined employee impact before making your own approval decision. If there is no new publication, the app reports no change.
2. **Challenge a historical answer offline.** Run `python -m atlas story`, then `python -m atlas verify output/reviewer-story/original-receipt.json`. The isolated simulated story records the detected 16.63 → 18.50 correction, simulated review and re-evaluation: 24 in-scope workers, two newly below the floor. Its original COMPLIANT result for AST-0025 still reproduces. In the live UI, Employee decisions → Results from opens saved inspections; Scenario lab is only for manual hypothetical rates.
3. **Challenge the code.** Run `python -m atlas lab`. The tests must catch real injected mistakes: choosing the lower floor, failing equality, activating a future rule early, ignoring expiry and silently falling back when a state rule is missing.

## Decisions that matter

| Observation | Product decision | Cost accepted |
|---|---|---|
| 16 employees have annual salary; no source conversion rule | Preserve review states; optional estimate is explicit | Lower automatic coverage instead of invented certainty |
| A federal correction changes a coverage threshold without changing wages | Route to review; document reliance on upstream Covered field | Operator effort even when amount is unchanged |
| Publication, effective, discovery and approval times differ | Store each separately; query rule knowledge at a timestamp | More temporal state than a simple current-rate table |
| A review can succeed while downstream work crashes | Atomically queue a durable re-evaluation job; retry idempotently | A small queue and explicit job lifecycle |
| Workers can move after a historical work date | Backfill the stored historical employee input and location | Cannot reconstruct dates never observed |

## What the result means

The baseline has 21 below-floor, 11 compliant and 16 review cases. The synthetic correction produces 23, 9 and 16 respectively. The weekly total rises from 3,148.80 to 3,886.08 AST, supported by 32 hourly records. These are scheduled-hours estimates, not final liabilities. The packaged live example is a pre-review state; local reviewer actions are not shipped.

There are 118 automated tests plus the executable scenario lab. The oracle independently checks arithmetic using exact fractions. Automatic AI suggestions are kept separate from rule approval and calculation. The current classifier matched 11 of 12 fictional cases in one recorded run; it still misread conflicting dates. These bounded checks do not establish general model accuracy or production legal correctness. See [validation](validation.md) and [AI review](ai-review.md).

## Why this scope

Atlas focuses on preserving explainable decisions through corrections, incomplete data and failures. The console makes that workflow easy to inspect; the CLI, exported results and receipts make the claims independently checkable.

Further work includes broader independently labelled publication cases and domain-owner agreement on salary/coverage policy. A broader autonomous agent would not solve the missing salary and coverage authority.

Read [research](research.md) for source evidence, [README](../README.md) for setup, and [validation](validation.md) for verification results.
