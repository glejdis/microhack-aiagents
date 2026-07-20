# Coach & Facilitator Guide

Everything you need to **run** the *Agentic AI Hacks · Contract Lifecycle Management (CLM)* microhack —
timings, per-challenge coaching notes, common blockers, what "done" looks like, and reset/recovery
tips. Participants never see this file; it's for the people running the room.

> **TL;DR for coaches:** the challenge code **is** the reference solution. Every script runs
> end-to-end. Your job is to keep teams unblocked on **environment** issues (region/model
> availability, RBAC propagation, `.env`) so they spend their time on **agent** concepts, not YAML.

---

## 1. Who this is for

- **Lead coach** — owns the tech talk, timing, and go/no-go on Challenge 0.
- **Floating coaches** — 1 per 2–3 teams, unblock environment issues, run the checkpoints below.
- Assumes coaches have done a **full dry-run** end-to-end at least once in the target region.

---

## 2. Before the event (do this a week out)

| Task | Why it matters |
|------|----------------|
| **Pick a region with all 3 models** (`gpt-4.1`, `gpt-4o-mini`, `claude-sonnet-4-5`). `swedencentral` is a good default. | Challenge 0 dies here if a model isn't offered. **Verify in the Foundry model catalog for your exact subscription.** |
| **Confirm Claude is enabled** in both the **model catalog** *and* the **Foundry chat runner** for that region. | If Foundry can't serve Claude via the chat client, Ch1 needs the Anthropic-SDK fallback (documented in-challenge). Know this before the room does. |
| **Check quota** — Basic Azure AI Search + the model SKUs (TPM for each deployment). Request increases early. | Quota denials are the #1 day-of blocker and can take hours to approve. |
| **Decide the subscription model** — one sub per team (cleanest) vs a shared sub with per-team resource groups / env names. | `azd up` uses an environment name as the RG suffix; shared subs need unique names per team. |
| **Do a full dry-run** in the target region, including `azd up` **and** `scripts/deploy.sh`. | You'll hit the region/quota issues before the participants do. |
| **Pre-provision (optional but recommended)** a subscription per team the night before. | Saves ~20 of Challenge 0's 30 min; teams start on agents, not provisioning. |
| **Cost check** — models are pay-per-token; Search Basic + Storage + App Insights are the fixed cost. Tear down with `azd down` / delete the RG after. | Budget approval + a reminder to delete afterwards. |
| **Teams/M365 tenant** — confirm you (or the participants) can **sideload a custom Teams app** and publish to M365 Copilot. | Challenge 4's publish step needs sideload rights; many corp tenants block it. Have a coach-owned tenant as fallback. |

### Pre-flight checklist (per team, morning of)

- [ ] Team has an **Azure subscription** with Owner/Contributor + rights to create role assignments.
- [ ] Region confirmed to offer all three models.
- [ ] They can **fork** the repo and **open a Codespace** (or have the devcontainer locally).
- [ ] `Microsoft.BotService` provider registered (needed in Ch4): `az provider register --namespace Microsoft.BotService`.

---

## 3. Run of show (4.5 h)

| Time | Block | Coach cadence |
|------|-------|---------------|
| 09:00 – 10:00 | **Tech talk** — the CLM story, the agentic architecture, multi-model (Claude + GPT), Foundry IQ, tracing/eval, MCP, publish. | Show the [architecture diagram](images/architecture.png). Set the "human always signs" guardrail expectation. |
| 10:00 – 12:30 | **Hacking — Challenges 0, 1, 2** | **Gate at Ch0:** no team moves on until `smoke_test.py` is green. Float hard here. |
| 12:30 – 13:30 | Lunch | — |
| 13:30 – 15:30 | **Hacking — Challenges 3, 4** | Ch4 builds on a working Ch3 orchestrator — make sure Ch3 runs cleanly first. Remind teams before lunch. |
| 15:30 – 16:00 | **Wrap-up / demos** | Each team demos one thing: a cited draft, a bake-off result, an MCP call, or a live Teams alert. |
| *Overflow* | **Challenge 5 (bonus)** — Safety, Red-Teaming & CI gate | For fast finishers or as a follow-up; does **not** fit inside 4.5 h. |

