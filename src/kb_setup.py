"""Challenge 2 — Foundry IQ / knowledge grounding setup.

Foundry IQ grounds an agent on your corpus. Under the hood the agent uses an
**Azure AI Search** index (built in Challenge 1 by src/scripts/seed_corpus.py, which
crawls the SharePoint contract library with a SharePoint Online indexer) via
agentic retrieval (plan → search → rerank → cite).

This module resolves the project's default Azure AI Search connection and builds
the Foundry Azure AI Search tool you can attach to any Microsoft Agent Framework
agent. The SAME code grounds a Claude-backed agent or a GPT-backed one — Foundry
keeps the tool/grounding API identical across model providers.

Run standalone to verify your connection + index:
    python src/kb_setup.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # src (clm_common)

from clm_common.config import settings  # noqa: E402


def get_search_connection_id(project) -> str:
    """Return the connection id of the project's default Azure AI Search resource."""
    from azure.ai.projects.models import ConnectionType

    conn = project.connections.get_default(ConnectionType.AZURE_AI_SEARCH)
    return conn.id


def build_knowledge_tool(*, connection_id: str | None = None, project=None):
    """Build the Foundry Azure AI Search grounding tool over the clm-corpus index.

    Pass ``connection_id`` to skip resolution (cheap, no network — handy when
    rebuilding the tool per call), or ``project`` to resolve it from an existing
    AIProjectClient. With neither, a short-lived project client is opened to look
    up the default Azure AI Search connection.

    Returns a Foundry tool object ready to drop into an ``Agent``'s ``tools=[...]``.
    """
    from agent_framework.foundry import FoundryChatClient

    if connection_id is None:
        if project is not None:
            connection_id = get_search_connection_id(project)
        else:
            from clm_common.foundry import get_project_client

            with get_project_client() as own_project:
                connection_id = get_search_connection_id(own_project)

    return FoundryChatClient.get_azure_ai_search_tool(
        index_connection_id=connection_id,
        index_name=settings.search_index,
        query_type="semantic",
        top_k=5,
    )


def get_bing_connection_id(project) -> str:
    """Return the connection id of the Grounding-with-Bing-Search connection.

    Resolved by NAME (``AZURE_BING_CONNECTION_NAME``) because Foundry has no
    dedicated Bing connection *type* — a Grounding with Bing Search resource
    surfaces as a generic project connection. Raises if the name is unset.
    """
    if not settings.bing_connection_name:
        raise RuntimeError(
            "AZURE_BING_CONNECTION_NAME is not set. Provision a 'Grounding with Bing "
            "Search' resource, add it as a project connection, then set the env var "
            "(or set AZURE_BING_CONNECTION_ID directly)."
        )
    return project.connections.get(name=settings.bing_connection_name).id


def build_web_search_tool(*, connection_id: str | None = None, project=None):
    """Build the Foundry web-grounding tool (Grounding with Bing Search), or None.

    This is the SINGLE place web grounding is constructed for the whole repo. When
    you get Web IQ access, swap ONLY this function's body to return the Web IQ tool
    and every agent picks it up unchanged — no agent or config edits needed.

    Returns ``None`` when no Bing connection is configured (``web_search_enabled``
    is False), so agents stay runnable with zero web setup. Pass ``connection_id``
    to skip resolution, or ``project`` to resolve from an existing AIProjectClient;
    with neither, a short-lived project client resolves the connection by name.
    """
    if not settings.web_search_enabled:
        return None

    from agent_framework.foundry import FoundryChatClient

    connection_id = connection_id or settings.bing_connection_id
    if connection_id is None:
        if project is not None:
            connection_id = get_bing_connection_id(project)
        else:
            from clm_common.foundry import get_project_client

            with get_project_client() as own_project:
                connection_id = get_bing_connection_id(own_project)

    # Grounding with Bing Search (preview) — works on non-OpenAI Foundry models
    # (the Claude specialists) and exposes finer Bing params than the GA
    # get_web_search_tool (which is Azure-OpenAI-only).
    return FoundryChatClient.get_bing_grounding_tool(
        connection_id=connection_id,
        count=5,
    )


def main() -> None:
    from clm_common.foundry import get_project_client

    with get_project_client() as project:
        conn_id = get_search_connection_id(project)
        print("✓ Default Azure AI Search connection:", conn_id)
        print("✓ Index:", settings.search_index)
        build_knowledge_tool(connection_id=conn_id)
        print("✓ Built Foundry Azure AI Search grounding tool (semantic, top_k=5).")
        if settings.web_search_enabled:
            build_web_search_tool(project=project)
            print("✓ Built Foundry web-grounding tool (Grounding with Bing Search).")
        else:
            print("• Web search off (set AZURE_BING_CONNECTION_NAME to enable).")


if __name__ == "__main__":
    main()
