"""Toolchain verification tests use synthetic archives, never execute their Go."""
import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from build import verify_toolchain


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
