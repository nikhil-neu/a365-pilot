# Administrator deployment: review, approve, execute

The toolkit can now execute a reviewed deployment using your existing administrator
sessions. Nothing deploys simply because you run an assessment or build. The deployment
plan names the tenant, subscription, resources, exact changes, impact and recovery steps.
You approve that plan's digest before execution. Plans expire after 30 minutes and must
still match the configuration and observed state.

This is for development/test tenants. Existing product licensing, permissions and
service availability still apply. A Microsoft 365 developer tenant does not provide an
Azure subscription or unlock unavailable Agent 365 features.

## What you can deploy

| Component | Toolkit action after approval | Remaining verification |
| --- | --- | --- |
| Purview DLP | Create a new named policy and rule for explicit pilot mailboxes/sites, in `TestWithoutNotifications` | Check scope, predicate, distribution and a benign sensitive-data test in Purview |
| Unified audit | Enable audit ingestion, as a separate tenant-wide change | Confirm events arrive |
| Sentinel foundation | Create a Log Analytics workspace and enable Sentinel in an existing resource group; reuse existing foundation without changing it | Provisioning and billing |
| Defender XDR → Sentinel | Create the documented `MicrosoftThreatProtection` connector for incidents/alerts | Product eligibility, connector health and arriving alerts |
| Microsoft 365 → Sentinel | Create the `Office365` connector for Exchange, SharePoint and Teams audit | Unified audit, connector health and arriving events |
| Sentinel content pack | Three hunting queries, approved-agent watchlist, two disabled scheduled analytics rules, a workbook, and disabled incident-task automation | Compile/run queries, verify watchlist upload, tune detections and separately approve enabling them |
| Defender Security for AI onboarding | Portal step described in [connectors](connectors.md) | Its Microsoft 365 connector is different from XDR → Sentinel |

The pack includes a [human response playbook](../playbooks/sentinel-triage.md). It does
not create a Logic App, automatically contain agents, or install every Content Hub
solution. Agent 365 **data lake** onboarding is also separate; this pack uses the
Log Analytics `SecurityAlert` and `OfficeActivity` tables, not `AgentsInfo`.

## 1. Fill the deployment configuration

Keep your current `config/pilot.local.json`. Create the additional local file once:

```sh
cp config/admin.example.json config/admin.local.json
```

Edit `config/admin.local.json`:

- `subscriptionId`: the Azure subscription attached to the selected test directory.
- `resourceGroup`: an existing resource group where you can deploy the pilot.
- `workspaceName` and `location`: the intended Log Analytics workspace and Azure region.
- `retentionInDays` and `dailyQuotaGb`: review costs. A daily ingestion cap is **not** a spending limit and can interrupt visibility.
- `connectors`: select which connectors to create. Ingestion is tenant-wide; pilot identity lists do not narrow connector collection.
- `pilotUserIds`: actual pilot users' UPNs for the DLP hunting query.
- `agentObjectIds`: verified individual Entra agent object IDs for the watchlist and alert correlation.
- `purview`: your new pilot policy/rule names, specific user mailbox primary SMTP addresses and/or SharePoint site URLs, and the sensitive information type. No `All` scopes are accepted.

Purview runs only use the `purview` settings, so Azure placeholders can remain for a
Purview-only deployment. The Python Sentinel validator validates both sections; replace
mailbox placeholders there too. Do not copy tenant IDs or scopes from examples into a
real plan. Names are not proof that an identity is an agent: confirm the object IDs in
the agent inventory before including them.

## 2. Preview the Sentinel pack offline

```sh
python3 scripts/a365-admin.py build \
  --config config/pilot.local.json \
  --admin-config config/admin.local.json \
  --out artifacts/admin-offline-build.json
```

This creates JSON request manifests for installation and enable/disable stages. It does not authenticate,
call Azure, check licensing or produce an executable approval plan.

## 3. Prepare your administrator sessions

Follow [setup](setup.md) for the dedicated Azure CLI cache and explicit login to your
test tenant. The deployment scripts do not log in, switch accounts, consent, activate
PIM, assign licenses, register providers or grant roles for you.

