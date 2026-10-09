# a365-toolkit

An administrator toolkit for deploying, configuring and verifying the Entra, Defender,
Purview and Sentinel services that support Agent 365. Production administration is the
target; development and sandbox tenants qualify the workflows before wider rollout.

**Current release:** live executors remain development/test-only and have been tested
offline with mocks, not qualified through live deployment. The shared entry point routes
to existing service executors; cross-service orchestration and production support are planned.

## Start in Copilot Chat

Select **a365-toolkit** in the VS Code Copilot Chat agent picker and say:

> Help me set up the security services for Agent 365.

Choose the services in chat. The agent guides prerequisites, shows concrete deployment
plans, asks for approval in the conversation, runs supported executors and reports
verification gaps. See [the chat workflow](docs/chat-deployment.md). The CLI is the
execution layer and remains available for troubleshooting and scripted use.

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
