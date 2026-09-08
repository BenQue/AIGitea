"""Profile-bound collector tests: all host behavior is injected and read-only."""

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import aisoft_company_baseline_v2 as b


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "codex/runtime/aisoft_company_baseline_v2.py"
V1_SCRIPT = ROOT / "codex/runtime/aisoft_company_baseline.py"
NOW = datetime(2026, 9, 7, 8, 0, tzinfo=timezone.utc)


def profile():
    return {
        "contract_version": b.PROFILE_CONTRACT,
        "gitea": {
            "unit": "aisoft-gitea.service",
            "binary": "/opt/aisoft/gitea/1.26.4/gitea",
            "expected_version": "1.26.4",
            "listen_ip": "10.23.45.67",
            "port": 8888,
            "storage": "/var/lib/aisoft-gitea",
        },
        "postgresql": {
            "major": 18,
            "cluster": "giteaunit",
            "unit": "postgresql@18-giteaunit.service",
            "binary": "/usr/lib/postgresql/18/bin/postgres",
            "expected_version": "18.7",
            "listen_ip": "127.0.0.1",
            "port": 55432,
            "storage": "/var/lib/postgresql/18/giteaunit",
        },
    }


def binding(selected=None):
    selected = selected or profile()
    return {
        "environment": "company-scm-ci",
        "host_role": "scm-ci",
        "host_sha256": b.host_digest(),
        "collector_sha256": b.script_digest(),
        "profile_sha256": b.profile_digest(selected),
        "source_sha": "1" * 40,
        "evidence_id": "12345678-1234-4567-8123-123456789012",
    }


def values():
    result = {
        "gitea_service": {"enabled": "enabled", "active": "active"},
        "postgresql_service": {"enabled": "enabled", "active": "active"},
        "runner_service": {"enabled": "enabled", "active": "active"},
        "gitea_binary": "1.26.4",
        "postgresql_binary": "18.7",
        "gitea_listener": "exposed",
        "postgresql_listener": "loopback",
        "gitea_health": "pass",
        "gitea_api_version": "1.26.4",
        "postgresql_server_version": "18.7",
        "ufw": {"active": "yes", "default_deny_incoming": "yes", "rule_count": 17},
        "network": "reachable",
        "authentication": "available",
        "acl": "read-allowed",
        "repository": {"exists": "yes", "identity_sha256": "2" * 64, "head_sha": "3" * 40},
        "protection": {"direct_push_denied": "yes", "force_push_denied": "yes",
                       "human_only_merge": "yes", "required_ci_count": 1},
        "runner_registration": "registered",
        "sync": {"timer": {"enabled": "enabled", "active": "active"},
                 "source_sha": "3" * 40, "destination_sha": "3" * 40},
        "backup": {"available": "yes", "off_host": "yes", "set_sha256": "4" * 64},
        "isolated_restore": {"verified": "yes", "isolated": "yes", "set_sha256": "4" * 64},
        "ufw_review": "approved-networks-only",
        "storage_ownership": "expected-service-owners",
        "service_binding": "fixed-binaries-and-data",
        "gitea_storage": {"kind": "directory", "uid": 123, "gid": 123,
                           "mode": 0o750, "free_bytes": 100000},
        "postgresql_storage": {"kind": "directory", "uid": 124, "gid": 124,
                               "mode": 0o700, "free_bytes": 100000},
    }
    return result


def inventory(selected=None):
    selected = selected or profile()
    return {
        "contract_version": b.CONTRACT,
        "collector_version": b.VERSION,
        **binding(selected),
        "profile": selected,
        "collected_at": b.timestamp(NOW),
        "historical": {},
        "current": {
            key: b.observation(
                key, selected, value,
                basis="operator-reviewed" if key in b.MANUAL else "host-probe",
                evidence="5" * 64 if key in b.MANUAL else None,
            )
            for key, value in values().items()
        },
    }


