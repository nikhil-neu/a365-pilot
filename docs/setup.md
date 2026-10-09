> Product direction: [a365-toolkit workflow](deployment-workflow.md). These instructions retain the existing sandbox configuration and command compatibility.

# Setup and explicit tenant selection

Stage 0 needs Python 3.9+ only. Do not install Microsoft modules or authenticate to run
the offline tests. Run the README checks first. For live Graph reads, install a supported
Azure CLI using Microsoft's installer. The kit supports the commercial global cloud only.

1. Have the administrator identify the isolated development/test tenant UUID, exact
   organization display name and the local environment label. Confirm them out of band.
2. Copy the example to `config/pilot.local.json`. Local config is gitignored. Replace
   CA targets with individual agent **object IDs**, and resources with **application
   IDs** before CA planning. A Stage 1 read-only assessment can retain CA placeholders
   when no test agent exists yet. These are different identifier namespaces. No wildcards or blueprint targets.
   Fill policy names, choose a profile and add approved inventory entries using the
   separate example. Profiles describe recommended controls, not product enforcement.
3. Review [permissions](permissions.md). Use separate read and change sessions. Scope
   availability depends on the authentication client and existing administrator consent.
   Azure CLI does not acquire arbitrary Graph permissions by listing them in a command.
   If its first-party client lacks a scope, the operation stays not verifiable; use the
   documented portal procedure or have an administrator review an approved authentication
   client integration. Do not paste tokens or silently grant tenant-wide consent.
4. Create a dedicated cache outside the repository and explicitly log in. These commands
   perform authentication; only run them when the administrator has selected the tenant.

```sh
export A365_AZURE_CONFIG_DIR="$HOME/.a365-pilot-azure"
mkdir -p "$A365_AZURE_CONFIG_DIR"
chmod 700 "$A365_AZURE_CONFIG_DIR"
AZURE_CONFIG_DIR="$A365_AZURE_CONFIG_DIR" az login \
  --tenant '<TEST-TENANT-ID>' --allow-no-subscriptions
```

Do not accept new consent prompts without explicit approval. The CLI never runs `az
login` or changes an account. It passes `--tenant` to token acquisition and checks the
returned tenant, then queries `/organization` and checks ID **and exact display name**.
The environment is an operator-defined binding, not a discovered Power Platform
environment or proof the tenant is nonproduction. Azure CLI owns its external credential
cache; access tokens are held only in process memory by this kit. Do not use shell tracing.

Run the README read-only command. To obtain a catalog snapshot, add
`--snapshot-out artifacts/catalog-snapshot.json`. Portal and service roles, license
eligibility and connector health remain separate checks even if Graph requests succeed.

## Purview session

On a workstation with PowerShell 7.2+, install the supported `Microsoft.Graph.Authentication`,
`Microsoft.Graph.Identity.DirectoryManagement`, and `ExchangeOnlineManagement` modules
through your approved software process. In a fresh PowerShell process connect explicitly:

```powershell
Connect-MgGraph -TenantId '<TEST-TENANT-ID>' -Scopes 'Organization.Read.All' -ContextScope Process
Connect-ExchangeOnline -UserPrincipalName '<TEST-ADMIN-UPN>' -Prefix A365Audit
Connect-IPPSSession -UserPrincipalName '<TEST-ADMIN-UPN>' -Prefix A365Dlp
./scripts/Test-Purview.ps1 -Config config/pilot.local.json `
  -TenantId '<TEST-TENANT-ID>' -Environment isolated-pilot
```

At sign-in select the chosen test tenant explicitly; stop on an unexpected tenant or
consent prompt. The verifier rejects every mixed/stale Exchange connection, checks the
Graph organization and uses prefixed commands. Neither session creation nor the verifier
changes policy. Disconnect using `Disconnect-ExchangeOnline` and `Disconnect-MgGraph`
afterward. Do not persist transcripts containing authentication material or raw audit data.

Microsoft sources: [Azure CLI token acquisition](https://learn.microsoft.com/en-us/cli/azure/account#az-account-get-access-token),
[Graph organization](https://learn.microsoft.com/en-us/graph/api/organization-list?view=graph-rest-1.0),
[connection information](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/get-connectioninformation?view=exchange-ps).

## Deploy controls after approval

Continue with [administrator deployment](admin-deployment.md) for toolkit-executed
Purview DLP, audit enablement and the Sentinel pack. Assessment alone never installs them.
