"""Fixed review packages; mechanical completeness is not a semantic review PASS."""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from .contract import ContractError
from .route_policy import concrete_skills
from .ticket_execution import (SHA, TICKET, context, digest, git, identity,
                               receipt_identity, safe_path, working_state)
from .worktree import head_sha, is_ancestor


def in_scope(path: str, scope: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in scope)


def started(repo: Path, number: int, tid: str, issue: dict | None = None) -> tuple[dict, dict]:
    if not TICKET.fullmatch(tid):
        raise ContractError('invalid exact Ticket ID')
    path = safe_path(repo, f'.superpowers/aisoft/{number}/{tid}.json')
    if not path.is_file():
        raise ContractError('start receipt missing; cannot infer ticket BASE')
    start = json.loads(path.read_text())
    provider = start.get('identity', {}).get('provider')
    ctx = context(repo, number, provider, issue)
    if (start.get('identity') != receipt_identity(ctx) or start.get('ticket') != tid
            or tid not in ctx['plan']['tickets'] or start.get('scope') != ctx['scope']
            or start.get('route') != ctx['route'] or start.get('policy_sha256') != ctx['policy_sha256']):
        raise ContractError('start identity/plan/route/scope no longer matches')
    base = start.get('ticket_base')
    if not isinstance(base, str) or not SHA.fullmatch(base) or not is_ancestor(repo, base, head_sha(repo)):
        raise ContractError('ticket BASE must be the recorded full ancestor SHA')
    state = start.get('initial_state')
    if (not isinstance(state, dict) or set(state) != {'staged', 'unstaged', 'untracked'}
            or any(not isinstance(v, dict) for v in state.values())):
        raise ContractError('initial working-tree evidence missing')
    return ctx, start


def range_data(repo: Path, base: str, head: str) -> dict:
    if not SHA.fullmatch(base) or not is_ancestor(repo, base, head) or base == head:
        raise ContractError('review BASE must precede HEAD and be its ancestor')
    names = list(filter(None, git(repo, 'diff', '--name-only', '-z', '--no-renames', base, head).split('\0')))
    if not names:
        raise ContractError('empty net diff cannot become a review candidate')
    if git(repo, 'rev-list', '--merges', f'{base}..{head}').strip():
        raise ContractError('candidate history must remain linear')
    diff = git(repo, 'diff', '--binary', '--no-ext-diff', '--no-textconv', base, head)
    return {'base': base, 'head': head, 'commits': git(repo, 'rev-list', '--reverse', f'{base}..{head}').splitlines(),
            'files': names, 'diff_sha256': digest(diff)}