class FakeHost:
    def __init__(self, selected=None):
        self.profile = selected or profile()
        self.commands = []
        self.endpoints = []
        self.paths = []

    def invoke(self, argv):
        self.commands.append(argv)
        if argv[0] == "/usr/bin/systemctl":
            return 0, "enabled" if argv[1] == "is-enabled" else "active"
        if argv[0].endswith("/gitea"):
            return 0, "Gitea version 1.26.4 built with go1.26"
        if argv[0].endswith("/postgres"):
            return 0, "postgres (PostgreSQL) 18.7"
        if argv[0] == "/usr/bin/ss":
            port = int(argv[-1].rsplit(":", 1)[1])
            component = (self.profile["gitea"] if port == self.profile["gitea"]["port"]
                         else self.profile["postgresql"])
            return 0, f"LISTEN 0 4096 {component['listen_ip']}:{port} 0.0.0.0:*"
        if argv == ["/usr/sbin/ufw", "status", "verbose"]:
            return 0, ("Status: active\n"
                       "Default: deny (incoming), allow (outgoing), deny (routed)\n"
                       "8888 ALLOW IN 10.0.0.0/8")
        raise AssertionError(argv)

    def http(self, host, port, path):
        self.endpoints.append((host, port, path))
        value = {"version": "1.26.4"} if path.endswith("version") else {
            "status": "pass",
            "description": "untrusted description must not escape",
            "checks": {"database:ping": [{"status": "pass"}],
                       "cache:ping": [{"status": "pass"}]},
        }
        return 200, json.dumps(value).encode()

    def storage(self, path):
        self.paths.append(path)
        return values()["gitea_storage"] if path == self.profile["gitea"]["storage"] else values()["postgresql_storage"]

    def collect(self):
        with patch.object(b.sys, "platform", "linux"):
            return b.collect(binding(self.profile), profile=self.profile, invoke=self.invoke,
                             http=self.http, storage=self.storage, now=NOW)


