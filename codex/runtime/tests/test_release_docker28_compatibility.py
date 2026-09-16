"""Issue #296 disposable preflight safety tests, never a real acceptance claim."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

DRIVER = Path(__file__).resolve().parents[2] / 'tests/integration/docker28-classic-driver.py'


class Docker28PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('docker28_driver', DRIVER)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def capability(self, side='producer'):
        return {'server': {'Version': '29.7.1' if side == 'producer' else '28.1.1',
                           'Os': 'linux', 'Arch': 'amd64'},
                'compose': '5.1.4' if side == 'producer' else '2.35.1',
                'info': {'ID': side + '-daemon', 'Driver': 'overlayfs' if side == 'producer' else 'overlay2',
                         'DriverStatus': [['driver-type', 'io.containerd.snapshotter.v1']] if side == 'producer' else [],
                         'DockerRootDir': '/var/lib/aisoft-296-' + side}}

    def test_exact_capabilities(self):
        for side in ('producer', 'consumer'):
            self.module.validate_capability(side, self.capability(side))

    def test_wrong_version_store_arch_root_fail_closed(self):
        for field, value in [('Version', '28.1.2'), ('Arch', 'arm64')]:
            cap = self.capability('consumer')
            cap['server'][field] = value
            with self.assertRaises(self.module.Blocked):
                self.module.validate_capability('consumer', cap)
        for field, value in [('Driver', 'overlayfs'), ('DockerRootDir', '/var/lib/docker')]:
            cap = self.capability('consumer')
            cap['info'][field] = value
            with self.assertRaises(self.module.Blocked):
                self.module.validate_capability('consumer', cap)

    def test_duplicate_daemon_rejected(self):
        a, b = self.capability(), self.capability('consumer')
        b['info']['ID'] = a['info']['ID']
        with self.assertRaises(self.module.Blocked):
            self.module.validate_pair({'producer': a, 'consumer': b})

    def test_unapproved_no_subprocess(self):
        with patch.dict('os.environ', {}, clear=True), patch.object(self.module, 'run') as run:
            with self.assertRaises(self.module.Blocked):
                self.module.require_approval()
            run.assert_not_called()

    def test_existing_vm_rejected_before_mutation(self):
        with patch.object(self.module, 'run', return_value='aisoft-296-consumer\n') as run:
            with self.assertRaises(self.module.Blocked):
                self.module.assert_names_available()
            self.assertEqual(run.call_count, 1)

    def test_immutable_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'evidence.json'
            self.module.write_json(path, {'result': 'BLOCKED'})
            with self.assertRaises(FileExistsError):
                self.module.write_json(path, {'result': 'PASS'})
            self.assertEqual(json.loads(path.read_text())['result'], 'BLOCKED')

    def test_real_runtime_identity_mismatch_is_not_normalized(self):
        producer = {'Id': 'sha256:' + 'a' * 64, 'Os': 'linux', 'Architecture': 'amd64'}
        consumer = {**producer, 'Id': 'sha256:' + 'b' * 64}
        result = self.module.compare_identity(producer, consumer)
        self.assertEqual(result['result'], 'BLOCKED')
        self.assertIn('image ID', result['message'])
        self.assertEqual(self.module.compare_identity(producer, producer)['result'], 'PASS')

    def test_pin_requires_official_urls_and_checksum(self):
        with self.assertRaises(self.module.Blocked):
            self.module.validate_software({'artifacts': [], 'registry_image': 'registry:2'})

    def test_cleanup_partial_provision_preserves_existing_vms(self):
        ownership = {'created': ['producer'], 'baseline_vm_names': ['AppServer', 'DockerLab']}
        before = 'AppServer\nDockerLab\naisoft-296-producer'
        with tempfile.TemporaryDirectory() as tmp, patch.object(self.module, 'require_approval'), \
                patch.object(self.module, 'state', return_value=ownership), \
                patch.object(self.module, 'verify_owner') as verify, \
                patch.object(self.module, 'source_evidence', return_value={}), \
                patch.object(self.module, 'run', side_effect=[before, '', 'AppServer\nDockerLab']) as run:
            result = self.module.cleanup(Path(tmp) / 'cleanup.json')
            self.assertEqual(result['result'], 'PASS')
            self.assertEqual(result['removed'], ['aisoft-296-producer'])
            self.assertEqual(run.call_args_list[1].args[0], ['orb', 'delete', '--force', 'aisoft-296-producer'])
            verify.assert_called_once_with('producer', ownership)

    def test_cleanup_marker_mismatch_prevents_any_deletion(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(self.module, 'require_approval'), \
                patch.object(self.module, 'state', return_value={'created': ['producer']}), \
                patch.object(self.module, 'verify_owner', side_effect=self.module.Blocked('marker mismatch')), \
                patch.object(self.module, 'run') as run:
            with self.assertRaises(self.module.Blocked):
                self.module.cleanup(Path(tmp) / 'cleanup.json')
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
