"""Command line entry point. Offline unless --live is explicitly supplied."""
import argparse
import json
import sys
from pathlib import Path

from .audit import audit_inventory
from .core import ROOT, SafetyError, check_config, guid, now, read_json, report, require, result, save_report, timestamp, write_json
from .graph import Graph, HUNT
from .operations import apply_plan, assess, build_plan, ca_payload, envelope, inventory_snapshot, validate_live


def parser():
    p = argparse.ArgumentParser(description='Agent 365 security operations kit: isolated development/test tenants only')
    p.add_argument('command', choices=['check-config', 'assess', 'plan', 'build', 'validate', 'apply', 'contain', 'audit', 'verify-invocation'])
    p.add_argument('--config', default=str(ROOT / 'config/pilot.example.json'))
    p.add_argument('--live', action='store_true', help='Explicit opt-in to tenant reads; no login or consent performed')
    p.add_argument('--tenant-id')
    p.add_argument('--environment')
    p.add_argument('--out', type=Path, help='New JSON report path; Markdown and HTML siblings are also created')
    p.add_argument('--plan-out', type=Path)
    p.add_argument('--plan-file', type=Path)
    p.add_argument('--intent', choices=['ca-deploy', 'ca-promote', 'ca-disable', 'registry-block', 'registry-unblock'], default='ca-deploy')
    p.add_argument('--agent-id', help='Exact registry package ID (not display name or appId)')
    p.add_argument('--snapshot', type=Path)
    p.add_argument('--snapshot-out', type=Path)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--approve', help='SHA-256 digest of the exact reviewed plan, supplied after human approval')
    p.add_argument('--evidence-dir', type=Path)
    p.add_argument('--app-id', help='Observability application/client ID, not Entra object ID')
    p.add_argument('--conversation-id')
    p.add_argument('--since', help='UTC ISO-8601 invocation start')
    p.add_argument('--until', help='UTC ISO-8601 invocation end')
    return p