For Sentinel, the plan needs Azure read access to the selected subscription/resource
group and relevant workspace resources, plus `Organization.Read.All` for Graph tenant
verification. Apply needs the relevant Azure resource write permissions. Typical role
assignments are Microsoft Sentinel Contributor, Log Analytics Contributor and workbook
write access at the appropriate scope; a resource-group Contributor can cover these
resource writes but is broader. Connector setup can additionally require Microsoft
Entra security roles and product-specific permissions. Global Administrator alone does
not confer Azure resource-group access. Ensure `Microsoft.OperationalInsights`,
`Microsoft.SecurityInsights` and `Microsoft.Insights` are already registered for the
subscription. Obtain any missing roles/registrations through your normal admin process.

For Purview, open PowerShell and use the same three explicit connections shown in
[setup](setup.md): Graph, Exchange with prefix `A365Audit`, and Security & Compliance
with prefix `A365Dlp`. Invoke the script **inside that same PowerShell session**, not
from a new `pwsh -File` process. The script verifies the tenant name/ID and every session
before reading or changing settings. DLP writes need DLP Compliance Management;
audit changes need Audit Logs; mailbox scope verification needs recipient read access.
Install the Microsoft modules first if they are absent. Existing license eligibility
is required; no script can bypass procurement restrictions.

## 4. Plan and deploy Sentinel one stage at a time

Start with `foundation`:

```sh
python3 scripts/a365-admin.py plan --live --stage foundation \
  --config config/pilot.local.json --admin-config config/admin.local.json \
  --tenant-id '<YOUR-TEST-TENANT-ID>' --environment isolated-pilot \
  --out artifacts/sentinel-foundation-plan.json
```

Read the saved plan. Review every `create` and `reuse`, current and desired settings,
resource ID, connector scope, roles, costs and rollback. Record the human approval and
change ticket in your access-controlled change system. The digest binds the plan; it
is not an electronic signature or evidence of an approver's identity.

First run the optional dry-run:

```sh
python3 scripts/a365-admin.py apply --live \
  --config config/pilot.local.json --admin-config config/admin.local.json \
  --tenant-id '<YOUR-TEST-TENANT-ID>' --environment isolated-pilot \
  --plan-file artifacts/sentinel-foundation-plan.json
```

Only after you approve that exact plan, execute it using the displayed digest:

```sh
python3 scripts/a365-admin.py apply --live \
  --config config/pilot.local.json --admin-config config/admin.local.json \
  --tenant-id '<YOUR-TEST-TENANT-ID>' --environment isolated-pilot \
  --plan-file artifacts/sentinel-foundation-plan.json \
  --execute --approve '<HUMAN-APPROVED-DIGEST>' \
  --evidence-dir artifacts/sentinel-foundation-run-01
```

Then repeat **plan → review → approve → apply**, with new filenames, for:

1. `--stage connectors`, once the workspace and Sentinel onboarding are ready.
2. `--stage content`, once both `SecurityAlert` and `OfficeActivity` tables and their required columns exist. Allow ingestion time and generate benign test activity as appropriate.

Each stage has its own plan and approval. Existing connectors with another ID are
blocked for review to avoid duplicate ingestion. Content deployment refuses to replace
existing resources with different settings. Replanning safely reuses matching resources;
a watchlist must finish upload and its items must match before it can be reused.
Existing foundation resources are consumed without changing their retention, cap or tags.

Azure provisioning can be asynchronous. A `not verifiable` result is not a failed
transaction that is safe to retry blindly. Inspect `intent.json`, numbered receipts,
`outcome.json` and Azure resource state. Wait for provisioning, then make a **new** plan
for the remaining changes. No write is automatically retried and no rollback deletes
resources. Concurrent administrator activity is not transactionally locked.

Verify the content configuration afterward:

```sh
python3 scripts/a365-admin.py verify --live --stage content \
  --config config/pilot.local.json --admin-config config/admin.local.json \
  --tenant-id '<YOUR-TEST-TENANT-ID>' --environment isolated-pilot \
  --out artifacts/sentinel-content-verification.json
```

