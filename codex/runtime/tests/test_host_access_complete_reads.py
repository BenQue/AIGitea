"""Issue #336 source acceptance: synthetic transport/refs; no installed custody access."""
import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from email.message import Message
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aisoft_host_access.broker import BrokerError, HostAccessBroker, ReadCollection, _pull_transport
from aisoft_host_access.cli import main
from aisoft_host_access.contract import load_access_contract
from tests.test_host_access import ACCESS, GOVERNANCE, StaticCredentials


def pull(number):
    return {"number": number, "state": "closed" if number % 2 else "open", "merged": number % 2 == 1,
            "title": "synthetic", "head": {"ref": "change/333-pat-rotation-acceptance" if number == 51 else "unrelated"},
            "base": {"repo": {"full_name": "admin/aisoft-platform"}, "ref": "main"}}


class ReadFixture:
    def __init__(self, count=125, cap=50):
        self.items = [pull(i + 1) for i in range(count)]
        self.cap, self.calls = cap, []
        self.mutate = None
        self.contract = load_access_contract(ACCESS, GOVERNANCE)
        self.broker = HostAccessBroker(self.contract, credentials=StaticCredentials(), transport=self.transport)

    def transport(self, method, url, headers, body, **kwargs):
        if url.endswith('/api/v1/user'):
            return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
        assert method == 'GET' and body is None
        assert 0 < kwargs['response_limit'] <= 4 * 1024 * 1024 and kwargs['follow_redirects'] is False
        self.calls.append(url)
        assert '/repos/admin/aisoft-platform/pulls?state=' in url and '&sort=oldest&limit=50&page=' in url
        page = int(url.rsplit('page=', 1)[1])
        start = (page - 1) * self.cap
        raw = json.dumps(self.items[start:start + self.cap]).encode()
        result = (200, {'X-Total-Count': str(len(self.items))}, raw)
        return self.mutate(len(self.calls), page, result) if self.mutate else result

    def read(self, state='all'):
        return self.broker.execute('aisoft-platform', 'gitea.pulls.read', state=state)


