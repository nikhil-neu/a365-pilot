"""Readiness and narrow, approval-bound pilot changes."""
from datetime import datetime, timezone
from urllib.parse import quote

from .core import ROOT, SafetyError, digest, guid, now, require, result, timestamp, write_json
from .graph import CA, CATALOG, HUNT

CA_FIELDS = ('displayName', 'state', 'conditions', 'grantControls')


def ca_payload(cfg):
    ca = cfg['conditionalAccess']
    return {'displayName': ca['displayName'], 'state': ca['state'],
            'conditions': {'clientAppTypes': ['all'], 'applications': {'includeApplications': ca['resourceAppIds']},
                           'clientApplications': {'includeAgentIdServicePrincipals': ca['agentObjectIds']},
                           'agentIdRiskLevels': 'high'},
            'grantControls': {'operator': 'OR', 'builtInControls': ['block']}}


def is_agent(package):
    return bool({str(x).lower() for x in package.get('elementTypes', [])} & {'bot', 'bots', 'declarativeagent', 'customengineagent'}) or 'copilot' in {str(x).lower() for x in package.get('supportedHosts', [])}


def package_path(package_id, beta=False):
    require(isinstance(package_id, str) and package_id and len(package_id) <= 512, 'Invalid package ID')
    return (CATALOG.replace('/v1.0/', '/beta/') if beta else CATALOG) + '/' + quote(package_id, safe='')


def package_summary(p):
    # Never persist elementDetails definitions, descriptions, instructions or raw manifests.
    return {k: p.get(k) for k in ('id', 'displayName', 'platform', 'version', 'appId', 'isBlocked', 'availableTo', 'deployedTo', 'elementTypes', 'supportedHosts')}


def probe(name, fn, maturity='stable'):
    try:
        evidence = fn()
        if evidence == []:
            return result(name, 'not verifiable', {'rows': [], 'reason': 'No records returned; coverage or prerequisite state not established'}, maturity=maturity)
        return result(name, 'skipped', evidence, observed='read succeeded; inspect evidence, not a compliance assertion', maturity=maturity)
    except SafetyError as exc:
        return result(name, 'not verifiable', str(exc), maturity=maturity)


def hunt(graph, filename):
    query = (ROOT / 'queries' / filename).read_text()
    data = graph.request('POST', HUNT, {'Query': query})
    require(isinstance(data.get('results'), list), 'Hunting result missing results array')
    return data['results']


def assess(graph, cfg):
    operations = []
    operations.append(probe('license-inventory', lambda: graph.collection('/v1.0/subscribedSkus?$select=skuId,skuPartNumber,capabilityStatus,consumedUnits,servicePlans')))
    operations.append(result('license-eligibility', 'manual admin step required', 'Confirm Agent 365 license assignment, underlying entitlements, terms acceptance, Entra P2 for risk policies and applicable Defender/Purview licenses. SKU presence alone is not proof.', rollback='No automatic licensing or consent changes'))
    operations.append(probe('active-directory-roles', lambda: graph.collection('/v1.0/me/transitiveMemberOf/microsoft.graph.directoryRole?$select=id,displayName,roleTemplateId')))
    operations.append(result('effective-product-roles', 'manual admin step required', 'Role list is partial: confirm active PIM assignments, scoped Entra roles, AI Administrator, Defender unified RBAC, Purview role groups, Power Platform and Azure roles per docs/permissions.md.'))
    operations.append(probe('conditional-access', lambda: graph.collection(CA), 'beta'))
    operations.append(probe('agent-risk', lambda: graph.collection('/beta/identityProtection/riskyAgents'), 'beta / preview risk signals'))
    operations.append(probe('registry', lambda: [package_summary(p) for p in graph.collection(CATALOG)], 'preview feature / v1.0 read API'))
    operations.append(probe('defender-agent-inventory', lambda: hunt(graph, 'inventory.kql'), 'preview AgentsInfo'))
    operations.append(probe('telemetry-freshness', lambda: hunt(graph, 'telemetry-health.kql'), 'stable CloudAppEvents / Agent 365 observability'))
    for name, detail in {
        'defender-connectors': 'Follow docs/connectors.md: record connector health, selected workloads, collection status and last event. Empty queries do not prove connector health.',
        'purview-auditing-policies': 'Run scripts/Test-Purview.ps1 with explicit tenant selection. For approved audit enablement or new DLP simulation policies use scripts/Set-PurviewPilot.ps1; see docs/admin-deployment.md.',
        'power-platform': 'Verify selected environment ID, environment access, Copilot Studio DLP and real-time protection in admin center; see docs/connectors.md.',
        'foundry-azure': 'Verify explicit subscription/directory/project, RBAC, Agent 365 registration and observability in Foundry; no ARM changes are automatic.',
        'custom-observability': 'No agent implementation detected in this greenfield kit. Instrumentation requires framework/authentication discovery; see docs/telemetry.md.'
    }.items():
        operations.append(result(name, 'manual admin step required', detail))
    return operations


