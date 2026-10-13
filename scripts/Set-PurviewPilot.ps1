#requires -Version 7.2
<# Explicit administrator sessions only. Plans are read-only; apply defaults to dry-run.
No login, consent, licensing, enforcement promotion or deletion is performed. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Plan','Apply')][string]$Command,
    [Parameter(Mandatory)][string]$Config,
    [Parameter(Mandatory)][string]$AdminConfig,
    [Parameter(Mandatory)][guid]$TenantId,
    [Parameter(Mandatory)][string]$Environment,
    [ValidateSet('DlpCreate','AuditEnable')][string]$Intent = 'DlpCreate',
    [string]$PlanFile,
    [switch]$Execute,
    [string]$Approve,
    [string]$EvidenceDirectory
)
$ErrorActionPreference = 'Stop'
$script:writeStarted = $false
$script:receipts = @()
function Hash-Text([string]$Text) {
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
}
function Json($Value) { return ConvertTo-Json -InputObject $Value -Depth 30 -Compress }
function Save-NewJson([string]$Path, $Value) {
    $full = [IO.Path]::GetFullPath($Path)
    $parent = [IO.Path]::GetDirectoryName($full)
    if (-not [IO.Directory]::Exists($parent)) { throw 'Create a controlled evidence parent directory first' }
    $stream = [IO.File]::Open($full, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        if (-not $IsWindows) { & chmod 600 $full; if ($LASTEXITCODE -ne 0) { throw 'Unable to protect evidence file' } }
        $writer = [IO.StreamWriter]::new($stream, [Text.UTF8Encoding]::new($false))
        try { $writer.Write((Json $Value)) } finally { $writer.Dispose() }
    } finally { $stream.Dispose() }
}
function Assert-Identity {
    $context = Get-MgContext
    if (-not $context -or $context.TenantId -ne $TenantId.ToString()) { throw 'Graph context mismatch' }
    $org = @(Get-MgOrganization -Property Id,DisplayName)
    Write-Host ($org | Select-Object Id,DisplayName | ConvertTo-Json -Compress)
    if ($org.Count -ne 1 -or $org[0].Id -ne $TenantId.ToString() -or $org[0].DisplayName -cne $cfg.tenant.displayName) { throw 'Tenant identity mismatch' }
    $sessions = @(Get-ConnectionInformation)
    if ($sessions.Count -lt 2 -or @($sessions | Where-Object { $_.TenantID -ne $TenantId.ToString() -or $_.State -ne 'Connected' }).Count -gt 0 -or
        @($sessions | Where-Object ModulePrefix -eq 'A365Audit').Count -ne 1 -or @($sessions | Where-Object ModulePrefix -eq 'A365Dlp').Count -ne 1) { throw 'Require verified A365Audit/A365Dlp sessions in only the selected tenant' }
}
function Get-Snapshot([string]$SelectedIntent) {
    if ($SelectedIntent -eq 'AuditEnable') {
        $audit = Get-A365AuditAdminAuditLogConfig
        if ($audit.UnifiedAuditLogIngestionEnabled -isnot [bool]) { throw 'Audit state is unknown' }
        return [ordered]@{ auditEnabled=$audit.UnifiedAuditLogIngestionEnabled }
    }
    # Enumerating avoids treating an authorization error on an Identity lookup as absence.
    $policies = @(Get-A365DlpDlpCompliancePolicy)
    $rules = @(Get-A365DlpDlpComplianceRule)
    if (@($policies | Where-Object Name -eq $p.policyName).Count -gt 0 -or @($rules | Where-Object Name -eq $p.ruleName).Count -gt 0) { throw 'Policy/rule already exists; create-only workflow refuses overwrite or retry' }
    $types = @(Get-A365DlpDlpSensitiveInformationType | Where-Object Name -eq $p.sensitiveInformationType)
    if ($types.Count -ne 1 -or -not $types[0].Id) { throw 'Sensitive information type must resolve exactly once' }
    $mailboxes = @()
    foreach ($upn in $p.exchangeLocations) {
        $m = @(Get-A365AuditMailbox -Identity $upn)
        if ($m.Count -ne 1 -or $m[0].RecipientTypeDetails.ToString() -ne 'UserMailbox' -or $m[0].PrimarySmtpAddress.ToString() -ne $upn -or -not $m[0].ExternalDirectoryObjectId) { throw 'Scope must resolve to an individual pilot user mailbox by primary SMTP address' }
        $mailboxes += [ordered]@{ address=$upn; objectId=$m[0].ExternalDirectoryObjectId.ToString() }
    }
    return [ordered]@{ policyAbsent=$true; ruleAbsent=$true; sensitiveTypeId=$types[0].Id.ToString(); mailboxes=$mailboxes }
}
try {
    if ($Execute -and $Command -ne 'Apply') { throw 'Execute requires Apply' }
    if ($Approve -and -not $Execute) { throw 'Approve requires Execute' }
    if (-not $PlanFile) { throw 'PlanFile required' }
    $cfg = Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json
    $admin = Get-Content -LiteralPath $AdminConfig -Raw | ConvertFrom-Json
    $p = $admin.purview
    if ($cfg.schemaVersion -ne 1 -or $admin.schemaVersion -ne 1 -or $cfg.tenant.purpose -notin @('test','development') -or $TenantId -eq [guid]::Empty -or
        $cfg.tenant.id -ne $TenantId.ToString() -or $cfg.tenant.environment -cne $Environment -or -not $cfg.tenant.displayName) { throw 'Explicit development/test tenant mismatch' }
    if ($p.policyName -cnotmatch '^A365-PILOT-[A-Za-z0-9_-]{1,64}$' -or $p.ruleName -cnotmatch '^A365-PILOT-[A-Za-z0-9_-]{1,64}$') { throw 'Invalid pilot names' }
    if ($p.minCount -isnot [long] -and $p.minCount -isnot [int]) { throw 'minCount must be an integer' }
    if ($p.minCount -lt 1 -or $p.minCount -gt 100 -or -not $p.sensitiveInformationType) { throw 'Invalid sensitive information selection' }
    if ($p.exchangeLocations -isnot [array] -or $p.sharePointLocations -isnot [array] -or ($p.exchangeLocations.Count + $p.sharePointLocations.Count) -eq 0) { throw 'Explicit DLP locations required' }
    foreach ($v in $p.exchangeLocations) { if ($v -cnotmatch '^[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$') { throw 'Explicit mailbox address required; All prohibited' } }
    foreach ($v in $p.sharePointLocations) { if ($v -cnotmatch '^https://[a-z0-9-]+\.sharepoint\.com/sites/[A-Za-z0-9_-]+$') { throw 'Explicit SharePoint site URL required; All prohibited' } }
    Write-Host 'Requires Organization.Read.All, Exchange recipient read access, DLP Compliance Management for DLP writes or Audit Logs role for audit writes; applicable Purview licensing. Only selected test tenant sessions are used.'
    $configHash = Hash-Text (Json $cfg)
    $adminHash = Hash-Text (Json $admin)
    if ($Command -eq 'Apply') {
        $doc = Get-Content -LiteralPath $PlanFile -Raw | ConvertFrom-Json
        if ($doc.schemaVersion -ne 1 -or $doc.origin -ne 'live-read-only-purview' -or $doc.approvalDigest -cne (Hash-Text $doc.planJson)) { throw 'Invalid or modified plan' }
        $plan = $doc.planJson | ConvertFrom-Json
        $createdAt = if ($plan.createdAt -is [datetime]) { [DateTimeOffset]$plan.createdAt } else { [DateTimeOffset]::Parse($plan.createdAt, [Globalization.CultureInfo]::InvariantCulture) }
        $age = [DateTimeOffset]::UtcNow - $createdAt
        if ($age.TotalSeconds -lt 0 -or $age.TotalMinutes -gt 30 -or $plan.configHash -cne $configHash -or $plan.adminHash -cne $adminHash -or $plan.tenantId -ne $TenantId.ToString() -or $plan.environment -cne $Environment) { throw 'Plan expired or configuration changed' }
        if ($plan.intent -notin @('DlpCreate','AuditEnable')) { throw 'Invalid intent' }
        $Intent = $plan.intent
        Write-Host $doc.planJson
        if ($Execute -and ($Approve -cne $doc.approvalDigest -or $cfg.profile -eq 'read-only')) { throw 'Exact human-approved digest and write-capable profile required' }
    }
    Assert-Identity
    $snapshot = Get-Snapshot $Intent
    if ($Command -eq 'Plan') {
        $plan = [ordered]@{
            createdAt=[DateTimeOffset]::UtcNow.ToString('o'); tenantId=$TenantId.ToString(); tenantName=$cfg.tenant.displayName; environment=$Environment
            intent=$Intent; configHash=$configHash; adminHash=$adminHash; snapshotJson=(Json $snapshot)
            desired=$(if ($Intent -eq 'DlpCreate') { [ordered]@{ policy=$p; mode='TestWithoutNotifications'; ruleDisabled=$false; blockAccess=$true; sensitiveTypeId=$snapshot.sensitiveTypeId } } else { @{ UnifiedAuditLogIngestionEnabled=$true } })
            impact=$(if ($Intent -eq 'DlpCreate') { 'Create one new policy/rule for explicit mailboxes/sites in simulation mode. No blocking or notifications. This is workload DLP, not universal agent-only protection.' } else { 'Enable unified audit ingestion across this entire test tenant.' })
            rollback='No automatic rollback. For a partial DLP create, inspect exact policy/rule IDs and disable the new policy after separate approval. Do not disable tenant auditing as rollback.'
            requiredRoles='DLP Compliance Management or Audit Logs; Organization.Read.All; Exchange recipient read access'; interface='Documented Exchange Online and Security & Compliance PowerShell cmdlets'
        }
        $text = Json $plan
        $doc = [ordered]@{ schemaVersion=1; origin='live-read-only-purview'; planJson=$text; approvalDigest=(Hash-Text $text) }
        Save-NewJson $PlanFile $doc
        Write-Output (Json $doc)
        exit 0
    }
    if ($plan.snapshotJson -cne (Json $snapshot)) { throw 'Remote preconditions changed; replan' }
    # Reconstruct the expected actions; never execute script text or cmdlets from a plan.
    $expected = if ($Intent -eq 'DlpCreate') { [ordered]@{ policy=$p; mode='TestWithoutNotifications'; ruleDisabled=$false; blockAccess=$true; sensitiveTypeId=$snapshot.sensitiveTypeId } } else { @{ UnifiedAuditLogIngestionEnabled=$true } }
    if ((Json $plan.desired) -cne (Json $expected)) { throw 'Plan desired state differs from supported action' }
    if (-not $Execute) { Write-Output '{"status":"skipped","evidence":"Dry-run; tenant and preconditions match. No write issued."}'; exit 0 }
    if (-not $EvidenceDirectory -or (Test-Path -LiteralPath $EvidenceDirectory)) { throw 'Supply a new evidence directory' }
    $null = New-Item -ItemType Directory -Path $EvidenceDirectory
    if (-not $IsWindows) { & chmod 700 ([IO.Path]::GetFullPath($EvidenceDirectory)); if ($LASTEXITCODE -ne 0) { throw 'Cannot protect evidence directory' } }
    Save-NewJson (Join-Path $EvidenceDirectory 'intent.json') $doc
    Assert-Identity
    if ($plan.snapshotJson -cne (Json (Get-Snapshot $Intent))) { throw 'Last-minute precondition drift' }
    $script:writeStarted = $true
    if ($Intent -eq 'AuditEnable') {
        if (-not $snapshot.auditEnabled) { Set-A365AuditAdminAuditLogConfig -UnifiedAuditLogIngestionEnabled $true -Confirm:$false }
        $after = Get-A365AuditAdminAuditLogConfig
        if ($after.UnifiedAuditLogIngestionEnabled -ne $true) { throw 'Audit readback mismatch or propagation pending' }
        $script:receipts += @{ operation='audit-enable'; status='applied'; configurationVerified=$true; runtimeEffectVerified=$false }
    } else {
        $params = @{ Name=$p.policyName; Mode='TestWithoutNotifications'; Confirm=$false }
        if ($p.exchangeLocations.Count) { $params.ExchangeLocation = [string[]]$p.exchangeLocations }
        if ($p.sharePointLocations.Count) { $params.SharePointLocation = [string[]]$p.sharePointLocations }
        $created = New-A365DlpDlpCompliancePolicy @params -ErrorAction Stop
        if (-not $created -or -not $created.Guid) { throw 'Policy creation returned no identity; inspect remote state before recovery' }
        $script:receipts += @{ operation='dlp-policy-create'; name=$p.policyName; guid=[string]$created.Guid; status='not verifiable' }
        Save-NewJson (Join-Path $EvidenceDirectory 'policy-receipt.json') $script:receipts
        $observed = @(Get-A365DlpDlpCompliancePolicy -Identity $p.policyName)
        if ($observed.Count -ne 1 -or $observed[0].Mode.ToString() -ne 'TestWithoutNotifications' -or -not $observed[0].Guid) { throw 'Policy readback mismatch' }
        $policyId = $observed[0].Guid.ToString()
        # Check that no rule appeared between policy creation and rule creation.
        if (@(Get-A365DlpDlpComplianceRule | Where-Object Name -eq $p.ruleName).Count) { throw 'Rule appeared concurrently; stopping partial deployment' }
        $sensitive = @(@{ Name=[string]$p.sensitiveInformationType; minCount=[string]$p.minCount })
        $rule = New-A365DlpDlpComplianceRule -Name $p.ruleName -Policy $policyId -ContentContainsSensitiveInformation $sensitive -BlockAccess $true -Disabled $false -Confirm:$false -ErrorAction Stop
        if (-not $rule -or -not $rule.Guid) { throw 'Rule creation returned no identity; inspect remote state before recovery' }
        $script:receipts += @{ operation='dlp-rule-create'; name=$p.ruleName; guid=[string]$rule.Guid; policyGuid=$policyId; status='not verifiable' }
        Save-NewJson (Join-Path $EvidenceDirectory 'rule-receipt.json') $script:receipts
        $after = @(Get-A365DlpDlpComplianceRule -Identity $p.ruleName)
        if ($after.Count -ne 1) { throw 'Rule readback unavailable' }
        # Cmdlet location/rule representations differ across workloads. Preserve uncertainty
        # instead of treating creation or mode alone as proof of effective DLP coverage.
        $script:receipts += @{ operation='dlp-simulation'; status='not verifiable'; policyGuid=$policyId; policyMode='TestWithoutNotifications'; evidence='Policy and rule created/read back. Verify exact locations, sensitive-information predicate, rule action and distribution status in Purview; then run a benign test.'; runtimeEffectVerified=$false }
    }
    $unknown = @($script:receipts | Where-Object status -eq 'not verifiable').Count -gt 0
    $outcome = @{ status=$(if ($unknown) {'not verifiable'} else {'applied'}); operations=$script:receipts }
    Save-NewJson (Join-Path $EvidenceDirectory 'outcome.json') $outcome
    Write-Output (Json $outcome)
    if ($unknown) { exit 2 }; exit 0
} catch {
    $outcome = @{ status='not verifiable'; writeAttempted=$script:writeStarted; operations=$script:receipts; evidence='Validation, session, permission, write or readback failed. Provider output withheld. If writeAttempted, inspect intent and exact resource state before retrying; partial changes may exist.' }
    if ($script:writeStarted -and $EvidenceDirectory -and -not (Test-Path (Join-Path $EvidenceDirectory 'outcome.json'))) { Save-NewJson (Join-Path $EvidenceDirectory 'outcome.json') $outcome }
    Write-Output (Json $outcome)
    exit 2
}
