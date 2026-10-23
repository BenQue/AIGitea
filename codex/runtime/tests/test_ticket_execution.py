"""Real-Git execution adapter fixtures; all writes stay in a temporary checkout."""
import unittest

from aisoft_loop.ticket_execution import parse_plan


class PlanTests(unittest.TestCase):
    def test_rejects_no_ticket_graph(self):
        from aisoft_loop.contract import ContractError
        with self.assertRaises(ContractError):
            parse_plan('# No executable plan')


if __name__ == '__main__':
    unittest.main()

import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch
from aisoft_loop.contract import ContractError
from aisoft_loop.ticket_execution import (prepare_ticket, digest, records, ROOT, START, END)
from aisoft_worktree_owner import claim

PLAN = '''---
issue: 57
branch: change/57-ticket-adapter
created: 2026-10-23
updated: 2026-10-23
---

# Plan
Global constraint: preserve unrelated user files; stop on scope change.

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | first slice | - | pending |
| T02 | second slice | T01 | pending |

## T01: First

- **blocked_by**: none
- **scope**: src.txt
- **AC**: AC-1
- **validation**: `python3 -m unittest first`
- **Expected**: first passes
- **constraints**: no network writes

## T02: Second

- **blocked_by**: T01
- **scope**: src.txt
- **AC**: AC-2
- **validation**: `python3 -m unittest second`
- **Expected**: second passes
- **constraints**: preserve first
'''


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name).resolve()
        self.run_git('init', '-b', 'change/57-ticket-adapter')
        self.run_git('config', 'user.name', 'Fixture')
        self.run_git('config', 'user.email', 'fixture@example.invalid')
        self.directory = self.repo / 'docs/changes/57-ticket-adapter'
        self.directory.mkdir(parents=True)
        self.summary = self.directory / 'summary-ticket-adapter-261023.md'
        self.plan = self.directory / 'plan-ticket-adapter-261023.md'
        self.verification = self.directory / 'verification-ticket-adapter-261023.md'
        self.summary.write_text('''---
issue: 57
gitea_url: http://fixture.invalid/admin/fixture/issues/57
branch: change/57-ticket-adapter
created: 2026-10-23
status: approved
change_type: feature
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
reason: fixture new feature
override_reason: ""
risk_flags: []
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-ticket-adapter-261023.md
  spec: spec-ticket-adapter-261023.md
  plan: plan-ticket-adapter-261023.md
  verification: verification-ticket-adapter-261023.md
---
''')
        (self.directory / 'spec-ticket-adapter-261023.md').write_text('---\nissue: 57\nbranch: change/57-ticket-adapter\ncreated: 2026-10-23\ngit_scope:\n  - src.txt\n  - docs/changes/57-ticket-adapter/plan-ticket-adapter-261023.md\n  - docs/changes/57-ticket-adapter/verification-ticket-adapter-261023.md\n---\n')
        self.plan.write_text(PLAN)
        self.verification.write_text('---\nissue: 57\nbranch: change/57-ticket-adapter\ncreated: 2026-10-23\n---\n# Verification\n')
        (self.repo / '.gitignore').write_text('.superpowers/\n*.ignored\n')
        (self.repo / 'src.txt').write_text('baseline\n')
        self.run_git('add', '.')
        self.run_git('commit', '-m', 'baseline')
        self.base = self.run_git('rev-parse', 'HEAD').strip()
        claim(self.repo / '.git', branch='change/57-ticket-adapter', session='fixture-owner', worktree=self.repo)
        self.env = patch.dict(os.environ, {'AISOFT_SESSION_ID': 'fixture-owner', 'HOME': str(self.repo / 'home')})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.issue = {'number': 57, 'state': 'open', 'labels': [{'name': 'approved'}],
                      'html_url': 'http://fixture.invalid/admin/fixture/issues/57',
                      'body': '## Acceptance criteria\n- AC-1: works\n'}

    def run_git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, text=True, capture_output=True).stdout

    def prepare(self, tid='T01', **kw):
        return prepare_ticket(self.repo, 57, tid, kw.pop('provider', 'codex'), issue=self.issue, **kw)

    def commit(self, text='implemented'):
        (self.repo / 'src.txt').write_text(text)
        self.run_git('add', 'src.txt')
        self.run_git('commit', '-m', text)
        return self.run_git('rev-parse', 'HEAD').strip()

    def completion(self, tid='T01', base=None, head=None):
        parsed = parse_plan(self.plan.read_text())
        task = parsed['tickets'][tid]
        return {'base': base or self.base, 'head': head or self.run_git('rev-parse', 'HEAD').strip(),
                'semantic_hash': parsed['semantic_hash'], 'validation_sha256': digest(task['validation']),
                'ac': {ac: 'PASS' for ac in task['ac']},
                'checks': [{'command': c, 'result': 'PASS', 'evidence': 'fixture observed exit 0'} for c in task['commands']]}

    def evidence(self, entry):
        self.verification.write_text('---\nissue: 57\nbranch: change/57-ticket-adapter\ncreated: 2026-10-23\n---\n# Verification\n```aisoft-execution\n' + json.dumps({'change_base': self.base, 'tickets': {'T01': entry}}) + '\n```\n')


