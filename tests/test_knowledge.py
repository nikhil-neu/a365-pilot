import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from a365.knowledge import from_inventory, collect_catalog, main
from a365.core import SafetyError
from a365.graph import CATALOG


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {'schemaVersion': 1, 'capturedAt': '2026-10-10T08:00:00Z', 'source': 'authorized inventory', 'agents': [
            {'packageId': 'agent1', 'name': 'Real inventory name', 'platform': None, 'owners': ['owner-id'], 'instructions': 'NEVER EXPORT'}]}

    def test_export_does_not_invent_relationships(self):
        d = from_inventory(self.snapshot, 'tenant-export')
        self.assertEqual(d['dataKind'], 'tenant-export')
        self.assertIsNone(d['agents'][0]['sources'])
        self.assertFalse(d['agents'][0]['sourcesComplete'])
        self.assertIsNone(d['discoveredContainers']['value'])
        self.assertEqual(d['labels'], [])
        self.assertNotIn('NEVER EXPORT', str(d))
        self.assertFalse(d['complete'])

    def test_sample_provenance_remains_sample(self):
        self.assertEqual(from_inventory(self.snapshot, 'sample')['dataKind'], 'sample')
        with self.assertRaises(SafetyError):
            from_inventory(self.snapshot, 'assumed-live')

    def test_duplicates_and_bad_timestamp_fail(self):
        d = copy.deepcopy(self.snapshot)
        d['agents'] *= 2
        with self.assertRaises(SafetyError):
            from_inventory(d, 'tenant-export')
        d = copy.deepcopy(self.snapshot)
        d['capturedAt'] = '2026-10-10'
        with self.assertRaises(SafetyError):
            from_inventory(d, 'tenant-export')

    def test_catalog_requires_identity_and_only_reads(self):
        graph = Mock(verified=False, tenant={'id': 'selected', 'environment': 'test'})
        cfg = {'tenant': graph.tenant}
        with self.assertRaises(SafetyError):
            collect_catalog(graph, cfg)
        graph.collection.assert_not_called()
        graph.verified = True
        graph.collection.return_value = [{'id': 'one', 'displayName': 'Agent', 'elementTypes': ['DeclarativeAgent'], 'instructions': 'NEVER EXPORT'}]
        with patch('a365.knowledge.is_agent', return_value=True):
            result = collect_catalog(graph, cfg)
        graph.collection.assert_called_once_with(CATALOG)
        graph.authorize.assert_not_called()
        self.assertIsNone(result['agents'][0]['owners'])
        self.assertNotIn('NEVER EXPORT', str(result))

    def test_collect_requires_explicit_live_opt_in(self):
        with patch('a365.knowledge.Graph.from_cli') as auth:
            self.assertEqual(main(['collect', '--out', '/tmp/a365-knowledge-never-created.json']), 1)
            auth.assert_not_called()


class StudioTests(unittest.TestCase):
    def test_environment_origin_rejects_untrusted_urls(self):
        from a365.studio import environment_origin
        self.assertEqual(environment_origin('https://example.crm4.dynamics.com/'), 'https://example.crm4.dynamics.com')
        for value in ['http://example.crm.dynamics.com', 'https://example.com', 'https://user:secret@example.crm.dynamics.com', 'https://example.crm.dynamics.com/path', 'https://example.crm.dynamics.com?token=x']:
            with self.assertRaises(SafetyError):
                environment_origin(value)

    def test_parser_exports_only_supported_metadata(self):
        import importlib.util
        if importlib.util.find_spec('yaml') is None:
            self.skipTest('Optional PyYAML dependency not installed')
        from a365.studio import parse_source
        result = parse_source('kind: KnowledgeSourceConfiguration\ndescription: DO NOT EXPORT\nsource:\n  kind: SharePointKnowledgeSource\n  siteUrl: https://example.sharepoint.com/sites/a?token=SECRET\n')
        self.assertEqual(result, {'type': 'SharePointKnowledgeSource', 'location': 'https://example.sharepoint.com/sites/a'})
        self.assertIsNone(parse_source('kind: AdaptiveDialog\ninstructions: NEVER EXPORT'))
        self.assertIsNone(parse_source('a: &loop [*loop]'))
        self.assertIsNone(parse_source('!!python/object/apply:os.system ["echo forbidden"]'))

    def test_collector_excludes_topics_and_file_data(self):
        import importlib.util
        if importlib.util.find_spec('yaml') is None:
            self.skipTest('Optional PyYAML dependency not installed')
        from a365.studio import collect_studio
        bot = '11111111-1111-4111-8111-111111111111'
        component = '22222222-2222-4222-8222-222222222222'
        tenant = {'id': 'selected', 'displayName': 'Mock tenant'}
        client = Mock(verified=True, tenant=tenant, origin='https://example.crm.dynamics.com')
        client.collection.side_effect = [[{'botid': bot, 'name': 'Mock agent'}], [{'botcomponentid': component, 'componenttype': 16, '_parentbotid_value': bot, 'name': 'Knowledge', 'data': 'kind: KnowledgeSourceConfiguration\nsource:\n  kind: WebsiteKnowledgeSource\n  siteUrl: https://example.invalid/reference\n'}], []]
        output = collect_studio(client, {'tenant': tenant})
        source = output['agents'][0]['sources'][0]
        self.assertEqual(source['location']['value'], 'https://example.invalid/reference')
        self.assertIsNone(source['runtimeRetrieved']['value'])
        self.assertIsNone(source['containerLabel']['value'])
        self.assertIsNone(source['external']['value'])
        self.assertFalse(output['agents'][0]['sourcesComplete'])
        calls = [c.args[0] for c in client.collection.call_args_list]
        self.assertIn('componenttype%20eq%2016', calls[1])
        self.assertIn('componenttype%20eq%2014', calls[2])
        self.assertNotIn(',data', calls[2])
        client.authorize.assert_not_called()

    def test_dataverse_denies_writes_and_wrong_host(self):
        from a365.studio import Dataverse, PREFIX
        client = Dataverse('not-a-token', {'id': 'selected'})
        client.origin = 'https://example.crm.dynamics.com'
        with self.assertRaises(SafetyError):
            client.request('POST', PREFIX+'bots', {})
        with self.assertRaises(SafetyError):
            client.url('https://other.crm.dynamics.com'+PREFIX+'bots')
        with self.assertRaises(SafetyError):
            client.url(PREFIX+'conversationtranscripts')

    def test_dataverse_pagination_cannot_expand_to_topic_content(self):
        from a365.studio import Dataverse, PREFIX
        client = Dataverse('not-a-token', {'id': 'selected'})
        client.origin = 'https://example.crm.dynamics.com'
        bot = '11111111-1111-4111-8111-111111111111'
        base = PREFIX + 'botcomponents?$select=botcomponentid,name,componenttype,_parentbotid_value,data&$filter=_parentbotid_value%20eq%20' + bot + '%20and%20componenttype%20eq%2016%20and%20statecode%20eq%200'
        self.assertTrue(client.url(base).startswith(client.origin))
        for bad in (base.replace('eq%2016', 'eq%2015'), base + '&$expand=parentbotid', base.replace(',data', ',content'), PREFIX + 'bots?$select=*'):
            with self.assertRaises(SafetyError):
                client.url(bad)