class BaselineV2Tests(unittest.TestCase):
    def test_both_collector_versions_verify_with_original_pins(self):
        for version in ("2.0.0", "2.0.1"):
            value = inventory()
            value["collector_version"] = version
            value["collector_sha256"] = "a" * 64
            pins = binding()
            pins["collector_sha256"] = "a" * 64
            self.assertEqual(b.verify(b.seal(value, NOW), pins, NOW)["validation"], "PASS")
        self.assertEqual(FakeHost().collect()["inventory"]["collector_version"], "2.0.1")

    def test_strict_gitea_prefix_and_version(self):
        for output, status in (("gitea version 1.26.4 built with go1.26", "PASS"),
                               ("Gitea version 1.26.4", "PASS"),
                               ("GITEA version 1.26.4", "BLOCKED"),
                               ("gitea version 1.26.4\nSECRET_SENTINEL", "BLOCKED"),
                               ("gitea version 1.26.4.1", "BLOCKED"),
                               ("gitea version 1000.26.4", "BLOCKED"),
                               ("gitea version x.26.4", "BLOCKED")):
            fake = FakeHost()
            original = fake.invoke
            fake.invoke = lambda argv: (0, output) if argv[0].endswith("/gitea") else original(argv)
            with self.subTest(output=output):
                self.assertEqual(fake.collect()["inventory"]["current"]["gitea_binary"]["status"], status)

    def test_runtime_enablement_is_gap_and_bad_status_blocks(self):
        for rc, value, status in ((0, "enabled-runtime", "GAP"), (0, "unknown", "BLOCKED"),
                                  (3, "enabled-runtime", "BLOCKED"), (9, "enabled", "BLOCKED")):
            fake = FakeHost()
            original = fake.invoke
            fake.invoke = lambda argv: (rc, value) if argv[1] == "is-enabled" else original(argv)
            current = fake.collect()["inventory"]["current"]["postgresql_service"]
            self.assertEqual(current["status"], status)
            if status == "GAP":
                self.assertEqual(current["value"]["enabled"], "enabled-runtime")

    def test_v1_collector_is_byte_compatible(self):
        self.assertEqual(hashlib.sha256(V1_SCRIPT.read_bytes()).hexdigest(),
                         "3561d2f1fc607cdee1ba4688489645db1b2142cf57cc4d99433c35b1f33a7a88")

    def test_profile_is_canonical_closed_and_digest_bound(self):
        selected = profile()
        self.assertEqual(b.decode(b.profile_bytes(selected)), selected)
        self.assertEqual(len(b.profile_digest(selected)), 64)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, b.PROFILE_FILENAME)
            path.write_bytes(b.profile_bytes(selected))
            path.chmod(0o600)
            self.assertEqual(b.load_profile(path), selected)
            path.write_text(json.dumps(selected, indent=2) + "\n")
            with self.assertRaisesRegex(b.Invalid, "PROFILE_NOT_CANONICAL"):
                b.load_profile(path)

    def test_unsafe_profile_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "real.json"
            real.write_bytes(b.profile_bytes(profile()))
            real.chmod(0o600)
            alias = root / b.PROFILE_FILENAME
            alias.symlink_to(real)
            with self.assertRaises(b.Invalid):
                b.load_profile(alias)
            alias.unlink()
            alias.write_bytes(b.profile_bytes(profile()))
            alias.chmod(0o666)
            with self.assertRaisesRegex(b.Invalid, "PROFILE_FILE_UNSAFE"):
                b.load_profile(alias)

    def test_unknown_profile_fields_are_rejected(self):
        for path in ((), ("gitea",), ("postgresql",)):
            changed = copy.deepcopy(profile())
            target = changed
            for key in path:
                target = target[key]
            target["password"] = "sensitive sentinel"
            with self.subTest(path=path), self.assertRaises(b.Invalid):
                b.validate_profile(changed)

    def test_only_private_or_loopback_gitea_ipv4_is_allowed(self):
        for address in ("8.8.8.8", "169.254.1.1", "0.0.0.0", "224.0.0.1", "example.invalid", "http://10.0.0.1"):
            changed = profile()
            changed["gitea"]["listen_ip"] = address
            with self.subTest(address=address), self.assertRaises(b.Invalid):
                b.validate_profile(changed)
        for address in ("10.1.2.3", "172.16.0.1", "192.168.5.9", "127.0.0.1"):
            changed = profile()
            changed["gitea"]["listen_ip"] = address
            self.assertEqual(b.validate_profile(changed), changed)

    def test_postgresql_identity_relations_are_strict(self):
        for key, value in (("unit", "postgresql@18-other.service"),
                           ("storage", "/var/lib/postgresql/18/other"),
                           ("expected_version", "17.9"),
                           ("cluster", "bad-name")):
            changed = profile()
            changed["postgresql"][key] = value
            with self.subTest(key=key), self.assertRaises(b.Invalid):
                b.validate_profile(changed)

    def test_all_current_pass_adopts_without_mutation_grant(self):
        result = b.seal(inventory(), NOW)
        self.assertEqual(b.verify(result, binding(), NOW)["decision"], "adopt")
        self.assertIs(result["receipt"]["mutation_authorized"], False)

    def test_profile_tamper_or_digest_mismatch_is_rejected(self):
        value = inventory()
        value["profile"]["gitea"]["port"] = 9999
        with self.assertRaisesRegex(b.Invalid, "PROFILE_DIGEST_MISMATCH"):
            b.seal(value, NOW)
        envelope = b.seal(inventory(), NOW)
        changed = binding()
        changed["profile_sha256"] = "0" * 64
        with self.assertRaises(b.Invalid):
            b.verify(envelope, changed, NOW)

    def test_each_missing_current_fact_blocks_even_with_history(self):
        selected = profile()
        for key in b.VALUES:
            value = inventory(selected)
            value["historical"][key] = b.observation(
                key, selected, values()[key], basis="historical", evidence="a" * 64)
            value["current"][key] = b.observation(key, selected)
            with self.subTest(key=key):
                self.assertEqual(b.assess(value, NOW)["decision"], "BLOCKED")

    def test_known_noncritical_gap_can_be_remediation(self):
        value = inventory()
        value["current"]["runner_registration"] = b.observation(
            "runner_registration", profile(), "absent", basis="operator-reviewed", evidence="a" * 64)
        self.assertEqual(b.assess(value, NOW)["decision"], "adopt-with-remediation")

    def test_version_profile_controls_binary_api_and_server(self):
        selected = profile()
        for key in ("postgresql_binary", "postgresql_server_version"):
            self.assertTrue(b.good(key, "18.7", selected))
            self.assertFalse(b.good(key, "18.4", selected))
        self.assertTrue(b.good("gitea_api_version", "1.26.4", selected))

    def test_external_gitea_and_hyphen_free_cluster_fixture_passes(self):
        fake = FakeHost()
        result = fake.collect()
        current = result["inventory"]["current"]
        self.assertEqual(current["gitea_listener"]["value"], "exposed")
        self.assertEqual(current["gitea_health"]["status"], "PASS")
        self.assertEqual(current["postgresql_listener"]["value"], "loopback")
        self.assertEqual(current["postgresql_binary"]["value"], "18.7")
        self.assertEqual(current["postgresql_service"]["status"], "PASS")

    def test_exact_probe_allowlist_is_profile_derived(self):
        fake = FakeHost()
        fake.collect()
        selected = fake.profile
        commands = []
        for unit in (selected["gitea"]["unit"], selected["postgresql"]["unit"], "act_runner.service"):
            commands.extend([["/usr/bin/systemctl", "is-enabled", unit],
                             ["/usr/bin/systemctl", "is-active", unit]])
        commands.extend([[selected["gitea"]["binary"], "--version"],
                         [selected["postgresql"]["binary"], "--version"],
                         ["/usr/bin/ss", "-H", "-ltn", "sport = :8888"],
                         ["/usr/bin/ss", "-H", "-ltn", "sport = :55432"],
                         ["/usr/sbin/ufw", "status", "verbose"]])
        self.assertEqual(fake.commands, commands)
        self.assertEqual(fake.endpoints, [
            ("10.23.45.67", 8888, "/api/healthz"),
            ("10.23.45.67", 8888, "/api/v1/version"),
        ])
        self.assertEqual(fake.paths, ["/var/lib/aisoft-gitea", "/var/lib/postgresql/18/giteaunit"])

    def test_listener_requires_exact_address_without_wildcard(self):
        for output in ("", "LISTEN 0 4096 0.0.0.0:8888 0.0.0.0:*",
                       "LISTEN 0 4096 10.23.45.68:8888 0.0.0.0:*"):
            fake = FakeHost()
            original = fake.invoke

            def invoke(argv, output=output):
                if argv[0] == "/usr/bin/ss" and argv[-1].endswith(":8888"):
                    return 0, output
                return original(argv)

            fake.invoke = invoke
            result = fake.collect()["inventory"]["current"]["gitea_listener"]
            with self.subTest(output=output):
                self.assertEqual(result["status"], "GAP")
                self.assertIn(result["value"], {"absent", "mismatch"})

    def test_wrong_binding_rejects_before_host_probe(self):
        for key in ("host_sha256", "collector_sha256", "profile_sha256"):
            changed = binding()
            changed[key] = "0" * 64
            fake = FakeHost()
            with patch.object(b.sys, "platform", "linux"), self.assertRaises(b.Invalid):
                b.collect(changed, profile=fake.profile, invoke=fake.invoke, now=NOW)
            self.assertEqual(fake.commands, [])

    def test_probe_failures_are_sanitized(self):
        fake = FakeHost()
        fake.invoke = lambda argv: (_ for _ in ()).throw(PermissionError("sensitive sentinel"))
        result = fake.collect()
        self.assertEqual(result["receipt"]["decision"], "BLOCKED")
        self.assertNotIn("sentinel", json.dumps(result))

    def test_health_requires_exact_database_and_cache_checks(self):
        for checks in ({}, {"fake": [{"status": "pass"}]}, {"cache:ping": [{"status": "pass"}]}):
            fake = FakeHost()
            fake.http = lambda host, port, path, checks=checks: (
                200, json.dumps({"status": "pass", "checks": checks}).encode())
            current = fake.collect()["inventory"]["current"]["gitea_health"]
            self.assertEqual(current["status"], "GAP")

    def test_operator_evidence_completes_profile_bound_envelope(self):
        fake = FakeHost()
        envelope = fake.collect()
        record = {**binding(fake.profile), "observed_at": b.timestamp(NOW),
                  "evidence_sha256": "a" * 64,
                  "facts": {key: value for key, value in values().items() if key in b.MANUAL}}
        result = b.supplement(envelope, record, binding(fake.profile), NOW)
        self.assertEqual(result["receipt"]["decision"], "adopt")

    def test_operator_cannot_override_host_probe_or_use_stale_record(self):
        envelope = FakeHost().collect()
        record = {**binding(), "observed_at": b.timestamp(NOW), "evidence_sha256": "a" * 64,
                  "facts": {"gitea_binary": "1.26.4"}}
        with self.assertRaises(b.Invalid):
            b.supplement(envelope, record, binding(), NOW)
        record["facts"] = {}
        record["observed_at"] = b.timestamp(NOW - timedelta(seconds=1))
        with self.assertRaises(b.Invalid):
            b.supplement(envelope, record, binding(), NOW)

    def test_cli_verify_end_to_end(self):
        value = inventory()
        value["collected_at"] = b.timestamp(b.utcnow())
        envelope = b.seal(value)
        args = [sys.executable, "-I", "-S", "-B", str(SCRIPT), "verify"]
        for key, item in binding().items():
            args.extend(["--" + key.replace("_", "-"), item])
        result = subprocess.run(args, input=b.canonical(envelope), capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["decision"], "adopt")

    def test_identity_reads_only_fixed_canonical_sibling_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copied = root / SCRIPT.name
            shutil.copyfile(SCRIPT, copied)
            profile_path = root / b.PROFILE_FILENAME
            profile_path.write_bytes(b.profile_bytes(profile()))
            profile_path.chmod(0o600)
            result = subprocess.run([sys.executable, "-I", "-S", "-B", str(copied), "identity"],
                                    capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            identity = json.loads(result.stdout)
            self.assertEqual(identity["collector_sha256"], hashlib.sha256(copied.read_bytes()).hexdigest())
            self.assertEqual(identity["profile_sha256"], b.profile_digest(profile()))

    def test_cli_rejection_never_echoes_arguments(self):
        result = subprocess.run([sys.executable, "-I", "-S", "-B", str(SCRIPT), "collect",
                                 "--password", "sensitive-sentinel"], capture_output=True)
        self.assertEqual(result.returncode, 20)
        self.assertNotIn(b"sentinel", result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["code"], "ARGUMENT_INVALID")

    def test_collect_requires_isolated_no_site_no_bytecode(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "identity"], capture_output=True)
        self.assertEqual(result.returncode, 20)
        self.assertEqual(json.loads(result.stdout)["code"], "UNSAFE_INTERPRETER")

    def test_published_schemas_match_cli(self):
        for command, relative in (("profile-schema", "company-delivery/baseline/profile-v1.schema.json"),
                                  ("schema", "company-delivery/baseline/inventory-v2.schema.json")):
            expected = (ROOT / relative).read_bytes()
            actual = subprocess.run([sys.executable, "-I", "-S", "-B", str(SCRIPT), command],
                                    capture_output=True, check=True).stdout
            self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
