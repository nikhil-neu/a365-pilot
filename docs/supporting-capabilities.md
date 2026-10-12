# Supporting capability readiness

Start the toolkit prompt with Run, choose **Supporting capability readiness**, then
select one or more capabilities using native Copilot multi-select. Choose Assess,
Set up or Verify. The coordinator presents current state, prerequisites, setup method,
approval and required verification. Nothing is enabled just by selecting it.

The offline catalog is [supporting-capabilities.json](../config/supporting-capabilities.json).
It contains workflow definitions, not tenant observations. Every initial state is
**not assessed**. Display it without authentication with:

```sh
python3 scripts/a365-toolkit.py readiness
```

| Selection | Delivery in this release | Verification required |
| --- | --- | --- |
| Frontier preview eligibility | Guided enrollment and eligibility review | Applicable feature availability and enrollment; never accept terms automatically |
| Agent risk assessment | Read-only Graph beta collector; existing CA executor for separate approved plans | Risk read evidence plus independent coverage verification |
| Defender Security for AI and connectors | Guided Microsoft 365 connector and Copilot Studio integration; existing hunting and Sentinel executors | Connected state and fresh correlated events |
| Local agent discovery | Guided endpoint prerequisites and discovery review | Selected device onboarding and fresh discovery evidence |
| Endpoint agent runtime protection | Guided documented administrator deployment; no new endpoint executor | Device setting readback plus benign runtime test |
| Purview AI interaction collection | Guided, separate opt-in; not covered by audit/DLP executor | Policy scope/status and authorized Purview-side verification |
| Copilot Studio agent identity verification | Guided exact metadata/object comparison; migration assessment | Entra Agent ID matches the agent; migration is not executed |
| Third-party risk signals | Guided partner integration and administrator opt-in | Partner-origin signal mapped to the correct agent |

For a guided setup, review the exact target and settings before proceeding to the
Microsoft portal or endpoint tooling. Native controls offer Proceed to guided setup,
Change scope, Skip and Stop. Completed/Blocked/Skip records an administrator report,
not proof that the toolkit performed or independently verified the change. Record only
nonsecret evidence references and timestamps. Missing evidence stays not verifiable.

## Agent risk collector

Use the existing [sign-in setup](setup.md). Required delegated permissions are
Organization.Read.All for identity verification, IdentityRiskyAgent.Read.All for risk
inventory and IdentityRiskEvent.Read.All for detections. The signed-in administrator
also needs a supported role, such as Security Reader. The collector neither signs in
nor grants consent. Current transport is commercial-cloud and development/test only.

```sh
python3 scripts/a365-toolkit.py risk --live \
  --config config/pilot.local.json \
  --tenant-id '<EXPLICIT-TEST-TENANT-ID>' --environment isolated-pilot \
  --out artifacts/agent-risk-01.json
```

The output contains the verified tenant, collection timestamps, API paths, projected
risk metadata and separate results for both reads. Unknown fields are null. Failed or
incomplete reads have null counts/records, never zero. Successful reads have status
skipped because no state was changed. Empty results do not demonstrate protection is
enabled. Exit 2 means the report was saved but protection coverage remains unverified;
exit 1 means validation/authentication/output failed. Files are never overwritten.
No risk dismissal, compromise confirmation, prompt contents or raw evidence strings
are collected. These beta interfaces and the collector have only been tested offline.

Sources: [riskyAgents](https://learn.microsoft.com/en-us/graph/api/riskyagent-list?view=graph-rest-beta),
[agentRiskDetections](https://learn.microsoft.com/en-us/graph/api/identityprotectionroot-list-agentriskdetections?view=graph-rest-beta).

## Guided setup details

- **Frontier:** identify the specific preview capability first. Review current eligibility
  and terms in the [enrollment guide](https://learn.microsoft.com/en-us/microsoft-agent-365/frontier).
  Do not infer entitlement from E5 or enroll a tenant automatically.
- **Defender:** follow [Security for AI setup](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/get-started-defender-security-for-ai).
  Check existing enablement, Microsoft 365 connector components and the separate
  Copilot Studio/Power Platform integration. XDR-to-Sentinel is a different connector.
- **Discovery:** use the [local discovery guide](https://learn.microsoft.com/en-us/defender-endpoint/discover-local-ai-agents)
  to review supported endpoints, onboarding and required settings. Cloud agent
  inventory does not establish endpoint coverage.
- **Runtime protection:** select exact test devices and review [supported methods and prerequisites](https://learn.microsoft.com/en-us/defender-endpoint/configure-ai-agent-runtime-protection).
  The documented settings are AiAgentProtection and AiAgentNetworkInspection via
  Set-MpPreference. Start with Audit and read back with Get-MpPreference; perform the
  documented benign demonstration. Block needs separate approval. Preserve prior
  settings for recovery. Do not execute on the toolkit host merely because it runs
  the coordinator; this repository currently supplies guidance, not a device executor.
- **Content collection:** review [Purview collection behavior](https://learn.microsoft.com/en-us/purview/ai-microsoft-purview-considerations).
  Select workloads/users, capture choice, retention and reviewer access explicitly.
  Capture is not automatically enabled by selecting all capabilities. Never copy
  prompts/responses into toolkit reports, chat or the knowledge dashboard.
- **Identity:** inspect Advanced metadata in Copilot Studio and compare the Entra Agent
  ID with the directory object. [Current identity documentation](https://learn.microsoft.com/en-us/microsoft-copilot-studio/admin-use-entra-agent-identities)
  says new agents receive IDs automatically; do not instruct admins to enable the
  retired environment opt-in. Older agents require a separate migration review.
- **Partner signals:** select the actual provider, review partner-side setup and enable
  the optional integration through Agents settings only after explicit approval.
  [Microsoft's announcement](https://techcommunity.microsoft.com/blog/agent-365-blog/whats-new-in-agent-365-%E2%80%93-july-2026/4543654)
  describes this opt-in. No public toggle executor is supplied here.

## Acceptance

Offline tests cover collector gates, field projection and unknown results. Host testing
must still confirm native selection and skip behavior. Sandbox testing must confirm
API permissions, current schemas and real signal arrival. Guided completion is never
an automatic compliance assertion. Production qualification remains outstanding.
