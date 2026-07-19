# Agentic AI Hacks · Contract Lifecycle Management

Build a **multi-model, multi-agent** contract assistant on **Microsoft Foundry** — grounded with
**Foundry IQ**, traced and evaluated, exposed as an **MCP server**, and published to **Microsoft 365
Copilot & Teams** with proactive renewal alerts.

> A 4.5-hour microhack · 5 challenges (+ optional bonus) · code-first (Python) · GitHub Codespaces.

---

## The scenario — Contoso Global

Contoso Global signs hundreds of contracts a month. Legal & Procurement drown in intake, clause
review, and renewals: ~17-day turnaround and ~11% of auto-renewals missed. Contracts are scattered
across SharePoint, email, and legacy systems, and comparing a counterparty draft to the enterprise
standard is slow and manual.

You'll build an **Agentic CLM** system: an **Orchestrator** coordinating grounded specialist agents
that draft from approved templates, extract and risk-score clauses, answer cited questions over the
corpus, and proactively alert on renewals — all with **human sign-off and full tracing**.

---

## Architecture

```mermaid
flowchart TB
    user["User in Microsoft 365 Copilot / Teams"]
    user <--> orch

    subgraph Foundry["Microsoft Foundry project"]
        orch["Orchestrator Agent<br/>(GPT-4.1)"]
        intake["Intake &amp; Drafting<br/>(Claude Sonnet 4.5)"]
        clause["Clause &amp; Risk<br/>(Claude Sonnet 4.5)"]
        renew["Obligation &amp; Renewal<br/>(GPT-4o-mini)"]
        orch --> intake
        orch --> clause
        orch --> renew
    end

    subgraph Ground["Grounding & tools"]
        iq[("Foundry IQ<br/>Azure AI Search")]
        sql[("Azure SQL<br/>contract status")]
        mcp["MCP server<br/>draft_contract · analyze_contract"]
    end

    intake --> iq
    clause --> iq
    renew --> sql
    orch --> mcp

    subgraph Obs["Observability & governance"]
        ai["App Insights · Tracing"]
        eval["Evaluations · Content Safety"]
    end
    Foundry -.traces.-> ai
    Foundry -.scorecard.-> eval

    renew -. "proactive alert" .-> user
```

### Multi-model fleet

Anthropic **Claude is generally available in Microsoft Foundry** (model catalog **and** Foundry Agent
Service), Azure-hosted with Entra identity, consolidated billing, and data-residency controls — so
specialists run on Claude while orchestration runs on GPT, all inside **one** Foundry project.

| Agent | Model | Why this model |
|-------|-------|----------------|
| **Orchestrator** | GPT-4.1 | Fast, deterministic routing + tool/hand-off calls |
| **Intake & Drafting** | **Claude Sonnet 4.5** | High-fidelity, template-grounded drafting |
| **Clause & Risk** | **Claude Sonnet 4.5** | 200K-context clause comparison + nuanced risk rationale |
| **Obligation & Renewal** | GPT-4o-mini | Cheap, high-frequency structured extraction + alerts |

---

## What you'll learn

- **Foundry Agent Service** — build grounded, tool-using agents (on GPT **and** Claude).
- **Foundry IQ** — agentic retrieval over Azure AI Search with cited answers.
- **Tools & MCP** — function tools (Azure SQL) and exposing the workflow as an MCP server.
- **GenAIOps** — OpenTelemetry tracing to App Insights, evaluation scorecards, a quality gate, and a
  **Claude-vs-GPT bake-off**.
- **Multi-agent orchestration** — an orchestrator delegating to specialists.
- **Publish** — ship the assistant to **M365 Copilot & Teams** and push **proactive alerts**.
- **Responsible AI** *(bonus)* — red-team the agent, add Content Safety/PII guardrails, and gate
  releases on a **quality + safety** check in CI.

---

## Challenges

| # | Challenge | Focus | Duration |
|---|-----------|-------|----------|
| [0](challenge-0/) | Resource deployment · Codespaces · `.env` · corpus seeding | Setup | 30 min |
| [1](challenge-1/) | Intake & Drafting agent + Foundry IQ + tools | Grounding · tools · guardrails | 60 min |
| [2](challenge-2/) | Observability, tracing & evaluation | Tracing · eval | 60 min |
| [3](challenge-3/) | Clause & Risk agent + Orchestrator + MCP server | Orchestration · MCP | 60 min |
| [4](challenge-4/) | Publish to M365 Copilot & Teams + proactive alerts | Publish · alerts | 60 min |
| [5](challenge-5/) 🧪 | *Bonus:* Safety, Red-Teaming & Continuous Eval | Responsible AI · CI gate | optional |

## Suggested agenda (4.5h)

| Time | Activity |
|------|----------|
| 09:00 – 10:00 | Tech Talk |
| 10:00 – 12:30 | Team hacking — Challenges 0, 1, 2 |
| 12:30 – 13:30 | Lunch break |
| 13:30 – 15:30 | Team hacking — Challenges 3, 4 |
| 15:30 – 16:00 | Final discussion / wrap up |

> 🧪 **Bonus [Challenge 5](challenge-5/)** (Safety, Red-Teaming & Continuous Eval) is optional — for
> teams who finish early. It doesn't fit inside the 4.5h; tackle it if you have time or as follow-up.

---

## Prerequisites

- An **Azure subscription** with rights to create a Foundry project and deploy models (GPT **and**
  Anthropic Claude — confirm Claude availability in your target region via the model catalog).
- **GitHub account** (to fork + open in Codespaces).
- Basic Python. No local install needed — the devcontainer has everything.
- For Challenge 4: a Microsoft 365 tenant where you can sideload a Teams app (or a coach-provided one).

## Getting started

1. **Fork** this repo, then **Code → Codespaces → Create codespace**. The devcontainer installs
   Python 3.11, Azure CLI, Node, and `requirements.txt` automatically.
2. `az login`
3. Do **[Challenge 0](challenge-0/)** to deploy resources and seed the corpus. The deploy script
   autofills your `.env`.
4. Work through Challenges 1 → 4.

---

## Repo layout

```
.
├── .devcontainer/            # Codespaces definition
├── src/clm_common/           # shared config + Foundry client helpers
├── scripts/                  # deploy, seed corpus, smoke test
├── data/                     # CLM corpus + evaluation dataset
├── challenge-0/ … challenge-4/   # one folder per challenge (README + code)
├── challenge-5/              # bonus: safety, red-teaming & CI eval gate
└── images/                   # architecture + per-challenge diagrams
```

Each challenge README follows the same anatomy: **🎯 Objective · 🧭 Context · ✅ Tasks · ✔️ Success
criteria · 🚀 Go Further · 🛠️ Troubleshooting · 🧠 Reflection**.

---

> **Guardrail:** the agents assist Legal & Procurement — they draft, analyze, and recommend, but they
> **do not give legal advice** and **never execute a contract**. A human always approves and signs.