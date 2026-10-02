from __future__ import annotations

import os
import json
import tempfile
import time
import subprocess
import hashlib
import io
from contextlib import redirect_stderr
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace

from aisoft_host_access.broker import BrokerError, HostAccessBroker
from aisoft_host_access.contract import load_access_contract


ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'a' * 40
CAPABILITY = '1' * 64  # Synthetic operator grant; never a live credential.


class RotationSurfaceTests(unittest.TestCase):
    def test_ordinary_caller_is_refused_before_secret_resolution(self):
        contract = load_access_contract(ROOT / 'codex/config/host-access-broker.json',
                                        ROOT / 'codex/config/gitea-governance.json')
        with patch('os.geteuid', return_value=501):
            with self.assertRaises(BrokerError) as caught:
                HostAccessBroker(contract).execute(
                    'newemaint', 'gitea.credential.rotate', issue=316,
                    sha=SOURCE, token_kind='routine-merge-agent')
        self.assertEqual(caught.exception.code, 'ROTATION_OPERATOR_REQUIRED')

    def test_wrong_typed_arguments_are_zero_rotation_calls(self):
        contract = load_access_contract(ROOT / 'codex/config/host-access-broker.json',
                                        ROOT / 'codex/config/gitea-governance.json')
        for values in ({'issue': 316, 'sha': SOURCE},
                       {'issue': 316, 'sha': SOURCE, 'token_kind': 'routine-merge-agent', 'body': 'override'},
                       {'number': 316, 'sha': SOURCE, 'token_kind': 'routine-merge-agent'}):
            with patch('aisoft_host_access.credential_rotation.rotate') as mutation:
                with self.assertRaises(BrokerError) as caught:
                    HostAccessBroker(contract).execute('newemaint', 'gitea.credential.rotate', **values)
                self.assertEqual(caught.exception.code, 'ARGUMENT_MISMATCH')
                mutation.assert_not_called()

    def test_project_and_provider_runner_have_no_rotation_method(self):
        from aisoft_host_access.runner import GovernedHostRunner, RoutineMergeRunner
        self.assertFalse(hasattr(GovernedHostRunner, 'rotate'))
        self.assertFalse(hasattr(RoutineMergeRunner, 'rotate'))


