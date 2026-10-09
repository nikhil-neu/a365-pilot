---
description: Apply only an explicitly selected and human-approved pilot plan.
agent: a365-toolkit
---

Require an existing live read-only plan. Show the concrete action, precondition, tenant/environment, digest, roles, permissions, licensing, beta status, blast radius and rollback. Default to `apply` dry-run. Obtain explicit human approval of this exact plan before using --execute and --approve. Never fill approval yourself. Replan after expiry or drift. Save evidence before writing; verify configuration and separately test runtime effect.

Follow the [agent safety contract](../agents/a365-toolkit.agent.md) and
[pilot runbook](../../docs/pilot.md). Report each operation with evidence, impact,
rollback and one of the five supported status values.

For approved Purview or Sentinel setup, follow [administrator deployment](../../docs/admin-deployment.md)
and its separate plan/apply commands. Do not feed those plans into the Graph-only apply command.
