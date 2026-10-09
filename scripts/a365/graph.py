"""Microsoft Graph transport with explicit identity and an exact-request write gate."""
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .core import ROOT, SafetyError, require

ORIGIN = 'https://graph.microsoft.com'
ORG = '/v1.0/organization?$select=id,displayName'
CATALOG = '/v1.0/copilot/admin/catalog/packages'
CA = '/beta/identity/conditionalAccess/policies'
HUNT = '/v1.0/security/runHuntingQuery'


class ApiError(SafetyError):
    def __init__(self, status, request_id='unavailable'):
        self.status = status
        super().__init__('Graph HTTP {} (request-id {}); response body withheld'.format(status, request_id))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SafetyError('Graph redirect rejected')


class Graph:
    token_resource = ORIGIN
    def __init__(self, token, tenant):
        self._token = token
        self.tenant = tenant
        self.verified = False
        self.permit = None
        self.opener = build_opener(NoRedirect())

    @classmethod
    def from_cli(cls, tenant):
        cache = os.environ.get('A365_AZURE_CONFIG_DIR', '')
        require(cache and Path(cache).is_absolute(), 'Set A365_AZURE_CONFIG_DIR to a dedicated absolute Azure CLI cache outside this repository')
        resolved = Path(cache).resolve()
        require(ROOT != resolved and ROOT not in resolved.parents, 'Credential cache must be outside the repository')
        env = dict(os.environ, AZURE_CONFIG_DIR=str(resolved))
        try:
            proc = subprocess.run(['az', 'account', 'get-access-token', '--tenant', tenant['id'], '--resource', cls.token_resource, '--output', 'json'], capture_output=True, text=True, env=env, timeout=60, check=False)
            require(proc.returncode == 0, 'Token acquisition failed; authenticate explicitly as described in docs/setup.md. CLI output withheld.')
            data = json.loads(proc.stdout)
            require(data.get('tenant', '').lower() == tenant['id'].lower(), 'Token tenant differs from selected tenant')
            require(isinstance(data.get('accessToken'), str) and data['accessToken'], 'No access token returned')
            return cls(data['accessToken'], tenant)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            raise SafetyError('Azure CLI unavailable or invalid token response; no token persisted') from None

    @staticmethod
    def url(path):
        url = path if path.startswith('https://') else ORIGIN + path
        parsed = urlparse(url)
        require(parsed.scheme == 'https' and parsed.netloc == 'graph.microsoft.com' and not parsed.fragment and not parsed.username, 'Untrusted Graph URL or pagination link')
        require(parsed.path.startswith(('/v1.0/', '/beta/')) and '..' not in parsed.path and '\\' not in parsed.path, 'Invalid Graph path')
        return url

    def request(self, method, path, body=None):
        url = self.url(path)
        require(self.verified or (method == 'GET' and url == ORIGIN + ORG), 'Identity verification must precede all other requests')
        read_query = method == 'POST' and url == ORIGIN + HUNT
        if method != 'GET' and not read_query:
            require(self.permit == (method, url, body), 'Tenant write denied: no exact approved request')
            self.permit = None  # Single use. Never automatically retry a write.
        request = Request(url, data=None if body is None else json.dumps(body).encode(), method=method,
                          headers={'Authorization': 'Bearer ' + self._token, 'Content-Type': 'application/json'})
        for attempt in range(3):
            try:
                with self.opener.open(request, timeout=30) as response:
                    raw = response.read()
                    data = json.loads(raw) if raw else {}
                    require(isinstance(data, dict), 'Graph response must be a JSON object')
                    return data
            except HTTPError as exc:
                if (method == 'GET' or read_query) and exc.code in (429, 503) and attempt < 2:
                    delay = exc.headers.get('Retry-After', '1')
                    time.sleep(min(int(delay) if delay.isdigit() else 1, 5))
                    continue
                raise ApiError(exc.code, exc.headers.get('request-id', 'unavailable')) from None
            except (URLError, TimeoutError, ValueError):
                raise SafetyError('Graph transport or JSON response failed; write outcome may be unknown; do not retry a mutation blindly') from None

    def collection(self, path):
        rows, visited = [], set()
        while path:
            url = self.url(path)
            require(url not in visited and len(visited) < 1000, 'Pagination loop or limit reached; inventory incomplete')
            visited.add(url)
            page = self.request('GET', path)
            require(isinstance(page.get('value'), list), 'Collection missing value array; cannot claim complete inventory')
            rows.extend(page['value'])
            path = page.get('@odata.nextLink')
        return rows

    def verify(self):
        rows = self.collection(ORG)
        require(len(rows) == 1, 'Organization check did not return exactly one tenant')
        org = rows[0]
        # Display observed identity even on mismatch. No other API request follows a mismatch.
        print('Observed tenant: {} ({}) / environment {}'.format(org.get('displayName'), org.get('id'), self.tenant['environment']), flush=True)
        require(org.get('id', '').lower() == self.tenant['id'].lower() and org.get('displayName') == self.tenant['displayName'], 'Selected test tenant ID/name does not match organization')
        self.verified = True
        return {'id': org['id'], 'displayName': org['displayName']}

    def authorize(self, method, path, body):
        require(self.verified, 'Cannot authorize before identity check')
        self.permit = (method, self.url(path), body)
