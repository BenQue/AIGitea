from pathlib import Path
from copy import deepcopy
import json
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"
CLI = ARCH / "bin/aisoft-architecture"


class ArchitectureCliTests(unittest.TestCase):
    def common(self, project: Path) -> list[str]:
        return [
            "--catalog", str(ARCH / "catalog.json"),
            "--profiles-dir", str(ARCH / "profiles"),
            "--schema-dir", str(ARCH / "schemas"),
            "--project", str(project),
            "--today", "2026-09-05",
        ]

    def run_cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment.update({"http_proxy": "http://127.0.0.1:1", "https_proxy": "http://127.0.0.1:1", "NO_PROXY": ""})
        return subprocess.run([str(CLI), *args], text=True, capture_output=True, check=False, env=environment)

    def test_validate_and_explain_are_machine_readable(self) -> None:
        result = self.run_cli(["validate", *self.common(ARCH / "fixtures/valid/windows-project.json")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])

        result = self.run_cli(["explain", "--catalog", str(ARCH / "catalog.json"), "--component", "runtime.node.24"])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "preferred")
        self.assertNotIn("environment", payload)

    def test_lock_twice_is_byte_identical_and_validates(self) -> None:
        fixtures = ("linux-project.json", "linux-systemd-project.json")
        for fixture in fixtures:
            with self.subTest(fixture=fixture), tempfile.TemporaryDirectory() as directory:
                first = Path(directory) / "first.json"
                second = Path(directory) / "second.json"
                project = ARCH / "fixtures/valid" / fixture
                for output in (first, second):
                    result = self.run_cli(["lock", *self.common(project), "--output", str(output)])
                    self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(first.read_bytes(), second.read_bytes())
                payload = json.loads(first.read_text())
                self.assertEqual(payload["schema_version"], "2.0")
                self.assertEqual(payload["profile_checksum_contract"], "profile-machine-v1")
                result = self.run_cli(["validate", *self.common(project), "--lock", str(first)])
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_failure_diagnostic_does_not_echo_input_values(self) -> None:
        result = self.run_cli(["validate", *self.common(ARCH / "fixtures/invalid/mutable-oci.json")])
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stderr)
        self.assertFalse(payload["valid"])
        self.assertEqual(payload["diagnostics"][0]["code"], "OCI_DIGEST_REQUIRED")
        self.assertNotIn("6f7b03", result.stderr)

    def test_all_legacy_references_validate_without_rewriting(self) -> None:
        for reference in ("newemaint/target-candidate", "windows", "sqlite"):
            with self.subTest(reference=reference):
                root = ARCH / "reference" / reference
                lock = root / "architecture.lock.json"
                original = lock.read_bytes()
                result = self.run_cli(["validate", *self.common(root / "architecture.json"), "--lock", str(lock)])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(lock.read_bytes(), original)

    def test_explicit_migration_writes_only_temporary_v2_candidate(self) -> None:
        root = ARCH / "reference/sqlite"
        original = (root / "architecture.lock.json").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            candidates = [Path(directory) / "candidate.json", Path(directory) / "repeat.json"]
            for candidate in candidates:
                result = self.run_cli(["lock", *self.common(root / "architecture.json"), "--output", str(candidate)])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(candidate.read_text())["schema_version"], "2.0")
                result = self.run_cli(["validate", *self.common(root / "architecture.json"), "--lock", str(candidate)])
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(candidates[0].read_bytes(), candidates[1].read_bytes())
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["candidate.json", "repeat.json"])
        self.assertEqual((root / "architecture.lock.json").read_bytes(), original)

    def test_historical_prose_and_valid_machine_drift_through_cli(self) -> None:
        project = ARCH / "fixtures/valid/node-sqlite-native-project.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "linux-node-sqlite-v1.json"
            output = root / "lock.json"
            common = self.common(project)
            common[common.index("--profiles-dir") + 1] = str(root)
            profile.write_bytes((ARCH / "fixtures/profile-checksum/before-prose.json").read_bytes())
            result = self.run_cli(["lock", *common, "--output", str(output)])
            self.assertEqual(result.returncode, 0, result.stderr)
            original = output.read_bytes()
            profile.write_bytes((ARCH / "fixtures/profile-checksum/after-prose.json").read_bytes())
            result = self.run_cli(["validate", *common, "--lock", str(output)])
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(profile.read_text())
            data["delivery_contracts"].remove("docker-release/v1")
            profile.write_text(json.dumps(data))
            result = self.run_cli(["validate", *common, "--lock", str(output)])
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], "LOCK_DRIFT")
            self.assertEqual(output.read_bytes(), original)

    def test_unknown_formats_markers_and_tampering_are_read_only_failures(self) -> None:
        project = ARCH / "fixtures/valid/windows-project.json"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "lock.json"
            result = self.run_cli(["lock", *self.common(project), "--output", str(output)])
            self.assertEqual(result.returncode, 0, result.stderr)
            baseline = json.loads(output.read_text())
            cases = []
            for version in ("3.0", "../../arbitrary", None, ["2.0"]):
                value = deepcopy(baseline)
                value["schema_version"] = version
                cases.append((value, "LOCK_SCHEMA_VERSION_UNSUPPORTED"))
            value = deepcopy(baseline)
            value["profile_checksum_contract"] = "another-algorithm"
            cases.append((value, "SCHEMA_CONST"))
            value = deepcopy(baseline)
            value.pop("profile_checksum_contract")
            cases.append((value, "SCHEMA_REQUIRED"))
            value = deepcopy(baseline)
            value["schema_version"] = "1.0"
            cases.append((value, "SCHEMA_UNKNOWN_FIELD"))
            value = deepcopy(baseline)
            value["$schema"] = "./architecture/schemas/architecture-lock-v1.schema.json"
            cases.append((value, "SCHEMA_CONST"))
            value = deepcopy(baseline)
            value["resolved_components"][0]["version"] = "untrusted-version"
            cases.append((value, "LOCK_CHECKSUM_TAMPERED"))
            cases.append(([], "SCHEMA_TYPE"))
            for value, code in cases:
                with self.subTest(code=code, value_type=type(value).__name__):
                    output.write_text(json.dumps(value))
                    original = output.read_bytes()
                    result = self.run_cli(["validate", *self.common(project), "--lock", str(output)])
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stderr)["diagnostics"][0]["code"], code)
                    self.assertEqual(output.read_bytes(), original)
                    self.assertEqual(list(Path(directory).iterdir()), [output])
                    self.assertNotIn("untrusted-version", result.stderr)

    def test_cli_has_no_legacy_writer_or_ignore_switch(self) -> None:
        project = ARCH / "fixtures/valid/windows-project.json"
        for switch in ("--schema-version", "--ignore-drift"):
            with self.subTest(switch=switch), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "lock.json"
                result = self.run_cli(["lock", *self.common(project), "--output", str(output), switch, "1.0"])
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
