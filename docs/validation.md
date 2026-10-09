# Configuration and three-surface verification

1. Run offline tests and `scripts/check_repository.py`. Validate the selected config.
2. Run `validate --live` with explicit tenant/environment. Inspect actual report-only
   CA payload/scope. A promoted policy intentionally differs from the report-only baseline;
   record its approved promotion plan rather than redefining every drift as expected.
3. Run the Purview verifier. Inspect policy locations/rules and the Defender connector
   checklist separately. A mode or connector flag does not prove runtime behavior.
4. Choose one harmless test agent and record package ID, Entra object ID, agent appId,
   blueprint object/app IDs, owner and supported platform. Do not join across identifier
   namespaces without a confirmed mapping. Record a new UUID conversation ID and UTC
   start/end around one benign invocation. Do not store input/output contents.
5. Run the following read-only query after allowing for the service's documented ingestion
   delay. Widen only the explicit observation window if necessary; record retries.

```sh
python3 scripts/a365.py verify-invocation --live --config config/pilot.local.json \
  --tenant-id '<TEST-TENANT-ID>' --environment isolated-pilot \
  --app-id '<AGENT-APPLICATION-ID>' --conversation-id '<RUN-CONVERSATION-UUID>' \
  --since '<START-UTC-ISO8601>' --until '<END-UTC-ISO8601>' \
  --out artifacts/invocation-check.json
```

6. In Defender inspect the selected agent's activity and match the invocation. Keep
   timestamp, operation, appId, conversation ID and record/evidence reference only.
7. In Microsoft 365 admin center **Agents > All Agents**, select the same agent and
   inspect available analytics/activity for the observation period. Record the evidence
   reference. If the view exposes only aggregate activity, record that limitation rather
   than claiming exact run correlation.
8. In Purview **Solutions > Audit**, search the same UTC window and relevant agent activity
   operations for the supported platform. Match identifiers in the event where exposed.
   Inspect DSPM/AI observability if licensed and available. Do not bulk-export interaction
   contents. Missing fields or absent events are **not verifiable** for that surface.

Success requires independent evidence for each surface; Defender ingestion does not prove
Purview or admin-center visibility. Record latency and negative evidence. An agent not
invoked during the window is not automatically missing telemetry. No synthetic invocation
is sent by this CLI; the administrator chooses a benign test with the agent owner.

For enforcement or containment, perform a fresh authentication/access attempt and test each
affected channel after propagation. Existing tokens, cached sessions, alternate credentials
and externally hosted endpoints may behave differently. Preserve both configuration
readback and observed runtime outcome.

## Offline versus tenant tests

Python tests mock Graph transport, pagination, permissions failures and mutation/readback.
They validate local behavior, not Microsoft licensing, schema availability, KQL execution
or eventual consistency. The repository check validates KQL safety conventions but is not
a Kusto compiler. PowerShell mock tests run where PowerShell is installed; CI includes them.
The live pilot is the acceptance test for actual platform compatibility.
