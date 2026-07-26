# Solution 02 — Grounded Agent with Foundry IQ + Tools

**[← Back to Challenge 2](../../challenges/challenge-02.md)** · [Home](../../README.md)

Your first agent: the **Intake & Drafting agent** — grounded on the Contoso corpus,
citing its sources, using function tools, and guard-railed to refuse legal advice.
It runs on **Anthropic Claude Sonnet 4.5**, but the grounding code is identical to
what you'd run on GPT — Foundry is a model-agnostic control plane.

## Expected end state

- Foundry IQ knowledge source built over the `clm-corpus` index by
  [`src/kb_setup.py`](../../src/kb_setup.py) (also reports the web-grounding tool).
- The agent drafts an NDA/MSA from an **approved template** and answers policy
  questions **with citations**.
- Guardrails hold: the agent refuses to give legal advice and stays grounded.

## Key files

| Path | Role |
|------|------|
| [`src/agents/intake_drafting_agent.py`](../../src/agents/intake_drafting_agent.py) | The grounded, tool-using, guard-railed drafting agent (Claude Sonnet 4.5) |
| [`src/kb_setup.py`](../../src/kb_setup.py) | Builds the Foundry IQ knowledge source + web-grounding tool over `clm-corpus` |
| [`src/sample_prompts.md`](../../src/sample_prompts.md) | Prompts to exercise drafting, grounded Q&A, and the guardrails |
| [`src/clm_common/`](../../src/clm_common/) | Shared config + Foundry client helpers reused by every agent |

## Run it

```bash
python src/kb_setup.py                       # prints the Search connection id + clm-corpus index
python src/agents/intake_drafting_agent.py   # drafts + answers with citations
```

## Common issues

| Symptom | Cause / fix |
|---------|-------------|
| No citations returned | Confirm the `clm-corpus` index is populated (Challenge 1's `seed_corpus.py`). |
| Claude not served in region | Fall back to the Anthropic-SDK path or `gpt-5.4`; the grounding concepts are identical. |
| Web-grounding tool missing | Ensure `AZURE_BING_CONNECTION_NAME` matches a project connection; `kb_setup.py` reports whether it built. |
