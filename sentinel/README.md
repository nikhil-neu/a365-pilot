# A365 Sentinel pilot content pack

Use [administrator deployment](../docs/admin-deployment.md) to build, plan, approve,
deploy and verify the pack. Request payloads are generated deterministically by
`scripts/a365/admin.py`; `scripts/a365-admin.py build` exports all of them offline.

The pack has three hunting queries, one watchlist, two initially disabled analytics
rules, one workbook and one initially disabled incident-task automation rule. Foundation
and connector deployment are separate approved stages. The response playbook is
[human triage](../playbooks/sentinel-triage.md), not an automatically executing Logic App.

Queries here target Log Analytics `SecurityAlert` and `OfficeActivity`. The top-level
`queries/` folder targets Defender Advanced Hunting and must not be imported directly
as Sentinel rules. Identity lists scope correlation; connector ingestion is tenant-wide.

The agent-alert query recognizes only `Entities[].AadUserId` matches. It is a limited
triage query, not complete agent identity coverage. The DLP query describes pilot-user
activity, not proof of an agent invocation. Keep rules disabled until queries compile,
test events are observed, attribution is reviewed and thresholds are tuned.

After validation, `--stage activate` plans enabling the installed rules and task automation.
`--stage deactivate` plans disabling them. Both require new explicit approvals.
