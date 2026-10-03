"""Toolchain verification tests use synthetic archives, never execute their Go."""
import hashlib
import io
import os
import subprocess
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import json

import build

from build import verify_toolchain


class NativeHelperCleanupTests(unittest.TestCase):
    def check_cleanup(self, primary_exit):
        # Execute the actual shell setup/EXIT trap without downloading a toolchain.
        script = Path(__file__).resolve().parents[2] / 'tests/test-gitea-pat-helper-linux.sh'
        prefix, separator, _ = script.read_text().partition('case "$(uname -m)" in')
        self.assertTrue(separator, 'native test setup seam missing')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools = root / 'bin'
            tools.mkdir()
            uname = tools / 'uname'
            uname.write_text('#!/bin/sh\nprintf "%s\\n" Linux\n')
            uname.chmod(0o755)
            external = root / 'external-cache'
            external.mkdir()
            sentinel = external / 'keep'
            sentinel.write_bytes(b'external caller cache')
            sentinel.chmod(0o444)
            receipt = root / 'private-path'
            runner = root / 'runner.sh'
            runner.write_text(prefix + '''
mkdir -p "$TMP/gopath/pkg/mod/example@v1"
printf '%s' synthetic > "$TMP/gopath/pkg/mod/example@v1/model.go"
chmod 0444 "$TMP/gopath/pkg/mod/example@v1/model.go"
chmod 0555 "$TMP/gopath/pkg/mod/example@v1"
printf '%s' "$TMP" > "$CLEANUP_RECEIPT"
exit ''' + str(primary_exit) + '\n')
            env = {**os.environ, 'PATH': str(tools) + os.pathsep + os.environ['PATH'],
                   'TMPDIR': str(root), 'GOPATH': str(external),
                   'CLEANUP_RECEIPT': str(receipt)}
            result = subprocess.run(['bash', str(runner), '--output', str(root / 'artifact')],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, primary_exit, result.stderr)
            self.assertFalse(Path(receipt.read_text()).exists(), 'private cache leaked')
            self.assertEqual(sentinel.read_bytes(), b'external caller cache')
            self.assertEqual(sentinel.stat().st_mode & 0o777, 0o444)

    def test_readonly_module_cleanup_preserves_success_and_external_cache(self):
        self.check_cleanup(0)

    def test_readonly_module_cleanup_preserves_primary_failure(self):
        self.check_cleanup(37)


class PinnedModelSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.module = self.root / 'module-cache'
        self.model = self.module / 'models/auth/access_token.go'
        self.model.parent.mkdir(parents=True)
        self.model.write_bytes(b'synthetic pinned token model')
        for name in ('go.mod', 'go.sum'):
            (self.root / name).write_bytes(b'fixed module input\n')
        self.pin = {'module': 'code.gitea.io/gitea', 'version': 'v1.26.4',
                    'module_sum': 'h1:synthetic-fixed-sum',
                    'model_path': 'models/auth/access_token.go',
                    'model_sha256': hashlib.sha256(self.model.read_bytes()).hexdigest()}
        self.selected = {'Path': self.pin['module'], 'Version': self.pin['version'],
                         'Sum': self.pin['module_sum']}
        self.downloaded = dict(self.selected, Dir=str(self.module))
        self.calls = []

    def invoke(self, mutate=False):
        def command(go, args, env):
            self.calls.append(args)
            if args[0] == 'list':
                return json.dumps(self.selected).encode()
            if args[:3] != ['mod', 'download', '-json']:
                self.fail('unexpected command before model verification')
            if mutate:
                (self.root / 'go.sum').write_bytes(b'changed input')
            return json.dumps(self.downloaded).encode()
        with patch.object(build, 'ROOT', self.root), patch.object(build, 'run', side_effect=command):
            return build.pinned_model_source(Path('/synthetic/go'), {}, self.pin)

    def test_cold_cache_materializes_exact_pinned_model(self):
        self.assertNotIn('Dir', self.selected)
        self.assertEqual(self.invoke(), self.model)
        self.assertEqual(self.calls[1], ['mod', 'download', '-json',
                                        'code.gitea.io/gitea@v1.26.4'])
        for name in ('go.mod', 'go.sum'):
            self.assertEqual((self.root / name).read_bytes(), b'fixed module input\n')

    def test_warm_cache_uses_verified_download_source(self):
        self.selected['Dir'] = '/unused-selected-module-path'
        self.assertEqual(self.invoke(), self.model)

    def test_graph_drift_and_replacement_refuse_before_download(self):
        original = dict(self.selected)
        for key, value in (('Path', 'other/module'), ('Version', 'v1.26.5'),
                           ('Sum', 'h1:wrong'), ('Replace', {})):
            with self.subTest(key=key):
                self.selected = dict(original, **{key: value})
                self.calls.clear()
                with self.assertRaisesRegex(SystemExit, 'MODEL_PIN_MISMATCH'):
                    self.invoke()
                self.assertEqual(len(self.calls), 1)

    def test_download_binding_and_source_directory_refuse_before_model(self):
        original = dict(self.downloaded)
        for key, value in (('Path', 'other/module'), ('Version', 'v1.26.5'),
                           ('Sum', 'h1:wrong'), ('Error', 'synthetic download failure'),
                           ('Dir', None), ('Dir', 'relative-cache')):
            with self.subTest(key=key, value=value):
                self.downloaded = dict(original, **{key: value})
                with self.assertRaises(SystemExit):
                    self.invoke()

    def test_model_bytes_mismatch_refuses_before_build(self):
        self.model.write_bytes(b'altered model')
        with self.assertRaisesRegex(SystemExit, 'MODEL_BYTES_MISMATCH'):
            self.invoke()

    def test_download_cannot_change_frozen_module_inputs(self):
        with self.assertRaisesRegex(SystemExit, 'MODULE_INPUTS_CHANGED'):
            self.invoke(mutate=True)


class ToolchainPinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.go = self.root / 'go/bin/go'
        self.go.parent.mkdir(parents=True)
        self.go.write_bytes(b'synthetic-go-version-go1.26.3')
        self.archive = self.root / 'synthetic-toolchain.tar.gz'
        with tarfile.open(self.archive, 'w:gz') as packed:
            entry = tarfile.TarInfo('go/bin/go')
            entry.size = len(self.go.read_bytes())
            packed.addfile(entry, io.BytesIO(self.go.read_bytes()))
        self.lock = {'files': [{'filename': self.archive.name,
                               'sha256': hashlib.sha256(self.archive.read_bytes()).hexdigest()}]}

    def test_verified_archive_is_bound_to_extracted_toolchain(self):
        root, evidence = verify_toolchain(self.go, self.archive, self.lock)
        self.assertEqual(root, self.go.parent.parent.resolve())
        self.assertEqual(evidence['sha256'], self.lock['files'][0]['sha256'])
        self.assertEqual(len(evidence['extracted_tree_sha256']), 64)

    def test_same_version_string_does_not_accept_tampered_binary(self):
        self.go.write_bytes(b'altered-synthetic-go-version-go1.26.3')
        with self.assertRaisesRegex(SystemExit, 'TOOLCHAIN_BYTES_MISMATCH'):
            verify_toolchain(self.go, self.archive, self.lock)

    def test_archive_mismatch_rejected_before_execution(self):
        self.archive.write_bytes(b'wrong archive')
        with self.assertRaisesRegex(SystemExit, 'TOOLCHAIN_ARCHIVE_MISMATCH'):
            verify_toolchain(self.go, self.archive, self.lock)

    def test_extra_file_and_symlink_are_rejected(self):
        (self.go.parent / 'extra').write_bytes(b'extra tool')
        with self.assertRaisesRegex(SystemExit, 'TOOLCHAIN_BYTES_MISMATCH'):
            verify_toolchain(self.go, self.archive, self.lock)
        (self.go.parent / 'extra').unlink()
        (self.go.parent / 'extra').symlink_to(self.go)
        with self.assertRaisesRegex(SystemExit, 'TOOLCHAIN_BYTES_MISMATCH'):
            verify_toolchain(self.go, self.archive, self.lock)


if __name__ == '__main__':
    unittest.main()