Open the workbook and saved hunting queries in Sentinel. Run each query and verify
actual test events. The scheduled rules and incident-task automation remain disabled.
After the queries and benign events validate, use the same **plan → review → approve → apply**
sequence with `--stage activate` and new filenames to enable the two installed rules and
incident-task automation. `--stage deactivate` prepares a separately approved change to
disable those same resources without deleting evidence. These stages preserve other
existing properties and refuse changes if the installed rule configuration differs from
the pack. Deactivation does not require healthy ingestion. A live API must accept the queries; offline tests do not compile KQL. DLP events are scoped to pilot
users, not proven to originate from agents. Agent alert correlation only matches alerts
whose entities contain the configured ID in `AadUserId`; other entity formats are not
covered. No matching rows is inconclusive.

## 5. Plan and deploy Purview DLP

In the already connected PowerShell session, create a plan:

```powershell
./scripts/Set-PurviewPilot.ps1 -Command Plan -Intent DlpCreate `
  -Config config/pilot.local.json -AdminConfig config/admin.local.json `
  -TenantId '<YOUR-TEST-TENANT-ID>' -Environment isolated-pilot `
  -PlanFile artifacts/purview-dlp-plan.json
```

Review `planJson` and its digest. It resolves the sensitive information type and each
mailbox, verifies the policy/rule names are unused, and records the exact locations.
After approval:

```powershell
./scripts/Set-PurviewPilot.ps1 -Command Apply `
  -Config config/pilot.local.json -AdminConfig config/admin.local.json `
  -TenantId '<YOUR-TEST-TENANT-ID>' -Environment isolated-pilot `
  -PlanFile artifacts/purview-dlp-plan.json `
  -Execute -Approve '<HUMAN-APPROVED-DIGEST>' `
  -EvidenceDirectory artifacts/purview-dlp-run-01
```

Omitting `-Execute` and `-Approve` performs a dry-run. The policy is created directly
in `TestWithoutNotifications`, then the rule is added to its exact GUID. Although the
rule's intended action is blocking, simulation mode performs no blocking or notifications.
The toolkit never promotes it to enforcement or changes an existing policy.

The result deliberately remains `not verifiable` until an admin checks the effective
policy locations, sensitive-information predicate, rule action and distribution status
in Purview and performs a benign test. A create receipt or successful mode read is not
proof of DLP protection. Partial creation keeps receipts; inspect before recovery.
Add the new policy name to `pilot.local.json` → `purview.policyNames` **after** applying
(the configuration hash must remain unchanged between plan and apply), then run the
existing [Purview verifier](purview.md).

For audit ingestion, repeat the same sequence with `-Intent AuditEnable` and new
plan/evidence paths. This is explicitly tenant-wide and has its own approval. Never
disable auditing as an automatic rollback.

## References and tested boundary

The new flows are offline/mock tested. They have not been deployed to a live tenant.
The XDR connector uses a preview ARM API; availability and behavior can differ by tenant.
The supported interfaces are:

- [Sentinel onboarding](https://learn.microsoft.com/en-us/azure/templates/microsoft.securityinsights/2025-03-01/onboardingstates) and [connector schemas](https://learn.microsoft.com/en-us/azure/templates/microsoft.securityinsights/2025-07-01-preview/dataconnectors).
- [Scheduled analytics](https://learn.microsoft.com/en-us/azure/templates/microsoft.securityinsights/2025-03-01/alertrules), [watchlists](https://learn.microsoft.com/en-us/azure/templates/microsoft.securityinsights/2025-03-01/watchlists), [automation rules](https://learn.microsoft.com/en-us/azure/templates/microsoft.securityinsights/2025-03-01/automationrules), [workbooks](https://learn.microsoft.com/en-us/azure/templates/microsoft.insights/2022-04-01/workbooks), and [saved searches](https://learn.microsoft.com/en-us/azure/templates/microsoft.operationalinsights/2020-08-01/workspaces/savedsearches).
- [New-DlpCompliancePolicy](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/new-dlpcompliancepolicy?view=exchange-ps), [New-DlpComplianceRule](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/new-dlpcompliancerule?view=exchange-ps), and [audit enablement](https://learn.microsoft.com/en-us/purview/audit-log-enable-disable).
- [Defender Security for AI setup](https://learn.microsoft.com/en-us/defender-xdr/security-for-ai/get-started-defender-security-for-ai) and [Sentinel connector reference](https://learn.microsoft.com/en-us/azure/sentinel/data-connectors-reference) for the separate Agent 365 data lake path.
