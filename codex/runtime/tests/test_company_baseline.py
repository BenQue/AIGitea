"""Public collector/receipt seam: no company access or state mutation in tests."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import aisoft_company_baseline as b

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "codex/runtime/aisoft_company_baseline.py"
NOW = datetime(2026, 9, 6, 14, 0, tzinfo=timezone.utc)


def binding():
    return {"environment": "company-scm-ci", "host_role": "scm-ci", "host_sha256": b.host_digest(),
            "collector_sha256": b.script_digest(), "source_sha": "1" * 40,
            "evidence_id": "12345678-1234-4567-8123-123456789012"}


def values():
    result = {k: {"enabled": "enabled", "active": "active"} for k in b.UNITS}
    result.update({"gitea_binary": "1.26.4", "postgresql_binary": "18.4",
                   "gitea_listener": "exposed", "postgresql_listener": "loopback", "gitea_health": "pass",
                   "gitea_api_version": "1.26.4", "postgresql_server_version": "18.4",
                   "ufw": {"active": "yes", "default_deny_incoming": "yes", "rule_count": 3},
                   "network": "reachable", "authentication": "available", "acl": "read-allowed",
                   "repository": {"exists": "yes", "identity_sha256": "2" * 64, "head_sha": "3" * 40},
                   "protection": {"direct_push_denied": "yes", "force_push_denied": "yes",
                                  "human_only_merge": "yes", "required_ci_count": 1},
                   "runner_registration": "registered",
                   "sync": {"timer": {"enabled": "enabled", "active": "active"},
                            "source_sha": "3" * 40, "destination_sha": "3" * 40},
                   "backup": {"available": "yes", "off_host": "yes", "set_sha256": "4" * 64},
                   "isolated_restore": {"verified": "yes", "isolated": "yes", "set_sha256": "4" * 64},
                   "ufw_review": "approved-networks-only", "storage_ownership": "expected-service-owners",
                   "service_binding": "fixed-binaries-and-data"})
    for key in b.STORES:
        result[key] = {"kind": "directory", "uid": 123, "gid": 123, "mode": 0o750, "free_bytes": 100000}
    return result


def inventory():
    return {"contract_version": b.CONTRACT, "collector_version": b.VERSION, **binding(),
            "collected_at": b.timestamp(NOW), "historical": {},
            "current": {k: b.observation(k, v, basis="operator-reviewed" if k in b.MANUAL else "host-probe",
                                         evidence="5" * 64 if k in b.MANUAL else None) for k, v in values().items()}}


class FakeHost:
    def __init__(self):
        self.commands, self.endpoints, self.paths = [], [], []

    def invoke(self, argv):
        self.commands.append(argv)
        if argv[0] == "/usr/bin/systemctl":
            return 0, "enabled" if argv[1] == "is-enabled" else "active"
        if argv[0].endswith("/gitea"):
            return 0, "Gitea version 1.26.4 built with go1.26"
        if argv[0].endswith("/postgres"):
            return 0, "postgres (PostgreSQL) 18.4"
        if argv[0] == "/usr/bin/ss":
            port = argv[-1].split(":")[-1]
            return 0, f"LISTEN 0 4096 127.0.0.1:{port} 0.0.0.0:*"
        if argv == ["/usr/sbin/ufw", "status", "verbose"]:
            return 0, "Status: active\nDefault: deny (incoming), allow (outgoing), disabled (routed)\n8888 ALLOW IN 10.0.0.0/8"
        raise AssertionError(argv)

    def http(self, path):
        self.endpoints.append(path)
        value = {"version": "1.26.4"} if path.endswith("version") else {
            "status": "pass", "description": "untrusted description must not escape", "checks": {
                "database:ping": [{"status": "pass"}], "cache:ping": [{"status": "pass"}]}}
        return 200, json.dumps(value).encode()

    def storage(self, path):
        self.paths.append(path)
        return values()["gitea_storage"]

    def collect(self):
        with patch.object(b.sys, "platform", "linux"):
            return b.collect(binding(), invoke=self.invoke, http=self.http, storage=self.storage, now=NOW)


class BaselineTests(unittest.TestCase):
    def test_all_current_pass_adopts_without_grant(self):
        result = b.seal(inventory(), NOW)
        self.assertEqual(b.verify(result, binding(), NOW)["decision"], "adopt")
        self.assertIs(result["receipt"]["mutation_authorized"], False)

    def test_each_missing_check_blocks_even_historical_pass(self):
        for key in b.VALUES:
            with self.subTest(key=key):
                value = inventory()
                value["historical"][key] = b.observation(key, values()[key], basis="historical", evidence="a"*64)
                value["current"][key] = b.observation(key)
                self.assertEqual(b.assess(value, NOW)["decision"], "BLOCKED")

    def test_known_noncritical_gap_needs_remediation(self):
        value = inventory()
        value["current"]["runner_registration"] = b.observation("runner_registration", "absent", basis="operator-reviewed", evidence="a"*64)
        self.assertEqual(b.assess(value, NOW)["decision"], "adopt-with-remediation")

    def test_confirmed_absent_repo_and_sync_allow_remediation_without_fake_sha(self):
        value = inventory()
        value["current"]["repository"] = b.observation("repository", {
            "exists": "no", "identity_sha256": "a"*64, "head_sha": None}, basis="operator-reviewed", evidence="a"*64)
        value["current"]["sync"] = b.observation("sync", {
            "timer": {"enabled": "not-found", "active": "not-found"}, "source_sha": None,
            "destination_sha": None}, basis="operator-reviewed", evidence="a"*64)
        self.assertEqual(b.assess(value, NOW)["decision"], "adopt-with-remediation")
        with self.assertRaises(b.Invalid):
            b.observation("repository", {"exists": "yes", "identity_sha256": "a"*64, "head_sha": None})

    def test_unsafe_postgres_listener_blocks(self):
        value = inventory()
        value["current"]["postgresql_listener"] = b.observation("postgresql_listener", "exposed")
        self.assertEqual(b.assess(value, NOW)["decision"], "BLOCKED")

    def test_different_backup_restore_sets_block(self):
        value = inventory()
        value["current"]["isolated_restore"]["value"]["set_sha256"] = "b"*64
        self.assertEqual(b.assess(value, NOW)["decision"], "BLOCKED")

    def test_unknown_fields_rejected_at_every_object_level(self):
        original = b.seal(inventory(), NOW)

        def paths(v, prefix=()):
            if isinstance(v, dict):
                yield prefix
                for k, x in v.items():
                    yield from paths(x, (*prefix, k))
        for path in paths(original):
            with self.subTest(path=path):
                changed = copy.deepcopy(original)
                target = changed
                for key in path:
                    target = target[key]
                target["password"] = "sensitive sentinel"
                with self.assertRaises(b.Invalid):
                    b.verify(changed, binding(), NOW)

    def test_boolean_cannot_replace_integer(self):
        value = inventory()
        value["current"]["ufw"]["value"]["rule_count"] = True
        with self.assertRaises(b.Invalid):
            b.seal(value, NOW)

    def test_forged_pass_and_historical_promotion_rejected(self):
        for field, replacement in (("status", "PASS"), ("basis", "historical")):
            value = inventory()
            value["current"]["network"] = b.observation("network", "unreachable", basis="operator-reviewed", evidence="a"*64)
            value["current"]["network"][field] = replacement
            with self.assertRaises(b.Invalid):
                b.seal(value, NOW)

    def test_checksum_and_receipt_tampering_rejected(self):
        for field in ("checksum", "receipt"):
            value = b.seal(inventory(), NOW)
            if field == "checksum":
                value["inventory_sha256"] = "0"*64
            else:
                value["receipt"]["mutation_authorized"] = True
            with self.assertRaises(b.Invalid):
                b.verify(value, binding(), NOW)

    def test_stale_future_and_impossible_dates_rejected(self):
        for date in ("2026-09-05T13:59:59Z", "2026-09-06T14:00:01Z", "2026-99-06T14:00:00Z"):
            value = inventory()
            value["collected_at"] = date
            with self.assertRaises(b.Invalid):
                b.seal(value, NOW)

    def test_binding_mismatch_all_dimensions(self):
        envelope = b.seal(inventory(), NOW)
        for key in binding():
            changed = binding()
            changed[key] = "different"
            with self.assertRaises(b.Invalid):
                b.verify(envelope, changed, NOW)

    def test_duplicate_json_keys_nan_and_limit_rejected(self):
        for raw in (b'{"status":1,"status":2}', b'{"x": NaN}', b" "*(b.LIMIT+1), b'"\xff"'):
            with self.assertRaises(b.Invalid):
                b.decode(raw)

    def test_collection_is_repeatable_and_does_not_write(self):
        fake = FakeHost()
        with patch("builtins.open", side_effect=AssertionError("write or read outside allowed seam")):
            first, second = fake.collect(), fake.collect()
        self.assertEqual(first, second)
        self.assertEqual(first["receipt"]["decision"], "BLOCKED")
        for key in b.MANUAL:
            self.assertEqual(first["inventory"]["current"][key]["status"], "NOT RUN")
        self.assertNotIn("untrusted", json.dumps(first))

    def test_exact_probe_allowlist(self):
        fake = FakeHost()
        fake.collect()
        commands = [["/usr/bin/systemctl", action, unit] for unit in b.UNITS.values() for action in ("is-enabled", "is-active")]
        commands += [[path, "--version"] for path, _ in b.BINARIES.values()]
        commands += [["/usr/bin/ss", "-H", "-ltn", f"sport = :{p}"] for p in (8888, 55432)]
        commands += [["/usr/sbin/ufw", "status", "verbose"]]
        self.assertEqual(fake.commands, commands)
        self.assertEqual(fake.endpoints, ["/api/healthz", "/api/v1/version"])
        self.assertEqual(fake.paths, list(b.STORES.values()))

    def test_wrong_host_or_collector_rejects_before_any_probe(self):
        for key in ("host_sha256", "collector_sha256"):
            changed = binding()
            changed[key] = "0"*64
            fake = FakeHost()
            with self.assertRaises(b.Invalid):
                b.collect(changed, invoke=fake.invoke, now=NOW)
            self.assertEqual(fake.commands, [])

    def test_missing_commands_and_permission_denied_are_sanitized(self):
        fake = FakeHost()
        fake.invoke = lambda argv: (_ for _ in ()).throw(PermissionError("sensitive sentinel"))
        result = fake.collect()
        self.assertEqual(result["receipt"]["decision"], "BLOCKED")
        self.assertNotIn("sentinel", json.dumps(result))

    def test_install_page_empty_health_checks_fails(self):
        fake = FakeHost()
        fake.http = lambda path: (200, b'{"status":"pass","checks":{}}')
        result = fake.collect()
        self.assertEqual(result["inventory"]["current"]["gitea_health"]["status"], "GAP")

    def test_health_missing_database_or_cache_is_not_pass(self):
        for checks in ({"fake": [{"status": "pass"}]}, {"cache:ping": [{"status": "pass"}]}):
            fake = FakeHost()
            fake.http = lambda path: (200, json.dumps({"status": "pass", "checks": checks}).encode())
            self.assertEqual(fake.collect()["inventory"]["current"]["gitea_health"]["status"], "GAP")

    def test_redirects_oversized_or_invalid_http_never_pass(self):
        for response in ((302, b"redirect"), (200, b"a"*(b.LIMIT+1)), (200, b'{"version":"token sentinel"}')):
            fake = FakeHost()
            fake.http = lambda path: response
            result = fake.collect()
            self.assertEqual(result["inventory"]["current"]["gitea_api_version"]["status"], "BLOCKED")
            self.assertNotIn("sentinel", json.dumps(result))

    def test_ambiguous_listener_is_not_accepted(self):
        fake = FakeHost()
        original = fake.invoke
        fake.invoke = lambda argv: (0, "LISTEN unknown") if argv[0].endswith("/ss") else original(argv)
        self.assertEqual(fake.collect()["inventory"]["current"]["gitea_listener"]["status"], "BLOCKED")

    def test_storage_symlink_and_unsafe_modes_fail(self):
        for mode in (0, 0o777, 0o1770):
            self.assertFalse(b.good("gitea_storage", {**values()["gitea_storage"], "mode": mode}))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/"real").mkdir()
            (root/"alias").symlink_to(root/"real")
            self.assertEqual(b.metadata(str(root/"alias"))["kind"], "symlink")

    def test_operator_evidence_can_complete_readback(self):
        fake = FakeHost()
        envelope = fake.collect()
        record = {**binding(), "observed_at": b.timestamp(NOW), "evidence_sha256": "a"*64,
                  "facts": {k: v for k, v in values().items() if k in b.MANUAL}}
        result = b.supplement(envelope, record, binding(), NOW)
        self.assertEqual(result["receipt"]["decision"], "adopt")

    def test_operator_cannot_override_host_probe_or_use_old_record(self):
        envelope = FakeHost().collect()
        record = {**binding(), "observed_at": b.timestamp(NOW), "evidence_sha256": "a"*64, "facts": {"gitea_binary": "1.26.4"}}
        with self.assertRaises(b.Invalid):
            b.supplement(envelope, record, binding(), NOW)
        record["facts"] = {}
        record["observed_at"] = b.timestamp(NOW-timedelta(seconds=1))
        with self.assertRaises(b.Invalid):
            b.supplement(envelope, record, binding(), NOW)

    def test_child_output_is_bounded_and_stderr_discarded(self):
        self.assertEqual(b.run([sys.executable, "-c", "import sys; print('ok'); print('sentinel',file=sys.stderr)"]), (0, "ok"))
        with self.assertRaises(b.Invalid):
            b.run([sys.executable, "-c", "print('x'*70000)"])

    def test_cli_rejection_never_echoes_arguments_or_input(self):
        result = subprocess.run([sys.executable, "-I", "-S", "-B", str(SCRIPT), "collect", "--password", "sensitive-sentinel"], capture_output=True)
        self.assertEqual(result.returncode, 20)
        self.assertNotIn(b"sentinel", result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)["code"], "ARGUMENT_INVALID")

    def test_cli_verify_end_to_end(self):
        value = inventory()
        value["collected_at"] = b.timestamp(b.utcnow())
        envelope = b.seal(value)
        args = [sys.executable, "-I", "-S", "-B", str(SCRIPT), "verify"]
        for k, v in binding().items():
            args += ["--"+k.replace("_", "-"), v]
        result = subprocess.run(args, input=b.canonical(envelope), capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["decision"], "adopt")

    def test_published_schema_matches_program(self):
        expected = (ROOT/"company-delivery/baseline/inventory-v1.schema.json").read_bytes()
        actual = subprocess.run([sys.executable, "-I", "-S", "-B", str(SCRIPT), "schema"], capture_output=True, check=True)
        self.assertEqual(expected, actual.stdout)
        self.assertEqual(json.loads(actual.stdout), b.schema())

    def test_closed_stdout_has_no_traceback(self):
        process = subprocess.Popen([sys.executable, "-I", "-S", "-B", str(SCRIPT), "schema"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.stdout.close()
        self.assertEqual(process.wait(timeout=5), 20)
        self.assertEqual(process.stderr.read(), b"")
        process.stderr.close()

    def test_collection_cli_requires_isolated_no_site_no_bytecode(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "identity"], capture_output=True)
        self.assertEqual(result.returncode, 20)
        self.assertEqual(json.loads(result.stdout)["code"], "UNSAFE_INTERPRETER")

    def test_interpreter_ignores_injected_pythonpath(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "sitecustomize.py").write_text("raise Exception('sensitive-sentinel')")
            result = subprocess.run([sys.executable, "-I", "-S", "-B", str(SCRIPT), "identity"],
                                    env={"PYTHONPATH": tmp, "PYTHONINSPECT": "1"}, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(b"sentinel", result.stdout+result.stderr)

    def test_runbook_command_blocks_at_most_fifty_lines(self):
        text = (ROOT/"company-delivery/baseline/README.md").read_text()
        blocks = text.split("```")[1::2]
        self.assertGreaterEqual(len(blocks), 3)
        self.assertTrue(all(len(block.splitlines())-1 <= 50 for block in blocks))


if __name__ == "__main__":
    unittest.main()
