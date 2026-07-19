#!/usr/bin/env python
"""Challenge 0 — smoke test.

Verifies the environment is wired up before you start building agents:
  1. `.env` is loaded and required variables are present.
  2. The Foundry project is reachable and can create+run a tiny agent on a GPT
     deployment AND on the Claude deployment (proving the multi-model fleet).

Run:  python scripts/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clm_common.config import settings  # noqa: E402
from clm_common.foundry import get_project_client, run_prompt  # noqa: E402


def check_env() -> bool:
    ok = True
    print("1) Checking environment…")
    required = {
        "AZURE_AI_PROJECT_ENDPOINT": settings.project_endpoint,
        "MODEL_ORCHESTRATOR": settings.model_orchestrator,
        "MODEL_DRAFTING": settings.model_drafting,
        "MODEL_CLAUSE_RISK": settings.model_clause_risk,
        "MODEL_RENEWAL": settings.model_renewal,
    }
    for name, value in required.items():
        status = "✓" if value else "✗ MISSING"
        print(f"   {status} {name} = {value or ''}")
        ok = ok and bool(value)
    return ok


def ping_model(project, model: str, label: str) -> bool:
    print(f"2) Pinging {label} deployment '{model}'…")
    try:
        agent = project.agents.create_agent(
            model=model,
            name=f"smoke-{label}",
            instructions="Reply with exactly one word: OK.",
        )
        try:
            reply = run_prompt(project.agents, agent.id, "Say OK.")
            print(f"   ✓ {label} replied: {reply.strip()[:60]}")
            return "[run failed" not in reply
        finally:
            project.agents.delete_agent(agent.id)
    except Exception as exc:  # noqa: BLE001
        print(f"   ✗ {label} failed: {exc}")
        if label == "claude":
            print("     → If Claude isn't supported in the Agent runner for your region,")
            print("       see challenge-1/README.md for the Anthropic-SDK fallback.")
        return False


def main() -> int:
    if not check_env():
        print("\n✗ Environment incomplete. Run scripts/deploy.sh or fill .env, then retry.")
        return 1

    with get_project_client() as project:
        gpt_ok = ping_model(project, settings.model_orchestrator, "gpt")
        claude_ok = ping_model(project, settings.model_drafting, "claude")

    print("\nSmoke test:", "✅ PASS" if (gpt_ok and claude_ok) else "⚠️  PARTIAL (see notes above)")
    return 0 if (gpt_ok and claude_ok) else 2


if __name__ == "__main__":
    raise SystemExit(main())
