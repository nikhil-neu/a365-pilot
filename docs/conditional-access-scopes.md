# Conditional Access scope selection

Existing configurations retain individual identity targeting and selected resources.
For a blueprint review, use [the example](../config/blueprint-ca.example.json).
The optional `conditionalAccess.targetType` is `individual` (default) or `blueprint`.
`agentObjectIds` then contains tenant service-principal object IDs of that type;
for blueprints it must not contain the global blueprint application ID. Live planning
checks the typed Graph endpoint before constructing the policy.

`resourceScope` is `selected` (default) or `all`. Selected resources require explicit
application IDs in `resourceAppIds`. All resources requires an empty list and emits
`includeApplications: ["All"]`. It never means all agents.

Blueprint scope includes current and future derived autonomous identities across the
tenant, not just a selected Copilot Studio environment. It excludes delegated user
flows, agent user accounts and blueprint provisioning tokens. All resources covers
Entra-protected token requests, not access using API keys or all file permissions.
The baseline remains high agent risk, block access, report-only: no actual blocking.

Expanded scopes are **plan-only** in this release, including when an apply digest is
provided. The Graph beta payload needs live qualification before enabling deployment.
Read failures or an unknown blueprint principal must remain unresolved; never substitute
all agent identities or claim the plan has been verified. Existing narrow scopes retain
their approval-bound deployment behavior.

For the IBM walkthrough, select blueprint and All resources, resolve the shared Copilot
Studio blueprint principal in that tenant, and stop after the read-only plan. No new
resource application ID is needed. Do not overwrite an earlier configuration or plan.

Microsoft documents [blueprint and resource targeting](https://learn.microsoft.com/en-us/entra/identity/conditional-access/howto-target-agent-identities)
and the [Graph beta client application schema](https://learn.microsoft.com/en-us/graph/api/resources/conditionalaccessclientapplications?view=graph-rest-beta).
