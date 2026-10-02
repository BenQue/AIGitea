#!/usr/bin/env python3
"""Actual helper process canaries; full DB fixture is restricted to a disposable container."""
import argparse
import json
import os
from pathlib import Path
import pwd
import sqlite3
import subprocess
import sys


def run_suite(binary, *, isolated=False, fixture=None):
    if not __debug__:
        raise SystemExit('TEST_OPTIMIZATION_UNSUPPORTED')
    if sys.platform != 'linux':
        raise SystemExit('LINUX_TEST_HOST_REQUIRED')
    canary = 'c316'*10  # Synthetic 40-hex PAT; upstream rejects other lengths before DB lookup.
    try:
        service = pwd.getpwnam('git')
    except KeyError:
        service = None
    if service is not None and service.pw_uid == os.geteuid():
        raise SystemExit('TEST_CALLER_MUST_NOT_BE_LIVE_SERVICE_USER')

    def invoke(request, code=None, result=None, *, service_user=False, args=()):
        options = dict(user=service.pw_uid, group=service.pw_gid, extra_groups=[]) if service_user else {}
        value = subprocess.run([str(binary), *args], input=json.dumps(request).encode(),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
                               env={'PATH':'/usr/bin:/bin', 'LANG':'C'}, **options)
        assert canary.encode() not in value.stdout + value.stderr, 'process Secret leak'
        assert value.stderr == b'', 'unexpected helper stderr'
        receipt = json.loads(value.stdout)
        if code:
            assert value.returncode == 2 and receipt == {'result':'BLOCKED', 'code':code}, receipt
        else:
            assert value.returncode == 0 and receipt['result'] == result, receipt
        return receipt

    version = subprocess.run([str(binary), '--version'], capture_output=True, timeout=10)
    assert version.returncode == 0 and not version.stderr
    assert json.loads(version.stdout) == {'helper_version':'1', 'gitea_model_version':'1.26.4', 'toolchain':'go1.26.3'}
    request = {'action':'inspect', 'project_id':'newemaint', 'token_kind':'routine-merge-agent', 'token':canary}
    invoke(request, 'SERVICE_IDENTITY_REQUIRED')
    invoke(request, 'REQUEST_INVALID', args=('--unsupported',))
    if not isolated:
        print('PASS: actual Linux helper version/entrypoint Secret canary; DB fixture NOT RUN')
        return

    if os.geteuid() != 0 or not Path('/.dockerenv').is_file():
        raise SystemExit('DISPOSABLE_ROOT_CONTAINER_REQUIRED')
    # Never overwrite an existing fixture, install, config or canonical manifest.
    fixed = [Path('/usr/local/share/aisoft'), Path('/etc/gitea'), Path('/fixtures'), Path('/usr/local/bin/gitea')]
    if any(p.exists() for p in fixed) or service is not None:
        raise SystemExit('EMPTY_DISPOSABLE_CONTAINER_REQUIRED')
    subprocess.run(['useradd', '--system', '--no-create-home', 'git'], check=True, capture_output=True)
    service = pwd.getpwnam('git')
    root = Path('/fixtures')
    root.mkdir(mode=0o700)
    os.chown(root, service.pw_uid, service.pw_gid)
    install = Path('/usr/local/share/aisoft')
    install.mkdir(parents=True, mode=0o755)
    repository = Path(__file__).resolve().parents[3]
    for name in ('host-access-broker.json', 'gitea-governance.json'):
        destination = install/name
        destination.write_bytes((repository/'codex/config'/name).read_bytes())
        destination.chmod(0o644)
    Path('/etc/gitea').mkdir(mode=0o755)
    config = Path('/etc/gitea/app.ini')
    database = root/'synthetic.db'
    config.write_text('[database]\nDB_TYPE = sqlite3\nPATH = /fixtures/synthetic.db\nLOG_SQL = false\n')
    config.chmod(0o644)
    gitea = Path('/usr/local/bin/gitea')
    gitea.write_text('#!/bin/sh\n[ "$1" = --version ] || exit 2\nprintf "%s\\n" "Gitea version 1.26.4 built with go1.26.3 : test-fixture"\n')
    gitea.chmod(0o755)  # Version metadata stub, never a real Gitea server/CLI.
    if fixture is None:
        raise SystemExit('UPSTREAM_MODEL_FIXTURE_REQUIRED')
    database.write_bytes(fixture.read_bytes())  # Schema/hashes come from actual fixed Go models.
    database.chmod(0o600)
    os.chown(database, service.pw_uid, service.pw_gid)
    def ids():
        with sqlite3.connect(database) as db:
            return [row[0] for row in db.execute('SELECT id FROM access_token ORDER BY id')]
    inspected = invoke(request, result='verified', service_user=True)
    assert (inspected['token_id'], inspected['user_id'], inspected['scopes']) == (1,11,['write:repository'])
    assert ids() == [1,2,3]
    revoke = dict(request, action='revoke', expected_token_id=1, expected_user_id=11, expected_token_name='issue-208-routine-merge-agent')
    invoke(dict(revoke, expected_user_id=12), 'TOKEN_BINDING_MISMATCH', service_user=True)
    assert ids() == [1,2,3]
    with sqlite3.connect(database) as db:
        db.execute("CREATE TRIGGER prevent_revoke BEFORE DELETE ON access_token BEGIN SELECT RAISE(ABORT, '"+canary+"'); END")
    invoke(revoke, 'REVOKE_FAILED', service_user=True)
    assert ids() == [1,2,3]
    with sqlite3.connect(database) as db:
        db.execute('DROP TRIGGER prevent_revoke')
    invoke(revoke, result='revoked', service_user=True)
    assert ids() == [2,3]
    invoke(request, 'TOKEN_UNKNOWN', service_user=True)
    config.write_text('[database]\nDB_TYPE = sqlite3\nPATH = /fixtures/'+canary+'\n')
    invoke(request, 'DB_PATH_UNSAFE', service_user=True)
    print('PASS: actual Linux helper isolated model inspect/exact revoke/driver-error canary/other-token preservation; live NOT RUN')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--isolated-container', action='store_true')
    parser.add_argument('--fixture', type=Path)
    arguments = parser.parse_args()
    run_suite(arguments.binary.resolve(strict=True), isolated=arguments.isolated_container,
              fixture=arguments.fixture.resolve(strict=True) if arguments.fixture else None)