**Pace check:** a team should finish **Ch0 by ~10:30**, **Ch1 by ~11:30**, **Ch2 by ~12:30**. If a
team is 20+ min behind at a checkpoint, hand them a hint (below) rather than let them grind.

---

## 4. Per-challenge coaching notes

Each challenge README has the full participant instructions. Below is the **coach layer**: the point
of the challenge, what "done" looks like, where teams get stuck, and the hint to give.

### Challenge 0 · Setup & Foundry Foundations *(30 min · setup)*

- **Point:** stand up the whole Foundry environment + seed the corpus with **zero local install**.
- **Done when:** `python scripts/smoke_test.py` prints `✅ PASS` (a tiny agent runs on **both**
  `gpt-4.1` **and** `claude-sonnet-4-5`) and the `clm-corpus` index shows documents in the portal.
- **Provisioning paths** — all produce the same resources and `.env`: **`azd up`** (Bicep in
  `challenge-0/infra/`), **`scripts/deploy.sh`** (`.ps1` on Windows), or the one-click **Deploy to
  Azure** button / `az deployment sub create` on `infra/azuredeploy.json` (then
  `python scripts/write_env.py --deployment <name>` for `.env`). Let teams pick one; don't mix.
- **Watch for:**
  - *Model deploy fails* → the model/version isn't in their region. Switch region (`eastus2`/`westus3`)
    or adjust the version in `deploy.sh`. **This is the single most common Ch0 blocker.**
  - *`account project create` unavailable* → the CLI project command is preview. Create the project in
    the **portal**, then set `AZURE_AI_PROJECT_ENDPOINT` in `.env` by hand.
  - *Claude ping fails in smoke test* → runner may not host Claude yet; they can still proceed (Ch1 has
    the fallback). Don't let them rabbit-hole here.
  - *`az login` in Codespaces* → must use `az login --use-device-code`.
  - *RBAC not propagated* → role assignments can take a few minutes; a retry usually fixes "auth" errors
    right after `azd up`.
- **Coach hint if stuck on region:** "Open the Foundry model catalog filtered to *your* subscription and
  pick a region that lists all three — don't trust a blog's default."

### Challenge 1 · Grounded Agent with Foundry IQ + Tools *(60 min · grounding · tools · guardrails)*

- **Point:** build the **Intake & Drafting agent on Claude Sonnet 4.5** — grounded, cited, tool-enabled,
  and guard-railed (refuses legal advice). Establishes the pattern reused in Ch3/4.
- **Done when:** answers are **cited** from the corpus; `get_contract_status` fires for **CT-4821**; the
  legal-advice prompt is **refused**; the model shown in the portal is the **Claude** deployment.
- **Key teaching moment:** the agent/tool/grounding API is **identical** whether `model` points at GPT
  or Claude — that's the whole point of Foundry as a model-agnostic control plane.
- **Agents are built in-process:** with the Microsoft Agent Framework each run builds its agent against
  the Foundry chat client — nothing persists server-side, so there's no `--keep` and nothing to clean up.
- **Watch for:**
  - *No citations* → confirm `seed_corpus.py` populated the index + the semantic config exists; raise `top_k`.
  - *Function tool never called* → keep the docstring + type hints (the schema is derived from them) and
    ensure it's wrapped with `function_tool(...)` and passed in `tools=[...]`.
  - *Search connection returns nothing* → set `AZURE_SEARCH_CONNECTION_NAME` in `.env`; check portal →
    Connected resources.
  - *Run `failed` on Claude* → use the **Anthropic-SDK fallback** in the README (§ Claude fallback). Point
    them to it; don't let them think the whole platform is broken.
- **Coach hint:** "Run `sample_prompts.md` top to bottom — it deliberately exercises draft → cited Q&A →
  status lookup → refusal, one per capability."

### Challenge 2 · Observability, Tracing & Evaluation *(60 min · tracing · eval)*

- **Point:** make the agent **observable** (OTel traces → App Insights) and **measurable** (evaluation
  scorecard + a **Claude-vs-GPT bake-off** + a **quality gate**).
- **Done when:** prompt/retrieval/tool spans are visible for **both** providers; a scorecard prints
  (groundedness/relevance/coherence/fluency); the **bake-off** captures quality vs latency; `--gate`
  fails when the threshold is set above the measured score.
