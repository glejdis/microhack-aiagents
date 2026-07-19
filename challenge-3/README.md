# Challenge 3 · Orchestration + MCP Server

> **Duration:** 60 min · **Prerequisites:** Challenge 1 pattern understood (grounded agent), Ch2
> optional but recommended (you'll see orchestration spans).

## 🎯 Objective

Add the **2nd specialist** (Clause & Risk on Claude), stand up an **Orchestrator agent** (GPT-4.1)
that routes to both specialists via **connected agents**, then expose the whole workflow as an **MCP
server** callable from VS Code / GitHub Copilot.

## 🧭 Context

- **Clause & Risk agent** reuses the Ch1 grounding pattern → fast to build. It compares a
  counterparty draft to the enterprise standard and returns a **risk score**.
- **Orchestrator** (GPT-4.1) uses **`ConnectedAgentTool`** to call each specialist as a tool. A
  **GPT orchestrator coordinating Claude specialists** is multi-model composition in one project. It
  manages routing, hand-offs and human-in-the-loop.
- **MCP** (Model Context Protocol) lets you expose the workflow as standard tools so *any* MCP client
  can reuse it. You'll run a local **stdio** server and call it from VS Code.

```
        ┌────────────── Orchestrator (GPT-4.1) ──────────────┐
 user → │  routes + hand-offs + human-in-the-loop            │
        └───────┬───────────────────────────┬───────────────┘
                │ connected agent            │ connected agent
        Intake & Drafting (Claude)   Clause & Risk (Claude)
                └──────────── grounded on Foundry IQ ─────────┘
        Also exposed as an MCP server: draft_contract · analyze_contract · get_contract_status
```

## ✅ Tasks

1. **Build the Clause & Risk agent** and analyze the (deliberately red-flag) sample draft:
   ```bash
   python challenge-3/agents/clause_risk_agent.py
   ```
   Expect: clause table, flagged deviations (e.g. uncapped liability, 60-day auto-renew), **High**
   risk with top-3 issues, all cited against the standard clause library.

2. **Build the Orchestrator** with both specialists connected, and run a multi-step thread
   (draft → analyze → status):
   ```bash
   python challenge-3/orchestrator.py --keep    # --keep so Ch4 can publish it
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
  more connected agents.
- Expose the MCP server **remotely** (HTTP/SSE behind APIM) instead of stdio, and consume it from a
  Foundry agent with `MCPTool(server_label=..., server_url=..., require_approval=...)`.
- Add an approval step (`require_approval`) before high-impact tools run.

## 🛠️ Troubleshooting

| Symptom | Fix |
|---------|-----|
| Orchestrator doesn't route correctly | Sharpen the routing rules in `INSTRUCTIONS`; make connected-agent `description`s specific. |
| `ConnectedAgentTool` import error | Update `azure-ai-agents` (see requirements.txt); it's in `azure.ai.agents.models`. |
| MCP server not listed in VS Code | Ensure the MCP feature is enabled and `mcp.json` path is correct; check the server starts standalone first. |
| MCP tool call times out | Each call spins up + tears down a Foundry agent (a few seconds). Keep drafts short while testing. |

## 🧠 Reflection

- Connected agents vs one mega-agent with many tools — what do you gain (separation, per-agent
  models/eval) and what do you pay (latency, orchestration complexity)?
- MCP makes the workflow portable. Who else in the org could consume `analyze_contract` without
  touching your code?

➡️ Next: **[Challenge 4 — Publish to M365 Copilot & Teams + Alerts](../challenge-4/)**
