# Control matrix

| Control | Product/interface | Role/license | Automation and maturity | Verification | Rollback / boundary |
| --- | --- | --- | --- | --- | --- |
| Tenant pinning | Entra Graph organization v1.0 | Organization.Read.All | Stable, enforced on every live CLI entry | Exact selected UUID/name and environment binding | No change; reconnect explicitly on mismatch |
| License readiness | Graph subscribedSkus + admin billing | LicenseAssignment.Read.All; eligible Agent 365 suite | Stable inventory; eligibility/assignment manual | SKU capability and assigned service entitlement in admin center | No automatic purchase/assignment |
| Role readiness | Graph own directory roles + product portals | Own read; product RBAC | Stable partial evidence; manual effective-role verification | PIM active assignment, scoped roles, delegated scopes, product roles | No automatic grants |
| Risky autonomous agent access | Graph beta CA conditions/clientApplications | CA Administrator, Policy.ReadWrite.ConditionalAccess, AgentIdentity.Read.All; P2 + Agent 365 | Beta agent selectors, preview risk; create report-only and explicit promote/disable | Readback + report-only and enforced sign-ins for exact identities/resources | Disable exact policy; no token revocation or runtime stop |
| Audit ingestion | Exchange administrative audit configuration | Audit read / Audit Logs write role; Purview Audit | Stable read script; approved AuditEnable workflow | Flag plus benign event in Purview | Retain audit by default; never erase evidence |
| DLP policy mode | Purview Security & Compliance PowerShell | DLP read/manage roles; workload license | Approved new simulation policy/rule; existing-policy changes manual | Mode, scope, rule review and benign matching test | Restore exact policy's previous mode after approval; scope may span all agents/users |
| Defender prerequisites | Security for AI and Microsoft 365 connector | Security Administrator; Agent 365 + required Defender entitlements | Portal setup and health manual; hunting read automated | Connected state, workloads, timestamps and post-setup invocation | Restore only approved settings; disabling loses visibility across scope |
| SOC hunting | Graph security runHuntingQuery v1.0 / AgentsInfo | ThreatHunting.Read.All and Defender RBAC | Stable query API; preview inventory table | Queries compile and match known pilot inventory/activity in tenant | Remove shared queries; no tenant setting changed by query |
| Registry drift | Copilot package v1.0, explicit identity enrichment, normalized snapshots | AI Administrator, CopilotPackages.Read.All; optional identity/grant/risk read | Preview catalog feature; automated partial comparison | Complete pagination, ID mapping, unknown vs missing, baseline review | No changes; approve new baseline only after investigation |
| Custom telemetry | Microsoft OpenTelemetry Distro / supported framework | Observability auth model and license assignment | Manual, conditional integration; no framework found in kit | Metadata privacy inspection and three-surface invocation check | Remove exporter/config after approved change; existing retained records persist |
| Package availability containment | Graph beta block/unblock | AI Administrator, delegated CopilotPackages.ReadWrite.All, Agent 365 | Beta, simulated by default; one approved reversible action | isBlocked readback and access attempt in each channel | Opposite action only if prior state permits; not infrastructure/token termination |
| Identity disable / permission revoke | Entra documented identity-specific interface | Applicable Agent ID/Application role and exact write scope | Manual selected response; never broad blueprint revoke | Identity/grant state and fresh token test | Restore prior enabled state or exact grant after approval |
| Foundry/Copilot Studio boundaries | Provider/environment admin surfaces | Exact Azure/Power Platform roles | Manual platform review / approved stop | Selected resource/env and runtime test | Resource-specific restart; shared infrastructure blast radius must be reviewed |
| Evidence dashboard | Local escaped HTML from report | Local report access only | Automated, offline | Same operations as JSON/Markdown; explicit unknowns | Delete local rendering per retention policy; retain incident evidence |

The kit automates only its listed narrow operations. Profiles never grant permissions,
license a product or assert enforcement. See [permissions](permissions.md) and
[limitations](limitations.md) before planning a change.

The [Sentinel pack](../sentinel/README.md) adds approved workspace/onboarding, connector,
watchlist, hunting, workbook, analytics and task-automation deployment. Analytics and
automation are installed disabled, then enabled/disabled through separately approved
plans. Configuration readback, query validity, ingestion and runtime detections are
separate verification steps. See [administrator deployment](admin-deployment.md).
