#!/usr/bin/env python3
"""One-shot fixed AppServer collector. Standard library only, no caller inputs."""
from __future__ import annotations

import datetime
import errno
import hashlib
import ipaddress
import json
import os
import platform
import re
import selectors
import signal
import socket
import stat
import subprocess
import sys
import time


HELPER = '/usr/local/libexec/aisoft/application-target-preflight'
LIMITS = {
    'request_seconds': 30, 'probe_seconds': 5, 'control_bytes': 65536,
    'helper_bytes': 262144, 'file_bytes': 65536, 'machines': 64,
    'sockets': 256, 'containers': 128, 'units': 6, 'groups': 32,
    'directories': 16, 'text_bytes': 256,
}
UNITS = ('nginx.service', 'postgresql.service', 'postgresql@18-main.service',
         'pm2-benque.service', 'localwms-api.service', 'localwms-worker.service')
DIRECTORIES = {
    'etc_localwms': '/etc/localwms', 'opt_localwms': '/opt/localwms',
    'current': '/opt/localwms/current', 'releases': '/opt/localwms/releases',
    'state': '/opt/localwms/state', 'backups': '/opt/localwms/backups',
    'retired_app_data': '/opt/retired-app-data-20260913',
    'retired_nginx': '/etc/nginx/sites-retired-20260913',
}
BINARIES = {'node': '/opt/node24.18.0/bin/node',
            **{name: '/usr/lib/postgresql/18/bin/' + name
               for name in ('postgres', 'psql', 'pg_dump', 'pg_restore')}}
NPM_METADATA = '/opt/node24.18.0/bin/npm'
NPM_PACKAGE = '/opt/node24.18.0/lib/node_modules/npm/package.json'
FILESYSTEMS = {'root': '/', 'opt': '/opt', 'pg18': '/var/lib/postgresql/18/main'}
READ_PATHS = {'/etc/machine-id', '/etc/os-release', '/usr/lib/os-release',
              '/proc/meminfo', NPM_PACKAGE, HELPER}
COMMANDS = {'/usr/bin/id', '/usr/bin/ss', '/usr/bin/systemctl', *BINARIES.values()}
ALL_PATHS = READ_PATHS | COMMANDS | set(DIRECTORIES.values()) | set(FILESYSTEMS.values()) | {NPM_METADATA}
SS_ARGUMENTS = ('--listening', '--tcp', '--udp', '--numeric', '--no-header', '--oneline', '--processes')
UNIT_ARGUMENTS = ('--system', 'show', '--no-pager', '--property=LoadState,ActiveState,MainPID', '--')
VERSION = re.compile(r'(?:v)?[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?')
NAME = re.compile(r'[A-Za-z0-9_.@+-]{1,256}')


class ProbeFailure(Exception):
    def __init__(self, reason, status='BLOCKED'):
        self.reason, self.status = reason, status
        super().__init__(reason)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def text(value):
    if type(value) is not str or len(value.encode('utf-8')) > LIMITS['text_bytes']:
        raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')
    if not value or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    return value


def integer(value):
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    return value


def bounded_json(raw):
    if type(raw) is not bytes or len(raw) > LIMITS['file_bytes']:
        raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError()
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise ProbeFailure('INVALID_VALUE', 'FAIL') from None


def read_fd(fd):
    result = bytearray()
    while True:
        chunk = os.read(fd, min(8192, LIMITS['file_bytes'] + 1 - len(result)))
        if not chunk:
            return bytes(result)
        result.extend(chunk)
        if len(result) > LIMITS['file_bytes']:
            raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')


def bounded_command(argv, *, deadline, pass_fds=(), executable=None):
    remaining = min(LIMITS['probe_seconds'], deadline - time.monotonic())
    if remaining <= 0:
        raise ProbeFailure('PROBE_TIMEOUT')
    end, process = time.monotonic() + remaining, None
    try:
        process = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C', 'HOME': '/nonexistent'},
            start_new_session=True, pass_fds=pass_fds, executable=executable,
        )
        total, result = 0, bytearray()
        with selectors.DefaultSelector() as selector:
            for pipe in (process.stdout, process.stderr):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic() >= end:
                    raise ProbeFailure('PROBE_TIMEOUT')
                for key, _ in selector.select(min(0.1, end - time.monotonic())):
                    chunk = os.read(key.fileobj.fileno(), min(8192, LIMITS['file_bytes'] + 1 - total))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    if total > LIMITS['file_bytes']:
                        raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')
                    if key.fileobj is process.stdout:
                        result.extend(chunk)
            try:
                process.wait(timeout=max(0.001, end - time.monotonic()))
            except subprocess.TimeoutExpired:
                raise ProbeFailure('PROBE_TIMEOUT') from None
        if process.returncode:
            raise ProbeFailure('PROBE_FAILED')
        return bytes(result)
    except OSError:
        raise ProbeFailure('PROBE_UNAVAILABLE') from None
    finally:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            process.stdout.close()
            process.stderr.close()


