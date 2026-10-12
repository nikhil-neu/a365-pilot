# Agent Knowledge Exposure

Open [index.html](index.html) directly in a browser. No server, hosting, Microsoft
Copilot integration, tenant connection or package installation is required. The existing
VS Code Copilot workflow is unchanged. All assets are local and the page's content
security policy prohibits network connections. Source locations are displayed as text,
not navigated automatically. Nothing is persisted to browser storage.

The initial view is **SAMPLE DATA**, loaded from [sample.js](sample.js), generated from
[sample.json](sample.json). Every agent, owner, label assignment and runtime observation
in this fixture is fictional. Select **Load JSON** to import an authorized metadata export;
select **Reset to sample** to restore the preview. Files are limited to 5 MB. Validation
rejects malformed records without replacing the current dataset. Close the page to clear
loaded data. Avoid uploading this dashboard or sensitive exports to a public website.

## Available repository data

The existing `inventory_snapshot` interface in `scripts/a365/operations.py` exposes
`packageId`, `name`, `platform`, `owners`, identity mappings and enrichment metadata.
It does **not** expose configured knowledge-source relationships, container labels,
content labels, connection access context or source-level runtime retrieval evidence.
These must come from a separately authorized platform/configuration export or operator
metadata snapshot. A [read-only Copilot Studio collector](../../docs/knowledge-collection.md) now reads supported knowledge component metadata. Labels and runtime retrieval remain uncollected.
Do not infer knowledge sources from app permissions or from the existing hunting queries.

This format reuses the agent inventory field names but is a separate interface, not a
replacement for the existing inventory/audit format. It can represent an agent with no
source inventory (`sources: null`, `sourcesComplete: false`) without inventing sources.

## JSON format, version 1

The complete example is [sample.json](sample.json). The browser's strict validator is
[model.js](model.js); additional fields are rejected to keep exports metadata-only.

| Root field | Format / meaning |
| --- | --- |
| `schemaVersion` | Integer `1` |
| `dataKind` | `sample` or `tenant-export`; exporter declaration, not authenticated provenance |
| `name` | Dataset display name |
| `capturedAt` | ISO timestamp with timezone |
| `complete` | Whether the exporter claims the agent inventory covers its intended scope |
| `labels` | Array of `{id, name, rank}`; rank is an explicitly supplied nonnegative integer or null. Higher means more sensitive. No name-based ordering is inferred. |
| `discoveredContainers` | Observation whose value is an array of unique container/site IDs, or null if unavailable. Includes unconnected containers only when actually discovered. |
| `agents` | Agent records described below |

An agent has `packageId` (unique stable ID), `name` and `platform` (string or null),
`owners` (string array or null), `evidence` (metadata provenance below), `sourcesComplete`
(boolean), and `sources` (array or null). An empty complete array means the export confirms
no configured sources; null means unavailable. Agent evidence applies to its identity,
name, platform and owner metadata. Split exports if those cannot share provenance.

A source has an `id` unique within the agent, plus every observation field below.
All fields are required; supply null when unknown rather than omitting a field.

```json
{
  "value": null,
  "evidence": {
    "source": "Platform export or evidence reference; value not exposed",
    "checkedAt": null
  }
}
```

Known source values require an evidence timestamp with timezone. Unknown values may have
a timestamp documenting an attempted check. `checkedAt` is when the supporting evidence
was observed, not proof that labels or permissions remain current. `capturedAt` never
substitutes for missing field-level evidence.

| Source observation | Value |
| --- | --- |
| `name`, `type`, `location` | String or null. Location is a redacted URL/path. HTTP(S) URLs must omit credentials, query parameters and fragments. |
| `container` | `{id, kind}` with kind `site` or `container`; null if mapping unknown; `{id: null, kind: "notApplicable"}` for an explicitly non-container source |
| `containerLabel` | Label ID or null; only a site/container classification, never inferred from content |
| `contentLabels` | Array of label IDs from content-classification evidence, or null. Empty means no labels recorded in the supplied evidence, not proof all content is unlabeled. |
| `external` | Boolean or null, determined by the exporter relative to its declared organizational boundary; not inferred from hostname |
| `accessContext` | String or null; only expose delegated/maker-provided context supported by platform evidence. Not a claim of effective user access. |
| `lastCheck` | Last source sync/check timestamp with timezone or null; its evidence identifies which kind of check it represents |
| `runtimeRetrieved` | true only if source-level runtime retrieval is evidenced; false means not observed in the supplied evidence, never proof no retrieval occurred; null if unavailable |

