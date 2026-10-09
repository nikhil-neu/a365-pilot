# Start in Copilot Chat

Open this repository in VS Code with GitHub Copilot available. In the Chat agent picker,
select **a365-toolkit** and say:

> Help me set up the security services for Agent 365.

The custom agent lives in [.github/agents/a365-toolkit.agent.md](../.github/agents/a365-toolkit.agent.md).
In a compatible Local chat session, `/a365-toolkit` is an optional shortcut. The custom
agent is the primary entry point; administrators do not need to learn separate slash
commands for each service. Older prompts remain compatibility shortcuts to this agent.

If the agent is absent, use VS Code's chat customization diagnostics to check workspace
custom-agent discovery. Prompt-file availability varies by session type; use the custom
agent picker rather than assuming the slash shortcut works everywhere.

## What the admin sees

The conversation starts with a choice:

> What would you like to do: assess the current setup, install/configure services,
> verify a deployment, review drift, or investigate/contain one agent package?
>
> For setup, choose any combination: Entra agent Conditional Access; Defender
> integrations; Purview audit; Purview DLP; Sentinel essentials; all applicable services.

The admin can answer naturally, for example:

> Start with Purview auditing and the Sentinel pack. Leave Conditional Access for later.

The agent gathers only relevant missing inputs, establishes the selected tenant and
read-only discovery scope, checks prerequisites and explains blocked components. It
coordinates dependencies but does not silently select extra services. Licensing and
portal-only setup remain visible steps. Existing deployment code is development/test-only;
production support remains planned.

## Approval happens in the conversation

The agent prepares a live read-only plan and displays one card at a time:

```text
Plan P1 — Enable unified audit
Tenant: <verified name and UUID> | Environment: <selected environment>
Selection: Purview audit
Current state: <observed state>
Change: Enable unified audit ingestion
Scope: Entire selected tenant
Prerequisites: <observed access, licensing and remaining unknowns>
Impact / cost: <specific consequences; no invented price estimate>
Recovery: Preserve audit; do not automatically disable it to roll back
Plan: <path to saved live plan>
Digest: <full approval digest from that plan>
Freshness: <creation time and remaining validity; maximum 30 minutes>
Verification: Configuration readback, followed by expected audit events

Approve P1, change the scope, or skip this component?
```

This is an illustrative card, not a pending deployment approval. The real card must
include actual state, exact parameters/targets, roles, permissions, interface maturity,
licensing gaps and recovery from the generated plan. The agent waits for an explicit
reply. After `Approve P1`, it passes that plan's digest to the executor; the admin need
not manually paste CLI arguments. Approval of one component does not authorize another.
An expired or changed plan gets a new card and fresh approval. Skipping or declining
issues no mutation. Enforcement and activation require separate plans and approval.

The coordinator records the reply and plan reference locally. That record and the digest
are not authenticated signatures. Retain the approval/change ticket in your controlled
change system where required. Copilot's terminal/tool permission dialog may also appear;
it is separate from approval of the deployment plan. Do not disable host permissions.

## Execution and recovery

The chat agent runs the existing deterministic executors through the toolkit entry point.
Purview requires an existing verified PowerShell session. If the host cannot use that
persistent session, the agent supplies the reviewed command for the admin to execute
there and marks the step as awaiting evidence; it must not pretend it ran successfully.

Plans and receipts remain under gitignored `artifacts/`. The session journal records
selection, pending work and evidence references only. A resumed conversation rechecks
state and requests fresh approval for new writes; it never replays stored approval.
Unknown or partial outcomes pause the affected sequence. The agent can offer to continue
independent selected components while the administrator resolves the blocked one.

The final summary distinguishes configured resources from verified ingestion and runtime
behavior. The [capability matrix](capability-matrix.md) defines available executors and
remaining gaps. This is a repository-defined conversational workflow, not a bespoke
Copilot extension with a trusted multi-select widget or server-enforced approval identity.

## Validation boundary

Offline checks validate the customization files, command routing and executor safeguards.
The conversation has not been end-to-end tested in a live Copilot session or against a
tenant. Check agent discovery, selection, decline/skip, approval expiry, state drift and
partial-failure behavior in the sandbox before wider use.

References: [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents),
[host permissions and approvals](https://code.visualstudio.com/docs/agents/run/approvals).
