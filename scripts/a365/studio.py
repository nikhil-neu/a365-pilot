"""Read-only Copilot Studio metadata adapter; no topics, transcripts or file bodies."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, quote, parse_qs
from urllib.request import Request

from .core import SafetyError, guid, now, require
from .graph import Graph, ApiError

PREFIX = '/api/data/v9.2/'
BOTS = PREFIX + 'bots?$select=botid,name,_ownerid_value'


def environment_origin(value):
    p = urlparse(value)
    require(p.scheme == 'https' and p.path in ('', '/') and not p.query and not p.fragment and not p.username,
            'Supply an HTTPS Dataverse environment origin, without path, query or credentials')
    require(re.fullmatch(r'[a-z0-9-]+\.(?:api\.)?crm[0-9]*\.dynamics\.com', p.netloc or ''),
            'Only explicit commercial-cloud Dataverse environment hosts are supported')
    return 'https://' + p.netloc


class Dataverse(Graph):
    @classmethod
    def connect(cls, tenant, origin):
        origin = environment_origin(origin)
        # Class scoped to this origin; avoids shared/global audience changes.
        bound = type('BoundDataverse', (cls,), {'token_resource': origin})
        client = bound.from_cli(tenant)
        client.origin = origin
        return client

    def url(self, path):
        url = path if path.startswith('https://') else self.origin + path
        p = urlparse(url)
        require(p.scheme == 'https' and p.netloc == urlparse(self.origin).netloc and not p.fragment and not p.username,
                'Dataverse link escaped selected environment')
        require(p.path.startswith(PREFIX) and '..' not in p.path and '\\' not in p.path and '%' not in p.path,
                'Invalid Dataverse path')
        require(p.path[len(PREFIX):].split('(')[0] in ('WhoAmI', 'bots', 'botcomponents'), 'Dataverse resource is outside metadata scope')
        query = parse_qs(p.query, keep_blank_values=True)
        require(all(len(v) == 1 for v in query.values()), 'Duplicate Dataverse query keys')
        table = p.path[len(PREFIX):].split('(')[0]
        if table == 'WhoAmI':
            require(not query, 'Unexpected identity query')
        elif table == 'bots':
            require(set(query) <= {'$select', '$skiptoken'} and query.get('$select') == ['botid,name,_ownerid_value'], 'Bot query escaped metadata projection')
        else:
            require(set(query) <= {'$select', '$filter', '$skiptoken'}, 'Unexpected component query')
            match = re.fullmatch(r'_parentbotid_value eq ([0-9a-fA-F-]{36}) and componenttype eq (16|14) and statecode eq 0', query.get('$filter', [''])[0])
            require(match and guid(match.group(1)), 'Component query must bind one bot and a supported source type')
            expected = 'botcomponentid,name,componenttype,_parentbotid_value' + (',data' if match.group(2) == '16' else '')
            require(query.get('$select') == [expected], 'Component query escaped metadata projection')
        return url

    def request(self, method, path, body=None):
        require(method == 'GET' and body is None, 'Knowledge collector permits GET only')
        url = self.url(path)
        require(self.verified or url == self.origin + PREFIX + 'WhoAmI', 'Verify Dataverse identity before metadata reads')
        request = Request(url, method='GET', headers={'Authorization': 'Bearer ' + self._token, 'Accept': 'application/json', 'OData-Version': '4.0'})
        try:
            with self.opener.open(request, timeout=60) as response:
                data = json.loads(response.read())
                require(isinstance(data, dict), 'Invalid Dataverse response')
                return data
        except HTTPError as exc:
            raise ApiError(exc.code, exc.headers.get('x-ms-service-request-id', 'unavailable')) from None
        except (URLError, TimeoutError, ValueError):
            raise SafetyError('Dataverse read failed; response body withheld') from None

    def verify(self):
        identity = self.request('GET', PREFIX + 'WhoAmI')
        require(guid(identity.get('OrganizationId')) and guid(identity.get('UserId')), 'Dataverse identity is incomplete')
        self.verified = True
        print(json.dumps({'dataverseEnvironment': self.origin, 'organizationId': identity['OrganizationId'], 'authenticationTenant': self.tenant['id'], 'mode': 'read-only'}), flush=True)
        return identity


def parse_source(raw):
    """Project an allowlisted source definition; never return raw YAML or descriptions."""
    if not isinstance(raw, str) or not raw or len(raw) > 1048576:
        return None
    try:
        import yaml
    except ImportError:
        raise SafetyError('Copilot Studio collection requires PyYAML; install requirements-knowledge.txt in a virtual environment') from None
    try:
        # Reject aliases to bound expansion and avoid recursive graphs.
        if any(isinstance(t, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)) for t in yaml.scan(raw)):
            return None
        d = yaml.safe_load(raw)
        if not isinstance(d, dict):
            return None
        if isinstance(d.get('KnowledgeSourceConfiguration'), dict):
            d = d['KnowledgeSourceConfiguration']
        if d.get('kind') != 'KnowledgeSourceConfiguration':
            return None
        s = d.get('source')
        if not isinstance(s, dict):
            return None
        kind = s.get('kind')
        if kind not in ('WebsiteKnowledgeSource', 'SharePointKnowledgeSource'):
            return None
        location = s.get('siteUrl')
        if not isinstance(location, str):
            return None
        u = urlparse(location)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.port not in (None, 443):
            return None
        # Opaque sharing-token URLs cannot be safely normalized to a source location.
        if u.path.startswith('/:'):
            return {'type': kind, 'location': None}
        # Query/fragment may contain tokens. Discard them without recording originals.
        return {'type': kind, 'location': 'https://' + u.netloc + u.path}
    except (yaml.YAMLError, ValueError, RecursionError):
        return None


def collect_studio(client, cfg, bot_ids=None):
    from .knowledge import observation
    require(client.verified and client.tenant == cfg['tenant'], 'Selected tenant and verified Dataverse session required')
    require(all(guid(v) for v in (bot_ids or [])), 'Agent selections must be Dataverse bot UUIDs')
    bots = [client.request('GET', PREFIX + 'bots(' + v + ')?$select=botid,name,_ownerid_value') for v in bot_ids] if bot_ids else client.collection(BOTS)
    stamp = now()
    agents, seen = [], set()
    for bot in bots:
        botid = bot.get('botid')
        require(guid(botid) and botid not in seen, 'Invalid/duplicate Dataverse bot ID')
        seen.add(botid)
        if bot_ids:
            require(botid in bot_ids, 'Dataverse returned a different bot identity')
        evidence_source = client.origin + PREFIX + 'bots(' + botid + ')'
        agent = {'packageId': 'dataverse:' + botid, 'name': bot.get('name') if isinstance(bot.get('name'), str) else None,
                 'platform': 'Copilot Studio', 'owners': [bot['_ownerid_value']] if guid(bot.get('_ownerid_value')) else None,
                 'sourcesComplete': False, 'sources': None, 'evidence': {'source': evidence_source, 'checkedAt': stamp}}
        sources = []
        try:
            for component_type in (16, 14):
                columns = 'botcomponentid,name,componenttype,_parentbotid_value' + (',data' if component_type == 16 else '')
                path = PREFIX + 'botcomponents?$select=' + columns + '&$filter=' + quote('_parentbotid_value eq {} and componenttype eq {} and statecode eq 0'.format(botid, component_type), safe='')
                rows = client.collection(path)
                for row in rows:
                    require(row.get('_parentbotid_value') == botid and row.get('componenttype') == component_type and guid(row.get('botcomponentid')), 'Component identity/type mismatch')
                    ref = client.origin + PREFIX + 'botcomponents(' + row['botcomponentid'] + ')'
                    parsed = parse_source(row.get('data')) if component_type == 16 else None
                    source = {'id': row['botcomponentid']}
                    values = {'name': row.get('name') if isinstance(row.get('name'), str) else None,
                              'type': parsed['type'] if parsed else 'Uploaded file attachment' if component_type == 14 else 'Knowledge source (unparsed configuration)',
                              'location': parsed['location'] if parsed else None,
                              'container': {'id': None, 'kind': 'notApplicable'} if parsed and parsed['type'] == 'WebsiteKnowledgeSource' else None,
                              'containerLabel': None, 'contentLabels': None, 'external': None, 'accessContext': None,
                              'lastCheck': stamp, 'runtimeRetrieved': None}
                    for key, value in values.items():
                        source[key] = observation(value, ref + ('; metadata read time, not sync time' if key == 'lastCheck' else '; not exposed/collected' if value is None else '; authoring configuration'), stamp)
                    sources.append(source)
            require(len({s['id'] for s in sources}) == len(sources), 'Duplicate component IDs')
            agent['sources'] = sources
        except ApiError as exc:
            # Do not turn denied/missing components into a complete empty inventory.
            agent['sources'] = sources or None
            agent['evidence']['source'] += '; component collection incomplete, HTTP ' + str(exc.status)
        agents.append(agent)
    return {'schemaVersion': 1, 'dataKind': 'tenant-export',
            'name': cfg['tenant']['displayName'] + ' · ' + client.origin + ' · Copilot Studio authoring metadata (partial)',
            'capturedAt': stamp, 'complete': False, 'labels': [],
            'discoveredContainers': observation(None, 'Tenant site/container enumeration not performed', stamp), 'agents': agents}
