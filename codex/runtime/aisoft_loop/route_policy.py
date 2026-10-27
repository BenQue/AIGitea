"""Concrete provider routes, read from the one governed Markdown policy (#427).

This is a bounded interpreter of that table, not another classifier or scheduler.
Unsupported policy syntax fails instead of quietly keeping obsolete decisions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Mapping
from urllib.parse import urlsplit

from .classification import Classification
from .contract import ContractError

ROOT = Path(__file__).resolve().parents[3]
POLICY_RELATIVE = Path('skills/aisoft-platform/references/route-policy.md')
PROVIDERS = ('codex', 'claude', 'cursor')


def policy_path() -> Path:
    source = ROOT / POLICY_RELATIVE
    if source.is_file():
        return source
    # Project bundle: the same source has three provider landings. Never read HOME
    # or choose an execution provider by whichever plugin happens to be installed.
    project = ROOT.parent.parent
    paths = [project / tool / POLICY_RELATIVE for tool in ('.agents', '.claude', '.cursor')]
    paths = [p for p in paths if p.is_file()]
    if not paths or len({p.read_bytes() for p in paths}) != 1:
        raise ContractError('route policy missing or provider copies disagree')
    return paths[0]


def _codes(text: str) -> list[str]:
    return re.findall(r'`([^`]+)`', text)


def _table(text: str, heading: str, width: int) -> list[list[str]]:
    try:
        section = text.split(heading + '\n', 1)[1].split('\n## ', 1)[0]
    except IndexError as exc:
        raise ContractError(f'route policy missing {heading}') from exc
    rows = [[c.strip() for c in line.strip().strip('|').split('|')]
            for line in section.splitlines() if line.startswith('|') and not line.startswith('|---')]
    if len(rows) < 2 or any(len(row) != width for row in rows):
        raise ContractError(f'route policy invalid table {heading}')
    return rows[1:]


def known_skills() -> set[str]:
    names = {p.parent.name for p in (ROOT / 'skills').glob('*/SKILL.md')}
    for manifest in (ROOT / 'codex/vendor').glob('*/*/manifest.json'):
        names.update(s['name'] for s in json.loads(manifest.read_text())['skills'])
    if not names:
        project = ROOT.parent.parent
        for tool in ('.agents', '.claude', '.cursor'):
            names.update(p.parent.name for p in (project / tool / 'skills').glob('*/SKILL.md'))
        # Claude's official plugins are intentionally not copied into its project
        # landing. The released policy declares their required route vocabulary;
        # verify its shipped digest rather than inspecting HOME or mistaking a
        # missing project copy for an unknown plugin. This proves source names,
        # never installation or actual invocation. Extra skills still need a
        # visible SKILL.md or the source vendor manifest.
        history = ROOT / 'usage/bundle.json'
        if not history.is_file():
            raise ContractError('released route vocabulary unavailable')
        bundle = json.loads(history.read_text())
        released = next((m for m in bundle['releases'][-1]['members']
                         if m['source'] == str(POLICY_RELATIVE)), None)
        path = policy_path()
        if not released or hashlib.sha256(path.read_bytes()).hexdigest() != released['sha256']:
            raise ContractError('exported policy differs from its released source digest')
        text = path.read_text()
        for row in _table(text, '## 推导表', 10):
            names.update(s for s in _codes(row[-1]) if not s.startswith('@'))
        for row in _table(text, '## Provider 映射', 3):
            names.update(_codes(' '.join(row[1:])))
        for row in _table(text, '## 细化规则', 3):
            if row[2].startswith('skills '):
                names.update(_codes(row[2]))
    return names


def concrete_skills(value: object) -> list[str]:
    if not isinstance(value, str):
        raise ContractError('route.skills must be a string of concrete skills')
    skills = [s.strip() for s in value.split(',')]
    if not skills or len(set(skills)) != len(skills) or any(not re.fullmatch(r'[a-z0-9][a-z0-9-]*', s) for s in skills):
        raise ContractError('route.skills contains empty, duplicate or unexpanded skills')
    unknown = set(skills) - known_skills()
    if unknown:
        raise ContractError('route.skills unknown: ' + ', '.join(sorted(unknown)))
    return skills


def resolve_route(classification: Classification, *, provider: str,
                  change_control: str = 'production', platform_repo: bool = True,
                  splits_into_issues: bool = False, policy: Path | None = None) -> dict:
    if provider not in PROVIDERS:
        raise ContractError('route_provider must explicitly be codex, claude or cursor')
    if change_control not in ('production', 'development'):
        raise ContractError('unsupported change_control')
    path = policy or policy_path()
    data = path.read_bytes()
    text = data.decode('utf-8')
    rows = _table(text, '## 推导表', 10)
    mappings = _table(text, '## Provider 映射', 3)
    refinements = _table(text, '## 细化规则', 3)
    if [r[0] for r in rows] != ['R1', 'R2', 'R3', 'R4', 'R5'] or [r[0] for r in refinements] != ['M1','V1','S1','P1','G1']:
        raise ContractError('unsupported route policy row/rule order')
    if [m[0] for m in mappings] != list(PROVIDERS):
        raise ContractError('unsupported provider mapping')
    # Conditions are a small, explicit grammar. Prose edits to their semantics
    # require an interpreter update; no unknown condition silently passes.
    row_conditions = [
        '无 `effective_complexity`、`contract_effect: unclear` 或 `confidence: low`',
        'complex 且 `change_control: development`',
        'complex，`production`，含高风险 flag', 'complex，`production`，无高风险 flag', 'small',
    ]
    rule_conditions = ['R5 且 `change_type: bugfix`', 'R4 且 `required_docs` 含 `verification`',
                       'R3、平台仓、安全类', 'R3、项目仓',
                       'R3 或 R4，且（`change_type: feature` 或 `contract_effect: add` 或一个阶段要拆成多个 Issue）']
    if [r[1] for r in rows] != row_conditions or [r[1] for r in refinements] != rule_conditions:
        raise ContractError('unsupported route policy condition; revalidate interpreter')
    try:
        high_risk = set(_codes(text.split('**高风险 flag**：',1)[1].split('。',1)[0]))
        security = set(_codes(text.split('**安全类**：',1)[1].split('任一',1)[0]))
    except IndexError as exc:
        raise ContractError('missing policy risk definitions') from exc
    effective = classification.route(change_control=change_control).effective_complexity
    flags = set(classification.risk_flags)
    type_rule = re.search(r'`change_type` 为 (.*?) 视同含高风险 flag', text, re.S)
    if type_rule is None or not _codes(type_rule[1]):
        raise ContractError('unsupported policy risk type definition')
    risky = bool(flags & high_risk) or classification.change_type in _codes(type_rule[1])
    row_index = (0 if effective is None else 1 if effective == 'complex' and change_control == 'development'
                 else 2 if effective == 'complex' and risky else 3 if effective == 'complex' else 4)
    row = rows[row_index]
    cells = [_codes(c) for c in row[2:]]
    if any(len(c) != 1 for c in cells[:-1]) or not cells[-1]:
        raise ContractError('invalid policy route values')
    values = [c[0] for c in cells[:-1]]
    route = dict(zip(('process','tier','effort','method','verify'), values[:5]))
    route['review'] = values[5 if platform_repo else 6]
    mapping = mappings[PROVIDERS.index(provider)]
    if any(len(_codes(c)) != 1 for c in mapping[1:]):
        raise ContractError('invalid concrete provider mapping')
    obligations = dict(zip(('@plan','@completion'), [_codes(c)[0] for c in mapping[1:]]))
    skills = [obligations.get(s, s) for s in cells[-1]]
    rules = [row[0]]
    actions = [re.sub(r'`[^`]+`', 'VALUE', r[2]) for r in refinements]
    if actions != ['method 改为 VALUE', 'verify 改为 VALUE', 'review 改为 VALUE',
                   'skills 末尾加 VALUE（Matt 两轴审查，至少 spec 轴）', 'skills 最前面加 VALUE']:
        raise ContractError('unsupported policy modifier action')
    security_type = re.search(r'\*\*安全类\*\*：(.*?)任一 flag，或 `change_type: ([a-z-]+)`。', text, re.S)
    if security_type is None:
        raise ContractError('unsupported policy security type definition')
    from .contract import _required_roles, ROUTE_VALUES
    roles = _required_roles(list(classification.required_docs))
    closed = {r[0]: frozenset(_codes(r[1])) for r in _table(text, '## 取值闭集', 2)}
    if closed != ROUTE_VALUES:
        raise ContractError('unsupported policy closed sets; update contract validator')
    modifiers = {r[0]: _codes(r[2]) for r in refinements}
    if any(len(v) != 1 for v in modifiers.values()):
        raise ContractError('invalid policy modifier values')
    for key, applies, field in (
        ('M1', row_index == 4 and classification.change_type == 'bugfix', 'method'),
        ('V1', row_index == 3 and 'verification' in roles, 'verify'),
        ('S1', row_index == 2 and platform_repo and (bool(flags & security) or classification.change_type == security_type[2]), 'review'),
        ('P1', row_index == 2 and not platform_repo, 'append'),
        ('G1', row_index in (2,3) and (classification.change_type == 'feature' or classification.contract_effect == 'add' or splits_into_issues), 'prepend'),
    ):
        if applies:
            value = modifiers[key][0]
            if field == 'append': skills.append(value)
            elif field == 'prepend': skills.insert(0, value)
            else: route[field] = value
            rules.append(key)
    route['skills'] = ', '.join(concrete_skills(', '.join(skills)))
    route['confirm'] = '2'
    from .contract import validate_route
    validate_route({'route': route, 'effective_complexity': effective,
                    'contract_effect': classification.contract_effect, 'confidence': classification.confidence})
    return {'route_provider': provider, 'route': route, 'matched_rules': rules,
            'policy_sha256': hashlib.sha256(data).hexdigest(), 'policy_path': str(path)}


def repository_context(summary: Mapping[str, object], repo: Path | None = None) -> tuple[str, bool]:
    from .change_control import declared_change_control, resolve_change_control
    path = urlsplit(str(summary.get('gitea_url', ''))).path.strip('/').split('/')
    if len(path) < 4 or path[-2] != 'issues':
        raise ContractError('route context requires an exact repository Issue URL')
    owner, name = path[-4:-2]
    # A project-declared checkout carries its own change_control (#434).
    declared = declared_change_control(repo, f'{owner}/{name}') if repo is not None else None
    phase = declared if declared is not None else resolve_change_control(name)
    return phase, (owner, name) == ('admin', 'aisoft-platform')


def execution_entry(route: Mapping[str, str], provider: str) -> str:
    """Required skills and the provider's execution default are different facts."""
    mappings = _table(policy_path().read_text(), '## Provider 映射', 3)
    engines = {_codes(row[1])[0] for row in mappings}
    selected = set(concrete_skills(route['skills'])) & engines
    if len(selected) > 1:
        raise ContractError('execution entry is ambiguous; concrete route contains multiple plan engines')
    if selected:
        return selected.pop()
    return _codes(next(row[1] for row in mappings if row[0] == provider))[0]


