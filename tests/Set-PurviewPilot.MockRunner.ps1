param([string]$Case)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$tenant = '11111111-1111-4111-8111-111111111111'
$work = Join-Path ([IO.Path]::GetTempPath()) ('a365-admin-test-' + [guid]::NewGuid())
$null = New-Item -ItemType Directory $work
$cfg = Get-Content "$repo/config/pilot.example.json" -Raw | ConvertFrom-Json
$cfg.tenant.id = $tenant; $cfg.tenant.displayName = 'Mock tenant'
$admin = Get-Content "$repo/config/admin.example.json" -Raw | ConvertFrom-Json
$admin.purview.exchangeLocations = @('pilot@example.test')
$cfg | ConvertTo-Json -Depth 15 | Set-Content "$work/pilot.json"
$admin | ConvertTo-Json -Depth 15 | Set-Content "$work/admin.json"
$global:a365Mock = @{}
$global:a365Mock.writes = @()
$global:a365Mock.policy = $null; $global:a365Mock.rule = $null; $global:a365Mock.audit = $false
$global:a365Mock.phase = 'plan'
function Get-MgContext { [pscustomobject]@{TenantId=$tenant} }
function Get-MgOrganization {
    param($Property)
    [pscustomobject]@{Id=$(if ($Case -eq 'wrong-tenant') {'wrong'} else {$tenant}); DisplayName='Mock tenant'}
}
function Get-ConnectionInformation {
    [pscustomobject]@{TenantID=$tenant; State='Connected'; ModulePrefix='A365Audit'}
    [pscustomobject]@{TenantID=$(if ($Case -eq 'mixed-session') {'wrong'} else {$tenant}); State='Connected'; ModulePrefix='A365Dlp'}
}
function Get-A365AuditMailbox { param($Identity) [pscustomobject]@{RecipientTypeDetails='UserMailbox'; PrimarySmtpAddress=$Identity; ExternalDirectoryObjectId='33333333-3333-4333-8333-333333333333'} }
function Get-A365AuditAdminAuditLogConfig { [pscustomobject]@{UnifiedAuditLogIngestionEnabled=$global:a365Mock.audit} }
function Set-A365AuditAdminAuditLogConfig {
    param($UnifiedAuditLogIngestionEnabled, $Confirm)
    $global:a365Mock.writes += 'audit'; $global:a365Mock.audit = $UnifiedAuditLogIngestionEnabled
}
function Get-A365DlpDlpSensitiveInformationType { [pscustomobject]@{Name='Credit Card Number'; Id='44444444-4444-4444-8444-444444444444'} }
function Get-A365DlpDlpCompliancePolicy {
    param($Identity)
    if ($Case -eq 'permission-failure') { throw '403' }
    if ($Case -eq 'existing-policy' -or ($Case -eq 'drift' -and $global:a365Mock.phase -eq 'apply')) { return [pscustomobject]@{Name=$admin.purview.policyName; Mode='Enable'; Guid='existing'} }
    if ($global:a365Mock.policy) { $global:a365Mock.policy }
}
function Get-A365DlpDlpComplianceRule { param($Identity) if ($global:a365Mock.rule) { $global:a365Mock.rule } }
function New-A365DlpDlpCompliancePolicy {
    param($Name, $Mode, $ExchangeLocation, $SharePointLocation, $Confirm)
    if (-not (Test-Path "$work/evidence/intent.json")) { throw 'Missing durable intent before mutation' }
    if ($Mode -ne 'TestWithoutNotifications' -or @($ExchangeLocation).Count -ne 1 -or $ExchangeLocation[0] -ne 'pilot@example.test') { throw 'Unsafe DLP parameters' }
    $global:a365Mock.writes += 'policy'
    $global:a365Mock.policy = [pscustomobject]@{Name=$Name; Mode=$Mode; Guid='55555555-5555-4555-8555-555555555555'}
    $global:a365Mock.policy
}
function New-A365DlpDlpComplianceRule {
    param($Name, $Policy, $ContentContainsSensitiveInformation, $BlockAccess, $Disabled, $Confirm)
    $global:a365Mock.writes += 'rule'
    if ($Case -eq 'partial-failure') { throw 'Timeout' }
    if ($Policy -ne $global:a365Mock.policy.Guid -or $Disabled -or -not $BlockAccess -or $ContentContainsSensitiveInformation[0].minCount -ne 1) { throw 'Unsafe rule parameters' }
    $global:a365Mock.rule = [pscustomobject]@{Name=$Name; Guid='66666666-6666-4666-8666-666666666666'}
    $global:a365Mock.rule
}
try {
    $params = @{ Config="$work/pilot.json"; AdminConfig="$work/admin.json"; TenantId=$tenant; Environment='isolated-pilot'; PlanFile="$work/plan.json" }
    if ($Case -eq 'audit-enable') { $params.Intent = 'AuditEnable' }
    $null = & "$repo/scripts/Set-PurviewPilot.ps1" -Command Plan @params
    $planCode = $LASTEXITCODE
    if ($Case -in @('wrong-tenant','mixed-session','existing-policy','permission-failure')) {
        if ($planCode -ne 2 -or $global:a365Mock.writes.Count) { throw 'Unsafe plan behavior' }
    } else {
        if ($planCode -ne 0 -or $global:a365Mock.writes.Count) { throw 'Plan failed or mutated state' }
        $global:a365Mock.phase = 'apply'
        $doc = Get-Content "$work/plan.json" -Raw | ConvertFrom-Json
        if ($Case -eq 'tampered') { $doc.planJson += ' '; $doc | ConvertTo-Json -Depth 30 | Set-Content "$work/plan.json" }
        if ($Case -eq 'expired') {
            $plan = $doc.planJson | ConvertFrom-Json
            $plan.createdAt = '2000-01-01T00:00:00Z'
            $doc.planJson = $plan | ConvertTo-Json -Depth 30 -Compress
            $doc.approvalDigest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($doc.planJson))).ToLowerInvariant()
            $doc | ConvertTo-Json -Depth 30 | Set-Content "$work/plan.json"
        }
        $applyParams = @{}
        if ($Case -ne 'dry-run') { $applyParams.Execute=$true; $applyParams.Approve=$(if ($Case -eq 'wrong-approval') {'wrong'} else {$doc.approvalDigest}); $applyParams.EvidenceDirectory="$work/evidence" }
        $null = & "$repo/scripts/Set-PurviewPilot.ps1" -Command Apply @params @applyParams
        $code = $LASTEXITCODE
        if ($Case -eq 'dry-run') { if ($code -ne 0 -or $global:a365Mock.writes.Count) { throw 'Dry-run mutated or failed' } }
        elseif ($Case -eq 'audit-enable') { if ($code -ne 0 -or ($global:a365Mock.writes -join ',') -ne 'audit') { throw 'Audit apply failed' } }
        elseif ($Case -in @('create','partial-failure')) {
            if ($code -ne 2 -or ($global:a365Mock.writes -join ',') -ne 'policy,rule' -or -not (Test-Path "$work/evidence/outcome.json")) { throw 'Expected recorded DLP writes and unverified effective coverage' }
        } else { if ($code -ne 2 -or $global:a365Mock.writes.Count) { throw 'Approval/state gate failed' } }
    }
    Write-Host "PASS Purview admin $Case"
} finally { Remove-Item -LiteralPath $work -Recurse -Force }