Never include prompts, responses, document bodies, query text, credentials, tokens or
raw API payloads. Validation is a shape check, not a secret scanner: redact all metadata
before export. Labels and ranks must be provided by the authorized exporter. The viewer
cannot establish whether a supplied runtime observation is authentic.

## Calculations and interaction

Metrics cover the entire loaded dataset; filters only narrow source rows and the agent
list. Agent flags always use all its configured sources, so filtering away one source
does not erase a mixed-sensitivity finding. Agents with unavailable source inventories
remain visible unless a source-specific filter is applied.

- Discovered count: distinct IDs in `discoveredContainers.value`; null is Not available.
  This is the supplied inventory count, not a claim to have enumerated the whole tenant.
- Connected count: distinct configured container IDs across agents; repeated relationships
  to the same container are counted once. Missing mappings or partial coverage yield a
  lower bound; zero with incomplete coverage is Unknown.
- Highest label: maximum explicitly ranked **container** label, with ties shown together.
  Unknown labels are counted separately. If a known label has no rank, highest is Unknown.
- Mixed sensitivity: at least two different known container label IDs. Content labels
  do not affect this flag. A negative finding requires complete sources and known labels.
- Multiple containers: at least two distinct container IDs, not two documents/URLs.
- External: any explicitly external configured source. Unknown classifications remain unknown.
- Summary flag counts: confirmed positives, with unresolved-agent counts and partial-inventory
  notes. Unknown is displayed instead of a misleading zero when coverage is incomplete.

Search matches agent, owner, platform, source name/type and location. Filters compose with
AND. Source columns sort by agent/name, label rank, and external status; unknown values
stay last in either direction. Details show every configured source's field-level evidence,
reasons behind flags and suggested reviews. Review actions are advisory only.

## Maintenance and offline checks

Regenerate the file-compatible sample after editing its JSON:

```sh
python3 -c 'import json,pathlib; p=pathlib.Path("dashboards/knowledge-exposure"); (p/"sample.js").write_text("window.KNOWLEDGE_SAMPLE = "+json.dumps(json.loads((p/"sample.json").read_text()), indent=2)+";\n")'
node tests/knowledge-exposure.test.js
python3 -m unittest discover -s tests -q
python3 scripts/check_repository.py
```

The sample wrapper avoids `fetch` restrictions when opening `file://` pages. The same
calculation/validation module is used by the browser and Node tests. No generated count
is hardcoded into the page.

Optional browser integration test: with Playwright available to Node and
`CHROME_PATH` pointing to a Chrome/Chromium executable, run
`node tests/knowledge-exposure.browser.cjs`. It uses a temporary browser profile,
opens the page via file://, checks interactions and saves desktop/mobile screenshots
under /tmp. Playwright is a development-test dependency only, not a dashboard dependency.

## Data governance review

The data-first section groups exact configured locations and lists all connected agents
in the loaded snapshot. Sources without a location fall back to known container IDs;
unresolved sources remain separate. This is not canonical file/site resolution. Its
search is independent of the agent filters. Expand each location to review source-level
labels, access context, runtime evidence and timestamps, plus suggested remediation.

No JSON schema change is required. Effective permissions, sharing and applicable DLP
coverage are not in the current collector/schema and display Not available. Unknown
labels are not classified as unlabeled. Agent owners are not assumed to own the data.
The view performs no mutations and does not infer that a configured source was read.

## Simplified design preview

Open [wireframe.html](wireframe.html) locally for the proposed data-first layout.
Search and filter locations, then select a row to inspect connected agents, protection
evidence and suggested next steps. All fixtures, risk findings and timestamps are
fictional. This standalone wireframe does not authenticate, import tenant data or
change settings. The existing snapshot dashboard remains available via its link.