class CompletePullReads(unittest.TestCase):
    def fails(self, fixture, code):
        with self.assertRaises(BrokerError) as caught:
            fixture.read()
        self.assertEqual(caught.exception.code, code)
        self.assertFalse(hasattr(caught.exception, 'read_receipt'))

    def test_125_entries_include_merged_closed_and_source_after_page_one(self):
        fixture = ReadFixture()
        values = fixture.read()
        self.assertEqual(values, fixture.items)
        self.assertEqual(sum(p['head']['ref'].startswith('change/333-') for p in values), 1)
        self.assertEqual(values.read_receipt['terminal_empty_pages'], [4, 4])
        self.assertEqual(len(fixture.calls), 8)
        self.assertEqual(values.read_receipt['server_total'], 125)

    def test_full_page_always_needs_next_empty_page(self):
        for count in (0, 49, 50, 51, 100):
            with self.subTest(count=count):
                fixture = ReadFixture(count)
                values = fixture.read()
                self.assertEqual(len(values), count)
                self.assertEqual(values.read_receipt['terminal_empty_pages'], [(count + 49) // 50 + 1] * 2)

    def test_server_caps_below_requested_limit_do_not_hide_later_pages(self):
        fixture = ReadFixture(50, cap=25)
        self.assertEqual(len(fixture.read()), 50)
        self.assertEqual([int(url.rsplit('=', 1)[1]) for url in fixture.calls], [1, 2, 3, 1, 2, 3])

    def test_duplicates_after_page_one_fail(self):
        fixture = ReadFixture(51)
        fixture.items[50]['number'] = 1
        self.fails(fixture, 'READ_COLLECTION_DUPLICATE')

    def test_empty_page_with_nonzero_total_does_not_prove_absence(self):
        fixture = ReadFixture(1)
        fixture.mutate = lambda call, page, result: (200, {'X-Total-Count': '1'}, b'[]')
        self.fails(fixture, 'READ_COLLECTION_INCOMPLETE')

    def test_total_header_missing_duplicated_or_invalid_fail(self):
        for headers, code in [({}, 'READ_TOTAL_INVALID'),
                              ({'X-Total-Count': '1', 'x-total-count': '1'}, 'READ_TOTAL_INVALID'),
                              ({'X-Total-Count': '-1'}, 'READ_TOTAL_INVALID'),
                              ({'X-Total-Count': '01'}, 'READ_TOTAL_INVALID'),
                              ({'X-Total-Count': 1}, 'RESPONSE_SCHEMA_INVALID')]:
            with self.subTest(headers=headers):
                fixture = ReadFixture(1)
                fixture.mutate = lambda c, p, r: (r[0], headers, r[2])
                self.fails(fixture, code)

    def test_total_changes_during_scan_fail(self):
        fixture = ReadFixture(51)
        fixture.mutate = lambda c, p, r: (r[0], {'X-Total-Count': '52' if c == 2 else '51'}, r[2])
        self.fails(fixture, 'READ_COLLECTION_MOVED')

    def test_equal_count_but_changed_second_scan_fails(self):
        fixture = ReadFixture(1)
        def mutate(c, p, r):
            if c == 3:
                values = json.loads(r[2])
                values[0]['title'] = 'changed'
                return r[0], r[1], json.dumps(values).encode()
            return r
        fixture.mutate = mutate
        self.fails(fixture, 'READ_COLLECTION_MOVED')

    def test_transient_failure_and_redirect_are_never_complete(self):
        for status in (301, 401, 403, 404, 429, 500):
            with self.subTest(status=status):
                fixture = ReadFixture(51)
                fixture.mutate = lambda c, p, r: (status, {}, b'{}') if c == 2 else r
                self.fails(fixture, 'HTTP_' + str(status) if status in (401, 403, 404) else 'HTTP_ERROR')

    def test_transport_failure_is_sanitized(self):
        fixture = ReadFixture(1)
        def bad(*args):
            raise OSError('synthetic detail must not escape')
        fixture.mutate = bad
        with self.assertRaises(BrokerError) as caught:
            fixture.read()
        self.assertEqual(str(caught.exception), 'pull scan transport failed')

    def test_bad_json_duplicate_keys_or_non_array_fails(self):
        for raw in (b'{', b'{}', b'[{"number":1,"number":2}]', b'[NaN]'):
            with self.subTest(raw=raw):
                fixture = ReadFixture(1)
                fixture.mutate = lambda c, p, r: (200, {'X-Total-Count': '1'}, raw)
                self.fails(fixture, 'RESPONSE_SCHEMA_INVALID')

    def test_wrong_manifest_repo_bool_number_or_invalid_state_fails(self):
        for field, value in [('number', True), ('state', 'merged'), ('merged', 1), ('base', {'repo': {'full_name': 'other/repo'}})]:
            with self.subTest(field=field):
                fixture = ReadFixture(1)
                fixture.items[0][field] = value
                self.fails(fixture, 'RESPONSE_SCHEMA_INVALID')

    def test_filter_mismatch_fails(self):
        fixture = ReadFixture(1)
        with self.assertRaises(BrokerError):
            fixture.read(state='open')

    def test_count_and_terminal_page_bounds_fail_closed(self):
        for count, cap in [(5000, 50), (100, 1)]:
            with self.subTest(count=count):
                self.fails(ReadFixture(count, cap), 'READ_SCAN_BOUND')

    def test_time_bound_stops_before_any_page_request(self):
        fixture = ReadFixture(1)
        with patch('aisoft_host_access.broker.time.monotonic', side_effect=[0, 100]):
            self.fails(fixture, 'READ_SCAN_TIME_BOUND')
        self.assertEqual(fixture.calls, [])

    def test_aggregate_scan_and_single_page_byte_bounds_fail_closed(self):
        fixture = ReadFixture(125)
        for item in fixture.items:
            item['body'] = 'x' * 30000
        self.fails(fixture, 'READ_SCAN_BOUND')
        fixture = ReadFixture(1)
        fixture.items[0]['body'] = 'x' * (2 * 1024 * 1024)
        self.fails(fixture, 'READ_SCAN_BOUND')

    def test_empty_page_total_and_entry_count_must_agree(self):
        fixture = ReadFixture(1)
        fixture.mutate = lambda c, p, r: (r[0], {'X-Total-Count': '0'}, r[2])
        self.fails(fixture, 'READ_COLLECTION_INCOMPLETE')

    def test_cli_keeps_array_stdout_and_separate_coverage_receipt(self):
        fixture = ReadFixture(51)
        out, err = io.StringIO(), io.StringIO()
        with patch('aisoft_host_access.cli.HostAccessBroker', return_value=fixture.broker), redirect_stdout(out), redirect_stderr(err):
            code = main(['--access-manifest', str(ACCESS), '--governance-manifest', str(GOVERNANCE),
                         'broker', '--project', 'aisoft-platform', '--operation', 'gitea.pulls.read', '--state', 'all'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue()), fixture.items)
        proof = json.loads(err.getvalue())
        import hashlib
        self.assertEqual(proof['stdout_sha256'], hashlib.sha256(out.getvalue().encode()).hexdigest())
        self.assertNotIn('Authorization', err.getvalue())

    def test_maximum_4950_entries_finish_with_page_100_empty_in_both_scans(self):
        fixture = ReadFixture(4950)
        result = fixture.read()
        self.assertEqual(result.read_receipt['terminal_empty_pages'], [100, 100])
        self.assertEqual(len(result), 4950)
        self.assertEqual(len(fixture.calls), 200)

    def test_open_and_closed_filters_retain_complete_observations(self):
        for state in ('open', 'closed'):
            with self.subTest(state=state):
                fixture = ReadFixture(125)
                fixture.items = [item for item in fixture.items if item['state'] == state]
                self.assertEqual(fixture.read(state), fixture.items)
                self.assertTrue(all('?state=' + state + '&' in url for url in fixture.calls))

    def test_repeated_raw_total_headers_are_not_coalesced_into_success(self):
        fixture = ReadFixture(0)
        fixture.mutate = lambda c, p, r: (200, [('X-Total-Count', '0'), ('X-Total-Count', '0')], b'[]')
        self.fails(fixture, 'READ_TOTAL_INVALID')

    def test_nested_duplicate_nonfinite_utf8_and_wrong_scalar_types_fail(self):
        for raw in (b'[{"meta":{"x":1,"x":2}}]', b'[Infinity]', b'[-Infinity]',
                    b'[{"extra":1e999}]', b'\xff', b'["\ud800"]'):
            with self.subTest(raw=raw):
                fixture = ReadFixture(1)
                fixture.mutate = lambda c, p, r: (200, {'X-Total-Count': '1'}, raw)
                self.fails(fixture, 'RESPONSE_SCHEMA_INVALID')
        for field, value in [('state', []), ('state', {}), ('number', 1.0), ('number', 0),
                             ('merged', None), ('base', [])]:
            with self.subTest(field=field, value=value):
                fixture = ReadFixture(1)
                fixture.items[0][field] = value
                self.fails(fixture, 'RESPONSE_SCHEMA_INVALID')

    def test_second_scan_type_change_is_detected_even_when_python_values_compare_equal(self):
        fixture = ReadFixture(1)
        fixture.items[0]['extra'] = True
        def mutate(call, page, result):
            if call == 3:
                items = json.loads(result[2])
                items[0]['extra'] = 1
                return result[0], result[1], json.dumps(items).encode()
            return result
        fixture.mutate = mutate
        self.fails(fixture, 'READ_COLLECTION_MOVED')

    def test_identity_and_late_second_scan_share_the_original_deadline(self):
        for expire_at in ('identity', 'second'):
            fixture = ReadFixture(1)
            current = [0]
            original = fixture.broker.transport
            def delayed(method, url, headers, body, **kwargs):
                result = original(method, url, headers, body, **kwargs)
                if (expire_at == 'identity' and url.endswith('/user')) or (expire_at == 'second' and len(fixture.calls) == 3):
                    current[0] = 56
                return result
            fixture.broker.transport = delayed
            with self.subTest(expire_at=expire_at), patch('aisoft_host_access.broker.time.monotonic', side_effect=lambda: current[0]):
                self.fails(fixture, 'READ_SCAN_TIME_BOUND')

    def test_cli_failure_has_no_partial_array_or_success_receipt(self):
        fixture = ReadFixture(51)
        fixture.mutate = lambda c, p, r: (500, {}, b'private error') if c == 5 else r
        out, err = io.StringIO(), io.StringIO()
        with patch('aisoft_host_access.cli.HostAccessBroker', return_value=fixture.broker), redirect_stdout(out), redirect_stderr(err):
            code = main(['--access-manifest', str(ACCESS), '--governance-manifest', str(GOVERNANCE),
                         'broker', '--project', 'aisoft-platform', '--operation', 'gitea.pulls.read', '--state', 'all'])
        self.assertEqual(code, 20)
        self.assertEqual(len(fixture.calls), 5)
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(json.loads(err.getvalue())['code'], 'HTTP_ERROR')
        self.assertNotIn('private error', err.getvalue())

    def test_cli_rejects_receipt_tampering_before_stdout(self):
        baseline = ReadFixture(1).read()
        modifications = [None, [], {'count': True}, {'server_total': 2}, {'scan_count': 1},
                         {'limit': 25}, {'terminal_empty_pages': [True, 2]}, {'stdout_sha256': '0' * 64},
                         {'project': 'other'}, {'repository': 'other/repo'}, {'identity': 'admin'},
                         {'state': 'open'}, {'extra': 'unapproved'}, {'observed_at': 0}]
        for change in modifications:
            value = copy.deepcopy(baseline)
            if type(change) is dict:
                value.read_receipt.update(change)
            else:
                value.read_receipt = change
            broker = Mock()
            broker.execute.return_value = value
            out, err = io.StringIO(), io.StringIO()
            with self.subTest(change=change), patch('aisoft_host_access.cli.HostAccessBroker', return_value=broker), redirect_stdout(out), redirect_stderr(err):
                code = main(['--access-manifest', str(ACCESS), '--governance-manifest', str(GOVERNANCE),
                             'broker', '--project', 'aisoft-platform', '--operation', 'gitea.pulls.read', '--state', 'all'])
            self.assertEqual(code, 20)
            self.assertEqual(out.getvalue(), '')
            self.assertEqual(json.loads(err.getvalue())['code'], 'RESPONSE_SCHEMA_INVALID')

    def test_stdout_hash_covers_utf8_bytes_even_on_an_ascii_text_stream(self):
        fixture = ReadFixture(1)
        fixture.items[0]['title'] = '中文验收'
        output = SimpleNamespace(buffer=io.BytesIO(), encoding='ascii', write=Mock(side_effect=AssertionError('text encoding used')))
        err = io.StringIO()
        with patch('aisoft_host_access.cli.HostAccessBroker', return_value=fixture.broker), redirect_stdout(output), redirect_stderr(err):
            code = main(['--access-manifest', str(ACCESS), '--governance-manifest', str(GOVERNANCE),
                         'broker', '--project', 'aisoft-platform', '--operation', 'gitea.pulls.read', '--state', 'all'])
        self.assertEqual(code, 0)
        raw = output.buffer.getvalue()
        self.assertIn('中文验收'.encode(), raw)
        self.assertEqual(json.loads(err.getvalue())['stdout_sha256'], hashlib.sha256(raw).hexdigest())


class BoundedPullTransport(unittest.TestCase):
    def response(self, chunks, headers=()):
        message = Message()
        for key, value in headers:
            message[key] = value
        sock = Mock()
        response = Mock(status=200, headers=message, fp=SimpleNamespace(raw=SimpleNamespace(_sock=sock)))
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read1.side_effect = chunks
        return response, sock

    def read(self, response, limit=1024):
        opener = Mock()
        opener.open.return_value = response
        with patch('aisoft_host_access.broker.build_opener', return_value=opener):
            return _pull_transport('GET', 'http://example.invalid/fixed', {}, None,
                                   response_limit=limit, deadline=time.monotonic() + 55)

    def test_valid_large_page_and_chunked_response_use_incremental_socket_deadlines(self):
        for headers in ([('Content-Length', '131073')], [('Transfer-Encoding', 'chunked')]):
            response, sock = self.response([b'x' * 65536, b'x' * 65536, b'x', b''], headers)
            self.assertEqual(len(self.read(response, 140000)[2]), 131073)
            self.assertEqual(sock.settimeout.call_count, 4)
            self.assertTrue(all(0 < call.args[0] <= 55 for call in sock.settimeout.call_args_list))

    def test_ambiguous_or_compressed_framing_and_truncated_body_fail(self):
        for headers in ([('Content-Length', '2'), ('content-length', '2')],
                        [('Content-Length', '2'), ('Transfer-Encoding', 'chunked')],
                        [('Content-Encoding', 'gzip')], [('Transfer-Encoding', 'gzip')],
                        [('Content-Length', '3')]):
            response, _ = self.response([b'[]', b''], headers)
            with self.subTest(headers=headers), self.assertRaises(BrokerError) as caught:
                self.read(response)
            self.assertEqual(caught.exception.code, 'RESPONSE_SCHEMA_INVALID')

    def test_input_overflow_and_slow_chunk_never_return_partial_body(self):
        response, _ = self.response([b'xxxx', b''])
        with self.assertRaises(BrokerError) as caught:
            self.read(response, 3)
        self.assertEqual(caught.exception.code, 'READ_SCAN_BOUND')
        response, _ = self.response([b'[]', b''])
        with patch('aisoft_host_access.broker.time.monotonic', side_effect=[0, 0, 0, 56]), self.assertRaises(BrokerError) as caught:
            self.read(response)
        self.assertEqual(caught.exception.code, 'READ_SCAN_TIME_BOUND')

    def test_socket_error_detail_is_sanitized(self):
        response, _ = self.response([TimeoutError('private socket detail')])
        with self.assertRaises(BrokerError) as caught:
            self.read(response)
        self.assertEqual(caught.exception.code, 'TRANSPORT_ERROR')
        self.assertNotIn('private', str(caught.exception))


class CompleteNamespaceReads(unittest.TestCase):
    def broker(self, responses, *, fetched='a' * 40):
        contract = load_access_contract(ACCESS, GOVERNANCE)
        self.commands, self.responses = [], iter(responses)
        def runner(argv, *, cwd=None, env=None, timeout=None):
            self.commands.append(list(argv))
            if argv[:3] == ['git', 'ls-remote', '--heads']:
                value = next(self.responses)
                return subprocess.CompletedProcess(argv, 1 if value is None else 0, value or '', '')
            if argv[:2] == ['git', 'rev-parse']:
                return subprocess.CompletedProcess(argv, 0, fetched + '\n', '')
            if argv[:2] == ['git', 'fetch']:
                return subprocess.CompletedProcess(argv, 0, '', '')
            raise AssertionError('unexpected synthetic command')
        broker = HostAccessBroker(contract, credentials=StaticCredentials(), runner=runner, invocation_cwd='/synthetic',
                                  transport=lambda *a, **k: (200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'))
        broker._validated_project_worktree = lambda canonical, checkout: '/synthetic'
        broker._validated_remote = lambda project, checkout: ('origin', 'http://example.invalid/fixed.git')
        return broker

    def read(self, broker):
        return broker.execute('aisoft-platform', 'git.fetch.change', branch='change/333-pat-rotation-acceptance')

    def test_explicit_absence_keeps_nonzero_contract_with_two_empty_observations(self):
        with self.assertRaises(BrokerError) as caught:
            self.read(self.broker(['', '']))
        self.assertEqual(caught.exception.code, 'REMOTE_CHANGE_ABSENT')
        proof = caught.exception.public_receipt
        self.assertEqual(proof['refs'], [])
        self.assertIsNone(proof['requested_head'])
        self.assertEqual(proof['scan_count'], 2)
        self.assertFalse(any(a[:2] == ['git', 'fetch'] for a in self.commands))

    def test_alternate_slug_is_reported_without_claiming_empty_namespace(self):
        other = 'b' * 40 + '\trefs/heads/change/333-other-scope\n'
        with self.assertRaises(BrokerError) as caught:
            self.read(self.broker([other, other]))
        self.assertEqual(caught.exception.public_receipt['refs'], [{'branch': 'change/333-other-scope', 'sha': 'b' * 40}])

    def test_present_exact_branch_fetches_and_compares_head_then_second_scan(self):
        line = 'a' * 40 + '\trefs/heads/change/333-pat-rotation-acceptance\n'
        receipt = self.read(self.broker([line, line]))
        self.assertEqual(receipt['namespace']['requested_head'], 'a' * 40)
        self.assertEqual([a[:2] for a in self.commands], [['git', 'ls-remote'], ['git', 'fetch'], ['git', 'rev-parse'], ['git', 'ls-remote']])

    def test_transport_error_is_not_absence(self):
        with self.assertRaises(BrokerError) as caught:
            self.read(self.broker([None]))
        self.assertEqual(caught.exception.code, 'TRANSPORT_ERROR')
        self.assertFalse(hasattr(caught.exception, 'public_receipt'))

    def test_namespace_movement_and_wrong_fetched_head_fail(self):
        line = 'a' * 40 + '\trefs/heads/change/333-pat-rotation-acceptance\n'
        for responses, fetched in [([line, ''], 'a' * 40), ([line, line], 'b' * 40), (['', line], 'a' * 40)]:
            with self.subTest(responses=responses), self.assertRaises(BrokerError) as caught:
                self.read(self.broker(responses, fetched=fetched))
            self.assertEqual(caught.exception.code, 'READ_COLLECTION_MOVED')

    def test_duplicate_foreign_malformed_and_oversized_refs_fail(self):
        line = 'a' * 40 + '\trefs/heads/change/333-pat-rotation-acceptance\n'
        for value in [line + line, 'a' * 40 + '\trefs/heads/change/334-other-scope\n', 'wrong', 'x' * 65537]:
            with self.subTest(value=value[:60]), self.assertRaises(BrokerError) as caught:
                self.read(self.broker([value]))
            self.assertIn(caught.exception.code, {'RESPONSE_SCHEMA_INVALID', 'READ_SCAN_BOUND'})

    def test_cli_absence_retains_exit20_and_public_receipt_without_success_stdout(self):
        broker = self.broker(['', ''])
        out, err = io.StringIO(), io.StringIO()
        with patch('aisoft_host_access.cli.HostAccessBroker', return_value=broker), redirect_stdout(out), redirect_stderr(err):
            code = main(['--access-manifest', str(ACCESS), '--governance-manifest', str(GOVERNANCE),
                         'broker', '--project', 'aisoft-platform', '--operation', 'git.fetch.change',
                         '--branch', 'change/333-pat-rotation-acceptance'])
        self.assertEqual(code, 20)
        self.assertEqual(out.getvalue(), '')
        value = json.loads(err.getvalue())
        self.assertEqual(value['code'], 'REMOTE_CHANGE_ABSENT')
        self.assertEqual(value['public_receipt']['refs'], [])

    def test_maximum_ref_count_and_legacy_ref_are_bounded_and_sorted(self):
        lines = ['a' * 40 + '\trefs/heads/change/333\n']
        lines += ['b' * 40 + '\trefs/heads/change/333-scope-' + str(i) + '\n' for i in range(99)]
        with self.assertRaises(BrokerError) as caught:
            self.read(self.broker([''.join(lines), ''.join(reversed(lines))]))
        self.assertEqual(caught.exception.code, 'REMOTE_CHANGE_ABSENT')
        self.assertEqual(len(caught.exception.public_receipt['refs']), 100)
        lines.append('c' * 40 + '\trefs/heads/change/333-extra-scope\n')
        with self.assertRaises(BrokerError) as caught:
            self.read(self.broker([''.join(lines)]))
        self.assertEqual(caught.exception.code, 'READ_SCAN_BOUND')
        self.assertFalse(hasattr(caught.exception, 'public_receipt'))

    def test_control_ref_invalid_sha_and_foreign_names_never_prove_absence(self):
        line = 'a' * 40 + '\trefs/heads/change/333-other-scope'
        for raw in (line + '\r\n', line + '\u2028', line + '\x00\n', line + '\n\n',
                    'A' * 40 + '\trefs/heads/change/333-other-scope\n',
                    'a' * 40 + '\trefs/tags/change/333-other-scope\n',
                    'a' * 40 + '\trefs/heads/change/3333-other-scope\n', '\ud800'):
            with self.subTest(raw=repr(raw)), self.assertRaises(BrokerError) as caught:
                self.read(self.broker([raw]))
            self.assertEqual(caught.exception.code, 'RESPONSE_SCHEMA_INVALID')
            self.assertFalse(hasattr(caught.exception, 'public_receipt'))

    def test_second_scan_transport_or_fetch_failure_has_no_absence_receipt(self):
        line = 'a' * 40 + '\trefs/heads/change/333-pat-rotation-acceptance\n'
        for responses in (['', None], [line, None]):
            with self.subTest(responses=responses), self.assertRaises(BrokerError) as caught:
                self.read(self.broker(responses))
            self.assertEqual(caught.exception.code, 'TRANSPORT_ERROR')
            self.assertFalse(hasattr(caught.exception, 'public_receipt'))
        broker = self.broker([line, line])
        original = broker.runner
        def bad_fetch(argv, **kwargs):
            if argv[:2] == ['git', 'fetch']:
                return subprocess.CompletedProcess(argv, 1, '', 'private failure')
            return original(argv, **kwargs)
        broker.runner = bad_fetch
        with self.assertRaises(BrokerError) as caught:
            self.read(broker)
        self.assertEqual(caught.exception.code, 'TRANSPORT_ERROR')
        self.assertFalse(hasattr(caught.exception, 'public_receipt'))

    def test_cli_rejects_tampered_absence_receipt(self):
        broker = self.broker(['', ''])
        with self.assertRaises(BrokerError) as caught:
            self.read(broker)
        baseline = caught.exception.public_receipt
        for changed in ({'scan_count': True}, {'complete': False}, {'requested_head': 'a' * 40},
                        {'issue': 334}, {'repository': 'other/repo'}, {'extra': 1},
                        {'refs': [{'branch': 'change/334-other-scope', 'sha': 'a' * 40}]}):
            error = BrokerError('REMOTE_CHANGE_ABSENT', 'synthetic absence')
            error.public_receipt = copy.deepcopy(baseline)
            error.public_receipt.update(changed)
            broker = Mock()
            broker.execute.side_effect = error
            out, err = io.StringIO(), io.StringIO()
            with self.subTest(changed=changed), patch('aisoft_host_access.cli.HostAccessBroker', return_value=broker), redirect_stdout(out), redirect_stderr(err):
                code = main(['--access-manifest', str(ACCESS), '--governance-manifest', str(GOVERNANCE),
                             'broker', '--project', 'aisoft-platform', '--operation', 'git.fetch.change',
                             '--branch', 'change/333-pat-rotation-acceptance'])
            self.assertEqual(code, 20)
            self.assertEqual(out.getvalue(), '')
            value = json.loads(err.getvalue())
            self.assertEqual(value['code'], 'RESPONSE_SCHEMA_INVALID')
            self.assertNotIn('public_receipt', value)


class BoundedNamespaceProcesses(unittest.TestCase):
    def run_fixture(self, source, timeout=2):
        broker = HostAccessBroker(load_access_contract(ACCESS, GOVERNANCE), credentials=StaticCredentials())
        with tempfile.TemporaryDirectory() as checkout:
            return broker._change_read_command([sys.executable, '-c', source], checkout,
                                               os.environ, time.monotonic() + timeout)

    def test_actual_process_byte_limit_accepts_exact_limit_and_rejects_one_more(self):
        self.assertEqual(len(self.run_fixture('import sys; sys.stdout.write("x" * 65536)')), 65536)
        with self.assertRaises(BrokerError) as caught:
            self.run_fixture('import sys; sys.stdout.write("x" * 65537)')
        self.assertEqual(caught.exception.code, 'READ_SCAN_BOUND')

    def test_actual_process_timeout_kills_child_and_discards_partial_output(self):
        spawned = []
        original = subprocess.Popen
        def capture(*args, **kwargs):
            process = original(*args, **kwargs)
            spawned.append(process)
            return process
        with patch('aisoft_host_access.broker.subprocess.Popen', side_effect=capture), self.assertRaises(BrokerError) as caught:
            self.run_fixture('import sys,time; print("partial", flush=True); time.sleep(5)', timeout=0.1)
        self.assertEqual(caught.exception.code, 'READ_SCAN_TIME_BOUND')
        self.assertEqual(len(spawned), 1)
        self.assertIsNotNone(spawned[0].poll())

    def test_actual_process_failure_and_non_utf8_are_sanitized(self):
        for source, code in [('import sys; print("private", file=sys.stderr); sys.exit(1)', 'TRANSPORT_ERROR'),
                             ('import os; os.write(1, b"\\xff")', 'RESPONSE_SCHEMA_INVALID')]:
            with self.subTest(source=source), self.assertRaises(BrokerError) as caught:
                self.run_fixture(source)
            self.assertEqual(caught.exception.code, code)
            self.assertNotIn('private', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
