# a365-toolkit capability matrix

This is the delivery baseline, not a claim of complete Microsoft product coverage.
The machine-readable counterpart is [capabilities.json](../config/capabilities.json).
Current deployment code is offline/mock tested; live service behavior is not established.

| Service | Available implementation | Missing or separately performed | Acceptance evidence needed |
| --- | --- | --- | --- |
| Entra | Narrow high-risk agent CA create/report-only, promote and disable | Broader baseline and production qualification | Exact identity/resource scope, policy readback and tested sign-in behavior |
| Defender | Available inventory/hunting reads; XDR-to-Sentinel connector deployment | Security for AI portal onboarding; comprehensive connector health verification | Connected required workloads, fresh telemetry and a correlated benign invocation |
| Purview audit | Read state and separately approved tenant-wide enablement | End-to-end agent/workload audit coverage | Enabled state plus expected events with correct actor and timestamps |
| Purview DLP | New explicit mailbox/site policy and rule in simulation | Existing-policy reconciliation, enforcement promotion, agent-path coverage | Effective scope, predicate, distribution status and benign matching test |
| Sentinel ingestion | Workspace, onboarding, XDR and Office365 connectors | Separate Agent 365 data lake onboarding; more data sources | Provisioning, connector health, actual schemas and fresh records |
| Sentinel content | Three hunting queries, watchlist, two scheduled rules, workbook, incident-task automation; approved enable/disable | Broader agent-specific detections, tuning and executable response runbooks | Queries compile, expected test signals, correct attribution and incident/task behavior |
| Response | Registry block/unblock workflow; documented human triage | Executable response automation beyond these operations | Exact approved target, readback, runtime effect and tested recovery |
| Administration | Copilot Chat selection/approval workflow, shared command entry point, scoped plans, approval digests, receipts and inventory comparison | Cross-service orchestration, consolidated readiness, general drift repair and production qualification | No unapproved changes; state drift stops execution; partial changes remain recoverable |

## Delivery sequence

1. **Product alignment (this milestone):** name, capability inventory, shared command entry
   point, deployment lifecycle and accurate client documents.
2. **Unified orchestration:** environment-aware configuration, dependency graph, consolidated
   readiness and plans, service-specific approval boundaries and resumable execution.
3. **Coverage expansion:** documented Defender provisioning paths where supported, DLP
   lifecycle management, more agent-specific Sentinel content and executable runbooks.
4. **Production qualification:** sandbox service validation, existing-resource reconciliation,
   rollout/repair/recovery tests and explicit production deployment support.

Licenses, permissions, supported APIs and tenant availability are prerequisites. For an
unavailable automation interface, the toolkit should name the exact admin step and verify
its result where possible. It must not report that component as deployed automatically.

## Supporting capability readiness

Choose **Supporting capability readiness** in the toolkit agent for Frontier, agent
risk, Defender onboarding, local discovery, endpoint runtime protection, Purview
collection, agent identities and partner signals. The new risk collector is read-only;
the other new capabilities provide guided setup and verification, not new deployment
executors. See [delivery status and instructions](supporting-capabilities.md).
