"""Offline safety and partial-deployment tests; no Azure authentication."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from a365.admin import (API, Arm, ArmError, apply, check_admin, envelope, ids,
                        make_plan, matches, path_for, resources)
from a365.core import ROOT, SafetyError, digest, read_json

TENANT = '11111111-1111-4111-8111-111111111111'
SUB = '22222222-2222-4222-8222-222222222222'
AGENT = '33333333-3333-4333-8333-333333333333'


class MockArm:
    def __init__(self, cfg, admin):
        self.cfg, self.admin = cfg, admin
        self.state, self.writes = {}, []
        self.permit = None
        self.fail_at = None
        group, workspace = ids(admin['sentinel'])
        self.state[group + '?api-version=2022-09-01'] = {'id': group}
        self.workspace = workspace

    def request(self, method, path, body=None):
        if method == 'GET':
            if path not in self.state:
                raise ArmError(404)
            return copy.deepcopy(self.state[path])
        if self.permit != (method, path, body):
            raise SafetyError('unapproved write')
        self.permit = None
        self.writes.append((method, path, copy.deepcopy(body)))
        if self.fail_at == len(self.writes):
            raise ArmError(503)
        self.state[path] = copy.deepcopy(body)
        return body

    def get(self, item):
        return copy.deepcopy(self.state.get(path_for(item)))

    def authorize(self, method, path, body):
        self.permit = (method, path, copy.deepcopy(body))

    def seed_foundation(self):
        for item in resources(self.cfg, self.admin, 'foundation'):
            self.state[path_for(item)] = copy.deepcopy(item['body'])

    def seed_tables(self):
        for table, cols in {'SecurityAlert': ['TimeGenerated','Entities','SystemAlertId','AlertSeverity','ProviderName'], 'OfficeActivity': ['TimeGenerated','UserId','Operation','OfficeWorkload']}.items():
            self.state[self.workspace + '/tables/' + table + '?api-version=2022-10-01'] = {'properties': {'schema': {'columns': [{'name': c} for c in cols]}}}


class AdminTests(unittest.TestCase):
    def setUp(self):
        self.cfg = read_json(ROOT / 'config/pilot.example.json')
        self.cfg['tenant'].update(id=TENANT, displayName='Test')
        self.admin = read_json(ROOT / 'config/admin.example.json')
        self.admin['sentinel'].update(subscriptionId=SUB, location='eastus', pilotUserIds=['pilot@example.test'], agentObjectIds=[AGENT])
        self.admin['purview']['exchangeLocations'] = ['pilot@example.test']
        self.arm = MockArm(self.cfg, self.admin)

    def test_example_is_offline_only(self):
        example = read_json(ROOT / 'config/admin.example.json')
        check_admin(example)
        with self.assertRaises(SafetyError):
            check_admin(example, live=True)
        check_admin(self.admin, live=True)

    def test_reject_wildcard_scope_and_kql_injection(self):
        for path, value in [('pilotUserIds', ['*']), ('agentObjectIds', ['\"); delete']), ('dailyQuotaGb', -1), ('subscriptionId', 'bad')]:
            bad = copy.deepcopy(self.admin)
            bad['sentinel'][path] = value
            with self.assertRaises(SafetyError):
                check_admin(bad, live=True)
        self.admin['purview']['exchangeLocations'] = ['All']
        with self.assertRaises(SafetyError):
            check_admin(self.admin, live=True)

    def test_full_content_is_deterministic_disabled_and_separate_schema(self):
        first = resources(self.cfg, self.admin, 'content')
        self.assertEqual(first, resources(self.cfg, self.admin, 'content'))
        self.assertEqual(len(first), 8)
        self.assertNotIn('AgentsInfo\n|', json.dumps(first))
        self.assertNotIn('__PILOT_', json.dumps(first))
        for item in first:
            if item['body'].get('kind') == 'Scheduled':
                self.assertFalse(item['body']['properties']['enabled'])
            if '/automationRules/' in item['id']:
                self.assertFalse(item['body']['properties']['triggeringLogic']['isEnabled'])
        self.assertIn('2025-07-01-preview', json.dumps(resources(self.cfg, self.admin, 'connectors')))

    def test_plan_and_dry_run_make_zero_writes(self):
        doc = envelope(make_plan(self.arm, self.cfg, self.admin, 'foundation'))
        self.assertEqual(apply(self.arm, self.cfg, self.admin, doc)['status'], 'skipped')
        self.assertEqual(self.arm.writes, [])

    def test_approval_missing_or_wrong_never_writes(self):
        doc = envelope(make_plan(self.arm, self.cfg, self.admin, 'foundation'))
        for approval in (None, 'wrong'):
            with self.assertRaises(SafetyError):
                apply(self.arm, self.cfg, self.admin, doc, True, approval, '/tmp/should-not-exist')
        self.assertEqual(self.arm.writes, [])

    def test_success_records_intent_before_writes_and_reuses_on_replan(self):
        doc = envelope(make_plan(self.arm, self.cfg, self.admin, 'foundation'))
        with tempfile.TemporaryDirectory() as folder:
            evidence = Path(folder) / 'new'
            original = self.arm.authorize
            def authorize(*args):
                self.assertTrue((evidence / 'intent.json').exists())
                original(*args)
            self.arm.authorize = authorize
            outcome = apply(self.arm, self.cfg, self.admin, doc, True, doc['approvalDigest'], evidence)
            self.assertEqual(outcome['status'], 'applied')
            self.assertEqual(len(self.arm.writes), 2)
            self.assertTrue((evidence / 'outcome.json').exists())
            self.assertEqual({i['action'] for i in make_plan(self.arm, self.cfg, self.admin, 'foundation')['changes']}, {'reuse'})

    def test_tamper_expiry_and_config_drift(self):
        original = envelope(make_plan(self.arm, self.cfg, self.admin, 'foundation'))
        tamper = copy.deepcopy(original)
        tamper['plan']['changes'][0]['body']['location'] = 'westus'
        with self.assertRaises(SafetyError):
            apply(self.arm, self.cfg, self.admin, tamper)
        old = copy.deepcopy(original)
        old['createdAt'] = '2000-01-01T00:00:00Z'
        old['approvalDigest'] = digest({k: v for k, v in old.items() if k != 'approvalDigest'})
        with self.assertRaises(SafetyError):
            apply(self.arm, self.cfg, self.admin, old)
        self.admin['sentinel']['dailyQuotaGb'] = 2
        with self.assertRaises(SafetyError):
            apply(self.arm, self.cfg, self.admin, original)
        self.assertFalse(self.arm.writes)

    def test_remote_drift_and_read_only_profile(self):
        doc = envelope(make_plan(self.arm, self.cfg, self.admin, 'foundation'))
        self.arm.seed_foundation()
        with self.assertRaises(SafetyError):
            apply(self.arm, self.cfg, self.admin, doc)
        self.cfg['profile'] = 'read-only'
        doc = envelope(make_plan(self.arm, self.cfg, self.admin, 'foundation'))
        with self.assertRaises(SafetyError):
            apply(self.arm, self.cfg, self.admin, doc, True, doc['approvalDigest'], '/tmp/never')

    def test_partial_failure_stops_and_keeps_evidence(self):
        doc = envelope(make_plan(self.arm, self.cfg, self.admin, 'foundation'))
        self.arm.fail_at = 1
        with tempfile.TemporaryDirectory() as folder:
            evidence = Path(folder) / 'new'
            outcome = apply(self.arm, self.cfg, self.admin, doc, True, doc['approvalDigest'], evidence)
            self.assertEqual(outcome['status'], 'not verifiable')
            self.assertEqual(len(self.arm.writes), 1)
            self.assertTrue((evidence / '00-intent.json').exists())
            self.assertTrue((evidence / 'outcome.json').exists())

    def test_content_requires_real_tables_and_refuses_overwrite(self):
        self.arm.seed_foundation()
        with self.assertRaises(ArmError):
            make_plan(self.arm, self.cfg, self.admin, 'content')
        self.arm.seed_tables()
        make_plan(self.arm, self.cfg, self.admin, 'content')
        item = resources(self.cfg, self.admin, 'content')[0]
        self.arm.state[path_for(item)] = {'properties': {'query': 'other query'}}
        with self.assertRaises(SafetyError):
            make_plan(self.arm, self.cfg, self.admin, 'content')

    def test_duplicate_connector_is_blocked(self):
        self.arm.seed_foundation()
        self.arm.state[self.arm.workspace + '/providers/Microsoft.SecurityInsights/dataConnectors?api-version=2025-07-01-preview'] = {'value': [{'kind': 'Office365', 'id': 'other-id'}]}
        with self.assertRaises(SafetyError):
            make_plan(self.arm, self.cfg, self.admin, 'connectors')

    def test_activation_preserves_properties_and_can_be_disabled_without_tables(self):
        self.arm.seed_foundation()
        self.arm.seed_tables()
        for item in resources(self.cfg, self.admin, 'content'):
            self.arm.state[path_for(item)] = copy.deepcopy(item['body'])
            if '/alertRules/' in item['id']:
                self.arm.state[path_for(item)]['properties']['customDetails'] = {'Actor': 'AgentObjectId'}
        doc = envelope(make_plan(self.arm, self.cfg, self.admin, 'activate'))
        self.assertEqual({c['action'] for c in doc['plan']['changes']}, {'update'})
        self.assertEqual(len(doc['plan']['changes']), 3)
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(apply(self.arm, self.cfg, self.admin, doc, True, doc['approvalDigest'], Path(folder) / 'new')['status'], 'applied')
        for method, path, body in self.arm.writes:
            if '/alertRules/' in path:
                self.assertTrue(body['properties']['enabled'])
                self.assertIn('customDetails', body['properties'])
        for path in list(self.arm.state):
            if '/tables/' in path:
                del self.arm.state[path]
        off = make_plan(self.arm, self.cfg, self.admin, 'deactivate')
        self.assertEqual({c['action'] for c in off['changes']}, {'update'})

    def test_activation_rejects_missing_or_modified_rule(self):
        self.arm.seed_foundation()
        self.arm.seed_tables()
        with self.assertRaises(SafetyError):
            make_plan(self.arm, self.cfg, self.admin, 'activate')
        for item in resources(self.cfg, self.admin, 'content'):
            self.arm.state[path_for(item)] = copy.deepcopy(item['body'])
            if '/alertRules/' in item['id']:
                self.arm.state[path_for(item)]['properties']['query'] = 'unexpected query'
        with self.assertRaises(SafetyError):
            make_plan(self.arm, self.cfg, self.admin, 'activate')

    def test_watchlist_contents_must_match_after_upload(self):
        arm = Arm('never-a-real-token', self.cfg['tenant'])
        item = next(x for x in resources(self.cfg, self.admin, 'content') if '/watchlists/' in x['id'])
        observed = copy.deepcopy(item['body'])
        del observed['properties']['rawContent']
        observed['properties']['uploadStatus'] = 'Complete'
        with patch.object(arm, 'request', side_effect=[observed, {'value': [{'properties': {'itemsKeyValue': {'AgentObjectId': AGENT}}}]}]):
            self.assertTrue(matches(arm.get(item), item['body']))
        with patch.object(arm, 'request', side_effect=[copy.deepcopy(observed), {'value': [], 'nextLink': 'unverified'}]):
            with self.assertRaises(SafetyError):
                arm.get(item)

    def test_arm_rejects_cross_subscription_and_unapproved_put(self):
        arm = Arm('never-a-real-token', self.cfg['tenant'])
        arm.subscription = SUB
        arm.verified = True
        for path in ('https://example.test/subscriptions/' + SUB, '/subscriptions/' + TENANT + '?api-version=2022-12-01', '/subscriptions/' + SUB + '/%2e%2e?api-version=1'):
            with self.assertRaises(SafetyError):
                arm.url(path)
        item = resources(self.cfg, self.admin, 'foundation')[0]
        with self.assertRaises(SafetyError):
            arm.request('PUT', path_for(item), item['body'])

    def test_subscription_tenant_mismatch_stops(self):
        arm = Arm('never-a-real-token', self.cfg['tenant'])
        with patch.object(arm, 'request', return_value={'tenantId': SUB, 'state': 'Enabled'}):
            with self.assertRaises(SafetyError):
                arm.bind(SUB)
        self.assertFalse(arm.verified)

    def test_only_404_means_absence(self):
        arm = Arm('never-a-real-token', self.cfg['tenant'])
        item = resources(self.cfg, self.admin, 'foundation')[0]
        with patch.object(arm, 'request', side_effect=ArmError(403)):
            with self.assertRaises(ArmError):
                arm.get(item)
        with patch.object(arm, 'request', side_effect=ArmError(404)):
            self.assertIsNone(arm.get(item))


if __name__ == '__main__':
    unittest.main()
