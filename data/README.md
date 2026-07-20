# CLM Corpus (Contoso Global)

Seed data for the microhack. Challenge 0 uploads these to Blob Storage and indexes them into
Azure AI Search so the **Foundry IQ** knowledge base can ground the agents with cited answers.

| Folder | Contents | Used by |
|--------|----------|---------|
| `contract_templates/` | Approved NDA / MSA / SOW templates (Markdown) | Intake & Drafting agent (Ch1) |
| `clause_library/` | `standard_clauses.md` — enterprise-standard positions (CL-01…CL-10) | Clause & Risk agent (Ch3) |
| `policies/` | Contracting policy (approval thresholds, no-legal-advice rule) | All agents (grounding + guardrails) |
| `contracts/` | **5 executed contract PDFs** (one per row in `contracts_seed.json`) | Foundry IQ grounding (Ch1), lifecycle lookups |
| `counterparty_drafts/` | `acme_msa_draft.pdf` — an **inbound** draft full of red flags | Clause & Risk agent (Ch3) |
| `evaluation/` | `evaluation_dataset.jsonl` — 16 labelled cases | Evaluation (Ch2) |

> **Contracts are PDFs.** Executed contracts (`contracts/`) and inbound drafts
> (`counterparty_drafts/`) are real, text-extractable PDF documents — the format
> legal teams actually exchange. Contoso-authored reference material (templates,
> clause library, policy) stays Markdown because it's authoring source, not an
> exchanged document. The seeding script (`scripts/seed_corpus.py`) extracts PDF
> text with **pypdf** via `clm_common.documents.read_document_text`, so both
> formats land in the same search index.

### Regenerating the contract PDFs

The PDFs are committed, but their full text lives in source at
`scripts/make_sample_contracts.py` (a reportlab generator, build-time only). To
tweak a clause and rebuild:

```bash
pip install reportlab
python scripts/make_sample_contracts.py
```

Each generated contract matches its `contracts_seed.json` metadata exactly and
is deliberately aligned to (or, for Medium/High rows, deviates from) the Standard
Clause Library so the Clause & Risk agent and evaluators have gradable material.

## Evaluation dataset shape

Each line is one JSON object:

```json
{"query": "...", "ground_truth": "...", "context": "...", "category": "grounded_qa"}
```

Categories: `grounded_qa` (answerable + cited), `clause_risk` (compare to standard),
`refusal` (must decline legal advice), `tool_call` (must call the contract-status tool).
At eval time a `target` callable generates the `response`; evaluators score it against
`context` (groundedness) and `ground_truth` (relevance/correctness).