def validate_provider_route(summary: Mapping[str, object], *, change_control: str | None = None,
                            platform_repo: bool | None = None, repo: Path | None = None) -> None:
    """Provider-aware cards are strict; historical cards remain read-only compatible."""
    if 'route_provider' not in summary:
        return
    provider = summary['route_provider']
    if provider not in PROVIDERS or not isinstance(summary.get('route'), dict):
        raise ContractError('route_provider requires a concrete provider and route card')
    from .contract import _classification_from_front_matter
    if change_control is None or platform_repo is None:
        change_control, platform_repo = repository_context(summary, repo)
    expected = resolve_route(_classification_from_front_matter(summary), provider=provider,
                             change_control=change_control, platform_repo=platform_repo)['route']
    actual = summary['route']
    concrete_skills(actual.get('skills'))
    differences = [key for key in expected if actual.get(key) != expected[key]]
    reason = str(summary.get('override_reason') or '')
    # A stale classification override is not blanket authority to change skills.
    if differences and any(not re.search(r'\b' + key + r'\b', reason) for key in differences):
        raise ContractError('route contradicts provider/policy; explicit override_reason must name: ' + ', '.join(differences))


def resolve_issue_route(repo: Path, number: int, provider: str) -> dict:
    from .contract import resolve_summary, _classification_from_front_matter
    _, summary = resolve_summary(repo, number)
    if 'route_provider' in summary and summary['route_provider'] != provider:
        raise ContractError('explicit provider conflicts with summary.route_provider')
    phase, platform = repository_context(summary, repo)
    result = resolve_route(_classification_from_front_matter(summary), provider=provider,
                           change_control=phase, platform_repo=platform)
    existing = summary.get('route') or {}
    result['differences'] = {k: {'stored': existing.get(k), 'resolved': v}
                             for k,v in result['route'].items() if existing.get(k) != v}
    if 'route_provider' in summary:
        result['policy_route'] = result['route']
        result['route'] = dict(existing)
        result['override_reason'] = summary.get('override_reason', '')
    result['historical_card'] = 'route_provider' not in summary
    result['issue'] = number
    return result