def inventory_snapshot(graph, cfg):
    packages = graph.collection(CATALOG)
    agents = []
    for p in packages:
        if not is_agent(p):
            continue
        record = dict(packageId=p['id'], name=p.get('displayName'), platform=p.get('platform'), version=p.get('version'),
                           observabilityAppId=p.get('appId'), owners=None, permissions=None, tools=None, controls=None,
                           agentObjectId=None, blueprintId=None, risk=None, lastSeen=None)
        enrichment = enrich(graph, cfg, p)
        for key in ('owners', 'agentObjectId', 'blueprintId', 'risk'):
            if key in enrichment:
                record[key] = enrichment[key]
        record['enrichmentEvidence'] = enrichment
        agents.append(record)
    return dict(schemaVersion=1, tenantId=cfg['tenant']['id'], environment=cfg['tenant']['environment'], capturedAt=now(),
                source=CATALOG, complete=False, agents=agents,
                coverage='All catalog pages read; agent detection based on host/element metadata. Cross-platform coverage and enrichment not established.')


def enrich(graph, cfg, package):
    """Use explicit mapping only after verifying its appId against the live package."""
    approved = next((a for a in cfg['approvedInventory'] if a['packageId'] == package['id']), None)
    evidence = {'source': 'live Graph reads', 'unknown': ['effective permissions including inherited blueprint grants', 'declared tools', 'control coverage', 'invocation freshness']}
    if not approved or not guid(approved.get('agentObjectId')) or not package.get('appId'):
        evidence['unknown'] += ['identity mapping', 'owners', 'risk']
        return evidence
    identity_path = '/beta/servicePrincipals/' + approved['agentObjectId'] + '/microsoft.graph.agentIdentity'
    try:
        identity = graph.request('GET', identity_path)
        require(identity.get('appId') == package['appId'], 'Package/identity appId mismatch; mapping not trusted')
        evidence.update(agentObjectId=identity['id'], blueprintId=identity.get('agentIdentityBlueprintId'))
        owners = graph.collection(identity_path + '/owners?$select=id')
        evidence['owners'] = [x['id'] for x in owners]
    except SafetyError as exc:
        evidence['identityError'] = str(exc)
        return evidence
    # Direct grants are useful evidence but are not a complete effective permission boundary.
    evidence['directApplicationGrants'] = probe('direct-app-grants', lambda: graph.collection('/v1.0/servicePrincipals/' + identity['id'] + '/appRoleAssignments?$select=id,appRoleId,resourceId'))
    evidence['directDelegatedGrants'] = probe('direct-delegated-grants', lambda: graph.collection('/v1.0/servicePrincipals/' + identity['id'] + '/oauth2PermissionGrants?$select=id,resourceId,scope,consentType'))
    try:
        risks = graph.collection('/beta/identityProtection/riskyAgents')
        matching = [x for x in risks if x.get('id') == identity['id']]
        if len(matching) == 1:
            evidence['risk'] = matching[0].get('riskLevel')
        else:
            evidence['unknown'].append('risk: no unique riskyAgent record; absence is not proof of no risk')
    except SafetyError as exc:
        evidence['riskError'] = str(exc)
    return evidence


def validate_live(graph, cfg):
    operations = []
    try:
        policies = [p for p in graph.collection(CA) if p.get('displayName') == cfg['conditionalAccess']['displayName']]
        wanted = ca_payload(cfg)
        matches = len(policies) == 1 and ca_matches(wanted, policies[0])
        operations.append(result('verify-ca-baseline', 'skipped' if matches else 'failed', {'expected': wanted, 'actual': policies}, observed='matches report-only baseline' if matches else 'missing, duplicate or drifted'))
    except SafetyError as exc:
        operations.append(result('verify-ca-baseline', 'not verifiable', str(exc)))
    operations.extend([probe('verify-defender-inventory', lambda: hunt(graph, 'inventory.kql'), 'preview'),
                       probe('verify-telemetry-health', lambda: hunt(graph, 'telemetry-health.kql'))])
    operations.append(result('verify-invocation-across-surfaces', 'manual admin step required', 'Use docs/validation.md with one benign invocation, exact appId, conversation ID, UTC window and evidence from all three surfaces. Inventory presence is not invocation proof.'))
    return operations


def subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and sorted(expected) == sorted(actual)
    return expected == actual


def policy_view(p):
    return {k: p.get(k) for k in CA_FIELDS}


def ca_matches(expected, actual):
    metadata = ('id', 'createdDateTime', 'modifiedDateTime', 'templateId', '@odata.context', '@odata.type')
    normalized = {k: v for k, v in actual.items() if k not in metadata and v is not None}
    return strip_empty(normalized) == strip_empty(expected)


def build_plan(graph, cfg, intent, target=None):
    require(intent in ('ca-deploy', 'ca-promote', 'ca-disable', 'registry-block', 'registry-unblock'), 'Unsupported operation')
    require(cfg['profile'] != 'read-only', 'read-only profile prohibits mutation plans')
    plan = dict(schemaVersion=1, tenant=cfg['tenant'], configDigest=digest(cfg), intent=intent, target=target, maturity='beta',
                requiredRoles=[], requiredPermissions=[], licensing=[], precondition=None, request=None, desired=None)
    if intent.startswith('ca-'):
        require(target is None, 'CA target comes only from explicit configured object IDs')
        for field in ('agentObjectIds', 'resourceAppIds'):
            require(all(guid(value) for value in cfg['conditionalAccess'][field]), 'Replace all CA target placeholders before live CA planning')
        # Typed endpoint proves each target is an individual agent identity, not a blueprint principal.
        identities = []
        for agent_id in cfg['conditionalAccess']['agentObjectIds']:
            obj = graph.request('GET', '/beta/servicePrincipals/' + agent_id + '/microsoft.graph.agentIdentity')
            require(obj.get('id', '').lower() == agent_id.lower(), 'Agent identity lookup mismatch')
            identities.append({'id': obj['id'], 'displayName': obj.get('displayName'), 'agentIdentityBlueprintId': obj.get('agentIdentityBlueprintId')})
        policies = [p for p in graph.collection(CA) if p.get('displayName') == cfg['conditionalAccess']['displayName']]
        require(len(policies) <= 1, 'Duplicate policy names; manual reconciliation required')
        expected = ca_payload(cfg)
        plan.update(requiredRoles=['Conditional Access Administrator'], requiredPermissions=['Policy.Read.All', 'Policy.ReadWrite.ConditionalAccess', 'AgentIdentity.Read.All'],
                    licensing=['Agent 365 plus Entra ID P2 (or qualifying E7/E5 entitlement); confirm assignment'], identities=identities,
                    impact='Only the listed autonomous agent identity object IDs requesting tokens for the listed resource application IDs at high agent risk. No delegated user, agent-user or blueprint token coverage.',
                    rollback='Create ca-disable plan to disable this policy; review and approve its new digest. Promotion can be reversed in Entra to report-only after approval.')
        if not policies:
            require(intent == 'ca-deploy', 'Policy does not exist')
            plan.update(request={'method': 'POST', 'path': CA, 'body': expected}, desired=expected)
        else:
            existing = policies[0]
            require(guid(existing.get('id')), 'Invalid CA policy ID')
            # Reject changes in scope, exclusions, sessions or unknown nonempty settings.
            desired_scope = dict(expected, state=existing['state'])
            require(ca_matches(desired_scope, existing), 'Policy scope drift; do not overwrite unrelated policy settings')
            state = {'ca-deploy': cfg['conditionalAccess']['state'], 'ca-promote': 'enabled', 'ca-disable': 'disabled'}[intent]
            require(intent != 'ca-deploy' or existing['state'] == state, 'Existing state differs; use an explicit state-change operation')
            plan.update(precondition=policy_view(existing), policyId=existing['id'], desired=dict(expected, state=state))
            if existing['state'] != state:
                plan['request'] = {'method': 'PATCH', 'path': CA + '/' + existing['id'], 'body': {'state': state}}
        if intent == 'ca-promote':
            plan['impact'] += ' ENFORCEMENT: high-risk matching token requests will be denied. Requires reviewed report-only sign-ins and owner recovery approval.'
    else:
        require(target, 'Name one exact registry package ID')
        package = graph.request('GET', package_path(target))
        require(package.get('id') == target and is_agent(package), 'Target is not a verified agent package')
        require(type(package.get('isBlocked')) is bool, 'Registry block state unavailable')
        blocked = intent == 'registry-block'
        approved = next((a for a in cfg['approvedInventory'] if a['packageId'] == target), None)
        plan.update(precondition=package_summary(package), desired={'isBlocked': blocked},
                    enrichment={'observed': package_summary(package), 'liveIdentity': enrich(graph, cfg, package), 'approvedInventoryReference': approved,
                                'unknown': ['current owners', 'effective permissions', 'tools', 'risk', 'identity/blueprint mapping unless separately verified'],
                                'warning': 'Approved inventory is desired state, not live enrichment. Review Defender agent detail and Entra identity before approval.'},
                    requiredRoles=['AI Administrator'], requiredPermissions=['CopilotPackages.ReadWrite.All (delegated only)'], licensing=['Microsoft Agent 365'],
                    impact='Changes availability of this exact package for every assigned user and channel in the tenant. Does not stop external infrastructure or guarantee token revocation. Shared package may represent multiple deployments.',
                    rollback='Plan registry-{} for this exact package, then approve and verify. Restore only the recorded prior state.'.format('unblock' if blocked else 'block'))
        if package['isBlocked'] != blocked:
            plan['request'] = {'method': 'POST', 'path': package_path(target, beta=True) + ('/block' if blocked else '/unblock'), 'body': None}
    return plan


