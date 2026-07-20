# Diagrams

Editable source diagrams for the CLM microhack. Each view is provided in **two
formats** so you can open and edit in whichever tool you prefer.

| View | draw.io | Excalidraw | Rendered |
|------|---------|------------|----------|
| **Architecture** — Orchestrator + specialist agents on Microsoft Foundry, grounded by Foundry IQ, traced & evaluated, published to Teams/M365 Copilot | [`architecture.drawio`](architecture.drawio) | [`architecture.excalidraw`](architecture.excalidraw) | [`architecture.svg`](architecture.svg) |
| **User journey** — the Contoso contract manager's path: draft → review → ask → sign‑off → track → proactive renewal alert | [`user-journey.drawio`](user-journey.drawio) | [`user-journey.excalidraw`](user-journey.excalidraw) | — |

## How to open / edit

- **draw.io (`.drawio`)** — open at [app.diagrams.net](https://app.diagrams.net),
  or in VS Code with the **Draw.io Integration** extension (`hediet.vscode-drawio`).
- **Excalidraw (`.excalidraw`)** — open at [excalidraw.com](https://excalidraw.com)
  (or the Microsoft‑internal instance), or in VS Code with the **Excalidraw**
  extension (`pomdtr.excalidraw-editor`).

## Legend (architecture)

- 🟦 **Blue** = GPT agents · 🟪 **Purple** = Claude (Anthropic) agents ·
  🟧 **Orange** = tools / MCP · **dashed** = telemetry (traces, eval scorecards).

> The **[`architecture.svg`](architecture.svg)** is the rendered image embedded in the top‑level
> README (a vector export of the `.drawio` / `.excalidraw` architecture view). The `.drawio` and
> `.excalidraw` files are the editable equivalents; `user-journey.*` adds the end‑to‑end journey view.
