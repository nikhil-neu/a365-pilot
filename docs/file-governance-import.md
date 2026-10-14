# File governance JSON review

Open [the file governance dashboard](../dashboards/knowledge-exposure/wireframe.html)
in a local browser. The historical filename is retained for existing links; this page
now supports validated JSON import. No application registration, server, authentication
or tenant API connection is required. Browser network connections are prohibited.

1. Download JSON example for the complete structure, or use
   [file-governance.sample.json](../dashboards/knowledge-exposure/file-governance.sample.json).
2. Prepare an authorized metadata export in that format. Do not simply relabel the
   sample as tenant data. Replace every fictional record and evidence reference.
3. Select **Load governance JSON**. Files are limited to 5 MB / 10,000 file records.
   An invalid import leaves the previous dataset visible and displays an error.
4. Search by file, site or agent. Select a file to inspect all observations and provenance.
   Needs evidence includes files that also have findings in another category.
5. Export review downloads a plain-text report of the entire dataset (not just filtered
   rows), including evidence, findings and next steps. Prepare review summary is advisory;
   neither action changes tenant state. Reset to sample restores the fictional preview.

## Contract: file governance version 1

This is a separate file-level format from the existing agent knowledge inventory JSON.
Existing Studio exports cannot be imported directly: they lack file resolution and
protection evidence. The existing [inventory dashboard](../dashboards/knowledge-exposure/index.html)
continues to accept those exports unchanged.

Root fields, all required:

| Field | Meaning |
| --- | --- |
| schemaVersion | `1` |
| dataKind | `sample` or `tenant-export`; exporter declaration, not verified provenance |
| name, tenantId, environment | Nonempty dataset and target identifiers |
| capturedAt | ISO timestamp with timezone |
| complete | Exporter's declaration about the specified inventory scope, not all tenant files |
| files | Array; empty is valid and never replaced with samples |

Each file requires `id` (unique canonical identity), `name`, `site` (display location),
`location` (HTTP(S) URL without credentials/query/fragment, or null), `evidence`,
`agents`, and `observations`. Prefer site/drive/item identifiers for file IDs; do not
merge files solely by matching names. Each agent requires `id`, `name`, `relationship`
(`configured-source` or `configured-file`), and `evidence`. An empty agents array means
no supplied relationships, not proof no agents use the file. Source relationships do
not establish agent-specific effective access or runtime retrieval.

Every `evidence` object requires `source` (metadata evidence reference) and `checkedAt`
(ISO timestamp with timezone). File evidence supports identity/location; each agent
relationship has separate provenance. Unknown observations use the timestamp of the
failed check or the exporter's record of missing evidence, never an invented successful read.

Every observation has exactly `value`, `state`, `evidence`. States are `known`, `unknown`,
`notApplicable`; unknown and notApplicable require null values. All these observations
are required:

| Key | Known value |
| --- | --- |
| container | Container label name/identifier; separate from file label |
| label | `Labeled` or `Unlabeled`; only successful inspection can confirm Unlabeled |
| labelName | File label name/identifier; required known for Labeled, notApplicable for Unlabeled |
| sharing | `Anonymous link`, `External guest`, or `Internal readers` |
| dlp | `Simulation only`, `Scope excluded`, or `Policy in scope` |
| runtime | `Observed retrieval` or `Not observed`; the latter means no observation in supplied evidence |
| access, inheritance, policy, rule, exclusion, owner | Descriptive metadata string |

The sharing and DLP values summarize the supplied assessment. Record multiple policy
or grant details in their descriptive fields, including exact IDs and scope. This v1
format does not model exhaustive grants or evaluate effective access itself. If a
mixed policy assessment cannot be summarized accurately, mark DLP unknown and explain
in the policy/rule fields. Do not label a file unprotected because one policy excludes it.

Findings flag confirmed unlabeled files, sharing needing owner review, simulation and
explicit scope exclusions. These are review candidates, not automatic compliance
violations. A labeled file is not necessarily correctly classified. A site label does
not establish file classification. Policy inclusion does not prove rule matching or
runtime enforcement. Unknown observations are counted separately and never treated
as confirmed gaps. Sources and timestamps remain visible so stale evidence can be reviewed.

Only metadata is allowed: no document bodies, prompts, responses, passwords, tokens or
raw provider payloads. Unknown fields are rejected. Free-text fields are not a secret
scanner; the export producer must redact sensitive content. Values render as text;
locations are not fetched. Data stays in page memory until replaced or the page closes;
exported reports are local files the administrator must handle appropriately.

## What is not implemented

No live SharePoint file enumeration, permission/label collector, Purview policy evaluation
or runtime collector was added. Real evidence must be prepared using separately authorized
exports. The tool does not independently verify the imported evidence or obtain access
that the administrator does not have. It does not apply labels, remove grants or change DLP.

## Checks

```sh
node tests/file-governance.test.js
node tests/knowledge-exposure.test.js
python3 scripts/check_repository.py
```
