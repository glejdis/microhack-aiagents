# Challenge 1 · Grounded Agent with Foundry IQ + Tools

Welcome to your first agent! In Challenge 0 you provisioned Microsoft Foundry and seeded the
**Contoso Global** contract corpus. Now you'll turn that corpus into a working assistant: the
**Intake & Drafting agent** — a grounded, cited, tool-enabled, guard-railed agent that drafts
contracts from approved templates and answers policy questions **with sources**. It runs on
**Anthropic Claude Sonnet 4.5**, and the twist you'll internalize here is that grounding it on Claude
takes the *exact same code* as grounding it on GPT — because Foundry is a **model-agnostic control
plane**.

If something isn't working as expected, please let your coach know.

> **⏱️ Duration:** ~60 min

> **📋 Prerequisites:**
> - **Challenge 0 complete** — `.env` populated, corpus seeded into Azure AI Search, smoke test green.
> - A model deployment for **`claude-sonnet-4-5`** (created in Challenge 0) reachable from your project.

> 🧩 **How to use this challenge:** the code in this folder is a **complete, working reference
> implementation** — you're not building it from a blank file. **Run it, read it, and understand *why*
> it works**, then take it further with **🚀 Go Further**. Stuck? The code *is* the answer key.

---

## 🎯 Objective

Build the **Intake & Drafting agent** on **Anthropic Claude Sonnet 4.5** and make it:

- **Grounded** — every substantive answer is drawn from the CLM corpus via **Foundry IQ**, not the
  model's parametric memory.
- **Cited** — answers reference the source documents they came from.
- **Tool-enabled** — a **function tool** (`get_contract_status`) performs structured lookups the model
  must not guess.
- **Guard-railed** — the agent **refuses** to give legal advice and flags policy deviations for human
  review.

## 🧩 What you'll build

| Component | What it is | Where it lives |
|-----------|-----------|----------------|
| **Knowledge tool (Foundry IQ)** | An `AzureAISearchTool` over the `clm-corpus` index — grounds the agent on Contoso's templates, clauses, policy and contracts | [`kb_setup.py`](kb_setup.py) → `build_knowledge_tool()` |
| **Function tool** | `get_contract_status(contract_id)` — deterministic lookup of status, renewal date, risk and owner (Azure SQL, falling back to seed JSON) | [`src/clm_common/tools.py`](../src/clm_common/tools.py) |
| **Guard-railed persona** | Instructions that force citations, forbid invented terms, and refuse legal advice | `INSTRUCTIONS` in [`agents/intake_drafting_agent.py`](agents/intake_drafting_agent.py) |
| **Claude-backed agent** | The same Agent Framework API as GPT, with `model` pointed at the Claude deployment | `create_agent()` in [`agents/intake_drafting_agent.py`](agents/intake_drafting_agent.py) |
| **A repeatable demo** | Builds the agent, runs four prompts (draft · cited Q&A · tool call · refusal) in one session | `main()` in [`agents/intake_drafting_agent.py`](agents/intake_drafting_agent.py) |

## 🧭 Context and Background

### How grounding works — the Foundry IQ chain

**Foundry IQ** is how you ground an agent on *your* knowledge. You never hand the model a pile of
documents; instead you attach a **knowledge base** as a **tool**, and the agent performs **agentic
retrieval** — it plans sub-queries, searches, reranks, and returns **cited** passages — during a run.

```mermaid
flowchart LR
  A["Corpus in Blob Storage<br/>templates · clauses · policy · contracts"] --> B["Azure AI Search index<br/>clm-corpus · semantic"]
  B --> C["Foundry IQ<br/>knowledge base"]
  C --> D["AzureAISearchTool<br/>(kb_setup.py)"]
  D --> E["Intake &amp; Drafting agent<br/>Claude Sonnet 4.5"]
  F["get_contract_status<br/>function tool"] --> E
  E --> G["Cited draft / answer<br/>+ tool results"]
  style E fill:#EDE4F5,stroke:#7A4FB5,stroke-width:2px
  style D fill:#FCEBDD,stroke:#E8590C,stroke-width:2px
  style F fill:#FCEBDD,stroke:#E8590C,stroke-width:2px
```

The index itself was built in **Challenge 0** by `scripts/seed_corpus.py`. In this challenge you
simply **attach it** as a tool and let the agent retrieve from it.

### Two kinds of tools

An agent grounds and acts through **tools**. This agent has both flavors:

- **Knowledge tool** (`AzureAISearchTool`) — for *unstructured* knowledge: "what does our standard
  limitation-of-liability clause say?" Answered from the corpus, **with citations**.
- **Function tool** (`get_contract_status`) — for *structured* facts the model must never hallucinate:
  "what's the renewal date of `CT-4821`?" The Agent Framework generates the tool's JSON schema **from the
  Python type hints + docstring**, and `function_tool(...)` (`approval_mode="never_require"`) runs the
  function automatically mid-run.

> [!NOTE]
> Because the schema is derived from the function signature and docstring, **keeping good type hints
> and a clear docstring is not optional** — they *are* the tool contract the model sees.

### Why Claude here — and why the API doesn't change

Drafting rewards strong instruction-following and long-context legal reasoning, so the Intake &
Drafting agent runs on **Claude Sonnet 4.5** (`MODEL_DRAFTING`). The whole point of Foundry as a
control plane is that you get there by pointing `model` at the Claude deployment — **the
agent/tool/grounding API is identical across providers**. The same `Agent(client=..., tools=[...]) →
run` shape hosts a GPT agent (you'll see that in Challenge 3's orchestrator) with no other changes.

### Guardrails at the prompt layer

The `INSTRUCTIONS` block encodes Contoso's policy: never invent legal terms, always cite, call the
tool for contract facts, and **refuse legal advice** (recommend qualified counsel instead). That's
the first line of defense; content-safety policies (Challenge 5) add a second, independent one.

### The knowledge base — what actually grounds the agent

Everything the agent "knows" comes from the corpus you seeded in Challenge 0:

| Corpus source | Contents | Role in Challenge 1 |
|---------------|----------|---------------------|
| [`challenge-0/data/contract_templates/`](../challenge-0/data/contract_templates/) | Approved **NDA / MSA / SOW** templates (PDF) | Drafting source — the agent fills placeholders, never invents terms |
| [`challenge-0/data/clause_library/`](../challenge-0/data/clause_library/) | Enterprise-standard positions **CL-01…CL-12** (PDF) | Cited answers about standard clauses (e.g. the liability cap) |
| [`challenge-0/data/policies/`](../challenge-0/data/policies/) | Approval thresholds + the **no-legal-advice** rule (plus a delegation-of-authority matrix) | Grounds policy answers; reinforces the guardrail |
| [`challenge-0/data/contracts/`](../challenge-0/data/contracts/) | **5 executed contract PDFs** (text-extractable) | Grounding + narrative basis for status lookups |
| [`challenge-0/data/contracts_seed.json`](../challenge-0/data/contracts_seed.json) | Structured metadata for the same 5 contracts | Backs `get_contract_status` (SQL fallback) |

### Files in this challenge

| File | What it does |
|------|--------------|
| [`kb_setup.py`](kb_setup.py) | Resolves the project's **default Azure AI Search connection** and builds the `AzureAISearchTool` (the Foundry IQ knowledge base). Run it standalone to verify grounding is wired up. |
| [`agents/intake_drafting_agent.py`](agents/intake_drafting_agent.py) | Defines the agent (persona, guardrails, knowledge + function tools) and runs a four-prompt demo. Agents are built in-process — nothing persists server-side. |
| [`sample_prompts.md`](sample_prompts.md) | Curated prompts that exercise every capability: grounded drafting, cited Q&A, the function tool, and the refusal guardrail. |

## 🧰 Services & models in this challenge

This agent is small, but every line stands on a concrete resource — the exact ones `azd up` provisioned in
Challenge 0 ([`challenge-0/infra/resources.bicep`](../challenge-0/infra/resources.bicep)). Here's **what
each is**, the **specifics wired into this repo**, and **why it's in the architecture**.

### Microsoft Foundry — AI Services account + model runtime

**What it is:** the managed **control plane + model runtime**. Challenge 0 creates one
`Microsoft.CognitiveServices` account (`kind: AIServices`, SKU `S0`) holding a project **`clm-project`**;
your `.env` reaches it through `AZURE_AI_PROJECT_ENDPOINT`
(`https://<account>.services.ai.azure.com/api/projects/clm-project`).

- **All three models deploy onto that one account** — `gpt-4.1`, `gpt-4o-mini`, `claude-sonnet-4-5` — so a
  single `get_project_client()` ([`src/clm_common/foundry.py`](../src/clm_common/foundry.py)) reaches each.
