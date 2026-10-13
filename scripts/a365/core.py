"""Strict configuration, evidence and offline report helpers."""
import hashlib
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[2]
STATUSES = {'applied', 'skipped', 'manual admin step required', 'failed', 'not verifiable'}


class SafetyError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise SafetyError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Timestamp must include timezone')
    return result


def guid(value):
    try:
        return str(UUID(value)) == value.lower() and UUID(value).int != 0
    except (ValueError, TypeError, AttributeError):
        return False


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Never overwrite an existing evidence file or follow a destination symlink.
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def write_text(path, value):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(value)


def check_config(cfg, live=False):
    require(isinstance(cfg, dict) and cfg.get('schemaVersion') == 1, 'Expected config schemaVersion 1')
    require(set(cfg) == {'schemaVersion', 'tenant', 'profile', 'conditionalAccess', 'purview', 'telemetry', 'approvedInventory'}, 'Unknown or missing configuration keys')
    tenant = cfg['tenant']
    require(set(tenant) == {'id', 'displayName', 'environment', 'purpose'}, 'Invalid tenant configuration')
    require(tenant['purpose'] in ('development', 'test'), 'Only development/test tenants supported')
    require(all(isinstance(tenant[k], str) and tenant[k].strip() for k in ('id', 'displayName', 'environment')), 'Explicit tenant identity required')
    require(re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', tenant['environment']), 'Invalid environment name')
    require(guid(tenant['id']) or (not live and tenant['id'] == '<TEST-TENANT-ID>'), 'Supply a nonzero test tenant UUID')
    if live:
        require('<' not in tenant['displayName'], 'Replace tenant display-name placeholder')
    profile = ROOT / 'config' / 'profiles' / (cfg['profile'] + '.json')
    require(cfg['profile'] in ('read-only', 'data-access', 'action-capable', 'soc-monitoring', 'agent-assurance'), 'Unknown profile')
    require(profile.exists(), 'Missing profile')
    ca = cfg['conditionalAccess']
    required_ca = {'displayName', 'agentObjectIds', 'resourceAppIds', 'riskLevels', 'state'}
    require(required_ca <= set(ca) <= required_ca | {'targetType', 'resourceScope'}, 'Invalid CA configuration')
    require(ca.get('targetType', 'individual') in ('individual', 'blueprint'), 'Invalid CA targetType')
    require(ca.get('resourceScope', 'selected') in ('selected', 'all'), 'Invalid CA resourceScope')
    require(isinstance(ca['displayName'], str) and ca['displayName'].startswith('A365-PILOT-'), 'CA name must start A365-PILOT-')
    require(ca['state'] == 'enabledForReportingButNotEnforced', 'Baseline must be report-only; promotion is a separate plan')
    require(ca['riskLevels'] == ['high'], 'Pilot baseline supports high agent risk only')
    for key in ('agentObjectIds', 'resourceAppIds'):
        values = ca[key]
        if key == 'resourceAppIds' and ca.get('resourceScope') == 'all':
            require(values == [], 'All resources requires empty resourceAppIds; do not combine scopes')
            continue
        require(isinstance(values, list) and values and all(isinstance(v, str) for v in values) and len(values) == len(set(values)), key + ' must be a nonempty unique list')
        require(all(guid(v) or (isinstance(v, str) and v.startswith('<') and v.endswith('>')) for v in values), key + ' requires UUIDs or unconfigured placeholders; wildcard scopes prohibited')
    purview = cfg['purview']
    require(set(purview) == {'policyNames', 'expectedMode', 'auditRequired'}, 'Invalid Purview configuration')
    require(isinstance(purview['policyNames'], list) and all(isinstance(x, str) and x for x in purview['policyNames']), 'Invalid Purview policyNames')
    require(purview['expectedMode'] == 'TestWithoutNotifications' and purview['auditRequired'] is True, 'Pilot Purview baseline must request audit and test mode')
    telemetry = cfg['telemetry']
    require(set(telemetry) == {'collectContent', 'maxAgeHours'}, 'Invalid telemetry configuration')
    require(telemetry['collectContent'] is False, 'Content collection is not supported by this kit')
    require(type(telemetry['maxAgeHours']) is int and 1 <= telemetry['maxAgeHours'] <= 720, 'Invalid telemetry age')
    require(isinstance(cfg['approvedInventory'], list), 'Inventory must be a list')
    seen = set()
    for agent in cfg['approvedInventory']:
        required = {'packageId', 'name', 'platform', 'version', 'owners', 'permissions', 'tools', 'requiredControls', 'agentObjectId', 'blueprintId', 'observabilityAppId'}
        require(set(agent) == required, 'Invalid approved inventory fields')
        require(isinstance(agent['packageId'], str) and agent['packageId'] and agent['packageId'] not in seen, 'Duplicate/empty package ID')
        seen.add(agent['packageId'])
        for key in ('owners', 'permissions', 'tools', 'requiredControls'):
            require(isinstance(agent[key], list) and all(isinstance(x, str) and x for x in agent[key]), 'Inventory ' + key + ' must contain strings')
        for key in ('agentObjectId', 'blueprintId', 'observabilityAppId'):
            require(agent[key] is None or guid(agent[key]) or (not live and agent[key].startswith('<')), 'Invalid inventory identity')
    return cfg


def result(operation, status, evidence, impact='Read-only; no tenant change', rollback='None required', **extra):
    require(status in STATUSES, 'Unknown status')
    return dict(operation=operation, status=status, evidence=evidence, impact=impact, rollback=rollback, **extra)


def report(command, cfg, operations, **extra):
    return dict(schemaVersion=1, command=command, capturedAt=now(), tenant=cfg['tenant'], operations=operations, **extra)


def save_report(path, data):
    write_json(path, data)
    from .presentation import markdown, html_report
    write_text(Path(path).with_suffix('.md'), markdown(data))
    write_text(Path(path).with_suffix('.html'), html_report(data))
