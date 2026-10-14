# a365-toolkit

An administrator toolkit for deploying, configuring and verifying the Entra, Defender,
Purview and Sentinel services that support Agent 365. Production administration is the
target; development and sandbox tenants qualify the workflows before wider rollout.

**Current release:** live executors remain development/test-only and have been tested
offline with mocks, not qualified through live deployment. The shared entry point routes
to existing service executors; cross-service orchestration and production support are planned.

## Start in Copilot Chat

In a VS Code **Local** Copilot Chat session, open
[the toolkit prompt](.github/prompts/a365-toolkit.prompt.md) and click its **Run** button.
It selects **a365-toolkit** and starts the guided workflow without composing a prompt.
Selecting the agent in the picker alone does not start a turn.

Choose an action using Copilot's native selection controls, select multiple services,
and enter missing values through its input fields. Review each concrete plan and use
its approval selector before execution. If native controls are unavailable, the agent
is instructed to stop. These are agent instructions, not an independently enforced UI
or approval system. See [the chat workflow](docs/chat-deployment.md).
The CLI remains the execution layer for troubleshooting and scripted use.

Start with the [capability matrix](docs/capability-matrix.md) and
[deployment workflow](docs/deployment-workflow.md). Client documents:
[executive brief](docs/assets/a365-toolkit-executive-brief.pdf) and
[one-page overview](docs/assets/a365-toolkit-one-pager.pdf).

```sh
python3 scripts/a365-toolkit.py capabilities
python3 scripts/a365-toolkit.py workflow
```

Python 3.9+ and its standard library provide a small, cross-platform CLI, Graph HTTP
transport, strict JSON validation, evidence reports and offline tests. Azure CLI supplies
short-lived tokens from a dedicated external cache. PowerShell 7.2+ and Microsoft's
modules support the Purview verifier and separately approved administrator deployments. No application
framework, database, hosted service or AI API is required.

## Start offline

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_repository.py
python3 scripts/a365.py check-config
python3 scripts/a365.py build --plan-out artifacts/offline-plan.json --out artifacts/offline-build.json
```

Outputs must have new names; evidence files are never overwritten. JSON, Markdown and
an escaped, offline HTML dashboard are produced by `scripts/a365.py --out`.
The separate administrator deployment CLI produces JSON manifests and evidence. `build` compiles selected
configuration into local review artifacts. It does not enable a control.

## Agent Knowledge Exposure dashboard

Open [the local dashboard](dashboards/knowledge-exposure/index.html) directly in a browser.
It starts with clearly labeled fictional sample data. Use **Load JSON** to inspect your
own metadata export; no hosting or browser tenant API calls are involved. Configured
sources, container labels, content labels and runtime retrieval evidence are kept separate.

See [the JSON format and data limitations](dashboards/knowledge-exposure/README.md).
Use the [read-only collection guide](docs/knowledge-collection.md) for real Copilot Studio
knowledge metadata or catalog identity-only exports. Labels, resolved containers and
runtime retrieval remain unknown where not collected. This dashboard does not
change the VS Code Copilot workflow or modify tenant settings.

## Layout

| Directory | Purpose |
| --- | --- |
| `.github/agents`, `.github/prompts` | Reusable coordinator and one primary chat workflow and legacy shortcuts |
| `config` | Versioned neutral pilot settings, profiles and approved inventory template |
| `scripts` | Assessment, Graph safety gates, approved Sentinel/Purview deployment, auditor |
| `queries` | Current Defender `AgentsInfo` and metadata-only activity queries |
| `dashboards` | Local evidence dashboard guidance |
| `sentinel` | Deployable SOC content and separate Log Analytics queries |
| `playbooks` | Containment decision, approval, evidence and recovery |
| `docs` | Setup, permissions, control matrix, stages, verification and limitations |
| `tests` | Mocked responses and offline safety/behavior tests |

## Read-only pilot

Follow [setup](docs/setup.md), copy `config/pilot.example.json` to
`config/pilot.local.json`, and replace placeholders with the explicitly selected test
tenant and exact organization name. Individual agent identity and resource IDs can
remain placeholders for assessment; they are required before live CA planning.
Use a dedicated Azure CLI cache outside this repo and explicitly authenticate as
described there. Then run:

```sh
python3 scripts/a365.py assess --live \
  --config config/pilot.local.json \
  --tenant-id '<TEST-TENANT-ID>' --environment isolated-pilot \
  --out artifacts/read-only-assessment.json
```

Authentication is not automatic. Read-only assessment never grants consent. Insufficient
access is reported as not verifiable; it does not trigger privilege escalation.

## Administrator deployment

For **toolkit execution after your approval**, follow the [administrator guide](docs/admin-deployment.md).
Use `scripts/a365-admin.py` for staged Sentinel deployment and `scripts/Set-PurviewPilot.ps1`
for DLP simulation policy creation or separately approved audit enablement. The additional
settings live in `config/admin.local.json`; the existing assessment configuration is preserved.
No live installation has been performed.

## Workflows and contracts

`assess` gathers readiness evidence; `plan` previews one change; `build` emits local
artifacts; `validate` checks configuration and observed controls; `apply` defaults to
a dry-run of a saved plan; `contain` simulates one package block. `audit` compares a
normalized snapshot with approved inventory. `verify-invocation` queries one exact run.
Use `python3 scripts/a365.py --help` for arguments.

Exit codes: **0** completed with applied/skipped results, **1** failed configuration,
drift or safety check, **2** unknown or manual work remains. A successful read has
status `skipped` because no tenant change occurred; its `observed` field and evidence
describe what was verified. `applied` requires a write and configuration readback,
but runtime effects still require a separate test. Never use the exit code alone as
a compliance assertion.

See [pilot stages](docs/pilot.md), [control matrix](docs/control-matrix.md),
[validation](docs/validation.md), [drift review](docs/drift-review.md),
[containment](playbooks/containment.md), and [limitations](docs/limitations.md).
Interfaces were checked against [Microsoft sources](docs/sources.md) on 2026-10-09.

## Supporting capability readiness

Choose **Supporting capability readiness** in the toolkit agent for Frontier, agent
risk, Defender onboarding, local discovery, endpoint runtime protection, Purview
collection, agent identities and partner signals. The new risk collector is read-only;
the other new capabilities provide guided setup and verification, not new deployment
executors. See [delivery status and instructions](docs/supporting-capabilities.md).

The knowledge dashboard now includes a **Data governance review** section: search data
locations, expand connected agents, inspect label/runtime evidence and review suggested
next steps. It uses the loaded snapshot; effective permissions, sharing and DLP coverage
remain unavailable pending additional collectors. Open
[dashboards/knowledge-exposure/index.html](dashboards/knowledge-exposure/index.html).

## Start in Codex

Open this repository in a local Codex session and say **Start a365-toolkit**.
[AGENTS.md](AGENTS.md) routes that request to the same toolkit scripts and safeguards.
This is a repository workflow, not an additional agent-picker item. Native selection
controls depend on the Codex host; see [the Codex entry point](docs/codex-workflow.md)
for assessment setup, explicit approvals and report delivery.

Conditional Access scope options: [blueprint and All resources planning](docs/conditional-access-scopes.md).

## File governance review

Open [the local file governance dashboard](dashboards/knowledge-exposure/wireframe.html),
load a metadata JSON export, review labels/sharing/DLP evidence and export a text report.
No app registration is required. The initial dataset is fictional; real tenant evidence
must be supplied separately. See [the import format and limitations](docs/file-governance-import.md).
