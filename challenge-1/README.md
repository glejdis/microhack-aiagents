# Challenge 1 · Grounded Agent with Foundry IQ + Tools

> **Duration:** 60 min · **Prerequisites:** Challenge 0 complete (`.env` populated, corpus seeded,
> smoke test green).

## 🎯 Objective

Build the **Intake & Drafting agent** on **Anthropic Claude Sonnet 4.5** and make it: **grounded**
(answers from the CLM corpus), **cited**, **tool-enabled** (a function tool for contract status),
and **guard-railed** (refuses legal advice).

## 🧭 Context

**Foundry IQ** is how you ground an agent on your knowledge. The chain is:

```
corpus (Blob)  →  Azure AI Search index (built in Ch0)  →  knowledge base  →  agent tool
                         (agentic retrieval: plan → search → rerank → cite)
```

You attach that knowledge base to the agent as a tool (`AzureAISearchTool`), plus a **function
tool** (`get_contract_status`) for structured lookups. The agent runs on **Claude** simply by
pointing `model` at the `claude-sonnet-4-5` deployment — **the agent/tool/grounding API is identical
across providers**, which is the whole point of Foundry as a model-agnostic control plane.

## ✅ Tasks

1. **Verify the knowledge connection** resolves and the index is present:
   ```bash
   python challenge-1/kb_setup.py
   ```
   You should see the default Azure AI Search connection id and the `clm-corpus` index.

2. **Read the agent definition** in `agents/intake_drafting_agent.py`. Note:
   - `model=settings.model_drafting` → **Claude Sonnet 4.5**,
   - the persona + **refusal** instructions,
   - grounding via `build_knowledge_tool(project)` and the `get_contract_status` **FunctionTool**,
   - `enable_auto_function_calls(toolset)` so the function runs automatically during a run.

3. **Run the agent** end-to-end (creates the agent, runs four demo prompts, then deletes it):
   ```bash
   python challenge-1/agents/intake_drafting_agent.py
   # keep it for later challenges / the portal:
   python challenge-1/agents/intake_drafting_agent.py --keep
   ```

4. **Exercise every capability** with `sample_prompts.md` — a draft, a cited Q&A, a `CT-4821`
   status lookup, and a legal-advice prompt that must be refused.

5. **(Optional) Add content safety.** In the portal, attach **Prompt Shields / PII** guardrails to
   the agent, or discuss where they'd sit. The refusal instructions already cover the no-legal-advice
   policy at the prompt layer.

## ✔️ Success criteria

- Cited answers drawn from the corpus (you can see the source documents).
- The `get_contract_status` tool is invoked for `CT-4821` and returns real fields.
- The legal-advice prompt is **refused** with a recommendation to consult counsel.
- The agent is running on the **Claude** deployment (confirm the model name in the portal).

## 🚀 Go Further

- Add a **Web IQ (Bing)** grounding tool for external/regulatory lookups.
- Add a second knowledge base scoped to a single contract type and compare retrieval quality.
- Tighten the persona so drafts always include a "⚠️ requires human review" banner.

## 🛠️ Troubleshooting

| Symptom | Fix |
|---------|-----|
| `get_default(AZURE_AI_SEARCH)` returns nothing | Ensure Ch0 created the Search resource and it's connected to the project (portal → Connected resources). Set `AZURE_SEARCH_CONNECTION_NAME` in `.env`. |
| No citations returned | Confirm `scripts/seed_corpus.py` populated the index and the semantic config exists; raise `top_k`. |
| Function tool never called | Keep the docstring + type hints (the schema comes from them); ensure `enable_auto_function_calls(toolset)` ran. |
| Run status `failed` on Claude | See the fallback below — the Agent runner may not yet host Claude in your region. |

### ⚙️ Claude fallback (if the Agent runner can't host Claude in your region)

The **preferred** path is `model="claude-sonnet-4-5"` on `create_agent`, exactly like GPT. If that
run fails because the Agent Service runner doesn't support Anthropic models in your region yet, call
Claude **directly** through Foundry with the Anthropic SDK, and keep grounding/tools in your own code:

```python
from anthropic import AnthropicFoundry           # pip: anthropic (already in requirements.txt)
from clm_common.config import settings, credential

token = credential().get_token("https://cognitiveservices.azure.com/.default").token
client = AnthropicFoundry(
    base_url=settings.project_endpoint.split("/api/projects")[0],   # the AI Services endpoint
    api_key=token,                                                  # Entra token as bearer
)
msg = client.messages.create(
    model=settings.model_drafting,
    max_tokens=1024,
    messages=[{"role": "user", "content": "Draft a mutual NDA…"}],
)
print(msg.content[0].text)
```

You'd then do retrieval (Azure AI Search) and the contract-status lookup yourself and pass results
into the prompt. Prefer the native agent path when available — this is only a safety net.

## 🧠 Reflection

- Why put **drafting** on Claude and **routing** on GPT? (Instruction-following & long-context legal
  reasoning vs fast deterministic tool-calling.)
- Where should guardrails live — in the prompt, as a content-safety policy, or both? What does each
  catch that the other misses?

➡️ Next: **[Challenge 2 — Observability, Tracing & Evaluation](../challenge-2/)**
