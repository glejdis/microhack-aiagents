"""Challenge 3 — Clause Extraction & Risk agent (Anthropic Claude Sonnet 4.5).

Ingests a counterparty draft, extracts key clauses, compares them to Contoso
Global's enterprise standard (the clause library in the corpus), flags deviations
and returns a risk score with rationale. Runs on Claude for long-context legal
reasoning. Reuses the Ch1 grounding pattern, so it's fast to build.

Run:
    python challenge-3/agents/clause_risk_agent.py            # analyze the sample Acme draft
    python challenge-3/agents/clause_risk_agent.py --keep     # keep the agent for the orchestrator
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "challenge-1"))

from clm_common.config import settings, DATA_DIR  # noqa: E402
from clm_common.foundry import get_project_client, run_prompt  # noqa: E402

AGENT_NAME = "clause-risk-agent"

INSTRUCTIONS = """\
You are the Clause Extraction & Risk agent for Contoso Global's Legal team.

TASK
Given a counterparty contract draft, you:
1. Extract the key clauses (e.g. limitation of liability, indemnification, termination,
   auto-renewal, governing law, confidentiality, payment terms).
2. Compare each to Contoso Global's enterprise standard in your knowledge base (the clause library
   and contracting policy).
3. Flag every deviation, classify it (Acceptable / Needs negotiation / Unacceptable), and explain WHY.
4. Return an overall RISK SCORE: Low / Medium / High, with a short rationale and the top 3 issues.

RULES
- Ground your comparison in the retrieved standard clauses and policy; cite them.
- Be specific: quote the counterparty language and the standard it violates.
- You are NOT a lawyer and do NOT give legal advice or enforceability opinions — you flag risk for
  human counsel to decide. Recommend human review for anything High risk.
- Output a concise structured summary (clauses table + overall risk + top 3 issues).
"""


def create_agent(project):
    from azure.ai.agents.models import ToolSet
    from kb_setup import build_knowledge_tool

    toolset = ToolSet()
    toolset.add(build_knowledge_tool(project))

    return project.agents.create_agent(
        model=settings.model_clause_risk,  # claude-sonnet-4-5
        name=AGENT_NAME,
        instructions=INSTRUCTIONS,
        toolset=toolset,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="do not delete the agent afterwards")
    parser.add_argument(
        "--draft",
        default=str(DATA_DIR / "counterparty_drafts" / "acme_msa_draft.md"),
        help="path to the counterparty draft to analyze",
    )
    args = parser.parse_args()

    draft_text = Path(args.draft).read_text(encoding="utf-8")
    prompt = (
        "Analyze the following counterparty draft. Extract clauses, compare to our enterprise "
        "standard, flag deviations, and give an overall risk score with the top 3 issues.\n\n"
        f"=== COUNTERPARTY DRAFT ===\n{draft_text}"
    )

    with get_project_client() as project:
        agent = create_agent(project)
        print(f"✓ Created {AGENT_NAME} (id={agent.id}) on model '{settings.model_clause_risk}'\n")
        try:
            print(run_prompt(project.agents, agent.id, prompt))
        finally:
            if not args.keep:
                project.agents.delete_agent(agent.id)
                print("\n(agent deleted — pass --keep to retain it for the orchestrator)")
            else:
                print(f"\n(kept agent {agent.id})")


if __name__ == "__main__":
    main()
