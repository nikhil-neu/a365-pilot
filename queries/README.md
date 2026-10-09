# Defender query pack

Run these in Defender Advanced Hunting, with the exact tenant and authorized hunting
role selected. `AgentsInfo` is the current preview inventory table. `CloudAppEvents`
contains runtime metadata when the relevant connector/observability path is working.
`AgentId` in observability is an appId; `EntraAgentId` in inventory is an object ID.
Do not join them by name or assume equality.

| File | Use |
| --- | --- |
| inventory.kql | Latest agent metadata, owner count, permission/tool fingerprints |
| missing-owners.kql | Ownerless or unknown-owner review queue |
| configuration-drift.kql | Changed version/permission/tool fingerprints |
| unexpected-permissions-tools.kql | Compare against approved hashes supplied by administrator |
| telemetry-health.kql | Last observed invocation by observability application ID |
| missing-telemetry.kql | Expected application IDs with no recent invocation |
| suspicious-tool-activity.kql | Tool calls outside reviewed tool list; triage signal only |
| verify-invocation.kql | Exact app/conversation/time correlation, filled safely by CLI |

Empty allowlists are deliberate placeholders, not permissive policy defaults. Populate
them through a reviewed repo change. The two freshness queries use a documented 24-hour
example threshold; adjust to the selected profile/config cadence during review. Quiet
agents need a scheduled benign invocation before declaring telemetry missing.

No raw prompts, response bodies or tool arguments are returned. Metadata hashes may
change when JSON ordering changes. Built-in risk is assessed through Graph riskyAgents
and Defender's agent detail, not an undocumented hunting column. Validate queries in the
tenant before saving as shared SOC queries; they are not scheduled detection rules.

Sources: [AgentsInfo schema](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-agentsinfo-table),
[observability field mappings](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/observability-attribute-reference).
