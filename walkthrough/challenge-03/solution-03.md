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

## 🛠️ Task-by-task walkthrough

### Task 1 · Enable tracing
[`src/tracing_setup.py`](../../src/tracing_setup.py) sets the content-recording flag **on import** (must happen before the agents SDK loads), then wires the Azure Monitor exporter and Agent Framework instrumentation:
```python
# src/tracing_setup.py — set BEFORE importing the agent framework anywhere
os.environ.setdefault("ENABLE_SENSITIVE_DATA", "true")
os.environ.setdefault("AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED", "true")

def enable_tracing(project=None):
    conn = settings.appinsights_connection_string \
        or (project and project.telemetry.get_application_insights_connection_string())
    configure_azure_monitor(connection_string=conn)   # 1) register exporters
    enable_instrumentation(enable_sensitive_data=True) # 2) emit invoke_agent / chat / execute_tool spans
```
```bash
python src/tracing_setup.py
```
✅ **You should see:**
```text
✓ Tracing enabled → Application Insights (content recording ON).
Run an agent now; open Foundry portal → Tracing to see spans.
```

> 📸 **Screenshot slot:** the "Tracing enabled" confirmation.
>
> <img src="../../images/challenge-03/steps/01-tracing-on.svg" alt="Screenshot slot: tracing enabled" width="75%">

### Task 2 · Generate traffic, inspect spans
Re-run any agent (e.g. the Ch2 demo), then open **Foundry portal → Tracing**. Inspect the **prompt / retrieval / tool** spans and token counts. Spans take **1–2 min** to appear — refresh if empty.

> 📸 **Screenshot slot:** a run's span timeline in **Tracing**, and the **Agent Monitoring** dashboard.
>
> <img src="../../images/challenge-03/steps/02-portal-tracing.svg" alt="Screenshot slot: Foundry Tracing" width="75%">
> <img src="../../images/challenge-03/steps/03-agent-monitoring.svg" alt="Screenshot slot: Agent Monitoring" width="75%">

### Task 3 · Run the evaluation
[`src/evaluators.py`](../../src/evaluators.py) builds a *target* that runs the agent per row, then scores with the Foundry evaluators over `evaluation_dataset.jsonl`:
```python
# src/evaluators.py
def evaluators_dict():
    cfg = judge_model_config()      # an Azure OpenAI GPT deployment as the LLM judge
    return {
        "groundedness": GroundednessEvaluator(model_config=cfg),
        "relevance":    RelevanceEvaluator(model_config=cfg),
        "coherence":    CoherenceEvaluator(model_config=cfg),
        "fluency":      FluencyEvaluator(model_config=cfg),
    }

result = evaluate(data=str(DATASET), target=target, evaluators=evaluators_dict(), ...)
```
```bash
python src/evaluators.py
```
✅ **You should see** (scores 1–5; your numbers differ):
```text
=== Intake & Drafting (claude-sonnet-4-5) ===
  groundedness                             4.6
  relevance                                4.4
  coherence                                4.7
  fluency                                  4.8
  mean latency (s)                         3.2
```

> 📸 **Screenshot slot:** the evaluation scorecard in the terminal.
>
> <img src="../../images/challenge-03/steps/04-scorecard.svg" alt="Screenshot slot: evaluation scorecard" width="75%">

### Task 4 · Run the bake-off
`--bakeoff` runs the **same** target on the GPT deployment and prints Claude vs GPT side by side:
```bash
python src/evaluators.py --bakeoff
```
```text
--- Bake-off (Claude vs GPT) ---
  groundedness                             claude=4.6   gpt=4.5
  relevance                                claude=4.4   gpt=4.3
  mean latency (s)                         claude=3.2   gpt=1.9
```

### Task 5 · Add a quality gate (for CI)
The gate reads mean groundedness and **exits 3** if it's below the threshold — the crux from `main()`:
```python
# src/evaluators.py
if args.gate is not None:
    score = claude.get("groundedness.groundedness") or claude.get("groundedness")
    if float(score) < args.gate:
        print("❌ GATE FAILED — groundedness below threshold. Blocking release.")
        return 3   # non-zero exit fails the CI job
    print("✅ GATE PASSED.")
```
```bash
python src/evaluators.py --gate 4.0     # passes
python src/evaluators.py --gate 5.0     # prove it can fail:
```
```text
Quality gate: groundedness=4.6 threshold=5.0
❌ GATE FAILED — groundedness below threshold. Blocking release.
```

### Task 6 · (Portal) Continuous evaluation
Enable **continuous/online evaluation** on the agent in the portal so production traffic is scored automatically. Portal-only preview today — the `--gate` flag is the code-first equivalent for CI.

> 📸 **Screenshot slot:** the gate failing on a too-strict threshold.
>
> <img src="../../images/challenge-03/steps/05-gate-fail.svg" alt="Screenshot slot: quality gate fails" width="75%">

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
