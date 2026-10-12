# Read-only knowledge metadata collection

The dashboard can now consume exports from two real-data paths. Both run outside the
browser, reuse the dedicated Azure CLI cache and verify the explicit tenant through
Graph before reading platform metadata. Neither logs in, grants consent or modifies
settings. Current live execution remains development/test-only.

## Copilot Studio: configured knowledge metadata

This path reads the selected Dataverse environment's `bot` records and active
`botcomponent` records of types 16 (Knowledge Source) and 14 (File Attachment). It
projects metadata only. It does not read topics, agent instructions, conversation
transcripts, file bodies or prompt/response contents. The YAML `data` field is read only
for Knowledge Source components, parsed in memory, and discarded after extracting
supported source kind and URL fields. Raw configuration is never written to output.

Supported configuration parsing: WebsiteKnowledgeSource and SharePointKnowledgeSource.
Uploaded attachments are represented by component identity/name without downloading
them. Unrecognized source schemas remain visible with unknown location/type detail.
Topic-embedded, custom and inherited sources are not exhaustively enumerated, so coverage
always remains partial. Authoring configuration is not proof of the published runtime
configuration or actual retrieval.

Install the optional parser in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-knowledge.txt
```

Use the [existing sign-in setup](setup.md). Graph requires Organization.Read.All.
Dataverse requires an existing authorized delegated session for the selected environment
and read access to the bot and botcomponent tables; Azure CLI may not have the required
Dataverse consent in your tenant. The collector reports failures instead of granting
permissions or substituting another identity. Configure a supported authorized client
through your administrator process if necessary.

Find the environment URL in Power Platform admin center → Environments → selected
sandbox/test environment → Environment URL. It is an origin such as
`https://yourorg.crm.dynamics.com`, not the Copilot Studio browser page URL. This version
supports commercial-cloud Dataverse hosts only. The existing config environment label
is not a Power Platform environment ID or evidence of its actual environment type.

```sh
export A365_AZURE_CONFIG_DIR="$HOME/.a365-pilot-azure"
.venv/bin/python scripts/a365-toolkit.py knowledge collect-studio --live \
  --config config/pilot.local.json \
  --tenant-id '<EXPLICIT-TEST-TENANT-ID>' --environment isolated-pilot \
  --dataverse-url 'https://yourorg.crm.dynamics.com' \
  --out artifacts/knowledge-studio-01.json
```

Optionally add `--bot-id '<DATAVERSE-BOT-UUID>'` to limit collection; repeat for several
agents. Otherwise the collector reads accessible agents in that explicit environment.
Owners are Dataverse user/team object IDs, not display names. Source IDs are component
UUIDs; dashboard `packageId` is `dataverse:<botid>` and is not a Graph catalog package ID.
No cross-catalog identity mapping is inferred.

Dataverse identity verification uses WhoAmI and displays the environment origin and
organization ID. The access token is obtained for the explicitly selected tenant and
environment audience. The environment must be selected by the administrator; the
collector does not discover or switch environments silently. Pagination stays bound
to that origin and the metadata projection; redirects are rejected.

## Fields deliberately still unknown

- Tenant-wide discovered site/container inventory.
- Authoritative container IDs for configured SharePoint file/folder URLs. A URL path
  is not silently treated as a site identity, so connected-container counts can be unknown.
- Container sensitivity labels, label ranking and content sensitivity evidence.
- Whether a source is external to your organization. Public website type alone is not
  proof of organizational ownership or boundary; hostnames are not used to guess.
- Source-specific delegated/maker connection context and runtime retrieval evidence.

`lastCheck` is the collector's metadata read timestamp, **not** last successful sync.
Known fields identify their Dataverse record and collection time. Missing values identify
what was not collected. A partial/denied component read never becomes a complete empty
source list. Exit code 2 means an export was written but knowledge coverage remains
unverified/partial; errors before export return 1 and do not create sample fallback data.

## Catalog identity-only export

If only tenant catalog access is available:

```sh
python3 scripts/a365-toolkit.py knowledge collect --live \
  --config config/pilot.local.json \
  --tenant-id '<EXPLICIT-TEST-TENANT-ID>' --environment isolated-pilot \
  --out artifacts/knowledge-catalog-01.json
```

This additionally requires CopilotPackages.Read.All and authorized catalog access. It
exports available agent names/platforms. It cannot infer knowledge connections, owners,
labels or runtime reads; sources remain null. No extra role or permission queries run.

An existing normalized toolkit inventory can also be converted without authentication:

```sh
python3 scripts/a365-toolkit.py knowledge convert-inventory \
  --snapshot artifacts/inventory.json --snapshot-kind tenant-export \
  --out artifacts/knowledge-inventory-01.json
```

Use `--snapshot-kind sample` for fixtures. This provenance declaration is not verified by
the converter. Conversion never inserts the dashboard's fictional sample relationships.

## View and verify

Open [the dashboard](../dashboards/knowledge-exposure/index.html) and choose **Load JSON**.
Select the newly generated file. Its banner changes to TENANT EXPORT. The default preview
continues to show SAMPLE DATA until you explicitly load an export. Files remain local;
no credentials or tenant API calls are added to the browser.

Compare a selected agent's records with its Knowledge page in Copilot Studio. Differences
may indicate unsupported source kinds, draft/published differences, inherited sources or
insufficient access. Resolve those gaps before interpreting the dashboard as complete.
The [format documentation](../dashboards/knowledge-exposure/README.md) defines the evidence
semantics. Mocked tests do not establish live access or tenant coverage.

Primary references: [Dataverse agent table](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/reference/entities/bot),
[agent component table](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/reference/entities/botcomponent),
[Microsoft Agent Inventory data-source mapping](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/kit-agent-inventory-data-source),
[Microsoft's knowledge configuration examples](https://github.com/microsoft/copilot-studio-plugin/blob/main/reference/knowledge-schema.md),
and [Dataverse WhoAmI example](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/quick-start-blazor-server-app).

## Switching Copilot Studio environments

The collector already accepts a different `--dataverse-url` on every run. There is no
hardcoded organization URL. The optional chat target list
[config/knowledge-environments.example.json](../config/knowledge-environments.example.json)
can be copied to `config/knowledge-environments.local.json` (gitignored). Add entries
with `name`, `tenantId` and `dataverseUrl`. This list is read by the Copilot coordinator;
the CLI does not load it automatically. The agent offers saved targets through native
selection, plus an option to enter another URL. It passes the selected URL to the CLI.

For a different tenant, select a matching pilot configuration and explicitly authorized
session as well. The `--environment` argument remains the label in that configuration;
it is not the Power Platform environment ID. Collect one environment per export and
use a new output filename. Load the desired export in the dashboard; automatic merging
or tenant-wide enumeration is not implemented. A saved target is not proof of access
or approval to collect.