- **The "aha":** tracing shows *what happened*; evaluation shows *how good it was*. The bake-off is the
  concrete payoff of a model-agnostic platform.
- **Watch for:**
  - *No spans* → `APPLICATIONINSIGHTS_CONNECTION_STRING` must be set, the content-recording flag must be
    set **before** the agents SDK import (`tracing_setup` does this on import — import it first), and
    ingestion lags **1–2 min**. Tell teams to wait, not thrash.
  - *Evaluator auth error* → the judge is an **Azure OpenAI** deployment; set `AZURE_OPENAI_ENDPOINT` /
    `AZURE_OPENAI_DEPLOYMENT` or rely on the derived project endpoint + AAD.
  - *`groundedness` key not found by the gate* → SDK versions name it `groundedness` vs
    `groundedness.groundedness`; print `result["metrics"]`.
  - *Bake-off is slow* → it runs the dataset **twice** (once per model). Trim the JSONL while iterating.
- **Commands worth demoing:** `evaluators.py --bakeoff` and `evaluators.py --gate 5.0` (watch it fail
  on purpose — exit code 3).

### Challenge 3 · Orchestration + MCP Server *(60 min · orchestration · MCP)*

- **Point:** add the **Clause & Risk** specialist (Claude), stand up a **GPT-4.1 Orchestrator** that
  routes to both specialists via the **agent-as-tool pattern**, and expose the workflow as an **MCP server**.
- **Done when:** one orchestrator thread runs **draft → extract → risk** by delegating; the Clause & Risk
  agent returns a structured, cited risk assessment; the **MCP server is discoverable + callable** from
  VS Code / Copilot Chat (`#draft_contract`, `#analyze_contract`, `#get_contract_status`).
- **Ch4 builds on this orchestrator:** it publishes the Ch3 orchestrator pattern — make sure it runs cleanly.
  Call this out loudly before lunch.
- **Watch for:**
  - *Orchestrator routes wrong* → sharpen `INSTRUCTIONS` routing rules and make each specialist's
    `as_tool(description=...)` specific.
  - *`agent_framework` import error* → `pip install agent-framework-core agent-framework-foundry` (see requirements.txt).
  - *MCP server not listed in VS Code* → ensure the MCP feature is on and `challenge-3/.vscode/mcp.json`
    is picked up; confirm the server starts standalone first (`python challenge-3/mcp_server/server.py`).
  - *MCP call times out* → each call spins up + tears down a Foundry agent (a few seconds); keep test
    drafts short.
- **Sample draft is rigged:** the Clause & Risk sample has deliberate red flags (uncapped liability,
  60-day auto-renew) so a **High** risk result is the expected, demo-able outcome.

### Challenge 4 · Publish to M365 Copilot & Teams + Proactive Alerts *(60 min ≈ 30 publish + 30 alerts)*

- **Point:** ship the orchestrator to **Teams / M365 Copilot** (conversational, no bot code) **and**
  push **proactive** renewal/risk alerts into Teams (needs a saved conversation reference).
- **Done when:** the orchestrator answers **live in Teams and M365 Copilot** with grounded, cited
  responses; **and** a proactive alert (e.g. the CT-4821 message) appears **without** the user prompting.
- **The distinction to teach:** conversational = **pull** (auto Azure Bot Service channel); proactive =
  **push** (save `TurnContext.get_conversation_reference` on first inbound, then
  `ADAPTER.continue_conversation(...)`).
- **Watch for:**
  - *Publish option missing* → `Microsoft.BotService` not registered, or no rights to create an Azure Bot.
  - *Works in Teams but not Copilot* → the app must be **approved for M365 Copilot** and manifest scopes
    must include it.
  - *`continue_conversation` 401/403* → check `MICROSOFT_APP_ID` / `MICROSOFT_APP_PASSWORD`; the bot must
    own the saved conversation reference.
  - *Alert never arrives* → `TEAMS_SERVICE_URL` + `TEAMS_CONVERSATION_ID` must come from a **real inbound**
    message to *this* bot.
