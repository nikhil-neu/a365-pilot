# a365-toolkit deployment workflow

The product is an administrator toolkit for preparing the security services that support
Agent 365. Production administration is the target; development and sandbox tenants are
where the same workflows must first be qualified. Pilot rollout is a scope option, not
the product's identity. Current executors still restrict live operations to development/test.

## Current entry point

The administrator-facing entry point is the **a365-toolkit** custom agent in Copilot
Chat. See [selection and approval in chat](chat-deployment.md). The commands below
are its underlying execution interface, not steps every administrator must memorize.

```sh
python3 scripts/a365-toolkit.py capabilities
python3 scripts/a365-toolkit.py workflow
python3 scripts/a365-toolkit.py tenant assess --help
python3 scripts/a365-toolkit.py sentinel build --help
python3 scripts/a365-toolkit.py purview
```

`tenant` and `sentinel` forward arguments to the existing executors and preserve their
approval gates and exit codes. Purview must run inside the existing verified PowerShell
session; the entry point explains that requirement. This is a shared entry point, not yet
a cross-service orchestrator. See [actual deployment commands](admin-deployment.md).

## Unified lifecycle

| Phase | Administrator outcome | Current implementation |
| --- | --- | --- |
| Select | Explicit tenant, environment, subscription and workload scope | Existing configuration; no inferred tenant |
| Discover | Existing controls, licenses, roles and prerequisites | Partial Graph assessment plus service preflights; effective permissions need review |
| Plan | Dependency-ordered changes with exact scope, costs and recovery | Separate service plans; consolidated plan is planned |
| Approve | Recorded approval for concrete changes | Exact digest per plan; approval identity recorded externally |
| Deploy | Supported changes executed in dependency order | Entra/registry, Purview and Sentinel executors; admin coordinates services |
| Verify | Configuration, ingestion and runtime behavior independently evidenced | Partial readback; portal checks and benign tests remain necessary |
| Activate | Approved enforcement or detection activation | CA and Sentinel supported; DLP enforcement is a gap |
| Maintain | Detect drift, propose repairs, update and recover | Inventory comparison exists; general repair/reconciliation is planned |

For Sentinel, provision/reuse the foundation, configure connectors, wait for required
tables, then install content. Validate queries and events before activating detections.
Audit enablement may be needed before Microsoft 365 audit events are available. DLP
simulation is followed by distribution/scope checks and a benign test. Defender Security
for AI onboarding and Agent 365 data lake onboarding are distinct from Sentinel XDR ingestion.

## Production qualification

Production support must include explicit production identity checks, scoped pilot cohorts,
protection for existing settings, deployment receipts and tested recovery. Qualification
requires live sandbox deployment, rerun and partial-failure tests, evidence of real
telemetry and control behavior, and review of each API/feature's availability and licensing.
Removing the current environment check alone would not establish production support.

Future readiness reporting should distinguish verified, awaiting approval, prerequisite
blocked, unavailable, not applicable and unverified capabilities. Existing operation
statuses remain unchanged until that reporting model is implemented. A generated artifact,
a successful write and verified runtime protection are separate outcomes.

## Naming and migration

The product name is **a365-toolkit**. Existing `pilot.local.json`, script entry points,
`A365-PILOT-` resource identifiers and the workspace directory remain compatible. A brand
change must not create duplicate policies, rename remote resources or invalidate existing
approvals silently. Future configuration migration needs a versioned migration tool.

The [capability matrix](capability-matrix.md) is the implementation baseline. Broader
production support, orchestration and executable runbooks are planned capabilities,
not features implied by the new product name.
