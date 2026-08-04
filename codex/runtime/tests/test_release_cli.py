from __future__ import annotations

import contextlib
import io
import unittest

from aisoft_release.cli import build_parser


class ReleaseCliTests(unittest.TestCase):
    def test_stable_commands_require_only_profile_and_release_id(self) -> None:
        parser = build_parser()
        for command in ("verify", "deploy", "status", "rollback"):
            with self.subTest(command=command):
                args = parser.parse_args(
                    [command, "--profile", "/tmp/profile.json", "--release-id", "a" * 40]
                )
                self.assertEqual(args.command, command)
                self.assertFalse(hasattr(args, "command_override"))

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


if __name__ == "__main__":
    unittest.main()
