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
var storageName = 'clmstor${resourceToken}'
var appInsightsName = 'clm-appinsights-${resourceToken}'
var logAnalyticsName = 'clm-logs-${resourceToken}'
var containerName = 'clm-corpus'
var searchIndexName = 'clm-corpus'
var searchConnectionName = 'clm-search'

// ---- Model deployment names ----------------------------------------------
var gptOrchestrator = 'gpt-4.1'
var gptMini = 'gpt-4o-mini'
var claude = 'claude-sonnet-4-5'

// ---- Built-in role definition ids ----------------------------------------
var roleAiDeveloper = '64702f94-c441-49e6-a78b-ef80e0188fee'            // Azure AI Developer
var roleCognitiveServicesUser = 'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User
var roleSearchIndexDataContributor = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
var roleSearchServiceContributor = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
var roleSearchIndexDataReader = '1407120a-92aa-4202-b7e9-c0e197c71c8f'
var roleStorageBlobDataContributor = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var roleStorageBlobDataReader = '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'

var wantSql = toLower(deploySql) == 'true' && !empty(sqlAdminPassword)
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
// Storage — corpus source docs + clm-corpus container
// ==========================================================================
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  tags: tags
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource corpusContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: containerName
  properties: {
    publicAccess: 'None'
  }
}

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
    model: { format: 'OpenAI', name: 'gpt-4.1', version: '2025-04-14' }
  }
}

resource deployMini 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: account
  name: gptMini
  sku: { name: 'GlobalStandard', capacity: 30 }
  properties: {
    model: { format: 'OpenAI', name: 'gpt-4o-mini', version: '2024-07-18' }
  }
  dependsOn: [ deployOrchestrator ]
}

// Claude: model-format Anthropic, version "2" = Azure-hosted (vs "1" on Anthropic).
resource deployClaude 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: account
  name: claude
  sku: { name: 'GlobalStandard', capacity: 20 }
  properties: {
    model: { format: 'Anthropic', name: 'claude-sonnet-4-5', version: '2' }
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

resource raUserBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignUserRoles) {
  name: guid(storage.id, principalId, roleStorageBlobDataContributor)
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleStorageBlobDataContributor)
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

resource raAccountBlobReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, account.id, roleStorageBlobDataReader)
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleStorageBlobDataReader)
    principalId: account.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ==========================================================================
// Outputs — consumed by the postprovision hook to write .env
// ==========================================================================
output AZURE_AI_PROJECT_ENDPOINT string = 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'

output MODEL_ORCHESTRATOR string = gptOrchestrator
output MODEL_DRAFTING string = claude
output MODEL_CLAUSE_RISK string = claude
output MODEL_RENEWAL string = gptMini

output AZURE_SEARCH_ENDPOINT string = 'https://${search.name}.search.windows.net'
output AZURE_SEARCH_INDEX string = searchIndexName
output AZURE_SEARCH_CONNECTION_NAME string = searchConnectionName

#disable-next-line outputs-should-not-contain-secrets
output AZURE_STORAGE_CONNECTION_STRING string = 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
output AZURE_STORAGE_CONTAINER string = containerName

#disable-next-line outputs-should-not-contain-secrets
output APPLICATIONINSIGHTS_CONNECTION_STRING string = appInsights.properties.ConnectionString
output AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED string = 'true'

#disable-next-line outputs-should-not-contain-secrets BCP318
output AZURE_SQL_CONNECTION_STRING string = wantSql ? 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=clmdb;Uid=clmadmin;Pwd=${sqlAdminPassword};Encrypt=yes;TrustServerCertificate=no;' : ''
