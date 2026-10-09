---
description: Read-only repository and selected test tenant readiness assessment.
agent: a365-toolkit
---

Run offline configuration/repository checks first. If tenant reads are explicitly requested, use `assess --live` with the supplied tenant ID and environment. Display identity, roles, licensing and read-only impact. Do not enable controls or grant consent. Include failed and unknown checks and the manual connector/Purview checklist.

Follow the [agent safety contract](../agents/a365-toolkit.agent.md) and
[pilot runbook](../../docs/pilot.md). Report each operation with evidence, impact,
rollback and one of the five supported status values.
