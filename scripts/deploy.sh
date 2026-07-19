#!/usr/bin/env bash
# ==========================================================================
# Challenge 0 — provision the Foundry CLM microhack resources and write .env
# ==========================================================================
# Usage:   ./scripts/deploy.sh [--with-sql]
# Requires: az CLI (logged in via `az login`), an Azure subscription with
#           rights to deploy GPT and Anthropic Claude models.
#
# NOTE: Model + region availability changes over time. Confirm your target
#       region offers gpt-4.1, gpt-4o-mini AND Claude Sonnet 4.5 in the
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
STORAGE="${STORAGE:-clmstor${SUFFIX}}"
APPINSIGHTS="${APPINSIGHTS:-clm-appinsights}"
WITH_SQL="false"
[[ "${1:-}" == "--with-sql" ]] && WITH_SQL="true"

# Model deployments (name=catalog-model:version:format)
GPT_ORCH="gpt-4.1"
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
deploy_model "$GPT_ORCH" "gpt-4.1"          "2025-04-14" "OpenAI"    30
deploy_model "$GPT_MINI" "gpt-4o-mini"      "2024-07-18" "OpenAI"    30
# Claude: model-format Anthropic, version "2" = Hosted on Azure (vs "1" on Anthropic).
deploy_model "$CLAUDE"   "claude-sonnet-4-5" "2"         "Anthropic" 20

# ---- 4. Azure AI Search (Foundry IQ backing store) -----------------------
az search service create \
  -n "$SEARCH" -g "$RG" -l "$LOCATION" \
  --sku basic --partition-count 1 --replica-count 1 -o none
echo "  ✓ Azure AI Search created"

# ---- 5. Storage (corpus source docs) -------------------------------------
az storage account create \
  -n "$STORAGE" -g "$RG" -l "$LOCATION" --sku Standard_LRS -o none
STORAGE_CONN=$(az storage account show-connection-string -n "$STORAGE" -g "$RG" -o tsv)
az storage container create --name clm-corpus --connection-string "$STORAGE_CONN" -o none
echo "  ✓ Storage + container created"

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
  echo "    tool will fall back to data/contracts_seed.json."
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

AZURE_STORAGE_CONNECTION_STRING=${STORAGE_CONN}
AZURE_STORAGE_CONTAINER=clm-corpus

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
