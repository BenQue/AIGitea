from __future__ import annotations

import json
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock

from aisoft_host_access.broker import BrokerError, HostAccessBroker
from aisoft_host_access.contract import load_access_contract
from aisoft_host_access.cli import main as cli_main
from aisoft_host_access.application_preflight import PreflightError, run_bounded
from aisoft_host_access.application_preflight import envelope
from aisoft_host_access.contract import APPLICATION_TARGET
from aisoft_host_access.runner import GovernedHostRunner


ROOT = Path(__file__).resolve().parents[3]


class PreflightRouteTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_access_contract(
            ROOT / 'codex/config/host-access-broker.json',
            ROOT / 'codex/config/gitea-governance.json',
        )
        self.credentials = Mock()
        self.credentials.resolve.side_effect = AssertionError('credential access forbidden')
        self.reader = Mock(return_value=json.dumps([
            {'name': 'AppServer', 'state': 'running'},
        ]).encode())

    def test_running_requires_no_start_proof_and_never_resolves_gitea_credentials(self):
        broker = HostAccessBroker(self.contract, credentials=self.credentials,
                                  preflight_reader=self.reader)
        result = broker.execute('localwms', 'application.target.preflight.read',
                                target='localwms-local-test')
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['reason'], 'TARGET_EXECUTION_NO_START_UNPROVEN')
        self.assertEqual(result['target_execution_count'], 0)
        self.assertEqual(self.reader.call_count, 1)
        self.credentials.resolve.assert_not_called()

    def test_bad_target_or_cross_project_is_rejected_before_any_io(self):
        for project, target in [('localwms', x) for x in (
            '', 'AppServer', 'localwms-local-Test', 'localwms-local-test;id',
            '/etc/passwd', 'https://example.invalid', 'sudo id', 1, True, [], {},
        )] + [('aisoft-platform', 'localwms-local-test'), ('hsdb', 'localwms-local-test')]:
            with self.subTest(project=project, target=target):
                reader, credentials = Mock(), Mock()
                with self.assertRaises(BrokerError):
                    HostAccessBroker(self.contract, credentials=credentials,
                                     preflight_reader=reader).execute(
                        project, 'application.target.preflight.read', target=target)
                reader.assert_not_called()
                credentials.resolve.assert_not_called()

    def test_exact_argument_set_rejects_missing_extra_and_old_operation_target(self):
        for op, kwargs in [
            ('application.target.preflight.read', {}),
            ('application.target.preflight.read', {'target': 'localwms-local-test', 'number': 1}),
            ('gitea.repo.read', {'target': 'localwms-local-test'}),
        ]:
            with self.subTest(op=op, kwargs=kwargs):
                with self.assertRaises(BrokerError) as caught:
                    HostAccessBroker(self.contract, credentials=self.credentials,
                                     preflight_reader=self.reader).execute('localwms', op, **kwargs)
                self.assertEqual(caught.exception.code, 'ARGUMENT_MISMATCH')
        self.reader.assert_not_called()
        self.credentials.resolve.assert_not_called()

    def test_stopped_missing_duplicate_unknown_and_wrong_case_never_execute_target(self):
        cases = [([], 'TARGET_MISSING'),
                 ([{'name': 'appserver', 'state': 'running'}], 'TARGET_MISSING'),
                 ([{'name': 'AppServer', 'state': 'stopped'}], 'TARGET_STOPPED'),
                 ([{'name': 'AppServer', 'state': 'unexpected'}], 'TARGET_STATE_UNKNOWN'),
                 ([{'name': 'AppServer', 'state': 'running'}] * 2, 'TARGET_AMBIGUOUS')]
        for rows, reason in cases:
            with self.subTest(reason=reason):
                self.reader.return_value = json.dumps(rows).encode()
                result = HostAccessBroker(self.contract, credentials=self.credentials,
                    preflight_reader=self.reader).execute('localwms',
                    'application.target.preflight.read', target='localwms-local-test')
                self.assertEqual(result['reason'], reason)
                self.assertEqual(result['target_execution_count'], 0)
        self.credentials.resolve.assert_not_called()

    def test_control_bytes_rows_duplicate_keys_and_stderr_cannot_leak(self):
        for raw, reason in [(b'x' * 65537, 'LIMIT_EXCEEDED'),
            (json.dumps([{'name': 'vm', 'state': 'running'}] * 65).encode(), 'LIMIT_EXCEEDED'),
            (b'[{"name":"AppServer","name":"attacker","state":"running"}]', 'RESPONSE_SCHEMA_INVALID'),
            (b'FAKE_SECRET_SENTINEL', 'RESPONSE_SCHEMA_INVALID')]:
            self.reader.return_value = raw
            result = HostAccessBroker(self.contract, credentials=self.credentials,
                preflight_reader=self.reader).execute('localwms',
                'application.target.preflight.read', target='localwms-local-test')
            self.assertEqual(result['reason'], reason)
            self.assertFalse(result['complete'])
            self.assertNotIn('FAKE_SECRET_SENTINEL', json.dumps(result))

    def test_running_to_stopped_race_has_no_target_command_path(self):
        events = []
        def running_then_stopped(argv, **kwargs):
            events.append(tuple(argv))
            events.append('fixture machine stopped after observation')
            return b'[{"name":"AppServer","state":"running"}]'
        result = HostAccessBroker(self.contract, credentials=self.credentials,
            preflight_reader=running_then_stopped).execute('localwms',
            'application.target.preflight.read', target='localwms-local-test')
        self.assertEqual(events[0], ('/usr/local/bin/orb', 'list', '--format', 'json'))
        self.assertEqual(len(events), 2)
        self.assertEqual(result['reason'], 'TARGET_EXECUTION_NO_START_UNPROVEN')
        self.assertEqual(result['target_execution_count'], 0)

    def test_manifest_binding_rejects_extra_routes_overrides_and_duplicates(self):
        original = json.loads((ROOT / 'codex/config/host-access-broker.json').read_text())
        for field, bad in [('machine', 'DockerLab'), ('operator', 'root'),
                           ('helper', '/bin/sh'), ('project_id', 'hsdb'), ('extra', True)]:
            modified = json.loads(json.dumps(original))
            modified['application_targets'][0][field] = bad
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'manifest.json'
                path.write_text(json.dumps(modified))
                with self.assertRaises(ValueError):
                    load_access_contract(path, ROOT / 'codex/config/gitea-governance.json')

    def test_legacy_manifest_without_new_route_retains_old_operations(self):
        old = json.loads((ROOT / 'codex/config/host-access-broker.json').read_text())
        old.pop('application_targets')
        old['operations'] = [x for x in old['operations'] if x['name'] != 'application.target.preflight.read']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            path.write_text(json.dumps(old))
            contract = load_access_contract(path, ROOT / 'codex/config/gitea-governance.json')
            self.assertEqual(len(contract.operations), 38)
            self.assertEqual(contract.raw['mac_host']['orbstack_machine'], 'gitea-ci')

    def test_cli_rejects_duplicated_and_extra_flags_without_echoing_values(self):
        base = ['--access-manifest', str(ROOT / 'codex/config/host-access-broker.json'),
                '--governance-manifest', str(ROOT / 'codex/config/gitea-governance.json'),
                'broker', '--project', 'localwms', '--operation', 'application.target.preflight.read',
                '--target', 'localwms-local-test']
        for extra in [ ['--target', 'FAKE_SECRET_SENTINEL'],
                       ['--number', 'FAKE_SECRET_SENTINEL'], ['--url', 'FAKE_SECRET_SENTINEL'] ]:
            stderr, stdout = io.StringIO(), io.StringIO()
            with redirect_stderr(stderr), redirect_stdout(stdout):
                rc = cli_main(base + extra)
            self.assertEqual(rc, 20)
            self.assertNotIn('FAKE_SECRET_SENTINEL', stderr.getvalue() + stdout.getvalue())
            self.assertEqual(json.loads(stderr.getvalue())['code'], 'ARGUMENT_MISMATCH')

    def test_typed_adapter_binds_args_and_refuses_unknown_or_wrong_machine_reply(self):
        payload = envelope(APPLICATION_TARGET)
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps(payload), ''))
        adapter = GovernedHostRunner(self.contract, 'localwms', command_runner=runner)
        result = adapter.application_target_preflight_read('localwms-local-test')
        self.assertEqual(result['machine'], 'AppServer')
        self.assertEqual(runner.call_args.args[0], [
            '/usr/local/libexec/aisoft/host-access-broker', '--project', 'localwms',
            '--operation', 'application.target.preflight.read', '--target', 'localwms-local-test'])
        for key, value in [('machine', 'DockerLab'), ('Env', 'FAKE_SECRET_SENTINEL'),
                           ('target_execution_count', True), ('status', 'PASS')]:
            malformed = dict(payload)
            malformed[key] = value
            runner.return_value = subprocess.CompletedProcess([], 0, json.dumps(malformed), '')
            with self.assertRaises(BrokerError):
                adapter.application_target_preflight_read('localwms-local-test')
        runner.reset_mock()
        with self.assertRaises(ValueError):
            adapter.application_target_preflight_read('AppServer')
        runner.assert_not_called()


class BoundedProbeTests(unittest.TestCase):
    def test_pipe_limit_is_checked_before_json_parsing_and_stderr_is_discarded(self):
        with self.assertRaises(PreflightError) as caught:
            run_bounded([sys.executable, '-c', 'import os; os.write(1,b"x"*100000)'], limit=64)
        self.assertEqual(caught.exception.reason, 'LIMIT_EXCEEDED')
        self.assertEqual(run_bounded([sys.executable, '-c',
            'import os; os.write(2,b"FAKE_SECRET_SENTINEL"); os.write(1,b"{}");']), b'{}')

    def test_timeout_cancels_probe(self):
        with self.assertRaises(PreflightError) as caught:
            run_bounded([sys.executable, '-c', 'import time; time.sleep(10)'], timeout=0.05)
        self.assertEqual(caught.exception.reason, 'PROBE_TIMEOUT')


if __name__ == '__main__':
    unittest.main()