def strip_empty(value):
    if isinstance(value, dict):
        return {k: strip_empty(v) for k, v in value.items() if v not in (None, [], {})}
    return value


def envelope(plan):
    doc = {'createdAt': now(), 'origin': 'live-read-only', 'plan': plan}
    doc['approvalDigest'] = digest(doc)
    return doc


def apply_plan(graph, cfg, document, approval, evidence_dir, execute=False):
    require(document.get('origin') == 'live-read-only', 'Offline plans cannot be applied')
    unsigned = {k: v for k, v in document.items() if k != 'approvalDigest'}
    require(document.get('approvalDigest') == digest(unsigned), 'Plan integrity failure')
    age = (datetime.now(timezone.utc) - timestamp(document['createdAt'])).total_seconds()
    require(0 <= age <= 1800, 'Plan expired or future-dated; create and review a fresh plan')
    plan = document['plan']
    require(plan['tenant'] == cfg['tenant'] and plan['configDigest'] == digest(cfg), 'Plan tenant/environment/config mismatch')
    fresh = build_plan(graph, cfg, plan['intent'], plan['target'])
    require(fresh == plan, 'Live state changed since review; generate a new plan')
    if not execute:
        return result(plan['intent'], 'skipped', {'dryRun': True, 'plan': plan}, impact=plan['impact'], rollback=plan['rollback'])
    require(approval == document['approvalDigest'], 'Explicit approval digest required')
    if plan['request'] is None:
        return result(plan['intent'], 'skipped', 'Already in desired state; no write issued', impact=plan['impact'], rollback=plan['rollback'])
    # Durable intent and prior state must be saved before issuing any mutation.
    write_json(evidence_dir / 'intent.json', document)
    request = plan['request']
    graph.authorize(request['method'], request['path'], request['body'])
    accepted = False
    try:
        response = graph.request(request['method'], request['path'], request['body'])
        accepted = True
        if plan['intent'].startswith('ca-'):
            policy_id = plan.get('policyId') or response.get('id')
            require(guid(policy_id), 'Write accepted but policy ID missing; find the exact named policy before retry')
            write_json(evidence_dir / 'receipt.json', {'policyId': policy_id, 'capturedAt': now()})
            current = graph.request('GET', CA + '/' + policy_id)
            verified = ca_matches(plan['desired'], current)
            observed = policy_view(current)
        else:
            current = graph.request('GET', package_path(plan['target']))
            verified = current.get('id') == plan['target'] and subset(plan['desired'], current)
            observed = package_summary(current)
        outcome = result(plan['intent'], 'applied' if verified else 'not verifiable', {'writeAccepted': True, 'observed': observed, 'configurationVerified': verified, 'runtimeEffectVerified': False}, impact=plan['impact'], rollback=plan['rollback'])
    except SafetyError as exc:
        outcome = result(plan['intent'], 'not verifiable', {'writeAccepted': accepted, 'error': str(exc), 'instruction': 'Inspect current state before retry. Intent contains prior state and recovery instructions.'}, impact=plan['impact'], rollback=plan['rollback'])
    write_json(evidence_dir / 'outcome.json', outcome)
    return outcome