def run(args):
    cfg = check_config(read_json(args.config), live=args.live)
    require(not args.execute or args.command == 'apply', '--execute is allowed only for apply')
    require(not args.approve or (args.command == 'apply' and args.execute), '--approve requires apply --execute')
    require(not args.snapshot_out or (args.command == 'assess' and args.live), '--snapshot-out requires assess --live')
    require(not args.plan_out or args.command in ('plan', 'build', 'contain'), '--plan-out requires a planning/build command')
    require(not args.out or args.out.suffix == '.json', '--out must be a new .json report path')
    if args.command in ('check-config', 'build', 'audit'):
        require(not args.live, args.command + ' is offline only')
    graph = None
    if args.live:
        require(args.tenant_id and args.environment, 'Every live command requires --tenant-id and --environment')
        require(args.tenant_id.lower() == cfg['tenant']['id'].lower() and args.environment == cfg['tenant']['environment'], 'CLI selection differs from configured test tenant')
        permissions = ['Organization.Read.All']
        roles = ['Tenant organization read access']
        if args.command == 'assess':
            permissions += ['LicenseAssignment.Read.All', 'User.Read', 'Policy.Read.All', 'IdentityRiskyAgent.Read.All', 'CopilotPackages.Read.All', 'ThreatHunting.Read.All']
            roles += ['Directory Readers or supported license reader', 'Security Reader', 'AI Administrator', 'Defender hunting RBAC']
        elif args.command in ('validate', 'verify-invocation'):
            permissions += ['ThreatHunting.Read.All'] + (['Policy.Read.All'] if args.command == 'validate' else [])
            roles += ['Defender hunting RBAC', 'Security Reader']
        elif args.command in ('plan', 'contain', 'apply'):
            permissions += ['Policy.Read.All / AgentIdentity.Read.All for CA plans', 'CopilotPackages.Read.All for registry plans', 'Optional enrichment: Application.Read.All, Directory.Read.All, IdentityRiskyAgent.Read.All']
            roles += ['CA read role or AI Administrator; identity read role if mapping is configured']
        print(json.dumps({'operation': args.command, 'selectedTenant': cfg['tenant'], 'intent': args.intent if args.command in ('plan', 'apply', 'contain') else None,
                          'mode': 'approved write requested' if args.execute else 'read-only',
                          'requiredPermissions': permissions, 'requiredRoles': roles,
                          'requirements': 'Organization.Read.All plus operation-specific permissions/roles in docs/permissions.md; licensed Agent 365, Entra and Defender/Purview as applicable.',
                          'impact': 'Reads organization and selected tenant metadata; apply can issue one approved mutation. No consent or license assignment performed.'}, indent=2), flush=True)
        if args.command == 'apply':
            require(args.plan_file, 'Apply needs --plan-file')
            displayed = read_json(args.plan_file)
            print(json.dumps({'reviewedPlanBeforeAnyWrite': displayed}, indent=2), flush=True)
        graph = Graph.from_cli(cfg['tenant'])
        graph.verify()
    if args.command == 'check-config':
        operations = [result('configuration', 'skipped', 'Schema and safety constraints valid; placeholders allowed offline', observed='valid')]
    elif args.command in ('assess', 'validate'):
        operations = (assess(graph, cfg) if args.command == 'assess' else validate_live(graph, cfg)) if graph else [result('offline-readiness', 'skipped', {'configurationValid': True, 'tenantConnected': False, 'next': 'Run python3 -m unittest discover -s tests -v'}), result('tenant-controls', 'not verifiable', 'Offline; no live control or license state read')]
    elif args.command in ('plan', 'contain', 'build'):
        if args.command == 'contain':
            require(args.agent_id, 'Containment requires one exact --agent-id package ID')
            intent = 'registry-block'
        else:
            intent = args.intent
        if graph:
            doc = envelope(build_plan(graph, cfg, intent, args.agent_id))
            if args.plan_out:
                write_json(args.plan_out, doc)
            operations = [result(intent, 'skipped', doc, impact=doc['plan']['impact'], rollback=doc['plan']['rollback'], simulation=True)]
        else:
            require(intent == 'ca-deploy' or args.command == 'contain', 'State-change plans need live precondition reads')
            offline = {'origin': 'offline-not-applicable', 'baseline': ca_payload(cfg), 'profile': read_json(ROOT / 'config/profiles' / (cfg['profile'] + '.json')),
                       'purview': cfg['purview'], 'defender': 'manual admin checklist: docs/connectors.md',
                       'registry': {'action': 'simulate availability block' if args.command == 'contain' else 'audit only', 'packageId': args.agent_id},
                       'enrichment': 'not verifiable offline; owner, platform, identity, permissions, tools and risk require live evidence'}
            if args.plan_out:
                write_json(args.plan_out, offline)
            operations = [result('offline-artifacts', 'skipped', offline, impact='Local output only; no control enabled')]
    elif args.command == 'apply':
        require(graph and args.plan_file, 'Apply needs --live and --plan-file; defaults to dry-run')
        require(not args.execute or (args.evidence_dir and args.approve), 'Execution requires approval digest and a fresh evidence directory')
        operations = [apply_plan(graph, cfg, read_json(args.plan_file), args.approve, args.evidence_dir, args.execute)]
    elif args.command == 'audit':
        require(args.snapshot, 'Audit requires --snapshot; acquire it using assess --live --snapshot-out')
        operations = audit_inventory(cfg, read_json(args.snapshot))
    elif args.command == 'verify-invocation':
        require(graph, 'Invocation verification requires --live')
        require(guid(args.app_id) and guid(args.conversation_id), 'Use exact app and conversation UUIDs')
        require(args.since and args.until and timestamp(args.since) < timestamp(args.until), 'Explicit increasing invocation window required')
        query = (ROOT / 'queries/verify-invocation.kql').read_text().replace('<APP-ID>', args.app_id).replace('<CONVERSATION-ID>', args.conversation_id).replace('<START-UTC>', timestamp(args.since).isoformat()).replace('<END-UTC>', timestamp(args.until).isoformat())
        data = graph.request('POST', HUNT, {'Query': query})
        rows = data.get('results')
        require(isinstance(rows, list), 'Invalid hunting response')
        operations = [result('defender-invocation', 'skipped' if rows else 'not verifiable', rows, observed='invocation metadata observed' if rows else 'no matching event; retry after expected ingestion delay'),
                      result('purview-and-admin-center-invocation', 'manual admin step required', 'Match same agent, conversation and UTC window in both portals; docs/validation.md. Defender alone does not verify all surfaces.')]
    else:
        raise SafetyError('Unsupported command')
    if args.snapshot_out:
        require(graph and args.command == 'assess', '--snapshot-out requires assess --live')
        write_json(args.snapshot_out, inventory_snapshot(graph, cfg))
    data = report(args.command, cfg, operations, live=bool(graph))
    if args.out:
        save_report(args.out, data)
    print(json.dumps(data, indent=2))
    if any(x['status'] == 'failed' for x in operations):
        return 1
    if any(x['status'] in ('not verifiable', 'manual admin step required') for x in operations):
        return 2
    return 0


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return run(args)
    except (SafetyError, OSError, ValueError, KeyError, TypeError) as exc:
        # Do not echo raw provider bodies, subprocess stderr or tokens.
        detail = str(exc) if isinstance(exc, SafetyError) else 'Local input/output or schema error: ' + type(exc).__name__
        print(json.dumps(result(args.command, 'failed', detail)), file=sys.stderr)
        return 1
