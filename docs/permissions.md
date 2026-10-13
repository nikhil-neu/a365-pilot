# Permissions and licensing by operation

All live CLI operations first require delegated `Organization.Read.All` and a matching
organization response. The built-in transport uses Azure CLI's existing delegated
session; it does not create applications, request new scopes or administer consent.
Graph API permission and product RBAC are separate requirements. Use only the rows
needed for the selected operation. Unavailable permissions produce unknown checks.

| Operation | Interface / maturity | Delegated permission or cmdlet RBAC | Role / licensing assumptions |
| --- | --- | --- | --- |
| Identity check | Graph v1.0 `/organization` | `Organization.Read.All` | Tenant member with permitted read access |
| SKU inventory | Graph v1.0 `/subscribedSkus` | `LicenseAssignment.Read.All` | Directory Readers or supported license-read role; does not prove product assignment/eligibility |
| Own active directory roles | Graph v1.0 `/me/transitiveMemberOf/microsoft.graph.directoryRole` | `User.Read`; additional directory permissions may be needed for full properties | Current signed-in principal; not a full PIM/custom/product RBAC audit |
| CA read | Graph beta `/identity/conditionalAccess/policies` | `Policy.Read.All` | Security Reader (or another supported CA read role); Entra entitlement |
| CA create/state change | Same, POST/PATCH | `Policy.ReadWrite.ConditionalAccess` plus read permissions | Conditional Access Administrator; Agent 365 and Entra ID P2 for high agent risk, or qualifying suite |
| Agent identity read | Graph beta typed `agentIdentity` and owners | `AgentIdentity.Read.All` | Directory Readers or supported identity read role; Agent ID availability |
| Direct grants | Graph v1.0 service principal app-role/delegated grants | `Application.Read.All` for app-role assignments; `Directory.Read.All` for delegated grants | Supported directory/application read role; these are optional enrichment reads, not a request to add broad consent |
| Agent risk | Graph beta `/identityProtection/riskyAgents` | `IdentityRiskyAgent.Read.All` | Security Reader; agent risk preview and applicable ID Protection licensing |
| Package catalog | Graph v1.0 list/get; Agent 365 feature documented as preview | `CopilotPackages.Read.All` | AI Administrator; Agent 365 license |
| Package block/unblock | Graph beta POST action | `CopilotPackages.ReadWrite.All`, **delegated only** | AI Administrator; Agent 365; tenant-wide availability of one package |
| Advanced Hunting | Graph v1.0 `/security/runHuntingQuery` | `ThreatHunting.Read.All` | Defender hunting read access (Security Reader or scoped Unified RBAC); licensed/onboarded source tables |
| Audit check | Exchange `Get-AdminAuditLogConfig` | View-Only Audit Logs or Audit Logs management role | Applicable Purview Audit entitlement |
| DLP read | Compliance `Get-DlpCompliancePolicy` | Purview read role group containing View-Only DLP Compliance Management | Applicable Purview DLP entitlement; agent/workload capabilities vary |
| Audit enable (approved script) | `Set-AdminAuditLogConfig` | Audit Logs role | Approved tenant-wide audit change; never disable as automatic rollback |
| DLP mode change (manual) | `Set-DlpCompliancePolicy` | DLP Compliance Management | Approved policy-wide change, not a per-agent switch |
| Defender setup (manual) | Security for AI portal | Security Administrator | Agent 365, required Defender workload entitlements; Power Platform Administrator also participates for Copilot Studio |
| Foundry review/stop (manual) | Azure/Foundry portal or resource-specific ARM API | Reader for inspection; exact resource action for stop | Explicit subscription/project; provider-specific RBAC and licensing; no generic agent-stop API assumed |

Before a change, show the applicable row and concrete resources. When broader role or
permission access seems needed, report the gap and request a separate consent/assignment
decision. Do not default to Global Administrator or `Directory.ReadWrite.All`.

Commercial eligibility changes independently of API access. Check the current
[Agent 365 overview](https://learn.microsoft.com/en-us/microsoft-agent-365/overview),
[licensing FAQ](https://www.microsoft.com/licensing/faqs/122), and
[agent CA prerequisites](https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-autonomous-agents).
An available SKU, successful token acquisition, or HTTP 200 does not establish all prerequisites.
See [source index](sources.md) for per-endpoint permission references.

## Approved administrator deployment

[Deployment instructions](admin-deployment.md) cover the separate Sentinel and Purview
executors. New DLP policies/rules use `New-DlpCompliancePolicy` and `New-DlpComplianceRule`
with DLP Compliance Management and applicable workload licenses; mailbox scope resolution
uses the prefixed `Get-Mailbox` and requires Exchange recipient read access. Sentinel
uses explicit subscription-bound ARM requests, Azure resource read/write RBAC, and
connector-specific product roles. Microsoft Entra Global Administrator alone is not an
Azure resource-group role. No role assignment or consent is automated.

## Current-user Agent 365 assignment

Assessment now reads `/v1.0/me/licenseDetails` using the existing delegated session.
`LicenseAssignment.Read.All` and a supported license-details read role are required;
no consent is granted automatically. The report exposes
`currentUserHasAgent365License`: true for the documented Agent 365 SKU or its service
plan within an assigned suite; false if a complete well-formed read has no match; null
if unavailable/incomplete. This checks the signed-in administrator, not all agent owners.
Disabled/pending service-plan states are shown separately: assignment is not enablement.
Frontier and future product mappings are not inferred by name.

References: [licenseDetails](https://learn.microsoft.com/en-us/graph/api/user-list-licensedetails?view=graph-rest-1.0),
[product and plan IDs](https://learn.microsoft.com/en-us/entra/identity/users/licensing-service-plan-reference).
