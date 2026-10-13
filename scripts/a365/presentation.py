"""Human-readable projections; original statuses and evidence remain authoritative."""
import html
import json
from collections import Counter


def display_status(item):
    if item['status'] == 'skipped' and item.get('observed') == 'read succeeded; inspect evidence, not a compliance assertion':
        return 'Read succeeded — no changes made'
    return item['status'].capitalize()


def row(item):
    status = item['status']
    display = display_status(item)
    evidence = item['evidence']
    if isinstance(evidence, str):
        summary = evidence
    elif item['operation'] == 'active-directory-roles' and isinstance(evidence, list) and evidence:
        summary = '; '.join(x.get('displayName') if isinstance(x, dict) and isinstance(x.get('displayName'), str) and x['displayName'] else 'Role name unavailable' for x in evidence)
    elif isinstance(evidence, list):
        summary = '{} records returned; review details for scope and contents.'.format(len(evidence))
    elif isinstance(evidence, dict) and isinstance(evidence.get('reason'), str):
        summary = evidence['reason']
    else:
        summary = 'Structured evidence available in the details below.'
    next_step = {
        'not verifiable': 'Resolve the reported access, prerequisite or evidence gap; repeat the read.',
        'manual admin step required': 'Complete the documented administrator verification and retain evidence.',
        'failed': 'Investigate the failure; verify current state before retrying.',
        'applied': 'Verify runtime effect and retain recovery evidence.',
        'skipped': 'Review the evidence; a successful read is not proof of protection.'
    }[status]
    return [item['operation'].replace('-', ' ').capitalize(), display, summary, next_step]


def markdown(data):
    def cell(v):
        return html.escape(str(v)).replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')
    lines = ['# A365 toolkit assessment report', '',
             'Tenant: {} ({})'.format(cell(data['tenant']['displayName']), cell(data['tenant']['id'])),
             '', 'Environment: '+cell(data['tenant']['environment']), '', 'Captured: '+cell(data['capturedAt']),
             '', 'Mode: '+('Live evidence' if data.get('live') else 'Offline; no tenant connection'), '',
             '| Check | Result | Evidence summary | Next step |', '| --- | --- | --- | --- |']
    lines += ['| '+' | '.join(cell(v) for v in row(item))+' |' for item in data['operations']]
    lines += ['', 'Read succeeded means metadata was retrieved, not that a control is compliant. '
              'Skipped retains its original meaning unless an explicit successful-read observation exists. '
              'JSON retains the original statuses and full evidence.', '']
    return '\n'.join(lines)


def html_report(data):
    esc = lambda x: html.escape(str(x))
    rows = ''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row(item))+'</tr>' for item in data['operations'])
    details = ''.join('<details><summary>'+esc(item['operation'])+' — '+esc(display_status(item))+'</summary><pre>'+esc(json.dumps(item, indent=2))+'</pre></details>' for item in data['operations'])
    counts = Counter(display_status(item) for item in data['operations'])
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><title>A365 toolkit report</title><style>
body{font:14px/1.6 system-ui;color:#203a32;background:#f5f7f6;margin:0;padding:32px}main{max-width:1250px;margin:auto}h1{font-size:30px}p{color:#52665c}.table{overflow-x:auto;background:white;border:1px solid #dbe3de;border-radius:8px}table{width:100%;border-collapse:collapse;text-align:left}th{background:#e9f0ec}td,th{padding:15px;border-bottom:1px solid #e0e7e2;vertical-align:top}td:first-child{min-width:150px;font-weight:600}td:nth-child(2){min-width:135px}details{background:white;margin:10px 0;padding:14px;border:1px solid #dbe3de;border-radius:6px}summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}.counts{padding:14px;background:#e9f0ec}@media print{body{padding:0;background:white}table{font-size:10px}tr{break-inside:avoid}}@media(max-width:600px){body{padding:15px}}
</style></head><body><main><h1>A365 toolkit report</h1><p>'''+esc(data['command'])+' · '+esc(data['tenant']['displayName'])+' ('+esc(data['tenant']['id'])+')</p><p>Environment: '+esc(data['tenant']['environment'])+' · Captured: '+esc(data['capturedAt'])+'</p><p>'+('Live evidence' if data.get('live') else 'OFFLINE — no tenant connection')+'</p><p class="counts">'+esc(' · '.join('{}: {}'.format(k,v) for k,v in counts.items()))+'</p><h2>Assessment summary</h2><div class="table"><table><thead><tr><th>Check</th><th>Result</th><th>Evidence summary</th><th>Next step</th></tr></thead><tbody>'+rows+'</tbody></table></div><p>Read succeeded means metadata was retrieved, not that protection is enabled or compliant. Unknown results and manual work remain unresolved. Original statuses, impact and recovery appear below.</p><h2>Evidence details</h2>'+details+'</main></body></html>'