def metadata_value(info):
    kind = ('file' if stat.S_ISREG(info.st_mode) else
            'directory' if stat.S_ISDIR(info.st_mode) else
            'symlink' if stat.S_ISLNK(info.st_mode) else
            'socket' if stat.S_ISSOCK(info.st_mode) else 'other')
    return {'uid': integer(info.st_uid), 'gid': integer(info.st_gid),
            'mode': stat.S_IMODE(info.st_mode), 'kind': kind, 'is_symlink': kind == 'symlink'}


class NativeSystem:
    """Only compiled paths; openat pins ancestors and O_NOFOLLOW pins content."""
    def _parent(self, path, trusted=False):
        if path not in ALL_PATHS or not hasattr(os, 'O_NOFOLLOW'):
            raise ProbeFailure('UNTRUSTED_PATH')
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in path.split('/')[1:-1]:
                if not part:
                    continue
                info = os.fstat(fd)
                if trusted and (info.st_uid != 0 or info.st_mode & 0o022):
                    raise ProbeFailure('UNTRUSTED_PATH')
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            info = os.fstat(fd)
            if trusted and (info.st_uid != 0 or info.st_mode & 0o022):
                raise ProbeFailure('UNTRUSTED_PATH')
            return fd, path.rsplit('/', 1)[1] or '.'
        except BaseException:
            os.close(fd)
            raise

    def _open(self, path, trusted=False, directory=False):
        parent, leaf = self._parent(path, trusted)
        try:
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if directory:
                flags |= os.O_DIRECTORY
            fd = os.open(leaf, flags, dir_fd=parent)
        finally:
            os.close(parent)
        info = os.fstat(fd)
        if (trusted and (info.st_uid != 0 or info.st_mode & 0o022)) or (
                not directory and not stat.S_ISREG(info.st_mode)):
            os.close(fd)
            raise ProbeFailure('UNTRUSTED_PATH')
        return fd

    def metadata(self, path):
        parent, leaf = self._parent(path)
        try:
            return metadata_value(os.stat(leaf, dir_fd=parent, follow_symlinks=False))
        finally:
            os.close(parent)

    def read(self, path):
        if path not in READ_PATHS:
            raise ProbeFailure('UNTRUSTED_PATH')
        if path == '/etc/os-release':
            parent, leaf = self._parent(path, trusted=True)
            try:
                info = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    link = os.readlink(leaf, dir_fd=parent)
                    if link not in ('/usr/lib/os-release', '../usr/lib/os-release'):
                        raise ProbeFailure('UNTRUSTED_PATH')
                    path = '/usr/lib/os-release'
            finally:
                os.close(parent)
        fd = self._open(path, trusted=True)
        try:
            return read_fd(fd)
        finally:
            os.close(fd)

    def filesystem(self, path):
        fd = self._open(path, directory=True)
        try:
            info = os.fstatvfs(fd)
            return {'total_bytes': integer(info.f_blocks * info.f_frsize),
                    'available_bytes': integer(info.f_bavail * info.f_frsize),
                    'free_bytes': integer(info.f_bfree * info.f_frsize)}
        finally:
            os.close(fd)

    def command(self, path, args, deadline):
        vector = tuple(args)
        permitted = (
            path in BINARIES.values() and vector == ('--version',) or
            path == '/usr/bin/id' and vector in (('-un',), ('--', 'localwms'), ('--', 'aisoft-preflight')) or
            path == '/usr/bin/ss' and vector == SS_ARGUMENTS or
            path == '/usr/bin/systemctl' and len(vector) == 6 and vector[:-1] == UNIT_ARGUMENTS and vector[-1] in UNITS
        )
        if not permitted:
            raise ProbeFailure('UNTRUSTED_PATH')
        fd = self._open(path, trusted=True)
        try:
            if not os.fstat(fd).st_mode & 0o111:
                raise ProbeFailure('UNTRUSTED_PATH')
            if os.pread(fd, 4, 0) != b'\x7fELF':
                raise ProbeFailure('UNTRUSTED_PATH')
            # Executes the opened inode, so path replacement cannot swap the binary.
            # Preserve argv[0]: PostgreSQL derives its --version program name from it.
            return bounded_command([path, *args], deadline=deadline, pass_fds=(fd,),
                                   executable='/proc/self/fd/' + str(fd))
        finally:
            os.close(fd)

    def operator(self, deadline):
        return self.command('/usr/bin/id', ['-un'], deadline).decode('utf-8').strip()

    def fingerprint(self):
        if os.path.abspath(__file__) != HELPER:
            raise ProbeFailure('SOURCE_PATH_UNTRUSTED')
        return hashlib.sha256(self.read(HELPER)).hexdigest()

    def hostname(self): return socket.gethostname()
    def architecture(self): return platform.machine()
    def cpus(self): return os.cpu_count()

    def account(self, user, deadline):
        if user not in ('localwms', 'aisoft-preflight'):
            raise ProbeFailure('UNTRUSTED_PATH')
        raw = self.command('/usr/bin/id', ['--', user], deadline).decode('utf-8').strip()
        match = re.fullmatch(r'uid=(\d+)\(' + re.escape(user) +
                            r'\) gid=(\d+)\(([A-Za-z0-9_.@+-]+)\) groups=(.*)', raw)
        if not match:
            raise ProbeFailure('INVALID_VALUE', 'FAIL')
        groups = match[4].split(',', LIMITS['groups'])
        if len(groups) > LIMITS['groups']:
            raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')
        values = []
        for group in groups:
            entry = re.fullmatch(r'(\d+)\(([A-Za-z0-9_.@+-]+)\)', group)
            if not entry:
                raise ProbeFailure('INVALID_VALUE', 'FAIL')
            values.append({'gid': integer(int(entry[1])), 'name': text(entry[2])})
        return {'uid': integer(int(match[1])), 'gid': integer(int(match[2])), 'groups': values}


