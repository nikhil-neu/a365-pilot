import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from a365.licensing import current_user_license, SKU, PLAN
from a365.core import SafetyError

class LicenseTests(unittest.TestCase):
    def check(self, rows):
        g=Mock();g.collection.return_value=rows
        return current_user_license(g)['evidence']
    def test_direct_assignment(self):
        self.assertTrue(self.check([{'skuId':SKU,'servicePlans':[]}])['currentUserHasAgent365License'])
    def test_suite_disabled_still_assigned(self):
        e=self.check([{'skuId':'suite','servicePlans':[{'servicePlanId':PLAN,'provisioningStatus':'Disabled'}]}])
        self.assertTrue(e['currentUserHasAgent365License'])
        self.assertEqual(e['matches'][0]['servicePlanStates'],['Disabled'])
    def test_empty_false(self):
        self.assertFalse(self.check([])['currentUserHasAgent365License'])
    def test_unrelated_false(self):
        self.assertFalse(self.check([{'skuId':'other','servicePlans':[]}])['currentUserHasAgent365License'])
    def test_malformed_unknown(self):
        self.assertIsNone(self.check([{}])['currentUserHasAgent365License'])
    def test_denied_unknown(self):
        g=Mock();g.collection.side_effect=SafetyError('denied')
        self.assertIsNone(current_user_license(g)['evidence']['currentUserHasAgent365License'])
