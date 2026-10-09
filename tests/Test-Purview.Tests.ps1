#requires -Version 7.2
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile("$repo/scripts/Test-Purview.ps1", [ref]$tokens, [ref]$parseErrors) | Out-Null
if ($parseErrors.Count) { throw 'Purview script parse failure' }
$engine = (Get-Process -Id $PID).Path
$expected = @{good=0; 'wrong-tenant'=2; 'mixed-session'=2; 'wrong-mode'=1; 'audit-off'=1; 'missing-prefix'=2}
foreach ($case in $expected.Keys) {
    $output = & $engine -NoProfile -File "$PSScriptRoot/Test-Purview.MockRunner.ps1" -Case $case
    if ($LASTEXITCODE -ne $expected[$case]) { throw "Unexpected exit code for $case : $LASTEXITCODE" }
    if ($case -eq 'good' -and ($output -join '') -notmatch 'unified-audit') { throw 'Missing mocked audit evidence' }
    Write-Host "PASS $case"
}
