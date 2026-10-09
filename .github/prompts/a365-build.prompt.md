---
description: Build or update repository artifacts without connecting to a tenant.
agent: a365-toolkit
---

Edit only local artifacts within the request. Use `build` without --live for deterministic configuration output. Never authenticate, acquire tokens, grant consent or call tenant APIs. Run offline tests and repository checks. Clearly distinguish generated artifacts from deployed controls.

Follow the [agent safety contract](../agents/a365-toolkit.agent.md) and
[pilot runbook](../../docs/pilot.md). Report each operation with evidence, impact,
rollback and one of the five supported status values.
