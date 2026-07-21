#!/usr/bin/env bash
# ==========================================================================
# Challenge 0 — provision the Foundry CLM microhack resources and write .env
# ==========================================================================
# Usage:   ./scripts/deploy.sh [--with-sql]
# Requires: az CLI (logged in via `az login`), an Azure subscription with
#           rights to deploy GPT and Anthropic Claude models.
#
# NOTE: Model + region availability changes over time. Confirm your target
#       region offers gpt-5.3, gpt-4o-mini AND Claude Sonnet 4.5 in the
#       Foundry model catalog before running. See the challenge-0 README.
# ==========================================================================
set -euo pipefail

# ---- Configuration (override via environment) ----------------------------
LOCATION="${LOCATION:-swedencentral}"
SUFFIX="${SUFFIX:-$(echo $RANDOM | md5sum 2>/dev/null | cut -c1-5 || echo $RANDOM)}"
RG="${RG:-rg-clm-microhack}"
FOUNDRY="${FOUNDRY:-clmfoundry${SUFFIX}}"
PROJECT="${PROJECT:-clm-project}"
SEARCH="${SEARCH:-clmsearch${SUFFIX}}"
APPINSIGHTS="${APPINSIGHTS:-clm-appinsights}"
WITH_SQL="false"
[[ "${1:-}" == "--with-sql" ]] && WITH_SQL="true"

# Model deployments (name=catalog-model:version:format)
GPT_ORCH="gpt-5.3"
GPT_MINI="gpt-4o-mini"
CLAUDE="claude-sonnet-4-5"

echo "▶ Resource group:  $RG ($LOCATION)"
echo "▶ Foundry account: $FOUNDRY / project $PROJECT"

# ---- 1. Resource group ---------------------------------------------------
az group create -n "$RG" -l "$LOCATION" -o none

# ---- 2. Foundry (AI Services) account + project --------------------------
az cognitiveservices account create \
  -n "$FOUNDRY" -g "$RG" -l "$LOCATION" \
  --kind AIServices --sku S0 --custom-domain "$FOUNDRY" \
  --yes -o none
echo "  ✓ Foundry account created"

# Create the Foundry project (preview CLI extension may be required:
#   az extension add --name ai-foundry   OR create the project in the portal).
az cognitiveservices account project create \
  --account-name "$FOUNDRY" -g "$RG" --project-name "$PROJECT" -o none \
  || echo "  ! Project create via CLI unavailable — create '$PROJECT' in the Foundry portal, then re-run to fetch the endpoint."

# ---- 3. Model deployments (GPT + Claude) ---------------------------------
deploy_model () {  # name  model-name  version  format  sku-capacity
  echo "  → deploying $1 ($4 $2 v$3)"
  az cognitiveservices account deployment create \
    -n "$FOUNDRY" -g "$RG" \
    --deployment-name "$1" \
    --model-name "$2" --model-version "$3" --model-format "$4" \
    --sku-name "GlobalStandard" --sku-capacity "${5:-20}" -o none \
    || echo "    ! $1 deployment failed — check the model is available in $LOCATION."
}
# gpt-5.3 deployment: no base `gpt-5.3` model in swedencentral — use gpt-5.3-chat.
# Confirm the exact model/version in your region's Foundry catalog.
deploy_model "$GPT_ORCH" "gpt-5.3-chat"     "2026-03-03" "OpenAI"    30
deploy_model "$GPT_MINI" "gpt-4o-mini"      "2024-07-18" "OpenAI"    30
# Claude: model-format Anthropic; version is the date-stamped Azure catalog version.
deploy_model "$CLAUDE"   "claude-sonnet-4-5" "20250929"  "Anthropic" 20

# ---- 4. Azure AI Search (Foundry IQ backing store) -----------------------
az search service create \
  -n "$SEARCH" -g "$RG" -l "$LOCATION" \
  --sku basic --partition-count 1 --replica-count 1 -o none
echo "  ✓ Azure AI Search created"

