# labautomation — provisioning & seeding

Everything a coach or `azd` runs to stand up a team's environment lives here: the
**Bicep infrastructure**, the **deploy scripts** that autofill `.env`, and the
**seed** scripts that load the CLM corpus and contract-status data.

## What gets provisioned

[`infra/`](infra/) holds the Bicep templates (plus `azuredeploy.json` for the
one-click **Deploy to Azure** button) that create the Microsoft Foundry project, the
GPT + Claude model deployments, Azure AI Search, Azure SQL, and Application Insights.
`azure.yaml` at the repo root points `azd` at this folder.

## Scripts

| Path | Role |
|------|------|
| [`deploy.sh`](deploy.sh) · [`deploy.ps1`](deploy.ps1) | Provision resources and autofill the repo-root `.env` |
| [`write_env.py`](write_env.py) | Writes `.env` from deployment outputs (also the `azd` postprovision hook) |
| [`seed_corpus.py`](seed_corpus.py) | Seeds the `clm-corpus` Azure AI Search index (SharePoint crawl or local-PDF fallback over `../src/data/`) |
| [`seed_sql.py`](seed_sql.py) | Optional — seeds the contract-status table in Azure SQL |
| [`setup_sharepoint_app.sh`](setup_sharepoint_app.sh) · [`.ps1`](setup_sharepoint_app.ps1) | Coach setup — the Entra app registration for the SharePoint crawl |
| [`upload_corpus_to_sharepoint.py`](upload_corpus_to_sharepoint.py) | Coach setup — upload the corpus PDFs into a SharePoint library |
| [`smoke_test.py`](smoke_test.py) | Gate — confirms a tiny agent runs on **both** the GPT and Claude deployments |

## Getting started

```bash
az login
./labautomation/deploy.sh          # or: azd up   (Windows: labautomation\deploy.ps1)
python labautomation/seed_corpus.py # seed the corpus index (idempotent)
python labautomation/smoke_test.py  # expect ✅ PASS before starting Challenge 2
```

> Pick **one** provisioning path (`azd up` **or** the deploy script **or** the
> one-click button) — don't mix them. The first two autofill your `.env`. See the
> **[Coach & Facilitator Guide](../docs/coach-guide.md)** for the full run-of-show and
> a reset/recovery playbook.
