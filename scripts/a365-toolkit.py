#!/usr/bin/env python3
"""Product entry point; routes to existing safety-gated executors without approving changes."""
import json
import subprocess
import sys
from a365.core import ROOT, read_json


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ('--help', '-h'):
        print('a365-toolkit: administrator security deployment toolkit\n'
              '  capabilities             Offline capability inventory and gaps\n'
              '  workflow                 Offline deployment sequence\n'
              '  tenant <arguments>       Existing a365.py assessment/Entra/registry commands\n'
              '  sentinel <arguments>     Existing a365-admin.py build/plan/apply/verify commands\n'
              '  purview                  Show same-session PowerShell instructions\n'
              'Current live executors are development/test only. Production support is planned.')
        return 0
    command, rest = args[0], args[1:]
    if command in ('capabilities', 'workflow', 'purview') and rest:
        print('This command takes no additional arguments', file=sys.stderr)
        return 1
    if command == 'capabilities':
        print(json.dumps(read_json(ROOT / 'config/capabilities.json'), indent=2))
        return 0
    if command == 'workflow':
        print('1. Select tenant, environment and workload scope.\n'
              '2. Assess licenses, roles, existing controls and telemetry.\n'
              '3. Build artifacts and prepare service-specific live read-only plans.\n'
              '4. Review exact changes, scope, cost, prerequisites and recovery; record approval.\n'
              '5. Apply only the approved plan using its digest.\n'
              '6. Verify configuration, ingestion and benign runtime tests separately.\n'
              '7. Approve enforcement/activation separately; review drift afterward.\n'
              'Current implementation uses separate service plans, not a cross-service transaction.\n'
              'Guide: docs/deployment-workflow.md')
        return 0
    if command == 'purview':
        print('In your existing, tenant-verified PowerShell session, use:\n'
              './scripts/Set-PurviewPilot.ps1 -Command Plan ...\n'
              './scripts/Set-PurviewPilot.ps1 -Command Apply ...\n'
              'Full parameters: docs/admin-deployment.md. This entry point does not create a new session.')
        return 0
    scripts = {'tenant': 'a365.py', 'sentinel': 'a365-admin.py'}
    if command not in scripts:
        print('Unknown command; use --help', file=sys.stderr)
        return 1
    # Argument array, no shell, no added --live/--execute/approval or hidden login.
    return subprocess.run([sys.executable, str(ROOT / 'scripts' / scripts[command]), *rest], check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
