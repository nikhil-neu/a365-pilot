# Named-agent containment and recovery

Start with one exact registry package ID. Display names are not unique. Assess tenant
identity before enrichment. Record owner, platform, package/version, individual identity,
blueprint, granted/inherited permissions, tools, risk source/time and suspected activity.
Treat missing information as unknown and confirm desired-inventory metadata independently.

| Response | What it does | Boundary / recovery |
| --- | --- | --- |
| Conditional Access denial | Denies matching resource token requests | Does not make a package unavailable or stop compute; delegated/agent-user/blueprint flows differ. Disable or restore report-only after approval. |
| Registry package block | Changes this package's availability to assigned users/channels | May affect several deployments/users; external runtime/authentication can continue. Unblock only if originally unblocked. |
| Identity disablement | Stops supported future authentication for the selected identity | Existing tokens and alternate credentials may persist. Verify exact identity type; restore previous accountEnabled state. |
| Permission revocation | Removes one identified grant | Confirm direct vs inherited vs tenant-wide grant. Regrant exact previous permission only after consent approval. Never broadly revoke blueprint permissions. |
| Infrastructure stop | Stops the specified runtime resource where that provider supports stop | Shared hosting can affect many agents. Managed/serverless Foundry agents have no universal stop operation. Use resource-specific approved stop/restart instructions. |

Choose the narrowest reversible response that addresses the incident, not simply the
first available command. For a compromised resource token flow, an identity-specific
response may be more appropriate than package blocking; those responses require the
documented manual platform procedure. The kit automates only package availability blocking
and the pilot CA baseline lifecycle. It never substitutes a broader action automatically.

## Simulation

```sh
python3 scripts/a365.py contain --live --config config/pilot.local.json \
  --tenant-id '<TEST-TENANT-ID>' --environment isolated-pilot \
  --agent-id '<EXACT-PACKAGE-ID>' --plan-out artifacts/containment-plan.json \
  --out artifacts/containment-simulation.json
```

This issues only reads. Show observed owner/identity/risk evidence, unknown permissions
and tools, all assigned users/channels, candidate responses, selected action and blast
radius. A package can be shared by multiple deployments: confirm the intended boundary
with the owner. No permanent deletion or blueprint-wide permissions action is allowed.

For execution, route the saved plan through [the apply procedure](../docs/pilot.md) with
human approval for that exact digest. A separate approval is required for a different
response, enforcement, consent or infrastructure stop. The CLI writes intent before the
mutation and records readback. Retry neither a write timeout nor an unverified block blindly.

## Verify and recover

Record observed `isBlocked`, portal state, UTC time, actor/change ticket and per-channel
access test. A configuration flag alone does not prove running jobs or tokens have stopped.
Preserve risk/telemetry evidence before response; do not erase logs or dismiss risk merely
to pass verification.

After resolving the incident and obtaining recovery approval, create a fresh
`plan --live --intent registry-unblock --agent-id '<EXACT-PACKAGE-ID>'` with explicit
tenant arguments, review and apply. If the agent was already blocked before this incident,
do not unblock it. Verify package readback and a benign permitted invocation. Restore
exact prior policy/grant/runtime state only when it remains appropriate. Record unresolved
effects as not verifiable and escalate to the owner; never delete the agent as cleanup.
