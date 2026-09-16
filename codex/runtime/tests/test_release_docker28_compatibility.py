"""Issue #296 disposable preflight safety tests, never a real acceptance claim."""
import importlib.util
import copy
import hashlib
import tarfile
import runpy
import sys
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
        ownership = {'nonce': 'a' * 32, 'created': ['producer'], 'baseline_vm_names': ['AppServer', 'DockerLab']}
        before = 'AppServer\nDockerLab\naisoft-296-producer'
        with tempfile.TemporaryDirectory() as tmp, patch.object(self.module, 'require_approval'), \
                patch.object(self.module, 'state', return_value=ownership), \
                patch.object(self.module, 'verify_owner') as verify, \
                patch.object(self.module, 'source_evidence', return_value={}), \
                patch.object(self.module, 'digest', return_value='f' * 64), \
                patch.object(self.module, 'journal'), \
                patch.object(self.module, 'run', side_effect=[before, '', 'AppServer\nDockerLab']) as run:
            result = self.module.cleanup(Path(tmp) / 'cleanup.json')
            self.assertEqual(result['result'], 'PASS')
            self.assertEqual(result['removed'], ['aisoft-296-producer'])
            self.assertEqual(run.call_args_list[1].args[0], ['orb', 'delete', '--force', 'aisoft-296-producer'])
            verify.assert_called_once_with('producer', ownership)

    def test_cleanup_marker_mismatch_prevents_any_deletion(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(self.module, 'require_approval'), \
                patch.object(self.module, 'state', return_value={'created': ['producer'], 'baseline_vm_names': []}), \
                patch.object(self.module, 'verify_owner', side_effect=self.module.Blocked('marker mismatch')), \
                patch.object(self.module, 'run', return_value='aisoft-296-producer') as run:
            with self.assertRaises(self.module.Blocked):
                self.module.cleanup(Path(tmp) / 'cleanup.json')
            self.assertEqual(run.call_args_list[0].args[0], ['orb', 'list', '--quiet'])
            self.assertEqual(run.call_count, 1)

    def test_create_failure_preserves_intent_before_machine_id(self):
        ownership = {'created': [], 'creation_steps': {}, 'machine_ids': {}, 'nonce': 'a' * 32}
        history = []
        with patch.object(self.module, 'journal', side_effect=lambda x: history.append(copy.deepcopy(x))), \
                patch.object(self.module, 'run', return_value=''), \
                patch.object(self.module, 'vm', side_effect=self.module.Blocked('injected machine-id failure')):
            with self.assertRaisesRegex(self.module.Blocked, 'must not be adopted or deleted'):
                self.module.create_vm('producer', ownership)
        self.assertEqual(history[0]['creation_steps']['producer'], 'create-pending')
        self.assertEqual(history[1]['created'], ['producer'])
        self.assertEqual(history[1]['creation_steps']['producer'], 'created-unverified')
        self.assertEqual(ownership['creation_intent'], 'producer')

    def test_cleanup_second_vm_failure_preserves_first_completion_and_can_resume(self):
        ownership = {'nonce': 'a' * 32, 'created': ['producer', 'consumer'], 'baseline_vm_names': ['AppServer'], 'deleted': []}
        history = []
        with tempfile.TemporaryDirectory() as tmp, patch.object(self.module, 'require_approval'), \
                patch.object(self.module, 'state', return_value=ownership), \
                patch.object(self.module, 'verify_owner'), \
                patch.object(self.module, 'source_evidence', return_value={}), \
                patch.object(self.module, 'digest', return_value='f' * 64), \
                patch.object(self.module, 'journal', side_effect=lambda x: history.append(copy.deepcopy(x))):
            evidence = Path(tmp) / 'cleanup.json'
            with patch.object(self.module, 'run', side_effect=['AppServer\naisoft-296-producer\naisoft-296-consumer', '', self.module.Blocked('second deletion failed')]):
                with self.assertRaises(self.module.Blocked):
                    self.module.cleanup(evidence)
            self.assertEqual(history[-1]['deleted'], ['producer'])
            self.assertEqual(history[-1]['deletion_intent'], 'consumer')
            with patch.object(self.module, 'run', side_effect=['AppServer\naisoft-296-consumer', '', 'AppServer']) as run:
                self.assertEqual(self.module.cleanup(evidence)['result'], 'PASS')
            self.assertEqual(run.call_args_list[1].args[0], ['orb', 'delete', '--force', 'aisoft-296-consumer'])

    def test_missing_vm_without_completion_record_never_deleted(self):
        ownership = {'created': ['producer'], 'baseline_vm_names': [], 'deletion_intent': 'producer'}
        with tempfile.TemporaryDirectory() as tmp, patch.object(self.module, 'require_approval'), \
                patch.object(self.module, 'state', return_value=ownership), \
                patch.object(self.module, 'run', return_value='') as run:
            with self.assertRaisesRegex(self.module.Blocked, 'without a completed deletion record'):
                self.module.cleanup(Path(tmp) / 'cleanup.json')
            self.assertEqual(run.call_count, 1)

    def test_orb_vm_argv_uses_supported_run_syntax(self):
        with patch.object(self.module, 'run', return_value='machine-id') as run:
            self.assertEqual(self.module.vm('producer', 'cat', '/etc/machine-id'), 'machine-id')
            self.assertEqual(run.call_args.args[0], ['orb', 'run', '-m', 'aisoft-296-producer', '-u', 'root', 'cat', '/etc/machine-id'])

    def test_resume_requires_exact_successful_creation_and_isolation(self):
        ownership = {'created': ['producer'], 'creation_intent': 'producer',
                     'creation_steps': {'producer': 'created-unverified'}, 'baseline_vm_names': []}
        orb_id, machine_id = 'A' * 26, 'b' * 32
        current = {'id': orb_id, 'name': 'aisoft-296-producer',
                   'image': {'arch': 'amd64', 'distro': 'ubuntu', 'version': 'noble'},
                   'config': {'isolated': True, 'forward_ssh_agent': False, 'memory_limit_mib': 4096,
                              'cpu_limit': 2, 'disk_limit_bytes': 20 * 1024**3,
                              'mounts': [{'source': str(self.module.LAB), 'destination': self.module.MOUNT}]}}
        self.module.validate_resume(ownership, orb_id, machine_id, [current])
        for mutate in ('pending', 'wrong-id', 'shared', 'baseline'):
            owner, vm = copy.deepcopy(ownership), copy.deepcopy(current)
            if mutate == 'pending':
                owner['creation_steps']['producer'] = 'create-pending'
            elif mutate == 'wrong-id':
                vm['id'] = 'C' * 26
            elif mutate == 'shared':
                vm['config']['forward_ssh_agent'] = True
            else:
                owner['baseline_vm_names'] = ['aisoft-296-producer']
            with self.assertRaises(self.module.Blocked):
                self.module.validate_resume(owner, orb_id, machine_id, [vm])

    def test_installer_validates_real_tar_root_and_rejects_unsafe_members(self):
        script = self.module.FIXTURES.joinpath('install-daemon.sh').read_text()
        program = script.split("<<'PY'\n", 1)[1].split('\nPY', 1)[0]
        for case in ('valid-root', 'traversal', 'symlink'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                archive = root / 'engine.tgz'
                with tarfile.open(archive, 'w:gz') as output:
                    entry = tarfile.TarInfo('docker')
                    entry.type = tarfile.DIRTYPE
                    output.addfile(entry)
                    if case != 'valid-root':
                        entry = tarfile.TarInfo('docker/../escape' if case == 'traversal' else 'docker/link')
                        if case == 'symlink':
                            entry.type, entry.linkname = tarfile.SYMTYPE, '/etc/passwd'
                        output.addfile(entry)
                root.joinpath('software-lock.json').write_text(json.dumps({'artifacts': [{
                    'id': 'engine-producer', 'filename': 'engine.tgz',
                    'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}]}))
                with patch('sys.argv', ['validate', 'producer']), patch('pathlib.Path', return_value=root):
                    if case == 'valid-root':
                        exec(compile(program, 'install-daemon-archive-validation', 'exec'), {})
                    else:
                        with self.assertRaises(AssertionError):
                            exec(compile(program, 'install-daemon-archive-validation', 'exec'), {})

    def test_candidate_and_final_matrix_exact_bounds(self):
        sys.path.insert(0, str(self.module.ROOT / 'codex/runtime'))
        from aisoft_release.compatibility import DockerCapability, require_supported
        from aisoft_release.errors import ReleaseError
        functions = runpy.run_path(str(self.module.FIXTURES / 'lifecycle.py'))
        original = json.loads((self.module.ROOT / 'docker-release/compatibility/image-stores-v1.json').read_text())
        candidate = functions['candidate_matrix'](original, 'a' * 40)
        self.assertEqual(candidate['rows'][:len(original['rows'])], original['rows'])
        self.assertEqual(functions['candidate_matrix'](candidate, 'a' * 40), candidate)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'matrix.json'
            for matrix in (candidate, original):
                path.write_text(json.dumps(matrix))
                exact = DockerCapability('28.1.1', '2.35.1', 'linux', 'amd64', 'classic')
                is_supported = any(row['image_store'] == 'classic' and row['status'] == 'supported' and row['engine']['minimum'] == '28.1.1' for row in matrix['rows'])
                if is_supported:
                    require_supported(exact, path)
                else:
                    with self.assertRaises(ReleaseError):
                        require_supported(exact, path)
                for engine, compose, arch, store in (
                    ('28.1.0', '2.35.1', 'amd64', 'classic'), ('28.1.2', '2.35.1', 'amd64', 'classic'),
                    ('28.1.1', '2.35.0', 'amd64', 'classic'), ('28.1.1', '2.35.2', 'amd64', 'classic'),
                    ('28.1.1', '2.35.1', 'amd64', 'containerd'), ('28.1.1', '2.35.1', 'arm64', 'classic'),
                    ('29.7.1', '2.35.1', 'amd64', 'classic')):
                    with self.subTest(engine=engine, compose=compose, arch=arch, store=store), self.assertRaises(ReleaseError):
                        require_supported(DockerCapability(engine, compose, 'linux', arch, store), path)

    def test_archive_requires_exact_journal_bound_cleanup_and_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            lab = Path(tmp) / 'lab'
            lab.mkdir()
            nonce = 'a' * 32
            ownership = {'names': self.module.NAMES, 'nonce': nonce, 'created': list(self.module.SIDES),
                         'deleted': list(self.module.SIDES), 'creation_intent': None, 'deletion_intent': None,
                         'baseline_vm_names': ['AppServer']}
            (lab / 'ownership.json').write_text(json.dumps(ownership))
            (lab / 'preserve.txt').write_text('immutable previous run')
            receipt = Path(tmp) / 'cleanup.json'
            receipt.write_text(json.dumps({'result': 'PASS', 'run_id': nonce,
                'ownership_sha256': self.module.digest(lab / 'ownership.json'),
                'removed': list(self.module.NAMES.values()), 'baseline_vm_names': ['AppServer'], 'preserved_vm_names': ['AppServer']}))
            with patch.object(self.module, 'LAB', lab), patch.object(self.module, 'require_approval'), \
                    patch.object(self.module, 'source_evidence', return_value={}):
                with patch.object(self.module, 'run', return_value='AppServer\naisoft-296-consumer'):
                    with self.assertRaises(self.module.Blocked):
                        self.module.archive_cleaned_lab(receipt, nonce)
                self.assertTrue((lab / 'preserve.txt').exists())
                with patch.object(self.module, 'run', return_value='AppServer'):
                    result = self.module.archive_cleaned_lab(receipt, nonce)
                self.assertEqual(result['result'], 'PASS')
                self.assertFalse(lab.exists())
                self.assertEqual(Path(result['destination']).joinpath('preserve.txt').read_text(), 'immutable previous run')

    def test_synthetic_architecture_and_compose_pass_real_contract_parsers(self):
        sys.path.insert(0, str(self.module.ROOT / 'codex/runtime'))
        from aisoft_release.contract import load_release_artifact
        from aisoft_release.compose import validate_compose_model
        from tests.release_test_support import create_release, SHA_A, update_manifest, write_json, sha256
        functions = runpy.run_path(str(self.module.FIXTURES / 'lifecycle.py'))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, _, manifest = create_release(root, SHA_A)
            release_dir = root / 'releases' / SHA_A
            arch = functions['architecture'](self.module.software())
            write_json(release_dir / 'architecture.lock.json', arch)
            def apply(value):
                value['architecture'].update(profile_id=arch['profile_id'], project_id=arch['project_id'],
                                             catalog_revision=arch['catalog_revision'], sha256=sha256(release_dir / 'architecture.lock.json'))
            update_manifest(release_dir, apply)
            files = load_release_artifact(root / 'releases', SHA_A)
            images = {image.service: {'runtime_reference': image.runtime_reference} for image in files.manifest.images}
            compose = functions['compose_source'](SHA_A, images)
            validate_compose_model(compose, files.manifest)
            self.assertEqual(compose['services']['migrate']['profiles'], ['migration'])
            self.assertFalse(compose['services']['web'].get('ports'))

    def test_lifecycle_mutation_counts_ignore_readonly_calls(self):
        functions = runpy.run_path(str(self.module.FIXTURES / 'lifecycle.py'))
        calls = [['image', 'inspect', 'ref'], ['compose', '--file', 'f', 'config'],
                 ['image', 'pull', 'ref'], ['image', 'load', '-i', 'archive'], ['compose', '--file', 'f', 'run', 'migrate']]
        self.assertEqual(functions['mutation_count'](calls), 3)


if __name__ == '__main__':
    unittest.main()
