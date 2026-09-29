# AI review

The parser knows the two websites' supported structures. AI provides a second reading of saved publication text when a reviewer opens an inspection. It runs automatically in the background, not when the operator clicks Inspect.

## In the application

Rule review shows the parser category, the AI category and supporting source text. Disagreements are labelled. A numerical rule still needs the existing human approval; daily federal and state updates still share one inspection. Neither agreement nor disagreement changes the rule's status automatically.

AI sandbox is separate. Choose one of the twelve fictional notices and click **Get AI suggestion**. The expected answer is shown only in the comparison, never sent to the model.

## Operation

- Set `GROQ_API_KEY` in the server environment, or the Windows user environment. Atlas does not load a .env file. Keep credentials out of source control.
- The model is Groq's `openai/gpt-oss-120b`, with low reasoning and structured JSON output. No paid-plan upgrade is performed by Atlas. Provider quotas and availability still apply.
- Set `ATLAS_AI_DISABLED=1` to stop model requests. Ordinary source review and calculations remain available.
- The background worker discovers committed, non-simulated publication candidates every five seconds and processes one request at a time. First startup also processes existing publications.
- Requests share an eight-second minimum spacing with sandbox requests in the same server process. Each HTTP request has a 25-second socket timeout. Pending work survives restarts.
- Transient failures retry after 60 and 120 seconds, up to three attempts. Authentication errors and oversized input stop immediately. Exhausted suggestions show unavailable; the source can still be reviewed. No unlimited retry loop runs.
- Results live beside the main database in `<database-name>-ai.sqlite3`. The main database is opened read-only by this worker. Candidate version, snapshot reference, source URL, evidence hash, model, prompt version, timestamps and validated output are retained.

Only saved publication text is sent to Groq. Employee data, reviewer identities, approval notes and credentials are not part of the prompt. Redirects are refused. Input is capped at 6,000 characters rather than silently truncated; responses are size-limited. Instruction-like source content is quarantined before automatic inference.

The model selects source-segment IDs; Atlas builds quotations directly from those segments. Valid references prove that the text exists, not that the interpretation is correct. Model output is escaped in the UI and never executed.

## Evidence and limits

The initial extraction experiment matched all 17 classifications but only 12 complete field-and-quotation checks. The separate 12-case classification experiment matched 10 categories. It helped with five unfamiliar wording/layout examples, but misread conflicting dates and a withdrawn order. These are selected fictional tests, not a general accuracy estimate.

The live classifier has its own versioned prompt, including a daily-rate category. A September 29 run of this prompt matched **11 of 12** fictional cases: conflicting dates were still incorrectly labelled a final rate. The withdrawn-order case matched this time. This variation is another reason to keep suggestions advisory. The [saved run](ai-evaluation.json) records every answer and the prompt-version hash. Earlier experiment scores should not be treated as an accuracy guarantee for this implementation. Run the current prompt with:

```bash
python scripts/evaluate_ai.py
```

This makes real API calls on fictional fixtures and writes an isolated JSON report under output. Unit and integration tests use fake providers and do not require credits.

The worker operates on publications already captured as candidates. If the entire website layout fails extraction, AI does not automatically discover a replacement structure or rescue ingestion. A single local server owns the queue; multi-process workers and production access controls are not implemented. Human approval does not eliminate model risk: reviewers must check the original evidence, especially when the model and parser disagree.
