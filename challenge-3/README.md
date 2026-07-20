# Challenge 3 · Orchestration + MCP Server

> **Duration:** 60 min · **Prerequisites:** Challenge 1 pattern understood (grounded agent), Ch2
> optional but recommended (you'll see orchestration spans).

> 🧩 **How to use this challenge:** the code in this folder is a **complete, working reference
> implementation** — you're not building it from a blank file. **Run it, read it, and understand *why*
> it works**, then take it further with **🚀 Go Further**. Stuck? The code *is* the answer key.

## 🎯 Objective

Add the **2nd specialist** (Clause & Risk on Claude), stand up an **Orchestrator agent** (GPT-5.3)
that routes to both specialists via the **agent-as-tool pattern**, then expose the whole workflow as an **MCP
server** callable from VS Code / GitHub Copilot.

## 🧭 Context

- **Clause & Risk agent** reuses the Ch1 grounding pattern → fast to build. It compares a
  counterparty draft to the enterprise standard and returns a **risk score**.
- **Orchestrator** (GPT-5.3) uses the Agent Framework's **`agent.as_tool(...)`** to call each specialist as a tool. A
  **GPT orchestrator coordinating Claude specialists** is multi-model composition in one project. It
  manages routing, hand-offs and human-in-the-loop.
- **MCP** (Model Context Protocol) lets you expose the workflow as standard tools so *any* MCP client
  can reuse it. You'll run a local **stdio** server and call it from VS Code.

```
        ┌────────────── Orchestrator (GPT-5.3) ──────────────┐
 user → │  routes + hand-offs + human-in-the-loop            │
        └───────┬───────────────────────────┬───────────────┘
                │ agent-as-tool             │ agent-as-tool
        Intake & Drafting (Claude)   Clause & Risk (Claude)
                └──────────── grounded on Foundry IQ ─────────┘
        Also exposed as an MCP server: draft_contract · analyze_contract · get_contract_status
```

## 🧰 Services & models in this challenge

This challenge is about **composition**: many specialist agents behind one orchestrator, plus a standard
protocol that makes the whole workflow reusable outside your code.

### Agent-as-tool composition (`agent.as_tool(...)`)

**What it is:** the Microsoft Agent Framework's **multi-agent orchestration** primitive. You wrap an
existing agent as a *tool* and hand it to an orchestrator, which then calls specialists the same way it
calls a function.

- **Separation of concerns** — each specialist has its own model, instructions and evaluation.
- The orchestrator handles **routing, hand-offs and human-in-the-loop**.
- A **GPT orchestrator coordinating Claude specialists** = multi-model composition in one project.
- `agent.as_tool(name=..., description=...)` wires each specialist into
  [`challenge-3/orchestrator.py`](orchestrator.py); agents are built in-process, so there's nothing to keep.

**Why here:** it lets the Orchestrator delegate *drafting* and *clause/risk* to the right specialist
instead of one bloated mega-agent. → [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/overview/agent-framework-overview)

### Model — GPT-5.3 (the orchestrator)

**What it is:** the LLM behind the Orchestrator (`MODEL_ORCHESTRATOR = gpt-5.3`) — deployment `gpt-5.3`
(`format: OpenAI`, version confirmed in your region's Foundry catalog, SKU `GlobalStandard`, capacity 30), sitting alongside the Claude
specialists on the same account.

- Fast, **deterministic tool-calling** and reliable **routing** decisions.
- Same Agents API as the Claude agents — only the `model` id differs.

**Why here:** routing and hand-offs reward speed and predictable tool selection (GPT), while drafting
rewards long-context legal reasoning (Claude) — the platform lets you pick **the right model per job**.
→ [Models in Microsoft Foundry](https://learn.microsoft.com/azure/ai-foundry/)

### Model Context Protocol (MCP)

**What it is:** an **open standard** for exposing tools/data to any LLM client. You run a local **stdio**
server that publishes the workflow as standard tools; any MCP client (VS Code, GitHub Copilot) can
discover and call them.

- **Portable** — the same tools work across editors, agents and hosts.
- Decouples *who provides a capability* from *who consumes it*.
- `challenge-3/mcp_server/server.py` serves over **stdio**; VS Code loads it from
  `challenge-3/.vscode/mcp.json` (start **clm-mcp**), exposing `draft_contract` · `analyze_contract` · `get_contract_status`.

**Why here:** it turns your agents into reusable building blocks the rest of the org can call **without
touching your code**. → [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro)

### Azure SQL Database

**What it is:** the **optional** managed relational store behind `get_contract_status` — provisioned only
when you deploy with `deploySql=true` (`Basic` tier, database `clmdb`, table `dbo.contracts`); without it
the tool falls back to `contracts_seed.json`.

- Queried via **pyodbc** (`ODBC Driver 18 for SQL Server`) in [`src/clm_common/tools.py`](../src/clm_common/tools.py).
- Authoritative, **queryable** system-of-record for structured contract facts.

**Why here:** structured contract facts belong in a database the tool can query, not in the model's
memory. → [Azure SQL Database](https://learn.microsoft.com/en-us/azure/azure-sql/database/sql-database-paas-overview?view=azuresql)

## ✅ Tasks

1. **Build the Clause & Risk agent** and analyze the (deliberately red-flag) sample drafts. By
   default it analyzes **both** inbound drafts (`acme_msa_draft.pdf` and `globex_nda_redline.pdf`),
   reusing one agent:
   ```bash
   python challenge-3/agents/clause_risk_agent.py
   # analyze a single draft instead:
   python challenge-3/agents/clause_risk_agent.py --draft challenge-0/data/counterparty_drafts/globex_nda_redline.pdf
   ```
   Expect: per draft, a clause table, flagged deviations (e.g. uncapped liability, 60-day
   auto-renew) with the negotiation-playbook fallback for items to negotiate, **High** risk with
   top-3 issues and the required approver per the delegation-of-authority matrix, all cited against
   the standard clause library.

2. **Build the Orchestrator** with both specialists connected, and run a multi-step thread
   (draft → analyze → status):
   ```bash
   python challenge-3/orchestrator.py
   ```
   Note which specialist the orchestrator says it used for each turn.

3. **Run the MCP server** and inspect its tools:
   ```bash
   python challenge-3/mcp_server/server.py       # serves over stdio (Ctrl-C to stop)
   ```

4. **Consume it from VS Code.** Open this repo in VS Code, ensure `challenge-3/.vscode/mcp.json`
   is picked up (Command Palette → *MCP: List Servers* → start **clm-mcp**), then in Copilot Chat
   (Agent mode) call `#draft_contract` / `#analyze_contract` / `#get_contract_status`. This proves
   the workflow is reusable outside your script.

## ✔️ Success criteria

- One orchestrator thread runs **draft → extract → risk** by delegating to the two specialists.
- The Clause & Risk agent returns a structured risk assessment with citations.
- The MCP server is **discoverable and callable** from an MCP client (VS Code/Copilot), returning
  the same results as the agents.

## 🚀 Go Further

- Add the **Review & Negotiation** and **Signature & Repository** agents from the 5-agent vision as
  more agent-as-tool specialists.
- Expose the MCP server **remotely** (HTTP/SSE behind APIM) instead of stdio, and consume it from a
  Foundry agent with `MCPTool(server_label=..., server_url=..., require_approval=...)`.
- Add an approval step (`require_approval`) before high-impact tools run.

## 🛠️ Troubleshooting

| Symptom | Fix |
|---------|-----|
| Orchestrator doesn't route correctly | Sharpen the routing rules in `INSTRUCTIONS`; make each specialist's `as_tool(description=...)` specific. |
| `agent_framework` import error | Install the framework: `pip install agent-framework-core agent-framework-foundry` (see requirements.txt). |
| MCP server not listed in VS Code | Ensure the MCP feature is enabled and `mcp.json` path is correct; check the server starts standalone first. |
| MCP tool call times out | Each call spins up + tears down a Foundry agent (a few seconds). Keep drafts short while testing. |

## 🧠 Reflection

- Specialist agents-as-tools vs one mega-agent with many tools — what do you gain (separation, per-agent
  models/eval) and what do you pay (latency, orchestration complexity)?
- MCP makes the workflow portable. Who else in the org could consume `analyze_contract` without
  touching your code?

➡️ Next: **[Challenge 4 — Publish to M365 Copilot & Teams + Alerts](../challenge-4/)**
