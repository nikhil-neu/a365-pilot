# Microsoft interface references

Reviewed on 2026-10-09. Use the documented maturity and exact property/route names;
service changes may require a new review before live use. Examples in this repository
are neutral and contain no copied tenant context.

| Area | Primary reference |
| --- | --- |
| Custom agent format | [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents) |
| Slash prompts and compatibility | [VS Code prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files) |
| Registry current routing | [Agent 365 Graph APIs](https://learn.microsoft.com/en-us/microsoft-agent-365/admin/graph-api) |
| Catalog list | [List packages](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/admin-settings/package/copilotpackages-list) |
| Catalog detail | [Get package](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/admin-settings/package/copilotpackagedetail-get) |
| Reversible availability | [Block](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/admin-settings/package/copilotpackage-block), [unblock](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/admin-settings/package/copilotpackage-unblock) |
| Registry migration notice | [Legacy list API](https://learn.microsoft.com/en-us/graph/api/agentregistry-list-agentinstances?view=graph-rest-beta) |
| CA boundary | [Conditional Access for agents](https://learn.microsoft.com/en-us/entra/identity/conditional-access/agent-id) |
| CA autonomous risk baseline | [Autonomous agent policy](https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-autonomous-agents) |
| CA payload | [Conditions](https://learn.microsoft.com/en-us/graph/api/resources/conditionalaccessconditionset?view=graph-rest-beta), [agent selectors](https://learn.microsoft.com/en-us/graph/api/resources/conditionalaccessclientapplications?view=graph-rest-beta) |
| CA operations | [Create policy](https://learn.microsoft.com/en-us/graph/api/conditionalaccessroot-post-policies?view=graph-rest-beta), [update policy](https://learn.microsoft.com/en-us/graph/api/conditionalaccesspolicy-update?view=graph-rest-beta) |
| Typed identity | [Get agentIdentity](https://learn.microsoft.com/en-us/graph/api/agentidentity-get?view=graph-rest-beta), [owners](https://learn.microsoft.com/en-us/graph/api/agentidentity-list-owners?view=graph-rest-1.0) |
| Direct grants | [Application grants](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-approleassignments?view=graph-rest-1.0), [delegated grants](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list-oauth2permissiongrants?view=graph-rest-1.0) |
| Agent risk | [List riskyAgents](https://learn.microsoft.com/en-us/graph/api/riskyagent-list?view=graph-rest-beta) |
| Tenant and licenses | [Organization](https://learn.microsoft.com/en-us/graph/api/organization-list?view=graph-rest-1.0), [subscribedSkus](https://learn.microsoft.com/en-us/graph/api/subscribedsku-list?view=graph-rest-1.0) |
| Own roles | [User transitive membership](https://learn.microsoft.com/en-us/graph/api/user-list-transitivememberof?view=graph-rest-1.0) |
| Hunting execution | [Graph runHuntingQuery](https://learn.microsoft.com/en-us/graph/api/security-security-runhuntingquery?view=graph-rest-1.0) |
| Inventory schema | [AgentsInfo](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-agentsinfo-table) |
| Activity schema | [CloudAppEvents](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-cloudappevents-table) |
| Defender setup | [Security for AI setup](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/get-started-defender-security-for-ai) |
| License transition | [Agent security transition](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/transition-agent-security-to-agent-365) |
| Observability | [Concepts](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/observability-concepts), [attribute contract](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/observability-attribute-reference), [data handling](https://learn.microsoft.com/en-us/microsoft-agent-365/admin/data-residency-protection-compliance) |
| Audit | [Enable/verify audit](https://learn.microsoft.com/en-us/purview/audit-log-enable-disable) |
| DLP | [Get policy](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-dlpcompliancepolicy?view=exchange-ps), [set policy](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/set-dlpcompliancepolicy?view=exchange-ps) |
| Session identity | [Get-ConnectionInformation](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-connectioninformation?view=exchange-ps) |

Portal paths and API availability can vary by rollout/license. A missing capability is
an explicit limit, not permission to discover private APIs or bypass admin approval.
