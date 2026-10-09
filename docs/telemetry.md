# Telemetry without default content capture

The kit queries only metadata and never exports raw manifests, `Instructions`,
`RawAgentInfo`, full `RawEventData`, prompt/response text or tool arguments/results.
`collectContent` must remain false. Microsoft-managed platforms may collect their own
telemetry independently; this flag does not disable platform-side collection. Review
that behavior with the tenant administrator before enabling services.

No custom agent framework or authentication implementation exists in this greenfield
repository. Therefore instrumentation is **manual admin step required**, not installed.
Do not infer a framework from a profile name or add an exporter to an unrelated runtime.

For a future custom agent, inspect only its supplied source/dependency manifests. Record
language, framework and version, hosting platform, authentication flow (delegated, app-only,
Agent ID or embodied agent), appId, blueprint appId where applicable and selected tenant.
Verify compatibility against Microsoft's current integration guide. The recommended new
integration path is the Microsoft OpenTelemetry Distro; the older Agent 365 observability
SDK is deprecated. Do not install it for a new integration.

Before changing instrumentation, review exporter authentication scopes/roles and obtain
approval for any consent. Verify that content capture can be disabled in the detected
framework and exporter. Microsoft's 2026-10-01 attribute reference lists message bodies
as mandatory for certain operations. If a supported metadata-only integration cannot
meet ingestion requirements, stop that integration and report the limitation; do not
fabricate message payloads or silently turn content collection on. A separate user-approved
privacy/design decision is needed. Never collect model reasoning traces.

After a supported integration, use a synthetic benign invocation and inspect the outgoing
payload in a local test without credentials. Confirm no content or secrets, verify actual
span acceptance (including per-span rejection results), then independently verify all
three downstream surfaces. HTTP 200 alone is insufficient. At least one eligible license
assignment may be required to initialize the backend; SKU inventory is not that check.

Sources: [integration concepts](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/observability-concepts),
[attribute contract](https://learn.microsoft.com/en-us/microsoft-agent-365/developer/observability-attribute-reference),
[data handling](https://learn.microsoft.com/en-us/microsoft-agent-365/admin/data-residency-protection-compliance).
