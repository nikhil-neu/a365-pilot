# Defender, platform and connector checklist

**Manual admin step required.** No documented connector provisioning interface has been
selected for this kit; no portal network calls are replayed. Record tenant UUID/name,
selected environment/subscription, actor, UTC time, previous state and evidence reference.
Approval is required before any setup toggle or consent change.

## Defender and Microsoft 365

1. In the selected tenant's Defender portal, open **Settings > Security for AI > Get
   started**. Verify Agent 365 onboarding and the Security for AI setting. Record actual
   status; do not toggle it merely to test access.
2. Open the **Microsoft 365 connector** step. Verify **Microsoft Entra ID Management
   events**, **Microsoft 365 activities**, and prerequisite **Microsoft Entra Users and
   groups** are selected. If missing, document previous selections and obtain approval
   before connecting. After setup, verify the status is **Connected** and inspect health
   errors/last successful collection in the connector details.
3. For Copilot Studio, open its step, review real-time protection and the Power Platform
   integration. Coordinate the integration URL and same application ID with the Power
   Platform Administrator. Approval must cover the actual environment and integration
   permissions. Confirm both sides show connected and record a benign test result.

These paths and prerequisites follow Microsoft's
[setup procedure](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/get-started-defender-security-for-ai).

## Platform prerequisites and health

In Power Platform admin center verify tenant, environment UUID/type, authorized makers,
Copilot Studio availability, DLP connector classification and integration state. A
local label such as `isolated-pilot` is not a Power Platform environment UUID. Record the
actual ID in controlled evidence. Do not change environment-wide DLP for one agent without
enumerating other affected agents and flows.

In Foundry/Azure verify the directory, subscription UUID, resource group, project and
agent identities. Check project access, actual observability configuration, registration
and diagnostic delivery. Agent-level security now depends on Agent 365; an existing
Defender for Cloud plan is not enough. For third-party agents review registry sync in
the Agent 365 admin center and source-account read permissions. Use only documented
onboarding, keep changes separately approved, and record last sync/error state. See
[Microsoft's transition guidance](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/transition-agent-security-to-agent-365).

## Post-setup verification

Run `assess --live` and `validate --live`; execute `queries/inventory.kql` and
`queries/telemetry-health.kql` in Advanced Hunting. Follow [invocation validation](validation.md).
Connector connected, a present inventory row, a valid table, and a successful benign
invocation are distinct facts. Empty results, 403, missing tables, and stale timestamps
stay **not verifiable** until independently resolved. Do not mark an empty agent tenant
as healthy merely because queries returned HTTP 200.

Recover using the recorded previous selections only after approval. Disabling a connector
can remove visibility for many workloads and must not be used as a routine test rollback.

## Deploy connectors into Sentinel

The [administrator workflow](admin-deployment.md) can create Defender XDR and Office365
Sentinel connectors after approval. These are separate from the Security for AI connector
above. The Agent 365 data lake connector is also a separate onboarding path.
