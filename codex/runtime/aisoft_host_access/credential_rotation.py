"""Operator-only PAT transaction; public receipts never contain Secret data."""
from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import os
import pwd
import re
import stat
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from .broker import BrokerError
from .contract import AccessContract, ROTATION_POLICY

SHA = re.compile(r'^[0-9a-f]{40}$')
TOKEN = re.compile(r'^[A-Za-z0-9._-]{1,128}$')
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
CAPABILITY = re.compile(r'^[0-9a-f]{64}$')


def blocked(code):
    # Never format upstream errors, PATs, helper JSON or caller values.
    raise BrokerError(code, 'credential rotation refused; protected transaction retained')


def strict_json(raw, limit=16384):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                blocked('ROTATION_SCHEMA_INVALID')
            result[key] = value
        return result
    try:
        if len(raw) > limit:
            blocked('ROTATION_SCHEMA_INVALID')
        value = json.loads(raw, object_pairs_hook=pairs,
                           parse_constant=lambda _: blocked('ROTATION_SCHEMA_INVALID'))
        if not isinstance(value, dict):
            blocked('ROTATION_SCHEMA_INVALID')
        return value
    except (ValueError, TypeError, UnicodeError):
        blocked('ROTATION_SCHEMA_INVALID')


@dataclass(frozen=True)
class OperatorGrant:
    binding: dict
    capability: str | None = field(default=None, repr=False)
    capability_digest: str | None = field(default=None, repr=False)


def require_private_pipes():
    """Only anonymous OS pipes, including rejection of unlinked named FIFOs."""
    try:
        for stream in (sys.stdin, sys.stdout):
            fd = stream.fileno()
            metadata = os.fstat(fd)
            if not stat.S_ISFIFO(metadata.st_mode):
                blocked('ROTATION_PIPE_REQUIRED')
            if sys.platform == 'linux':
                if os.readlink(f'/proc/self/fd/{fd}') != f'pipe:[{metadata.st_ino}]':
                    blocked('ROTATION_PIPE_REQUIRED')
            elif sys.platform == 'darwin':
                if metadata.st_nlink != 0 or metadata.st_dev != 0:
                    blocked('ROTATION_PIPE_REQUIRED')
            else:
                blocked('ROTATION_PIPE_REQUIRED')
    except (OSError, ValueError, AttributeError):
        blocked('ROTATION_PIPE_REQUIRED')


def verify_operator_capability(value, digest):
    if (not isinstance(value, str) or not CAPABILITY.fullmatch(value)
            or not isinstance(digest, str) or not CAPABILITY.fullmatch(digest)
            or not hmac.compare_digest(hashlib.sha256(value.encode('ascii')).hexdigest(), digest)):
        blocked('ROTATION_OPERATOR_REQUIRED')


@dataclass(frozen=True)
class RotationTarget:
    project_id: str
    token_kind: str
    username: str
    relative_path: str
    scopes: tuple[str, ...]


def rotation_target(contract: AccessContract, project_id, kind):
    project = contract.project(project_id)
    bindings = contract.raw['identity_bindings']
    governance = contract.governance.raw
    if kind in ('manager-audit', 'manager-mutation'):
        binding = bindings[kind.replace('-', '_')]
        username = contract.governance.platform_manager
        relative = binding['relative_path']
        scopes = governance['platform_manager'][kind.split('-')[1] + '_token_scopes']
    elif kind == 'project-agent':
        username = project.project_agent
        relative = bindings['project_agent']['relative_path_template'].format(project_id=project_id)
        scopes = governance['project_agent_policy']['token_scopes']
    elif kind == 'routine-merge-agent' and project.routine_merge_agent:
        username = project.routine_merge_agent
        relative = bindings['routine_merge_agent']['relative_path_template'].format(project_id=project_id)
        scopes = governance['routine_merge_agent_policy']['token_scopes']
    else:
        blocked('ROTATION_TARGET_INVALID')
    return RotationTarget(project_id, kind, username, relative, tuple(sorted(scopes)))


