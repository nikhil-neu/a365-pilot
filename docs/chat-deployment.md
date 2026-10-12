# Start in Copilot Chat

Open this repository in VS Code with GitHub Copilot available, using a Local chat
session. Open [the toolkit prompt](../.github/prompts/a365-toolkit.prompt.md) and click
**Run** in the editor. No opening prompt needs to be composed. This launches the
[a365-toolkit agent](../.github/agents/a365-toolkit.agent.md). Selecting its name in the
agent picker alone does not start a turn. `/a365-toolkit` remains an optional shortcut.

If the agent is absent, use VS Code's chat customization diagnostics. Native input
requires `vscode/askQuestions` enabled in the session. When that tool or its required
controls are unavailable, the workflow must stop with a compatibility explanation.
It must not fall back to asking for typed chat answers.

## What the admin sees

1. An **Action** single-select: assess, install/configure, verify, drift review,
   containment simulation, knowledge exposure, offline build, resume or stop.
2. A **Services** multi-select when relevant: Entra Conditional Access, Defender,
   Purview audit, Purview DLP and Sentinel essentials. Check all five for all services.
3. A **Target** selector displaying the configured tenant name, UUID and environment.
   Missing identifiers, URLs and paths use native text-entry controls and validation.
4. A **Discovery** selector confirming the displayed read-only scope or offline work.
5. A separate **Plan decision** selector for each concrete deployment plan.

Explanations and evidence stay in chat. Decisions, scope changes, missing inputs and
recovery choices use native controls. Secrets are never entered in these fields;
authentication uses Microsoft's sign-in UI. Choosing services does not approve writes.
Legacy prompts and natural-language requests confirm action/scope through the controls.

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

Native selector follows: Skip / Change scope / Approve P1 — <full digest> / Stop
```

This is an illustrative card, not a pending deployment approval. The real card must
include actual state, exact parameters/targets, roles, permissions, interface maturity,
licensing gaps and recovery from the generated plan. The agent waits for an explicit
submitted selection. Only the exact approval option for that plan authorizes passing
its digest to the executor; the admin need
not manually paste CLI arguments. Approval of one component does not authorize another.
An expired or changed plan gets a new card and fresh approval. Skipping or declining
issues no mutation. Enforcement and activation require separate plans and approval.

Skipped, empty, cancelled, unrecognized or automated responses never authorize a write.
Free-text yes or Approve P1 is not accepted; the agent presents the native selector.
Approval is not preselected or recommended.

The coordinator records the submitted selection and plan reference locally. That record and the digest
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
Copilot extension or server-enforced approval identity. VS Code provides the native
widgets. Instructions standardize the choices, but do not guarantee model compliance;
existing executor validation remains the code-enforced boundary.

## Validation boundary

Offline checks validate the customization files, command routing and executor safeguards.
The conversation has not been end-to-end tested in a live Copilot session or against a
tenant. Check agent discovery, selection, decline/skip, approval expiry, state drift and
partial-failure behavior in the sandbox before wider use. Also verify:

- Run launches Action without requiring an opening prompt.
- Multiple services remain selected and only their required fields are requested.
- Invalid identifiers reopen native input without issuing dependent live calls.
- Skip, Cancel, empty answers and unavailable controls produce no mutations.
- An exact approval applies only to its current digest; changed plans ask again.
- Resume and recovery never reuse an old approval.

These are host acceptance checks, not claims of completed interactive testing.

References: [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents),
[host permissions and approvals](https://code.visualstudio.com/docs/agents/run/approvals),
[native tool reference](https://code.visualstudio.com/docs/agents/reference/tools-reference),
[prompt Run button](https://code.visualstudio.com/docs/agent-customization/prompt-files).

## Knowledge exposure review

For real dashboard data, follow [read-only knowledge collection](knowledge-collection.md).
Confirm tenant, platform and the explicit Dataverse environment before collecting. Use
`a365-toolkit.py knowledge collect-studio` for Copilot Studio; catalog collection provides
identity metadata only. Explain remaining unknown labels and runtime evidence.

## Supporting capability readiness

Choose **Supporting capability readiness** in the toolkit agent for Frontier, agent
risk, Defender onboarding, local discovery, endpoint runtime protection, Purview
collection, agent identities and partner signals. The new risk collector is read-only;
the other new capabilities provide guided setup and verification, not new deployment
executors. See [delivery status and instructions](supporting-capabilities.md).
