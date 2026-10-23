"""Real-Git candidate completeness and stale-review regressions."""
import unittest
from aisoft_loop.review_candidate import review_candidate
from .test_ticket_execution import GitFixture


class CandidateTests(GitFixture):
    def test_ticket_without_own_commit_is_rejected(self):
        from aisoft_loop.contract import ContractError
        self.commit('previous ticket')
        self.prepare()
        with self.assertRaises(ContractError):
            review_candidate(self.repo, 57, 'T01', self.run_git('rev-parse','HEAD').strip(), issue=self.issue)

import json
from pathlib import Path
from unittest.mock import patch
from aisoft_loop.contract import ContractError
from aisoft_loop.review_candidate import validate_reviews
from aisoft_loop.ticket_execution import digest, records
from .test_ticket_execution import PLAN


class RangeTests(GitFixture):
    def setUp(self):
        super().setUp()
        self.write_evidence({'change_base': self.base, 'tickets': {}})
        self.run_git('add', str(self.verification.relative_to(self.repo)))
        self.run_git('commit', '-m', 'record change base')
        self.base = self.run_git('rev-parse', 'HEAD').strip()

    def write_evidence(self, data):
        header = self.verification.read_text().split('# Verification')[0]
        self.verification.write_text(header + '# Verification\n```aisoft-execution\n' + json.dumps(data) + '\n```\n')

    def candidate(self, tid='T01', head=None, **kw):
        return review_candidate(self.repo,57,tid,head or self.run_git('rev-parse','HEAD').strip(),issue=self.issue,**kw)

    def review_receipts(self, package):
        return [{'axis': axis, 'base': package['ticket_range']['base'], 'head': package['ticket_range']['head'],
                 'package_sha256': package['package_sha256'], 'verdict': 'PASS', 'reviewer': 'fixture '+axis,
                 'evidence': 'fixture only'} for axis in package['review_axes']]

    def test_range_covers_multiple_commits_and_is_not_semantic_pass(self):
        self.prepare()
        first = self.commit('first slice')
        second = self.commit('second slice')
        package = self.candidate()
        self.assertEqual(package['ticket_range']['commits'], [first, second])
        self.assertEqual(package['ticket_range']['base'], self.base)
        self.assertEqual(package['semantic_scope_review'], 'NOT REVIEWED')
        self.assertEqual(package['unsaved_editor_content'], 'UNKNOWN')
        self.assertEqual(package['review_verdict'], 'NOT REVIEWED')
        validate_reviews(self.repo, package, self.review_receipts(package), issue=self.issue)

    def test_empty_net_diff_and_missing_or_nonancestor_base_reject(self):
        r = self.prepare()
        self.commit('temporary')
        self.commit('baseline\n')
        with self.assertRaisesRegex(ContractError, 'empty net diff'):
            self.candidate()
        receipt = self.repo/r['receipt']
        data = json.loads(receipt.read_text())
        data['ticket_base'] = '0'*40
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ContractError,'ancestor'):
            self.candidate()
        receipt.unlink()
        with self.assertRaisesRegex(ContractError,'receipt missing'):
            self.candidate()

    def test_staged_unstaged_and_untracked_omissions_refuse(self):
        self.prepare()
        self.commit()
        (self.repo/'src.txt').write_text('uncommitted')
        with self.assertRaisesRegex(ContractError,'omitted'):
            self.candidate()
        self.run_git('add','src.txt')
        with self.assertRaisesRegex(ContractError,'omitted'):
            self.candidate()
        self.run_git('commit','-m','fixture finish')
        (self.repo/'new-result.txt').write_text('result')
        with self.assertRaisesRegex(ContractError,'ownership unclear'):
            self.candidate()

    def test_initial_unrelated_dirt_preserved_but_further_change_refused(self):
        note = self.repo/'notes.txt'; note.write_text('user original')
        self.prepare()
        self.commit()
        self.candidate()
        self.assertEqual(note.read_text(),'user original')
        note.write_text('user plus agent')
        with self.assertRaises(ContractError):
            self.candidate()
        self.assertEqual(note.read_text(),'user plus agent')

    def test_initial_dirty_contract_file_requires_disposition_even_when_committed(self):
        (self.repo/'src.txt').write_text('preexisting user change')
        self.prepare()
        self.commit('includes preexisting change')
        with self.assertRaisesRegex(ContractError,'explicit disposition'):
            self.candidate()

    def test_committed_outside_scope_rejected(self):
        self.prepare(); self.commit()
        (self.repo/'unapproved.txt').write_text('not authorized')
        self.run_git('add','unapproved.txt'); self.run_git('commit','-m','fixture forbidden path')
        with self.assertRaisesRegex(ContractError,'outside authorized'):
            self.candidate()

    def test_moved_head_and_axes_with_different_candidates_invalidate_reviews(self):
        self.prepare(); self.commit()
        package = self.candidate(); reviews = self.review_receipts(package)
        reviews[1]['head'] = self.base
        with self.assertRaises(ContractError):
            validate_reviews(self.repo, package, reviews, issue=self.issue)
        reviews = self.review_receipts(package)
        self.commit('review fix')
        with self.assertRaisesRegex(ContractError,'exact current'):
            validate_reviews(self.repo, package, reviews, issue=self.issue)
        with self.assertRaises(ContractError):
            self.candidate(head='HEAD')

    def test_necessary_ignored_not_automatically_exempt(self):
        self.prepare(); self.commit()
        (self.repo/'result.ignored').write_text('necessary result')
        with self.assertRaisesRegex(ContractError,'ignored result'):
            self.candidate(necessary_ignored=('result.ignored',))
        data=records(self.verification.read_text())
        data['tickets']['T01']={'necessary_ignored': {'result.ignored': {'sha256': digest('necessary result'), 'disposition':'archived-in-verification'}}}
        self.write_evidence(data)
        self.run_git('add',str(self.verification.relative_to(self.repo)))
        self.run_git('commit','-m','archive necessary result digest and disposition')
        self.assertEqual(self.candidate()['mechanical_checks'],'PASS')

    def test_final_change_range_contains_first_ticket(self):
        self.prepare(); first = self.commit('first ticket')
        self.evidence(self.completion())
        self.plan.write_text(PLAN.replace('| - | pending |', '| - | done |'))
        self.run_git('add',str(self.directory.relative_to(self.repo))); self.run_git('commit','-m','record first ticket evidence')
        self.prepare('T02'); last=self.commit('second ticket')
        package=self.candidate('T02')
        self.assertIn(first,package['change_range']['commits'])
        self.assertNotIn(first,package['ticket_range']['commits'])
        data=records(self.verification.read_text()); data['change_base']=package['ticket_range']['base']
        self.write_evidence(data);self.run_git('add',str(self.verification.relative_to(self.repo)));self.run_git('commit','-m','fixture wrong batch base')
        with self.assertRaisesRegex(ContractError,'earlier ticket'):
            self.candidate('T02')

    def test_sp_route_does_not_gain_matt_axes(self):
        self.prepare(provider='claude');self.commit()
        package=self.candidate()
        self.assertEqual(package['review_axes'],[])
        validate_reviews(self.repo, package, [], issue=self.issue)

    def test_supplied_package_tampering_cannot_keep_old_digest(self):
        self.prepare(); self.commit(); package=self.candidate()
        altered=json.loads(json.dumps(package)); altered['review_axes']=[]
        with self.assertRaises(ContractError):
            validate_reviews(self.repo,altered,[],issue=self.issue)
        altered=json.loads(json.dumps(package)); altered['ticket_range']['base']='0'*40
        with self.assertRaises(ContractError):
            validate_reviews(self.repo,altered,self.review_receipts(altered),issue=self.issue)

    def test_project_p1_matt_review_survives_sp_execution(self):
        self.summary.write_text(self.summary.read_text().replace('risk_flags: []','risk_flags:\n  - security'))
        self.run_git('add',str(self.summary.relative_to(self.repo)));self.run_git('commit','-m','fixture approved high risk')
        self.write_evidence({'change_base': self.run_git('rev-parse','HEAD').strip(), 'tickets': {}})
        self.run_git('add',str(self.verification.relative_to(self.repo)));self.run_git('commit','-m','fixture new change base')
        self.prepare(provider='claude');self.commit()
        self.assertEqual(self.candidate()['review_axes'],['Standards','Spec'])

    def test_missing_completed_dependency_cannot_truncate_batch_range(self):
        self.prepare();self.commit('first')
        self.evidence(self.completion());self.plan.write_text(PLAN.replace('| - | pending |','| - | done |'))
        self.run_git('add',str(self.directory.relative_to(self.repo)));self.run_git('commit','-m','first completed')
        start=self.prepare('T02');self.commit('second')
        self.write_evidence({'change_base':start['ticket_base'],'tickets':{}})
        self.run_git('add',str(self.verification.relative_to(self.repo)));self.run_git('commit','-m','fixture erased first evidence')
        with self.assertRaises(ContractError):
            self.candidate('T02')

    def test_development_required_set_does_not_erase_execution_default(self):
        from aisoft_loop.route_policy import execution_entry
        self.assertEqual(execution_entry({'skills':'issue-session-flow'}, 'codex'),'implement')
        self.assertEqual(execution_entry({'skills':'verification-before-completion'}, 'claude'),'executing-plans')
        self.assertEqual(execution_entry({'skills':'executing-plans, verification-before-completion'}, 'codex'),'executing-plans')
