"""Microsoft Agent Framework helpers shared across challenges.

Every CLM agent in this repo is built with the **Microsoft Agent Framework**
(`agent-framework` + `agent-framework-foundry`). Foundry is used as the *chat
client provider*, which keeps the multi-model fleet (Claude + GPT deployments in
one Foundry project) and Foundry IQ / Azure AI Search grounding available while
the agent, tool-calling and orchestration APIs stay provider-agnostic.

The framework is async-first. This module gives challenge scripts one obvious way
to build a client, wrap a plain function as an auto-executed tool, and run a
prompt from either sync or async code:

    from clm_common.foundry import build_chat_client, function_tool, run_prompt
    from agent_framework import Agent

    agent = Agent(
        client=build_chat_client(settings.model_drafting),
        name="intake-drafting-agent",
        instructions=INSTRUCTIONS,
        tools=[function_tool(get_contract_status)],
    )
    print(run_prompt(agent, "Draft a mutual NDA for Acme."))     # sync callers
    text = await run_agent(agent, "…")                           # async callers
"""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Callable

from .config import settings, credential


def build_chat_client(model: str):
    """Return a `FoundryChatClient` bound to a specific model deployment.

    The SAME call backs a Claude agent or a GPT agent — only ``model`` changes,
    which is what lets the microhack run a multi-model fleet inside one Foundry
    project.
    """
    from agent_framework.foundry import FoundryChatClient

    return FoundryChatClient(
        model=model,
        project_endpoint=settings.require_project(),
        credential=credential(),
    )


def function_tool(func: Callable[..., Any]):
    """Wrap a plain Python function as an auto-executing Agent Framework tool.

    The type hints + docstring become the tool's JSON schema. ``approval_mode``
    is ``never_require`` so tools run automatically in these headless scripts;
    use ``always_require`` in an interactive/production app that wants a human to
    approve each call.
    """
    from agent_framework import tool

    return tool(approval_mode="never_require")(func)


async def run_agent(agent, prompt: str, *, session=None) -> str:
    """Run `prompt` on `agent` and return the reply text (async, framework-native)."""
    result = await agent.run(prompt, session=session)
    return result.text


# One event loop per thread. Reusing a live loop across repeated sync calls keeps
# the framework's underlying async HTTP client bound to an open loop (a fresh
# asyncio.run() per call would close the loop and break the next call), while
# per-thread isolation keeps it safe when a harness (e.g. azure-ai-evaluation)
# invokes a target from worker threads.
_local = threading.local()


def _thread_loop() -> asyncio.AbstractEventLoop:
    loop = getattr(_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _local.loop = loop
    return loop


def run_prompt(agent, prompt: str, *, session=None) -> str:
    """Single-turn helper for **sync** callers: run `prompt`, return the reply text."""
    return _thread_loop().run_until_complete(run_agent(agent, prompt, session=session))


def get_project_client():
    """Return an authenticated AIProjectClient for the configured Foundry project.

    Still used to resolve project connections (e.g. the default Azure AI Search
    connection that backs Foundry IQ grounding). Endpoint format:
        https://<resource>.services.ai.azure.com/api/projects/<project>
    """
    from azure.ai.projects import AIProjectClient

    return AIProjectClient(endpoint=settings.require_project(), credential=credential())