# ---- 5. Corpus source: SharePoint (bring-your-own) -----------------------
# The contract PDFs live in a SharePoint document library (Microsoft 365, not an
# Azure resource — nothing to create here). scripts/seed_corpus.py creates the
# Azure AI Search SharePoint Online data source + indexer that crawls it into the
# clm-corpus index. Fill the SHAREPOINT_* values in .env first (see challenge-0 README).
echo "  · Corpus source is SharePoint (BYO) — set SHAREPOINT_* in .env, then run seed_corpus.py"

# ---- 6. Application Insights ---------------------------------------------
az monitor app-insights component create \
  --app "$APPINSIGHTS" -g "$RG" -l "$LOCATION" --kind web -o none
APPINSIGHTS_CONN=$(az monitor app-insights component show --app "$APPINSIGHTS" -g "$RG" --query connectionString -o tsv)
echo "  ✓ Application Insights created"

# ---- 7. Azure SQL (optional) ---------------------------------------------
SQL_CONN=""
if [[ "$WITH_SQL" == "true" ]]; then
  SQLSERVER="clmsql${SUFFIX}"
  SQLDB="clmdb"
  SQLPWD="Clm!$(openssl rand -hex 8)"
  az sql server create -n "$SQLSERVER" -g "$RG" -l "$LOCATION" \
    --admin-user clmadmin --admin-password "$SQLPWD" -o none
  az sql db create -s "$SQLSERVER" -g "$RG" -n "$SQLDB" --service-objective Basic -o none
  az sql server firewall-rule create -s "$SQLSERVER" -g "$RG" \
    -n AllowAzure --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 -o none
  SQL_CONN="Driver={ODBC Driver 18 for SQL Server};Server=tcp:${SQLSERVER}.database.windows.net,1433;Database=${SQLDB};Uid=clmadmin;Pwd=${SQLPWD};Encrypt=yes;TrustServerCertificate=no;"
  echo "  ✓ Azure SQL created (admin password stored only in .env)"
else
  echo "  · Skipping Azure SQL (run with --with-sql to provision). The contract-status"
  echo "    tool will fall back to challenge-0/data/contracts_seed.json."
fi

# ---- 8. Resolve endpoints + write .env -----------------------------------
PROJECT_ENDPOINT="https://${FOUNDRY}.services.ai.azure.com/api/projects/${PROJECT}"
SEARCH_ENDPOINT="https://${SEARCH}.search.windows.net"

cat > .env <<ENV
# Autogenerated by scripts/deploy.sh — do not commit.
AZURE_AI_PROJECT_ENDPOINT=${PROJECT_ENDPOINT}

MODEL_ORCHESTRATOR=${GPT_ORCH}
MODEL_DRAFTING=${CLAUDE}
MODEL_CLAUSE_RISK=${CLAUDE}
MODEL_RENEWAL=${GPT_MINI}

AZURE_SEARCH_ENDPOINT=${SEARCH_ENDPOINT}
AZURE_SEARCH_INDEX=clm-corpus
AZURE_SEARCH_CONNECTION_NAME=clm-search

# SharePoint corpus (BYO) — fill these in before running seed_corpus.py.
SHAREPOINT_SITE_URL=
SHAREPOINT_DOC_LIBRARY=Documents
SHAREPOINT_APP_ID=
SHAREPOINT_APP_SECRET=
SHAREPOINT_TENANT_ID=

APPLICATIONINSIGHTS_CONNECTION_STRING=${APPINSIGHTS_CONN}
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true

AZURE_SQL_CONNECTION_STRING=${SQL_CONN}

MICROSOFT_APP_ID=
MICROSOFT_APP_PASSWORD=
MICROSOFT_APP_TENANT_ID=
TEAMS_SERVICE_URL=
TEAMS_CONVERSATION_ID=
ENV

echo ""
echo "✅ Deployment complete. Wrote .env with the project endpoint + connection strings."
echo "   Next: python scripts/seed_corpus.py && python scripts/smoke_test.py"
