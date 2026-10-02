"""#286: validate both dependency gates and persisted wait behaviour."""
import json
import subprocess
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

from aisoft_host_access.broker import BrokerError, HostAccessBroker, ResolvedCredential
from aisoft_host_access.contract import AccessContractError, load_access_contract
from aisoft_loop.controller import Controller
from tests.test_dependencies import ROOT, access, issue


class DependencyIntegrationTests(unittest.TestCase):
    def controller_fixture(self, values):
        from tests.test_controller import (
            ControllerTests, FakeGitea, FakeProvider, FakeVerifier, FakeGit,
            provider_result, verification,
        )
        from aisoft_host_access.runner import DependencyReader
        fixture = ControllerTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        summary = fixture.repo / 'docs/changes/8/00-summary.md'
        summary.write_text(summary.read_text().replace(
            'status: analyzed', 'depends_on:\n' + ''.join(f'  - {ref}\n' for ref in values)
            + 'status: analyzed'))
        gitea = FakeGitea(['success'] * 4)
        gitea.repository_identity = ('admin', 'SFMDigitalBoard')
        gitea.base_url = access().governance.base_url
        gitea.dependency_issues[284] = {'number': 284, 'state': 'closed', 'labels': ['deployed']}
        provider = FakeProvider([provider_result()])
        controller = fixture.controller(provider=provider, gitea=gitea,
                                        verifier=FakeVerifier([verification(True)]),
                                        git=FakeGit([('src/change.txt',)]))
        response = {'repository': 'admin/aisoft-platform', 'number': 284,
                    'reference': 'admin/aisoft-platform#284', 'state': 'open',
                    'labels': ['completed']}
        calls = []

        def command(argv, *, cwd):
            calls.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, json.dumps(response), '')

        controller.dependency_reader = DependencyReader(access(), 'sfm-digital-board',
                                                       command_runner=command)
        return fixture, controller, provider, gitea, response, calls

    def test_collision_wait_unlock_restart_and_qualified_evidence(self):
        from aisoft_loop.state import TerminalState
        fixture, controller, provider, gitea, response, calls = self.controller_fixture(
            ['admin/aisoft-platform#284'])
        first = controller.run(8)
        self.assertEqual(first.terminal_state, TerminalState.CONTINUE)
        self.assertIn('admin/aisoft-platform#284', first.message)
        self.assertIn('- admin/aisoft-platform#284', gitea.created_prs[0]['body'])
        state = controller.state_store.load(8)
        self.assertEqual(state['waiting_dependencies'], ['admin/aisoft-platform#284'])
        self.assertTrue(any('admin/aisoft-platform#284' in c for c in gitea.comments))
        # Recreate Controller against the persisted state, as after a process restart.
        resumed = Controller(repo=fixture.repo, gitea=gitea, provider=provider,
                             verifier=controller.verifier, git=controller.git,
                             state_store=controller.state_store, lock=controller.lock,
                             dependency_reader=controller.dependency_reader)
        self.assertEqual(resumed.run(8).terminal_state, TerminalState.CONTINUE)
        self.assertEqual(sum(c.startswith('Waiting for') for c in gitea.comments), 1)
        response['state'] = 'closed'
        self.assertEqual(resumed.run(8).terminal_state, TerminalState.READY_FOR_REVIEW)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(len(gitea.created_prs), 1)
        self.assertTrue(all(argv[-1] == 'admin/aisoft-platform#284' for argv in calls))

    def test_dependency_erasure_during_wait_requires_human(self):
        from aisoft_loop.state import TerminalState
        fixture, controller, provider, gitea, _, _ = self.controller_fixture(['admin/aisoft-platform#284'])
        self.assertEqual(controller.run(8).terminal_state, TerminalState.CONTINUE)
        summary = fixture.repo / 'docs/changes/8/00-summary.md'
        summary.write_text(summary.read_text().replace('depends_on:\n  - admin/aisoft-platform#284',
                                                       'depends_on: []'))
        self.assertEqual(controller.run(8).terminal_state, TerminalState.NEEDS_HUMAN_DECISION)
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(len(gitea.created_prs), 1)

    def test_dependency_erasure_while_ci_pending_requires_human(self):
        from aisoft_loop.state import TerminalState
        fixture, controller, provider, gitea, response, _ = self.controller_fixture(['admin/aisoft-platform#284'])
        gitea.statuses = ['pending', 'success']
        self.assertEqual(controller.run(8).terminal_state, TerminalState.CONTINUE)
        self.assertEqual(controller.state_store.load(8)['stage'], 'awaiting_ci')
        summary = fixture.repo / 'docs/changes/8/00-summary.md'
        summary.write_text(summary.read_text().replace('depends_on:\n  - admin/aisoft-platform#284',
                                                       'depends_on: []'))
        self.assertEqual(controller.run(8).terminal_state, TerminalState.NEEDS_HUMAN_DECISION)
        self.assertEqual(response['state'], 'open')
        self.assertEqual(len(provider.requests), 1)
        self.assertEqual(len(gitea.created_prs), 1)

    def test_untrusted_source_cannot_read_or_comment_before_binding(self):
        from aisoft_loop.state import TerminalState
        for source in (('other', 'SFMDigitalBoard'), ('admin', 'LocalWMS')):
            _, controller, provider, gitea, _, calls = self.controller_fixture(['admin/aisoft-platform#284'])
            gitea.repository_identity = source
            with self.subTest(source=source), patch.object(gitea, 'get_issue') as read:
                self.assertEqual(controller.run(8).terminal_state, TerminalState.NEEDS_HUMAN_DECISION)
                read.assert_not_called()
                self.assertEqual(gitea.comments, [])
                self.assertEqual(gitea.created_prs, [])
                self.assertEqual(provider.requests, [])
                self.assertEqual(calls, [])

    def test_audit_identity_requires_explicit_non_admin_before_target_read(self):
        for admin in (None, 'true', 1, [], {}):
            requests = []

            def transport(method, url, headers, body, *, response_limit=None, follow_redirects=True):
                requests.append(url)
                return 200, {}, json.dumps({'login': 'audit', 'is_admin': admin}).encode()

            b = HostAccessBroker(access(), transport=transport)
            with self.subTest(admin=admin), patch.object(b.credentials, 'resolve',
                    return_value=ResolvedCredential('audit', 'fixture-audit')):
                with self.assertRaises(BrokerError) as caught:
                    b.execute('sfm-digital-board', 'gitea.dependency.read', reference='admin/aisoft-platform#284')
                self.assertEqual(caught.exception.code, 'IDENTITY_MISMATCH')
                self.assertEqual(requests, [access().governance.base_url + '/api/v1/user'])

    def test_denied_binding_and_canonical_alias_rejected_before_provider(self):
        from aisoft_loop.state import TerminalState
        for values in (['admin/LocalWMS#284'], [284, 'admin/SFMDigitalBoard#284'],
                       ['admin/SFMDigitalBoard#8']):
            with self.subTest(values=values):
                _, controller, provider, gitea, _, calls = self.controller_fixture(values)
                result = controller.run(8)
                self.assertEqual(result.terminal_state, TerminalState.NEEDS_HUMAN_DECISION)
                self.assertEqual(provider.requests, [])
                self.assertEqual(gitea.created_prs, [])
                self.assertEqual(calls, [])

    def test_unavailable_or_malformed_surface_blocks_before_provider(self):
        from aisoft_loop.state import TerminalState
        for failure in ('missing', '403', '404', 'transport', 'json', 'identity'):
            with self.subTest(failure=failure):
                _, controller, provider, gitea, _, _ = self.controller_fixture(['admin/aisoft-platform#284'])

                def command(argv, *, cwd):
                    if failure in ('missing', 'transport'):
                        raise OSError('fixture unavailable')
                    if failure in ('403', '404'):
                        return subprocess.CompletedProcess(argv, 20, '', 'fixture denied')
                    return subprocess.CompletedProcess(argv, 0, '{' if failure == 'json' else '{}', '')

                controller.dependency_reader._command_runner = command
                self.assertEqual(controller.run(8).terminal_state, TerminalState.BLOCKED_EXTERNAL)
                self.assertEqual(provider.requests, [])
                self.assertEqual(gitea.created_prs, [])

    def test_mac_vm_adapter_fixed_surface_and_zero_fallback(self):
        from aisoft_host_access.runner import DependencyReader, BROKER_EXECUTABLE
        from aisoft_host_access.dependencies import project_issue
        for cwd in ('/Users/fixture/Projects/SFMDigitalBoard', '/home/fixture/SFMDigitalBoard'):
            calls = []

            def command(argv, *, cwd):
                calls.append((list(argv), cwd))
                return subprocess.CompletedProcess(argv, 0, json.dumps(
                    project_issue(issue(), ('admin', 'aisoft-platform', 284))), '')

            reader = DependencyReader(access(), 'sfm-digital-board', command_runner=command)
            reader._cwd = cwd
            reader.read('admin/aisoft-platform#284')
            self.assertEqual(calls, [([BROKER_EXECUTABLE, '--project', 'sfm-digital-board',
                                      '--operation', 'gitea.dependency.read', '--reference',
                                      'admin/aisoft-platform#284'], cwd)])

    def test_bounded_broker_failures_preserve_no_body_and_no_mutations(self):
        for failure in ('403', '404', 'transport', 'json', 'pr', 'identity', 'oversize', 'audit-admin'):
            requests = []

            def transport(method, url, headers, body, *, response_limit=None, follow_redirects=True):
                requests.append((method, url, headers['Authorization'], response_limit))
                self.assertIsNotNone(response_limit)
                self.assertFalse(follow_redirects)
                if url.endswith('/user'):
                    return 200, {}, json.dumps({'login': 'audit', 'is_admin': failure == 'audit-admin'}).encode()
                if failure in ('403', '404'):
                    return int(failure), {}, b'{}'
                if failure == 'transport':
                    raise OSError('fixture unavailable')
                value = issue()
                if failure == 'pr':
                    value['pull_request'] = {}
                if failure == 'identity':
                    value['number'] = 285
                data = b'{' if failure == 'json' else json.dumps(value).encode()
                if failure == 'oversize':
                    data = b'x' * (256 * 1024 + 1)
                return 200, {}, data

            b = HostAccessBroker(access(), transport=transport)
            with self.subTest(failure=failure), patch.object(
                    b.credentials, 'resolve', return_value=ResolvedCredential('audit', 'fixture-audit')):
                with self.assertRaises(BrokerError):
                    b.execute('sfm-digital-board', 'gitea.dependency.read', reference='admin/aisoft-platform#284')
                self.assertTrue(all(method == 'GET' and token == 'token fixture-audit'
                                    for method, _, token, _ in requests))

    def test_dependency_transport_does_not_follow_location_headers(self):
        from urllib.request import Request
        from aisoft_host_access.broker import _default_transport, _NoDependencyRedirect
        request = Request('http://manifest-fixed/api/v1/user')
        self.assertIsNone(_NoDependencyRedirect().redirect_request(
            request, None, 302, 'Found', {}, 'http://foreign-host/steal'))
        response = MagicMock()
        response.status = 302
        response.headers.raw_items.return_value = [('Location', 'http://foreign-host/steal')]
        response.read.return_value = b'{}'
        response.__enter__.return_value = response
        opener = MagicMock()
        opener.open.return_value = response
        with patch('aisoft_host_access.broker.build_opener', return_value=opener) as build, \
                patch('aisoft_host_access.broker.urlopen') as fallback:
            status, _, _ = _default_transport('GET', 'http://manifest-fixed/api/v1/user',
                                               {'Authorization': 'token fixture-audit'}, None,
                                               response_limit=256 * 1024, follow_redirects=False)
            self.assertEqual(status, 302)
            self.assertIsInstance(build.call_args.args[0], _NoDependencyRedirect)
            fallback.assert_not_called()
            self.assertEqual(opener.open.call_args.args[0].full_url, request.full_url)

    def test_access_manifest_edges_reject_unknown_duplicate_self_and_non_list(self):
        import tempfile
        for targets in (['unknown'], ['aisoft-platform'] * 2, ['sfm-digital-board'], 'aisoft-platform'):
            with self.subTest(targets=targets), tempfile.TemporaryDirectory() as directory:
                raw = json.loads((ROOT / 'codex/config/host-access-broker.json').read_text())
                next(p for p in raw['projects'] if p['project_id'] == 'sfm-digital-board')['dependency_read_targets'] = targets
                path = Path(directory) / 'access.json'
                path.write_text(json.dumps(raw))
                with self.assertRaises(AccessContractError):
                    load_access_contract(path, ROOT / 'codex/config/gitea-governance.json')

    def routine_fixture(self):
        from tests.test_routine_merge import RoutineBrokerTests
        fixture = RoutineBrokerTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        # Explicit fixture-only edge on an enabled routine project. Production
        # remains SFM -> platform only, as asserted separately above.
        fixture.contract = replace(fixture.contract, projects=tuple(
            replace(p, dependency_read_targets=('aisoft-platform',)) if p.project_id == 'newemaint' else p
            for p in fixture.contract.projects))
        fixture.summary = fixture.summary.replace('depends_on: []',
                                                  "depends_on:\n  - 'admin/aisoft-platform#284'")
        return fixture

    def test_routine_collision_and_failure_matrix_zero_merge_post(self):
        for failure in ('open', '403', '404', 'transport', 'json', 'pr', 'identity', 'closed'):
            fixture = self.routine_fixture()
            requests = []

            def transport(method, url, headers, body, *, response_limit=None, follow_redirects=True):
                if '/aisoft-platform/issues/284' in url:
                    requests.append((url, headers['Authorization']))
                    if failure in ('403', '404'):
                        return int(failure), {}, b'{}'
                    if failure == 'transport':
                        raise OSError('fixture transport')
                    value = issue('closed' if failure == 'closed' else 'open')
                    if failure == 'pr':
                        value['pull_request'] = {}
                    if failure == 'identity':
                        value['repository']['full_name'] = 'admin/NewEMaint'
                    return 200, {}, b'{' if failure == 'json' else json.dumps(value).encode()
                if url.endswith('/NewEMaint/issues/284'):
                    self.fail('local same-number terminal Issue must never be queried')
                if url.endswith('/user') and headers['Authorization'] == 'token fixture-audit':
                    return fixture.response({'login': 'audit', 'is_admin': False})
                return fixture.transport(method, url, headers, body)

            b = fixture.broker(transport)
            original_resolve = b.credentials.resolve

            def credential(project, operation):
                if operation.identity_route == 'manager-audit':
                    return ResolvedCredential('audit', 'fixture-audit')
                return original_resolve(project, operation)

            with self.subTest(failure=failure), patch.object(b.credentials, 'resolve', side_effect=credential):
                if failure == 'closed':
                    receipt = b.execute('newemaint', 'gitea.pull.merge.routine', number=7, sha=fixture.sha)
                    self.assertEqual(receipt['dependencies'], ['admin/aisoft-platform#284'])
                    self.assertEqual(len(fixture.posts), 1)
                else:
                    with self.assertRaises(BrokerError):
                        b.execute('newemaint', 'gitea.pull.merge.routine', number=7, sha=fixture.sha)
                    self.assertEqual(fixture.posts, [])
                self.assertEqual(requests, [(access().governance.base_url
                                            + '/api/v1/repos/admin/aisoft-platform/issues/284',
                                            'token fixture-audit')])

    def test_routine_invalid_or_denied_dependencies_never_query_target(self):
        for values in ('  - admin/LocalWMS#284', '  - http://host/repo#284', '  - 74',
                       '  - 284\n  - admin/NewEMaint#284'):
            fixture = self.routine_fixture()
            fixture.summary = fixture.summary.replace("  - 'admin/aisoft-platform#284'", values)
            b = fixture.broker()
            with self.subTest(values=values), patch.object(b, '_read_dependency') as read:
                with self.assertRaises(BrokerError):
                    b.execute('newemaint', 'gitea.pull.merge.routine', number=7, sha=fixture.sha)
                read.assert_not_called()
                self.assertEqual(fixture.posts, [])


if __name__ == "__main__":
    unittest.main()
