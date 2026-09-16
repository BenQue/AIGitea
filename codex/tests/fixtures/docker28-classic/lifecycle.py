"""Issue #296 synthetic Registry/offline public lifecycle orchestrator.

Imported only by the new task driver. All mutation targets are exact resources
inside the two freshly owned VMs; failure retains evidence for explicit cleanup.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

REMOTE = '/opt/aisoft-296/fixture'
PROJECT = 'aisoft-296-fixture'
DATABASE = 'aisoft-296-postgres'
DB_NETWORK = 'aisoft-296-database'
DB_VOLUME = 'aisoft-296-pgdata'
SERVICES = ('web', 'migrate')


def canonical_hash(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()).hexdigest()


def release_ids(source_sha):
    return {name: hashlib.sha1((source_sha + ':issue296:' + name).encode()).hexdigest() for name in ('a', 'b', 'fail')}


def candidate_matrix(source, source_sha):
    value = copy.deepcopy(source)
    if any(row['engine'] == {'minimum': '28.1.1', 'maximum_exclusive': '28.1.2'} and
           row['compose'] == {'minimum': '2.35.1', 'maximum_exclusive': '2.35.2'} and
           row['image_store'] == 'classic' and row['status'] == 'supported' for row in value['rows']):
        return value
    value['rows'].append({
        'row_id': 'issue-296-candidate-engine-28.1.1-compose-2.35.1-classic',
        'engine': {'minimum': '28.1.1', 'maximum_exclusive': '28.1.2'},
        'compose': {'minimum': '2.35.1', 'maximum_exclusive': '2.35.2'},
        'os': 'linux', 'architecture': 'amd64', 'image_store': 'classic', 'status': 'supported',
        'evidence': {'kind': 'real-e2e', 'evidence_id': 'issue-296-disposable-candidate-' + source_sha[:12],
                     'date': '2026-09-16', 'source': 'docs/changes/296-docker28-classic/verification-docker28-classic-260916.md'},
        'remediation': 'Disposable experiment only; not formal compatibility or company deployment approval.'})
    return value


def architecture(pins):
    # This is a synthetic fixture declaration, independent of business architecture.
    components = [
        {'component_id': 'oci.postgres.16-alpine', 'version': '16-alpine', 'state': 'preferred',
         'source_url': pins['fixture_sources']['postgres'], 'digest': pins['fixture_images']['postgres'].split('@')[1]},
        {'component_id': 'oci.python.3-13-alpine', 'version': '3.13-alpine', 'state': 'preferred',
         'source_url': pins['fixture_sources']['python'], 'digest': pins['fixture_images']['python'].split('@')[1]}]
    declaration = {'project_id': 'aisoft-296-fixture', 'components': components, 'purpose': 'synthetic disposable acceptance'}
    value = {'$schema': './architecture/schemas/architecture-lock-v1.schema.json', 'schema_version': '1.0',
             'project_id': 'aisoft-296-fixture', 'profile_id': 'linux-python-postgres-fixture-v1',
             'profile_version': '1.0.0', 'catalog_revision': '2026.09.296', 'delivery_contract': 'docker-release/v1',
             'resolved_components': components, 'exception_ids': [],
             'source_checksums': {'catalog_sha256': canonical_hash(components),
                                  'profile_sha256': canonical_hash({'profile_id': 'linux-python-postgres-fixture-v1'}),
                                  'declaration_sha256': canonical_hash(declaration)}}
    value['lock_sha256'] = canonical_hash(value)
    return value


def compose_source(release_id, images):
    services = {}
    for service in SERVICES:
        services[service] = {
            'image': images[service]['runtime_reference'], 'user': '65532:65532', 'read_only': True,
            'cap_drop': ['ALL'], 'security_opt': ['no-new-privileges:true'], 'tmpfs': ['/tmp:size=16m,mode=1777'],
            'deploy': {'resources': {'limits': {'cpus': '0.5', 'memory': '256M'}}},
            'logging': {'driver': 'json-file', 'options': {'max-size': '1m', 'max-file': '2'}},
            'networks': {'backend': None},
            'labels': {'com.aisoft.release.id': release_id, 'com.aisoft.release.service': service}}
    services['web']['healthcheck'] = {'test': ['CMD', 'python3', '-B', '/web.py', 'healthcheck'],
                                      'interval': '2s', 'timeout': '2s', 'retries': 5}
    services['migrate'].update(profiles=['migration'], networks={'backend': None, 'database': None},
                               environment={k: '${' + k + ':?required}' for k in ('PGHOST', 'PGPORT', 'PGUSER', 'PGDATABASE')})
    return {'services': services,
            'networks': {'backend': {'internal': True, 'name': PROJECT + '-backend'},
                         'database': {'external': True, 'name': DB_NETWORK}}}


def mutation_count(calls):
    return sum(1 for args in calls if
               (args[:1] == ['image'] and len(args) > 1 and args[1] in ('pull', 'load', 'tag', 'rm', 'import', 'push')) or
               (args[:1] == ['compose'] and any(v in args for v in ('run', 'up', 'down'))) )


def execute(ctx, evidence):
    ctx.require_approval()
    ctx.require(not evidence.exists() and evidence.parent.is_dir(), 'immutable lifecycle evidence path unavailable')
    preflight = ctx.preflight()
    ownership = ctx.state()
    ctx.require(not ownership.get('deleted'), 'cannot execute against cleaned VMs')
    pins = ctx.software()
    for image in ('python', 'postgres'):
        ctx.require(pins.get('fixture_images', {}).get(image, '').startswith('docker.io/library/' + image + '@sha256:'), 'fixture image pin missing')
    for side in ctx.SIDES:
        ctx.require(ctx.docker(side, 'ps', '-aq') == '' and ctx.docker(side, 'image', 'ls', '-aq') == '' and
                    ctx.docker(side, 'volume', 'ls', '-q') == '', 'fresh empty task daemons required')
    address = ctx.producer_address()
    ctx.require(address + ':5296' == ownership['registry_address'], 'Registry address changed')
    source = preflight['source']
    ids = release_ids(source['source_sha'])
    work = ctx.LAB / 'lifecycle'
    work.mkdir(mode=0o700)
    stage = work / 'snapshot'
    stage.mkdir(mode=0o700)
    (stage / 'runtime/aisoft_release').mkdir(parents=True)
    for path in (ctx.ROOT / 'codex/runtime/aisoft_release').glob('*.py'):
        shutil.copyfile(path, stage / 'runtime/aisoft_release' / path.name)
    for name in ('docker-wrapper.py', 'lifecycle-operation.py'):
        shutil.copyfile(ctx.FIXTURES / name, stage / name)
    for path in (ctx.FIXTURES / 'web.py', ctx.FIXTURES / 'migrate.sh'):
        shutil.copyfile(path, work / path.name)
    (stage / 'docker-mode').write_text('normal\n')
    (stage / 'docker-calls.jsonl').touch()
    (stage / 'releases').mkdir()
    matrix = candidate_matrix(json.loads((ctx.ROOT / 'docker-release/compatibility/image-stores-v1.json').read_text()), source['source_sha'])
    ctx.write_json(stage / 'candidate-matrix.json', matrix)
    resources = {'vms': ctx.NAMES, 'producer_containers': [ctx.REGISTRY_NAME, 'aisoft-296-seed-web', 'aisoft-296-seed-migrate'],
                 'consumer_containers': [DATABASE, PROJECT + '-web-1', PROJECT + '-migrate-run-*'],
                 'networks': [DB_NETWORK, PROJECT + '-backend'], 'volumes': [DB_VOLUME],
                 'compose_project': PROJECT, 'consumer_root': REMOTE, 'images': pins['fixture_images'],
                 'registry_image': pins['registry_image'], 'registry_address': address + ':5296',
                 'release_identity_kind': 'synthetic-sha-shaped-fixture', 'release_ids': ids, 'runtime_tags': [f'aisoft.local/admin/aisoft-platform/{service}:{release}' for release in ids.values() for service in SERVICES]}
    ctx.write_json(work / 'producer-approval-plan.json', {'source': source, 'capabilities': preflight['capabilities'],
                                                       'resources': resources, 'candidate_matrix_sha256': ctx.digest(stage / 'candidate-matrix.json')})
    result = {'issue': 296, 'kind': 'real-public-lifecycle', 'source': source,
              'capabilities': preflight['capabilities'], 'resources': resources,
              'phases': [], 'transports': {}, 'cleanup': 'NOT RUN', 'result': 'BLOCKED'}

    def safe_write(path, value):
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

    def calls():
        raw = ctx.vm('consumer', 'cat', REMOTE + '/docker-calls.jsonl')
        return [json.loads(line) for line in raw.splitlines() if line]

    def phase(action, release, transport, *, expect=True, root=None, suffix=''):
        before = calls()
        argv = ['python3', '-I', '-S', '-B', REMOTE + '/lifecycle-operation.py', action, '--release-id', release]
        if action == 'verify-artifact':
            argv += ['--release-root', root or REMOTE + '/releases']
        else:
            argv += ['--profile', REMOTE + '/profile-' + transport + '.json']
        output = json.loads(ctx.vm('consumer', *argv, timeout=180))
        new_calls = calls()[len(before):]
        record = {'action': action, 'release_id': release, 'transport': transport, 'case': suffix,
                  'receipt': output, 'docker_calls': new_calls, 'mutations': mutation_count(new_calls)}
        result['phases'].append(record)
        # Per-phase immutable host receipt survives a later subprocess timeout.
        ctx.write_json(work / ('phase-%03d.json' % len(result['phases'])), record)
        ctx.require((output.get('ok') is True) == expect, 'unexpected public phase result: ' + json.dumps(record))
        return record

    def database_receipts():
        text = ctx.docker('consumer', 'exec', DATABASE, 'psql', '-U', 'issue296', '-d', 'issue296', '-At',
                          '-c', 'SELECT marker,attempts FROM issue296_fixture.migration_receipt ORDER BY marker;')
        return dict(line.split('|') for line in text.splitlines())

    def start_database():
        ctx.docker('consumer', 'pull', pins['fixture_images']['postgres'], timeout=300)
        ctx.docker('consumer', 'network', 'create', '--internal', '--label', 'com.aisoft.issue=296', DB_NETWORK)
        ctx.docker('consumer', 'volume', 'create', '--label', 'com.aisoft.issue=296', DB_VOLUME)
        ctx.docker('consumer', 'run', '-d', '--name', DATABASE, '--label', 'com.aisoft.issue=296', '--network', DB_NETWORK,
                   '--mount', 'type=volume,src=' + DB_VOLUME + ',dst=/var/lib/postgresql/data',
                   '-e', 'POSTGRES_HOST_AUTH_METHOD=trust', '-e', 'POSTGRES_USER=issue296', '-e', 'POSTGRES_DB=issue296',
                   pins['fixture_images']['postgres'])
        for _ in range(60):
            try:
                ctx.docker('consumer', 'exec', DATABASE, 'pg_isready', '-U', 'issue296', '-d', 'issue296')
                return
            except ctx.Blocked:
                time.sleep(1)
        raise ctx.Blocked('synthetic PostgreSQL readiness timed out')

    def reset_transport():
        ctx.docker('consumer', 'compose', '--project-name', PROJECT, '--file', REMOTE + '/releases/' + ids['a'] + '/compose.json',
                   '--env-file', REMOTE + '/fixture.env', '--profile', 'migration', 'down', '--volumes', '--remove-orphans')
        ctx.docker('consumer', 'container', 'rm', '--force', '--volumes', DATABASE)
        ctx.docker('consumer', 'network', 'rm', DB_NETWORK)
        ctx.docker('consumer', 'volume', 'rm', DB_VOLUME)
        fixture_ids = set()
        for release in manifests.values():
            for image in release['images']:
                fixture_ids.add(ctx.inspect('consumer', image['runtime_reference'])['Id'])
        ctx.docker('consumer', 'image', 'rm', '--force', *sorted(fixture_ids))
        refs = ctx.docker('consumer', 'image', 'ls', '--format', '{{.Repository}}:{{.Tag}}')
        ctx.require(not any(tag in refs for tag in resources['runtime_tags']), 'fixture image tags remain before offline transport')
        ctx.require(ctx.docker('consumer', 'ps', '-aq') == '' and ctx.docker('consumer', 'volume', 'ls', '-q') == '',
                    'transport reset left unexpected containers or volumes')

    manifests = {}
    try:
        ctx.docker('producer', 'pull', pins['registry_image'], timeout=300)
        ctx.docker('producer', 'run', '-d', '--name', ctx.REGISTRY_NAME, '--label', 'com.aisoft.issue=296',
                   '--tmpfs', '/var/lib/registry:rw,size=1073741824', '-p', address + ':5296:5000', pins['registry_image'])
        for image in pins['fixture_images'].values():
            ctx.docker('producer', 'pull', '--platform', 'linux/amd64', image, timeout=300)
        result['base_image_inspects'] = {k: ctx.inspect('producer', v) for k, v in pins['fixture_images'].items()}
        for name, release_id in ids.items():
            release_dir = stage / 'releases' / release_id
            release_dir.mkdir()
            image_specs = {}
            release_marker = work / 'fixture-release'
            release_marker.write_text(release_id + '\n')
            for service in SERVICES:
                seed = 'aisoft-296-seed-' + service
                base = pins['fixture_images']['python' if service == 'web' else 'postgres']
                tag = address + ':5296/admin/aisoft-platform/' + service + ':' + release_id
                ctx.docker('producer', 'create', '--name', seed, base)
                file = 'web.py' if service == 'web' else 'migrate.sh'
                ctx.docker('producer', 'cp', ctx.MOUNT + '/lifecycle/' + file, seed + ':/' + file)
                ctx.docker('producer', 'cp', ctx.MOUNT + '/lifecycle/fixture-release', seed + ':/fixture-release')
                if name == 'fail' and service == 'web':
                    ctx.docker('producer', 'cp', ctx.MOUNT + '/lifecycle/fixture-release', seed + ':/fixture-fail')
                entrypoint = '["python3","-B","/web.py"]' if service == 'web' else '["/bin/sh","/migrate.sh"]'
                ctx.docker('producer', 'commit', '--change', 'USER 65532:65532', '--change', 'ENTRYPOINT ' + entrypoint,
                           '--change', 'CMD []', '--change', 'LABEL com.aisoft.issue=296', seed, tag)
                ctx.docker('producer', 'rm', '--volumes', seed)
                ctx.docker('producer', 'push', tag, timeout=300)
                metadata = ctx.inspect('producer', tag)
                references = [ref for ref in metadata['RepoDigests'] if ref.startswith(tag.rsplit(':', 1)[0] + '@sha256:')]
                ctx.require(len(references) == 1, 'fixture Registry digest is not unique')
                reference = references[0]
                ctx.docker('producer', 'pull', reference)
                image_id = ctx.inspect('producer', reference)['Id']
                runtime = f'aisoft.local/admin/aisoft-platform/{service}:{release_id}'
                ctx.docker('producer', 'tag', reference, runtime)
                image_specs[service] = {'service': service, 'reference': reference, 'digest': reference.split('@')[1],
                                       'image_id': image_id, 'transport_reference': runtime, 'runtime_reference': runtime}
            save_path = ctx.MOUNT + '/lifecycle/snapshot/releases/' + release_id + '/images.tar'
            ctx.docker('producer', 'save', '-o', save_path, *(image_specs[s]['runtime_reference'] for s in SERVICES), timeout=300)
            archive_sha = ctx.digest(release_dir / 'images.tar')
            inventory = {'contract_version': 'docker-release-offline-inventory/v2', 'archive_sha256': archive_sha,
                         'images': [{**image_specs[s], 'platform': 'linux/amd64'} for s in SERVICES]}
            ctx.write_json(release_dir / 'images.inventory.json', inventory)
            compose = compose_source(release_id, image_specs)
            ctx.write_json(release_dir / 'compose.json', compose)
            source_path = ctx.MOUNT + '/lifecycle/snapshot/releases/' + release_id + '/compose.json'
            model = json.loads(ctx.docker('producer', 'compose', '--project-name', PROJECT, '--file', source_path,
                                          'config', '--format', 'json', '--no-interpolate', '--no-env-resolution'))
            ctx.write_json(release_dir / 'compose.model.json', model)
            arch = architecture(pins)
            ctx.write_json(release_dir / 'architecture.lock.json', arch)
            manifest = {'contract_version': 'docker-release/v2', 'release_id': release_id, 'merge_sha': release_id,
                        'source_repository': 'admin/aisoft-platform', 'platform': 'linux/amd64',
                        'compose': {'path': 'compose.json', 'sha256': ctx.digest(release_dir / 'compose.json'),
                                    'model_path': 'compose.model.json', 'model_sha256': ctx.digest(release_dir / 'compose.model.json')},
                        'architecture': {'path': 'architecture.lock.json', 'profile_id': arch['profile_id'], 'project_id': arch['project_id'],
                                         'catalog_revision': arch['catalog_revision'], 'sha256': ctx.digest(release_dir / 'architecture.lock.json')},
                        'images': list(image_specs.values()), 'runtime_services': ['web'],
                        'migration': {'service': 'migrate', 'identity': 'sha256:' + hashlib.sha256((release_id + ctx.digest(ctx.FIXTURES / 'migrate.sh')).encode()).hexdigest(),
                                      'destructive': False, 'database_restore': 'manual-only'},
                        'offline_bundle': {'contract_version': 'docker-release-offline-bundle/v2', 'archive_path': 'images.tar', 'archive_sha256': archive_sha,
                                           'inventory_path': 'images.inventory.json', 'inventory_sha256': ctx.digest(release_dir / 'images.inventory.json')}}
            ctx.write_json(release_dir / 'release.json', manifest)
            manifests[name] = manifest
            sys.path.insert(0, str(ctx.ROOT / 'codex/runtime'))
            from aisoft_release.runner import ReleaseRuntime
            result.setdefault('producer_artifact_verification', {})[name] = ReleaseRuntime().verify_artifact(stage / 'releases', release_id)
        result['releases'] = manifests
        hostname = ctx.vm('consumer', 'hostname')
        for transport in ('registry', 'offline-bundle'):
            (stage / ('state-' + transport)).mkdir(mode=0o700)
            profile = {'contract_version': 'docker-release-target/v1', 'profile_id': 'issue296-' + transport,
                       'environment': 'test', 'host_role': 'scm-ci', 'expected_hostname': hostname, 'transport': transport,
                       'release_root': REMOTE + '/releases', 'state_root': REMOTE + '/state-' + transport,
                       'compose_project': PROJECT, 'env_file': REMOTE + '/fixture.env', 'source_repository': 'admin/aisoft-platform',
                       'architecture_profile_id': arch['profile_id'], 'architecture_project_id': arch['project_id'],
                       'catalog_revision': arch['catalog_revision'], 'wait_timeout_seconds': 45}
            safe_write(stage / ('profile-' + transport + '.json'), profile)
            result.setdefault('profiles', {})[transport] = profile
        (stage / 'fixture.env').write_text('PGHOST=' + DATABASE + '\nPGPORT=5432\nPGUSER=issue296\nPGDATABASE=issue296\n')
        snapshot_hashes = {str(p.relative_to(stage)): ctx.digest(p) for p in sorted(stage.rglob('*')) if p.is_file()}
        ctx.write_json(work / 'consumer-approval-plan.json', {'source': source, 'capabilities': preflight['capabilities'], 'resources': resources,
                                                           'releases': manifests, 'snapshot_sha256': snapshot_hashes})
        ctx.vm('consumer', 'test', '!', '-e', REMOTE)
        ctx.vm('consumer', 'mkdir', '-p', '-m', '0700', REMOTE)
        ctx.vm('consumer', 'cp', '-R', ctx.MOUNT + '/lifecycle/snapshot/.', REMOTE, timeout=120)
        ctx.vm('consumer', 'chown', '-R', 'root:root', REMOTE)
        ctx.vm('consumer', 'chmod', '0700', REMOTE + '/docker-wrapper.py')
        ctx.vm('consumer', 'chmod', '0600', REMOTE + '/fixture.env', REMOTE + '/profile-registry.json', REMOTE + '/profile-offline-bundle.json')
        # Compare every copied immutable input before the first lifecycle operation.
        for path, expected in snapshot_hashes.items():
            actual = ctx.vm('consumer', 'sha256sum', REMOTE + '/' + path).split()[0]
            ctx.require(actual == expected, 'consumer snapshot byte mismatch: ' + path)
        for transport in ('registry', 'offline-bundle'):
            start_database()
            record = phase('verify-artifact', ids['a'], transport)
            ctx.require(record['docker_calls'] == [], 'verify-artifact called Docker')
            record = phase('verify-target', ids['a'], transport)
            ctx.require(record['mutations'] == 0, 'verify-target mutated Docker')
            for mode in ('wrong-engine', 'wrong-compose', 'wrong-store'):
                ctx.vm('consumer', 'sh', '-c', 'cat > ' + REMOTE + '/docker-mode', stdin=mode + '\n')
                record = phase('verify-target', ids['a'], transport, expect=False, suffix=mode)
                ctx.require(record['mutations'] == 0, 'capability negative mutated Docker')
            ctx.vm('consumer', 'sh', '-c', 'cat > ' + REMOTE + '/docker-mode', stdin='normal\n')
            for name in ('a', 'b'):
                for action in ('verify-artifact', 'verify-target', 'stage', 'migrate', 'activate', 'status'):
                    completed = phase(action, ids[name], transport)
                    if action == 'stage':
                        mutations = [args for args in completed['docker_calls'] if args[:2] in (['image', 'pull'], ['image', 'load'])]
                        expected_action = 'pull' if transport == 'registry' else 'load'
                        ctx.require(len(mutations) == (2 if transport == 'registry' else 1) and
                                    all(args[1] == expected_action for args in mutations), 'transport did not use the required real pull/load path')
                for action, expected in (('stage', 'staged-noop'), ('migrate', 'migration-noop'), ('activate', 'healthy-noop')):
                    record = phase(action, ids[name], transport, suffix='same-sha-repeat')
                    ctx.require(record['receipt']['action'] == expected and record['mutations'] == 0, 'same-SHA phase is not idempotent')
            phase('rollback', ids['a'], transport, suffix='A-B-A')
            phase('status', ids['a'], transport, suffix='after-rollback')
            for action in ('verify-artifact', 'verify-target', 'stage', 'migrate'):
                phase(action, ids['fail'], transport)
            record = phase('activate', ids['fail'], transport, expect=False, suffix='deliberate-unhealthy')
            ctx.require('previous container release was preserved or restored' in record['receipt'].get('message', ''), 'failure did not report automatic restoration')
            phase('status', ids['a'], transport, suffix='after-failed-activation')
            rows = database_receipts()
            ctx.require(rows == {release: '1' for release in ids.values()}, 'migration repeated or receipt missing')
            state_bytes = json.loads(ctx.vm('consumer', 'cat', REMOTE + '/state-' + transport + '/state.json'))
            ctx.require(state_bytes['current_release'] == ids['a'], 'state did not preserve restored release A')
            result['transports'][transport] = {'result': 'PASS', 'migration_receipts': rows, 'state': state_bytes,
                'local_images': {name: [ctx.inspect('consumer', image['runtime_reference']) for image in manifest['images']] for name, manifest in manifests.items()}}
            if transport == 'registry':
                reset_transport()
        # Public artifact negatives after success, using isolated copies, zero Docker calls.
        for negative in ('artifact-tamper', 'identity-tamper'):
            target = REMOTE + '/' + negative
            ctx.vm('consumer', 'mkdir', target)
            ctx.vm('consumer', 'cp', '-R', REMOTE + '/releases/' + ids['a'], target, timeout=120)
            if negative == 'artifact-tamper':
                ctx.vm('consumer', 'sh', '-c', 'printf "\\n" >> ' + target + '/' + ids['a'] + '/compose.model.json')
            else:
                payload = copy.deepcopy(manifests['a'])
                payload['images'][0]['image_id'] = 'sha256:' + '0' * 64
                ctx.vm('consumer', 'sh', '-c', 'cat > ' + target + '/' + ids['a'] + '/release.json', stdin=json.dumps(payload))
            record = phase('verify-artifact', ids['a'], 'offline-bundle', expect=False, root=target, suffix=negative)
            ctx.require(record['docker_calls'] == [], 'artifact negative made Docker calls')
        ctx.require(source['files_sha256'] == ctx.source_evidence()['files_sha256'], 'source bytes drifted during lifecycle')
        result['result'] = 'PASS'
    except Exception as exc:
        result['error'] = str(exc)
    finally:
        ctx.write_json(evidence, result)
    return result
