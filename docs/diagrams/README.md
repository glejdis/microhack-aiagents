# Diagrams

Editable source diagrams for the CLM microhack. The **architecture** view is
maintained in **draw.io**; the **user journey** view is provided in **two
formats** so you can open and edit in whichever tool you prefer.

| View | draw.io | Excalidraw | Rendered |
|------|---------|------------|----------|
| **Architecture** — Orchestrator + specialist agents on Microsoft Foundry, grounded by Foundry IQ, traced & evaluated, published to Teams/M365 Copilot | [`architecture.drawio`](architecture.drawio) | — | [`architecture.svg`](architecture.svg) |
| **User journey** — the Contoso contract manager's path: draft → review → ask → sign‑off → track → proactive renewal alert | [`user-journey.drawio`](user-journey.drawio) | [`user-journey.excalidraw`](user-journey.excalidraw) | [`user-journey.svg`](user-journey.svg) |

## How to open / edit

- **draw.io (`.drawio`)** — open at [app.diagrams.net](https://app.diagrams.net),
  or in VS Code with the **Draw.io Integration** extension (`hediet.vscode-drawio`).
- **Excalidraw (`.excalidraw`)** — open at [excalidraw.com](https://excalidraw.com)
  (or the Microsoft‑internal instance), or in VS Code with the **Excalidraw**
  extension (`pomdtr.excalidraw-editor`).

## Legend (architecture)

- 🟦 **Blue** = GPT agents · 🟪 **Purple** = Claude (Anthropic) agents ·
  🟧 **Orange** = tools / MCP · 🟩 **Green** = data / grounding · ⬜ **Gray** = governance ·
  **dashed grey** = telemetry (traces, eval scorecards) · **dashed red** = alerts / guardrails.

> The **[`architecture.svg`](architecture.svg)** and **[`user-journey.svg`](user-journey.svg)** are the
> rendered images embedded in the top‑level README. The **`.drawio`** files (and the user‑journey
> **`.excalidraw`**) are the editable equivalents. Regenerate the journey view with
> `python scripts/make_user_journey.py`.
