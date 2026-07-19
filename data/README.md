# CLM Corpus (Contoso Global)

Seed data for the microhack. Challenge 0 uploads these to Blob Storage and indexes them into
Azure AI Search so the **Foundry IQ** knowledge base can ground the agents with cited answers.

| Folder | Contents | Used by |
|--------|----------|---------|
| `contract_templates/` | Approved NDA / MSA / SOW templates | Intake & Drafting agent (Ch1) |
| `clause_library/` | `standard_clauses.md` — enterprise-standard positions (CL-01…CL-10) | Clause & Risk agent (Ch3) |
| `policies/` | Contracting policy (approval thresholds, no-legal-advice rule) | All agents (grounding + guardrails) |
| `counterparty_drafts/` | `acme_msa_draft.md` — an **inbound** draft full of red flags | Clause & Risk agent (Ch3) |
| `evaluation/` | `evaluation_dataset.jsonl` — 16 labelled cases | Evaluation (Ch2) |

## Evaluation dataset shape

Each line is one JSON object:

```json
{"query": "...", "ground_truth": "...", "context": "...", "category": "grounded_qa"}
```

Categories: `grounded_qa` (answerable + cited), `clause_risk` (compare to standard),
`refusal` (must decline legal advice), `tool_call` (must call the contract-status tool).
At eval time a `target` callable generates the `response`; evaluators score it against
`context` (groundedness) and `ground_truth` (relevance/correctness).
