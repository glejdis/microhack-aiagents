"""Challenge 2 — Tracing / observability setup.

Turns on OpenTelemetry for the Azure AI Agents SDK and ships spans to
Application Insights, so you can inspect prompt / retrieval / tool spans in the
Foundry portal (Tracing + Agent Monitoring Dashboard). Traces span BOTH the
Claude and GPT agents — one pane of glass across providers.

IMPORTANT: content-recording env var must be set BEFORE importing the agents
SDK, so import this module (or call enable_tracing()) at the very top of your
entry point.

Usage:
    import tracing_setup            # sets the env flag on import
    tracing_setup.enable_tracing()  # wires the exporter (call once at startup)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Must be set before azure.ai.agents is imported anywhere.
os.environ.setdefault("AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED", "true")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clm_common.config import settings  # noqa: E402

_ENABLED = False


def enable_tracing(project=None) -> None:
    """Configure Azure Monitor + instrument the Agents SDK. Safe to call once.

    :param project: optional AIProjectClient — used to fetch the App Insights
        connection string from the project if it isn't already in the env.
    """
    global _ENABLED
    if _ENABLED:
        return

    conn = settings.appinsights_connection_string
    if not conn and project is not None:
        conn = project.telemetry.get_application_insights_connection_string()

    if not conn:
        print("⚠️  No Application Insights connection string. Set "
              "APPLICATIONINSIGHTS_CONNECTION_STRING in .env (Challenge 0 sets this).")
        return

    from azure.monitor.opentelemetry import configure_azure_monitor
    from azure.ai.agents.telemetry import AIAgentsInstrumentor

    configure_azure_monitor(connection_string=conn)
    AIAgentsInstrumentor().instrument()
    _ENABLED = True
    print("✓ Tracing enabled → Application Insights (content recording ON).")


if __name__ == "__main__":
    from clm_common.foundry import get_project_client

    with get_project_client() as project:
        enable_tracing(project)
        print("Run an agent now; open Foundry portal → Tracing to see spans.")
