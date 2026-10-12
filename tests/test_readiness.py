"""Risk evidence must preserve uncertainty and never export raw provider content."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from a365 import readiness
from a365.core import SafetyError


class RiskTests(unittest.TestCase):
    def graph(self):
        return Mock(verified=True, tenant={'id': 'test'})

    def test_no_live_never_authenticates(self):
        with patch.object(readiness.Graph, 'from_cli') as auth, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(readiness.main(['--out', '/tmp/not-written-risk.json']), 1)
            auth.assert_not_called()

    def test_unverified_never_queries(self):
        graph = self.graph()
        graph.verified = False
        with self.assertRaises(SafetyError):
            readiness.collect(graph)
        graph.collection.assert_not_called()

    def test_projection_and_empty_are_not_coverage(self):
        graph = self.graph()
        graph.collection.side_effect = [[{'id': 'a', 'riskLevel': 'high', 'additionalInfo': 'private', 'riskEvidence': 'private'}], []]
        report = readiness.collect(graph)
        self.assertEqual(report['results'][0]['count'], 1)
        self.assertNotIn('private', str(report))
        self.assertEqual(report['results'][1]['count'], 0)
        self.assertEqual(report['protectionCoverage'], 'not verifiable')
        graph.request.assert_not_called()

    def test_denied_and_malformed_remain_unknown(self):
        graph = self.graph()
        graph.collection.side_effect = [SafetyError('secret provider body'), [{'unexpected': True}]]
        report = readiness.collect(graph)
        for item in report['results']:
            self.assertIsNone(item['count'])
            self.assertIsNone(item['records'])
            self.assertEqual(item['status'], 'not verifiable')
        self.assertNotIn('secret provider body', str(report))
