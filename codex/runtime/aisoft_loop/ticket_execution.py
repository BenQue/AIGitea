"""Bounded Txx execution views. Git and contracts are read-only; only cache is written.

Completion evidence belongs in the mapped verification document (or summary for
routes without verification), in an `aisoft-execution` JSON fence. It is an audit
claim checked against Git and the plan, never an independent approval database.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from aisoft_worktree_owner import SESSION_RE, caller_session, read_marker
from .contract import (ContractError, _acceptance_criteria, _label_names,
                       parse_front_matter, resolve_documents, resolve_summary)
from .route_policy import ROOT, repository_context, resolve_issue_route
from .worktree import current_branch, head_sha, is_ancestor, resolve_git_dir

SHA = re.compile(r'[0-9a-f]{40}')
TICKET = re.compile(r'T(?:0[1-9]|[1-9][0-9]+)')
START = '<!-- execution-evidence:start -->'
END = '<!-- execution-evidence:end -->'


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if result.returncode:
        raise ContractError('Git read failed: ' + result.stderr.decode(errors='replace').strip())
    return result.stdout.decode('utf-8', errors='surrogateescape')


def safe_path(repo: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or not path.parts or any(p in ('.', '..') for p in path.parts):
        raise ContractError('path must stay inside exact worktree')
    cursor = repo
    for part in path.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ContractError('symlink is not an execution path: ' + relative)
    return cursor


def visible_lines(text: str) -> list[str]:
    """Mask fenced content, preserving line positions; reject unclosed fences."""
    result, fence = [], None
    for line in text.splitlines(keepends=True):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not line[match.end():].strip():
                fence = None
            result.append('\n')
        elif match:
            fence = match[1]
            result.append('\n')
        else:
            result.append(line)
    if fence:
        raise ContractError('unclosed code fence')
    return result


def field(body: str, names: str) -> str:
    raw = body.splitlines(keepends=True)
    visible = visible_lines(body)
    begin = next((i for i, line in enumerate(visible)
                  if re.match(r'^- \*\*(?:' + names + r')\*\*[:：]', line)), None)
    if begin is None:
        raise ContractError('ticket missing field: ' + names)
    end = next((i for i in range(begin+1, len(raw)) if re.match(r'^- \*\*', visible[i])), len(raw))
    value = re.sub(r'^- \*\*[^*]+\*\*[:：]\s*', '', raw[begin]) + ''.join(raw[begin+1:end])
    if not value.strip():
        raise ContractError('empty ticket field: ' + names)
    return value.strip()


def ids(text: str) -> list[str]:
    values = re.findall(r'\bT[0-9]+\b', text)
    if any(not TICKET.fullmatch(v) for v in values) or len(values) != len(set(values)):
        raise ContractError('ambiguous or duplicate ticket ID')
    return values


def _without_evidence(text: str) -> str:
    if START not in text and END not in text:
        return text
    if text.count(START) != 1 or text.count(END) != 1:
        raise ContractError('execution evidence markers must be one nonnested pair')
    before, rest = text.split(START)
    if END not in rest:
        raise ContractError('reversed execution evidence markers')
    evidence, after = rest.split(END)
    # The explicit region is allowed only directly inside its standalone audit
    # section. It cannot start halfway through a ticket or global constraint.
    visible_before = ''.join(visible_lines(before))
    if not re.search(r'^## (?:执行证据|Execution evidence)\s*\Z', visible_before, re.M):
        raise ContractError('evidence markers must directly follow the execution evidence heading')
    visible_evidence = ''.join(visible_lines(evidence))
    if re.search(r'^#{1,6} |^\||^- \*\*', visible_evidence, re.M):
        raise ContractError('evidence markers cannot enclose graph, task, fields or constraints')
    return before + after


def parse_plan(text: str) -> dict:
    clean = _without_evidence(text)
    lines = clean.splitlines(keepends=True)
    visible = visible_lines(clean)
    graph_starts = [i for i, l in enumerate(visible) if l.strip() == '## Ticket graph']
    if len(graph_starts) != 1:
        raise ContractError('exactly one Ticket graph is required')
    start = graph_starts[0]
    end = next((i for i in range(start+1, len(lines)) if visible[i].startswith('## ')), len(lines))
    rows, status_lines = {}, []
    for i in range(start+1, end):
        line = visible[i]
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if cells == ['Ticket', 'Delivers', 'Blocked by', 'Status'] or all(re.fullmatch(r'[- :]+', c) for c in cells):
            continue
        if len(cells) != 4 or not TICKET.fullmatch(cells[0]) or cells[0] in rows:
            raise ContractError('invalid or duplicate Ticket graph row')
        deps = ids(cells[2])
        if not deps and cells[2] not in ('-', '无', 'none'):
            raise ContractError('invalid dependency cell')
        if cells[3] not in ('pending', 'in-progress', 'done'):
            raise ContractError('unknown ticket status')
        rows[cells[0]] = {'delivers': cells[1], 'deps': deps, 'status': cells[3]}
        status_lines.append(i)
    if not rows:
        raise ContractError('empty Ticket graph')
    sections = []
    for i, line in enumerate(visible):
        m = re.match(r'^## (T[0-9]+)(?=[:： \t]|\s*$)', line)
        if m:
            if not TICKET.fullmatch(m[1]):
                raise ContractError('invalid ticket heading')
            finish = next((j for j in range(i+1, len(lines)) if visible[j].startswith('## ')), len(lines))
            sections.append((m[1], i, finish))
    if len(sections) != len(rows) or {s[0] for s in sections} != set(rows):
        raise ContractError('Ticket graph/body IDs must match exactly once')
    occupied = set()
    for tid, begin, finish in sections:
        body = ''.join(lines[begin:finish])
        deps = ids(field(body, 'blocked_by'))
        if deps != rows[tid]['deps'] or tid in deps or set(deps) - rows.keys():
            raise ContractError('body/graph dependency mismatch or unknown dependency')
        scope = field(body, '交付/范围|scope')
        ac_ids = set()
        for first, last in re.findall(r'\bAC-([0-9]+)\b(?:\s*[-–—]\s*AC-([0-9]+)\b)?', field(body, 'AC')):
            begin_ac, end_ac = int(first), int(last or first)
            if end_ac < begin_ac or end_ac - begin_ac > 1000:
                raise ContractError('invalid or excessive AC range; enumerate criteria explicitly')
            ac_ids.update(f'AC-{n}' for n in range(begin_ac, end_ac + 1))
        ac = sorted(ac_ids)
        validation = field(body, '验证|validation')
        expected = field(body, 'Expected')
        constraints = field(body, '约束/停止|停止条件|constraints')
        if not ac:
            raise ContractError('ticket needs explicit AC identifiers')
        rows[tid].update(body=body, scope=scope, ac=ac, validation=validation,
                         commands=re.findall(r'`([^`]+)`', validation), expected=expected,
                         constraints=constraints)
        occupied.update(range(begin, finish))
    visiting, done = set(), set()
    def visit(tid):
        if tid in visiting:
            raise ContractError('ticket dependency cycle')
        if tid in done:
            return
        visiting.add(tid)
        for dep in rows[tid]['deps']:
            visit(dep)
        visiting.remove(tid)
        done.add(tid)
    for tid in rows:
        visit(tid)
    semantic_lines = list(lines)
    for i in status_lines:
        cells = semantic_lines[i].strip().strip('|').split('|')
        cells[-1] = ' <execution-status> '
        semantic_lines[i] = '|' + '|'.join(cells) + '|\n'
    # Only top-level YAML front matter's updated value is audit-only.
    if semantic_lines and semantic_lines[0].strip() == '---':
        fm_end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), 0)
        for i in range(1, fm_end):
            if re.match(r'^updated:', semantic_lines[i]):
                semantic_lines[i] = 'updated: <audit-date>\n'
    return {'tickets': rows, 'global': ''.join(l for i, l in enumerate(lines) if i not in occupied),
            'raw_hash': digest(text), 'semantic_hash': digest(''.join(semantic_lines))}


def records(text: str) -> dict:
    # These are deliberately typed fences, not a search for arbitrary PASS text.
    matches = re.findall(r'^```aisoft-execution\n(.*?)\n```\s*$', text, re.M | re.S)
    if len(matches) > 1:
        raise ContractError('duplicate execution evidence records')
    if not matches:
        return {}
    try:
        data = json.loads(matches[0])
    except ValueError as exc:
        raise ContractError('invalid execution evidence JSON') from exc
    if not isinstance(data, dict) or set(data) - {'change_base', 'tickets', 'scope_amendments'} or not isinstance(data.get('tickets', {}), dict):
        raise ContractError('invalid execution evidence structure')
    return data


def read_issue(repo: Path, number: int) -> dict:
    """Use the existing project resolver and the one typed broker operation."""
    library = ROOT / 'codex/agent/aisoft-project-target.sh'
    script = 'source "$1"; aisoft_resolve_project_target "$2" "$3" "" || { printf "%s\\n" "$AISOFT_PROJECT_TARGET_ERROR" >&2; exit 2; }; printf "%s\\n%s\\n%s\\n%s\\n" "$AISOFT_PROJECT_ID" "$AISOFT_PROJECT_REPOSITORY" "$AISOFT_ACCESS_SOURCE" "$AISOFT_ACCESS_ENTRY"'
    result = subprocess.run(['bash', '-c', script, 'aisoft-ticket', str(library), str(ROOT/'codex/tools'), str(repo)], capture_output=True, text=True)
    if result.returncode:
        raise ContractError('project resolution failed: ' + result.stderr.strip())
    project, repository, source, entry = (result.stdout.rstrip('\n').split('\n') + ['', ''])[:4]
    if source == 'project':
        # Project-declared source (#434): the entry reads .aisoft/project.json from its cwd.
        result = subprocess.run([entry, '--operation', 'gitea.issue.read', '--number', str(number)],
                                cwd=repo, capture_output=True, text=True)
    else:
        result = subprocess.run(['/usr/local/libexec/aisoft/host-access-broker', '--project', project,
                                 '--operation', 'gitea.issue.read', '--number', str(number)], capture_output=True, text=True)
    if result.returncode:
        raise ContractError('typed Issue read failed: ' + result.stderr.strip())
    issue = json.loads(result.stdout)
    if issue.get('repository', {}).get('name') != repository:
        raise ContractError('broker Issue repository mismatch')
    return issue


def identity(repo: Path, number: int, branch: str) -> dict:
    marker = read_marker(resolve_git_dir(repo))
    if (not caller_session() or marker.session != caller_session() or marker.issue != number
            or marker.branch != branch or current_branch(repo) != branch or Path(marker.worktree).resolve() != repo):
        raise ContractError('Issue/branch/owner/worktree identity mismatch')
    return {'issue': number, 'branch': branch, 'owner': marker.session, 'worktree': str(repo)}


def working_state(repo: Path) -> dict:
    """NUL-delimited paths and content hashes; no shell and no credential contents."""
    state = {}
    for kind, args in [('staged', ['diff', '--cached', '--name-only', '-z', '--no-renames']),
                       ('unstaged', ['diff', '--name-only', '-z', '--no-renames']),
                       ('untracked', ['ls-files', '--others', '--exclude-standard', '-z'])]:
        entries = {}
        for name in filter(None, git(repo, *args).split('\0')):
            path = repo / name
            if path.is_symlink():
                value = 'symlink:' + os.readlink(path)
            elif path.is_file():
                value = digest(path.read_bytes())
            else:
                value = '<absent-or-non-file>'
            if kind == 'staged':
                value += ':' + digest(git(repo, 'diff', '--cached', '--binary', '--', name))
            entries[name] = value
        state[kind] = entries
    return state


def context(repo: Path, number: int, provider: str, issue: dict | None = None) -> dict:
    repo = repo.resolve()
    if Path(git(repo, 'rev-parse', '--show-toplevel').strip()).resolve() != repo:
        raise ContractError('--repo must be the exact worktree root')
    summary_path, summary = resolve_summary(repo, number)
    route = resolve_issue_route(repo, number, provider)
    if route['route']['process'] not in ('complex-production', 'complex-development'):
        raise ContractError('ticket adapter only applies to resolved complex execution; small stays small-direct')
    issue = read_issue(repo, number) if issue is None else issue
    if issue.get('number') != number or issue.get('state') != 'open' or 'approved' not in _label_names(issue.get('labels')):
        raise ContractError('open approved Issue required; triage is not startup approval')
    if summary.get('status') != 'approved' or issue.get('html_url') != summary.get('gitea_url'):
        raise ContractError('approved summary and exact Issue URL must agree')
    ident = identity(repo, number, str(summary['branch']))
    documents = resolve_documents(repo, number)
    directory = summary_path.parent
    phase, _ = repository_context(summary, repo)
    if phase == 'development':
        body = str(issue.get('body') or '')
        ac = _acceptance_criteria(body)
        if not ac:
            raise ContractError('development complex requires Issue acceptance criteria')
        # Keep all Issue constraints, not just the bullet identifiers.
        synthetic = ('## Ticket graph\n\n| Ticket | Delivers | Blocked by | Status |\n|---|---|---|---|\n'
                     '| T01 | Issue AC | - | pending |\n\n## T01: Issue execution\n'
                     '- **blocked_by**: none\n- **scope**: Issue AC\n- **AC**: ' + ', '.join(f'AC-{i+1}' for i in range(len(ac))) +
                     '\n- **validation**: Check every Issue AC and record actual results\n- **Expected**: All AC pass\n'
                     '- **constraints**: Original Issue body below; original approval and two confirmation points apply\n\n')
        # Issue headings are quoted so they cannot become synthetic plan headings.
        text = synthetic + '\n'.join('> '+line for line in body.splitlines()) + '\n'
        plan_path = 'issue:' + str(summary['gitea_url'])
    else:
        plan = safe_path(repo, str((directory / documents['plan']).relative_to(repo)))
        text = plan.read_text()
        plan_path = str(plan.relative_to(repo))
    parsed = parse_plan(text)
    evidence_path = directory / documents.get('verification', documents['summary'])
    evidence = records(evidence_path.read_text()) if evidence_path.exists() else {}
    spec = directory / documents.get('spec', documents['summary'])
    scope = parse_front_matter(spec.read_text()).get('git_scope', []) if spec.exists() else summary.get('git_scope', [])
    if not isinstance(scope, list) or not all(isinstance(p, str) for p in scope):
        raise ContractError('git_scope must be a path list')
    for path in scope:
        safe_path(repo, path)
    return {**ident, 'provider': provider, 'route': route['route'], 'policy_sha256': route['policy_sha256'],
            'plan_path': plan_path, 'plan': parsed, 'evidence': evidence, 'scope': scope,
            'evidence_path': str(evidence_path.relative_to(repo)), 'summary_path': str(summary_path.relative_to(repo))}


def receipt_identity(ctx: dict) -> dict:
    return {**{k: ctx[k] for k in ('issue', 'branch', 'owner', 'worktree', 'provider', 'plan_path')},
            'semantic_hash': ctx['plan']['semantic_hash']}


def scope_matches(ctx: dict, start: dict) -> bool:
    """Preserve the original receipt across an explicitly recorded expansion.

    The existing approved contract remains authoritative. This audit reference
    records the caller's human authorization; it is not a new approval engine.
    Unrecorded drift or removal of any original path still fails closed.
    """
    original, current = start.get('scope'), ctx['scope']
    if original == current:
        return True
    if (not isinstance(original, list) or not all(isinstance(p, str) for p in original)
            or not set(original) < set(current)):
        return False
    amendments = ctx['evidence'].get('scope_amendments', [])
    if not isinstance(amendments, list):
        return False
    return any(isinstance(a, dict) and a.get('from_scope') == original and a.get('to_scope') == current
               and isinstance(a.get('authorization'), str) and bool(a['authorization'].strip())
               for a in amendments)


def completed(repo: Path, ctx: dict, tid: str) -> bool:
    entry = ctx['evidence'].get('tickets', {}).get(tid)
    task = ctx['plan']['tickets'][tid]
    if not isinstance(entry, dict):
        raise ContractError(f'{tid}: completion requires commit and validation evidence')
    start = entry.get('start')
    expected_identity = receipt_identity(ctx)
    historical_owner = start.get('identity', {}).get('owner') if isinstance(start, dict) and isinstance(start.get('identity'), dict) else None
    if not isinstance(historical_owner, str) or not SESSION_RE.fullmatch(historical_owner):
        raise ContractError(f'{tid}: historical execution owner is missing')
    # A claimed successor may consume completed dependencies without rewriting
    # their historical owner. Resuming an unfinished ticket stays exact-owner.
    expected_identity['owner'] = historical_owner
    if (not isinstance(start, dict) or start.get('identity') != expected_identity
            or start.get('ticket') != tid or not scope_matches(ctx, start)
            or start.get('policy_sha256') != ctx['policy_sha256'] or start.get('route') != ctx['route']
            or not isinstance(start.get('initial_state'), dict) or not start.get('raw_plan_sha256')):
        raise ContractError(f'{tid}: completion needs matching persisted start receipt')
    cached = safe_path(repo, f'.superpowers/aisoft/{ctx["issue"]}/{tid}.json')
    if cached.exists() and json.loads(cached.read_text()) != start:
        raise ContractError(f'{tid}: completion disagrees with original start receipt')
    base, head = entry.get('base', ''), entry.get('head', '')
    if base != start.get('ticket_base'):
        raise ContractError(f'{tid}: completion BASE is not this ticket start')
    if (not isinstance(base, str) or not isinstance(head, str) or not SHA.fullmatch(base) or not SHA.fullmatch(head)
            or base == head or not is_ancestor(repo, base, head) or not is_ancestor(repo, head, head_sha(repo))
            or not git(repo, 'diff', '--name-only', base, head)):
        raise ContractError(f'{tid}: invalid completion commit range')
    if entry.get('semantic_hash') != ctx['plan']['semantic_hash'] or entry.get('validation_sha256') != digest(task['validation']) or entry.get('ac') != {ac: 'PASS' for ac in task['ac']}:
        raise ContractError(f'{tid}: acceptance/validation evidence does not match the plan')
    checks = entry.get('checks')
    if not isinstance(checks, list) or not checks or any(not isinstance(c, dict) or c.get('result') != 'PASS' or not c.get('evidence') or not c.get('command') for c in checks):
        raise ContractError(f'{tid}: required checks missing, FAIL or NOT RUN')
    if set(task['commands']) - {c['command'] for c in checks}:
        raise ContractError(f'{tid}: missing required command evidence')
    return True


def _render(ctx: dict) -> str:
    parts = ['# Derived execution view (regenerate; canonical Txx remains authoritative)\n']
    for i, (tid, task) in enumerate(ctx['plan']['tickets'].items(), 1):
        # task-brief recognizes only backtick fences. Convert fence delimiters in
        # a copy; all content, including fake headings inside fences, is retained.
        text = ctx['plan']['global'] + '\n' + task['body']
        # The pinned awk toggles on delimiters even inside an unlike fence.
        # Reject any inner delimiter that is not the canonical closing fence
        # before converting tildes, so example text can never escape its block.
        fence = None
        for line in text.splitlines():
            marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
            if not marker:
                continue
            delimiter, tail = marker.groups()
            if fence is None:
                fence = delimiter
            elif delimiter[0] == fence[0] and len(delimiter) >= len(fence) and not tail.strip():
                fence = None
            else:
                raise ContractError('fence form unsupported by pinned task-brief; nested delimiter')
        text = re.sub(r'^ {0,3}~{3,}(.*)$', r'```\1', text, flags=re.M)
        # The pinned awk toggles on every column-zero backtick delimiter. Reject
        # Markdown fence forms it cannot represent faithfully instead of truncating.
        if any(re.match(r'^ {1,3}`{3,}|^`{4,}', line) for line in text.splitlines()):
            raise ContractError('fence form unsupported by pinned task-brief; use column-zero triple backticks')
        # Genuine Task headings in prose would split the upstream brief.
        if re.search(r'^#+\s+Task\s+[0-9]+', ''.join(visible_lines(text)), re.M):
            raise ContractError('canonical Task N heading conflicts with derived view')
        parts.append(f'\n### Task {i}: {tid}\n\n' + text)
    return ''.join(parts)


def source_evidence() -> dict:
    manifests = sorted((ROOT / 'codex/vendor').glob('*/*/manifest.json'))
    if manifests:
        return {str(p.relative_to(ROOT)): {'sha256': digest(p.read_bytes()),
                'tag': json.loads(p.read_text()).get('tag'), 'commit': json.loads(p.read_text()).get('commit')}
                for p in manifests}
    bundle = ROOT / 'usage/bundle.json'
    if not bundle.is_file():
        raise ContractError('source bundle provenance unavailable')
    return {'bundle_sha256': digest(bundle.read_bytes()), 'evidence_layer': 'exported-source; not live session'}


def prepare_ticket(repo: Path, number: int, tid: str, provider: str, *, resume: bool = False, issue: dict | None = None) -> dict:
    repo = repo.resolve()
    ctx = context(repo, number, provider, issue)
    tasks = ctx['plan']['tickets']
    if tid not in tasks:
        raise ContractError('unknown exact Ticket ID')
    for dep in tasks[tid]['deps']:
        if tasks[dep]['status'] != 'done' or not completed(repo, ctx, dep):
            raise ContractError('dependency is not complete: ' + dep)
    for done, task in tasks.items():
        if task['status'] == 'done':
            completed(repo, ctx, done)
    key = receipt_identity(ctx)
    cache = safe_path(repo, f'.superpowers/aisoft/{number}')
    receipt = safe_path(repo, str(cache.relative_to(repo) / (tid + '.json')))
    slug = f'issue-{number}-{digest(ctx["owner"])[:16]}-{ctx["plan"]["semantic_hash"][:16]}'
    derived = safe_path(repo, str(cache.relative_to(repo) / (slug + '.md')))
    scratch = safe_path(repo, '.superpowers/sdd/' + slug)
    plan_id = str(derived.relative_to(repo))
    if scratch.exists():
        marker = safe_path(repo, str(scratch.relative_to(repo) / 'plan-path'))
        owner = safe_path(repo, str(scratch.relative_to(repo) / 'aisoft-identity.json'))
        if not marker.is_file() or marker.read_text().strip() != plan_id or not owner.is_file() or json.loads(owner.read_text()) != key:
            raise ContractError('foreign or unregistered sdd scratch; refusing adoption')
        for entry in scratch.rglob('*'):
            if entry.is_symlink():
                raise ContractError('symlink in sdd scratch')
    if resume:
        if not receipt.is_file():
            raise ContractError('start receipt missing; never infer BASE from HEAD~1')
        saved = json.loads(receipt.read_text())
        if (saved.get('identity') != key or saved.get('ticket') != tid or not scope_matches(ctx, saved)
                or saved.get('policy_sha256') != ctx['policy_sha256'] or saved.get('route') != ctx['route']):
            raise ContractError('resume identity/semantic contract mismatch')
        base = saved.get('ticket_base', '')
        if not isinstance(base, str) or not SHA.fullmatch(base) or not is_ancestor(repo, base, head_sha(repo)):
            raise ContractError('resume BASE is missing or not an ancestor')
        if saved.get('derived_plan') != plan_id or saved.get('scratch') != str(scratch.relative_to(repo)):
            raise ContractError('resume cache path mismatch')
    else:
        if receipt.exists() or tasks[tid]['status'] == 'done':
            raise ContractError('ticket already started/done; use --resume with original receipt')
        saved = {'identity': key, 'ticket': tid, 'ticket_base': head_sha(repo),
                 'raw_plan_sha256': ctx['plan']['raw_hash'], 'scope': ctx['scope'],
                 'initial_state': working_state(repo), 'derived_plan': plan_id,
                 'scratch': str(scratch.relative_to(repo)), 'policy_sha256': ctx['policy_sha256'],
                 'route': ctx['route'], 'source_evidence': source_evidence(),
                 'model_configuration': 'not observed by helper; caller records actual model/effort in verification'}
    view = _render(ctx)
    # Reject existing foreign contents before creating any file. A legitimate
    # resume may regenerate its view after audit-only plan state updates.
    if derived.exists() and not receipt.exists():
        registered = False
        for prior in cache.glob('T*.json'):
            safe_path(repo, str(prior.relative_to(repo)))
            value = json.loads(prior.read_text())
            registered |= value.get('identity') == key and value.get('derived_plan') == plan_id
        if not registered:
            raise ContractError('unregistered derived plan exists')
    cache.mkdir(parents=True, exist_ok=True)
    # Refuse a non-ignored cache rather than editing the user's ignore rules.
    if subprocess.run(['git', '-C', str(repo), 'check-ignore', '-q', str(cache / 'probe')]).returncode:
        raise ContractError('execution cache must already be ignored')
    scratch.mkdir(parents=True, exist_ok=True)
    safe_path(repo, str(scratch.relative_to(repo) / 'plan-path')).write_text(plan_id + '\n')
    safe_path(repo, str(scratch.relative_to(repo) / 'aisoft-identity.json')).write_text(json.dumps(key, sort_keys=True))
    derived.write_text(view)
    if not resume:
        with receipt.open('x') as stream:
            json.dump(saved, stream, indent=2, ensure_ascii=False)
    return {**saved, 'current_raw_plan_sha256': ctx['plan']['raw_hash'],
            'task_number': list(tasks).index(tid)+1, 'receipt': str(receipt.relative_to(repo)),
            'status': 'done-evidence-verified' if tasks[tid]['status'] == 'done' else 'prepared',
            'limits': 'preparation is not validation or review; helper executes no task commands'}
