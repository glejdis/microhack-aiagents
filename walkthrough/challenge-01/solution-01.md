# Solution 01 — Setup & Foundry Foundations

**[← Back to Challenge 1](../../challenges/challenge-01.md)** · [Home](../../README.md)

This challenge is pure setup — there is no agent to build yet. You provision the
Microsoft Foundry environment, wire up your `.env`, and seed the **Contoso Global**
contract corpus the later challenges ground on.

## Expected end state

- Codespace (or local devcontainer) built and dependencies installed.
- `az login` completed in the terminal.
- Resources provisioned via **one** path: `azd up` (Bicep in
  [`labautomation/infra/`](../../labautomation/infra/)), the
  [`labautomation/deploy.sh`](../../labautomation/deploy.sh) / `.ps1` script, or the
  one-click **Deploy to Azure** button.
- `.env` populated — the deploy script / `azd` postprovision hook autofills it via
  [`src/scripts/write_env.py`](../../src/scripts/write_env.py).
- The corpus is crawled into the `clm-corpus` Azure AI Search index by
  [`src/scripts/seed_corpus.py`](../../src/scripts/seed_corpus.py) (SharePoint path)
  or the local-PDF fallback over [`src/data/`](../../src/data/).
- **Done when** [`src/scripts/smoke_test.py`](../../src/scripts/smoke_test.py)
  prints `✅ PASS` — a tiny agent runs on **both** the GPT and Claude deployments.

## Key files

| Path | Role |
|------|------|
| [`labautomation/infra/`](../../labautomation/infra/) | Bicep templates + `azuredeploy.json` for the Foundry project, models, Search, SQL, App Insights |
| [`labautomation/deploy.sh`](../../labautomation/deploy.sh) · `.ps1` | Scripted provisioning that autofills `.env` |
| [`src/scripts/seed_corpus.py`](../../src/scripts/seed_corpus.py) | Seeds the `clm-corpus` index (SharePoint crawl or local-PDF fallback) |
| [`src/scripts/seed_sql.py`](../../src/scripts/seed_sql.py) | Optional: seeds contract-status rows in Azure SQL |
| [`src/scripts/smoke_test.py`](../../src/scripts/smoke_test.py) | Gate — confirms both model runners answer |
| [`src/data/`](../../src/data/) | The CLM corpus (contracts, templates, clause library, playbooks) + eval datasets |

## Common issues

| Symptom | Cause / fix |
|---------|-------------|
| A model isn't offered in your region | Pick a region with `gpt-5.4`, `gpt-5-mini`, **and** `claude-sonnet-4-5`; verify in the Foundry model catalog. |
| `smoke_test.py` fails on Claude | The runner may not host Claude in your region — deploy with `DEPLOY_CLAUDE_MODEL=false` to fall back to `gpt-5.4`. |
| Corpus / index empty | Re-run `python src/scripts/seed_corpus.py` (idempotent). |
