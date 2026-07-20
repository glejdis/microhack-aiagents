# Challenge 2 · Observability, Tracing & Evaluation

> **Duration:** 60 min · **Prerequisites:** Challenge 1 complete (Intake & Drafting agent runs).

> 🧩 **How to use this challenge:** the code in this folder is a **complete, working reference
> implementation** — you're not building it from a blank file. **Run it, read it, and understand *why*
> it works**, then take it further with **🚀 Go Further**. Stuck? The code *is* the answer key.

## 🎯 Objective

Make the agent **observable** and **measurable**: end-to-end traces in Application Insights, an
evaluation scorecard over a labelled dataset, a **Claude-vs-GPT bake-off**, and a **quality gate**
that blocks a bad build.

## 🧭 Context

- **Tracing** uses OpenTelemetry. The Agents SDK emits spans for prompts, retrieval and tool calls;
  `configure_azure_monitor` ships them to **Application Insights**, and the Foundry portal renders
  them in **Tracing** + the **Agent Monitoring Dashboard**. Because both agents live in one project,
  you see **Claude and GPT traces in one pane of glass**.
- **Evaluation** uses `azure-ai-evaluation`. Evaluators (groundedness, relevance, coherence,
  fluency) are **LLM-judged** by an Azure OpenAI deployment. A *target* callable generates the
  agent's response for each dataset row so evaluation is end-to-end.
- **Bake-off**: run the same agent + same scorecard on **Claude Sonnet 4.5** vs **GPT** and compare
  quality against latency — the concrete payoff of a model-agnostic platform.

## 🧰 Services & models in this challenge

Observability turns the agent from a black box into something you can **see** and **measure**. These are
the services that make that possible.

### OpenTelemetry + Azure Monitor OpenTelemetry Distro

**What it is:** the **open standard** for traces, metrics and logs. The Agents SDK emits OpenTelemetry
**spans** for every prompt, retrieval and tool call; `configure_azure_monitor(...)` from the Azure Monitor
distro exports them to Azure with one call.

- **Vendor-neutral** instrumentation — no bespoke logging code.
- Captures the **causal chain** of a run (prompt → retrieval → tool → response).
- Enable prompt/response capture with `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true` **before**
  importing the SDK.

**Why here:** it's how a multi-step agent run becomes an inspectable trace instead of a wall of print
statements. → [Enable OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable)

### Application Insights + Log Analytics

**What it is:** the **Azure Monitor** application-performance service (backed by a Log Analytics
workspace) that **stores and queries** the telemetry the agent emits.

- End-to-end **transaction/trace** views, latency and token metrics, failures.
- **KQL** queries over spans for custom analysis and dashboards.
- Provisioned in **Challenge 0**; the connection string lives in `APPLICATIONINSIGHTS_CONNECTION_STRING`.

**Why here:** it's the durable sink your traces land in — the data source behind the portal's Tracing and
monitoring views. → [Application Insights overview](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)

### Foundry Observability (portal Tracing + Agent Monitoring)

**What it is:** the **agent-aware UI** in the Foundry portal that renders those traces as **Tracing** and
an **Agent Monitoring Dashboard** — no query-writing required.

- Per-run **span timelines** with retrieval hits and tool arguments.
- Because both agents live in one project, you see **Claude and GPT traces in one pane of glass**.
- Home for **continuous/online evaluation** on live traffic.

**Why here:** it's the fastest way to *look at* what the agent actually did on a given run.
→ [Observability in Foundry](https://learn.microsoft.com/en-us/azure/foundry/concepts/observability)

### Azure AI Evaluation SDK (`azure-ai-evaluation`)

**What it is:** the library that **scores** agent responses. Evaluators (**groundedness, relevance,
coherence, fluency**) are **LLM-judged** by an Azure OpenAI deployment; a *target* callable generates the
agent's answer for each dataset row so evaluation is end-to-end.

- Ready-made **quality** and **safety** evaluators (safety ones take `azure_ai_project` + a credential).
- A **quality gate** (`--gate 4.0`) returns a non-zero exit code — drop-in for CI.
- Same scorecard across models powers the **Claude-vs-GPT bake-off**.

**Why here:** tracing shows *what happened*; evaluation shows *how good it was* — and lets a bad build
**fail the gate** before it ships. → [Evaluation & observability](https://learn.microsoft.com/en-us/azure/foundry/concepts/observability)

## ✅ Tasks

1. **Enable tracing** and confirm the exporter wires up:
   ```bash
   python challenge-2/tracing_setup.py
   ```
   > `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true` must be set **before** the agents SDK is
   > imported — `tracing_setup` does this on import, so import it first in any entry point.

2. **Generate traffic**, then open **Foundry portal → Tracing**. Run a few prompts (e.g. re-run the
   Ch1 demo) and inspect the **prompt / retrieval / tool** spans and the token counts.

3. **Run the evaluation** over the 16-row dataset (`challenge-0/data/evaluation/evaluation_dataset.jsonl`):
   ```bash
   python challenge-2/evaluators.py
   ```
   You'll get a scorecard for the Claude-backed agent.

4. **Run the bake-off** — Claude vs GPT on the same scorecard:
   ```bash
   python challenge-2/evaluators.py --bakeoff
   ```
   Compare groundedness/relevance vs mean latency. Which model wins for *this* task?

5. **Add a quality gate** (this is what a CI job would run):
   ```bash
   python challenge-2/evaluators.py --gate 4.0   # exit code 3 if groundedness < 4.0
   ```

6. **(Portal) Continuous evaluation.** In the portal, enable **continuous/online evaluation** on the
   agent so production traffic is scored automatically. (This is portal-only preview — no stable
   Python API yet; the `--gate` flag is the code-first equivalent for CI.)

## ✔️ Success criteria

- Prompt/retrieval/tool spans visible in the portal for **both** providers.
- An evaluation scorecard is produced (groundedness, relevance, coherence, fluency).
- The **Claude-vs-GPT** comparison is captured (quality + latency).
- The quality gate **fails** when you set a threshold above the measured score (try `--gate 5.0`).

## 🚀 Go Further

- Add **safety** evaluators (`ContentSafetyEvaluator`) — these take `azure_ai_project` + a credential
  instead of a `model_config`.
- Add a **`ToolCallAccuracyEvaluator`** for the `get_contract_status` tool rows.
- Run **AI red teaming** against the agent and add adversarial rows to the dataset.
- Wire `--gate` into a GitHub Action so PRs are blocked on a groundedness regression.

## 🛠️ Troubleshooting

| Symptom | Fix |
|---------|-----|
| No spans in the portal | Confirm `APPLICATIONINSIGHTS_CONNECTION_STRING` is set; content flag must be set before SDK import; allow 1–2 min for ingestion. |
| Evaluator auth error | The judge is an **Azure OpenAI** deployment. Set `AZURE_OPENAI_ENDPOINT`/`AZURE_OPENAI_DEPLOYMENT` (or rely on the derived project endpoint + AAD). |
| `groundedness` key not found by the gate | Print `result["metrics"]` and adjust the key — SDK versions name it `groundedness` or `groundedness.groundedness`. |
| Bake-off is slow | It runs the dataset twice (once per model). Trim the JSONL while iterating. |

## 🧠 Reflection

- Tracing shows *what happened*; evaluation shows *how good it was*. Which would catch a silent
  grounding regression, and which a latency spike?
- After the bake-off, would you keep drafting on Claude? What evidence (quality vs latency/cost)
  drives that call — and how would continuous eval keep you honest in production?

➡️ Next: **[Challenge 3 — Orchestration + MCP Server](../challenge-3/)**
