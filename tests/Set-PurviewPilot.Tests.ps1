#requires -Version 7.2
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$tokens = $null; $errors = $null
[System.Management.Automation.Language.Parser]::ParseFile("$repo/scripts/Set-PurviewPilot.ps1", [ref]$tokens, [ref]$errors) | Out-Null
if ($errors.Count) { throw ($errors | Out-String) }
$engine = (Get-Process -Id $PID).Path
foreach ($case in @('dry-run','create','audit-enable','wrong-approval','tampered','expired','wrong-tenant','mixed-session','existing-policy','permission-failure','drift','partial-failure')) {
    & $engine -NoProfile -File "$PSScriptRoot/Set-PurviewPilot.MockRunner.ps1" -Case $case
    if ($LASTEXITCODE -ne 0) { throw "Purview admin test failed: $case" }
}
