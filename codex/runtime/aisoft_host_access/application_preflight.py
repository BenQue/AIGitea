"""Fixed application target, bounded control-plane read, and no-start refusal.

There is intentionally no VM command executor: OrbStack's run/exec path has no
proved no-autostart primitive. Checking 'running' is not execution authority.
"""
from __future__ import annotations

import datetime
import json
import os
import math
import selectors
import signal
import subprocess
import time


LIMITS = {
    'request_seconds': 30, 'probe_seconds': 5, 'control_bytes': 65536,
    'helper_bytes': 262144, 'file_bytes': 65536, 'machines': 64,
    'sockets': 256, 'containers': 128, 'units': 6, 'groups': 32,
    'directories': 16, 'text_bytes': 256,
}


class PreflightError(Exception):
    def __init__(self, reason, status='BLOCKED'):
        self.reason, self.status = reason, status
        super().__init__(reason)


def run_bounded(argv, *, limit=65536, timeout=5, pass_fds=()):
    """Bound both pipes before allocation/decoding and cancel the process group."""
    deadline = time.monotonic() + timeout
    process = None
    try:
        process = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env={'PATH': '/usr/bin:/bin', 'LANG': 'C',
                                        'LC_ALL': 'C', 'HOME': '/Users/benque'},
            start_new_session=True, pass_fds=pass_fds,
        )
        total, output = 0, bytearray()
        with selectors.DefaultSelector() as selector:
            for pipe in (process.stdout, process.stderr):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise PreflightError('PROBE_TIMEOUT')
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fileobj.fileno(), min(8192, limit + 1 - total))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    if total > limit:
                        raise PreflightError('LIMIT_EXCEEDED', 'GAP')
                    if key.fileobj is process.stdout:
                        output.extend(chunk)
            try:
                process.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                raise PreflightError('PROBE_TIMEOUT') from None
            if process.returncode:
                raise PreflightError('CONTROL_READ_FAILED')
        return bytes(output)
    except OSError:
        raise PreflightError('CONTROL_READ_UNAVAILABLE') from None
    finally:
        if process is not None:
            # Descendants can retain pipes after the main probe exits.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()


def strict_json(data, limit):
    if type(data) is not bytes:
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
    if len(data) > limit:
        raise PreflightError('LIMIT_EXCEEDED', 'GAP')
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL') from None


def envelope(binding, *, started=None, operator=None, fingerprint=None):
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        'contract_version': 'application-target-preflight/v1',
        'observed_at_utc': now.isoformat(),
        'observed_at_jst': now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
        'project': binding['project_id'], 'target': binding['target_id'],
        'machine': binding['machine'], 'actual_operator': operator,
        'helper_version': binding['helper_version'], 'source_fingerprint': fingerprint,
        'limits': dict(LIMITS), 'duration_seconds': max(0, time.monotonic() - started) if started else 0,
        'status': 'BLOCKED', 'reason': 'TARGET_EXECUTION_NO_START_UNPROVEN',
        'complete': False, 'target_execution_count': 0, 'items': {},
        'preservation': {'collector_calls': 'NOT RUN', 'os_atime_audit': 'NOT RUN',
                         'whole_machine_before_after': 'NOT RUN'},
    }


def read_preflight(contract, binding, *, reader=None):
    started = time.monotonic()
    result = envelope(binding, started=started)
    reader = run_bounded if reader is None else reader
    try:
        raw = reader([contract.raw['mac_host']['orbstack_binary'], 'list', '--format', 'json'],
                     limit=LIMITS['control_bytes'], timeout=LIMITS['probe_seconds'])
        machines = strict_json(raw, LIMITS['control_bytes'])
        if type(machines) is not list:
            raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
        if len(machines) > LIMITS['machines']:
            raise PreflightError('LIMIT_EXCEEDED', 'GAP')
        matches = []
        for machine in machines:
            if not isinstance(machine, dict) or type(machine.get('name')) is not str:
                raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
            if len(machine['name'].encode()) > LIMITS['text_bytes']:
                raise PreflightError('LIMIT_EXCEEDED', 'GAP')
            if machine['name'] == binding['machine']:
                matches.append(machine)
        if len(matches) != 1:
            raise PreflightError('TARGET_MISSING' if not matches else 'TARGET_AMBIGUOUS')
        state = matches[0].get('state')
        if state != 'running':
            raise PreflightError('TARGET_STOPPED' if state == 'stopped' else 'TARGET_STATE_UNKNOWN')
        # Even a running->stopped race is safe: there is no target execution path.
    except PreflightError as error:
        result.update(status=error.status, reason=error.reason)
    except Exception:
        result.update(status='BLOCKED', reason='CONTROL_READ_UNAVAILABLE')
    result['duration_seconds'] = max(0, time.monotonic() - started)
    return result


def validate_control_reply(value):
    """This release cannot execute a target; only the bounded refusal is valid."""
    from .contract import APPLICATION_TARGET
    expected = envelope(APPLICATION_TARGET)
    if type(value) is not dict or set(value) != set(expected):
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
    fixed = ('contract_version', 'project', 'target', 'machine', 'actual_operator',
             'helper_version', 'source_fingerprint', 'limits', 'complete',
             'target_execution_count', 'items', 'preservation')
    if any(value[key] != expected[key] for key in fixed):
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
    if type(value['complete']) is not bool or type(value['target_execution_count']) is not int:
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
    if any(type(x) is not int for x in value['limits'].values()):
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
    reasons = {'TARGET_EXECUTION_NO_START_UNPROVEN', 'TARGET_MISSING', 'TARGET_AMBIGUOUS',
               'TARGET_STOPPED', 'TARGET_STATE_UNKNOWN', 'RESPONSE_SCHEMA_INVALID',
               'LIMIT_EXCEEDED', 'PROBE_TIMEOUT', 'CONTROL_READ_FAILED', 'CONTROL_READ_UNAVAILABLE'}
    if value['status'] not in ('BLOCKED', 'GAP', 'FAIL') or value['reason'] not in reasons:
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
    duration = value['duration_seconds']
    if type(duration) not in (int, float) or not math.isfinite(duration) or not 0 <= duration <= 30:
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL')
    try:
        utc = datetime.datetime.fromisoformat(value['observed_at_utc'])
        jst = datetime.datetime.fromisoformat(value['observed_at_jst'])
        if utc.utcoffset() != datetime.timedelta(0) or jst.utcoffset() != datetime.timedelta(hours=9) or utc != jst:
            raise ValueError()
    except (ValueError, TypeError):
        raise PreflightError('RESPONSE_SCHEMA_INVALID', 'FAIL') from None
    return value
