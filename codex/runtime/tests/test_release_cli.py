from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from aisoft_release.cli import build_parser, main

from tests.release_test_support import SHA_A, create_release, update_compose_model


class ReleaseCliTests(unittest.TestCase):
    def test_stable_commands_require_only_profile_and_release_id(self) -> None:
        parser = build_parser()
        for command in (
            "verify-target",
            "stage",
            "migrate",
            "activate",
            "verify",
            "deploy",
            "status",
            "rollback",
        ):
            with self.subTest(command=command):
                args = parser.parse_args(
                    [command, "--profile", "/tmp/profile.json", "--release-id", "a" * 40]
                )
                self.assertEqual(args.command, command)
                self.assertFalse(hasattr(args, "command_override"))

    def test_artifact_command_requires_release_root_not_profile(self) -> None:
        args = build_parser().parse_args(
            [
                "verify-artifact",
                "--release-root",
                "/tmp/releases",
                "--release-id",
                "a" * 40,
            ]
        )
        self.assertEqual(args.command, "verify-artifact")
        self.assertFalse(hasattr(args, "profile"))

    def test_arbitrary_extra_command_is_rejected(self) -> None:
        parser = build_parser()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "deploy",
                    "--profile",
                    "/tmp/profile.json",
                    "--release-id",
                    "a" * 40,
                    "--command",
                    "sh",
                ]
            )

    def test_artifact_cli_allows_sensitive_external_references_without_target_reads(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, _, _ = create_release(root)
            update_compose_model(
                root / "releases" / SHA_A,
                lambda model: model["services"]["web"].update(
                    {
                        "environment": {
                            "JWT_SECRET": "${JWT_SECRET:?required}",
                            "DATABASE_URL": "${DATABASE_URL:?required}",
                        }
                    }
                ),
            )
            profile_path.unlink()
            (root / "target.env").unlink()
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = main(
                    [
                        "verify-artifact",
                        "--release-root",
                        str(root / "releases"),
                        "--release-id",
                        SHA_A,
                    ]
                )
            self.assertEqual(result, 0)
            self.assertEqual(stderr.getvalue(), "")
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["target_facts"], "NOT_READ")
            self.assertEqual(payload["docker_calls"], 0)


if __name__ == "__main__":
    unittest.main()
