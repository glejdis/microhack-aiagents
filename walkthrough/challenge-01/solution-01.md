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

## 🛠️ Task-by-task walkthrough

### Tasks 1–3 · Fork, dev environment, `az login`
```bash
# Task 1: fork glejdis/microhack-aiagents on GitHub, then open your fork.
# Task 2: launch the devcontainer — Code ▸ Codespaces ▸ Create, or locally:
code .            # "Reopen in Container" when prompted
# Task 3: authenticate the Azure CLI (the deploy script and azd both reuse this login)
az login
az account set --subscription "<your-subscription-id>"
```

### Task 4 · Deploy the resources
Pick **one** path — all three provision the same Foundry project, models, Search, SQL and App Insights, then autofill `.env`:
```bash
azd up                             # Bicep in labautomation/infra/ (recommended)
# — or the scripted path —
./labautomation/deploy.sh          # bash;  deploy.ps1 on Windows
# — no Claude quota? skip it (drafting/clause-risk fall back to gpt-5.4) —
DEPLOY_CLAUDE_MODEL=false ./labautomation/deploy.sh
```
The `.env` is written for you by the postprovision hook → [`src/scripts/write_env.py`](../../src/scripts/write_env.py), which reads the deployment outputs (`azd env get-values`, or `--deployment` for the ARM path) and writes every env var the agents use — filling constants from a `DEFAULTS` map when an output is absent:
```python
# src/scripts/write_env.py — constants used when a deployment output is missing
DEFAULTS = {
    "MODEL_ORCHESTRATOR": "gpt-5.4",
    "MODEL_DRAFTING": "claude-sonnet-4-5",
    "MODEL_CLAUSE_RISK": "claude-sonnet-4-5",
    "MODEL_RENEWAL": "gpt-5-mini",
    "AZURE_SEARCH_INDEX": "clm-corpus",
    "AZURE_SEARCH_CONNECTION_NAME": "clm-search",
    # …
}
env = azd_env_values()                       # or arm_env_values(--deployment)
get = lambda k: env.get(k) or DEFAULTS.get(k, "")
# → writes AZURE_AI_PROJECT_ENDPOINT, MODEL_*, AZURE_SEARCH_*, App Insights, SQL … to .env
```

### Task 5 · Verify your resources
In the Foundry portal confirm the project, the **3 model deployments** (2 without Claude), and the `clm-corpus` Search index. From the CLI:
```bash
az cognitiveservices account deployment list -g <rg> -n clmfoundry<token> -o table
```

### Task 6 · Seed the corpus
```bash
python src/scripts/seed_corpus.py          # idempotent — crawls SharePoint, or local-PDF fallback over src/data/
python src/scripts/seed_sql.py             # optional — only if you deployed Azure SQL
```
`seed_corpus.py` builds the `clm-corpus` index the later challenges ground on; re-running is safe.

### Task 7 · Smoke test (the finish line)
The gate proves the project is reachable **and** that both model runners answer. The core of it builds a one-line agent per deployment:
```python
# src/scripts/smoke_test.py
def ping_model(model: str, label: str) -> bool:
    agent = Agent(
        client=build_chat_client(model),
        name=f"smoke-{label}",
        instructions="Reply with exactly one word: OK.",
    )
    reply = run_prompt(agent, "Say OK.")
    return bool(reply.strip())
# main() pings MODEL_ORCHESTRATOR (gpt) and MODEL_DRAFTING (claude);
# if Claude was skipped, MODEL_DRAFTING == MODEL_ORCHESTRATOR and the Claude ping is skipped.
```
```bash
python src/scripts/smoke_test.py
```
✅ **You should see** — this is the finish line for Challenge 1:
```text
1) Checking environment…            ✓ (all vars present)
2) Pinging gpt deployment 'gpt-5.4'… ✓ gpt replied: OK
2) Pinging claude deployment 'claude-sonnet-4-5'… ✓ claude replied: OK

Smoke test: ✅ PASS
```

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