class ParserTests(unittest.TestCase):
    def test_preserves_contract_and_ignores_only_bounded_audit_changes(self):
        p = parse_plan(PLAN)
        updated = PLAN.replace('updated: 2026-10-23', 'updated: 2026-10-24').replace('| - | pending |', '| - | done |')
        updated += '\n' + START + '\n```aisoft-execution\n{"tickets": {}}\n```\n' + END + '\n'
        # The intentionally added blank lines remain semantic; use the same envelope.
        original = PLAN + '\n\n'
        self.assertEqual(parse_plan(original)['semantic_hash'], parse_plan(updated)['semantic_hash'])
        self.assertNotEqual(p['raw_hash'], parse_plan(updated)['raw_hash'])
        for old, new in [('AC-1', 'AC-99'), ('first passes', 'different expected'), ('no network writes', 'network allowed')]:
            self.assertNotEqual(p['semantic_hash'], parse_plan(PLAN.replace(old, new))['semantic_hash'])

    def test_rejects_bad_graphs_and_fenced_body_substitutions(self):
        cases = [PLAN.replace('T02', 'T01'), PLAN.replace('| T01 | pending |', '| T99 | pending |'),
                 PLAN.replace('## T01:', '## T010:'), PLAN.replace('## T01:', '```md\n## T01:').replace('## T02:', '```\n## T02:'),
                 PLAN.replace('| - | pending |', '| T02 | pending |').replace('**blocked_by**: none', '**blocked_by**: T02'),
                 PLAN.replace('**Expected**:', '**Whatever**:')]
        for case in cases:
            with self.subTest(case=case[:90]), self.assertRaises(ContractError):
                parse_plan(case)

    def test_evidence_markers_cannot_hide_contract(self):
        for value in [START+PLAN+END, PLAN+START, PLAN+END+START, PLAN+START+START+END+END]:
            with self.assertRaises(ContractError):
                parse_plan(value)


