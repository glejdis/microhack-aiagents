# Solution 03 — Observability, Tracing & Evaluation

**[← Back to Challenge 3](../../challenges/challenge-03.md)** · [Home](../../README.md)

Make the agent **observable** and **measurable**: end-to-end OpenTelemetry traces in
Application Insights, an evaluation scorecard over a labelled dataset, a
**Claude-vs-GPT bake-off**, and a **quality gate** you can drop into CI.

## Expected end state

- `configure_azure_monitor(...)` in [`src/tracing_setup.py`](../../src/tracing_setup.py)
  emits spans to Application Insights — you can see agent runs end-to-end.
- [`src/evaluators.py`](../../src/evaluators.py) scores responses (Relevance,
  Coherence, Groundedness) over the labelled dataset and prints a scorecard.
- The bake-off compares Claude vs GPT on the same prompts.
- The gate `python src/evaluators.py --gate 4.0` **exits 3** if groundedness < 4.0.

## Key files

| Path | Role |
|------|------|
| [`src/tracing_setup.py`](../../src/tracing_setup.py) | Wires OpenTelemetry → Application Insights |
| [`src/evaluators.py`](../../src/evaluators.py) | Scores responses, runs the bake-off, and enforces the quality gate |
| [`src/data/evaluation/`](../../src/data/evaluation/) | The labelled eval dataset (+ adversarial prompts) |

## Run it

```bash
python src/tracing_setup.py                 # verify traces flow to App Insights
python src/evaluators.py                     # print the scorecard
python src/evaluators.py --bakeoff           # Claude-vs-GPT comparison
python src/evaluators.py --gate 4.0          # exit code 3 if groundedness < 4.0
```

## Common issues

| Symptom | Cause / fix |
|---------|-------------|
| No traces in App Insights | Confirm `APPLICATIONINSIGHTS_CONNECTION_STRING` is set in `.env` (Challenge 1 sets it). |
| Gate never fails | Try `--gate 5.0` to see it trip; exit code 3 signals a failed gate for CI. |
