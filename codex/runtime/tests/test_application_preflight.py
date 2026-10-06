from __future__ import annotations

import json
import io
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch
from types import SimpleNamespace
import os
import time
import stat

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

    def test_cli_parse_errors_do_not_echo_misplaced_manifest_or_missing_command(self):
        cases = [
            ['--access-manifest', 'unused', '--governance-manifest', 'unused',
             '--project', 'FAKE_SECRET_SENTINEL', 'broker', '--operation',
             'application.target.preflight.read', '--target', 'localwms-local-test'],
            ['--access-manifest', 'unused', '--governance-manifest', 'unused',
             'broker', '--project', 'localwms', '--operation',
             'application.target.preflight.read', '--target', 'localwms-local-test',
             '--label-manifest', 'FAKE_SECRET_SENTINEL'],
        ]
        for argv in cases:
            stderr, stdout = io.StringIO(), io.StringIO()
            with patch('aisoft_host_access.cli.load_access_contract') as load, \
                 redirect_stderr(stderr), redirect_stdout(stdout):
                rc = cli_main(argv)
            self.assertEqual(rc, 20)
            self.assertNotIn('FAKE_SECRET_SENTINEL', stderr.getvalue() + stdout.getvalue())
            self.assertEqual(json.loads(stderr.getvalue())['code'], 'ARGUMENT_MISMATCH')
            load.assert_not_called()

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


class CollectorTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'codex/tools/application-target-preflight.py'
        spec = importlib.util.spec_from_file_location('application_target_collector', path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_fixed_collector_projects_only_allowed_fields_without_npm_or_db_connection(self):
        path = ROOT / 'codex/tools/application-target-preflight.py'
        spec = importlib.util.spec_from_file_location('application_target_collector', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        system = FixtureSystem()
        result = module.collect(system)
        self.assertEqual(result['actual_operator'], 'aisoft-preflight')
        self.assertEqual(result['items']['identity.os']['value']['ID'], 'ubuntu')
        self.assertEqual(result['items']['runtime.npm']['value'], '11.6.0')
        self.assertNotIn('FAKE_SECRET_SENTINEL', json.dumps(result))
        self.assertFalse(any('npm' in event[1] for event in system.events if event[0] == 'command'))
        self.assertEqual(result['items']['postgres.instance']['status'], 'BLOCKED')
        self.assertEqual(result['items']['postgres.instance']['reason'], 'PG_READ_ROUTE_UNAUTHORIZED')

    def test_wrong_operator_prevents_all_field_and_version_reads(self):
        system = FixtureSystem()
        system.operator = lambda deadline: 'root'
        result = self.module.collect(system)
        self.assertEqual(result['reason'], 'OPERATOR_MISMATCH')
        self.assertEqual(result['target_execution_count'], 0)
        self.assertEqual(system.events, [])

    def test_untrusted_binary_metadata_is_never_executed(self):
        for changed in ({'uid': 1001}, {'mode': 0o777}, {'kind': 'symlink', 'is_symlink': True}):
            system = FixtureSystem()
            original = system.metadata
            def metadata(path):
                value = original(path)
                if path.endswith('/node'):
                    value.update(changed)
                return value
            system.metadata = metadata
            result = self.module.collect(system)
            self.assertEqual(result['items']['runtime.node']['reason'], 'UNTRUSTED_PATH')
            self.assertFalse(any(x[0] == 'command' and x[1].endswith('/node') for x in system.events))

    def test_missing_and_permission_items_are_explicit_and_never_provision(self):
        system = FixtureSystem()
        system.filesystem = Mock(side_effect=FileNotFoundError())
        system.account = Mock(side_effect=PermissionError('FAKE_SECRET_SENTINEL'))
        result = self.module.collect(system)
        self.assertEqual(result['items']['filesystem.pg18']['status'], 'GAP')
        self.assertEqual(result['items']['account.localwms']['status'], 'BLOCKED')
        self.assertNotIn('FAKE_SECRET_SENTINEL', json.dumps(result))

    def test_file_socket_group_and_scalar_bounds_mark_incomplete(self):
        system = FixtureSystem()
        original = system.read
        system.read = lambda path: b'x' * 65537 if path == '/proc/meminfo' else original(path)
        result = self.module.collect(system)
        self.assertEqual(result['items']['resources.memory']['reason'], 'LIMIT_EXCEEDED')
        for count in (256, 257):
            system = FixtureSystem()
            original_command = system.command
            system.command = lambda path, args, deadline: (
                b'tcp LISTEN 0 128 127.0.0.1:3100 0.0.0.0:*\n' * count
                if path.endswith('/ss') else original_command(path, args, deadline))
            item = self.module.collect(system)['items']['sockets.listeners']
            self.assertEqual(item['status'], 'PASS' if count == 256 else 'GAP')
            self.assertEqual(item['complete'], count == 256)
        system = FixtureSystem()
        system.account = lambda user, deadline: {'uid': 1002, 'gid': 1002,
            'groups': [{'gid': n, 'name': 'group' + str(n)} for n in range(33)]}
        self.assertEqual(self.module.collect(system)['items']['account.localwms']['reason'], 'LIMIT_EXCEEDED')
        system.hostname = lambda: 'x' * 257
        self.assertEqual(self.module.collect(system)['items']['identity.hostname']['reason'], 'LIMIT_EXCEEDED')

    def test_metadata_and_accounts_drop_home_env_and_configs(self):
        system = FixtureSystem()
        original_meta, original_account = system.metadata, system.account
        system.metadata = lambda path: {**original_meta(path), 'Env': 'FAKE_SECRET_SENTINEL'}
        system.account = lambda user, deadline: {**original_account(user, deadline),
            'home': 'FAKE_SECRET_SENTINEL', 'shadow': 'FAKE_SECRET_SENTINEL'}
        result = self.module.collect(system)
        self.assertNotIn('FAKE_SECRET_SENTINEL', json.dumps(result))
        self.assertEqual(len([x for x in system.events if x[0] == 'account']), 2)

    def test_units_and_paths_are_exact_not_dynamic_enumerations(self):
        system = FixtureSystem()
        result = self.module.collect(system)
        units = [x[2][-1] for x in system.events if x[0] == 'command' and x[1].endswith('systemctl')]
        self.assertEqual(units, ['nginx.service', 'postgresql.service', 'postgresql@18-main.service',
            'pm2-benque.service', 'localwms-api.service', 'localwms-worker.service'])
        reads = {x[1] for x in system.events if x[0] == 'read'}
        self.assertEqual(reads, {'/etc/machine-id', '/etc/os-release', '/proc/meminfo',
            '/opt/node24.18.0/lib/node_modules/npm/package.json'})
        self.assertEqual(result['items']['archive_inventory']['status'], 'GAP')
        self.assertEqual(result['preservation']['whole_machine_before_after'], 'NOT RUN')

    def test_missing_unit_is_gap_instead_of_pass(self):
        system = FixtureSystem()
        original_command = system.command
        system.command = lambda path, args, deadline: (
            b'LoadState=not-found\nActiveState=inactive\nMainPID=0\n'
            if path.endswith('/systemctl') and args[-1] == 'localwms-api.service'
            else original_command(path, args, deadline))
        item = self.module.collect(system)['items']['service.localwms-api.service']
        self.assertEqual(item['status'], 'GAP')
        self.assertEqual(item['reason'], 'MISSING')
        self.assertFalse(item['complete'])

    def test_helper_identity_limits_and_paths_match_approved_target(self):
        from aisoft_host_access.application_preflight import LIMITS
        self.assertEqual(self.module.HELPER, APPLICATION_TARGET['helper'])
        self.assertEqual(self.module.LIMITS, LIMITS)
        result = self.module.collect(FixtureSystem())
        for response_key, target_key in [('project', 'project_id'), ('target', 'target_id'),
                                         ('machine', 'machine'), ('helper_version', 'helper_version')]:
            self.assertEqual(result[response_key], APPLICATION_TARGET[target_key])

    def test_invalid_listener_address_or_unit_value_is_not_echoed(self):
        system = FixtureSystem()
        original_command = system.command
        system.command = lambda path, args, deadline: (
            b'tcp LISTEN 0 128 FAKE_SECRET_SENTINEL:3100 0.0.0.0:*\n'
            if path.endswith('/ss') else original_command(path, args, deadline))
        result = self.module.collect(system)
        self.assertEqual(result['items']['sockets.listeners']['reason'], 'INVALID_VALUE')
        self.assertNotIn('FAKE_SECRET_SENTINEL', json.dumps(result))

    def test_command_deadline_and_stderr_are_bounded(self):
        with self.assertRaises(self.module.ProbeFailure) as caught:
            self.module.bounded_command([sys.executable, '-c', 'import time; time.sleep(2)'],
                                        deadline=time.monotonic() + 0.05)
        self.assertEqual(caught.exception.reason, 'PROBE_TIMEOUT')
        with self.assertRaises(self.module.ProbeFailure) as caught:
            self.module.bounded_command([sys.executable, '-c',
                'import os; os.write(2,b"x"*100000)'], deadline=time.monotonic() + 2)
        self.assertEqual(caught.exception.reason, 'LIMIT_EXCEEDED')

    def test_native_openat_rejects_content_and_parent_symlink_escape(self):
        native = self.module.NativeSystem()
        real_open = os.open
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'etc').mkdir()
            secret = root / 'secret.env'
            secret.write_text('FAKE_SECRET_SENTINEL')
            (root / 'etc/machine-id').symlink_to(secret)
            def opened(path, flags, *args, **kwargs):
                return real_open(root if path == '/' else path, flags, *args, **kwargs)
            real_fstat = os.fstat
            def trusted(fd):
                info = real_fstat(fd)
                return SimpleNamespace(st_mode=info.st_mode, st_uid=0, st_gid=0)
            with patch.object(self.module.os, 'open', side_effect=opened), \
                    patch.object(self.module.os, 'fstat', side_effect=trusted):
                with self.assertRaises(OSError):
                    native.read('/etc/machine-id')
                (root / 'etc/machine-id').unlink()
                (root / 'etc').rmdir()
                (root / 'etc').symlink_to(root)
                with self.assertRaises(OSError):
                    native.read('/etc/machine-id')
                with self.assertRaises(self.module.ProbeFailure):
                    native.read('/secret.env')

    def test_native_binary_exec_uses_opened_inode_even_after_path_replacement(self):
        native = self.module.NativeSystem()
        real_open, real_fstat = os.open, os.fstat
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'opt/node24.18.0/bin/node'
            path.parent.mkdir(parents=True)
            path.write_bytes(b'\x7fELFfixture trusted binary')
            path.chmod(0o755)
            def opened(value, flags, *args, **kwargs):
                return real_open(root if value == '/' else value, flags, *args, **kwargs)
            def trusted(fd):
                info = real_fstat(fd)
                return SimpleNamespace(st_mode=info.st_mode, st_uid=0, st_gid=0)
            def command(argv, **kwargs):
                fd = kwargs['pass_fds'][0]
                path.unlink()
                path.write_bytes(b'FAKE_SECRET_SENTINEL')
                self.assertEqual(os.read(fd, 128), b'\x7fELFfixture trusted binary')
                self.assertEqual(argv, ['/opt/node24.18.0/bin/node', '--version'])
                self.assertEqual(kwargs['executable'], '/proc/self/fd/' + str(fd))
                return b'v24.18.0\n'
            with patch.object(self.module.os, 'open', side_effect=opened), \
                    patch.object(self.module.os, 'fstat', side_effect=trusted), \
                    patch.object(self.module, 'bounded_command', side_effect=command):
                self.assertEqual(native.command('/opt/node24.18.0/bin/node', ['--version'],
                                                 time.monotonic() + 2), b'v24.18.0\n')

    def test_native_rejects_mutating_command_vectors_before_any_file_or_process_access(self):
        native = self.module.NativeSystem()
        with patch.object(native, '_open') as opened:
            for path, args in [('/usr/bin/systemctl', ['restart', 'nginx.service']),
                ('/usr/bin/ss', ['-K']), ('/usr/lib/postgresql/18/bin/postgres', ['-D', '/tmp/data']),
                ('/opt/node24.18.0/bin/node', ['-e', 'write()']), ('/usr/bin/id', ['root'])]:
                with self.assertRaises(self.module.ProbeFailure):
                    native.command(path, args, time.monotonic() + 1)
            opened.assert_not_called()

    def test_helper_cli_refuses_all_caller_arguments_without_echo(self):
        result = subprocess.run([sys.executable, str(ROOT / 'codex/tools/application-target-preflight.py'),
            '--target', 'FAKE_SECRET_SENTINEL'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 20)
        self.assertNotIn('FAKE_SECRET_SENTINEL', result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stderr)['reason'], 'ARGUMENT_MISMATCH')

    def test_docker_only_fixed_gets_project_names_state_ports_named_volumes(self):
        system = FixtureSystem()
        def docker(endpoint, deadline):
            system.events.append(('docker_get', endpoint))
            values = {
                '/version': {'Version': '28.1.1', 'ApiVersion': '1.49', 'Os': 'linux', 'Arch': 'aarch64',
                             'Env': ['FAKE_SECRET_SENTINEL']},
                '/info': {'Driver': 'overlay2', 'DockerRootDir': '/FAKE_SECRET_SENTINEL'},
                '/containers/json?all=1&limit=129': [
                    {'Names': ['/localwms-old'], 'State': 'exited',
                     'Ports': [{'PrivatePort': 3100, 'PublicPort': 3100, 'Type': 'tcp', 'IP': '127.0.0.1'}],
                     'Mounts': [{'Type': 'volume', 'Name': 'retired-localwms-data',
                                'Source': '/FAKE_SECRET_SENTINEL', 'Destination': '/secret'},
                               {'Type': 'bind', 'Source': '/FAKE_SECRET_SENTINEL'}],
                     'Env': ['FAKE_SECRET_SENTINEL'], 'Command': 'FAKE_SECRET_SENTINEL',
                     'Labels': {'credential': 'FAKE_SECRET_SENTINEL'}}],
            }
            return json.dumps(values[endpoint]).encode()
        system.docker_json = docker
        result = self.module.collect(system)
        self.assertEqual(result['items']['docker']['status'], 'PASS')
        value = result['items']['docker']['value']
        self.assertEqual(value['containers'][0]['name'], 'localwms-old')
        self.assertEqual(value['containers'][0]['named_volumes'], ['retired-localwms-data'])
        self.assertNotIn('FAKE_SECRET_SENTINEL', json.dumps(result))
        self.assertEqual([x[1] for x in system.events if x[0] == 'docker_get'],
            ['/version', '/info', '/containers/json?all=1&limit=129'])

    def test_docker_container_max_plus_one_and_body_overflow_are_incomplete(self):
        system = FixtureSystem()
        for count in (128, 129):
            def docker(endpoint, deadline):
                value = ({'Version': '28.1.1', 'ApiVersion': '1.49', 'Os': 'linux', 'Arch': 'arm64'}
                    if endpoint == '/version' else {'Driver': 'overlay2'}
                    if endpoint == '/info' else [
                        {'Names': ['/c' + str(n)], 'State': 'exited', 'Ports': [], 'Mounts': []}
                        for n in range(count)])
                return json.dumps(value).encode()
            system.docker_json = docker
            value = self.module.collect(system)['items']['docker']
            self.assertEqual(value['status'], 'PASS' if count == 128 else 'GAP')
            self.assertEqual(value['complete'], count == 128)
        system.docker_json = lambda endpoint, deadline: b'x' * 65537
        value = self.module.collect(system)['items']['docker']
        self.assertEqual(value['reason'], 'LIMIT_EXCEEDED')
        self.assertFalse(value['complete'])

    def test_docker_permission_and_raw_error_never_trigger_cli_or_echo(self):
        system = FixtureSystem()
        result = self.module.collect(system)
        self.assertEqual(result['items']['docker']['status'], 'BLOCKED')
        self.assertEqual(result['items']['docker']['reason'], 'PERMISSION_DENIED')
        system.docker_json = Mock(side_effect=RuntimeError('FAKE_SECRET_SENTINEL'))
        result = self.module.collect(system)
        self.assertNotIn('FAKE_SECRET_SENTINEL', json.dumps(result))
        self.assertFalse(any(x[0] == 'command' and 'docker' in x[1] for x in system.events))

    def test_native_docker_socket_cannot_connect_or_activate_even_when_metadata_matches(self):
        native = self.module.NativeSystem()
        with tempfile.TemporaryDirectory() as directory:
            def parent(path, trusted):
                return os.open(directory, os.O_RDONLY | os.O_DIRECTORY), (
                    'run' if path == '/var/run' else 'docker.sock')
            def info(path, **kwargs):
                return SimpleNamespace(st_mode=(stat.S_IFLNK | 0o777) if path == 'run'
                    else stat.S_IFSOCK | 0o660, st_uid=0)
            with patch.object(native, '_parent', side_effect=parent), \
                    patch.object(self.module.os, 'stat', side_effect=info), \
                    patch.object(self.module.os, 'readlink', return_value='/run'), \
                    patch.object(self.module.socket, 'socket') as connect:
                with self.assertRaises(self.module.ProbeFailure) as caught:
                    native.docker_json('/version', time.monotonic() + 1)
                self.assertEqual(caught.exception.reason, 'DOCKER_NO_START_UNPROVEN')
                connect.assert_not_called()
        with patch.object(native, '_parent') as opened:
            with self.assertRaises(self.module.ProbeFailure):
                native.docker_json('http://example.invalid', time.monotonic() + 1)
            opened.assert_not_called()

    def test_timeout_kills_descendants_before_fixture_file_write(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'delayed-write'
            child = 'import time,pathlib; time.sleep(0.25); pathlib.Path(' + repr(str(marker)) + ').write_text("unexpected")'
            parent = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",' + repr(child) + ']); time.sleep(5)'
            with self.assertRaises(self.module.ProbeFailure):
                self.module.bounded_command([sys.executable, '-c', parent], deadline=time.monotonic() + 0.08)
            time.sleep(0.3)
            self.assertFalse(marker.exists())


class FixtureSystem:
    def __init__(self):
        self.events = []

    def operator(self, deadline):
        self.events.append(('operator',))
        return 'aisoft-preflight'

    def fingerprint(self):
        return '0' * 64

    def hostname(self): return 'fixture-appserver'
    def architecture(self): return 'aarch64'
    def cpus(self): return 4

    def read(self, path):
        self.events.append(('read', path))
        return {
            '/etc/machine-id': b'0123456789abcdef0123456789abcdef\n',
            '/etc/os-release': b'ID=ubuntu\nVERSION_ID="25.10"\nVERSION="25.10 (Questing Quokka)"\nVERSION_CODENAME=questing\nUNUSED=FAKE_SECRET_SENTINEL\n',
            '/proc/meminfo': b'MemTotal: 8388608 kB\nMemAvailable: 4194304 kB\n',
            '/opt/node24.18.0/lib/node_modules/npm/package.json': b'{"version":"11.6.0","Env":"FAKE_SECRET_SENTINEL"}',
        }[path]

    def metadata(self, path):
        self.events.append(('metadata', path))
        return {'uid': 0, 'gid': 0, 'mode': 493, 'kind': 'file', 'is_symlink': False}

    def filesystem(self, path):
        self.events.append(('filesystem', path))
        return {'total_bytes': 1000000000, 'available_bytes': 900000000, 'free_bytes': 900000000}

    def command(self, path, args, deadline):
        self.events.append(('command', path, tuple(args)))
        if path.endswith('node'): return b'v24.18.0\n'
        if path.endswith(('postgres', 'psql', 'pg_dump', 'pg_restore')):
            return (path.rsplit('/', 1)[1] + ' (PostgreSQL) 18.4\n').encode()
        if path.endswith('ss'):
            return b'tcp LISTEN 0 128 127.0.0.1:3100 0.0.0.0:* users:(("node",pid=123,fd=9))\n'
        if path.endswith('systemctl'):
            return b'LoadState=loaded\nActiveState=active\nMainPID=123\n'
        raise AssertionError('unexpected command')

    def account(self, user, deadline):
        self.events.append(('account', user))
        return {'uid': 1002, 'gid': 1002, 'groups': [{'gid': 1002, 'name': user}]}

    def docker_json(self, endpoint, deadline):
        self.events.append(('docker_get', endpoint))
        raise PermissionError()


if __name__ == '__main__':
    unittest.main()