def review_candidate(repo: Path, number: int, tid: str, head: str, *,
                     issue: dict | None = None, necessary_ignored: tuple[str, ...] = ()) -> dict:
    repo = repo.resolve()
    if not SHA.fullmatch(head) or head != head_sha(repo):
        raise ContractError('candidate HEAD must be the exact current full SHA')
    ctx, start = started(repo, number, tid, issue)
    ticket_range = range_data(repo, start['ticket_base'], head)
    evidence = ctx['evidence']
    change_base = evidence.get('change_base')
    if not isinstance(change_base, str) or not SHA.fullmatch(change_base):
        raise ContractError('persisted change_base missing; never use the last ticket BASE')
    if not is_ancestor(repo, change_base, start['ticket_base']):
        raise ContractError('change_base omits the current ticket start')
    for previous in evidence.get('tickets', {}).values():
        if isinstance(previous, dict) and 'base' in previous:
            base = previous['base']
            if not isinstance(base, str) or not SHA.fullmatch(base) or not is_ancestor(repo, change_base, base):
                raise ContractError('change_base omits an earlier ticket')
    change_range = range_data(repo, change_base, head)
    outside = [p for p in change_range['files'] if not in_scope(p, ctx['scope'])]
    if outside:
        raise ContractError('committed paths outside authorized git_scope: ' + ', '.join(outside))
    entry = evidence.get('tickets', {}).get(tid, {})
    dispositions = entry.get('dirty_dispositions', {})
    if not isinstance(dispositions, dict):
        raise ContractError('dirty_dispositions must name each path and its explicit treatment')
    before, after = start['initial_state'], working_state(repo)
    omissions, unresolved = set(), set()
    for kind in before:
        for path, value in after[kind].items():
            # Any current contract-related dirt is excluded from the candidate,
            # regardless of whether it already existed at start.
            if in_scope(path, ctx['scope']) or path in change_range['files'] or before[kind].get(path) != value:
                omissions.add(path)
        for path, value in before[kind].items():
            if after[kind].get(path) != value and not dispositions.get(path):
                unresolved.add(path)
    if omissions:
        raise ContractError('staged/unstaged/untracked results omitted or ownership unclear: ' + ', '.join(sorted(omissions)))
    if unresolved:
        raise ContractError('initial dirty files changed without explicit disposition: ' + ', '.join(sorted(unresolved)))
    declared = entry.get('necessary_ignored', {})
    if not isinstance(declared, dict):
        raise ContractError('necessary_ignored must be a path-to-disposition mapping')
    for path in set(necessary_ignored) | set(declared):
        file = safe_path(repo, path)
        disposition = declared.get(path)
        if (not file.is_file() or not isinstance(disposition, dict)
                or disposition.get('sha256') != digest(file.read_bytes())
                or disposition.get('disposition') != 'archived-in-verification'):
            raise ContractError('necessary ignored result has no verified disposition: ' + path)
        proof = git(repo, 'show', head + ':' + ctx['evidence_path'])
        if disposition['sha256'] not in proof:
            raise ContractError('ignored result evidence is not in candidate HEAD: ' + path)
    # Bind both axes to exactly this payload. Machine status deliberately makes
    # no claim about path ownership semantics or unsaved editor buffers.
    sources = {}
    for path in {ctx['summary_path'], ctx['plan_path'], ctx['evidence_path']}:
        if path.startswith('issue:'):
            sources[path] = ctx['plan']['raw_hash']
        else:
            sources[path] = digest(safe_path(repo, path).read_bytes())
    summary_path = repo / ctx['summary_path']
    from .contract import resolve_documents
    docs = resolve_documents(repo, number)
    if 'spec' in docs:
        spec = summary_path.parent / docs['spec']
        sources[str(spec.relative_to(repo))] = digest(spec.read_bytes())
    package = {'identity': receipt_identity(ctx), 'ticket': tid, 'ticket_range': ticket_range,
               'change_range': change_range, 'source_documents': sources,
               'policy_sha256': ctx['policy_sha256'], 'route': ctx['route'],
               'initial_state': before, 'current_state': after, 'dirty_dispositions': dispositions,
               'necessary_ignored': declared, 'source_evidence': start.get('source_evidence'),
               'review_axes': ['Standards', 'Spec'] if 'implement' in concrete_skills(ctx['route']['skills']) else [],
               'mechanical_checks': 'PASS', 'semantic_scope_review': 'NOT REVIEWED',
               'unsaved_editor_content': 'UNKNOWN', 'review_verdict': 'NOT REVIEWED'}
    package['package_sha256'] = digest(json.dumps(package, ensure_ascii=False, sort_keys=True))
    # Detect a concurrent writer before emitting a package.
    identity(repo, number, ctx['branch'])
    if head_sha(repo) != head or working_state(repo) != after:
        raise ContractError('candidate changed during inspection')
    return package


def validate_reviews(repo: Path, package: dict, reviews: list[dict], *, issue: dict | None = None) -> None:
    """Check declared review receipts, without creating or persisting a PASS."""
    fresh = review_candidate(repo, package['identity']['issue'], package['ticket'],
                             package['ticket_range']['head'], issue=issue)
    if fresh['package_sha256'] != package['package_sha256']:
        raise ContractError('candidate package changed; old reviews do not apply')
    axes = package['review_axes']
    if len(reviews) != len(axes) or {r.get('axis') for r in reviews} != set(axes):
        raise ContractError('review axes must match this route, with no duplicate review')
    for review in reviews:
        if (review.get('base') != package['ticket_range']['base']
                or review.get('head') != package['ticket_range']['head']
                or review.get('package_sha256') != package['package_sha256']
                or review.get('verdict') != 'PASS' or not review.get('reviewer') or not review.get('evidence')):
            raise ContractError('review does not describe this exact candidate or is not PASS')
