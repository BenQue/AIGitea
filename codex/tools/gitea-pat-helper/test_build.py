"""Toolchain verification tests use synthetic archives, never execute their Go."""
import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import json

import build

from build import verify_toolchain


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
