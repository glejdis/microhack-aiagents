"""Challenge 1 — Foundry IQ / knowledge grounding setup.

Foundry IQ grounds an agent on your corpus. Under the hood the agent uses an
**Azure AI Search** index (built in Challenge 0 by scripts/seed_corpus.py) via
agentic retrieval (plan → search → rerank → cite).

This module resolves the project's default Azure AI Search connection and builds
an `AzureAISearchTool` you can attach to any agent. The SAME code grounds a
Claude-backed agent or a GPT-backed one — Foundry keeps the tool/grounding API
identical across model providers.

Run standalone to verify your connection + index:
    python challenge-1/kb_setup.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clm_common.config import settings  # noqa: E402


def get_search_connection_id(project) -> str:
    """Return the connection id of the project's default Azure AI Search resource."""
    from azure.ai.projects.models import ConnectionType

    conn = project.connections.get_default(ConnectionType.AZURE_AI_SEARCH)
    return conn.id


def build_knowledge_tool(project):
    """Build an AzureAISearchTool over the clm-corpus index (the Foundry IQ knowledge base)."""
    from azure.ai.agents.models import AzureAISearchQueryType, AzureAISearchTool

    connection_id = get_search_connection_id(project)
    return AzureAISearchTool(
        index_connection_id=connection_id,
        index_name=settings.search_index,
        query_type=AzureAISearchQueryType.SEMANTIC,
        top_k=5,
    )


def main() -> None:
    from clm_common.foundry import get_project_client

    with get_project_client() as project:
        conn_id = get_search_connection_id(project)
        print("✓ Default Azure AI Search connection:", conn_id)
        print("✓ Index:", settings.search_index)
        tool = build_knowledge_tool(project)
        print("✓ Built AzureAISearchTool with", len(tool.definitions), "tool definition(s).")


if __name__ == "__main__":
    main()