class ExecutionTests(GitFixture):
    def test_upstream_task_start_to_brief_preserves_all_contract_text(self):
        receipt = self.prepare(provider='claude')
        self.assertEqual(receipt['ticket_base'], self.base)
        before = self.plan.read_bytes()
        script = ROOT / 'codex/vendor/superpowers/v7.0.0/skills/executing-plans/scripts/task-start'
        out = subprocess.run(['bash', str(script), str(self.repo / receipt['derived_plan']), '1'],
                             cwd=self.repo, env=dict(os.environ), capture_output=True, text=True, check=True).stdout
        brief = Path(next(l[7:] for l in out.splitlines() if l.startswith('brief: '))).read_text()
        for text in ['Task 1: T01', 'Global constraint:', 'AC-1', 'first passes', 'no network writes', 'python3 -m unittest first']:
            self.assertIn(text, brief)
        self.assertNotIn('Task 2:', brief)
        self.assertEqual(before, self.plan.read_bytes())
        self.assertEqual(self.run_git('status', '--porcelain'), '')

    def test_frontier_and_commit_validation_required(self):
        with self.assertRaises(ContractError):
            self.prepare('T02')
        self.prepare()
        self.plan.write_text(PLAN.replace('| - | pending |', '| - | done |'))
        with self.assertRaises(ContractError):
            self.prepare('T02')
        self.commit()
        entry = self.completion()
        self.evidence(entry)
        self.assertEqual(self.prepare('T02')['ticket_base'], entry['head'])
        self.assertEqual(self.prepare(resume=True)['status'], 'done-evidence-verified')
        for result in ['FAIL', 'NOT RUN']:
            entry['checks'][0]['result'] = result
            self.evidence(entry)
            with self.assertRaises(ContractError):
                self.prepare(resume=True)

    def test_resume_rejects_identity_semantics_missing_base_and_fake_complete(self):
        r = self.prepare()
        receipt = self.repo / r['receipt']
        original = receipt.read_text()
        for key, value in [('ticket_base', '0'*40), ('ticket', 'T02')]:
            changed = json.loads(original); changed[key] = value
            receipt.write_text(json.dumps(changed))
            with self.assertRaises(ContractError):
                self.prepare(resume=True)
        receipt.write_text(original)
        self.plan.write_text(PLAN.replace('first passes', 'changed acceptance'))
        with self.assertRaises(ContractError):
            self.prepare(resume=True)
        self.plan.write_text(PLAN)
        with patch.dict(os.environ, {'AISOFT_SESSION_ID': 'someone-else'}), self.assertRaises(ContractError):
            self.prepare(resume=True)
        self.assertEqual(self.prepare(resume=True)['ticket_base'], self.base)

    def test_cache_and_scratch_foreign_symlink_isolation(self):
        r = self.prepare()
        scratch = self.repo / r['scratch']
        (scratch / 'plan-path').write_text('foreign-plan.md')
        with self.assertRaises(ContractError):
            self.prepare(resume=True)
        (scratch / 'plan-path').write_text(r['derived_plan']+'\n')
        (scratch / 'task-1-brief.md').symlink_to(self.repo / 'src.txt')
        with self.assertRaises(ContractError):
            self.prepare(resume=True)
        self.assertEqual((self.repo/'src.txt').read_text(), 'baseline\n')

    def test_existing_user_dirt_is_recorded_and_preserved(self):
        (self.repo/'notes.txt').write_text('user notes')
        r = self.prepare()
        self.assertIn('notes.txt', r['initial_state']['untracked'])
        self.assertEqual((self.repo/'notes.txt').read_text(), 'user notes')
        self.assertEqual(self.run_git('diff', '--cached'), '')

    def test_small_rejected_and_development_uses_issue_without_plan(self):
        with patch('aisoft_loop.ticket_execution.repository_context', return_value=('development', False)):
            self.summary.write_text(self.summary.read_text().replace('  - plan\n', '').replace('  plan: plan-ticket-adapter-261023.md\n', '').replace('  - spec\n', '').replace('  spec: spec-ticket-adapter-261023.md\n', ''))
            self.plan.unlink()
            (self.directory / 'spec-ticket-adapter-261023.md').unlink()
            r = self.prepare()
            self.assertTrue(r['identity']['plan_path'].startswith('issue:'))
            self.assertIn('AC-1: works', (self.repo/r['derived_plan']).read_text())
        with patch('aisoft_loop.ticket_execution.resolve_issue_route', return_value={'route': {'process': 'small'}}), self.assertRaises(ContractError):
            self.prepare()
