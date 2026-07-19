"""Challenge 1 — Intake & Drafting agent (Anthropic Claude Sonnet 4.5).

Builds a grounded, cited, tool-enabled, guard-railed agent that:
  • drafts NDA/MSA/SOW from APPROVED templates in the corpus,
  • answers questions about clauses/policies with citations (Foundry IQ),
  • calls the `get_contract_status` function tool for structured lookups,
  • REFUSES to give legal advice (guardrail).

The agent runs on the **Claude Sonnet 4.5** deployment (MODEL_DRAFTING). Note how
the Foundry Agents API is identical to a GPT agent — only the `model` changes.

Run:
    python challenge-1/agents/intake_drafting_agent.py            # interactive demo
    python challenge-1/agents/intake_drafting_agent.py --keep     # leave the agent in the project
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # for kb_setup

from clm_common.config import settings  # noqa: E402
from clm_common.foundry import get_project_client, run_prompt  # noqa: E402
from clm_common.tools import get_contract_status  # noqa: E402

AGENT_NAME = "intake-drafting-agent"

INSTRUCTIONS = """\
You are the Intake & Drafting agent for Contoso Global's Legal & Procurement team.

WHAT YOU DO
- Draft NDAs, MSAs and SOWs using ONLY the approved templates and clause library in your knowledge
  base. Fill placeholders with the details the user provides; never invent legal terms.
- Answer questions about clauses, policies and standards using your knowledge base, and ALWAYS cite
  the source documents you used.
- When asked about a specific contract's status, renewal date, risk or owner, call the
  `get_contract_status` tool. Do not guess these facts.

GROUNDING & CITATIONS
- Base every substantive answer on retrieved corpus content. If the corpus does not contain the
  answer, say so plainly rather than speculating.

GUARDRAILS (must follow)
- You are NOT a lawyer and must NOT provide legal advice, legal opinions, or predictions about
  litigation/enforceability. If asked, refuse briefly and recommend review by qualified counsel.
- Do not disclose personal data or content outside the approved corpus.
- Keep a professional, concise tone. Flag anything that deviates from company policy for human review.
"""


def create_agent(project):
    """Create the Intake & Drafting agent with knowledge grounding + a function tool."""
    from azure.ai.agents.models import FunctionTool, ToolSet
    from kb_setup import build_knowledge_tool

    knowledge = build_knowledge_tool(project)
    functions = FunctionTool(functions={get_contract_status})

    toolset = ToolSet()
    toolset.add(knowledge)
    toolset.add(functions)

    # Auto-run local function tools during runs.create_and_process.
    project.agents.enable_auto_function_calls(toolset)

    agent = project.agents.create_agent(
        model=settings.model_drafting,  # claude-sonnet-4-5
        name=AGENT_NAME,
        instructions=INSTRUCTIONS,
        toolset=toolset,
    )
    return agent


DEMO_PROMPTS = [
    "Draft a mutual NDA between Contoso Global and Acme Corp for a 2-year term.",
    "What does our standard limitation-of-liability clause say, and what's the cap?",
    "What is the status and renewal date of contract CT-4821?",
    "Should we sue Acme for breach — will we win in court?",  # must be refused
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", action="store_true", help="do not delete the agent afterwards")
    args = parser.parse_args()

    with get_project_client() as project:
        agent = create_agent(project)
        print(f"✓ Created {AGENT_NAME} (id={agent.id}) on model '{settings.model_drafting}'\n")
        try:
            thread_id = project.agents.threads.create().id
            for prompt in DEMO_PROMPTS:
                print("―" * 80)
                print("USER:", prompt)
                answer = run_prompt(project.agents, agent.id, prompt, thread_id=thread_id)
                print("AGENT:", answer, "\n")
        finally:
            if not args.keep:
                project.agents.delete_agent(agent.id)
                print("(agent deleted — pass --keep to retain it for Challenge 2)")
            else:
                print(f"(kept agent {agent.id} — set INTAKE_AGENT_ID={agent.id} for later challenges)")


if __name__ == "__main__":
    main()
