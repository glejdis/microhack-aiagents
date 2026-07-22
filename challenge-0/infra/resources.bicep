// ==========================================================================
// Foundry CLM Microhack — resource module (resource-group scope)
// Mirrors scripts/deploy.sh so `azd up` produces the same resources, model
// deployments, and .env contract the challenges expect.
// ==========================================================================
@description('Azure region for all resources.')
param location string

@description('Short, unique token used to name globally-unique resources.')
param resourceToken string

@description('Object id of the user/service principal running the deployment (for RBAC). Leave empty to skip role assignments.')
param principalId string = ''

@description('Principal type for RBAC assignments: User or ServicePrincipal.')
@allowed([ 'User', 'ServicePrincipal' ])
param principalType string = 'User'

@description('Deploy the Anthropic Claude model ("true"/"false"). Set to "false" (azd env set DEPLOY_CLAUDE_MODEL false) if your subscription has no Claude quota or the Anthropic marketplace offer is unavailable — the two Claude-backed agents then fall back to the GPT orchestrator model.')
param deployClaudeModel string = 'true'

@description('Provision the optional Azure SQL backing store for the contract-status tool ("true"/"false").')
param deploySql string = 'false'

@description('Admin password for the optional Azure SQL server (required when deploySql is true).')
@secure()
param sqlAdminPassword string = ''

@description('Tags applied to every resource.')
param tags object = {}

// ---- Fixed names (match deploy.sh + .env contract) -----------------------
var foundryName = 'clmfoundry${resourceToken}'
var projectName = 'clm-project'
var searchName = 'clmsearch${resourceToken}'
var appInsightsName = 'clm-appinsights-${resourceToken}'
var logAnalyticsName = 'clm-logs-${resourceToken}'
var searchIndexName = 'clm-corpus'
var searchConnectionName = 'clm-search'

// ---- Model deployment names ----------------------------------------------
// NOTE: these are the *deployment* names (what the app calls at runtime via the
// MODEL_* env vars); the underlying catalog model/version is set below. In
// swedencentral there is no base `gpt-5.3` model — the orchestrator deployment
// (still named `gpt-5.3`) runs the `gpt-5.3-chat` catalog model.
var gptOrchestrator = 'gpt-5.3'
var gptMini = 'gpt-5-mini'
var claude = 'claude-sonnet-4-5'
// Orchestrator catalog model + version — confirm the exact model/version offered
// in your region's Foundry model catalog and update here if needed
// (`az cognitiveservices model list --location <region>`).
var gptOrchestratorModel = 'gpt-5.3-chat'
var gptOrchestratorVersion = '2026-03-03'
// Renewal / lightweight agent catalog model. gpt-4o-mini is deprecating in
// swedencentral (fires ServiceModelDeprecating on new deployments), so the
// renewal deployment runs gpt-5-mini instead — same GlobalStandard SKU, a later
// deprecation horizon, and still cheap/fast for the high-frequency agent.
var gptMiniModel = 'gpt-5-mini'
var gptMiniVersion = '2025-08-07'

// ---- Built-in role definition ids ----------------------------------------
var roleAiDeveloper = '64702f94-c441-49e6-a78b-ef80e0188fee'            // Azure AI Developer
var roleCognitiveServicesUser = 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User
var roleSearchIndexDataContributor = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
var roleSearchServiceContributor = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
var roleSearchIndexDataReader = '1407120a-92aa-4202-b7e9-c0e197c71c8f'

var wantSql = toLower(deploySql) == 'true' && !empty(sqlAdminPassword)
var wantClaude = toLower(deployClaudeModel) == 'true'
var assignUserRoles = !empty(principalId)

// ==========================================================================
// Observability — Log Analytics + Application Insights
// ==========================================================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ==========================================================================
// Corpus source of truth — SharePoint document library (bring-your-own)
// ==========================================================================
// The original contract PDFs live in a SharePoint Online document library, which
// is Microsoft 365 (not an Azure Resource Manager resource) and therefore not
// provisioned here. Challenge 0's scripts/seed_corpus.py creates the Azure AI
// Search SharePoint Online data source + indexer that crawls that library into
// the clm-corpus index. See the challenge-0 README for the prerequisite Entra
// app registration and .env values (SHAREPOINT_*).

// ==========================================================================
// Azure AI Search — Foundry IQ backing store (AAD data-plane auth enabled)
// ==========================================================================
resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchName
  location: location
  tags: tags
  sku: { name: 'basic' }
  identity: { type: 'SystemAssigned' }
  properties: {
    partitionCount: 1
    replicaCount: 1
    hostingMode: 'default'
    semanticSearch: 'free'
    // Allow BOTH AAD and API keys so AAD-based seeding (DefaultAzureCredential)
    // and portal/key access both work.
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

// ==========================================================================
// Foundry (AI Services) account + project + model deployments
// ==========================================================================
resource account 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: foundryName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: foundryName
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    // Required so the child `projects` resource below can be created under this
    // AIServices account (otherwise: "Project can only be created under
    // AIServices Kind account with allowProjectManagement set to true").
    allowProjectManagement: true
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: account
  name: projectName
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {
    displayName: 'CLM Microhack'
    description: 'Contract Lifecycle Management multi-agent microhack project.'
  }
}

