"""Challenge 3 — Clause Extraction & Risk agent (Anthropic Claude Sonnet 4.5).

Ingests a counterparty draft, extracts key clauses, compares them to Contoso
Global's enterprise standard (the clause library in the corpus), flags deviations
and returns a risk score with rationale. Built with the **Microsoft Agent
Framework** and runs on Claude for long-context legal reasoning. Reuses the Ch1
grounding pattern, so it's fast to build.

Run:
    python challenge-3/agents/clause_risk_agent.py            # analyze BOTH sample drafts
    python challenge-3/agents/clause_risk_agent.py --draft challenge-0/data/counterparty_drafts/globex_nda_redline.pdf  # one draft
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "challenge-1"))

from clm_common.config import settings, DATA_DIR  # noqa: E402
from clm_common.documents import read_document_text  # noqa: E402
from clm_common.foundry import build_chat_client, run_agent  # noqa: E402

AGENT_NAME = "clause-risk-agent"

# Inbound counterparty drafts analyzed by default (both are full of graded red flags).
SAMPLE_DRAFTS = [
    DATA_DIR / "counterparty_drafts" / "acme_msa_draft.pdf",
    DATA_DIR / "counterparty_drafts" / "globex_nda_redline.pdf",
]

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
- For each deviation classified 'Needs negotiation', cite the negotiation playbook's recommended
  fallback position (the approved counter-position(s) to propose, in order).
- For each High-risk item, state the required approver / escalation per the delegation-of-authority
  matrix (who must sign off, by role/threshold) — never self-approve.
- You are NOT a lawyer and do NOT give legal advice or enforceability opinions — you flag risk for
  human counsel to decide. Recommend human review for anything High risk.
- Output a concise structured summary (clauses table + overall risk + top 3 issues).
"""


def create_agent(model: str | None = None, *, connection_id: str | None = None):
    """Create the Clause & Risk agent grounded on the enterprise clause library."""
    from agent_framework import Agent
    from kb_setup import build_knowledge_tool

    knowledge = build_knowledge_tool(connection_id=connection_id)

    return Agent(
        client=build_chat_client(model or settings.model_clause_risk),  # claude-sonnet-4-5
        name=AGENT_NAME,
        instructions=INSTRUCTIONS,
        tools=[knowledge],
    )


async def _analyze_draft(agent, draft_path) -> None:
    """Read one counterparty draft and run the clause/risk analysis against it."""
    draft_text = read_document_text(str(draft_path))
    prompt = (
        "Analyze the following counterparty draft. Extract clauses, compare to our enterprise "
        "standard, flag deviations, and give an overall risk score with the top 3 issues.\n\n"
        f"=== COUNTERPARTY DRAFT ({Path(draft_path).name}) ===\n{draft_text}"
    )
    print("―" * 80)
    print(f"DRAFT: {Path(draft_path).name}")
    print(await run_agent(agent, prompt))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--draft",
        default=None,
        help=(
            "path to a single counterparty draft to analyze (.pdf or .md). "
            "If omitted, both sample drafts (acme_msa_draft.pdf and globex_nda_redline.pdf) "
            "are analyzed."
        ),
    )
    args = parser.parse_args()

    drafts = [args.draft] if args.draft else SAMPLE_DRAFTS

    agent = create_agent()
    print(f"✓ Built {AGENT_NAME} on model '{settings.model_clause_risk}'\n")
    for draft in drafts:
        await _analyze_draft(agent, draft)


if __name__ == "__main__":
    asyncio.run(main())
