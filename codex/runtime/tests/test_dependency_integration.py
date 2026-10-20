"""#286: validate both dependency gates and persisted wait behaviour."""
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aisoft_host_access.broker import BrokerError, HostAccessBroker, ResolvedCredential
from aisoft_host_access.contract import AccessContractError, load_access_contract
from tests.test_dependencies import ROOT, access, issue


class DependencyIntegrationTests(unittest.TestCase):
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
                    b.execute('gamma-board', 'gitea.dependency.read', reference='admin/aisoft-platform#284')
                self.assertEqual(caught.exception.code, 'IDENTITY_MISMATCH')
                self.assertEqual(requests, [access().governance.base_url + '/api/v1/user'])

    def test_mac_vm_adapter_fixed_surface_and_zero_fallback(self):
        from aisoft_host_access.runner import DependencyReader, BROKER_EXECUTABLE
        from aisoft_host_access.dependencies import project_issue
        for cwd in ('/Users/fixture/Projects/GammaBoard', '/home/fixture/GammaBoard'):
            calls = []

            def command(argv, *, cwd):
                calls.append((list(argv), cwd))
                return subprocess.CompletedProcess(argv, 0, json.dumps(
                    project_issue(issue(), ('admin', 'aisoft-platform', 284))), '')

            reader = DependencyReader(access(), 'gamma-board', command_runner=command)
            reader._cwd = cwd
            reader.read('admin/aisoft-platform#284')
            self.assertEqual(calls, [([BROKER_EXECUTABLE, '--project', 'gamma-board',
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
                    b.execute('gamma-board', 'gitea.dependency.read', reference='admin/aisoft-platform#284')
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
        for targets in (['unknown'], ['aisoft-platform'] * 2, ['gamma-board'], 'aisoft-platform'):
            with self.subTest(targets=targets), tempfile.TemporaryDirectory() as directory:
                raw = json.loads((ROOT / 'codex/tests/fixtures/manifests/host-access-broker.json').read_text())
                next(p for p in raw['projects'] if p['project_id'] == 'gamma-board')['dependency_read_targets'] = targets
                path = Path(directory) / 'access.json'
                path.write_text(json.dumps(raw))
                with self.assertRaises(AccessContractError):
                    load_access_contract(path, ROOT / 'codex/tests/fixtures/manifests/gitea-governance.json')

if __name__ == "__main__":
    unittest.main()
