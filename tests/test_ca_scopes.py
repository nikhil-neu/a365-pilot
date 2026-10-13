import copy
import tempfile
import unittest
from pathlib import Path
from test_kit import config, FakeGraph, AGENT
from a365.core import check_config, SafetyError
from a365.operations import ca_payload, build_plan, envelope, apply_plan

class ScopeTests(unittest.TestCase):
    def expanded(self):
        cfg = config()
        cfg['profile'] = 'agent-assurance'
        cfg['conditionalAccess'].update(targetType='blueprint', resourceScope='all', resourceAppIds=[])
        return cfg

    def test_legacy_and_explicit_all(self):
        legacy = config()
        check_config(legacy)
        self.assertEqual(ca_payload(legacy)['conditions']['applications']['includeApplications'], legacy['conditionalAccess']['resourceAppIds'])
        cfg = self.expanded()
        check_config(cfg)
        self.assertEqual(ca_payload(cfg)['conditions']['applications']['includeApplications'], ['All'])

    def test_reject_ambiguous_and_invalid_scopes(self):
        for change in ({'resourceAppIds':[AGENT]}, {'targetType':'all'}, {'resourceScope':'*'}, {'agentObjectIds':[]}, {'agentObjectIds':[{}]}):
            cfg = self.expanded()
            cfg['conditionalAccess'].update(change)
            with self.assertRaises(SafetyError):
                check_config(cfg)

    def test_blueprint_typed_read_and_no_execution(self):
        cfg = self.expanded()
        graph = FakeGraph(cfg)
        plan = build_plan(graph, cfg, 'ca-deploy')
        self.assertIn(('GET', '/beta/servicePrincipals/' + AGENT + '/microsoft.graph.agentIdentityBlueprintPrincipal'), graph.calls)
        self.assertIn('future', plan['impact'])
        doc = envelope(plan)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(SafetyError, 'plan-only'):
                apply_plan(graph, cfg, doc, doc['approvalDigest'], Path(directory), execute=True)
        self.assertEqual(graph.writes, [])

    def test_placeholder_cannot_be_live_plan(self):
        cfg = self.expanded()
        cfg['conditionalAccess']['agentObjectIds'] = ['<BLUEPRINT>']
        with self.assertRaises(SafetyError):
            build_plan(FakeGraph(cfg), cfg, 'ca-deploy')
