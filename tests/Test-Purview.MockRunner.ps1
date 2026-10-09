# Child process only; supplies mocked Microsoft cmdlets without importing any modules.
param([ValidateSet('good','wrong-tenant','mixed-session','wrong-mode','audit-off','missing-prefix')][string]$Case)
$tenant = '11111111-1111-4111-8111-111111111111'
$repo = Split-Path $PSScriptRoot -Parent
$cfg = Get-Content "$repo/config/pilot.example.json" -Raw | ConvertFrom-Json
$cfg.tenant.id = $tenant
$cfg.tenant.displayName = 'Mock isolated tenant'
$cfg.purview.policyNames = @('Mock policy')
$mockConfig = Join-Path ([IO.Path]::GetTempPath()) ("a365-ps-mock-" + [guid]::NewGuid() + '.json')
$cfg | ConvertTo-Json -Depth 10 | Set-Content $mockConfig
function Get-MgContext { [pscustomobject]@{TenantId=$tenant} }
function Get-MgOrganization {
    param($Property)
    [pscustomobject]@{ Id=$(if ($Case -eq 'wrong-tenant') {'wrong'} else {$tenant}); DisplayName='Mock isolated tenant' }
}
function Get-ConnectionInformation {
    [pscustomobject]@{TenantID=$tenant; State='Connected'; ModulePrefix='A365Audit'}
    [pscustomobject]@{TenantID=$(if ($Case -eq 'mixed-session') {'wrong'} else {$tenant}); State='Connected'; ModulePrefix=$(if ($Case -eq 'missing-prefix') {'Other'} else {'A365Dlp'})}
}
function Get-A365AuditAdminAuditLogConfig {
    if ($Case -in @('wrong-tenant','mixed-session','missing-prefix')) { throw 'Read occurred before valid identity' }
    [pscustomobject]@{UnifiedAuditLogIngestionEnabled=($Case -ne 'audit-off')}
}
function Get-A365DlpDlpCompliancePolicy {
    param($Identity)
    [pscustomobject]@{ Name=$Identity; Guid='44444444-4444-4444-8444-444444444444'; Mode=$(if ($Case -eq 'wrong-mode') {'Enable'} else {'TestWithoutNotifications'}) }
}
try {
    & "$repo/scripts/Test-Purview.ps1" -Config $mockConfig -TenantId $tenant -Environment isolated-pilot
    $testExit = $LASTEXITCODE
} finally {
    Remove-Item -LiteralPath $mockConfig -ErrorAction SilentlyContinue
}
exit $testExit
