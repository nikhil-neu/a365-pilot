---
description: Show deployment choices and a reviewable dry-run for the selected pilot.
agent: a365-toolkit
---

Read the selected capability profile. Explain CA report-only, Purview simulation, Defender setup and registry auditing choices. Use offline `plan` or, for an explicitly selected tenant, `plan --live` to capture real preconditions for one selected operation. Show exact scope, maturity, privilege requirements, digest, impact and rollback. No tenant writes. Do not call apply.

Follow the [agent safety contract](../agents/a365-toolkit.agent.md) and
[pilot runbook](../../docs/pilot.md). Report each operation with evidence, impact,
rollback and one of the five supported status values.
