---
description: Simulate a narrow reversible response for one named agent.
agent: a365-toolkit
---

Require one exact package ID; resolve display-name ambiguity using read-only inventory. Enrich owners, platform, identity/blueprint, permissions, tools and risk, marking unknowns. Follow playbooks/containment.md and compare the narrowest supported response. Use `contain` to simulate; --live only reads. Do not execute from this workflow. If the user requests execution, hand over a saved plan for a365-apply and exact human approval. Preserve recovery evidence; never permanently delete or broadly revoke blueprint permissions.

Follow the [agent safety contract](../agents/a365-toolkit.agent.md) and
[pilot runbook](../../docs/pilot.md). Report each operation with evidence, impact,
rollback and one of the five supported status values.