def os_release(raw):
    if len(raw) > LIMITS['file_bytes']:
        raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')
    result = {}
    for line in raw.decode('utf-8').splitlines():
        key, sep, value = line.partition('=')
        if key not in ('ID', 'VERSION_ID', 'VERSION', 'VERSION_CODENAME') or not sep:
            continue
        if key in result:
            raise ProbeFailure('INVALID_VALUE', 'FAIL')
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        if any(c in value for c in ('$', chr(96), '\\')):
            raise ProbeFailure('INVALID_VALUE', 'FAIL')
        result[key] = text(value)
    if set(result) != {'ID', 'VERSION_ID', 'VERSION', 'VERSION_CODENAME'}:
        raise ProbeFailure('MISSING', 'GAP')
    return result


def memory(raw):
    result = {}
    for line in raw.decode('ascii').splitlines():
        match = re.fullmatch(r'(MemTotal|MemAvailable):\s+(\d+) kB', line)
        if match:
            if match[1] in result:
                raise ProbeFailure('INVALID_VALUE', 'FAIL')
            result[match[1]] = integer(int(match[2]) * 1024)
    if set(result) != {'MemTotal', 'MemAvailable'}:
        raise ProbeFailure('MISSING', 'GAP')
    return result


def machine_id(raw):
    value = raw.decode('ascii').strip()
    if not re.fullmatch(r'[0-9a-f]{32}', value):
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    return value


def projected_metadata(value):
    if type(value) is not dict or value.get('kind') not in ('file', 'directory', 'symlink', 'socket', 'other'):
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    result = {key: integer(value.get(key)) for key in ('uid', 'gid', 'mode')}
    if result['mode'] > 0o7777 or type(value.get('is_symlink')) is not bool:
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    result.update(kind=value['kind'], is_symlink=value['is_symlink'])
    if result['is_symlink'] != (result['kind'] == 'symlink'):
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    return result


def projected_filesystem(value):
    if type(value) is not dict:
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    result = {key: integer(value.get(key)) for key in ('total_bytes', 'available_bytes', 'free_bytes')}
    if not result['available_bytes'] <= result['free_bytes'] <= result['total_bytes']:
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    return result