// Model deployments must be serialized on a single account.
resource deployOrchestrator 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: account
  name: gptOrchestrator
  sku: { name: 'GlobalStandard', capacity: 30 }
  properties: {
    model: { format: 'OpenAI', name: gptOrchestratorModel, version: gptOrchestratorVersion }
  }
}

resource deployMini 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: account
  name: gptMini
  sku: { name: 'GlobalStandard', capacity: 30 }
  properties: {
    model: { format: 'OpenAI', name: gptMiniModel, version: gptMiniVersion }
  }
  dependsOn: [ deployOrchestrator ]
}

// Claude: model-format Anthropic. Version is the date-stamped Azure Foundry
// catalog version (e.g. 20250929 for claude-sonnet-4-5 in swedencentral) — not
// Anthropic's own "1"/"2" scheme. Verify with `az cognitiveservices model list`.
// Gated on deployClaudeModel: Anthropic deployments can fail on zero
// subscription quota or missing marketplace offer data (InvalidModelProviderData)
// even when every step is correct — set DEPLOY_CLAUDE_MODEL=false to skip.
resource deployClaude 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = if (wantClaude) {
  parent: account
  name: claude
  sku: { name: 'GlobalStandard', capacity: 20 }
  properties: {
    model: { format: 'Anthropic', name: 'claude-sonnet-4-5', version: '20250929' }
  }
  dependsOn: [ deployMini ]
}

// Foundry IQ connection: project -> Azure AI Search (deploy.sh only sets the
// name and relies on the portal; here we actually create it).
resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: searchConnectionName
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${search.name}.search.windows.net'
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiType: 'Azure'
      ResourceId: search.id
      location: location
    }
  }
}

// ==========================================================================
// Azure SQL (optional) — contract status / renewal dates function tool
// ==========================================================================
resource sqlServer 'Microsoft.Sql/servers@2023-08-01' = if (wantSql) {
  name: 'clmsql${resourceToken}'
  location: location
  tags: tags
  properties: {
    administratorLogin: 'clmadmin'
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlDb 'Microsoft.Sql/servers/databases@2023-08-01' = if (wantSql) {
  parent: sqlServer
  name: 'clmdb'
  location: location
  tags: tags
  sku: { name: 'Basic', tier: 'Basic' }
}

resource sqlFirewall 'Microsoft.Sql/servers/firewallRules@2023-08-01' = if (wantSql) {
  parent: sqlServer
  name: 'AllowAzure'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ==========================================================================
// Role assignments
// ==========================================================================
// -- Deploying user / service principal -----------------------------------
resource raUserAiDeveloper 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(account.id, principalId, roleAiDeveloper)
  scope: account
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleAiDeveloper)
    principalId: principalId
    principalType: principalType
  }
}

resource raUserCognitiveUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(account.id, principalId, roleCognitiveServicesUser)
  scope: account
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleCognitiveServicesUser)
    principalId: principalId
    principalType: principalType
  }
}

resource raUserSearchIndexContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(search.id, principalId, roleSearchIndexDataContributor)
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleSearchIndexDataContributor)
    principalId: principalId
    principalType: principalType
  }
}

resource raUserSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(search.id, principalId, roleSearchServiceContributor)
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleSearchServiceContributor)
    principalId: principalId
    principalType: principalType
  }
}

// -- Foundry account managed identity (grounding / Foundry IQ retrieval) ---
resource raAccountSearchReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, account.id, roleSearchIndexDataReader)
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleSearchIndexDataReader)
    principalId: account.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ==========================================================================
// Outputs — consumed by the postprovision hook to write .env
// ==========================================================================
output AZURE_AI_PROJECT_ENDPOINT string = 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'

output MODEL_ORCHESTRATOR string = gptOrchestrator
// When Claude is skipped (deployClaudeModel=false) the two Claude-backed agents
// fall back to the GPT orchestrator deployment so the smoke test + later
// challenges still run end-to-end.
output MODEL_DRAFTING string = wantClaude ? claude : gptOrchestrator
output MODEL_CLAUSE_RISK string = wantClaude ? claude : gptOrchestrator
output MODEL_RENEWAL string = gptMini

output AZURE_SEARCH_ENDPOINT string = 'https://${search.name}.search.windows.net'
output AZURE_SEARCH_INDEX string = searchIndexName
output AZURE_SEARCH_CONNECTION_NAME string = searchConnectionName

#disable-next-line outputs-should-not-contain-secrets
output APPLICATIONINSIGHTS_CONNECTION_STRING string = appInsights.properties.ConnectionString
output AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED string = 'true'

#disable-next-line outputs-should-not-contain-secrets BCP318
output AZURE_SQL_CONNECTION_STRING string = wantSql ? 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=clmdb;Uid=clmadmin;Pwd=${sqlAdminPassword};Encrypt=yes;TrustServerCertificate=no;' : ''
