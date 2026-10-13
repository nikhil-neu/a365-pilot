# Limits and interface maturity

Reviewed 2026-10-09. This repository is a pilot implementation, not proof of tenant readiness.

- Agent CA targeting and `agentIdRiskLevels` use Graph beta. Risk signals and `AgentsInfo`
  are documented preview features. The kit selects individual autonomous agent identities,
  explicit resources and high risk for execution. Blueprint targeting and All resources
  are available for plan-only review pending live API qualification. Agent-user/delegated flows and blueprint provisioning
  tokens are not covered by this baseline. No wildcard/tenant-wide fallback exists.
- The current registry uses Copilot package APIs. List/get use documented v1.0 routes;
  the Agent 365 registry feature remains described as preview. Block/unblock are beta and
  support delegated permissions only. Legacy `/agentRegistry/agentInstances` is not used.
- No cross-platform inventory completeness is asserted from package enumeration. Effective
  grants, tools, control coverage and telemetry may require normalized documented-source
  evidence. Dynamic schema fields are not guessed. Risk is read from the beta riskyAgents
  API; no invented `RiskLevel` column is added to `AgentsInfo`.
- A profile is a recommendation and baseline, not an enforcement boundary. Scope may be
  tenant-wide, package-wide, policy-wide or shared across a blueprint. Only `read-only`
  additionally blocks mutation planning. Per-agent isolation requires platform support.
- Approved administrator scripts now support Sentinel foundation/connectors/content,
  new scoped DLP simulation policies/rules, and audit enablement. See [deployment](admin-deployment.md).
  Defender Security for AI portal onboarding, Power Platform/Foundry setup, existing DLP
  changes/enforcement, identity disabling, permission revocation and compute stops remain
  manual. Never replay portal-private APIs.
- SKU and role reads are partial readiness evidence. Eligible license assignment, terms
  acceptance, PIM/custom RBAC, product-specific roles and effective consent require an
  administrator. Current Azure CLI permissions may not cover the new Graph scopes; the
  CLI does not acquire them automatically. Commercial global cloud only is supported.
- Custom observability is conditional on a detected framework/authentication model and a
  supported no-content configuration. No agent runtime exists here; see telemetry.md.
- KQL files use documented current names but have not been compiled against a tenant.
  The separate Sentinel pack can deploy a workbook against SecurityAlert/OfficeActivity
  after approval. Defender tables are not assumed to exist in Log Analytics. Reports
  also supply a local HTML dashboard. Sentinel rules/automation are created disabled.
- All plans require freshness and exact current-state agreement, but the APIs lack a
  toolkit-wide atomic transaction/lock. Concurrent administrator changes remain a race.
  A digest binds a plan, not an approver identity; keep approval in a controlled change system.
- Readback proves configuration state, not token revocation or runtime enforcement. Empty
  query results and missing telemetry are not healthy outcomes. Writes are never retried.
- Output reports may contain security metadata, names and identifiers. Exclude them from
  source control, restrict access and choose a retention period. The repository's privacy
  setting does not control Microsoft-managed platform content collection.
- Custom `.agent.md` frontmatter uses only `name` and `description`; prompts use only
  `description` and `agent`. No tool IDs are invented. The current VS Code documentation
  says prompt files work with Local agent sessions but are deprecated/unloaded in Agent
  Host sessions. Use a compatible Local session to run the requested slash commands;
  the deterministic CLI is independent of that UI. GitHub Copilot surfaces differ in
  which customizations they load; prompt files are a VS Code mechanism.

Offline tests cannot establish service availability or live deployment success. No live
deployment, query execution or PowerShell service verification is claimed by bootstrap.
