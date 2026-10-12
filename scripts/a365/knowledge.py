"""Read-only inventory export for the knowledge dashboard. Never invent knowledge links."""
import argparse
import json
import sys
from pathlib import Path

from .core import ROOT, SafetyError, check_config, guid, now, read_json, require, timestamp, write_json
from .graph import Graph, CATALOG
from .operations import is_agent


def observation(value, source, checked_at):
    return {'value': value, 'evidence': {'source': source, 'checkedAt': checked_at}}


def from_inventory(snapshot, kind):
    require(kind in ('sample', 'tenant-export'), 'Explicit provenance kind required')
    require(snapshot.get('schemaVersion') == 1 and isinstance(snapshot.get('agents'), list), 'Expected version 1 toolkit inventory snapshot')
    stamp = snapshot.get('capturedAt')
    timestamp(stamp)
    require(isinstance(snapshot.get('source'), str) and snapshot['source'], 'Snapshot source required')
    agents, seen = [], set()
    for record in snapshot['agents']:
        key = record.get('packageId')
        require(isinstance(key, str) and key and key not in seen, 'Missing or duplicate package ID')
        seen.add(key)
        for field in ('name', 'platform'):
            require(record.get(field) is None or isinstance(record[field], str), 'Invalid agent metadata')
        owners = record.get('owners')
        require(owners is None or (isinstance(owners, list) and all(isinstance(x, str) for x in owners)), 'Owners must be strings or null')
        agents.append({'packageId': key, 'name': record.get('name'), 'platform': record.get('platform'),
                       'owners': owners, 'sourcesComplete': False, 'sources': None,
                       'evidence': {'source': snapshot['source'], 'checkedAt': stamp}})
    return {'schemaVersion': 1, 'dataKind': kind,
            'name': '{} agent inventory · knowledge relationships unavailable'.format('Sample' if kind == 'sample' else 'Tenant'),
            'capturedAt': stamp, 'complete': False, 'labels': [],
            'discoveredContainers': observation(None, 'Not collected by the agent inventory API', stamp), 'agents': agents}


def collect_catalog(graph, cfg):
    require(graph.verified, 'Verify selected tenant before collection')
    require(graph.tenant == cfg['tenant'], 'Collector tenant differs from selected configuration')
    rows = graph.collection(CATALOG)
    # Copy only normalized identity metadata. No manifest, instructions, permissions,
    # raw provider response, prompt/response, or inferred knowledge relationships.
    agents = []
    for record in rows:
        require(isinstance(record, dict), 'Invalid catalog record')
        if is_agent(record):
            agents.append({'packageId': record.get('id'), 'name': record.get('displayName'),
                           'platform': record.get('platform') if isinstance(record.get('platform'), str) else None,
                           'owners': None})
    snapshot = {'schemaVersion': 1, 'agents': agents, 'capturedAt': now(), 'source': CATALOG,
                'tenantId': cfg['tenant']['id'], 'environment': cfg['tenant']['environment']}
    return from_inventory(snapshot, 'tenant-export')


def main(argv=None):
    p = argparse.ArgumentParser(description='Read-only dashboard inventory export; knowledge-source collection is platform-specific and not provided by the catalog')
    p.add_argument('command', choices=('collect', 'collect-studio', 'convert-inventory'))
    p.add_argument('--config', default=str(ROOT / 'config/pilot.local.json'))
    p.add_argument('--live', action='store_true')
    p.add_argument('--tenant-id')
    p.add_argument('--environment')
    p.add_argument('--dataverse-url')
    p.add_argument('--bot-id', action='append', help='Optional explicit Dataverse bot UUID; repeat to select agents')
    p.add_argument('--snapshot', type=Path)
    p.add_argument('--snapshot-kind', choices=('sample', 'tenant-export'))
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args(argv)
    try:
        require(args.command == 'collect-studio' or (not args.dataverse_url and not args.bot_id), 'Dataverse arguments require collect-studio')
        require(args.out.suffix == '.json' and not args.out.exists(), 'Use a new .json output path')
        if args.command == 'convert-inventory':
            require(not args.live and args.snapshot and args.snapshot_kind, 'Offline conversion needs --snapshot and --snapshot-kind; no --live')
            data = from_inventory(read_json(args.snapshot), args.snapshot_kind)
        else:
            require(args.live and not args.snapshot and not args.snapshot_kind, 'Collection needs --live; snapshot arguments are for conversion only')
            cfg = check_config(read_json(args.config), live=True)
            require(args.tenant_id and args.tenant_id.lower() == cfg['tenant']['id'].lower() and args.environment == cfg['tenant']['environment'], 'Explicit tenant/environment must match configuration')
            if args.command == 'collect-studio':
                from .studio import Dataverse, environment_origin, collect_studio
                require(args.dataverse_url, 'Supply the explicitly selected --dataverse-url')
                origin = environment_origin(args.dataverse_url)
                require(all(guid(v) for v in (args.bot_id or [])), 'Invalid bot UUID')
                try:
                    import yaml  # Check optional dependency before authentication.
                except ImportError:
                    raise SafetyError('Install requirements-knowledge.txt in a virtual environment for Studio collection') from None
            print(json.dumps({'selectedTenant': cfg['tenant'], 'mode': 'read-only',
                              'permissions': ['Organization.Read.All', 'Dataverse user_impersonation and read access to bots/botcomponents' if args.command == 'collect-studio' else 'CopilotPackages.Read.All'],
                              'requirements': 'Existing authorized admin session and catalog access; no login, consent, role or license changes.',
                              'coverage': 'Partial Studio authoring knowledge metadata; labels, site resolution, external classification and runtime retrieval remain unknown.' if args.command == 'collect-studio' else 'Catalog agent identity metadata only; knowledge relationships unavailable.'}), flush=True)
            graph = Graph.from_cli(cfg['tenant'])
            graph.verify()
            if args.command == 'collect-studio':
                client = Dataverse.connect(cfg['tenant'], origin)
                client.verify()
                data = collect_studio(client, cfg, args.bot_id)
            else:
                data = collect_catalog(graph, cfg)
        write_json(args.out, data)
        print(json.dumps({'status': 'not verifiable', 'output': str(args.out), 'agentsExported': len(data['agents']),
                          'evidence': 'Metadata exported with partial/unknown knowledge coverage. Load the JSON in the dashboard. No sample relationships added.'}))
        return 2  # Metadata exported, but knowledge coverage remains explicitly unknown.
    except (SafetyError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(str(exc) if isinstance(exc, SafetyError) else 'Collection/input/output failed; provider response withheld', file=sys.stderr)
        return 1
