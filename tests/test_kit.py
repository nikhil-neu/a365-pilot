import copy
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from a365.core import ROOT, SafetyError, check_config, digest, now, read_json, report, result, save_report, write_json
from a365.graph import ApiError, CA, CATALOG, Graph, HUNT, ORG, ORIGIN
from a365.operations import apply_plan, assess, build_plan, ca_payload, envelope, package_summary, inventory_snapshot, validate_live
from a365.audit import audit_inventory
from a365.cli import main

TENANT = '11111111-1111-4111-8111-111111111111'
AGENT = '22222222-2222-4222-8222-222222222222'
RESOURCE = '33333333-3333-4333-8333-333333333333'
POLICY = '44444444-4444-4444-8444-444444444444'


def config():
    c = read_json(ROOT / 'config/pilot.example.json')
    c['tenant'].update(id=TENANT, displayName='Mock isolated tenant')
    c['conditionalAccess'].update(agentObjectIds=[AGENT], resourceAppIds=[RESOURCE])
    c['purview']['policyNames'] = ['Mock pilot policy']
    return c


class Response:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.body).encode() if self.body is not None else b''


class QueueOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def open(self, req, timeout):
        self.calls.append(req)
        if not self.responses:
            raise AssertionError('Unexpected HTTP request: ' + req.full_url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return Response(response)


class FakeGraph:
    """Stateful Microsoft-response fake; actual transport gate is tested separately."""
    def __init__(self, cfg=None):
        self.cfg = cfg or config()
        self.package = read_json(ROOT / 'tests/fixtures/package.json')
        self.policies = []
        self.writes = []
        self.calls = []
        self.permit = None
        self.verify_fail = False

    def collection(self, path):
        self.calls.append(('GET', path))
        if path == CA:
            return copy.deepcopy(self.policies)
        if path == CATALOG:
            return [copy.deepcopy(self.package)]
        if path.startswith('/beta/identityProtection'):
            return []
        return []

    def request(self, method, path, body=None):
        self.calls.append((method, path))
        if method == 'GET':
            if '/microsoft.graph.agentIdentity' in path:
                return {'id': AGENT, 'appId': RESOURCE, 'displayName': 'Mock identity', 'agentIdentityBlueprintId': POLICY}
            if path.startswith(CA + '/'):
                if self.verify_fail:
                    raise ApiError(403)
                return copy.deepcopy(self.policies[0])
            if path.startswith(CATALOG + '/'):
                if self.verify_fail and self.writes:
                    raise ApiError(403)
                return copy.deepcopy(self.package)
        if method == 'POST' and path == HUNT:
            return {'results': []}
        if method in ('POST', 'PATCH'):
            assert self.permit == (method, path, body), 'fake write without permit'
            self.permit = None
            self.writes.append((method, path, body))
            if path == CA:
                self.policies = [dict(copy.deepcopy(body), id=POLICY)]
                return self.policies[0]
            if path.startswith(CA + '/'):
                self.policies[0].update(body)
                return {}
            self.package['isBlocked'] = path.endswith('/block')
            return {}
        raise AssertionError('Unexpected request')

    def authorize(self, method, path, body):
        self.permit = method, path, body


class ConfigTests(unittest.TestCase):
    def test_example_and_live_config(self):
        check_config(read_json(ROOT / 'config/pilot.example.json'))
        check_config(config(), live=True)

    def test_placeholders_refused_live(self):
        with self.assertRaises(SafetyError):
            check_config(read_json(ROOT / 'config/pilot.example.json'), live=True)

    def test_unsafe_configs_refused(self):
        edits = [('tenant', 'purpose', 'production'), ('conditionalAccess', 'state', 'enabled'),
                 ('conditionalAccess', 'agentObjectIds', ['All']), ('conditionalAccess', 'resourceAppIds', []),
                 ('conditionalAccess', 'riskLevels', ['low']), ('telemetry', 'collectContent', True),
                 ('purview', 'expectedMode', 'Enable')]
        for section, key, value in edits:
            with self.subTest(key=key):
                c = config()
                c[section][key] = value
                with self.assertRaises(SafetyError):
                    check_config(c, live=True)

    def test_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.json'
            p.write_text('{"tenant":1,"tenant":2}')
            with self.assertRaises(SafetyError):
                read_json(p)

    def test_content_not_in_package_export(self):
        p = read_json(ROOT / 'tests/fixtures/package.json')
        self.assertNotIn('MOCK_PRIVATE', json.dumps(package_summary(p)))


class TransportTests(unittest.TestCase):
    def graph(self, responses, verified=False):
        g = Graph('mock-token', config()['tenant'])
        g.opener = QueueOpener(responses)
        g.verified = verified
        return g

    def test_identity_first_and_matching(self):
        g = self.graph([read_json(ROOT / 'tests/fixtures/organization.json')])
        with self.assertRaises(SafetyError):
            g.request('GET', CATALOG)
        with redirect_stdout(io.StringIO()):
            g.verify()
        self.assertTrue(g.verified)
        self.assertEqual(len(g.opener.calls), 1)

    def test_wrong_tenant_or_name_stops(self):
        for field in ('id', 'displayName'):
            body = read_json(ROOT / 'tests/fixtures/organization.json')
            body['value'][0][field] = 'unexpected'
            g = self.graph([body])
            with self.assertRaises(SafetyError), redirect_stdout(io.StringIO()):
                g.verify()
            self.assertFalse(g.verified)
            self.assertEqual(len(g.opener.calls), 1)

    def test_unapproved_write_and_single_use(self):
        g = self.graph([{}], verified=True)
        with self.assertRaises(SafetyError):
            g.request('PATCH', CA + '/' + POLICY, {'state': 'enabled'})
        g.authorize('PATCH', CA + '/' + POLICY, {'state': 'disabled'})
        with self.assertRaises(SafetyError):
            g.request('PATCH', CA + '/' + POLICY, {'state': 'enabled'})
        g.request('PATCH', CA + '/' + POLICY, {'state': 'disabled'})
        with self.assertRaises(SafetyError):
            g.request('PATCH', CA + '/' + POLICY, {'state': 'disabled'})

    def test_hunting_post_is_read_only(self):
        g = self.graph([{'results': []}], verified=True)
        self.assertEqual(g.request('POST', HUNT, {'Query': 'AgentsInfo | count'}), {'results': []})

    def test_pagination_all_pages(self):
        next_link = ORIGIN + CATALOG + '?$skiptoken=opaque'
        g = self.graph([{'value': [1], '@odata.nextLink': next_link}, {'value': [2]}], verified=True)
        self.assertEqual(g.collection(CATALOG), [1, 2])
        self.assertEqual(g.opener.calls[1].full_url, next_link)

    def test_foreign_pagination_denied_before_token_leak(self):
        g = self.graph([{'value': [], '@odata.nextLink': 'https://attacker.example/v1.0/collect'}], verified=True)
        with self.assertRaises(SafetyError):
            g.collection(CATALOG)
        self.assertEqual(len(g.opener.calls), 1)

    def test_loop_and_malformed_page(self):
        for response in ({'value': [], '@odata.nextLink': ORIGIN + CATALOG}, {'unexpected': []}):
            g = self.graph([response], verified=True)
            with self.assertRaises(SafetyError):
                g.collection(CATALOG)

    def test_bad_origins(self):
        for url in ('https://graph.microsoft.com.attacker.example/v1.0/x', 'https://graph.microsoft.com:443/v1.0/x',
                    'https://evil@graph.microsoft.com/v1.0/x', 'https://graph.microsoft.com/v1.0/../x', 'http://graph.microsoft.com/v1.0/x'):
            with self.subTest(url=url), self.assertRaises(SafetyError):
                Graph.url(url)

    def test_malformed_json_shape(self):
        for value in ([], 'unexpected', 1):
            g = self.graph([value], verified=True)
            with self.assertRaises(SafetyError):
                g.request('GET', CATALOG)

    def test_permission_error_sanitized(self):
        err = HTTPError(ORIGIN, 403, 'private body', {'request-id': 'mock-request'}, io.BytesIO(b'secret-body'))
        g = self.graph([err], verified=True)
        with self.assertRaises(ApiError) as ctx:
            g.collection(CATALOG)
        self.assertNotIn('secret-body', str(ctx.exception))

    def test_read_throttle_retries_but_write_does_not(self):
        def err():
            return HTTPError(ORIGIN, 429, '', {'Retry-After': '0'}, io.BytesIO(b''))
        g = self.graph([err(), {'value': []}], verified=True)
        self.assertEqual(g.collection(CATALOG), [])
        g = self.graph([err(), {}], verified=True)
        g.authorize('POST', CA, {})
        with self.assertRaises(ApiError):
            g.request('POST', CA, {})
        self.assertEqual(len(g.opener.calls), 1)

    def test_external_cache_required(self):
        with patch.dict(os.environ, {'A365_AZURE_CONFIG_DIR': str(ROOT / '.azure')}):
            with self.assertRaises(SafetyError):
                Graph.from_cli(config()['tenant'])

    def test_token_tenant_mismatch(self):
        fake = type('Proc', (), {'returncode': 0, 'stdout': json.dumps({'tenant': POLICY, 'accessToken': 'private'})})()
        with patch.dict(os.environ, {'A365_AZURE_CONFIG_DIR': '/tmp/a365-mock-cache'}), patch('subprocess.run', return_value=fake):
            with self.assertRaises(SafetyError):
                Graph.from_cli(config()['tenant'])


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.cfg = config()
        self.g = FakeGraph(self.cfg)

    def test_baseline_exact_scope_report_only(self):
        plan = build_plan(self.g, self.cfg, 'ca-deploy')
        body = plan['request']['body']
        self.assertEqual(body['state'], 'enabledForReportingButNotEnforced')
        self.assertEqual(body['conditions']['clientApplications']['includeAgentIdServicePrincipals'], [AGENT])
        self.assertEqual(body['conditions']['agentIdRiskLevels'], 'high')
        self.assertFalse(self.g.writes)

    def test_read_only_profile_blocks_change(self):
        self.cfg['profile'] = 'read-only'
        with self.assertRaises(SafetyError):
            build_plan(self.g, self.cfg, 'ca-deploy')

    def test_apply_defaults_dry_run(self):
        doc = envelope(build_plan(self.g, self.cfg, 'ca-deploy'))
        outcome = apply_plan(self.g, self.cfg, doc, None, None)
        self.assertEqual(outcome['status'], 'skipped')
        self.assertFalse(self.g.writes)

    def test_exact_approval_required(self):
        doc = envelope(build_plan(self.g, self.cfg, 'ca-deploy'))
        with self.assertRaises(SafetyError):
            apply_plan(self.g, self.cfg, doc, 'wrong', Path('/unused'), execute=True)
        self.assertFalse(self.g.writes)

    def test_tampered_plan_rejected_even_if_rehashed(self):
        doc = envelope(build_plan(self.g, self.cfg, 'ca-deploy'))
        doc['plan']['request']['body']['state'] = 'enabled'
        doc['approvalDigest'] = digest({k:v for k,v in doc.items() if k != 'approvalDigest'})
        with self.assertRaises(SafetyError):
            apply_plan(self.g, self.cfg, doc, doc['approvalDigest'], Path('/unused'), execute=True)
        self.assertFalse(self.g.writes)

    def test_expired_plan(self):
        doc = envelope(build_plan(self.g, self.cfg, 'ca-deploy'))
        doc['createdAt'] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        doc['approvalDigest'] = digest({k:v for k,v in doc.items() if k != 'approvalDigest'})
        with self.assertRaises(SafetyError):
            apply_plan(self.g, self.cfg, doc, None, None)

    def test_wrong_environment_and_offline_plan(self):
        doc = envelope(build_plan(self.g, self.cfg, 'ca-deploy'))
        changed = copy.deepcopy(self.cfg)
        changed['tenant']['environment'] = 'other'
        with self.assertRaises(SafetyError):
            apply_plan(self.g, changed, doc, None, None)
        doc['origin'] = 'offline-not-applicable'
        with self.assertRaises(SafetyError):
            apply_plan(self.g, self.cfg, doc, None, None)

    def test_create_verified_and_idempotent_plan(self):
        doc = envelope(build_plan(self.g, self.cfg, 'ca-deploy'))
        with tempfile.TemporaryDirectory() as tmp:
            outcome = apply_plan(self.g, self.cfg, doc, doc['approvalDigest'], Path(tmp), execute=True)
            self.assertEqual(outcome['status'], 'applied')
            self.assertTrue((Path(tmp) / 'intent.json').exists())
            self.assertEqual(read_json(Path(tmp) / 'receipt.json')['policyId'], POLICY)
        self.assertIsNone(build_plan(self.g, self.cfg, 'ca-deploy')['request'])
        self.assertEqual(len(self.g.writes), 1)

    def test_promotion_and_disable_preserve_scope(self):
        self.g.policies = [dict(ca_payload(self.cfg), id=POLICY)]
        for intent, state in [('ca-promote', 'enabled'), ('ca-disable', 'disabled')]:
            plan = build_plan(self.g, self.cfg, intent)
            self.assertEqual(plan['request']['body'], {'state': state})
            self.assertEqual(plan['desired']['conditions'], ca_payload(self.cfg)['conditions'])

    def test_scope_drift_and_duplicate_policy_refused(self):
        self.g.policies = [dict(ca_payload(self.cfg), id=POLICY)]
        self.g.policies[0]['conditions']['users'] = {'includeUsers': ['All']}
        with self.assertRaises(SafetyError):
            build_plan(self.g, self.cfg, 'ca-promote')
        self.g.policies = [dict(ca_payload(self.cfg), id=POLICY)] * 2
        with self.assertRaises(SafetyError):
            build_plan(self.g, self.cfg, 'ca-deploy')

    def test_fresh_state_change_stops_apply(self):
        doc = envelope(build_plan(self.g, self.cfg, 'registry-block', 'P_mock-agent'))
        self.g.package['version'] = '2.0'
        with self.assertRaises(SafetyError):
            apply_plan(self.g, self.cfg, doc, doc['approvalDigest'], Path('/unused'), execute=True)
        self.assertFalse(self.g.writes)

    def test_containment_and_recovery(self):
        for intent, expected in [('registry-block', True), ('registry-unblock', False)]:
            doc = envelope(build_plan(self.g, self.cfg, intent, 'P_mock-agent'))
            with tempfile.TemporaryDirectory() as tmp:
                outcome = apply_plan(self.g, self.cfg, doc, doc['approvalDigest'], Path(tmp), execute=True)
            self.assertEqual(outcome['status'], 'applied')
            self.assertEqual(self.g.package['isBlocked'], expected)

    def test_failed_readback_not_applied_and_evidence_retained(self):
        doc = envelope(build_plan(self.g, self.cfg, 'ca-deploy'))
        self.g.verify_fail = True
        with tempfile.TemporaryDirectory() as tmp:
            outcome = apply_plan(self.g, self.cfg, doc, doc['approvalDigest'], Path(tmp), execute=True)
            self.assertEqual(outcome['status'], 'not verifiable')
            self.assertTrue((Path(tmp) / 'intent.json').exists())
            self.assertTrue((Path(tmp) / 'outcome.json').exists())

    def test_evidence_collision_prevents_write(self):
        doc = envelope(build_plan(self.g, self.cfg, 'ca-deploy'))
        with tempfile.TemporaryDirectory() as tmp:
            write_json(Path(tmp) / 'intent.json', {})
            with self.assertRaises(FileExistsError):
                apply_plan(self.g, self.cfg, doc, doc['approvalDigest'], Path(tmp), execute=True)
        self.assertFalse(self.g.writes)

    def test_assess_validate_snapshot_never_write(self):
        assess(self.g, self.cfg)
        validate_live(self.g, self.cfg)
        snap = inventory_snapshot(self.g, self.cfg)
        self.assertFalse(self.g.writes)
        self.assertFalse(snap['complete'])
        self.assertIsNone(snap['agents'][0]['tools'])
        self.assertNotIn('MOCK_PRIVATE', json.dumps(snap))

    def test_empty_hunting_is_not_verified(self):
        operations = validate_live(self.g, self.cfg)
        self.assertEqual(next(x for x in operations if x['operation'] == 'verify-telemetry-health')['status'], 'not verifiable')

    def test_extra_policy_exclusion_is_drift(self):
        self.g.policies = [dict(ca_payload(self.cfg), id=POLICY)]
        self.g.policies[0]['conditions']['applications']['excludeApplications'] = [RESOURCE]
        findings = validate_live(self.g, self.cfg)
        self.assertEqual(findings[0]['status'], 'failed')

    def test_registry_already_blocked_no_write(self):
        self.g.package['isBlocked'] = True
        doc = envelope(build_plan(self.g, self.cfg, 'registry-block', 'P_mock-agent'))
        outcome = apply_plan(self.g, self.cfg, doc, doc['approvalDigest'], None, execute=True)
        self.assertEqual(outcome['status'], 'skipped')
        self.assertFalse(self.g.writes)

    def test_non_agent_package_is_refused(self):
        self.g.package.update(elementTypes=['officeAddIn'], supportedHosts=['Outlook'])
        with self.assertRaises(SafetyError):
            build_plan(self.g, self.cfg, 'registry-block', 'P_mock-agent')

    def test_wrong_agent_identity_is_refused(self):
        with patch.object(self.g, 'request', return_value={'id': POLICY}):
            with self.assertRaises(SafetyError):
                build_plan(self.g, self.cfg, 'ca-deploy')

    def test_ca_placeholders_allow_readiness_but_not_live_plan(self):
        self.cfg['conditionalAccess']['agentObjectIds'] = ['<TEST-AGENT-ID>']
        check_config(self.cfg, live=True)
        with self.assertRaises(SafetyError):
            build_plan(self.g, self.cfg, 'ca-deploy')
        self.assertFalse(self.g.calls)

    def test_write_timeout_keeps_intent_and_unknown_outcome(self):
        doc = envelope(build_plan(self.g, self.cfg, 'registry-block', 'P_mock-agent'))
        original = self.g.request
        def timed_out(method, path, body=None):
            if method == 'POST':
                raise SafetyError('Mock network timeout')
            return original(method, path, body)
        with patch.object(self.g, 'request', side_effect=timed_out), tempfile.TemporaryDirectory() as tmp:
            outcome = apply_plan(self.g, self.cfg, doc, doc['approvalDigest'], Path(tmp), execute=True)
            self.assertEqual(outcome['status'], 'not verifiable')
            self.assertTrue((Path(tmp) / 'intent.json').exists())
            self.assertTrue((Path(tmp) / 'outcome.json').exists())


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.cfg = config()
        self.expected = {'packageId': 'P_mock-agent', 'name': 'Mock test agent', 'platform': 'Custom', 'version': '1.0',
                         'owners': [AGENT], 'permissions': ['resource:read'], 'tools': ['tool:read'], 'requiredControls': ['audit'],
                         'agentObjectId': AGENT, 'blueprintId': POLICY, 'observabilityAppId': RESOURCE}
        self.cfg['approvedInventory'] = [self.expected]
        observed = {k:v for k,v in self.expected.items() if k != 'requiredControls'}
        observed.update(controls=['audit'], lastSeen=now(), risk='none')
        self.snap = dict(schemaVersion=1, tenantId=TENANT, environment='isolated-pilot', capturedAt=now(), complete=True, agents=[observed])

    def test_matching_inventory(self):
        self.assertEqual(audit_inventory(self.cfg, self.snap)[0]['status'], 'skipped')

    def test_unknown_not_clean(self):
        self.snap['agents'][0]['permissions'] = None
        self.assertEqual(audit_inventory(self.cfg, self.snap)[0]['status'], 'not verifiable')

    def test_drift_owner_permissions_tools_controls_telemetry_risk(self):
        a = self.snap['agents'][0]
        a.update(owners=[], permissions=['resource:write'], tools=['tool:write'], controls=[], version='2.0', risk='high',
                 lastSeen=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat())
        evidence = audit_inventory(self.cfg, self.snap)[0]
        self.assertEqual(evidence['status'], 'failed')
        for item in ('missing owner', 'unapproved permissions', 'unapproved tools', 'missing required controls', 'version drift', 'risky agent: high', 'telemetry stale or future-dated'):
            self.assertIn(item, evidence['evidence']['findings'])

    def test_stale_mixed_and_duplicate_snapshots_rejected(self):
        for field, value in [('tenantId', POLICY), ('environment', 'other'), ('capturedAt', '2000-01-01T00:00:00Z')]:
            s = copy.deepcopy(self.snap)
            s[field] = value
            with self.assertRaises(SafetyError):
                audit_inventory(self.cfg, s)
        self.snap['agents'] *= 2
        with self.assertRaises(SafetyError):
            audit_inventory(self.cfg, self.snap)

    def test_incomplete_not_discovered_unknown(self):
        self.snap.update(complete=False, agents=[])
        self.assertEqual(audit_inventory(self.cfg, self.snap)[0]['status'], 'not verifiable')

    def test_snapshot_controls_not_a_string(self):
        self.snap['agents'][0]['controls'] = 'audit'
        with self.assertRaises(SafetyError):
            audit_inventory(self.cfg, self.snap)


class CliAndReportTests(unittest.TestCase):
    def test_offline_commands_never_authenticate(self):
        with patch.object(Graph, 'from_cli', side_effect=AssertionError('network forbidden')):
            for command in ('check-config', 'assess', 'plan', 'build', 'validate'):
                with self.subTest(command=command), redirect_stdout(io.StringIO()):
                    self.assertIn(main([command]), (0, 2))

    def test_live_requires_selection_before_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'config.json'
            write_json(file, config())
            with patch.object(Graph, 'from_cli', side_effect=AssertionError('auth forbidden')), redirect_stderr(io.StringIO()):
                self.assertEqual(main(['assess', '--live', '--config', str(file)]), 1)

    def test_execute_not_allowed_on_assess_plan_build_contain(self):
        for command in ('assess', 'plan', 'build', 'contain', 'validate'):
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main([command, '--execute']), 1)

    def test_html_escaped_and_evidence_not_overwritten(self):
        c = config()
        c['tenant']['displayName'] = '<script>alert(1)</script>'
        data = report('mock', c, [result('mock', 'skipped', '<img src=x onerror=bad>')])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.json'
            save_report(path, data)
            self.assertNotIn('<script>', path.with_suffix('.html').read_text())
            self.assertIn('&lt;img', path.with_suffix('.html').read_text())
            with self.assertRaises(FileExistsError):
                save_report(path, data)


if __name__ == '__main__':
    unittest.main()
