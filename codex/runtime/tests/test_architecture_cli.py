from pathlib import Path
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
            "--today", "2026-08-02",
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
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            project = ARCH / "fixtures/valid/linux-project.json"
            for output in (first, second):
                result = self.run_cli(["lock", *self.common(project), "--output", str(output)])
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            result = self.run_cli(["validate", *self.common(project), "--lock", str(first)])
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_failure_diagnostic_does_not_echo_input_values(self) -> None:
        result = self.run_cli(["validate", *self.common(ARCH / "fixtures/invalid/mutable-oci.json")])
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stderr)
        self.assertFalse(payload["valid"])
        self.assertEqual(payload["diagnostics"][0]["code"], "OCI_DIGEST_REQUIRED")
        self.assertNotIn("6f7b03", result.stderr)


if __name__ == "__main__":
    unittest.main()
