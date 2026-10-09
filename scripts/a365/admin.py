"""Approved, staged Sentinel resource deployment. No implicit authentication or consent."""
import argparse
import copy
import csv
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request
from uuid import NAMESPACE_URL, uuid5

from .core import ROOT, SafetyError, check_config, digest, guid, now, read_json, require, timestamp, write_json
from .graph import Graph

ARM = 'https://management.azure.com'
API = '2025-03-01'
PREVIEW = '2025-07-01-preview'
STAGES = ('foundation', 'connectors', 'content', 'activate', 'deactivate')


def check_admin(cfg, live=False):
    require(set(cfg) == {'schemaVersion', 'sentinel', 'purview'} and cfg['schemaVersion'] == 1, 'Invalid admin schema')
    s = cfg['sentinel']
    require(set(s) == {'subscriptionId', 'resourceGroup', 'workspaceName', 'location', 'retentionInDays', 'dailyQuotaGb', 'connectors', 'pilotUserIds', 'agentObjectIds'}, 'Invalid Sentinel fields')
    require(guid(s['subscriptionId']) or (not live and s['subscriptionId'] == '<AZURE-SUBSCRIPTION-ID>'), 'Supply subscription UUID')
    for name in ('resourceGroup', 'workspaceName'):
        require(isinstance(s[name], str) and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{3,62}', s[name]), 'Invalid ' + name)
    require(isinstance(s['location'], str) and (re.fullmatch('[a-z0-9]+', s['location']) or (not live and s['location'] == '<AZURE-REGION>')), 'Supply Azure region name')
    require(type(s['retentionInDays']) is int and 30 <= s['retentionInDays'] <= 730, 'Retention must be 30..730 days')
    require(type(s['dailyQuotaGb']) in (int, float) and 0 < s['dailyQuotaGb'] <= 100, 'Explicit daily cap 0..100 GB required; this is not a billing cap')
    require(set(s['connectors']) == {'defenderXdr', 'office365'} and all(type(v) is bool for v in s['connectors'].values()), 'Invalid connector selections')
    for field in ('pilotUserIds', 'agentObjectIds'):
        values = s[field]
        require(isinstance(values, list) and 0 < len(values) <= 100 and len(values) == len(set(values)), 'Supply unique pilot identities')
        for v in values:
            require(isinstance(v, str), 'Identity must be text')
            valid = guid(v) if field == 'agentObjectIds' else re.fullmatch(r'[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', v)
            require(valid or (not live and v.startswith('<') and v.endswith('>')), 'Replace pilot identity placeholders')
    p = cfg['purview']
    require(set(p) == {'policyName', 'ruleName', 'exchangeLocations', 'sharePointLocations', 'sensitiveInformationType', 'minCount'}, 'Invalid Purview fields')
    for key in ('policyName', 'ruleName'):
        require(isinstance(p[key], str) and re.fullmatch(r'A365-PILOT-[A-Za-z0-9_-]{1,64}', p[key]), 'Pilot policy/rule prefix required')
    require(type(p['minCount']) is int and 1 <= p['minCount'] <= 100, 'Invalid sensitive information threshold')
    require(isinstance(p['sensitiveInformationType'], str) and 0 < len(p['sensitiveInformationType']) < 200, 'Choose one sensitive information type')
    require(all(isinstance(p[k], list) for k in ('exchangeLocations', 'sharePointLocations')), 'Locations must be lists')
    require(p['exchangeLocations'] or p['sharePointLocations'], 'Explicit DLP locations required')
    for v in p['exchangeLocations']:
        require(isinstance(v, str) and (re.fullmatch(r'[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', v) or (not live and v.startswith('<'))), 'Supply exact pilot mailbox UPNs; All is prohibited')
    for v in p['sharePointLocations']:
        require(isinstance(v, str) and re.fullmatch(r'https://[a-z0-9-]+\.sharepoint\.com/sites/[A-Za-z0-9_-]+', v), 'Supply exact SharePoint site URLs; All is prohibited')
    return cfg


def ids(s):
    group = '/subscriptions/{}/resourceGroups/{}'.format(s['subscriptionId'], s['resourceGroup'])
    return group, group + '/providers/Microsoft.OperationalInsights/workspaces/' + s['workspaceName']


def matches(actual, desired):
    if isinstance(desired, dict):
        return isinstance(actual, dict) and all(k in actual and matches(actual[k], v) for k, v in desired.items())
    if isinstance(desired, list):
        return actual == desired
    return actual == desired


def resources(cfg, admin, stage):
    if stage in ('activate', 'deactivate'):
        selected = []
        for item in resources(cfg, admin, 'content'):
            props = item['body']['properties']
            if '/alertRules/' in item['id']:
                props['enabled'] = stage == 'activate'
            elif '/automationRules/' in item['id']:
                props['triggeringLogic']['isEnabled'] = stage == 'activate'
            else:
                continue
            item['label'] = stage + ': ' + props['displayName']
            selected.append(item)
        return selected
    s = admin['sentinel']
    group, workspace = ids(s)
    si = workspace + '/providers/Microsoft.SecurityInsights/'
    output = []

    def add(resource_id, version, body, label):
        output.append({'id': resource_id, 'apiVersion': version, 'body': body, 'label': label})

    def stable_id(label):
        return str(uuid5(NAMESPACE_URL, workspace.lower() + '/a365-pilot/' + label))

    if stage == 'foundation':
        add(workspace, '2022-10-01', {'location': s['location'], 'tags': {'a365-pilot': cfg['tenant']['environment']}, 'properties': {'sku': {'name': 'PerGB2018'}, 'retentionInDays': s['retentionInDays'], 'workspaceCapping': {'dailyQuotaGb': s['dailyQuotaGb']}}}, 'Log Analytics workspace (billable)')
        add(si + 'onboardingStates/default', API, {'properties': {'customerManagedKey': False}}, 'Enable Sentinel (billable)')
    elif stage == 'connectors':
        if s['connectors']['defenderXdr']:
            add(si + 'dataConnectors/' + stable_id('xdr'), PREVIEW, {'kind': 'MicrosoftThreatProtection', 'properties': {'tenantId': cfg['tenant']['id'], 'dataTypes': {'incidents': {'state': 'Enabled'}, 'alerts': {'state': 'Enabled'}}}}, 'Defender XDR to Sentinel; preview ARM API')
        if s['connectors']['office365']:
            add(si + 'dataConnectors/' + stable_id('office'), API, {'kind': 'Office365', 'properties': {'tenantId': cfg['tenant']['id'], 'dataTypes': {k: {'state': 'Enabled'} for k in ('exchange', 'sharePoint', 'teams')}}}, 'Microsoft 365 audit to Sentinel; tenant-wide ingestion')
    elif stage == 'content':
        queries = {}
        for key in ('pilot-dlp', 'agent-alerts', 'telemetry-health'):
            queries[key] = (ROOT / 'sentinel/queries' / (key + '.kql')).read_text().replace('__PILOT_USERS__', json.dumps(s['pilotUserIds'])).replace('__AGENT_IDS__', json.dumps(s['agentObjectIds']))
            add(workspace + '/savedSearches/A365-PILOT-' + key, '2020-08-01', {'properties': {'category': 'Hunting Queries', 'displayName': 'A365-PILOT-' + key, 'query': queries[key], 'version': 1, 'tags': [{'name': 'hidden-title', 'value': 'A365 pilot'}]}}, 'Hunting: ' + key)
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(['AgentObjectId'])
        writer.writerows([[v] for v in sorted(s['agentObjectIds'])])
        add(si + 'watchlists/A365-PILOT-agents', API, {'properties': {'displayName': 'A365-PILOT-agents', 'provider': 'A365 pilot kit', 'source': 'approved-agents.csv', 'sourceType': 'Local', 'contentType': 'text/csv', 'itemsSearchKey': 'AgentObjectId', 'rawContent': csv_file.getvalue(), 'description': 'Approved individual identities; no prompt or response content'}}, 'Approved agent watchlist')
        rule_ids = []
        for key in ('pilot-dlp', 'agent-alerts'):
            rule_id = si + 'alertRules/' + stable_id(key)
            rule_ids.append(rule_id)
            add(rule_id, API, {'kind': 'Scheduled', 'properties': {'displayName': 'A365-PILOT-' + key, 'description': 'Pilot triage signal; validate entity attribution and tune before separately enabling.', 'enabled': False, 'severity': 'Informational', 'query': queries[key], 'queryFrequency': 'PT1H', 'queryPeriod': 'PT1H', 'triggerOperator': 'GreaterThan', 'triggerThreshold': 0, 'suppressionEnabled': False, 'suppressionDuration': 'PT1H', 'tactics': [], 'incidentConfiguration': {'createIncident': True, 'groupingConfiguration': {'enabled': False, 'reopenClosedIncident': False, 'lookbackDuration': 'PT1H', 'matchingMethod': 'AllEntities'}}}}, 'Disabled analytics: ' + key)
        workbook = {'version': 'Notebook/1.0', 'items': [ {'type': 1, 'content': {'json': '# A365 pilot operations\nCounts and identifiers only. Empty results do not prove protection. Defender AgentsInfo is not a Log Analytics table.'}, 'name': 'intro'}, *[{'type': 3, 'content': {'version': 'KqlItem/1.0', 'query': query, 'size': 0, 'title': name, 'queryType': 0, 'resourceType': 'microsoft.operationalinsights/workspaces', 'crossComponentResources': [workspace], 'visualization': 'table'}, 'name': name} for name, query in queries.items()]], 'isLocked': False, 'fallbackResourceIds': [workspace]}
        add(group + '/providers/Microsoft.Insights/workbooks/' + stable_id('workbook'), '2022-04-01', {'location': s['location'], 'kind': 'shared', 'properties': {'displayName': 'A365-PILOT-operations', 'category': 'sentinel', 'sourceId': workspace, 'serializedData': json.dumps(workbook)}}, 'SOC workbook')
        add(si + 'automationRules/' + stable_id('triage'), API, {'properties': {'displayName': 'A365-PILOT-human-triage', 'order': 1000, 'triggeringLogic': {'isEnabled': False, 'triggersOn': 'Incidents', 'triggersWhen': 'Created', 'conditions': [{'conditionType': 'Property', 'conditionProperties': {'propertyName': 'IncidentRelatedAnalyticRuleIds', 'operator': 'Contains', 'propertyValues': rule_ids}}]}, 'actions': [{'order': 1, 'actionType': 'AddIncidentTask', 'actionConfiguration': {'title': 'Verify A365 pilot evidence', 'description': 'Confirm tenant, agent identity, event time and policy scope. Follow playbooks/sentinel-triage.md. Obtain separate approval for containment; never export interaction content.'}}]}}, 'Disabled incident task automation; no containment')
    else:
        raise SafetyError('Unknown stage')
    return output


class ArmError(SafetyError):
    def __init__(self, status):
        self.status = status
        super().__init__('Azure HTTP {}; response body withheld'.format(status))


class Arm(Graph):
    token_resource = ARM

    def bind(self, subscription):
        self.subscription = subscription
        self.verified = False
        observed = self.request('GET', '/subscriptions/' + subscription + '?api-version=2022-12-01')
        require(observed.get('tenantId', '').lower() == self.tenant['id'].lower(), 'Subscription directory differs from selected tenant, or cannot be verified')
        require(observed.get('state') == 'Enabled', 'Subscription must be Enabled')
        self.verified = True

    def url(self, path):
        url = path if path.startswith('https://') else ARM + path
        p = urlparse(url)
        base = '/subscriptions/' + self.subscription
        require(p.scheme == 'https' and p.netloc == 'management.azure.com' and not p.fragment and not p.username, 'Untrusted ARM URL')
        require((p.path == base or p.path.startswith(base + '/')) and not any(x in p.path for x in ('..', '\\', '%')), 'ARM request escaped selected subscription')
        require(p.query.startswith('api-version=') and '&' not in p.query, 'Only fixed ARM API version queries allowed')
        return url

    def request(self, method, path, body=None):
        url = self.url(path)
        require(self.verified or (method == 'GET' and path == '/subscriptions/' + self.subscription + '?api-version=2022-12-01'), 'Verify subscription first')
        require(method in ('GET', 'PUT'), 'Only GET and approved PUT supported')
        if method != 'GET':
            require(self.permit == (method, url, body), 'No exact approved ARM request')
            self.permit = None
        req = Request(url, data=json.dumps(body).encode() if body is not None else None, method=method, headers={'Authorization': 'Bearer ' + self._token, 'Content-Type': 'application/json'})
        try:
            with self.opener.open(req, timeout=60) as response:
                data = json.loads(response.read() or b'{}')
                require(isinstance(data, dict), 'Invalid Azure response')
                return data
        except HTTPError as exc:
            raise ArmError(exc.code) from None
        except (URLError, TimeoutError, ValueError):
            raise SafetyError('Azure transport failed; mutation outcome may be unknown. Inspect evidence before replanning.') from None

    def get(self, item):
        try:
            observed = self.request('GET', path_for(item))
            if '/watchlists/' in item['id'] and observed.get('properties', {}).get('uploadStatus') == 'Complete':
                page = self.request('GET', item['id'] + '/watchlistItems?api-version=' + API)
                require(isinstance(page.get('value'), list) and not page.get('nextLink'), 'Cannot verify all watchlist items')
                rows = [v.get('properties', {}).get('itemsKeyValue', {}) for v in page['value']]
                require(all(set(row) == {'AgentObjectId'} for row in rows), 'Unexpected watchlist columns; refusing reuse')
                stream = io.StringIO()
                writer = csv.writer(stream)
                writer.writerow(['AgentObjectId'])
                writer.writerows([[row['AgentObjectId']] for row in sorted(rows, key=lambda r: r['AgentObjectId'])])
                observed['properties']['rawContent'] = stream.getvalue()
            return observed
        except ArmError as exc:
            if exc.status == 404:
                return None
            raise


def path_for(item):
    return item['id'] + '?api-version=' + item['apiVersion']


def ready(resource):
    return resource is not None and resource.get('properties', {}).get('provisioningState', 'Succeeded') == 'Succeeded'


def comparable(item, observed):
    return ready(observed) and matches(observed, item['body'])


def preflight(arm, cfg, admin, stage):
    group, workspace = ids(admin['sentinel'])
    arm.request('GET', group + '?api-version=2022-09-01')
    if stage != 'foundation':
        observed = arm.request('GET', workspace + '?api-version=2022-10-01')
        require(ready(observed), 'Workspace provisioning is not complete')
        require(observed.get('location') == admin['sentinel']['location'], 'Workspace region mismatch')
        arm.request('GET', workspace + '/providers/Microsoft.SecurityInsights/onboardingStates/default?api-version=' + API)
    if stage == 'connectors':
        page = arm.request('GET', workspace + '/providers/Microsoft.SecurityInsights/dataConnectors?api-version=' + PREVIEW)
        require(isinstance(page.get('value'), list) and not page.get('nextLink'), 'Cannot verify complete existing connector inventory')
        desired = {v['body']['kind']: v['id'].lower() for v in resources(cfg, admin, stage)}
        for connector in page['value']:
            if connector.get('kind') in desired:
                require(connector.get('id', '').lower() == desired[connector['kind']], 'Existing connector of this kind has a different ID; do not create duplicate tenant ingestion. Review in portal.')
    if stage in ('content', 'activate'):
        for table, columns in {'SecurityAlert': {'TimeGenerated', 'Entities', 'SystemAlertId', 'AlertSeverity', 'ProviderName'}, 'OfficeActivity': {'TimeGenerated', 'UserId', 'Operation', 'OfficeWorkload'}}.items():
            observed = arm.request('GET', workspace + '/tables/' + table + '?api-version=2022-10-01')
            names = {c['name'] for c in observed.get('properties', {}).get('schema', {}).get('columns', [])}
            names |= {c['name'] for c in observed.get('properties', {}).get('schema', {}).get('standardColumns', [])}
            require(columns <= names, 'Required table/schema unavailable: ' + table + '. Ingest data before planning content.')


def make_plan(arm, cfg, admin, stage):
    preflight(arm, cfg, admin, stage)
    changes = []
    for item in resources(cfg, admin, stage):
        observed = arm.get(item)
        # Existing foundation is consumed, never overwritten or retagged.
        if stage in ('activate', 'deactivate'):
            require(ready(observed), 'Install the pack before changing rule state')
            alternate = copy.deepcopy(item['body'])
            if '/alertRules/' in item['id']:
                alternate['properties']['enabled'] = not item['body']['properties']['enabled']
            else:
                alternate['properties']['triggeringLogic']['isEnabled'] = not item['body']['properties']['triggeringLogic']['isEnabled']
            require(matches(observed, item['body']) or matches(observed, alternate), 'Installed rule differs from this pack; refusing state change')
            action = 'reuse' if matches(observed, item['body']) else 'update'
            # Preserve all existing properties when changing only the enabled state.
            body = {k: copy.deepcopy(observed[k]) for k in ('kind', 'properties') if k in observed}
            if '/alertRules/' in item['id']:
                body['properties']['enabled'] = stage == 'activate'
            else:
                body['properties']['triggeringLogic']['isEnabled'] = stage == 'activate'
            item['body'] = body
        elif stage == 'foundation' and observed is not None:
            require(ready(observed), 'Existing resource still provisioning; wait and replan')
            if '/workspaces/' in item['id'] and '/providers/Microsoft.SecurityInsights/' not in item['id']:
                require(observed.get('location') == admin['sentinel']['location'], 'Existing workspace region mismatch')
            action = 'reuse'
        elif observed is None:
            action = 'create'
        else:
            require(comparable(item, observed), 'Existing resource differs or cannot be compared; refusing overwrite: ' + item['label'])
            action = 'reuse'
        before = None if observed is None else {k: observed.get(k) for k in item['body']}
        changes.append(dict(item, action=action, beforeDigest=digest(observed), before=before))
    return {'tenant': cfg['tenant'], 'configDigest': digest(cfg), 'adminDigest': digest(admin), 'stage': stage, 'changes': changes,
            'requiredRoles': ['Organization.Read.All for tenant verification', 'Azure Reader for plan; resource-specific write RBAC for apply', 'Microsoft Sentinel Contributor; Log Analytics Contributor; workbook write access', 'Connector-specific Entra security roles and product licenses; see docs/admin-deployment.md'],
            'impact': 'Foundation enables billable Azure services. Connectors ingest tenant-wide security/audit metadata; pilot lists do not restrict ingestion. Content creates disabled rules and automation. Activate enables two incident-generating rules and incident task creation; deactivate disables them, stopping their detections/task creation. Activation approval must follow query and benign-event validation. No consent, licenses, role grants or production changes.',
            'rollback': 'No automatic deletion. Preserve resource IDs and evidence; disable new rules/connectors only under a separate reviewed change. Never delete a shared workspace to roll back this pack.',
            'limitations': 'Configuration deployment is not proof of ingestion, agent coverage or successful runtime detection. Agent 365 data lake onboarding and Defender Security for AI portal steps are separate.'}


def envelope(plan):
    doc = {'schemaVersion': 1, 'origin': 'live-read-only-sentinel', 'createdAt': now(), 'plan': plan}
    return dict(doc, approvalDigest=digest(doc))


def apply(arm, cfg, admin, doc, execute=False, approval=None, evidence=None):
    unsigned = {k: v for k, v in doc.items() if k != 'approvalDigest'}
    require(doc.get('schemaVersion') == 1 and doc.get('origin') == 'live-read-only-sentinel' and doc.get('approvalDigest') == digest(unsigned), 'Invalid or modified Sentinel plan')
    age = (datetime.now(timezone.utc) - timestamp(doc['createdAt'])).total_seconds()
    require(0 <= age <= 1800, 'Plan expired; replan and obtain new approval')
    plan = doc['plan']
    require(plan == make_plan(arm, cfg, admin, plan['stage']), 'Configuration or remote state changed; replan and obtain new approval')
    if not execute:
        return {'status': 'skipped', 'evidence': 'Dry-run; fresh state matches plan; no mutation issued'}
    require(approval == doc['approvalDigest'], 'Exact human-approved digest required')
    require(cfg['profile'] != 'read-only', 'Read-only profile prohibits deployment')
    require(evidence, 'Supply a new --evidence-dir')
    directory = Path(evidence)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    write_json(directory / 'intent.json', doc)
    outcomes = []
    try:
        for index, item in enumerate(plan['changes']):
            # Check each precondition again immediately before its write.
            require(digest(arm.get(item)) == item['beforeDigest'], 'Resource drift detected; stop and replan')
            if item['action'] == 'reuse':
                outcomes.append({'id': item['id'], 'status': 'skipped', 'evidence': 'Existing resource reused; no PUT'})
                continue
            write_json(directory / ('{:02d}-intent.json'.format(index)), item)
            arm.authorize('PUT', path_for(item), item['body'])
            arm.request('PUT', path_for(item), item['body'])
            observed = arm.get(item)
            # A watchlist receipt proves resource existence, not uploaded item availability.
            ok = comparable(item, observed)
            outcome = {'id': item['id'], 'status': 'applied' if ok else 'not verifiable', 'evidence': 'Configuration readback matches' if ok else 'Accepted write; asynchronous provisioning or upload requires separate verification', 'runtimeEffectVerified': False}
            outcomes.append(outcome)
            write_json(directory / ('{:02d}-receipt.json'.format(index)), outcome)
            if not ok and '/watchlists/' not in item['id']:
                break
    except (SafetyError, OSError):
        outcomes.append({'status': 'not verifiable', 'evidence': 'Stopped after drift, write or readback failure; partial/unknown outcome. Inspect intent and resource state before any retry.'})
    result = {'status': 'not verifiable' if any(x['status'] == 'not verifiable' for x in outcomes) else 'applied', 'operations': outcomes, 'runtimeEffectVerified': False}
    write_json(directory / 'outcome.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description='Staged Sentinel admin deployment; offline build is the default safe starting point')
    parser.add_argument('command', choices=('build', 'plan', 'apply', 'verify'))
    parser.add_argument('--config', default=str(ROOT / 'config/pilot.example.json'))
    parser.add_argument('--admin-config', default=str(ROOT / 'config/admin.example.json'))
    parser.add_argument('--stage', choices=STAGES, default='foundation')
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--tenant-id')
    parser.add_argument('--environment')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--plan-file', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--approve')
    parser.add_argument('--evidence-dir', type=Path)
    args = parser.parse_args()
    try:
        require(not args.execute or args.command == 'apply', 'Only apply accepts --execute')
        require(not args.approve or args.execute, '--approve requires --execute')
        require((args.command == 'build') != args.live, 'Build must be offline; plan/apply/verify require --live')
        cfg = check_config(read_json(args.config), live=args.live)
        admin = check_admin(read_json(args.admin_config), live=args.live)
        if args.command == 'build':
            result = {'origin': 'offline-not-deployable', 'stages': {s: resources(cfg, admin, s) for s in STAGES}}
        else:
            require(args.tenant_id and args.tenant_id.lower() == cfg['tenant']['id'].lower() and args.environment == cfg['tenant']['environment'], 'Explicit tenant/environment selection required')
            require(args.command != 'plan' or args.out, 'Plan requires a new --out file')
            print(json.dumps({'selectedTenant': cfg['tenant'], 'subscriptionId': admin['sentinel']['subscriptionId'], 'mode': 'approved writes requested' if args.execute else 'read-only', 'requirements': 'Review roles, licensing, costs and scope in docs/admin-deployment.md. No login or consent is performed.'}), flush=True)
            doc = read_json(args.plan_file) if args.command == 'apply' and args.plan_file else None
            require(args.command != 'apply' or doc, 'Apply requires --plan-file')
            if doc:
                print(json.dumps(doc, indent=2), flush=True)
            graph = Graph.from_cli(cfg['tenant'])
            graph.verify()
            arm = Arm.from_cli(cfg['tenant'])
            arm.bind(admin['sentinel']['subscriptionId'])
            if args.command == 'plan':
                result = envelope(make_plan(arm, cfg, admin, args.stage))
            elif args.command == 'apply':
                result = apply(arm, cfg, admin, doc, args.execute, args.approve, args.evidence_dir)
            else:
                preflight(arm, cfg, admin, args.stage)
                operations = []
                for item in resources(cfg, admin, args.stage):
                    observed = arm.get(item)
                    operations.append({'id': item['id'], 'status': 'skipped' if comparable(item, observed) else 'not verifiable', 'evidence': 'Desired configuration matches' if comparable(item, observed) else 'Missing, different, asynchronous, or watchlist contents need portal/query verification'})
                result = {'status': 'not verifiable' if any(x['status'] == 'not verifiable' for x in operations) else 'skipped', 'operations': operations, 'runtimeEffectVerified': False}
        if args.out:
            write_json(args.out, result)
        print(json.dumps(result, indent=2))
        return 2 if result.get('status') == 'not verifiable' else 0
    except (SafetyError, OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc) if isinstance(exc, SafetyError) else 'Local input/output validation failed; no automatic retry', file=sys.stderr)
        return 1