- The **Microsoft Agent Framework** (`Agent(client=FoundryChatClient(...))`) runs the agent loop **in your
  process** — planning, tool-calls and retrieval — calling Foundry for model inference.
- The project also owns the grounding **`clm-search` connection** and the RBAC that makes retrieval keyless.

**Why here:** you build a grounded, tool-using **Claude** agent in ~15 lines, and moving to GPT is a
one-argument change (`model=`). → [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/overview/agent-framework-overview)

### Foundry IQ — agentic retrieval (`AzureAISearchTool`)

**What it is:** the **grounding layer**. [`kb_setup.py`](kb_setup.py) resolves the project's default Search
connection and builds `AzureAISearchTool(index_name="clm-corpus", query_type=SEMANTIC, top_k=5)`; you attach
it as a tool and the agent runs **plan → search → rerank → cite** during a run.

- Rides the project → Search connection **`clm-search`** (`category: CognitiveSearch`, **AAD** auth, shared).
- The Foundry account's **managed identity** holds **Search Index Data Reader**, so retrieval needs no keys.
- Returns the **top 5** semantically-reranked passages **with citations** — not one raw similarity hit.

**Why here:** it's what makes answers come from **Contoso's corpus, with sources**, not model memory.
→ [Agentic retrieval](https://learn.microsoft.com/azure/search/search-agentic-retrieval-concept)

### Azure AI Search — the `clm-corpus` index

**What it is:** the **retrieval engine** behind Foundry IQ. Challenge 0 provisions a **`basic`** search
service (1 partition · 1 replica, `semanticSearch: free`), and `scripts/seed_corpus.py` **pushes** the
documents in with `SearchClient.upload_documents` (no indexer).

- Index **`clm-corpus`**, semantic config **`clm-semantic`**, fields `id` · `title` · `content` · `source`.
- **Full-text + semantic (L2) re-ranking** over **one document per source file** (`source` = the subfolder).
- Built once in Ch0 — here you only **attach** and query it.

**Why here:** it's the searchable store that turns "the model guesses" into "the agent cites `CL-04`".
→ [Azure AI Search](https://learn.microsoft.com/azure/search/)

### Azure Blob Storage — corpus source of truth

**What it is:** the **object store** the raw documents land in before indexing. Ch0 creates a `Standard_LRS`
`StorageV2` account (blob public access **off**, TLS 1.2) with a **`clm-corpus`** container.

- `seed_corpus.py` uploads each file as `{subfolder}/{name}` (e.g. `contracts/CT-4821_msa.pdf`), `overwrite=True`.
- The Foundry account MI gets **Storage Blob Data Reader**; the deploying user gets **…Data Contributor** to seed.

**Why here:** it holds the templates, clause library, policy and executed-contract PDFs that Search indexes.
→ [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction)

### Model — Anthropic Claude Sonnet 4.5

**What it is:** this agent's LLM — deployment **`claude-sonnet-4-5`** (`format: Anthropic`, **version `2`** =
Azure-hosted, SKU `GlobalStandard`, capacity 20), read from `settings.model_drafting` (`MODEL_DRAFTING`).

- Strong **instruction-following** + **long-context** reasoning — ideal for careful legal drafting.
- Called through the **same Agents API** as the GPT deployments; only the deployment name differs.

**Why here:** drafting goes to Claude; routing/tool-calling to **`gpt-4.1`** (Ch3) and the renewal scan to
**`gpt-4o-mini`** (Ch4) — right model per job, one platform. → [Models in Microsoft Foundry](https://learn.microsoft.com/azure/ai-foundry/)

### Function tools — `get_contract_status`

**What it is:** plain Python in [`src/clm_common/tools.py`](../src/clm_common/tools.py) exposed as a tool.
`get_contract_status(contract_id: str) -> str` returns a JSON string; the Agent Framework derives the tool's
schema from the **type hints + docstring**, and `function_tool(...)` runs it automatically mid-run.

- **Prefers Azure SQL** (`SELECT … FROM dbo.contracts` via pyodbc) when `AZURE_SQL_CONNECTION_STRING` is set,
  else falls back to [`challenge-0/data/contracts_seed.json`](../challenge-0/data/contracts_seed.json) — the
  reply's `_note` tells you which source answered.
- Ships a second tool, `list_upcoming_renewals(within_days=90)`, ready for the **🚀 Go Further** step.

**Why here:** structured facts (status, renewal date, risk, owner) come from a **lookup**, never a guess —
the knowledge tool grounds *unstructured* answers, this grounds *structured* ones.
→ [Function calling with Foundry agents](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling)

## ✅ Tasks

### 1 · Verify the knowledge connection

Confirm the default Azure AI Search connection resolves and the index is present:

```bash
python challenge-1/kb_setup.py
```

Expected output (ids will differ):

```text
✓ Default Azure AI Search connection: /subscriptions/.../connections/clm-search
✓ Index: clm-corpus
✓ Built Foundry Azure AI Search grounding tool (semantic, top_k=5).
```

> [!TIP]
> If the connection doesn't resolve, it's almost always a Challenge 0 gap — see **Troubleshooting**.

### 2 · Read the agent definition

Open [`agents/intake_drafting_agent.py`](agents/intake_drafting_agent.py) and trace how it's wired:

- `model=settings.model_drafting` → **Claude Sonnet 4.5** (the only line that would change for GPT).
- The persona + **refusal** instructions in `INSTRUCTIONS`.
- Grounding via `build_knowledge_tool(...)` **plus** the `get_contract_status` **function tool**,
  passed together in the Agent's `tools=[...]`.
- `function_tool(...)` wraps the function with `approval_mode="never_require"` so it auto-executes during a run.

<details>
<summary><strong>🔬 Anatomy of the agent</strong> — the wiring in ~15 lines</summary>

```python
from agent_framework import Agent
from clm_common.foundry import build_chat_client, function_tool
from kb_setup import build_knowledge_tool
from clm_common.tools import get_contract_status

knowledge = build_knowledge_tool(connection_id=connection_id)   # Azure AI Search grounding over clm-corpus

agent = Agent(
    client=build_chat_client(settings.model_drafting),          # ← "claude-sonnet-4-5"; swap for a GPT id, nothing else changes
    name="intake-drafting-agent",
    instructions=INSTRUCTIONS,                                  # persona + citations + refusal policy
    tools=[
        knowledge,                                              # unstructured grounding (Foundry IQ)
        function_tool(get_contract_status),                     # structured lookups, approval_mode="never_require"
    ],
)
```

A single run then does: `agent.run(prompt, session=session)` — the agent plans, retrieves,
optionally calls `get_contract_status`, and drafts — then returns the assistant's text. The
`run_agent` / `run_prompt` helpers live in [`src/clm_common/foundry.py`](../src/clm_common/foundry.py).
</details>

### 3 · Run the agent end-to-end

This builds the agent and runs four demo prompts in one shared session:

```bash
python challenge-1/agents/intake_drafting_agent.py
```

The four built-in prompts deliberately cover all four behaviors — a **draft**, a **cited** clause
Q&A, a **`CT-4821` status** lookup (function tool), and a **legal-advice** prompt that must be
**refused**.

> [!NOTE]
> The agent is built in-process each run via the Microsoft Agent Framework — there's no server-side
> agent id to manage or clean up. Later challenges simply call `create_agent(...)` again.

### 4 · Exercise every capability

Work through [`sample_prompts.md`](sample_prompts.md) — via the demo script, the portal **Playground**,
or your own thread. Each section maps to one capability, and the file's *"What good looks like"* table
tells you the expected behavior:

| Prompt type | Expected behavior |
|-------------|-------------------|
| **Drafting** | Uses the approved template structure; fills only provided details; **no invented terms** |
| **Cited Q&A** | Answer grounded in the corpus **with citations**; says "not in corpus" if unknown |
| **Function tool** | Calls `get_contract_status`; returns **real fields** for `CT-4821` |
| **Legal advice** | **Brief refusal** + recommends qualified counsel |

For the tool call, `CT-4821` should come back with concrete, structured data — for example:

```json
{"contract_id": "CT-4821", "counterparty": "Acme Corp", "type": "MSA",
 "status": "Active", "renewal_date": "2026-09-01", "auto_renew": true,
 "notice_days": 90, "risk": "High", "owner": "legal@contoso.com",
 "_note": "(source: contracts_seed.json)"}
```

### 5 · (Optional) Add content safety

In the portal, attach **Prompt Shields / PII** guardrails to the agent, or discuss where they'd sit.
The refusal instructions already enforce the no-legal-advice policy at the prompt layer — content
safety adds a second, model-independent layer (previewed here, built in **Challenge 5**).

### ⚙️ Claude fallback (if Foundry can't serve Claude via the chat client in your region)

The **preferred** path is `model="claude-sonnet-4-5"` on `build_chat_client(...)`, exactly like GPT. If that
run fails because Foundry doesn't yet serve Anthropic models through the chat client in your region, call
Claude **directly** through Foundry with the Anthropic SDK and keep grounding/tools in your own code:

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

You'd then do retrieval (Azure AI Search) and the contract-status lookup yourself and pass the results
into the prompt. Prefer the native agent path when available — this is only a safety net.

## ✔️ Success criteria

You're done when:

- [ ] `python challenge-1/kb_setup.py` prints the Search connection id **and** the `clm-corpus` index.
- [ ] Cited answers are drawn from the corpus (you can see the source documents).
- [ ] The `get_contract_status` tool is invoked for `CT-4821` and returns real fields.
- [ ] The legal-advice prompt is **refused** with a recommendation to consult counsel.
- [ ] The agent is running on the **Claude** deployment (confirm the model name in the portal).

## 🚀 Go Further

- Add a **Web IQ (Bing)** grounding tool for external / regulatory lookups.
- Add a second knowledge base scoped to a single contract type and compare retrieval quality.
- Tighten the persona so every draft includes a **"⚠️ requires human review"** banner.
- Add a second function tool (e.g. `list_upcoming_renewals`, already in `clm_common.tools`) and watch
  the model choose between tools.

## 🛠️ Troubleshooting

| Symptom | Fix |
|---------|-----|
| `get_default(AZURE_AI_SEARCH)` returns nothing | Ensure Challenge 0 created the Search resource and connected it to the project (**portal → Connected resources**). Set `AZURE_SEARCH_CONNECTION_NAME` in `.env`. |
| No citations returned | Confirm `scripts/seed_corpus.py` populated the index and the semantic config exists; try raising `top_k` in `build_knowledge_tool`. |
| Function tool never called | Keep the docstring + type hints (the schema comes from them); ensure it's wrapped with `function_tool(...)` and passed in the Agent's `tools=[...]`, and the prompt actually asks for a specific contract. |
| `get_contract_status` says "not found" | Use a known id (`CT-4821`, `CT-3390`, `CT-5102`, `CT-2765`, `CT-6033`) — the error message lists them. |
| Run fails on Claude | Foundry may not serve Anthropic models via the chat client in your region yet — use the **Claude fallback** above. |
| `Missing required environment variable 'AZURE_AI_PROJECT_ENDPOINT'` | Re-run Challenge 0's deploy (which writes `.env`) or copy `.env.example` → `.env` and fill it in. |

## 🎯 What you accomplished

You built your first **grounded, cited, tool-using, guard-railed agent** — and did it on **Claude**
with the same API you'll use for GPT.

**Key achievements:**

- **Grounded on your corpus** — attached the Foundry IQ knowledge base as a tool so answers come from
  Contoso's documents, with citations, not model memory.
- **Mixed knowledge + function tools** — combined unstructured retrieval with a deterministic
  `get_contract_status` lookup in the Agent's `tools=[...]`, auto-invoked mid-run.
- **Enforced guardrails** — the agent refuses legal advice and flags policy deviations for a human.
- **Proved model-agnosticism** — ran the whole thing on Claude Sonnet 4.5 by changing a single
  `model` argument.

This agent becomes a building block later: the **orchestrator** (Challenge 3) will delegate drafting
to it, and everything it does will be **traced and evaluated** in Challenge 2.

## 📚 Learn more

- [Microsoft Foundry](https://learn.microsoft.com/azure/ai-foundry/)
- [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/overview/agent-framework-overview)
- [Function calling with Foundry agents](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling)
- [Foundry IQ / agentic retrieval](https://learn.microsoft.com/azure/search/search-agentic-retrieval-concept)
- [Azure AI Search](https://learn.microsoft.com/azure/search/)

## 🧠 Reflection

- Why put **drafting** on Claude and **routing** on GPT? (Instruction-following & long-context legal
  reasoning vs. fast, deterministic tool-calling.)
- Where should guardrails live — in the prompt, as a content-safety policy, or both? What does each
  catch that the other misses?
- When should a fact come from a **function tool** vs. **retrieval**? What breaks if you let the model
  guess contract metadata?

---

⬅️ Back: **[Challenge 0 — Setup & Foundry Foundations](../challenge-0/)** ·
➡️ Next: **[Challenge 2 — Observability, Tracing & Evaluation](../challenge-2/)**