class ProtectedDirectory:
    """Descriptor-relative operations: no symlinks, hardlinks or path traversal."""
    def __init__(self, fd, uid, device):
        self.fd, self.uid, self.device = fd, uid, device

    @classmethod
    def open(cls, path, uid, mode=0o700):
        parsed = PurePosixPath(path)
        if not parsed.is_absolute() or str(parsed) != str(path) or '..' in parsed.parts:
            blocked('ROTATION_PATH_UNSAFE')
        fd = os.open('/', DIRECTORY_FLAGS)
        try:
            for component in parsed.parts[1:]:
                nxt = os.open(component, DIRECTORY_FLAGS, dir_fd=fd)
                os.close(fd)
                fd = nxt
            meta = os.fstat(fd)
            if meta.st_uid != uid or stat.S_IMODE(meta.st_mode) != mode:
                blocked('ROTATION_DIRECTORY_UNSAFE')
            return cls(fd, uid, meta.st_dev)
        except BaseException:
            os.close(fd)
            raise

    def child(self, name, create=False):
        self.name(name)
        if create:
            try:
                os.mkdir(name, 0o700, dir_fd=self.fd)
                os.chown(name, self.uid, -1, dir_fd=self.fd, follow_symlinks=False)
                os.fsync(self.fd)
            except FileExistsError:
                pass
        fd = os.open(name, DIRECTORY_FLAGS, dir_fd=self.fd)
        meta = os.fstat(fd)
        if (meta.st_uid != self.uid or stat.S_IMODE(meta.st_mode) != 0o700
                or meta.st_dev != self.device):
            os.close(fd)
            blocked('ROTATION_DIRECTORY_UNSAFE')
        return ProtectedDirectory(fd, self.uid, self.device)

    @staticmethod
    def name(name):
        if not isinstance(name, str) or '/' in name or name in ('', '.', '..'):
            blocked('ROTATION_PATH_UNSAFE')

    def exists(self, name):
        self.name(name)
        try:
            os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            return True
        except FileNotFoundError:
            return False

    def validate_file(self, fd, modes=(0o400, 0o600)):
        meta = os.fstat(fd)
        if (not stat.S_ISREG(meta.st_mode) or meta.st_uid != self.uid or meta.st_nlink != 1
                or stat.S_IMODE(meta.st_mode) not in modes or meta.st_dev != self.device):
            blocked('ROTATION_FILE_UNSAFE')

    def read(self, name, limit=16384):
        self.name(name)
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        try:
            self.validate_file(fd)
            raw = os.read(fd, limit + 1)
            if len(raw) > limit:
                blocked('ROTATION_FILE_UNSAFE')
            return raw
        finally:
            os.close(fd)

    def token(self, name):
        try:
            value = self.read(name, 256).decode('ascii').strip()
        except UnicodeError:
            blocked('ROTATION_TOKEN_INVALID')
        if not TOKEN.fullmatch(value):
            blocked('ROTATION_TOKEN_INVALID')
        return value

    def write(self, name, raw):
        self.name(name)
        if self.exists(name):
            self.read(name)
        temporary = '.write-' + uuid.uuid4().hex
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=self.fd)
        try:
            os.fchown(fd, self.uid, -1)
            with os.fdopen(fd, 'wb', closefd=False) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(fd)
            os.rename(temporary, name, src_dir_fd=self.fd, dst_dir_fd=self.fd)
            os.fsync(self.fd)
        finally:
            os.close(fd)
            if self.exists(temporary):
                os.unlink(temporary, dir_fd=self.fd)

    def json_write(self, name, value):
        self.write(name, (json.dumps(value, sort_keys=True) + '\n').encode())

    def move(self, name, destination, target):
        self.read(name)
        if destination.exists(target):
            blocked('ROTATION_DESTINATION_EXISTS')
        os.rename(name, target, src_dir_fd=self.fd, dst_dir_fd=destination.fd)
        os.fsync(self.fd)
        os.fsync(destination.fd)

    def remove(self, name):
        if self.exists(name):
            self.read(name)
            os.unlink(name, dir_fd=self.fd)
            os.fsync(self.fd)

    def lock(self):
        name = '.rotation.lock'
        try:
            fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=self.fd)
            os.fchown(fd, self.uid, -1)
        except FileExistsError:
            fd = os.open(name, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        try:
            self.validate_file(fd, (0o600,))
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            os.close(fd)
            blocked('ROTATION_BUSY')
        except BaseException:
            os.close(fd)
            raise

    def close(self):
        os.close(self.fd)


class RotationTransaction:
    """The operator transaction seam; injected backend is for isolated tests only."""
    def __init__(self, root, uid, target, authorization, backend):
        self.root, self.uid, self.target = root, uid, target
        self.valid_until = authorization.get('expires_at')
        self.authorization = {key: value for key, value in authorization.items() if key != 'expires_at'}
        self.backend = backend

    def guard(self):
        if self.valid_until is not None and time.time() >= self.valid_until:
            blocked('ROTATION_GRANT_EXPIRED')

    def markers(self, parent, basename):
        creation = self.authorization['creation_issue']
        prefix = f'issue={creation}\nusername={self.target.username}\n'
        for name, expected in (
            (f'{self.target.username}.account-created-by-issue-{creation}', prefix),
            (f'{self.target.username}.must-change-password-unset-by-issue-{creation}',
             prefix + 'policy=must-change-password-unset\n'),
            (f'{basename}-created-by-issue-{creation}',
             prefix + f'token_kind={self.target.token_kind}\n'),
        ):
            if parent.read(name) != expected.encode():
                blocked('ROTATION_OWNERSHIP_INVALID')

    def metadata(self, token, name=None):
        value = self.backend.inspect(token, name)
        if (set(value) != {'token_id', 'user_id', 'token_name', 'scopes'}
                or type(value['token_id']) is not int or value['token_id'] <= 0
                or type(value['user_id']) is not int or value['user_id'] <= 0
                or not isinstance(value['token_name'], str)
                or not re.fullmatch(r'issue-[1-9][0-9]*-' + re.escape(self.target.token_kind)
                                    + r'(-rotation-[0-9a-f]{12})?', value['token_name'])
                or not isinstance(value['scopes'], list)
                or not all(isinstance(s, str) and re.fullmatch(r'(read|write):[a-z]+', s)
                           for s in value['scopes'])
                or len(value['scopes']) != len(set(value['scopes']))
                or (name is not None and value['token_name'] != name)):
            blocked('ROTATION_MODEL_INVALID')
        return value

    def receipt(self, result):
        return {'status': 'PASS', 'operation': 'gitea.credential.rotate', 'result': result,
                'issue': self.authorization['issue'], 'source_sha': self.authorization['source_sha'],
                'project_id': self.target.project_id, 'token_kind': self.target.token_kind,
                'scopes': list(self.target.scopes), 'old_pat_revoked': True,
                'observed_at': int(time.time())}

    def run(self):
        directories = []
        lock = None
        try:
            self.backend.capabilities()
            self.guard()
            parent = ProtectedDirectory.open(self.root, self.uid)
            directories.append(parent)
            parts = PurePosixPath(self.target.relative_path).parts
            for name in parts[:-1]:
                parent = parent.child(name)
                directories.append(parent)
            basename = parts[-1]
            self.markers(parent, basename)
            # Locks are per credential, including the two manager PAT kinds.
            tx = parent.child('.rotation-' + self.target.token_kind, create=True)
            directories.append(tx)
            lock = tx.lock()
            old_name = f"issue-{self.authorization['creation_issue']}-{self.target.token_kind}"
            previous = None
            if tx.exists('journal.json'):
                journal = strict_json(tx.read('journal.json'))
                self.validate_journal(journal, historical=True)
                if journal['authorization'] != self.authorization:
                    if (journal['phase'] != 'complete'
                            or journal['authorization']['creation_issue'] != self.authorization['creation_issue']):
                        blocked('ROTATION_JOURNAL_INVALID')
                    current = parent.token(basename)
                    previous = self.metadata(current, journal['candidate_name'])
                    if previous != journal['candidate']:
                        blocked('ROTATION_ACTIVE_MISMATCH')
                    # New scope contracts may intentionally differ; exact model ownership
                    # still has to match the completed provenance, never a guessed name.
                    old_name = journal['candidate_name']
                    archive = f"completed-{journal['authorization']['issue']}-{journal['authorization']['source_sha']}.json"
                    tx.json_write(archive, journal)
                    tx.remove('old.token')
                    tx.remove('candidate.token')
                    journal = None
                else:
                    self.validate_journal(journal)
            else:
                journal = None
            if journal is None:
                old = parent.token(basename)
                metadata = self.metadata(old, old_name)
                if previous is not None and metadata != previous:
                    blocked('ROTATION_ACTIVE_MISMATCH')
                journal = {'version': 1, 'authorization': self.authorization,
                           'target': self.target.__dict__, 'phase': 'ready', 'old': metadata,
                           'created_at': int(time.time()), 'updated_at': int(time.time()),
                           'candidate': None, 'candidate_name': f"issue-{self.authorization['issue']}-{self.target.token_kind}-rotation-{uuid.uuid4().hex[:12]}"}
                # Convert tuple to the on-disk JSON shape for equality on retry.
                journal['target'] = dict(journal['target'], scopes=list(self.target.scopes))
                tx.json_write('journal.json', journal)
            return self.advance(parent, basename, tx, journal)
        except BrokerError:
            raise
        except Exception:
            blocked('ROTATION_FAILED')
        finally:
            if lock is not None:
                os.close(lock)
            for directory in reversed(directories):
                directory.close()

    def validate_journal(self, journal, historical=False):
        target = dict(self.target.__dict__, scopes=list(self.target.scopes))
        authorization = journal.get('authorization')
        old_target = journal.get('target')
        if (not isinstance(authorization, dict) or set(authorization) != set(self.authorization)
                or type(authorization.get('issue')) is not int or authorization['issue'] <= 0
                or type(authorization.get('creation_issue')) is not int or authorization['creation_issue'] <= 0
                or not isinstance(authorization.get('source_sha'), str)
                or not SHA.fullmatch(authorization['source_sha'])
                or authorization.get('project_id') != self.target.project_id
                or authorization.get('token_kind') != self.target.token_kind
                or not isinstance(old_target, dict) or set(old_target) != set(target)
                or any(old_target[key] != target[key] for key in target if key != 'scopes')
                or not isinstance(old_target['scopes'], list)):
            blocked('ROTATION_JOURNAL_INVALID')
        if (set(journal) != {'version', 'authorization', 'target', 'phase', 'old',
                             'candidate', 'candidate_name', 'created_at', 'updated_at'}
                or journal['version'] != 1
                or type(journal['created_at']) is not int or type(journal['updated_at']) is not int
                or not 0 < journal['created_at'] <= journal['updated_at']
                or (not historical and (authorization != self.authorization or old_target != target))
                or journal['phase'] not in {'ready', 'isolated', 'issuing', 'candidate',
                                             'revoking', 'revoked', 'published', 'complete', 'aborted'}
                or not re.fullmatch(f"issue-{authorization['issue']}-{re.escape(self.target.token_kind)}-rotation-[0-9a-f]{{12}}",
                                    str(journal['candidate_name']))):
            blocked('ROTATION_JOURNAL_INVALID')

    @staticmethod
    def phase(tx, journal, phase):
        journal['phase'] = phase
        journal['updated_at'] = int(time.time())
        tx.json_write('journal.json', journal)

    def advance(self, parent, basename, tx, journal):
        if journal['phase'] in ('isolated', 'issuing', 'candidate', 'revoking') and parent.exists(basename):
            blocked('ROTATION_ACTIVE_MISMATCH')
        if journal['phase'] == 'aborted':
            blocked('ROTATION_ABORTED')
        if journal['phase'] == 'complete':
            current = parent.token(basename)
            observed = self.metadata(current, journal['candidate_name'])
            if observed != journal['candidate']:
                blocked('ROTATION_ACTIVE_MISMATCH')
            self.backend.verify(current, observed, self.target.scopes)
            tx.remove('old.token')
            tx.remove('candidate.token')
            return self.receipt('no-op')
        if journal['phase'] == 'ready':
            if not tx.exists('old.token'):
                current = parent.token(basename)
                if self.metadata(current) != journal['old']:
                    blocked('ROTATION_ACTIVE_MISMATCH')
                self.guard()
                parent.move(basename, tx, 'old.token')
            elif parent.exists(basename):
                blocked('ROTATION_ACTIVE_MISMATCH')
            elif self.metadata(tx.token('old.token')) != journal['old']:
                blocked('ROTATION_OLD_UNCONFIRMED')
            self.phase(tx, journal, 'isolated')
        if journal['phase'] == 'isolated':
            if self.metadata(tx.token('old.token')) != journal['old']:
                blocked('ROTATION_OLD_UNCONFIRMED')
            self.guard()
            self.phase(tx, journal, 'issuing')
            candidate = self.backend.generate(journal['candidate_name'])
            if not isinstance(candidate, str) or not TOKEN.fullmatch(candidate):
                blocked('ROTATION_CANDIDATE_UNKNOWN')
            try:
                tx.write('candidate.token', (candidate + '\n').encode('ascii'))
            except Exception:
                # Raw value is still in memory: compensate before it could be lost.
                metadata = self.metadata(candidate, journal['candidate_name'])
                if metadata['user_id'] != journal['old']['user_id']:
                    blocked('ROTATION_IDENTITY_MISMATCH')
                self.compensate(parent, basename, tx, journal, candidate, metadata)
                blocked('ROTATION_CANDIDATE_WRITE_FAILED')
        if journal['phase'] == 'issuing':
            if not tx.exists('candidate.token'):
                # CLI may have committed a token whose raw value was lost. No second issue.
                blocked('ROTATION_CANDIDATE_UNKNOWN')
            candidate = tx.token('candidate.token')
            journal['candidate'] = self.metadata(candidate, journal['candidate_name'])
            if journal['candidate']['user_id'] != journal['old']['user_id']:
                blocked('ROTATION_IDENTITY_MISMATCH')
            self.phase(tx, journal, 'candidate')
        if journal['phase'] == 'candidate':
            candidate = tx.token('candidate.token')
            try:
                if self.metadata(candidate, journal['candidate_name']) != journal['candidate']:
                    blocked('ROTATION_ACTIVE_MISMATCH')
                self.backend.verify(candidate, journal['candidate'], self.target.scopes)
            except BrokerError:
                # Compensate only the exact candidate; old legacy scope can be unsafe.
                self.compensate(parent, basename, tx, journal, candidate, journal['candidate'])
                blocked('ROTATION_CANDIDATE_REJECTED')
            self.phase(tx, journal, 'revoking')
        if journal['phase'] == 'revoking':
            candidate = tx.token('candidate.token')
            if self.metadata(candidate, journal['candidate_name']) != journal['candidate']:
                blocked('ROTATION_ACTIVE_MISMATCH')
            self.backend.verify(candidate, journal['candidate'], self.target.scopes)
            old = tx.token('old.token')
            if self.metadata(old) != journal['old']:
                blocked('ROTATION_OLD_UNCONFIRMED')
            self.guard()
            self.backend.revoke(old, journal['old'])
            self.phase(tx, journal, 'revoked')
        if journal['phase'] == 'revoked':
            if not self.backend.rejected(tx.token('old.token')):
                blocked('ROTATION_OLD_UNCONFIRMED')
            # A crash between rename and journal publication is recoverable by exact binding.
            source = tx if tx.exists('candidate.token') else parent
            name = 'candidate.token' if source is tx else basename
            candidate = source.token(name)
            if self.metadata(candidate, journal['candidate_name']) != journal['candidate']:
                blocked('ROTATION_ACTIVE_MISMATCH')
            self.backend.verify(candidate, journal['candidate'], self.target.scopes)
            tx.json_write('provenance.json', self.receipt('rotated'))
            if source is tx:
                self.guard()
                tx.move('candidate.token', parent, basename)
            self.phase(tx, journal, 'published')
        if journal['phase'] == 'published':
            candidate = parent.token(basename)
            try:
                if self.metadata(candidate, journal['candidate_name']) != journal['candidate']:
                    blocked('ROTATION_ACTIVE_MISMATCH')
                self.backend.verify(candidate, journal['candidate'], self.target.scopes)
                if not self.backend.rejected(tx.token('old.token')):
                    blocked('ROTATION_OLD_UNCONFIRMED')
            except BrokerError:
                parent.move(basename, tx, 'candidate.token')
                self.phase(tx, journal, 'revoked')
                raise
            self.phase(tx, journal, 'complete')
            tx.remove('old.token')
            return self.receipt('rotated')
        blocked('ROTATION_JOURNAL_INVALID')

    def compensate(self, parent, basename, tx, journal, candidate, metadata):
        self.guard()
        self.backend.revoke(candidate, metadata)
        if not self.backend.rejected(candidate):
            blocked('ROTATION_COMPENSATION_UNCONFIRMED')
        old = tx.token('old.token')
        if (self.metadata(old) == journal['old']
                and set(journal['old']['scopes']) == set(self.target.scopes)):
            self.backend.verify(old, journal['old'], self.target.scopes)
            self.guard()
            tx.move('old.token', parent, basename)
        self.phase(tx, journal, 'aborted')
        tx.remove('candidate.token')


ACCESS_PATH = '/usr/local/share/aisoft/host-access-broker.json'
GOVERNANCE_PATH = '/usr/local/share/aisoft/gitea-governance.json'


def trusted_read(path, *, group=None):
    """Root-owned install/grant metadata; never follows a writable ancestor."""
    fd = os.open('/', DIRECTORY_FLAGS)
    try:
        parts = PurePosixPath(path).parts[1:]
        for component in parts[:-1]:
            nxt = os.open(component, DIRECTORY_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = nxt
            st = os.fstat(fd)
            if st.st_uid != 0 or stat.S_IMODE(st.st_mode) & 0o022:
                blocked('ROTATION_TRUST_UNSAFE')
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            st = os.fstat(file_fd)
            if (st.st_uid != 0 or not stat.S_ISREG(st.st_mode) or st.st_nlink != 1
                    or stat.S_IMODE(st.st_mode) & 0o022
                    or (group is not None and (stat.S_IMODE(st.st_mode) != 0o640 or st.st_gid != group))):
                blocked('ROTATION_TRUST_UNSAFE')
            raw = os.read(file_fd, 16385)
            if len(raw) > 16384:
                blocked('ROTATION_TRUST_UNSAFE')
            return raw
        finally:
            os.close(file_fd)
    except (OSError, ValueError):
        blocked('ROTATION_TRUST_UNAVAILABLE')
    finally:
        os.close(fd)


def installation_receipt(contract, source_sha, *, vm=False):
    if str(contract.path) != ACCESS_PATH or str(contract.governance.path) != GOVERNANCE_PATH:
        blocked('ROTATION_INSTALL_REQUIRED')
    receipt = strict_json(trusted_read(ROTATION_POLICY['source_receipt']))
    expected = {'version', 'source_sha', 'merged_main', 'files', 'helper'}
    if (set(receipt) != expected or receipt['version'] != 1
            or receipt['source_sha'] != source_sha or receipt['merged_main'] is not True
            or not isinstance(receipt['files'], dict)):
        blocked('ROTATION_SOURCE_MISMATCH')
    # Read back bytes on both hosts rather than trusting a source-SHA string alone.
    required = {ACCESS_PATH, GOVERNANCE_PATH,
                '/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py',
                ROTATION_POLICY['vm_operator']}
    if set(receipt['files']) != required:
        blocked('ROTATION_SOURCE_MISMATCH')
    for path, digest in receipt['files'].items():
        # Modules can exceed grant/JSON limits; hash via validated descriptors below.
        if digest != trusted_digest(path):
            blocked('ROTATION_SOURCE_MISMATCH')
    if vm:
        helper = receipt['helper']
        if (not isinstance(helper, dict) or set(helper) != {'sha256', 'platform', 'model', 'toolchain'}
                or helper['platform'] not in ('linux/amd64', 'linux/arm64')
                or helper['model'] != '1.26.4' or helper['toolchain'] != 'go1.26.3'
                or helper['sha256'] != trusted_digest(ROTATION_POLICY['vm_helper'])):
            blocked('ROTATION_HELPER_UNAVAILABLE')


def trusted_digest(path):
    # Apply the same ancestor and file checks, streaming large binary/module bytes.
    fd = os.open('/', DIRECTORY_FLAGS)
    try:
        for component in PurePosixPath(path).parts[1:-1]:
            nxt = os.open(component, DIRECTORY_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = nxt
            st = os.fstat(fd)
            if st.st_uid != 0 or stat.S_IMODE(st.st_mode) & 0o022:
                blocked('ROTATION_TRUST_UNSAFE')
        binary = os.open(PurePosixPath(path).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            st = os.fstat(binary)
            if (st.st_uid != 0 or st.st_nlink != 1 or not stat.S_ISREG(st.st_mode)
                    or stat.S_IMODE(st.st_mode) & 0o022):
                blocked('ROTATION_TRUST_UNSAFE')
            digest = hashlib.sha256()
            while True:
                raw = os.read(binary, 65536)
                if not raw:
                    return digest.hexdigest()
                digest.update(raw)
        finally:
            os.close(binary)
    except OSError:
        blocked('ROTATION_TRUST_UNAVAILABLE')
    finally:
        os.close(fd)


def authorization(contract, target, issue, source_sha, *, vm=False):
    if type(issue) is not int or issue <= 0 or not isinstance(source_sha, str) or not SHA.fullmatch(source_sha):
        blocked('ROTATION_ARGUMENT_INVALID')
    installation_receipt(contract, source_sha, vm=vm)
    grant_path = f"{ROTATION_POLICY['grant_root']}/{target.project_id}-{target.token_kind}.json"
    group = pwd.getpwnam('git').pw_gid if vm else None
    grant = strict_json(trusted_read(grant_path, group=group))
    validate_grant(contract, target, issue, source_sha, grant, vm=vm)
    if not vm:
        # Mac grants are readable only by the separately elevated operator.
        directory = ProtectedDirectory.open(ROTATION_POLICY['grant_root'], 0)
        try:
            fd = os.open(PurePosixPath(grant_path).name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory.fd)
            try:
                directory.validate_file(fd, (0o600,))
            finally:
                os.close(fd)
        finally:
            directory.close()
    else:
        directory = ProtectedDirectory.open(ROTATION_POLICY['grant_root'], 0, mode=0o750)
        try:
            if os.fstat(directory.fd).st_gid != group:
                blocked('ROTATION_GRANT_INVALID')
        finally:
            directory.close()
    binding = {key: grant[key] for key in ('issue', 'source_sha', 'project_id', 'token_kind', 'creation_issue', 'expires_at')}
    return OperatorGrant(binding, capability=None if vm else grant['operator_capability'],
                         capability_digest=grant['operator_capability_sha256'] if vm else None)


def validate_grant(contract, target, issue, source_sha, grant, *, vm=False):
    """Exact grant schema, bound custody/target and current authorization window."""
    expected = {'version', 'operator_uid', 'issue', 'source_sha', 'project_id', 'token_kind',
                'credential_root', 'helper_path', 'not_before', 'expires_at', 'creation_issue'}
    proof_field = 'operator_capability_sha256' if vm else 'operator_capability'
    expected.add(proof_field)
    if (set(grant) != expected or type(grant['version']) is not int or grant['version'] != 1
            or type(grant['operator_uid']) is not int
            or grant['operator_uid'] != 0 or grant['issue'] != issue
            or grant['source_sha'] != source_sha or grant['project_id'] != target.project_id
            or grant['token_kind'] != target.token_kind
            or grant['credential_root'] != contract.raw['mac_host']['credential_root']
            or grant['helper_path'] != ROTATION_POLICY['vm_helper']
            or type(grant['creation_issue']) is not int or grant['creation_issue'] <= 0
            or type(grant['not_before']) is not int or type(grant['expires_at']) is not int
            or not grant['not_before'] <= time.time() < grant['expires_at']
            or not isinstance(grant[proof_field], str) or not CAPABILITY.fullmatch(grant[proof_field])):
        blocked('ROTATION_GRANT_INVALID')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class SystemBackend:
    """Secret stdin/stdout are private pipes, distinct from typed public receipts."""
    def __init__(self, contract, target, issue, source_sha, operator_capability):
        self.contract, self.target, self.issue, self.source_sha = contract, target, issue, source_sha
        self.operator_capability = operator_capability

    def vm(self, action, **values):
        mac = self.contract.raw['mac_host']
        argv = ['/usr/bin/sudo', '-n', '-H', '-u', mac['orbstack_user'], mac['orbstack_binary'],
                '-m', mac['orbstack_machine'], '-u', ROTATION_POLICY['vm_service_user'],
                ROTATION_POLICY['vm_operator'], '--vm-operation']
        request = dict(action=action, project_id=self.target.project_id,
                       token_kind=self.target.token_kind, issue=self.issue,
                       source_sha=self.source_sha, operator_capability=self.operator_capability, **values)
        try:
            result = subprocess.run(argv, input=json.dumps(request).encode(), stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, timeout=45, check=False,
                                    env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
            if result.returncode != 0 or len(result.stdout) > 16384:
                blocked('ROTATION_VM_FAILED')
            return strict_json(result.stdout)
        except (OSError, subprocess.SubprocessError):
            blocked('ROTATION_VM_FAILED')

    def capabilities(self):
        value = self.vm('capabilities')
        if value != {'result': 'ready', 'model': '1.26.4', 'toolchain': 'go1.26.3'}:
            blocked('ROTATION_CAPABILITY_INVALID')

    def generate(self, name):
        value = self.vm('generate', token_name=name)
        if set(value) != {'token'}:
            blocked('ROTATION_CANDIDATE_UNKNOWN')
        return value['token']

    def inspect(self, token, name=None):
        request = {'token': token}
        if name:
            request['expected_token_name'] = name
        value = self.vm('inspect', **request)
        if value.get('result') != 'verified':
            blocked('ROTATION_MODEL_INVALID')
        return {key: value[key] for key in ('token_id', 'user_id', 'token_name', 'scopes')}

    def revoke(self, token, metadata):
        value = self.vm('revoke', token=token, expected_token_name=metadata['token_name'],
                        expected_token_id=metadata['token_id'], expected_user_id=metadata['user_id'])
        expected = dict(metadata, result='revoked')
        if value != expected:
            blocked('ROTATION_REVOKE_UNCONFIRMED')

    def http(self, token, path):
        request = Request(self.contract.governance.base_url + '/api/v1/' + path,
                          headers={'Authorization': 'token ' + token, 'Accept': 'application/json'})
        try:
            try:
                response = build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=10)
            except HTTPError as error:
                response = error
            with response:
                raw = response.read(16385)
                if len(raw) > 16384:
                    blocked('ROTATION_HTTP_INVALID')
                return response.code, raw
        except Exception:
            blocked('ROTATION_HTTP_FAILED')

    def verify(self, token, metadata, scopes):
        code, raw = self.http(token, 'user')
        if code != 200:
            blocked('ROTATION_IDENTITY_FAILED')
        value = strict_json(raw)
        if (value.get('login') != self.target.username or value.get('is_admin') is not False
                or type(value.get('id')) is not int or value['id'] != metadata['user_id']):
            blocked('ROTATION_IDENTITY_MISMATCH')
        code, raw = self.http(token, 'notifications')
        value = strict_json(raw)
        match = re.search(r'token scope=([A-Za-z0-9:,_-]+)', str(value.get('message', '')))
        if (code != 403 or not match or set(match.group(1).split(',')) != set(scopes)
                or set(metadata['scopes']) != set(scopes)):
            blocked('ROTATION_SCOPE_MISMATCH')

    def rejected(self, token):
        code, _ = self.http(token, 'user')
        return code == 401


def rotate(contract, project_id, issue, source_sha, token_kind):
    if os.geteuid() != 0:
        raise BrokerError('ROTATION_OPERATOR_REQUIRED', 'independent operator identity required')
    if sys.platform != 'darwin':
        blocked('ROTATION_HOST_REQUIRED')
    try:
        target = rotation_target(contract, project_id, token_kind)
        grant = authorization(contract, target, issue, source_sha)
        uid = pwd.getpwnam(contract.raw['mac_host']['credential_owner']).pw_uid
        backend = SystemBackend(contract, target, issue, source_sha, grant.capability)
        return RotationTransaction(contract.raw['mac_host']['credential_root'], uid,
                                   target, grant.binding, backend).run()
    except BrokerError as error:
        code = error.code if re.fullmatch(r'ROTATION_[A-Z_]{1,64}', error.code) else 'ROTATION_FAILED'
        blocked(code)
    except Exception:
        blocked('ROTATION_FAILED')


def vm_operation(raw):
    """Fixed VM endpoint: existing git user plus protected, exact operator grant."""
    if sys.platform != 'linux' or os.geteuid() != pwd.getpwnam('git').pw_uid or os.geteuid() == 0:
        blocked('ROTATION_SERVICE_REQUIRED')
    request = strict_json(raw)
    common = {'action', 'project_id', 'token_kind', 'issue', 'source_sha', 'operator_capability'}
    fields = {'capabilities': set(), 'generate': {'token_name'}, 'inspect': {'token'},
              'revoke': {'token', 'expected_token_name', 'expected_token_id', 'expected_user_id'}}
    action = request.get('action')
    if not isinstance(action, str) or action not in fields:
        blocked('ROTATION_SCHEMA_INVALID')
    allowed = common | fields[action]
    if action == 'inspect' and 'expected_token_name' in request:
        allowed.add('expected_token_name')
    if set(request) != allowed:
        blocked('ROTATION_SCHEMA_INVALID')
    from .contract import load_access_contract
    contract = load_access_contract(ACCESS_PATH, GOVERNANCE_PATH)
    target = rotation_target(contract, request['project_id'], request['token_kind'])
    grant = authorization(contract, target, request['issue'], request['source_sha'], vm=True)
    verify_operator_capability(request['operator_capability'], grant.capability_digest)
    # Metadata commands cannot touch DB; do these before generating any PAT.
    def command(argv, data=None):
        try:
            result = subprocess.run(argv, input=data, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, timeout=30, check=False,
                                    env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'HOME': '/var/lib/gitea'})
            if result.returncode != 0 or len(result.stdout) > 16384:
                blocked('ROTATION_SERVICE_FAILED')
            return result.stdout
        except (OSError, subprocess.SubprocessError):
            blocked('ROTATION_SERVICE_FAILED')
    version = command([ROTATION_POLICY['gitea_binary'], '--version']).decode('ascii').strip()
    if not re.fullmatch(r'Gitea version 1\.26\.4 built with go[^\r\n]+', version):
        blocked('ROTATION_VERSION_MISMATCH')
    metadata = strict_json(command([ROTATION_POLICY['vm_helper'], '--version']))
    if metadata != {'helper_version': '1', 'gitea_model_version': '1.26.4', 'toolchain': 'go1.26.3'}:
        blocked('ROTATION_CAPABILITY_INVALID')
    if action == 'capabilities':
        return {'result': 'ready', 'model': '1.26.4', 'toolchain': 'go1.26.3'}
    if action == 'generate':
        name = request['token_name']
        if not isinstance(name, str) or not re.fullmatch(
                f"issue-{request['issue']}-{re.escape(target.token_kind)}-rotation-[0-9a-f]{{12}}", name):
            blocked('ROTATION_SCHEMA_INVALID')
        token = command([ROTATION_POLICY['gitea_binary'], '--config', ROTATION_POLICY['gitea_config'],
                         'admin', 'user', 'generate-access-token', '--username', target.username,
                         '--token-name', name, '--scopes', ','.join(target.scopes), '--raw']).decode('ascii').strip()
        if not TOKEN.fullmatch(token):
            blocked('ROTATION_CANDIDATE_UNKNOWN')
        return {'token': token}  # Authenticated private pipe; never a public receipt.
    helper_request = {'action': action, 'project_id': target.project_id, 'token_kind': target.token_kind}
    helper_request.update({key: request[key] for key in request if key not in common})
    value = strict_json(command([ROTATION_POLICY['vm_helper']], json.dumps(helper_request).encode()))
    if value.get('result') not in ('verified', 'revoked'):
        blocked('ROTATION_MODEL_INVALID')
    return value


def operator_main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        if arguments == ['--vm-operation']:
            require_private_pipes()
            value = vm_operation(sys.stdin.buffer.read(16385))
        else:
            # Exact schema avoids argparse echoing unexpected values into stderr.
            if len(arguments) != 8:
                blocked('ROTATION_SCHEMA_INVALID')
            pairs = dict(zip(arguments[::2], arguments[1::2]))
            if set(pairs) != {'--project', '--issue', '--sha', '--token-kind'}:
                blocked('ROTATION_SCHEMA_INVALID')
            if not re.fullmatch(r'[1-9][0-9]{0,17}', pairs['--issue']):
                blocked('ROTATION_SCHEMA_INVALID')
            from .contract import load_access_contract
            from .broker import HostAccessBroker
            contract = load_access_contract(ACCESS_PATH, GOVERNANCE_PATH)
            value = HostAccessBroker(contract).execute(
                pairs['--project'], 'gitea.credential.rotate', issue=int(pairs['--issue']),
                sha=pairs['--sha'], token_kind=pairs['--token-kind'])
        if arguments == ['--vm-operation']:
            require_private_pipes()
        print(json.dumps(value, sort_keys=True))
        return 0
    except Exception:
        # Especially on the private VM pipe, never echo request/error/CLI output.
        print('{"status":"BLOCKED_EXTERNAL","code":"ROTATION_OPERATOR_FAILED"}', file=sys.stderr)
        return 20


def installation_metadata(source_root, artifact=None):
    """Installer-only build pin/readback. No grant or Secret creation."""
    root = Path(source_root)
    def git(*args):
        # Exact approved source checkout only; never write global safe.directory.
        result = subprocess.run(['git', '-c', 'safe.directory=' + str(root.resolve()),
                                 '-C', str(root), *args], check=False,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return result
    head = git('rev-parse', 'HEAD')
    source_sha = head.stdout.decode().strip() if head.returncode == 0 else None
    merged = (source_sha is not None and SHA.fullmatch(source_sha) is not None
              and git('merge-base', '--is-ancestor', 'HEAD', 'origin/main').returncode == 0
              and git('status', '--porcelain').stdout == b'')
    files = {
        ACCESS_PATH: root / 'codex/config/host-access-broker.json',
        GOVERNANCE_PATH: root / 'codex/config/gitea-governance.json',
        '/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py':
            root / 'codex/runtime/aisoft_host_access/credential_rotation.py',
        ROTATION_POLICY['vm_operator']: root / 'codex/tools/rotate-gitea-service-account.sh',
    }
    helper = None
    if artifact:
        binary = Path(artifact)
        provenance = binary.with_name(binary.name + '.provenance.json')
        if binary.is_symlink() or provenance.is_symlink() or not binary.is_file() or not provenance.is_file():
            blocked('ROTATION_ARTIFACT_INVALID')
        evidence = strict_json(provenance.read_bytes(), limit=1048576)
        helper_root = root / 'codex/tools/gitea-pat-helper'
        lock = json.loads((helper_root / 'build-lock.json').read_bytes())
        architecture = {'aarch64': 'arm64', 'arm64': 'arm64', 'x86_64': 'amd64'}.get(os.uname().machine)
        platform = f'linux/{architecture}'
        pins = [item for item in lock['files'] if item['os'] + '/' + item['arch'] == platform]
        input_lock = evidence.get('toolchain_input', {})
        if (sys.platform != 'linux' or not merged or evidence.get('source_dirty') is not False
                or evidence.get('schema') != 'aisoft-gitea-pat-helper-build/v1'
                or evidence.get('source_commit') != source_sha
                or evidence.get('platform') != platform or evidence.get('toolchain') != 'go1.26.3'
                or evidence.get('gitea') != lock['gitea']
                or evidence.get('sha256') != hashlib.sha256(binary.read_bytes()).hexdigest()
                or evidence.get('go_mod_sha256') != hashlib.sha256((helper_root / 'go.mod').read_bytes()).hexdigest()
                or evidence.get('go_sum_sha256') != hashlib.sha256((helper_root / 'go.sum').read_bytes()).hexdigest()
                or evidence.get('source_sha256') != {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                                    for p in helper_root.glob('*.go')}
                or not isinstance(input_lock, dict)
                or len(pins) != 1 or input_lock.get('sha256') != pins[0]['sha256']
                or input_lock.get('filename') != pins[0]['filename']
                or not re.fullmatch(r'[0-9a-f]{64}', str(input_lock.get('extracted_tree_sha256', '')))):
            blocked('ROTATION_ARTIFACT_INVALID')
        version = subprocess.run([str(binary.resolve()), '--version'], check=False,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10,
                                 env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
        if version.returncode != 0 or strict_json(version.stdout) != {
                'helper_version': '1', 'gitea_model_version': '1.26.4', 'toolchain': 'go1.26.3'}:
            blocked('ROTATION_ARTIFACT_INVALID')
        helper = {'sha256': evidence['sha256'], 'platform': platform,
                  'model': '1.26.4', 'toolchain': 'go1.26.3'}
    return {'version': 1, 'source_sha': source_sha, 'merged_main': bool(merged),
            'files': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()},
            'helper': helper}


if __name__ == '__main__':
    raise SystemExit(operator_main())