class GrantTests(unittest.TestCase):
    def setUp(self):
        from aisoft_host_access.credential_rotation import rotation_target
        self.contract = load_access_contract(ROOT / 'codex/config/host-access-broker.json',
                                            ROOT / 'codex/config/gitea-governance.json')
        self.target = rotation_target(self.contract, 'newemaint', 'routine-merge-agent')
        self.grant = {'version': 1, 'operator_uid': 0, 'issue': 316, 'source_sha': SOURCE,
                      'project_id': 'newemaint', 'token_kind': 'routine-merge-agent',
                      'credential_root': self.contract.raw['mac_host']['credential_root'],
                      'helper_path': '/usr/local/libexec/aisoft/gitea-pat-helper',
                      'not_before': int(time.time()) - 10, 'expires_at': int(time.time()) + 600,
                      'creation_issue': 213, 'operator_capability': CAPABILITY}

    def test_exact_grant_and_all_binding_negatives(self):
        from aisoft_host_access.credential_rotation import validate_grant
        validate_grant(self.contract, self.target, 316, SOURCE, self.grant)
        for key, value in {'version': True, 'operator_uid': 501, 'issue': 313, 'source_sha': 'b'*40,
                           'project_id': 'localwms', 'token_kind': 'project-agent',
                           'credential_root': '/tmp/credentials', 'helper_path': '/tmp/helper',
                           'not_before': int(time.time()) + 10, 'expires_at': int(time.time()) - 1,
                           'creation_issue': False, 'operator_capability': 'BAD',
                           'operator_capability_sha256': CAPABILITY,
                           'url': 'https://override.invalid'}.items():
            with self.subTest(key=key):
                with self.assertRaises(BrokerError):
                    validate_grant(self.contract, self.target, 316, SOURCE, dict(self.grant, **{key:value}))
        for key in self.grant:
            missing = dict(self.grant)
            del missing[key]
            with self.assertRaises(BrokerError):
                validate_grant(self.contract, self.target, 316, SOURCE, missing)

    def test_vm_grant_has_only_digest_and_exact_bindings(self):
        from aisoft_host_access.credential_rotation import validate_grant
        grant = dict(self.grant)
        del grant['operator_capability']
        grant['operator_capability_sha256'] = hashlib.sha256(CAPABILITY.encode()).hexdigest()
        validate_grant(self.contract, self.target, 316, SOURCE, grant, vm=True)
        for override in ({'operator_capability': CAPABILITY},
                         {'operator_capability_sha256': 'bad'}, {'source_sha': 'b'*40},
                         {'project_id': 'localwms'}, {'issue': 313},
                         {'expires_at': int(time.time())-1}):
            with self.subTest(override=override), self.assertRaises(BrokerError):
                validate_grant(self.contract, self.target, 316, SOURCE, dict(grant, **override), vm=True)
        with self.assertRaises(BrokerError):
            validate_grant(self.contract, self.target, 316, SOURCE, grant)

    def test_untrusted_or_missing_grant_and_duplicate_json_fail_closed(self):
        from aisoft_host_access.credential_rotation import trusted_read, strict_json
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            p = root / 'grant.json'
            p.write_text(json.dumps(self.grant))
            p.chmod(0o600)
            with self.assertRaises(BrokerError):
                trusted_read(str(p))  # Actual user-owned ancestors are not root authority.
            with self.assertRaises(BrokerError):
                trusted_read(str(root/'missing.json'))
        for raw in (b'{"issue":316,"issue":313}', b'{} {}', b'null', b'{"a":NaN}'):
            with self.assertRaises(BrokerError):
                strict_json(raw)

    def test_env_does_not_choose_grant_store_helper_or_manifests(self):
        from aisoft_host_access.credential_rotation import authorization
        environment = {'ROTATION_GRANT': '/tmp/forged.json', 'GITEA_CONFIG': '/tmp/evil.ini',
                       'AISOFT_CREDENTIAL_ROOT': '/tmp/evil', 'GITEA_BIN': '/tmp/evil'}
        with patch.dict(os.environ, environment), patch(
                'aisoft_host_access.credential_rotation.installation_receipt') as installation, patch(
                'aisoft_host_access.credential_rotation.trusted_read', side_effect=BrokerError('BLOCKED', 'redacted')) as reader:
            with self.assertRaises(BrokerError):
                authorization(self.contract, self.target, 316, SOURCE)
            installation.assert_called_once_with(self.contract, SOURCE, vm=False)
            reader.assert_called_once_with(
                '/usr/local/etc/aisoft/credential-rotation-grants/newemaint-routine-merge-agent.json', group=None)


class RotationVMTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_access_contract(ROOT / 'codex/config/host-access-broker.json',
                                            ROOT / 'codex/config/gitea-governance.json')
        self.common = dict(action='capabilities', project_id='newemaint', token_kind='routine-merge-agent',
                           issue=316, source_sha=SOURCE, operator_capability=CAPABILITY)
        self.calls = []

    def test_direct_service_user_without_root_capability_is_zero_commands(self):
        name = 'issue-316-routine-merge-agent-rotation-0123456789ab'
        for proof in (None, '2'*64, hashlib.sha256(CAPABILITY.encode()).hexdigest(),
                      'A'*64, '', True, CAPABILITY+'\n'):
            request = dict(self.common, action='generate', token_name=name)
            del request['operator_capability']
            if proof is not None:
                request['operator_capability'] = proof
            with self.subTest(proof=proof):
                self.calls.clear()
                with self.assertRaises(BrokerError):
                    self.invoke(request)
                self.assertEqual(self.calls, [])

    def test_private_endpoint_rejects_regular_files_before_dispatch(self):
        from aisoft_host_access.credential_rotation import operator_main
        with tempfile.TemporaryFile('w+') as source, tempfile.TemporaryFile('w+') as output, \
             patch('sys.stdin', source), patch('sys.stdout', output), \
             patch('aisoft_host_access.credential_rotation.vm_operation') as dispatch, \
             redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(operator_main(['--vm-operation']), 20)
            dispatch.assert_not_called()
            output.seek(0)
            self.assertEqual(output.read(), '')
            self.assertNotIn(CAPABILITY, errors.getvalue())

    def test_named_and_unlinked_fifo_are_refused(self):
        from aisoft_host_access.credential_rotation import require_private_pipes
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'fifo'
            os.mkfifo(path, 0o600)
            with path.open('r+b', buffering=0) as fifo:
                for unlink in (False, True):
                    if unlink:
                        path.unlink()
                    with patch('sys.stdin', fifo), patch('sys.stdout', fifo), self.assertRaises(BrokerError):
                        require_private_pipes()

    def test_anonymous_pipes_and_linux_inode_binding(self):
        from aisoft_host_access.credential_rotation import require_private_pipes
        read_fd, write_fd = os.pipe()
        with os.fdopen(read_fd, 'rb') as source, os.fdopen(write_fd, 'wb') as output, \
             patch('sys.stdin', source), patch('sys.stdout', output):
            require_private_pipes()  # Real host anonymous descriptors.
            with patch('sys.platform', 'linux'), patch('os.readlink', side_effect=lambda p:
                    f'pipe:[{os.fstat(int(p.rsplit("/",1)[1])).st_ino}]'):
                require_private_pipes()  # Linux descriptor rule, not a live Linux transport PASS.
            for wrong in ('/tmp/fifo', '/tmp/fifo (deleted)', 'pipe:[0]'):
                with patch('sys.platform', 'linux'), patch('os.readlink', return_value=wrong), \
                     self.assertRaises(BrokerError):
                    require_private_pipes()

    def test_private_output_is_rechecked_before_secret_write(self):
        from aisoft_host_access.credential_rotation import operator_main
        read_fd, write_fd = os.pipe()
        with os.fdopen(read_fd, 'rb') as source, os.fdopen(write_fd, 'wb') as output, \
             patch('sys.stdin', source), patch('sys.stdout', output), redirect_stderr(io.StringIO()), \
             patch('aisoft_host_access.credential_rotation.require_private_pipes',
                   side_effect=[None, BrokerError('ROTATION_PIPE_REQUIRED', 'redacted')]) as guard, \
             patch('aisoft_host_access.credential_rotation.vm_operation', return_value={'token':'candidate-secret-canary'}), \
             patch.object(source, 'read', return_value=b'{}'):
            # The real stream's buffer is represented by this bounded synthetic request seam.
            with patch('sys.stdin', SimpleNamespace(fileno=source.fileno, buffer=source)):
                self.assertEqual(operator_main(['--vm-operation']), 20)
            self.assertEqual(guard.call_count, 2)
            os.set_blocking(read_fd, False)
            with self.assertRaises(BlockingIOError):
                os.read(read_fd, 512)

    def command(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if argv == ['/usr/local/bin/gitea', '--version']:
            output = b'Gitea version 1.26.4 built with go1.26.3 : bindata\n'
        elif argv == ['/usr/local/libexec/aisoft/gitea-pat-helper', '--version']:
            output = b'{"helper_version":"1","gitea_model_version":"1.26.4","toolchain":"go1.26.3"}'
        elif 'generate-access-token' in argv:
            output = b'candidate-secret-canary\n'
        else:
            request = json.loads(kwargs['input'])
            output = json.dumps({'result': 'verified', 'token_id': 11, 'user_id': 7,
                                 'token_name': 'issue-213-routine-merge-agent',
                                 'scopes': ['write:repository']}).encode()
            self.assertEqual(request['token'], 'old-secret-canary')
        return subprocess.CompletedProcess(argv, 0, stdout=output, stderr=b'candidate-secret-canary')

    def invoke(self, request, grant=True):
        from aisoft_host_access.credential_rotation import vm_operation, OperatorGrant
        with patch('sys.platform', 'linux'), patch('os.geteuid', return_value=501), \
             patch('pwd.getpwnam', return_value=SimpleNamespace(pw_uid=501, pw_gid=20)), \
             patch('aisoft_host_access.contract.load_access_contract', return_value=self.contract), \
             patch('aisoft_host_access.credential_rotation.authorization',
                   return_value=OperatorGrant({}, capability_digest=hashlib.sha256(CAPABILITY.encode()).hexdigest()),
                   side_effect=None if grant else BrokerError('ROTATION_GRANT_INVALID', 'redacted')), \
             patch('subprocess.run', side_effect=self.command):
            return vm_operation(json.dumps(request).encode())

    def test_fixed_capability_generate_and_helper_use_private_stdin_only(self):
        self.assertEqual(self.invoke(self.common)['result'], 'ready')
        self.calls.clear()
        name = 'issue-316-routine-merge-agent-rotation-0123456789ab'
        self.assertEqual(self.invoke(dict(self.common, action='generate', token_name=name)),
                         {'token': 'candidate-secret-canary'})
        argv, values = self.calls[-1]
        self.assertEqual(argv, ['/usr/local/bin/gitea', '--config', '/etc/gitea/app.ini',
                                'admin', 'user', 'generate-access-token', '--username',
                                'newemaint-routine-merger', '--token-name', name,
                                '--scopes', 'read:user,write:repository', '--raw'])
        self.assertEqual(values['stderr'], subprocess.DEVNULL)
        self.calls.clear()
        result = self.invoke(dict(self.common, action='inspect', token='old-secret-canary'))
        self.assertEqual(result['result'], 'verified')
        argv, values = self.calls[-1]
        self.assertEqual(argv, ['/usr/local/libexec/aisoft/gitea-pat-helper'])
        self.assertNotIn('old-secret-canary', ' '.join(argv))
        self.assertIn(b'old-secret-canary', values['input'])

    def test_vm_unknown_schema_and_missing_grant_are_zero_cli_calls(self):
        for request in (dict(self.common, url='https://override.invalid'),
                        dict(self.common, action='generate', token_name='arbitrary-name'),
                        dict(self.common, action='generate', token_name='issue-316-routine-merge-agent-rotation-0123456789ab')):
            self.calls.clear()
            with self.assertRaises(BrokerError):
                self.invoke(request, grant=False)
            self.assertEqual(self.calls, [])

    def test_canonical_mac_transport_ignores_env_and_never_uses_secret_argv(self):
        from aisoft_host_access.credential_rotation import SystemBackend, rotation_target
        target = rotation_target(self.contract, 'newemaint', 'routine-merge-agent')
        backend = SystemBackend(self.contract, target, 316, SOURCE, CAPABILITY)
        result = subprocess.CompletedProcess([], 0, stdout=b'{"result":"verified","token_id":11,"user_id":7,"token_name":"issue-213-routine-merge-agent","scopes":["write:repository"]}')
        with patch.dict(os.environ, {'GITEA_BIN':'/tmp/evil'}), patch('subprocess.run', return_value=result) as run:
            backend.inspect('old-secret-canary')
        argv = run.call_args.args[0]
        self.assertEqual(argv, ['/usr/bin/sudo', '-n', '-H', '-u', 'benque', '/usr/local/bin/orb',
                                '-m', 'gitea-ci', '-u', 'git',
                                '/usr/local/libexec/aisoft/rotate-gitea-service-account', '--vm-operation'])
        self.assertNotIn('old-secret-canary', ' '.join(argv))
        self.assertNotIn(CAPABILITY, ' '.join(argv))
        self.assertNotIn(CAPABILITY, json.dumps(run.call_args.kwargs['env']))
        self.assertIn(CAPABILITY.encode(), run.call_args.kwargs['input'])
        self.assertEqual(run.call_args.kwargs['stderr'], subprocess.DEVNULL)
        self.assertIn(b'old-secret-canary', run.call_args.kwargs['input'])

    def test_auth_http_cannot_follow_redirect_or_env_proxy(self):
        from aisoft_host_access.credential_rotation import SystemBackend, rotation_target, NoRedirect
        from urllib.request import ProxyHandler
        target = rotation_target(self.contract, 'newemaint', 'routine-merge-agent')
        backend = SystemBackend(self.contract, target, 316, SOURCE, CAPABILITY)
        class Response:
            code = 401
            def read(self, limit):
                return b'{}'
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        opener = SimpleNamespace(open=lambda *args, **kwargs: Response())
        with patch.dict(os.environ, {'HTTP_PROXY':'http://evil.invalid'}), patch(
                'aisoft_host_access.credential_rotation.build_opener', return_value=opener) as build:
            self.assertTrue(backend.rejected('old-secret-canary'))
        handlers = build.call_args.args
        self.assertTrue(any(isinstance(h, ProxyHandler) and h.proxies == {} for h in handlers))
        redirect = next(h for h in handlers if isinstance(h, NoRedirect))
        self.assertIsNone(redirect.redirect_request(None, None, 302, None, None, 'https://evil.invalid'))

    def test_cli_unknown_duplicate_fields_and_tty_private_pipe_fail_closed(self):
        import io
        from contextlib import redirect_stderr
        from aisoft_host_access.credential_rotation import operator_main
        for argv in (['--project','newemaint','--issue','316','--sha',SOURCE,
                      '--token-kind','routine-merge-agent','--path','/tmp/evil'],
                     ['--project','newemaint','--project','localwms','--sha',SOURCE,
                      '--token-kind','routine-merge-agent'], ['--vm-operation']):
            errors = io.StringIO()
            with redirect_stderr(errors), patch('sys.stdin.isatty', return_value=True), \
                 patch('aisoft_host_access.contract.load_access_contract') as load:
                self.assertEqual(operator_main(argv), 20)
                load.assert_not_called()
            self.assertNotIn('/tmp/evil', errors.getvalue())


class FakeGitea:
    """External-system seam: mutations and user scope gates are independent facts."""
    def __init__(self):
        self.tokens = {'old-secret-canary': {'token_id': 11, 'user_id': 7,
                       'token_name': 'issue-213-routine-merge-agent',
                       'scopes': ['write:repository']}}
        self.created = self.deleted = 0

    def capabilities(self):
        pass

    def inspect(self, token, name=None):
        if token not in self.tokens:
            raise BrokerError('TOKEN_UNKNOWN', 'unknown token')
        value = dict(self.tokens[token])
        if name is not None and value['token_name'] != name:
            raise BrokerError('TOKEN_BINDING_MISMATCH', 'wrong token name')
        return value

    def generate(self, name):
        self.created += 1
        token = 'candidate-secret-canary' if self.created == 1 else f'candidate-{self.created}-secret-canary'
        self.tokens[token] = {
            'token_id': 11 + self.created, 'user_id': 7, 'token_name': name,
            'scopes': ['read:user', 'write:repository']}
        return token

    def verify(self, token, metadata, scopes):
        actual = self.tokens.get(token)
        if not actual or 'read:user' not in actual['scopes']:
            raise BrokerError('IDENTITY_FAILED', 'user scope gate')
        if set(actual['scopes']) != set(scopes) or actual != metadata:
            raise BrokerError('TOKEN_SCOPE_MISMATCH', 'wrong scopes')

    def revoke(self, token, metadata):
        assert self.tokens[token] == metadata
        self.deleted += 1
        del self.tokens[token]

    def rejected(self, token):
        return token not in self.tokens


class RotationTransactionTests(unittest.TestCase):
    def setUp(self):
        from aisoft_host_access.credential_rotation import RotationTransaction, rotation_target
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve() / 'credentials'
        self.parent = self.root / 'projects/newemaint'
        self.parent.mkdir(parents=True)
        for p in (self.root, self.root / 'projects', self.parent):
            p.chmod(0o700)
        self.token = self.parent / 'routine-merge-agent.token'
        self.token.write_text('old-secret-canary\n')
        self.token.chmod(0o600)
        for name, data in {
            'newemaint-routine-merger.account-created-by-issue-213': 'issue=213\nusername=newemaint-routine-merger\n',
            'newemaint-routine-merger.must-change-password-unset-by-issue-213': 'issue=213\nusername=newemaint-routine-merger\npolicy=must-change-password-unset\n',
            'routine-merge-agent.token-created-by-issue-213': 'issue=213\nusername=newemaint-routine-merger\ntoken_kind=routine-merge-agent\n',
        }.items():
            p = self.parent / name
            p.write_text(data)
            p.chmod(0o600)
        contract = load_access_contract(ROOT / 'codex/config/host-access-broker.json',
                                        ROOT / 'codex/config/gitea-governance.json')
        self.target = rotation_target(contract, 'newemaint', 'routine-merge-agent')
        self.backend = FakeGitea()
        self.authorization = {'issue': 316, 'source_sha': SOURCE, 'creation_issue': 213,
                              'project_id': 'newemaint', 'token_kind': 'routine-merge-agent'}
        self.transaction = lambda: RotationTransaction(
            self.root, os.getuid(), self.target, self.authorization, self.backend)

    def test_rotates_legacy_scope_and_second_request_is_noop(self):
        value = self.transaction().run()
        self.assertEqual(value['result'], 'rotated')
        self.assertEqual(self.token.read_text().strip(), 'candidate-secret-canary')
        self.assertFalse(self.backend.rejected('candidate-secret-canary'))
        self.assertTrue(self.backend.rejected('old-secret-canary'))
        self.assertEqual(self.transaction().run()['result'], 'no-op')
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))
        self.assertNotIn('secret-canary', json.dumps(value))

    def test_revoke_failure_retains_candidate_and_retry_does_not_reissue(self):
        with patch.object(self.backend, 'revoke', side_effect=BrokerError('REVOKE_FAILED', 'redacted')):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        self.assertFalse(self.token.exists())
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 0))
        self.assertEqual(self.transaction().run()['result'], 'rotated')
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))

    def test_publish_failure_after_revoke_recovers_only_saved_candidate(self):
        rename = os.rename
        def fail_publish(src, dst, **kwargs):
            if src == 'candidate.token' and dst == self.token.name:
                raise OSError('synthetic candidate-secret-canary write failure')
            return rename(src, dst, **kwargs)
        with patch('os.rename', side_effect=fail_publish):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        self.assertFalse(self.token.exists())
        self.assertTrue(self.backend.rejected('old-secret-canary'))
        self.assertEqual(self.transaction().run()['result'], 'rotated')
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))

    def test_scope_mismatch_compensates_candidate_but_cannot_restore_legacy_pat(self):
        with patch.object(self.backend, 'verify', side_effect=BrokerError('SCOPE_INVALID', 'redacted')):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        self.assertFalse(self.token.exists())
        self.assertFalse(self.backend.rejected('old-secret-canary'))
        self.assertTrue(self.backend.rejected('candidate-secret-canary'))
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))
        with self.assertRaises(BrokerError):
            self.transaction().run()
        self.assertEqual(self.backend.created, 1)

    def test_scope_failure_restores_old_only_when_current_policy_is_satisfied(self):
        self.backend.tokens['old-secret-canary']['scopes'] = ['read:user', 'write:repository']
        verify = self.backend.verify
        def reject_candidate(token, *args):
            if token == 'candidate-secret-canary':
                raise BrokerError('SCOPE_INVALID', 'redacted')
            verify(token, *args)
        with patch.object(self.backend, 'verify', side_effect=reject_candidate):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        self.assertEqual(self.token.read_text().strip(), 'old-secret-canary')
        self.assertFalse(self.backend.rejected('old-secret-canary'))

    def test_lost_generate_result_never_generates_again(self):
        generate = self.backend.generate
        def lost(name):
            generate(name)
            raise OSError('synthetic transport lost candidate-secret-canary')
        with patch.object(self.backend, 'generate', side_effect=lost):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        with self.assertRaises(BrokerError) as caught:
            self.transaction().run()
        self.assertEqual(caught.exception.code, 'ROTATION_CANDIDATE_UNKNOWN')
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 0))
        self.assertFalse(self.token.exists())

    def test_missing_marker_and_unsafe_files_are_zero_external_mutation(self):
        marker = self.parent / 'routine-merge-agent.token-created-by-issue-213'
        marker.unlink()
        with self.assertRaises(BrokerError):
            self.transaction().run()
        self.assertEqual((self.backend.created, self.backend.deleted), (0, 0))
        self.assertEqual(self.token.read_text().strip(), 'old-secret-canary')

    def test_symlink_hardlink_mode_and_owner_fail_closed(self):
        for change in ('symlink', 'hardlink', 'mode', 'owner'):
            with self.subTest(change=change):
                if change == 'symlink':
                    self.token.rename(self.parent / 'original.token')
                    self.token.symlink_to('original.token')
                elif change == 'hardlink':
                    os.link(self.token, self.parent / 'extra-link')
                elif change == 'mode':
                    self.token.chmod(0o644)
                try:
                    tx = self.transaction()
                    if change == 'owner':
                        tx.uid = os.getuid() + 1
                    with self.assertRaises(BrokerError):
                        tx.run()
                    self.assertEqual((self.backend.created, self.backend.deleted), (0, 0))
                finally:
                    if change == 'symlink':
                        self.token.unlink()
                        (self.parent / 'original.token').rename(self.token)
                    elif change == 'hardlink':
                        (self.parent / 'extra-link').unlink()
                    elif change == 'mode':
                        self.token.chmod(0o600)

    def test_busy_target_is_refused_and_other_target_has_separate_lock(self):
        import fcntl
        tx = self.parent / '.rotation-routine-merge-agent'
        tx.mkdir(mode=0o700)
        lock = tx / '.rotation.lock'
        lock.touch(mode=0o600)
        with lock.open('rb') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BrokerError) as caught:
                self.transaction().run()
            self.assertEqual(caught.exception.code, 'ROTATION_BUSY')
        self.assertEqual(self.backend.created, 0)
        self.assertEqual(self.transaction().run()['result'], 'rotated')

    def test_401_required_403_does_not_prove_old_revoke(self):
        with patch.object(self.backend, 'rejected', return_value=False):
            with self.assertRaises(BrokerError) as caught:
                self.transaction().run()
        self.assertEqual(caught.exception.code, 'ROTATION_OLD_UNCONFIRMED')
        self.assertFalse(self.token.exists())
        self.assertEqual(self.transaction().run()['result'], 'rotated')
        self.assertEqual(self.backend.created, 1)

    def test_completed_request_refuses_drifted_active_token(self):
        self.transaction().run()
        self.backend.tokens['candidate-secret-canary']['scopes'] = ['write:repository']
        with self.assertRaises(BrokerError):
            self.transaction().run()
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))

    def test_new_exact_authorization_can_rotate_a_previously_completed_target(self):
        self.transaction().run()
        self.authorization = dict(self.authorization, issue=317)
        self.assertEqual(self.transaction().run()['result'], 'rotated')
        self.assertEqual(self.token.read_text().strip(), 'candidate-2-secret-canary')
        self.assertEqual(self.transaction().run()['result'], 'no-op')
        self.assertEqual((self.backend.created, self.backend.deleted), (2, 2))

    def test_candidate_saved_before_journal_crash_resumes_without_new_issue(self):
        rename = os.rename
        def crash(src, dst, **kwargs):
            if dst == 'journal.json' and (self.parent/'.rotation-routine-merge-agent/candidate.token').exists():
                raise OSError('synthetic journal crash')
            return rename(src, dst, **kwargs)
        with patch('os.rename', side_effect=crash):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 0))
        self.assertEqual(self.transaction().run()['result'], 'rotated')
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))

    def test_published_candidate_before_journal_crash_is_bound_and_resumed(self):
        rename = os.rename
        def crash(src, dst, **kwargs):
            if dst == 'journal.json' and self.token.exists() and self.backend.deleted == 1:
                raise OSError('synthetic post-rename crash')
            return rename(src, dst, **kwargs)
        with patch('os.rename', side_effect=crash):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        self.assertEqual(self.token.read_text().strip(), 'candidate-secret-canary')
        self.assertEqual(self.transaction().run()['result'], 'rotated')
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))

    def test_revoked_db_but_missing_journal_confirmation_fails_closed(self):
        rename = os.rename
        def crash(src, dst, **kwargs):
            if dst == 'journal.json' and self.backend.deleted == 1:
                raise OSError('synthetic post-revoke crash')
            return rename(src, dst, **kwargs)
        with patch('os.rename', side_effect=crash):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        with self.assertRaises(BrokerError):
            self.transaction().run()
        self.assertFalse(self.token.exists())
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))

    def test_candidate_file_failure_compensates_known_raw_before_it_is_lost(self):
        from aisoft_host_access.credential_rotation import ProtectedDirectory
        write = ProtectedDirectory.write
        def failed(directory, name, raw):
            if name == 'candidate.token':
                raise OSError('synthetic write failure')
            return write(directory, name, raw)
        with patch.object(ProtectedDirectory, 'write', failed):
            with self.assertRaises(BrokerError):
                self.transaction().run()
        self.assertFalse(self.token.exists())
        self.assertFalse(self.backend.rejected('old-secret-canary'))
        self.assertTrue(self.backend.rejected('candidate-secret-canary'))
        self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))

    def test_expiry_during_transaction_stops_before_old_revoke(self):
        clock = [1000]
        self.authorization = dict(self.authorization, expires_at=2000)
        verify = self.backend.verify
        def expire(*args):
            verify(*args)
            clock[0] = 2001
        with patch('time.time', side_effect=lambda: clock[0]):
            with patch.object(self.backend, 'verify', side_effect=expire):
                with self.assertRaises(BrokerError) as caught:
                    self.transaction().run()
            self.assertEqual(caught.exception.code, 'ROTATION_GRANT_EXPIRED')
            self.assertEqual((self.backend.created, self.backend.deleted), (1, 0))
            self.assertFalse(self.token.exists())
            self.authorization['expires_at'] = 3000
            self.assertEqual(self.transaction().run()['result'], 'rotated')
            self.assertEqual((self.backend.created, self.backend.deleted), (1, 1))


if __name__ == '__main__':
    unittest.main()
