# Diagrams

Source diagrams for the CLM microhack. The **architecture** view is maintained as an
editable **draw.io** file; the **user journey** view is a finalized image (`user-journey.png`).

| View | draw.io | Rendered |
|------|---------|----------|
| **Architecture** — Orchestrator + specialist agents on Microsoft Foundry, grounded by Foundry IQ, traced & evaluated, published to Teams/M365 Copilot | [`architecture.drawio`](architecture.drawio) | [`architecture.svg`](architecture.svg) |
| **User journey** — the Contoso contract manager's path: draft → review → ask → sign-off → track → proactive renewal alert | — | [`user-journey.png`](user-journey.png) |

## How to open / edit

- **draw.io (`.drawio`)** — open at [app.diagrams.net](https://app.diagrams.net),
  or in VS Code with the **Draw.io Integration** extension (`hediet.vscode-drawio`).

## Legend (architecture)

- 🟦 **Blue** = GPT agents · 🟪 **Purple** = Claude (Anthropic) agents ·
  🟧 **Orange** = tools / MCP · 🟩 **Green** = data / grounding · ⬜ **Gray** = governance ·
  **dashed grey** = telemetry (traces, eval scorecards) · **dashed red** = alerts / guardrails.

> The **[`architecture.svg`](architecture.svg)** is the rendered image embedded in the top-level
> README; **[`architecture.drawio`](architecture.drawio)** is its editable equivalent. The
> **[`user-journey.png`](user-journey.png)** is the finalized user-journey image embedded in the README.
