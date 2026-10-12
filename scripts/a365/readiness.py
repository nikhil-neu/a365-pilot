"""Read-only agent risk evidence. No risk dismissal, consent or mutation operations."""
import argparse
import json
import sys
from pathlib import Path
from .core import SafetyError, check_config, read_json, require, now, write_json
from .graph import Graph

FIELDS = {
    'riskyAgents': ('id', 'agentDisplayName', 'identityType', 'riskLevel', 'riskState', 'riskLastModifiedDateTime'),
    'agentRiskDetections': ('id', 'identityId', 'displayName', 'riskEventType', 'riskLevel', 'riskState', 'detectedDateTime', 'lastModifiedDateTime'),
}


def collect(graph):
    require(graph.verified, 'Verify tenant before collecting risk evidence')
    results = []
    for collection, fields in FIELDS.items():
        path = '/beta/identityProtection/' + collection + '?$select=' + ','.join(fields)
        item = {'capability': collection, 'source': path, 'checkedAt': now(),
                'status': 'not verifiable', 'count': None, 'records': None}
        try:
            rows = graph.collection(path)
            require(all(isinstance(row, dict) and isinstance(row.get('id'), str) and row['id'] for row in rows), 'Malformed risk metadata')
            # Explicit projection also strips unexpected provider fields from evidence.
            item.update(status='skipped', count=len(rows), records=[
                {key: row.get(key) if isinstance(row.get(key), (str, bool, int, float)) else None for key in fields}
                for row in rows])
            item['evidence'] = 'Read succeeded; an empty collection does not prove protection coverage.'
        except SafetyError:
            item['evidence'] = 'Read unavailable or incomplete; check permissions, service availability and transport. No raw response exported.'
        results.append(item)
    return {'schemaVersion': 1, 'operation': 'agent-risk-assessment', 'capturedAt': now(),
            'tenant': graph.tenant, 'dataKind': 'tenant-export', 'apiMaturity': 'beta',
            'protectionCoverage': 'not verifiable', 'results': results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--config', type=Path, default=Path('config/pilot.local.json'))
    parser.add_argument('--tenant-id')
    parser.add_argument('--environment')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        require(args.live, 'Risk collection requires explicit --live')
        require(args.out.suffix == '.json' and not args.out.exists(), 'Use a new .json evidence path')
        cfg = check_config(read_json(args.config), live=True)
        require(args.tenant_id and args.tenant_id.lower() == cfg['tenant']['id'].lower()
                and args.environment == cfg['tenant']['environment'], 'Explicit tenant/environment must match configuration')
        print('Read-only beta risk APIs; existing authorized session required; no login or consent changes.', flush=True)
        graph = Graph.from_cli(cfg['tenant'])
        graph.verify()
        report = collect(graph)
        write_json(args.out, report)
        print(json.dumps({'output': str(args.out), 'status': 'not verifiable',
                          'evidence': 'Risk read results saved; protection coverage needs separate verification.'}))
        return 2
    except (SafetyError, OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc) if isinstance(exc, SafetyError) else 'Risk assessment failed; input/provider details withheld', file=sys.stderr)
        return 1
