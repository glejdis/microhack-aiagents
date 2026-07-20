"""Challenge 2 — evaluation + Claude-vs-GPT bake-off + quality gate.

Runs the Foundry `azure-ai-evaluation` evaluators over
data/evaluation/evaluation_dataset.jsonl, using a *target* callable that
generates the agent's response for each row. Then it does the headline
**cross-model bake-off**: run the Intake & Drafting agent on **Claude Sonnet
4.5** vs a **GPT** deployment against the SAME scorecard, and compare quality vs
cost/latency. Finally, a **quality gate** fails the build if groundedness drops
below a threshold.

Usage:
    python challenge-2/evaluators.py                 # evaluate Claude (default)
    python challenge-2/evaluators.py --bakeoff       # Claude vs GPT comparison
    python challenge-2/evaluators.py --gate 4.0      # fail if mean groundedness < 4.0
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Enable tracing before importing the agents SDK (import has the side effect).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tracing_setup  # noqa: E402,F401  (sets content-recording env flag)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "challenge-1"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "challenge-1" / "agents"))

from clm_common.config import settings, DATA_DIR  # noqa: E402
from clm_common.foundry import build_chat_client, function_tool, get_project_client, run_prompt  # noqa: E402

DATASET = DATA_DIR / "evaluation" / "evaluation_dataset.jsonl"


def judge_model_config():
    """AzureOpenAIModelConfiguration for the LLM judge (an Azure OpenAI GPT deployment).

    Reads AZURE_OPENAI_* if present, otherwise derives the endpoint from the
    Foundry project and uses the orchestrator GPT deployment as the judge.
    """
    from azure.ai.evaluation import AzureOpenAIModelConfiguration

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint and settings.project_endpoint:
        # AI Services base endpoint also serves the Azure OpenAI surface.
        endpoint = settings.project_endpoint.split("/api/projects")[0]
    return AzureOpenAIModelConfiguration(
        azure_endpoint=endpoint,
        azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", settings.model_orchestrator),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),  # None → SDK uses AAD
    )


def build_target(model: str, connection_id: str):
    """Create an Intake & Drafting agent target on `model` and return a (fn, meta) pair.

    The returned callable maps a `query` to the agent's `response`, and records
    latency so the bake-off can compare cost/latency alongside quality. The agent
    is built once per worker thread (via thread-local storage) so the evaluation
    harness can invoke the target concurrently without sharing an event loop.
    """
    import threading

    from intake_drafting_agent import INSTRUCTIONS
    from agent_framework import Agent
    from clm_common.tools import get_contract_status
    from kb_setup import build_knowledge_tool

    meta = {"latencies": []}
    tls = threading.local()

    def _agent():
        agent = getattr(tls, "agent", None)
        if agent is None:
            agent = Agent(
                client=build_chat_client(model),
                name=f"eval-intake-{model}",
                instructions=INSTRUCTIONS,
                tools=[
                    build_knowledge_tool(connection_id=connection_id),
                    function_tool(get_contract_status),
                ],
            )
            tls.agent = agent
        return agent

    def target(query: str, **_: object) -> dict:
        start = time.perf_counter()
        response = run_prompt(_agent(), query)
        meta["latencies"].append(time.perf_counter() - start)
        return {"response": response}

    return target, meta


def evaluators_dict():
    from azure.ai.evaluation import (
        GroundednessEvaluator,
        RelevanceEvaluator,
        CoherenceEvaluator,
        FluencyEvaluator,
    )

    cfg = judge_model_config()
    return {
        "groundedness": GroundednessEvaluator(model_config=cfg),
        "relevance": RelevanceEvaluator(model_config=cfg),
        "coherence": CoherenceEvaluator(model_config=cfg),
        "fluency": FluencyEvaluator(model_config=cfg),
    }


def run_eval(model: str, connection_id: str) -> dict:
    """Evaluate the agent on `model` over the dataset; return the metrics summary."""
    from azure.ai.evaluation import evaluate

    target, meta = build_target(model, connection_id)
    result = evaluate(
        data=str(DATASET),
        target=target,
        evaluators=evaluators_dict(),
        evaluator_config={
            "default": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${target.response}",
                    "context": "${data.context}",
                    "ground_truth": "${data.ground_truth}",
                }
            }
        },
    )

    metrics = dict(result.get("metrics", {}))
    lat = meta["latencies"]
    metrics["_mean_latency_s"] = round(sum(lat) / len(lat), 2) if lat else None
    metrics["_model"] = model
    return metrics


def print_scorecard(title: str, metrics: dict) -> None:
    print(f"\n=== {title} ({metrics.get('_model')}) ===")
    for k, v in sorted(metrics.items()):
        if k.startswith("_"):
            continue
        print(f"  {k:<40} {v}")
    print(f"  {'mean latency (s)':<40} {metrics.get('_mean_latency_s')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bakeoff", action="store_true", help="compare Claude vs GPT")
    parser.add_argument("--gate", type=float, default=None,
                        help="fail if mean groundedness < THRESHOLD (e.g. 4.0)")
    args = parser.parse_args()

    if not DATASET.exists():
        print(f"✗ Missing dataset: {DATASET}")
        return 1

    from kb_setup import get_search_connection_id

    with get_project_client() as project:
        tracing_setup.enable_tracing(project)
        connection_id = get_search_connection_id(project)

    claude = run_eval(settings.model_drafting, connection_id)
    print_scorecard("Intake & Drafting", claude)

    gpt = None
    if args.bakeoff:
        gpt = run_eval(settings.model_orchestrator, connection_id)
        print_scorecard("Intake & Drafting", gpt)
        print("\n--- Bake-off (Claude vs GPT) ---")
        keys = [k for k in claude if not k.startswith("_")]
        for k in sorted(keys):
            print(f"  {k:<40} claude={claude.get(k)}   gpt={gpt.get(k)}")
        print(f"  {'mean latency (s)':<40} claude={claude['_mean_latency_s']}   "
              f"gpt={gpt['_mean_latency_s']}")

    if args.gate is not None:
        score = claude.get("groundedness.groundedness") or claude.get("groundedness")
        print(f"\nQuality gate: groundedness={score} threshold={args.gate}")
        if score is None:
            print("⚠️  Could not read groundedness metric — check evaluator output keys.")
            return 2
        if float(score) < args.gate:
            print("❌ GATE FAILED — groundedness below threshold. Blocking release.")
            return 3
        print("✅ GATE PASSED.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
