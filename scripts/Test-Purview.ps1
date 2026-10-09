#requires -Version 7.2
<#
Read-only, stable Exchange/Security & Compliance cmdlets. Existing explicitly
selected sessions required. Never connects, consents or writes tenant settings.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Config,
    [Parameter(Mandatory)][guid]$TenantId,
    [Parameter(Mandatory)][string]$Environment
)
$ErrorActionPreference = 'Stop'
try {
    $cfg = Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json
    if ($cfg.schemaVersion -ne 1 -or $cfg.tenant.purpose -notin @('test', 'development') -or
        $cfg.tenant.id -ne $TenantId.ToString() -or $cfg.tenant.environment -cne $Environment) {
        throw 'Explicit test tenant/environment mismatch'
    }
    Write-Host 'Read-only Purview verification. Requires Organization.Read.All, View-Only Audit Logs and DLP read RBAC; applicable Purview licensing. No policy changes.'
    $context = Get-MgContext
    if (-not $context -or $context.TenantId -ne $TenantId.ToString()) { throw 'Graph context tenant mismatch; reconnect explicitly' }
    $org = @(Get-MgOrganization -Property Id,DisplayName)
    Write-Host ($org | Select-Object Id,DisplayName | ConvertTo-Json -Compress)
    if ($org.Count -ne 1 -or $org[0].Id -ne $TenantId.ToString() -or $org[0].DisplayName -cne $cfg.tenant.displayName) { throw 'Organization identity mismatch' }
    $connections = @(Get-ConnectionInformation)
    if ($connections.Count -lt 2 -or @($connections | Where-Object { $_.TenantID -ne $TenantId.ToString() -or $_.State -ne 'Connected' }).Count -gt 0) {
        throw 'All Exchange and compliance connections must be connected to the selected tenant; remove mixed or stale sessions'
    }
    if (@($connections | Where-Object ModulePrefix -eq 'A365Audit').Count -ne 1 -or
        @($connections | Where-Object ModulePrefix -eq 'A365Dlp').Count -ne 1) {
        throw 'Require one A365Audit Exchange session and one A365Dlp compliance session; see setup.md'
    }
    $results = @()
    $audit = Get-A365AuditAdminAuditLogConfig
    $enabled = $audit.UnifiedAuditLogIngestionEnabled -eq $true
    $results += [ordered]@{ operation='unified-audit'; status=$(if ($enabled) {'skipped'} else {'failed'}); evidence=@{ enabled=$enabled }; impact='Read-only'; rollback='None' }
    foreach ($name in $cfg.purview.policyNames) {
        if ([string]::IsNullOrWhiteSpace($name) -or $name.Contains('<')) { throw 'Replace policy placeholders before live verification' }
        $policies = @(Get-A365DlpDlpCompliancePolicy -Identity $name)
        if ($policies.Count -ne 1) { throw 'Expected exactly one named policy' }
        $policy = $policies[0]
        $matches = $policy.Mode.ToString() -eq $cfg.purview.expectedMode
        $results += [ordered]@{ operation="dlp-mode:$name"; status=$(if ($matches) {'skipped'} else {'failed'}); evidence=@{ name=$policy.Name; guid=$policy.Guid; mode=$policy.Mode.ToString(); expected=$cfg.purview.expectedMode }; impact='Read-only. Mode does not prove agent coverage; review policy locations/rules in portal.'; rollback='None' }
    }
    [ordered]@{ schemaVersion=1; tenantId=$TenantId.ToString(); environment=$Environment; capturedAt=[DateTime]::UtcNow.ToString('o'); operations=$results } | ConvertTo-Json -Depth 8
    if (@($results | Where-Object status -eq 'failed').Count) { exit 1 }
    exit 0
} catch {
    # Suppress provider output, which may contain tenant data or authentication details.
    [ordered]@{ operation='purview-verification'; status='not verifiable'; evidence='Identity, session, permissions or query validation failed. Inspect selected sessions and prerequisites; no tenant write issued.'; impact='Read-only'; rollback='None' } | ConvertTo-Json
    exit 2
}
