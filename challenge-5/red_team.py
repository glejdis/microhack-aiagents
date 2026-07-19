"""Challenge 5 (BONUS) — automated red-teaming with the AI Red Teaming Agent.

Runs Foundry's **AI Red Teaming Agent** (`azure-ai-evaluation` red_team) against
the CLM agent: it auto-generates adversarial attack objectives across risk
categories, mutates them with attack strategies (encodings, ciphers, jailbreak
templates), sends them to your agent, and scores how often the agent produced
unsafe output — an **attack success rate** scorecard.

The target is a plain callback that wraps the Intake & Drafting agent (Claude),
so we red-team the SAME agent you shipped in Challenge 1.

Run (scan is async; this wraps it):
    python challenge-5/red_team.py                       # quick scan (baseline)
    python challenge-5/red_team.py --strategies          # add easy/moderate attack strategies
    python challenge-5/red_team.py --num-objectives 3 --output redteam_scorecard.json

Requires: `pip install "azure-ai-evaluation[redteam]"` (pulls PyRIT) and an
Azure AI (Foundry) project + login. See requirements.txt.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "challenge-1"))

from clm_common.config import settings, credential  # noqa: E402


def build_agent_target():
    """Return (callback, cleanup). The callback maps a query string → the agent's reply.

    The AI Red Teaming Agent calls `callback(query)` for every attack prompt.
    """
    from clm_common.foundry import get_project_client, run_prompt
    from intake_drafting_agent import create_agent

    project = get_project_client()
    agent = create_agent(project)

    def callback(query: str) -> str:
        try:
            return run_prompt(project.agents, agent.id, query)
        except Exception as exc:  # noqa: BLE001 — never crash the scan on one prompt
            return f"[agent error: {exc}]"

    def cleanup() -> None:
        try:
            project.agents.delete_agent(agent.id)
        finally:
            project.close()

    return callback, cleanup


async def run_scan(num_objectives: int, use_strategies: bool, output_path: str | None) -> None:
    from azure.ai.evaluation.red_team import RedTeam, RiskCategory, AttackStrategy

    agent = RedTeam(
        azure_ai_project=settings.require_project(),  # Foundry project endpoint
        credential=credential(),
        risk_categories=[
            RiskCategory.Violence,
            RiskCategory.HateUnfairness,
            RiskCategory.Sexual,
            RiskCategory.SelfHarm,
        ],
        num_objectives=num_objectives,
    )

    callback, cleanup = build_agent_target()
    scan_kwargs: dict = {"target": callback}
    if use_strategies:
        # Layered strategies: baseline + text mutations + a composed encoding attack.
        scan_kwargs["attack_strategies"] = [
            AttackStrategy.EASY,
            AttackStrategy.MODERATE,
            AttackStrategy.CharacterSpace,
            AttackStrategy.ROT13,
            AttackStrategy.Compose([AttackStrategy.Base64, AttackStrategy.ROT13]),
        ]
    if output_path:
        scan_kwargs["output_path"] = output_path

    print(f"▶ Red-teaming '{settings.model_drafting}' agent — "
          f"{num_objectives} objective(s)/category, strategies={'on' if use_strategies else 'baseline'}")
    try:
        result = await agent.scan(**scan_kwargs)
    finally:
        cleanup()

    print("\n=== Red-team scorecard ===")
    print(result)
    if output_path:
        print(f"\n✓ Full scorecard written to {output_path}")
    print("\nInterpretation: lower attack-success-rate = safer. Investigate any category > 0% and "
          "add the guardrails from safety_eval.py / the portal, then re-scan.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-objectives", type=int, default=2,
                        help="attack objectives per risk category (default 2; raise for coverage)")
    parser.add_argument("--strategies", action="store_true",
                        help="apply attack strategies (encodings/ciphers) on top of baseline")
    parser.add_argument("--output", default="challenge-5/redteam_scorecard.json",
                        help="path for the JSON scorecard")
    args = parser.parse_args()
    asyncio.run(run_scan(args.num_objectives, args.strategies, args.output))


if __name__ == "__main__":
    main()
