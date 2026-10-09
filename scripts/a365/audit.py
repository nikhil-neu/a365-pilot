"""Inventory comparison: absent evidence is unknown, never compliant."""
from datetime import datetime, timezone

from .core import require, result, timestamp


def audit_inventory(cfg, snapshot):
    require(snapshot.get('schemaVersion') == 1, 'Unsupported inventory snapshot')
    require(snapshot.get('tenantId', '').lower() == cfg['tenant']['id'].lower(), 'Inventory tenant mismatch')
    require(snapshot.get('environment') == cfg['tenant']['environment'], 'Inventory environment mismatch')
    age = (datetime.now(timezone.utc) - timestamp(snapshot['capturedAt'])).total_seconds() / 3600
    require(0 <= age <= cfg['telemetry']['maxAgeHours'], 'Inventory snapshot stale or in future')
    agents = snapshot.get('agents')
    require(isinstance(agents, list), 'Snapshot agents must be a list')
    require(type(snapshot.get('complete', False)) is bool, 'Snapshot completeness must be a boolean')
    ids = [a['packageId'] for a in agents]
    require(len(ids) == len(set(ids)), 'Duplicate discovered package IDs')
    approved = {a['packageId']: a for a in cfg['approvedInventory']}
    findings = []
    for a in agents:
        key = a['packageId']
        for field in ('owners', 'permissions', 'tools', 'controls'):
            require(a.get(field) is None or (isinstance(a[field], list) and all(isinstance(v, str) for v in a[field])), 'Normalized snapshot requires string lists or null')
        expected = approved.get(key)
        problems, unknown = [], []
        if not expected:
            problems.append('unapproved inventory entry')
        for field in ('owners', 'permissions', 'tools', 'controls', 'lastSeen', 'risk', 'agentObjectId', 'blueprintId'):
            if a.get(field) is None:
                unknown.append(field)
        if a.get('owners') == []:
            problems.append('missing owner')
        if a.get('risk') in ('high', 'medium'):
            problems.append('risky agent: ' + a['risk'])
        if a.get('lastSeen'):
            elapsed = (datetime.now(timezone.utc) - timestamp(a['lastSeen'])).total_seconds() / 3600
            if elapsed < 0 or elapsed > cfg['telemetry']['maxAgeHours']:
                problems.append('telemetry stale or future-dated')
        if expected:
            for field in ('name', 'platform', 'version', 'agentObjectId', 'blueprintId', 'observabilityAppId'):
                if a.get(field) is None:
                    unknown.append(field)
                elif a[field] != expected[field]:
                    problems.append(field + ' drift')
            for field in ('permissions', 'tools', 'owners'):
                if a.get(field) is not None:
                    require(isinstance(a[field], list) and all(isinstance(v, str) for v in a[field]), 'Normalized inventory requires string lists')
                    if set(a[field]) - set(expected[field]):
                        problems.append('unapproved ' + field)
                    if field == 'owners' and set(expected[field]) - set(a[field]):
                        problems.append('approved owner missing')
            if a.get('controls') is not None and set(expected['requiredControls']) - set(a['controls']):
                problems.append('missing required controls')
        findings.append(result('registry-audit:' + key, 'failed' if problems else ('not verifiable' if unknown else 'skipped'),
                               {'findings': problems, 'unknownFields': sorted(set(unknown)), 'source': snapshot.get('source', 'operator-supplied snapshot'), 'capturedAt': snapshot['capturedAt']},
                               observed='drift' if problems else ('unknown' if unknown else 'matches-approved-inventory')))
    for key in sorted(set(approved) - set(ids)):
        findings.append(result('registry-audit:' + key, 'failed' if snapshot.get('complete') is True else 'not verifiable', {'finding': 'approved agent not discovered', 'complete': snapshot.get('complete', False)}))
    if not findings:
        findings.append(result('registry-audit', 'not verifiable', 'No agents or approved baseline; no assurance established'))
    return findings
