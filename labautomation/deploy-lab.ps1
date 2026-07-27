<#
  deploy-lab.ps1 — EMEA MicroHack platform entry point for the Foundry CLM microhack.

  The microsoft/MicroHack platform invokes THIS script (never deploy.ps1/.sh) to
  provision a team's environment. It passes the parameter block below verbatim and
  SILENTLY SKIPS the script if the contract does not match exactly. The platform:
    - has already set the Az context to $SubscriptionId  -> do NOT Connect-AzAccount
    - for 'resourcegroup' modes: pre-created the RG and granted Owner -> do NOT New-AzResourceGroup
    - for 'subscription' mode: granted Owner on the subscription -> we create the RG ourselves
      with a deterministic per-user name via Get-MhhStableHash
    - imported Az.Accounts and Az.Resources for us

  Resources are provisioned from infra/resources.bicep (the resource-group-scoped
  module also used by `azd up`). deploy.ps1 / deploy.sh remain the local/Codespaces
  path; this script is the platform path.
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('subscription', 'resourcegroup', 'resourcegroup-with-subscriptionowner')]
    [string]$DeploymentType,

    [Parameter(Mandatory = $true)]
    [string]$SubscriptionId,

    [string]$ResourceGroupName = "",

    [string[]]$PreferredLocation = @(),

    [string[]]$AllowedEntraUserIds = @()
)

$ErrorActionPreference = 'Stop'

# --- Effective region -------------------------------------------------------
# Priority order from the platform; fall back to swedencentral, which offers the
# gpt-5.4 / gpt-5-mini deployments and the Anthropic Claude Sonnet 4.5 marketplace offer.
$effectiveLocation = if ($PreferredLocation.Count -gt 0) { $PreferredLocation[0] } else { 'swedencentral' }

# --- Resolve / create the resource group per the platform contract ----------
if ($DeploymentType -eq 'subscription') {
    # We own the subscription; create a deterministic, per-user resource group.
    $hashInput = if ($AllowedEntraUserIds.Count -gt 0) { $AllowedEntraUserIds } else { @($SubscriptionId) }
    $stableHash = Get-MhhStableHash $hashInput -Length 24
    $effectiveResourceGroup = "rg-clm-microhack-$stableHash"
    New-AzResourceGroup -Name $effectiveResourceGroup -Location $effectiveLocation -Force | Out-Null
}
else {
    # 'resourcegroup' / 'resourcegroup-with-subscriptionowner': the RG is pre-created and we hold Owner.
    $effectiveResourceGroup = $ResourceGroupName
}

# --- Deterministic token for globally-unique resource names -----------------
# resources.bicep names Search/Foundry/etc. as clm*${resourceToken}. Bicep's
# uniqueString() isn't available in PowerShell, so derive a stable lowercase token.
$resourceToken = (Get-MhhStableHash "$SubscriptionId-$effectiveResourceGroup" -Length 13).ToLower()

# --- RBAC principal ---------------------------------------------------------
# Grant the first allowed lab user data-plane roles (resources.bicep skips role
# assignments when principalId is empty).
$principalId = if ($AllowedEntraUserIds.Count -gt 0) { $AllowedEntraUserIds[0] } else { '' }

# --- Deploy -----------------------------------------------------------------
$scriptPath   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$templateFile = Join-Path $scriptPath 'infra/resources.bicep'
$tags = @{ project = 'foundry-clm-microhack'; 'lab-deployment-type' = $DeploymentType }

Write-Host "Deploying Foundry CLM microhack -> RG '$effectiveResourceGroup' ($effectiveLocation), token '$resourceToken'"

$deployment = New-AzResourceGroupDeployment `
    -ResourceGroupName $effectiveResourceGroup `
    -TemplateFile $templateFile `
    -location $effectiveLocation `
    -resourceToken $resourceToken `
    -principalId $principalId `
    -principalType 'User' `
    -deployClaudeModel 'true' `
    -deploySql 'false' `
    -deployBing 'false' `
    -tags $tags `
    -Verbose

# --- Return credentials / endpoints to the user dashboard -------------------
# The platform captures every @{ HackboxCredential = ... } written to the output stream.
@{ HackboxCredential = @{ name = 'ResourceGroup'; value = $effectiveResourceGroup; note = 'Resource group holding your CLM microhack resources' } }

$projectEndpoint = "$($deployment.Outputs.AZURE_AI_PROJECT_ENDPOINT.Value)"
if ($projectEndpoint) {
    @{ HackboxCredential = @{ name = 'FoundryProjectEndpoint'; value = $projectEndpoint; note = 'Microsoft Foundry project endpoint -> AZURE_AI_PROJECT_ENDPOINT in .env' } }
}

$searchEndpoint = "$($deployment.Outputs.AZURE_SEARCH_ENDPOINT.Value)"
if ($searchEndpoint) {
    @{ HackboxCredential = @{ name = 'SearchEndpoint'; value = $searchEndpoint; note = 'Azure AI Search endpoint -> AZURE_SEARCH_ENDPOINT in .env' } }
}
