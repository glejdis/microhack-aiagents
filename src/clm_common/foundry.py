"""Foundry client helpers shared across challenges.

Keeps agent boilerplate in one place so challenge scripts stay readable:

    from clm_common.foundry import get_project_client, run_prompt

    with get_project_client() as project:
        agent = project.agents.create_agent(model=..., name=..., instructions=...)
        answer = run_prompt(project.agents, agent.id, "draft an NDA for Acme")
"""
from __future__ import annotations

from .config import settings, credential


def get_project_client():
    """Return an authenticated AIProjectClient for the configured Foundry project.

    Endpoint format:
        https://<resource>.services.ai.azure.com/api/projects/<project>
    """
    from azure.ai.projects import AIProjectClient

    return AIProjectClient(endpoint=settings.require_project(), credential=credential())


def run_prompt(agents_client, agent_id: str, prompt: str, thread_id: str | None = None) -> str:
    """Single-turn helper: post `prompt`, run the agent, return the reply text.

    Reuses `thread_id` if given, otherwise creates a new thread. Returns the last
    agent text message, or a `[run failed: ...]` marker so callers can assert.
    """
    from azure.ai.agents.models import ListSortOrder

    if thread_id is None:
        thread_id = agents_client.threads.create().id

    agents_client.messages.create(thread_id=thread_id, role="user", content=prompt)
    run = agents_client.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)

    if run.status == "failed":
        return f"[run failed: {run.last_error}]"

    messages = agents_client.messages.list(thread_id=thread_id, order=ListSortOrder.ASCENDING)
    last_text = ""
    for msg in messages:
        if msg.role == "assistant" and msg.text_messages:
            last_text = msg.text_messages[-1].text.value
    return last_text
