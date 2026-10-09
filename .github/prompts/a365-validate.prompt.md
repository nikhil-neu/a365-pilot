---
description: Validate configuration and verify observed pilot control state.
agent: a365-toolkit
---

Run `check-config`, offline tests and repository checks. With explicit tenant selection, run `validate --live` and the read-only Purview verifier. Follow docs/validation.md for a benign invocation and independent evidence in all three Microsoft surfaces. No settings changes. Record unknown evidence and actual drift.

Follow the [agent safety contract](../agents/a365-toolkit.agent.md) and
[pilot runbook](../../docs/pilot.md). Report each operation with evidence, impact,
rollback and one of the five supported status values.
