# Purview configuration and verification

`config/pilot.example.json` is the versioned parameter set: named policies,
`TestWithoutNotifications`, audit required, no content collection. The read-only
`Test-Purview.ps1` compares actual state after validating the tenant and session identities.
Missing access is **not verifiable**, not evidence of disabled auditing.

The [administrator deployment workflow](admin-deployment.md) now automates creating
a new, explicitly scoped pilot DLP policy and rule in simulation mode, and separately
approved audit enablement. Selecting sensitive information types, locations, users,
rules and supported agent scenarios remains an administrator decision.
A universal agent-only DLP scope is not assumed. A policy's simulation mode does not
prove that the agent's data paths are covered.

## Existing-policy changes and manual alternatives

First use [setup](setup.md) and the verifier to prove tenant identity. Display exact
tenant, policy GUID/name, current mode, locations, rules, impacted users/agents, roles,
licensing and rollback. Save these fields in controlled evidence. Obtain explicit
approval for the precise change; the following are **manual admin steps**, not part of
`a365-apply` and not commands for the coordinator to run without approval.

To enable unified audit ingestion in the already verified prefixed Exchange session:

```powershell
Set-A365AuditAdminAuditLogConfig -UnifiedAuditLogIngestionEnabled $true
Get-A365AuditAdminAuditLogConfig | Select-Object UnifiedAuditLogIngestionEnabled
```

This is tenant-wide. Audit Logs role is required. Do not turn auditing off as automatic
rollback; review a separate change while preserving incident evidence.

For one existing approved pilot DLP policy, recheck that its exact GUID, current mode,
locations and rules have not changed since approval, then set only the reviewed mode:

```powershell
Set-A365DlpDlpCompliancePolicy -Identity '<EXACT-APPROVED-POLICY-GUID>' -Mode TestWithoutNotifications
Get-A365DlpDlpCompliancePolicy -Identity '<EXACT-APPROVED-POLICY-GUID>' | Select-Object Name,Guid,Mode
```

Changing an enforced policy to test mode weakens protection across its whole scope.
Prefer a dedicated pilot policy; don't repurpose an existing broad policy. Rules and
locations must be verified in Purview. Promotion to `Enable` requires a new explicit
approval after simulation review. Recovery sets the recorded prior mode for the same
policy after approval, then checks propagation and expected behavior.

Follow [validation](validation.md) for audit events. Do not export `AuditData` or interaction
contents by default; keep only actor/agent IDs, operation, timestamps and evidence references.

Sources: [audit configuration](https://learn.microsoft.com/en-us/purview/audit-log-enable-disable),
[DLP policy modes](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/set-dlpcompliancepolicy?view=exchange-ps).
