# Pilot stages and deployment

Use fresh output paths for every run. No stage advances automatically.

| Stage | Action | Exit evidence |
| --- | --- | --- |
| 0 Offline | Unit tests, repository checks, `build` | Valid config, deterministic artifacts, zero network calls |
| 1 Read-only | `assess --live`, Purview verifier, connector checklist | Exact tenant ID/name, observed roles/SKUs/config, explicit unknowns |
| 2 Dry-run | `plan --live --intent ca-deploy` | Selected scope, required privileges, report-only payload, rollback, digest |
| 3 Test deployment | Human approval then `apply --execute` | Durable intent, one mutation, configuration readback |
| 4 Verification | `validate --live`, invocation verification | Actual configuration plus Microsoft 365, Defender, Purview evidence |
| 5 Containment simulation | `contain --live --agent-id` | Named package, enrichment, availability blast radius, no write |

## Plan and apply one CA baseline

Repeat explicit tenant arguments on every command. `--live` here permits reads only.

```sh
python3 scripts/a365.py plan --live --config config/pilot.local.json \
  --tenant-id '<TEST-TENANT-ID>' --environment isolated-pilot \
  --intent ca-deploy --plan-out artifacts/ca-plan.json
```

Review the full plan and submit its digest to the human approver with the change ticket.
No broad `All` resource or tenant-wide agent selector is generated. The typed agent
identity lookup rejects blueprint IDs. Failed identity reads prevent the plan.

First test the saved plan without writing:

```sh
python3 scripts/a365.py apply --live --config config/pilot.local.json \
  --tenant-id '<TEST-TENANT-ID>' --environment isolated-pilot \
  --plan-file artifacts/ca-plan.json
```

Only after explicit approval of the concrete plan:

```sh
python3 scripts/a365.py apply --live --config config/pilot.local.json \
  --tenant-id '<TEST-TENANT-ID>' --environment isolated-pilot \
  --plan-file artifacts/ca-plan.json --execute \
  --approve '<APPROVED-SHA256-DIGEST>' --evidence-dir artifacts/ca-change-001 \
  --out artifacts/ca-change-001-report.json
```

Plans expire after 30 minutes. Apply reconstructs the plan from current state and rejects
changes, tampering, configuration drift, mismatched environment and wrong digest. Request
authorization is single-use. There is no retry of writes and no bulk mutation loop.
Keep change sessions isolated from other administrators: the APIs do not provide an
atomic lock across preflight and mutation, so a residual race remains.

If an outcome is unknown, inspect the saved intent/receipt and current state before any
retry. A POST timeout may have created the policy. Duplicate policy names stop execution.

## Promotion and recovery

After report-only sign-in results cover benign and risky pilot cases, confirm owners,
licenses, mappings, recovery credentials and no unintended scope. Create a new plan with
`--intent ca-promote`, get explicit approval for enforcement, then apply it using the
same procedure. The generated plan retains the exact agents/resources and high-risk
condition. Agent users, delegated users and blueprint provisioning tokens are outside
this policy. Promotion is optional, not a required stage or default behavior.

To stop enforcement, plan `ca-disable`, approve and apply. It disables only this policy.
If read-only verification finds external scope changes, fix or restore through the
approved Entra portal recovery procedure rather than overwriting unreviewed settings.
See [rollback](rollback.md). Defender/Purview setup remains separately approved admin
work; the CLI does not imply those products were deployed along with CA.