- **No-tenant fallback:** everything alert-related runs with `--dry-run` to print the exact text without
  sending — teams blocked on sideload rights can still complete the *logic*. The manifest template +
  **branded placeholder icons** live in `challenge-4/manifest/` (regenerate via
  `python scripts/make_icons.py`), so zipping the app package needs no design work.

### Challenge 5 · Safety, Red-Teaming & Continuous Eval 🧪 *(bonus · optional · ~45–60 min)*

- **Point:** close the responsible-AI loop — attack the agent with the **AI Red Teaming Agent**, add
  **Content Safety / PII** guardrails, and wire a **quality + safety gate into CI**.
- **Done when:** a red-team scorecard exists with a per-category **attack success rate**; the safety eval
  prints a **guardrail defect rate**; the gate **fails** on a strict threshold; and after **hardening**
  the rate is **measurably lower**.
- **Watch for:**
  - *`ModuleNotFoundError: azure.ai.evaluation.red_team`* → install the extra: `pip install "azure-ai-evaluation[redteam]"` (pulls PyRIT, one-time).
  - *Scan is slow* → lower `--num-objectives`; run baseline before `--strategies` (each objective is a
    full agent turn).
  - *Safety evaluators 401/403* → they need the **Foundry project** endpoint + a logged-in credential.
- **Zero-Azure preview:** `safety_eval.py --dry-run --gate 0.1` shows the gate mechanics with no Azure
  calls — good for teaching CI behaviour even if they're out of time/quota.

---

## 5. Reset & recovery playbook

| Situation | Fix |
|-----------|-----|
| **`.env` looks wrong / half-populated** | Re-run the provision path (`azd up` re-runs the `write_env.py` hook), or hand-set the missing keys from the portal (project endpoint under **Overview → Endpoint**). |
| **Corpus / index empty** | Re-run `python scripts/seed_corpus.py` (idempotent — re-uploads Blob + rebuilds the index). |
| **Legacy agents in the project** | The Microsoft Agent Framework builds agents in-process against the Foundry chat client — it registers **no** persistent server-side agents, so there's nothing to clean up. Delete any stragglers from earlier Agent-Service runs in **portal → Agents** if you like. |
| **Auth / 403 right after provisioning** | RBAC propagation lag — wait 2–3 min and retry before debugging anything else. |
| **Everything is wedged, start clean** | `azd down` (or delete the resource group), then `azd up` again. Budget ~15 min. |
| **Region has no Claude runner** | Proceed with the **Anthropic-SDK fallback** in Challenge 1 — the concepts still land; only the *hosting* path differs. |
| **Cross-challenge script `ModuleNotFoundError`** | Should not happen — the shared-module import paths are fixed and CI byte-compiles all six challenges. If it does, confirm the team didn't move files between folders. |

---

## 6. Facilitation tips

- **Gate Challenge 0.** Nobody advances on a red smoke test — a broken env poisons every later challenge.
- **Hint, don't solve.** Give the *smallest* nudge from the tables above; let teams keep ownership.
- **Protect the "aha" moments.** Make sure every team sees at least: a **cited** answer (Ch1), the
  **bake-off** (Ch2), a **routed** orchestrator turn (Ch3), and a **live Teams** response or alert (Ch4).
- **The code is the answer key.** If a team is truly stuck, read the relevant script *with* them — it's
  the reference implementation, fully commented.
- **Time-box the fallbacks.** Claude-runner and no-tenant fallbacks exist precisely so one environment
  gap doesn't cost a team the whole afternoon. Reach for them early.
- **Bank Challenge 5** for the one or two teams who fly — it's a great "take it home" extension.

---

## 7. Cross-cutting gotchas (memorize these)

1. **Region + model availability** decides everything — validate against the *actual* subscription.
2. **Tracing lag** is 1–2 min; the content-recording flag must be set **before** the SDK import.
3. **RBAC propagation** lag causes false "auth" failures right after provisioning — retry first.
4. **Agents are built in-process** with the Microsoft Agent Framework — nothing persists server-side, so each challenge rebuilds its agent (no `--keep`).
5. **Sideload rights** in the M365 tenant are the Ch4 wildcard — have a coach tenant on standby.

---

➡️ Participant docs start at the **[main README](../README.md)** and **[Challenge 0](../challenge-0/)**.
