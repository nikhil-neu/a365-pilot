"""Current delegated user's Agent 365 assignment, separate from feature readiness."""
from .core import SafetyError, now, result

# Microsoft licensing-service-plan-reference, checked 2026-10-12.
SKU = '796a6fb4-740b-4d36-bf56-9c12ca7fa069'
PLAN = 'd0ce5ebb-9db0-491f-b780-8973a1d815fe'
PATH = '/v1.0/me/licenseDetails?$select=skuId,skuPartNumber,servicePlans'


def current_user_license(graph):
    evidence = {'currentUserHasAgent365License': None, 'source': PATH,
                'checkedAt': now(), 'subject': 'Signed-in delegated user', 'matches': []}
    try:
        rows = graph.collection(PATH)
        malformed = False
        for license in rows:
            if not isinstance(license, dict):
                malformed = True
                continue
            plans = license.get('servicePlans')
            if not isinstance(plans, list):
                malformed = True
                plans = []
            matches = [p for p in plans if isinstance(p, dict) and str(p.get('servicePlanId', '')).lower() == PLAN]
            malformed |= any(not isinstance(p, dict) or not isinstance(p.get('servicePlanId'), str) for p in plans)
            malformed |= not isinstance(license.get('skuId'), str)
            if str(license.get('skuId', '')).lower() == SKU or matches:
                evidence['matches'].append({'skuId': license.get('skuId'),
                    'servicePlanStates': [p.get('provisioningStatus') if isinstance(p.get('provisioningStatus'), str) else None for p in matches]})
        assigned = True if evidence['matches'] else None if malformed else False
        evidence['currentUserHasAgent365License'] = assigned
        evidence['reason'] = 'Current user Agent 365 license: {}. Assignment does not prove enabled service plans, terms acceptance or feature readiness.'.format('Unknown' if assigned is None else str(assigned).lower())
        return result('current-user-agent365-license', 'not verifiable' if assigned is None else 'skipped', evidence,
                      observed='read succeeded; inspect evidence, not a compliance assertion')
    except SafetyError:
        evidence['reason'] = 'Current user Agent 365 license: Unknown. License details could not be read completely; check delegated permissions and role access.'
        return result('current-user-agent365-license', 'not verifiable', evidence)