def projected_account(value):
    if type(value) is not dict or type(value.get('groups')) is not list:
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    if len(value['groups']) > LIMITS['groups']:
        raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')
    groups = []
    for group in value['groups']:
        if type(group) is not dict or type(group.get('name')) is not str or not NAME.fullmatch(group['name']):
            raise ProbeFailure('INVALID_VALUE', 'FAIL')
        groups.append({'gid': integer(group.get('gid')), 'name': text(group['name'])})
    return {'uid': integer(value.get('uid')), 'gid': integer(value.get('gid')), 'groups': groups}


def listeners(raw):
    rows = []
    for line in raw.decode('utf-8').splitlines():
        if len(rows) == LIMITS['sockets']:
            raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')
        parts = line.split()
        if len(parts) < 6 or parts[0] not in ('tcp', 'udp') or parts[1] not in ('LISTEN', 'UNCONN'):
            raise ProbeFailure('INVALID_VALUE', 'FAIL')
        address, sep, port = parts[4].rpartition(':')
        if not sep or not port.isascii() or not port.isdigit() or not 0 < int(port) <= 65535:
            raise ProbeFailure('INVALID_VALUE', 'FAIL')
        address = text(address.strip('[]'))
        if address != '*':
            try:
                ipaddress.ip_address(address)
            except ValueError:
                raise ProbeFailure('INVALID_VALUE', 'FAIL') from None
        # No process argv, environment, cwd or Unix sockets are requested.
        process = re.search(r'\("([A-Za-z0-9_.@+-]+)",pid=(\d+),fd=\d+\)', line)
        rows.append({'protocol': parts[0], 'address': address, 'port': int(port),
                     'pid': integer(int(process[2])) if process else None,
                     'comm': text(process[1]) if process else None})
    return rows


def unit_value(raw):
    values = {}
    for line in raw.decode('utf-8').splitlines():
        key, sep, value = line.partition('=')
        if key in ('LoadState', 'ActiveState', 'MainPID') and sep:
            if key in values:
                raise ProbeFailure('INVALID_VALUE', 'FAIL')
            values[key] = value
    if set(values) != {'LoadState', 'ActiveState', 'MainPID'}:
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    if values['LoadState'] not in ('loaded', 'not-found', 'masked', 'error', 'bad-setting', 'stub', 'merged'):
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    if values['ActiveState'] not in ('active', 'reloading', 'inactive', 'failed', 'activating',
                                    'deactivating', 'maintenance', 'refreshing'):
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    if not re.fullmatch(r'[0-9]{1,10}', values['MainPID']):
        raise ProbeFailure('INVALID_VALUE', 'FAIL')
    values['MainPID'] = integer(int(values['MainPID']))
    return values


def observed(value):
    return {'status': 'PASS', 'reason': 'OBSERVED', 'value': value, 'complete': True, 'observed_at': now()}


def unavailable(reason, status='BLOCKED'):
    return {'status': status, 'reason': reason, 'value': None, 'complete': False, 'observed_at': now()}


