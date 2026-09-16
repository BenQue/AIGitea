#!/usr/bin/env python3
"""Issue #296 exact disposable lab and cross-store identity prerequisite.

Default is NOT RUN. This gate never claims lifecycle support; lifecycle must be
implemented and accepted separately after the unchanged identity contract passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tarfile
import io
import uuid

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / 'codex/tests/fixtures/docker28-classic'
LAB = Path('/private/tmp/aisoft-296-lab')
MOUNT = '/mnt/aisoft296'
SIDES = ('producer', 'consumer')
NAMES = {side: 'aisoft-296-' + side for side in SIDES}
VERSIONS = {'producer': ('29.7.1', '5.1.4'), 'consumer': ('28.1.1', '2.35.1')}
MARKER = 'issue-296-local-disposable-approved'
REGISTRY_NAME = 'aisoft-296-registry'
TRANSPORT_TAG = 'aisoft.local/issue296/identity:fixture'


class Blocked(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise Blocked(message)


def require_approval():
    require(os.environ.get('AISOFT_296_APPROVED') == MARKER, 'Issue #296 approval marker missing')


def run(argv, *, stdin=None, timeout=60):
    # Never inherit Docker, SSH-agent, provider, or credential environment into a VM command.
    env = {'PATH': os.environ['PATH'], 'HOME': os.environ.get('HOME', ''), 'LC_ALL': 'C'}
    result = subprocess.run([str(v) for v in argv], input=stdin, text=True,
                            capture_output=True, env=env, timeout=timeout)
    if result.returncode:
        raise Blocked('command failed: ' + ' '.join(map(str, argv)) + '\n' + result.stderr[-4000:])
    return result.stdout.strip()


def vm(side, *args, stdin=None, timeout=60):
    require(side in SIDES, 'unknown VM side')
    return run(['orb', 'run', '-m', NAMES[side], '-u', 'root', *args], stdin=stdin, timeout=timeout)


def docker(side, *args, timeout=120):
    return vm(side, '/usr/local/bin/docker', '--host', 'unix:///run/aisoft-296.sock', *args, timeout=timeout)


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def write_json(path, value):
    path = Path(path)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
    path.chmod(0o444)


def validate_software(value):
    artifacts = value.get('artifacts', [])
    expected = {f'{kind}-{side}' for side in SIDES for kind in ('engine', 'compose')}
    require(len(artifacts) == 4 and {a.get('id') for a in artifacts} == expected,
            'software manifest must pin exactly four Engine/Compose binaries')
    for item in artifacts:
        kind, side = item['id'].split('-')
        version = VERSIONS[side][0 if kind == 'engine' else 1]
        url = (f'https://download.docker.com/linux/static/stable/x86_64/docker-{version}.tgz' if kind == 'engine'
               else f'https://github.com/docker/compose/releases/download/v{version}/docker-compose-linux-x86_64')
        require(item.get('url') == url, 'software URL is not the exact official version')
        require(re.fullmatch('[0-9a-f]{64}', item.get('sha256', '')) is not None, 'software checksum missing')
        require(item.get('filename') == (f'docker-{version}.tgz' if kind == 'engine' else f'docker-compose-{version}'),
                'unexpected software filename')
    require(re.fullmatch(r'(?:docker.io/library/)?registry@sha256:[0-9a-f]{64}', value.get('registry_image', '')) is not None,
            'Registry image must be official and digest-pinned')
    return value


def software():
    return validate_software(json.loads((FIXTURES / 'software-lock.json').read_text()))


def assert_names_available():
    existing = set(run(['orb', 'list', '--quiet']).splitlines())
    require(not existing.intersection(NAMES.values()), 'task VM already exists; refuse reuse or deletion')


def state():
    require(LAB.is_dir() and not LAB.is_symlink(), 'owned lab directory missing or symlink')
    value = json.loads((LAB / 'ownership.json').read_text())
    require(value['names'] == NAMES and re.fullmatch('[0-9a-f]{32}', value['nonce']) is not None, 'invalid ownership record')
    return value


def verify_owner(side, ownership):
    expected = f"issue296:{ownership['nonce']}:{side}"
    require(vm(side, 'cat', '/etc/aisoft-296-owner') == expected, 'VM ownership marker mismatch')
    require(vm(side, 'cat', '/etc/machine-id') == ownership['machine_ids'][side], 'VM machine-id changed')


def source_evidence():
    paths = [Path(__file__), FIXTURES / 'software-lock.json', FIXTURES / 'install-daemon.sh',
             FIXTURES / 'identity.txt']
    paths += sorted((ROOT / 'codex/runtime/aisoft_release').glob('*.py'))
    return {'source_sha': run(['git', '-C', ROOT, 'rev-parse', 'HEAD']),
            'files_sha256': {str(p.relative_to(ROOT)): digest(p) for p in paths}}


def approval_plan():
    return {'issue': 296, 'status': 'NOT RUN', 'scope': 'local-disposable-only',
            'source': source_evidence(), 'software': software(),
            'vms': [{'name': NAMES[s], 'arch': 'amd64', 'cpus': 2, 'memory': '4G', 'disk': '20G',
                     'isolated': True, 'mount': str(LAB) + ':' + MOUNT,
                     'engine': VERSIONS[s][0], 'compose': VERSIONS[s][1],
                     'data_root': '/var/lib/aisoft-296-' + s} for s in SIDES],
            'resources': {'producer_containers': [REGISTRY_NAME], 'consumer_containers': [],
                          'registry_port': 5296, 'images': [TRANSPORT_TAG, software()['registry_image']], 'fixture_content_sha256': digest(FIXTURES / 'identity.txt'), 'consumer_digest_plan': 'created after producer push and before consumer mutation',
                          'volumes': [], 'networks': [], 'build_cache': 'exclusive disposable producer VM'},
            'lifecycle': 'NOT RUN: gated by unchanged runtime cross-store identity'}


def journal(ownership):
    """Atomically record each ownership transition before the next mutation."""
    temporary = LAB / ('.ownership-' + uuid.uuid4().hex + '.json')
    with temporary.open('x') as stream:
        json.dump(ownership, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(0o600)
    os.replace(temporary, LAB / 'ownership.json')


def create_vm(side, ownership):
    ownership['creation_intent'] = side
    ownership['creation_steps'][side] = 'create-pending'
    journal(ownership)
    try:
        run(['orb', 'create', '--isolated', '--mount', str(LAB) + ':' + MOUNT,
             '--memory', '4G', '--cpus', '2', '--disk', '20G', '-a', 'amd64', 'ubuntu:24.04', NAMES[side]], timeout=300)
        ownership['created'].append(side)
        ownership['creation_steps'][side] = 'created-unverified'
        journal(ownership)
        ownership['machine_ids'][side] = vm(side, 'cat', '/etc/machine-id')
        ownership['creation_steps'][side] = 'machine-id-read'
        journal(ownership)
        vm(side, 'sh', '-c', 'umask 077; cat > /etc/aisoft-296-owner', stdin=f"issue296:{ownership['nonce']}:{side}\n")
        verify_owner(side, ownership)
        ownership['creation_steps'][side] = 'marker-verified'
        ownership['creation_intent'] = None
        journal(ownership)
    except (Blocked, OSError, subprocess.TimeoutExpired) as exc:
        raise Blocked(f"creation interrupted for exact VM {NAMES[side]}; inspect {LAB}/ownership.json and orb list --quiet; "
                      "unverified VM must not be adopted or deleted automatically: " + str(exc)) from exc


def provision(downloads):
    require_approval()
    pins = software()
    assert_names_available()
    baseline = sorted(run(['orb', 'list', '--quiet']).splitlines())
    require(not LAB.exists() and not LAB.is_symlink(), 'lab path already exists; refuse reuse')
    for item in pins['artifacts']:
        path = downloads / item['filename']
        require(path.is_file() and not path.is_symlink() and digest(path) == item['sha256'], 'download checksum mismatch')
    LAB.mkdir(mode=0o700)
    for item in pins['artifacts']:
        shutil.copyfile(downloads / item['filename'], LAB / item['filename'])
    shutil.copyfile(FIXTURES / 'install-daemon.sh', LAB / 'install-daemon.sh')
    shutil.copyfile(FIXTURES / 'software-lock.json', LAB / 'software-lock.json')
    write_json(LAB / 'approval-plan.json', approval_plan())
    ownership = {'names': NAMES, 'nonce': uuid.uuid4().hex, 'machine_ids': {}, 'created': [],
                 'baseline_vm_names': baseline, 'creation_intent': None, 'creation_steps': {},
                 'deleted': [], 'deletion_intent': None}
    journal(ownership)
    for side in SIDES:
        create_vm(side, ownership)
    address = producer_address()
    ownership['registry_address'] = address + ':5296'
    journal(ownership)
    for side in SIDES:
        vm(side, 'bash', MOUNT + '/install-daemon.sh', side, address + ':5296', timeout=300)
        ownership['creation_steps'][side] = 'installed'
        journal(ownership)
    return preflight()


def validate_resume(ownership, orb_id, machine_id, inventory):
    require(ownership['created'] == ['producer'] and ownership.get('creation_intent') == 'producer' and
            ownership.get('creation_steps') == {'producer': 'created-unverified'},
            'resume only accepts a journaled successful producer create, never create-pending')
    require(re.fullmatch('[A-Z0-9]{26}', orb_id or '') is not None and
            re.fullmatch('[0-9a-f]{32}', machine_id or '') is not None, 'exact independently verified IDs required')
    require(not set(ownership['baseline_vm_names']).intersection(NAMES.values()), 'created VM overlaps baseline')
    require({v['name'] for v in inventory} == set(ownership['baseline_vm_names']) | {NAMES['producer']}, 'VM inventory changed')
    matches = [v for v in inventory if v['name'] == NAMES['producer']]
    require(len(matches) == 1 and matches[0]['id'] == orb_id, 'OrbStack VM ID does not match independent evidence')
    current = matches[0]
    config = current['config']
    require(current['image']['arch'] == 'amd64' and current['image']['distro'] == 'ubuntu' and
            current['image']['version'] == 'noble', 'unexpected resumed VM image')
    require(config.get('isolated') is True and config.get('forward_ssh_agent') is False and
            config.get('memory_limit_mib') == 4096 and config.get('cpu_limit') == 2 and
            config.get('disk_limit_bytes') == 20 * 1024**3 and
            config.get('mounts') == [{'source': str(LAB), 'destination': MOUNT}], 'VM isolation/resources changed')


def resume_provision(orb_id, machine_id, reviewed_install_sha256):
    require_approval()
    ownership = state()
    original = json.loads((LAB / 'approval-plan.json').read_text())
    pins = software()
    require(digest(FIXTURES / 'software-lock.json') == original['source']['files_sha256'][str((FIXTURES / 'software-lock.json').relative_to(ROOT))], 'original software lock changed')
    require(digest(LAB / 'software-lock.json') == digest(FIXTURES / 'software-lock.json'), 'copied software lock changed')
    require(re.fullmatch('[0-9a-f]{64}', reviewed_install_sha256 or '') is not None and
            digest(FIXTURES / 'install-daemon.sh') == reviewed_install_sha256, 'reviewed installer hash missing or mismatched')
    require(digest(LAB / 'install-daemon.sh') == original['source']['files_sha256'][str((FIXTURES / 'install-daemon.sh').relative_to(ROOT))], 'original installer copy changed')
    for item in pins['artifacts']:
        require(digest(LAB / item['filename']) == item['sha256'], 'original downloaded artifact changed')
    inventory = json.loads(run(['orb', 'list', '--format', 'json']))
    validate_resume(ownership, orb_id, machine_id, inventory)
    require(vm('producer', 'cat', '/etc/machine-id') == machine_id, 'machine-id does not match independent evidence')
    marker = vm('producer', 'sh', '-c', 'if [ -e /etc/aisoft-296-owner ]; then cat /etc/aisoft-296-owner; fi')
    expected = f"issue296:{ownership['nonce']}:producer"
    require(marker in ('', expected), 'existing owner marker conflicts')
    # Preserve the first plan, link a separately reviewable correction before mutation.
    write_json(LAB / 'resume-source-plan.json', {
        'original_plan_sha256': digest(LAB / 'approval-plan.json'), 'source': source_evidence(),
        'orb_id': orb_id, 'machine_id': machine_id,
        'reviewed_install_sha256': reviewed_install_sha256,
        'correction': 'OrbStack run argv and official Docker archive root directory validation'})
    ownership['machine_ids']['producer'] = machine_id
    ownership['orb_ids'] = {'producer': orb_id}
    journal(ownership)
    if not marker:
        vm('producer', 'sh', '-c', 'umask 077; cat > /etc/aisoft-296-owner', stdin=expected + '\n')
    verify_owner('producer', ownership)
    ownership['creation_steps']['producer'] = 'marker-verified'
    ownership['creation_intent'] = None
    journal(ownership)
    shutil.copyfile(FIXTURES / 'install-daemon.sh', LAB / 'install-daemon.sh')
    create_vm('consumer', ownership)
    address = producer_address()
    ownership['registry_address'] = address + ':5296'
    journal(ownership)
    for side in SIDES:
        vm(side, 'bash', MOUNT + '/install-daemon.sh', side, address + ':5296', timeout=300)
        ownership['creation_steps'][side] = 'installed'
        journal(ownership)
    return preflight()


def validate_capability(side, value):
    server, info = value['server'], value['info']
    require((server.get('Version'), value['compose'].removeprefix('v')) == VERSIONS[side], 'wrong exact Engine/Compose version')
    require((server.get('Os'), server.get('Arch')) == ('linux', 'amd64'), 'server must be linux/amd64')
    require(bool(info.get('ID')), 'daemon ID missing')
    require(info.get('DockerRootDir') == '/var/lib/aisoft-296-' + side, 'unexpected Docker data-root')
    markers = [row for row in (info.get('DriverStatus') or []) if row[0] == 'driver-type']
    if side == 'producer':
        require(info.get('Driver') == 'overlayfs' and markers == [['driver-type', 'io.containerd.snapshotter.v1']], 'producer is not containerd store')
    else:
        require(info.get('Driver') == 'overlay2' and not markers, 'consumer is not classic overlay2')


def validate_pair(values):
    for side in SIDES:
        validate_capability(side, values[side])
    require(values['producer']['info']['ID'] != values['consumer']['info']['ID'], 'shared daemon forbidden')


def preflight():
    require_approval()
    ownership = state()
    approved_source = json.loads((LAB / 'approval-plan.json').read_text())['source']
    resumed = LAB / 'resume-source-plan.json'
    if resumed.exists():
        correction = json.loads(resumed.read_text())
        require(correction['original_plan_sha256'] == digest(LAB / 'approval-plan.json'), 'original plan changed after resume')
        approved_source = correction['source']
    require(approved_source['files_sha256'] == source_evidence()['files_sha256'], 'approved source bytes changed')
    require(digest(LAB / 'software-lock.json') == digest(FIXTURES / 'software-lock.json'), 'software pin changed')
    values = {}
    for side in SIDES:
        verify_owner(side, ownership)
        values[side] = {'server': json.loads(docker(side, 'version', '--format', '{{json .Server}}')),
                        'compose': docker(side, 'compose', 'version', '--short'),
                        'info': {k: v for k, v in json.loads(docker(side, 'info', '--format', '{{json .}}')).items()
                                 if k in ('ID', 'Driver', 'DriverStatus', 'DockerRootDir')},
                        'installed_binary_checksums': vm(side, 'sha256sum', '/usr/local/bin/docker', '/usr/local/bin/dockerd',
                                                        '/usr/local/bin/containerd', '/usr/local/lib/docker/cli-plugins/docker-compose').splitlines()}
    validate_pair(values)
    return {'result': 'PASS', 'capabilities': values, 'source': source_evidence()}


def compare_identity(producer, consumer):
    sys.path.insert(0, str(ROOT / 'codex/runtime'))
    from aisoft_release.contract import ImageSpec
    from aisoft_release.errors import ContractError
    from aisoft_release.transport import _verify_content
    image = ImageSpec('identity', 'fixture@' + producer['Id'], producer['Id'], producer['Id'], TRANSPORT_TAG, TRANSPORT_TAG)
    try:
        _verify_content(consumer, image)
    except ContractError as exc:
        return {'result': 'BLOCKED', 'code': exc.code, 'message': exc.safe_message,
                'producer_image_id': producer['Id'], 'consumer_image_id': consumer['Id']}
    return {'result': 'PASS', 'producer_image_id': producer['Id'], 'consumer_image_id': consumer['Id']}


def inspect(side, reference):
    image = json.loads(docker(side, 'image', 'inspect', reference))[0]
    return {key: image.get(key) for key in ('Id', 'RepoTags', 'RepoDigests', 'Os', 'Architecture', 'RootFS', 'Descriptor')}


def producer_address():
    address = vm('producer', 'sh', '-c', "ip -4 route get 1.1.1.1 | sed -n 's/.* src \\([^ ]*\\).*/\\1/p'").splitlines()[0]
    require(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', address) is not None, 'producer IPv4 not detected')
    return address


def identity(evidence):
    require_approval()
    require(not evidence.exists() and evidence.parent.is_dir(), 'immutable evidence path unavailable')
    probes = preflight()
    for side in SIDES:
        require(docker(side, 'ps', '-aq') == '', 'unexpected container before mutation')
        require(docker(side, 'image', 'ls', '-aq') == '', 'unexpected image before mutation')
        require(docker(side, 'volume', 'ls', '-q') == '', 'unexpected volume before mutation')
    pins = software()
    payload = (FIXTURES / 'identity.txt').read_bytes()
    with tarfile.open(LAB / 'identity-rootfs.tar', mode='x') as archive:
        entry = tarfile.TarInfo('identity.txt')
        entry.size, entry.mode, entry.mtime = len(payload), 0o644, 0
        archive.addfile(entry, io.BytesIO(payload))
    # Registry is reachable only through the task producer VM; no host Docker socket.
    address = producer_address()
    require(address + ':5296' == state()['registry_address'], 'Registry address changed')
    reference_tag = f'{address}:5296/issue296/identity:fixture'
    plan = {'capabilities': probes['capabilities'], 'source': probes['source'], 'software': pins,
            'resources': {'vms': NAMES, 'containers': [REGISTRY_NAME], 'images': [pins['registry_image'], reference_tag, TRANSPORT_TAG],
                          'registry_address': address + ':5296', 'volumes': [], 'networks': []}}
    write_json(LAB / 'identity-approval-plan.json', plan)
    result = {'issue': 296, 'kind': 'real-cross-store-identity-prerequisite', 'plan': plan,
              'lifecycle': 'NOT RUN', 'cleanup': 'NOT RUN'}
    try:
        docker('producer', 'pull', '--platform', 'linux/amd64', pins['registry_image'], timeout=300)
        result['registry_image'] = inspect('producer', pins['registry_image'])
        docker('producer', 'run', '-d', '--name', REGISTRY_NAME, '--label', 'com.aisoft.issue=296',
               '--tmpfs', '/var/lib/registry:rw,size=268435456', '-p', address + ':5296:5000', pins['registry_image'])
        for _ in range(30):
            try:
                vm('producer', 'curl', '--fail', '--silent', f'http://{address}:5296/v2/')
                break
            except Blocked:
                time.sleep(1)
        else:
            raise Blocked('Registry readiness timeout')
        docker('producer', 'import', '--platform', 'linux/amd64', '--change', 'LABEL com.aisoft.issue=296',
               MOUNT + '/identity-rootfs.tar', reference_tag)
        docker('producer', 'push', reference_tag)
        producer_tag = inspect('producer', reference_tag)
        references = [r for r in producer_tag['RepoDigests'] if r.startswith(address + ':5296/issue296/identity@sha256:')]
        require(len(references) == 1, 'producer digest reference ambiguous')
        reference = references[0]
        docker('producer', 'pull', reference)
        producer = inspect('producer', reference)
        vm('producer', 'curl', '--fail', '--silent', '-H', 'Accept: application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json',
           '-o', MOUNT + '/registry-manifest.json',
           f'http://{address}:5296/v2/issue296/identity/manifests/' + reference.split('@')[1])
        manifest_bytes = (LAB / 'registry-manifest.json').read_bytes()
        manifest = json.loads(manifest_bytes)
        result['manifest'] = manifest
        result['manifest_bytes_sha256'] = hashlib.sha256(manifest_bytes).hexdigest()
        require('sha256:' + result['manifest_bytes_sha256'] == reference.split('@')[1], 'Registry manifest byte hash mismatch')
        docker('producer', 'tag', reference, TRANSPORT_TAG)
        docker('producer', 'save', '-o', MOUNT + '/identity.tar', TRANSPORT_TAG)
        result['offline_archive_sha256'] = digest(LAB / 'identity.tar')
        write_json(LAB / 'consumer-approval-plan.json', {
            'source': probes['source'], 'capabilities': probes['capabilities'],
            'resources': {'consumer_vm': NAMES['consumer'], 'images': [reference, TRANSPORT_TAG],
                          'containers': [], 'volumes': [], 'networks': []},
            'producer_inspect': producer, 'registry_manifest': manifest,
            'offline_archive_sha256': result['offline_archive_sha256']})
        docker('consumer', 'pull', reference)
        consumer_registry = inspect('consumer', reference)
        require(consumer_registry['Id'] == manifest['config']['digest'], 'classic Id is not Registry config digest')
        require(producer['RootFS'] == consumer_registry['RootFS'], 'cross-store RootFS differs')
        result.update({'reference': reference, 'producer': producer, 'consumer_registry': consumer_registry,
                       'registry_identity': compare_identity(producer, consumer_registry)})
        # Remove the Registry image before load to prove the offline transport materializes it.
        docker('consumer', 'image', 'rm', reference)
        require(docker('consumer', 'image', 'ls', '-aq') == '', 'consumer not empty before offline load')
        docker('consumer', 'load', '-i', MOUNT + '/identity.tar')
        consumer_offline = inspect('consumer', TRANSPORT_TAG)
        require(consumer_offline['RootFS'] == producer['RootFS'], 'offline RootFS differs')
        result['consumer_offline'] = consumer_offline
        result['offline_identity'] = compare_identity(producer, consumer_offline)
        result['result'] = ('PASS' if all(result[k]['result'] == 'PASS' for k in ('registry_identity', 'offline_identity')) else 'BLOCKED')
        result['next_gate'] = ('Implement and run full public lifecycle; support remains NOT RUN' if result['result'] == 'PASS'
                               else 'Runtime identity contract change requires a separately approved spec amendment')
    except (Blocked, subprocess.TimeoutExpired) as exc:
        result['result'] = 'BLOCKED'
        result['error'] = str(exc)
    finally:
        write_json(evidence, result)
    return result


def cleanup(evidence):
    require_approval()
    ownership = state()
    require(not evidence.exists() and evidence.parent.is_dir(), 'immutable cleanup evidence path unavailable')
    created = ownership['created']
    require(bool(created) and len(set(created)) == len(created) and set(created).issubset(SIDES), 'invalid created VM allowlist')
    require(ownership.get('creation_intent') is None,
            'creation identity unresolved; inspect exact VM ' + NAMES.get(ownership.get('creation_intent'), 'unknown') +
            ' and ownership.json; no automatic adoption/deletion')
    deleted = ownership.get('deleted', [])
    require(len(set(deleted)) == len(deleted) and set(deleted).issubset(created), 'invalid deletion journal')
    before = set(run(['orb', 'list', '--quiet']).splitlines())
    require(not ({NAMES[s] for s in deleted} & before), 'a deleted VM name reappeared; refuse cleanup')
    remaining = [side for side in created if side not in deleted]
    require({NAMES[s] for s in remaining}.issubset(before),
            'VM absent without a completed deletion record; inspect deletion_intent and exact VM inventory; no automatic adoption')
    owned_names = {NAMES[side] for side in remaining}
    require(set(ownership['baseline_vm_names']).issubset(before - owned_names), 'pre-existing VM inventory drift')
    for side in remaining:
        verify_owner(side, ownership)
    # Delete only verified owned VMs. Persist each completed removal before the next.
    for side in remaining:
        ownership['deletion_intent'] = side
        journal(ownership)
        run(['orb', 'delete', '--force', NAMES[side]], timeout=120)
        ownership.setdefault('deleted', []).append(side)
        ownership['deletion_intent'] = None
        journal(ownership)
    after = set(run(['orb', 'list', '--quiet']).splitlines())
    require(after == before - owned_names, 'VM inventory changed outside exact allowlist')
    result = {'result': 'PASS', 'removed': sorted(NAMES[s] for s in ownership['deleted']),
              'baseline_vm_names': ownership['baseline_vm_names'],
              'before_vm_names': sorted(before), 'preserved_vm_names': sorted(after), 'source': source_evidence()}
    write_json(evidence, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('not-run', 'plan', 'provision', 'resume-provision', 'preflight', 'identity', 'cleanup'), nargs='?', default='not-run')
    parser.add_argument('--downloads', type=Path)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--orb-id')
    parser.add_argument('--machine-id')
    parser.add_argument('--reviewed-install-sha256')
    args = parser.parse_args()
    try:
        if args.action == 'not-run':
            result = {'result': 'NOT RUN', 'message': 'Issue #296 requires explicit local disposable approval marker'}
        elif args.action == 'plan':
            result = approval_plan()
        elif args.action == 'provision':
            require(args.downloads is not None and args.downloads.is_absolute(), 'absolute --downloads required')
            result = provision(args.downloads)
        elif args.action == 'resume-provision':
            result = resume_provision(args.orb_id, args.machine_id, args.reviewed_install_sha256)
        elif args.action == 'preflight':
            result = preflight()
        else:
            require(args.evidence is not None and args.evidence.is_absolute(), 'absolute --evidence required')
            result = (identity if args.action == 'identity' else cleanup)(args.evidence)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result.get('result') == 'BLOCKED' else 0
    except (Blocked, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'result': 'BLOCKED', 'message': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
