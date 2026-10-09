# Inventory and drift review

Use `assess --live --snapshot-out artifacts/catalog-snapshot.json` with the explicit
tenant selection. The current registry adapter follows all pages, filters recognizable
agent packages, and verifies configured identity mappings against live appIds before
reading owners/risk. Direct app-role/delegated grants are evidence, not a declaration of
effective permissions: inherited blueprint rights, tool-specific credentials and other
platform permissions require review.

The snapshot intentionally marks overall cross-platform completeness false. Unknown
catalog metadata and absent permission/tool/control evidence remain null. Null means
unknown; an empty list is an explicit observation of none. Never turn a null into an
empty list to make a report look complete.

Run:

```sh
python3 scripts/a365.py audit --config config/pilot.local.json \
  --snapshot artifacts/catalog-snapshot.json --out artifacts/drift-review.json
```

For additional documented-source evidence, create a separate normalized snapshot with
the same schema, exact tenant/environment, source references and capture time. Store
per-agent metadata only: `packageId`, `name`, `platform`, `version`, `owners`, `permissions`,
`tools`, `controls`, `agentObjectId`, `blueprintId`, `observabilityAppId`, `risk`, `lastSeen`.
Use string lists for owners, canonical permission identifiers, tools and controls; use
ISO-8601 times with timezone. Preserve the original evidence and references. This is an
operator-supplied evidence adapter, not an undocumented Microsoft API schema. The kit
cannot attest to the authenticity of a manually prepared snapshot.

The auditor rejects stale/future snapshots and duplicate IDs. It reports unapproved
agents, missing/changed owners, version/identity/platform changes, unexpected rights/tools,
missing required controls and stale telemetry. Missing expected agents only become a
definite drift when the snapshot explicitly attests to complete coverage. Unknown data
never yields a compliant result.

Review every finding with the owner. Resolve identifier mapping errors and ingestion
delays first. Compare actual grants to least-privilege requirements. Do not silently
accept an unexpected permission by rewriting approved inventory. Change the baseline
only through a reviewed repository change, with source/time/approver evidence. Hash-based
KQL drift may include JSON ordering changes; investigate rather than auto-contain.

Use named-agent containment simulation for actual risk. Keep snapshots and reports under
restricted access outside source control; follow the pilot's evidence retention decision.
