"""Challenge 3 — Orchestrator agent (GPT-4.1) with connected specialist agents.

Builds the front-door **Orchestrator** on GPT-4.1 and connects the two Claude
specialists (Intake & Drafting, Clause & Risk) as **connected agents**. The
orchestrator routes each user request to the right specialist, manages hand-offs
and human-in-the-loop review. This is the agent you publish to Teams in Ch4.

A GPT orchestrator calling Claude-backed specialists demonstrates multi-model
composition inside one Foundry project.

Run:
    python challenge-3/orchestrator.py                 # one thread: draft → analyze → risk
    python challenge-3/orchestrator.py --keep          # keep agents (needed for Ch4 publish)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0] / "agents"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "challenge-1"))

from clm_common.config import settings  # noqa: E402
from clm_common.foundry import get_project_client, run_prompt  # noqa: E402

ORCHESTRATOR_NAME = "clm-orchestrator"

INSTRUCTIONS = """\
You are the CLM Orchestrator for Contoso Global — the single front door for Legal & Procurement.

You have two connected specialist agents:
- `intake_drafting` — drafts NDA/MSA/SOW from approved templates and answers cited questions about
  clauses, policies and contract status.
- `clause_risk` — analyzes a counterparty draft: extracts clauses, compares to our standard, flags
  deviations and returns a risk score.

ROUTING
- Drafting a document, or a question about our templates/policies/contract status → `intake_drafting`.
- Reviewing/analyzing an incoming counterparty draft or asking about its risk → `clause_risk`.
- A multi-step request (e.g. "draft X then analyze the counterparty's redline") → call them in order
  and combine the results.

HUMAN-IN-THE-LOOP
- For anything flagged High risk or any final document, clearly recommend human review before signing.
- Never provide legal advice yourself; defer to the specialists and to human counsel.
Summarize each specialist's output for the user and state which agent you used.
"""


def build_orchestrator(project):
    """Create the two specialists + the orchestrator wired with ConnectedAgentTool. Returns ids."""
    from azure.ai.agents.models import ConnectedAgentTool
    from intake_drafting_agent import create_agent as create_intake
    from clause_risk_agent import create_agent as create_clause_risk

    intake = create_intake(project)
    clause_risk = create_clause_risk(project)

    intake_tool = ConnectedAgentTool(
        id=intake.id,
        name="intake_drafting",
        description="Draft NDA/MSA/SOW from approved templates; answer cited questions about "
        "clauses, policies and contract status.",
    )
    clause_tool = ConnectedAgentTool(
        id=clause_risk.id,
        name="clause_risk",
        description="Analyze a counterparty draft: extract clauses, compare to standard, flag "
        "deviations, return a risk score.",
    )

    orchestrator = project.agents.create_agent(
        model=settings.model_orchestrator,  # gpt-4.1
        name=ORCHESTRATOR_NAME,
        instructions=INSTRUCTIONS,
        tools=[*intake_tool.definitions, *clause_tool.definitions],
    )
    return orchestrator.id, [intake.id, clause_risk.id, orchestrator.id]


DEMO = [
    "Draft a mutual NDA between Contoso Global and Acme Corp for a 2-year term.",
    "Now review the Acme MSA counterparty draft we received and give me its risk score.",
    "What's the renewal date and risk level of contract CT-4821?",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="keep all agents (for Ch4 publish)")
    args = parser.parse_args()

    with get_project_client() as project:
        orch_id, all_ids = build_orchestrator(project)
        print(f"✓ Orchestrator (id={orch_id}) on '{settings.model_orchestrator}' "
              f"with 2 connected Claude specialists\n")
        try:
            thread_id = project.agents.threads.create().id
            for prompt in DEMO:
                print("―" * 80)
                print("USER:", prompt)
                print("ORCHESTRATOR:", run_prompt(project.agents, orch_id, prompt, thread_id=thread_id), "\n")
        finally:
            if not args.keep:
                for aid in all_ids:
                    project.agents.delete_agent(aid)
                print("(agents deleted — pass --keep to retain for Challenge 4)")
            else:
                print(f"(kept agents — orchestrator id: {orch_id})")
                print("  → In the portal, open this orchestrator to publish it in Challenge 4.")


if __name__ == "__main__":
    main()
