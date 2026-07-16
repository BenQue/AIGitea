import json
from pathlib import Path
import tempfile
import unittest

from aisoft_loop.verifier import VerificationConfigError, Verifier, redact


class VerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        (self.repo / ".gitea").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_config(self, commands: list[dict], name: str = ".gitea/loop-verification.json") -> Path:
        target = self.repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"version": 1, "commands": commands}))
        return target

    def test_commands_use_argv_without_shell_interpretation(self) -> None:
        marker = self.repo / "should-not-exist"
        self.write_config(
            [
                {
                    "name": "argv-only",
                    "argv": ["printf", f"safe; touch {marker}"],
                    "timeout_seconds": 5,
                    "required": True,
                }
            ]
        )
        report = Verifier.from_file(self.repo).run_all()
        self.assertTrue(report.passed)
        self.assertFalse(marker.exists())
        self.assertIn("safe; touch", report.results[0].stdout)

    def test_required_failure_fails_report(self) -> None:
        self.write_config(
            [
                {
                    "name": "required",
                    "argv": ["python3", "-c", "raise SystemExit(7)"],
                    "timeout_seconds": 5,
                    "required": True,
                }
            ]
        )
        report = Verifier.from_file(self.repo).run_all()
        self.assertFalse(report.passed)
        self.assertEqual(report.results[0].exit_code, 7)

    def test_optional_failure_does_not_fail_report(self) -> None:
        self.write_config(
            [
                {
                    "name": "optional",
                    "argv": ["python3", "-c", "raise SystemExit(4)"],
                    "timeout_seconds": 5,
                    "required": False,
                }
            ]
        )
        report = Verifier.from_file(self.repo).run_all()
        self.assertTrue(report.passed)
        self.assertEqual(report.results[0].exit_code, 4)

    def test_timeout_is_reported_without_hanging(self) -> None:
        self.write_config(
            [
                {
                    "name": "timeout",
                    "argv": ["python3", "-c", "import time; time.sleep(1)"],
                    "timeout_seconds": 0.05,
                    "required": True,
                }
            ]
        )
        report = Verifier.from_file(self.repo).run_all()
        self.assertFalse(report.passed)
        self.assertTrue(report.results[0].timed_out)

    def test_output_is_truncated_to_64_kib(self) -> None:
        self.write_config(
            [
                {
                    "name": "large-output",
                    "argv": ["python3", "-c", "print('x' * 100000)"],
                    "timeout_seconds": 5,
                    "required": True,
                }
            ]
        )
        result = Verifier.from_file(self.repo).run_all().results[0]
        self.assertLessEqual(len(result.stdout.encode()), 65536 + 64)
        self.assertTrue(result.stdout.endswith("\n[output truncated]\n"))

    def test_credentials_and_dotenv_values_are_redacted(self) -> None:
        raw = (
            "Authorization: token top-secret\n"
            "GITEA_TOKEN=abc123\n"
            "db_password=hunter2\n"
            "API_KEY=key-value\n"
            "normal=value\n"
        )
        cleaned = redact(raw)
        for secret in ("top-secret", "abc123", "hunter2", "key-value"):
            self.assertNotIn(secret, cleaned)
        self.assertIn("normal=value", cleaned)
        self.assertGreaterEqual(cleaned.count("[REDACTED]"), 4)

    def test_empty_duplicate_or_string_commands_are_rejected(self) -> None:
        cases = (
            [],
            [
                {"name": "x", "argv": [], "timeout_seconds": 1, "required": True}
            ],
            [
                {"name": "x", "argv": "echo unsafe", "timeout_seconds": 1, "required": True}
            ],
            [
                {"name": "x", "argv": ["true"], "timeout_seconds": 1, "required": True},
                {"name": "x", "argv": ["true"], "timeout_seconds": 1, "required": True},
            ],
        )
        for commands in cases:
            with self.subTest(commands=commands):
                self.write_config(list(commands))
                with self.assertRaises(VerificationConfigError):
                    Verifier.from_file(self.repo)

    def test_config_path_must_stay_inside_repository(self) -> None:
        outside = self.repo.parent / "outside-verifier.json"
        outside.write_text('{"version":1,"commands":[]}')
        try:
            with self.assertRaisesRegex(VerificationConfigError, "inside repository"):
                Verifier.from_file(self.repo, outside)
        finally:
            outside.unlink()

    def test_unknown_config_fields_are_rejected(self) -> None:
        target = self.write_config(
            [
                {
                    "name": "safe",
                    "argv": ["true"],
                    "timeout_seconds": 1,
                    "required": True,
                    "shell": True,
                }
            ]
        )
        self.assertTrue(target.exists())
        with self.assertRaisesRegex(VerificationConfigError, "unknown fields"):
            Verifier.from_file(self.repo)


if __name__ == "__main__":
    unittest.main()
