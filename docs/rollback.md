# Rollback and evidence

Each applied plan has an `intent.json` containing exact tenant, environment, prior state,
request, scope, impact and rollback. CA creation also saves a `receipt.json` with the new
policy ID. `outcome.json` records configuration verification or the unknown outcome.
Store these files and the human approval/change ticket in restricted evidence storage.

CA: use a separately reviewed `ca-disable` plan to disable only the named pilot policy.
This is reversible and retains evidence. To restore report-only after promotion, use
the Entra portal after explicit approval and verify scope/state, or disable while the
owner reviews. Do not delete unrelated/duplicate policies or reset an entire tenant.

Registry: restore the recorded prior block state using a new block/unblock plan. Never
unblock an agent that was already blocked before the incident. Retest every relevant
channel and external execution path separately.

Purview/Defender: restore only the recorded policy mode or connector setting through
the corresponding approved admin procedure. Retain auditing; restoring a prior disabled
audit state needs separate review. Stopping data collection does not remove retained data.

If configuration changes during approval, the CLI refuses the old plan. If the request
times out or readback is delayed, status is not verifiable and the saved intent survives.
Use read-only inspection to determine whether the change happened before replanning.
No write retry, automatic destructive rollback or assumption of transactionality is made.
