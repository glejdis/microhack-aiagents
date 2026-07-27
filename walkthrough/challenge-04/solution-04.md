# Solution 04 — Orchestration + MCP Server

**[← Back to Challenge 4](../../challenges/challenge-04.md)** · [Home](../../README.md)

Add the **2nd specialist** (Clause & Risk on Claude), stand up an **Orchestrator
agent** (GPT-5.4) that delegates via the `agent.as_tool(...)` pattern, then expose the
whole workflow as an **MCP server** any client can call.

## Expected end state

- [`src/agents/clause_risk_agent.py`](../../src/agents/clause_risk_agent.py) scores
  clauses against the Standard Clause Library and flags deviations.
- [`src/orchestrator.py`](../../src/orchestrator.py) routes a request to the right
  specialist(s) in-process — agents built as tools.
- [`src/mcp_server/server.py`](../../src/mcp_server/server.py) serves
  `draft_contract` · `analyze_contract` · `get_contract_status` over **stdio**;
  VS Code loads it from [`src/.vscode/mcp.json`](../../src/.vscode/mcp.json).
- [`src/orchestrator_mcp.py`](../../src/orchestrator_mcp.py) runs the same GPT-5.4
  orchestrator as an **MCP client**, consuming the workflow over MCP instead of
  in-process.

## Key files

| Path | Role |
|------|------|
| [`src/agents/clause_risk_agent.py`](../../src/agents/clause_risk_agent.py) | Clause & Risk specialist (Claude Sonnet 4.5) |
| [`src/orchestrator.py`](../../src/orchestrator.py) | Orchestrator with specialists as tools |
| [`src/mcp_server/server.py`](../../src/mcp_server/server.py) | MCP server exposing the CLM workflow over stdio |
| [`src/.vscode/mcp.json`](../../src/.vscode/mcp.json) | VS Code MCP client config (`clm-mcp`) |
| [`src/orchestrator_mcp.py`](../../src/orchestrator_mcp.py) | Orchestrator consuming the MCP server as a client |

## Run it

```bash
python src/agents/clause_risk_agent.py       # analyze a counterparty draft
python src/orchestrator.py                    # route a request to specialists in-process
python src/mcp_server/server.py               # serve over stdio (Ctrl-C to stop)
python src/orchestrator_mcp.py                # launch the stdio server and call it as a client
```

## Common issues

| Symptom | Cause / fix |
|---------|-------------|
| `orchestrator_mcp.py` finds no tools / hangs | The stdio server failed to import — confirm `python src/mcp_server/server.py` starts standalone; run from repo root (`PYTHONPATH=src`). |
| MCP server not listed in VS Code | Ensure the MCP feature is on and `src/.vscode/mcp.json` is picked up. |
