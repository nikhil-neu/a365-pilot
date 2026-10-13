# A365 toolkit — Codex entry point

For ordinary repository development, follow the user's task; do not start an
administration workflow merely because this file was loaded.

When the user says **Start a365-toolkit**, asks to use the toolkit, or requests an
assessment/deployment through it, follow [the Codex workflow](docs/codex-workflow.md).
Use existing scripts through `scripts/a365-toolkit.py`. Do not invent tenant mutations.

Shared service behavior and safety rules live in
[the toolkit coordinator](.github/agents/a365-toolkit.agent.md),
[permissions](docs/permissions.md), and [limitations](docs/limitations.md).
Read them before running administration. For Codex, the host-specific interaction
mapping in docs/codex-workflow.md replaces only the coordinator's VS Code launch,
frontmatter tools, and vscode/askQuestions requirements. All tenant verification,
exact-plan approval, freshness, evidence and development/test restrictions still apply.
Never treat saved configuration, an open file or cached authentication as authorization.