def collect(system=None):
    system = NativeSystem() if system is None else system
    start = time.monotonic()
    deadline = start + LIMITS['request_seconds']
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    result = {
        'contract_version': 'application-target-preflight/v1',
        'observed_at_utc': timestamp.isoformat(),
        'observed_at_jst': timestamp.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
        'project': 'localwms', 'target': 'localwms-local-test', 'machine': 'AppServer',
        'actual_operator': None, 'helper_version': 'application-target-preflight/v1',
        'source_fingerprint': None, 'limits': dict(LIMITS), 'duration_seconds': 0,
        'status': 'BLOCKED', 'reason': 'OPERATOR_MISMATCH', 'complete': False,
        'target_execution_count': 0, 'items': {},
        'preservation': {'collector_calls': 'NOT RUN', 'os_atime_audit': 'NOT RUN',
                         'whole_machine_before_after': 'NOT RUN'},
    }
    try:
        if system.operator(deadline) != 'aisoft-preflight':
            return result
        result['actual_operator'] = 'aisoft-preflight'
        fingerprint = system.fingerprint()
        if not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
            raise ProbeFailure('SOURCE_PATH_UNTRUSTED')
        result['source_fingerprint'] = fingerprint
    except ProbeFailure as error:
        result.update(status=error.status, reason=error.reason)
        return result
    except Exception:
        result['reason'] = 'OPERATOR_HELPER_UNAVAILABLE'
        return result
    result['target_execution_count'] = 1  # standalone helper observation, never a VM lifecycle action

    def item(name, call):
        if time.monotonic() >= deadline:
            result['items'][name] = unavailable('PROBE_TIMEOUT')
            return
        try:
            value = call()
            if time.monotonic() >= deadline:
                raise ProbeFailure('PROBE_TIMEOUT')
            result['items'][name] = observed(value)
        except ProbeFailure as error:
            result['items'][name] = unavailable(error.reason, error.status)
        except FileNotFoundError:
            result['items'][name] = unavailable('MISSING', 'GAP')
        except PermissionError:
            result['items'][name] = unavailable('PERMISSION_DENIED')
        except OSError as error:
            result['items'][name] = unavailable('UNTRUSTED_PATH' if error.errno in (errno.ELOOP, errno.ENOTDIR)
                                               else 'PROBE_UNAVAILABLE')
        except Exception:
            result['items'][name] = unavailable('INVALID_VALUE', 'FAIL')

    def read(path):
        raw = system.read(path)
        if type(raw) is not bytes or len(raw) > LIMITS['file_bytes']:
            raise ProbeFailure('LIMIT_EXCEEDED', 'GAP')
        return raw

    item('identity.hostname', lambda: text(system.hostname()))
    item('identity.machine_id', lambda: machine_id(read('/etc/machine-id')))
    item('identity.os', lambda: os_release(read('/etc/os-release')))
    item('identity.architecture', lambda: text(system.architecture()))
    item('resources.cpu_count', lambda: integer(system.cpus()))
    item('resources.memory', lambda: memory(read('/proc/meminfo')))
    for name, path in FILESYSTEMS.items():
        item('filesystem.' + name, lambda path=path: projected_filesystem(system.filesystem(path)))
    for name, path in BINARIES.items():
        def binary(name=name, path=path):
            meta = projected_metadata(system.metadata(path))
            if meta['kind'] != 'file' or meta['uid'] != 0 or meta['mode'] & 0o022:
                raise ProbeFailure('UNTRUSTED_PATH')
            version = text(system.command(path, ['--version'], deadline).decode('utf-8').strip())
            pattern = VERSION if name == 'node' else re.compile(re.escape(name) + r' \(PostgreSQL\) 18\.[0-9]+(?: [A-Za-z0-9().+ _-]+)?')
            if not pattern.fullmatch(version):
                raise ProbeFailure('INVALID_VALUE', 'FAIL')
            return {'metadata': meta, 'version': version}
        item('runtime.' + name, binary)
    item('runtime.npm_metadata', lambda: projected_metadata(system.metadata(NPM_METADATA)))
    def npm():
        value = bounded_json(read(NPM_PACKAGE))
        version = value.get('version') if isinstance(value, dict) else None
        if type(version) is not str or not VERSION.fullmatch(version):
            raise ProbeFailure('INVALID_VALUE', 'FAIL')
        return text(version)
    item('runtime.npm', npm)
    item('sockets.listeners', lambda: listeners(system.command(
        '/usr/bin/ss', SS_ARGUMENTS, deadline)))
    for unit in UNITS:
        item('service.' + unit, lambda unit=unit: unit_value(system.command(
            '/usr/bin/systemctl', (*UNIT_ARGUMENTS, unit), deadline)))
    for user in ('localwms', 'aisoft-preflight'):
        item('account.' + user, lambda user=user: projected_account(system.account(user, deadline)))
    for name, path in DIRECTORIES.items():
        item('directory.' + name, lambda path=path: projected_metadata(system.metadata(path)))
    result['items']['docker'] = unavailable('SOCKET_READ_ROUTE_UNAVAILABLE')
    result['items']['postgres.instance'] = unavailable('PG_READ_ROUTE_UNAUTHORIZED')
    result['items']['archive_inventory'] = unavailable('ARCHIVE_INVENTORY_UNBOUND', 'GAP')
    result.update(status='GAP', reason='PARTIAL', duration_seconds=max(0, time.monotonic() - start))
    return result


def main():
    if len(sys.argv) != 1:
        print('{"status":"FAIL","reason":"ARGUMENT_MISMATCH"}', file=sys.stderr)
        return 20
    if sys.platform != 'linux':
        print('{"status":"BLOCKED","reason":"PLATFORM_UNSUPPORTED"}')
        return 20
    def alarm(_signum, _frame):
        raise ProbeFailure('PROBE_TIMEOUT')
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, LIMITS['request_seconds'])
    try:
        result = collect()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    raw = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(raw) > LIMITS['helper_bytes']:
        print('{"status":"GAP","reason":"LIMIT_EXCEEDED","complete":false}')
        return 20
    sys.stdout.buffer.write(raw + b'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
