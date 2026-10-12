#!/usr/bin/env python3
"""Offline repository checks. Not a Microsoft service or KQL compatibility test."""
import ast
import json
import re
from pathlib import Path

from a365.admin import check_admin, resources
from a365.core import ROOT, check_config, read_json, require


def check():
    for path in ROOT.rglob('*.py'):
        if '.venv' not in path.parts:
            ast.parse(path.read_text(), filename=str(path))
    pilot = check_config(read_json(ROOT / 'config/pilot.example.json'))
    admin = check_admin(read_json(ROOT / 'config/admin.example.json'))
    require(len(resources(pilot, admin, 'content')) == 8, 'Incomplete Sentinel pack')
    for path in (ROOT / 'sentinel/queries').glob('*.kql'):
        query = path.read_text()
        require('AgentsInfo' not in query and not re.search(r'\|\s*project\s+\*', query), 'Invalid Sentinel query scope')
        require('SecurityAlert' in query or 'OfficeActivity' in query, 'Unexpected Sentinel table')
    for path in (ROOT / 'config/profiles').glob('*.json'):
        profile = read_json(path)
        require(profile['schemaVersion'] == 1 and profile['name'] == path.stem, 'Invalid profile ' + path.name)
        require(profile['collectContent'] is False and profile['automaticPermissionGrants'] is False, 'Unsafe profile defaults')
        require(isinstance(profile['requiredControls'], list) and isinstance(profile['deploymentChoices'], list), 'Invalid profile controls')
    agent = ROOT / '.github/agents/a365-toolkit.agent.md'
    expected = {'assess', 'plan', 'build', 'validate', 'apply', 'contain', 'toolkit'}
    prompts = list((ROOT / '.github/prompts').glob('*.prompt.md'))
    require({p.name.replace('a365-', '').replace('.prompt.md', '') for p in prompts} == expected, 'Missing slash workflows')
    agents = list((ROOT / '.github/agents').glob('*.agent.md'))
    for path in agents + prompts:
        content = path.read_text()
        require(content.startswith('---\n'), 'Missing supported frontmatter')
        fields = dict(line.split(':', 1) for line in content.split('---', 2)[1].strip().splitlines())
        allowed = {'name', 'description'} if path in agents else {'description', 'agent'}
        if path == agent:
            allowed = allowed | {'tools'}
            require(json.loads(fields.get('tools', '[]')) ==
                    ['vscode/askQuestions', 'read', 'search', 'execute', 'edit'],
                    'Toolkit requires native input and execution tools')
        require(set(fields) == allowed, 'Unsupported/unexpected frontmatter fields')
        if path not in agents:
            require(fields['agent'].strip() == 'a365-toolkit', 'Prompt agent mismatch')
    for path in (ROOT / 'queries').glob('*.kql'):
        query = path.read_text()
        require('AIAgentsInfo' not in query, 'Retired hunting table')
        require('AgentsInfo' in query or 'CloudAppEvents' in query, 'Unknown data source')
        require(not re.search(r'\|\s*project\s+\*', query), 'Raw hunting output prohibited')
        require('project RawEventData' not in query and 'project Instructions' not in query, 'Content export prohibited')
    # Catch broken relative links in authored Markdown, excluding generated evidence.
    for folder in ('docs', 'playbooks', 'dashboards', 'queries', 'sentinel', '.github'):
        for path in (ROOT / folder).rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                require((path.parent / target.split('#')[0]).exists(), 'Broken link in {}: {}'.format(path, target))
    print(json.dumps({'operation': 'repository-check', 'status': 'skipped', 'evidence': 'Python syntax, config/profiles, custom agents and seven prompt formats, safe KQL conventions and relative links valid', 'impact': 'Offline only', 'rollback': 'None'}, indent=2))


if __name__ == '__main__':
    check()
