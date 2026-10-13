# Start the toolkit in Codex

Open this repository in Codex (local app, IDE extension or CLI with access to the
workspace). Start a new conversation after adding the repository instructions and say:

> Start a365-toolkit.

This activates the repository workflow through [AGENTS.md](../AGENTS.md). It does not
install a separate selectable model or a Copilot-style custom agent in an agent picker.
There is no new `/a365-toolkit` slash command or `$a365-toolkit` skill in this release.
The entry point is the instruction above. GitHub Copilot retains its existing agent
picker and prompt Run button.

For the assessment rehearsal you can be more specific:

> Start a365-toolkit. Prepare a read-only assessment using config/demo.local.json.
> Show me the selected tenant and scope before connecting. Use a new output filename,
> summarize the assessment in chat and link the HTML report.

## Codex coordinator instructions

Read the shared coordinator and guides named in AGENTS.md. Reuse the same capability
inventory, scripts and evidence contracts; the following rules adapt the host interface.

1. Start offline with action selection: Assess readiness; Install/configure; Verify;
   Review drift; Containment simulation; Knowledge exposure; Supporting capability
   readiness; Build offline artifacts; Resume; Stop. When intent is already explicit,
   preserve that choice rather than asking the administrator to select it again.
   Standard readiness assessment skips Services and proceeds to target/scope confirmation.
   If service selection is already pending, offer **Not applicable — standard readiness
   assessment** to clear it. It must be selected alone and is valid only for assessment,
   not installation or service-specific verification. It never means skip tenant/scope
   confirmation or label a control not applicable. Conflicting selections must be corrected.
2. Use the current host's structured question tools where available and permitted.
   Do not call `vscode/askQuestions` in Codex. Never invent a tool or assume multi-select
   exists. If only single-select is available, offer one capability at a time with
   Add another / Continue / Cancel. If a required input cannot be collected through
   native controls, explain the limitation and ask whether the user wants explicit
   text choices; do not silently change the selection-first interaction contract.
3. Tool-specific restrictions take precedence: a question tool limited to optional
   clarification must not be used for permission or deployment approval. Present the
   exact plan in ordinary chat and obtain an explicit plan-specific reply when necessary.
   Explain that this is the Codex host adaptation, not a verified approval widget.
   Never infer approval from silence, automatic responses, defaults or terminal approval.
4. Read the selected config and show its tenant UUID, exact name and environment.
   Preserve authorization already explicitly granted for the same scope in this session.
   Otherwise establish the exact read-only scope before live reads. The standard assess
   command runs its fixed set of probes; service selections do not narrow these calls.
   Do not misrepresent a Power Platform sandbox as an isolated tenant boundary.
5. For assessment, validate the selected configuration offline. Check that the chosen
   external Azure CLI cache path is known. A variable set in another terminal may not
   exist here: pass `A365_AZURE_CONFIG_DIR` explicitly to the executor when authorized.
   Never print tokens or inspect credential-cache contents. If authentication is absent
   or expired, guide explicit Microsoft sign-in; do not collect credentials in chat.
6. Invoke the existing toolkit executor with explicit --config, --tenant-id and
   --environment. Never rely on its example-config default for live operations.
   Choose a new output stem under artifacts; check JSON, Markdown and HTML siblings
   before running. Do not overwrite reports. A cache path or config value is never
   interpolated unsafely into a shell command.
7. For mutations, first generate and display the exact live plan, including target,
   digest, scope, impact, prerequisites, expiry and recovery. Obtain explicit approval
   for that plan only, then pass its digest to the existing executor. The host's command
   permission is separate. Replan and obtain fresh approval on drift or expiry. Do not
   automate guided-only capabilities or change auto-approval settings.
8. Read the generated report and summarize Check / Result / Evidence / Next step in
   chat. Link HTML, Markdown and JSON. Preserve unknowns, failures and manual tasks.
   Explain exit 2 as unresolved work when applicable, not necessarily execution failure.
   If no report was produced, show the sanitized error and never claim the file exists.
9. Resume and recovery follow the shared workflow: inspect prior receipts and current
   state; do not replay historical approval or retry uncertain writes blindly.

## Compatibility and validation

This adapter is repository instruction, not an independently enforced security boundary.
UI controls vary by Codex host. The existing executor guards enforce target and plan
checks; administrator approval provenance is not cryptographically authenticated.
Codex must have local tools/network permissions to reach the selected Microsoft services.
A cloud session does not automatically share your workstation's Azure CLI cache.

Repository checks validate the instruction links. End-to-end Codex assessment and
mutation flows still need rehearsal; adding AGENTS.md does not certify live execution.

Reference: [Codex repository instructions](https://developers.openai.com/codex/guides/agents-md).
