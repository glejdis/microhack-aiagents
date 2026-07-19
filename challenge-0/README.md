# Challenge 0 · Setup & Foundry Foundations

> **Duration:** 30 min · **Prerequisites:** an Azure subscription (rights to create a Foundry
> project and deploy GPT **and** Anthropic Claude models), a GitHub account.

> 🧩 **How to use this challenge:** the provisioning is **scripted for you** (`azd up` or the
> `scripts/deploy` script). **Run it, then confirm you understand what got created** — the Foundry
> project, the three-model fleet, and the search index the later challenges build on. Stuck? The
> scripts *are* the answer key.

## 🎯 Objective

Stand up the full Foundry environment and seed the CLM corpus with **zero local install**, so the
rest of the hack is pure agent-building.

## 🧭 Context

Everything runs from **GitHub Codespaces** using the devcontainer in this repo (Python 3.11, Azure
CLI, `azd`, Node). Provision the Azure resources one of two ways — **`azd up`** (Bicep, in `infra/`)
or the **`scripts/deploy` script** — both autofill the same `.env`:

- A **Foundry project** (AI Services account + project).
- Three **model deployments** — `gpt-4.1`, `gpt-4o-mini`, and **`claude-sonnet-4-5`** (Claude is GA
  in Microsoft Foundry). This is the multi-model fleet the agents use.
- **Azure AI Search** (backs the Foundry IQ knowledge base), **Blob Storage** (corpus), **App
  Insights** (tracing), and optionally **Azure SQL** (contract-status tool).

## ✅ Tasks

1. **Fork** this repo and open it in Codespaces: **Code → Codespaces → Create codespace on main**.
   Wait for the devcontainer to finish `pip install -r requirements.txt`.

2. **Log in to Azure** and pick your subscription:
   ```bash
   az login --use-device-code
   az account set --subscription "<your-subscription-id>"
   ```

3. **Deploy resources** — choose a region that offers all three models (check the Foundry model
   catalog; `swedencentral` is a good default). Pick **one** option:

   **Option A — `azd up` (recommended, Bicep in `infra/`):**
   ```bash
   azd auth login
   azd up          # prompts for an environment name + region, then provisions everything
   ```
   `azd up` deploys the Bicep in `infra/`, assigns the RBAC roles the later challenges need
   (Azure AI Developer, Search + Storage data roles), creates the `clm-search` Foundry IQ
   connection, and runs the `postprovision` hook (`scripts/write_env.py`) to write your `.env`.
   To also provision Azure SQL: `azd env set DEPLOY_SQL true` and `azd env set SQL_ADMIN_PASSWORD '<StrongP@ssw0rd!>'` before `azd up`.

   **Option B — deploy script (`az` CLI):**
   ```bash
   LOCATION=swedencentral ./scripts/deploy.sh          # add --with-sql to also provision Azure SQL
   ```
   > Windows (outside Codespaces): `./scripts/deploy.ps1` (`-WithSql` optional).

   Either path writes a populated **`.env`** at the repo root. Open it and confirm the values.

4. **Seed the corpus** (uploads `data/` to Blob + builds the `clm-corpus` search index):
   ```bash
   python scripts/seed_corpus.py
   # optional, only if you deployed Azure SQL:
   python scripts/seed_sql.py
   ```

5. **Smoke test** — proves the project is reachable and both a GPT and the Claude deployment run:
   ```bash
   python scripts/smoke_test.py
   ```

## ✔️ Success criteria

- `.env` is populated (project endpoint + connection strings).
- `python scripts/smoke_test.py` prints **✅ PASS** — a tiny agent runs on **both** `gpt-4.1` and
  `claude-sonnet-4-5`.
- In the Foundry portal you can see the project, the 3 model deployments, and the `clm-corpus` index
  with documents.

Expected smoke-test output:
```
1) Checking environment…            ✓ (all vars present)
2) Pinging gpt deployment 'gpt-4.1'… ✓ gpt replied: OK
2) Pinging claude deployment 'claude-sonnet-4-5'… ✓ claude replied: OK
Smoke test: ✅ PASS
```

## 🚀 Go Further

- Inspect the **Bicep** in `infra/` (`main.bicep` + `resources.bicep`) — it mirrors `deploy.sh` and
  is what `azd up` runs. Try `azd provision --preview` to see a what-if before deploying.
- Add **US Data Zone** deployment tiers for data-residency, or scope RBAC to a least-privilege role.
- Deploy `claude-haiku-4-5` too and compare it against `gpt-4o-mini` for the renewal agent later.

## 🛠️ Troubleshooting

| Symptom | Fix |
|---------|-----|
| `deployment failed` for a model | The model/version isn't available in your region. Try `eastus2`/`westus3`, or adjust the version in `scripts/deploy.sh`. Check the Foundry catalog. |
| `account project create` unavailable | The CLI project command is preview. Create the project in the **Foundry portal**, then set `AZURE_AI_PROJECT_ENDPOINT` in `.env` manually (Overview → Endpoint). |
| Claude ping fails in smoke test | Claude may not be enabled in the **Agent runner** for your region yet. You can still proceed — Challenge 1 documents an Anthropic-SDK fallback. |
| `az login` in Codespaces | Use `az login --use-device-code`. |
| Search/quota errors | Ensure the subscription has quota for Basic Search + the model SKUs; request quota if needed. |

## 🧠 Reflection

- Why keep the corpus in Blob **and** an Azure AI Search index? (Source of truth vs retrieval.)
- The fleet mixes GPT and Claude in one project. What does Foundry give you that stitching two
  vendor APIs together would not? (One identity, billing, tracing, and governance plane.)

➡️ Next: **[Challenge 1 — Intake & Drafting agent + Foundry IQ + tools](../challenge-1/)**
