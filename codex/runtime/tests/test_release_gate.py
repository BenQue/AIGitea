from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from aisoft_release.errors import GateError
from aisoft_release.gate import run_gate

from tests.release_test_support import SHA_A, write_json


class ReleaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.gate_root = self.root / "grants"
        self.action_root = self.gate_root / "stage"
        self.action_root.mkdir(parents=True)
        os.chmod(self.gate_root, 0o755)
        os.chmod(self.action_root, 0o755)
        self.audit_root = self.root / "audit"
        self.audit_root.mkdir()
        os.chmod(self.audit_root, 0o700)
        self.profile = self.root / "fixed-profile.json"
        self.audit = self.audit_root / "actions.jsonl"
        write_json(
            self.action_root / "target-a.json",
            {
                "contract_version": "docker-release-command-gate/v1",
                "action": "stage",
                "target_id": "target-a",
                "profile": str(self.profile),
                "audit_log": str(self.audit),
            },
            mode=0o600,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @patch("aisoft_release.gate.subprocess.run")
    def test_gate_executes_only_fixed_argv_and_audits_result(self, run: object) -> None:
        run.return_value = subprocess.CompletedProcess([], 0)
        result = run_gate(
            "stage",
            "target-a",
            SHA_A,
            gate_root=self.gate_root,
            cli_path=Path("/fixed/aisoft-docker-release"),
            enforce_root_owner=False,
        )
        self.assertEqual(result, 0)
        run.assert_called_once_with(
            [
                "/fixed/aisoft-docker-release",
                "stage",
                "--profile",
                str(self.profile),
                "--release-id",
                SHA_A,
            ],
            shell=False,
            check=False,
            env={
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
            },
        )
        records = [json.loads(line) for line in self.audit.read_text().splitlines()]
        self.assertEqual([record["event"] for record in records], ["started", "completed"])
        self.assertEqual(records[-1]["exit_code"], 0)
        self.assertEqual(self.audit.stat().st_mode & 0o777, 0o600)

    def test_arbitrary_action_short_sha_and_grant_mismatch_are_rejected(self) -> None:
        for action, release_id in (("shell", SHA_A), ("stage", "abc")):
            with self.subTest(action=action, release_id=release_id), self.assertRaises(
                GateError
            ), patch("aisoft_release.gate.subprocess.run") as run:
                run_gate(
                    action,
                    "target-a",
                    release_id,
                    gate_root=self.gate_root,
                    enforce_root_owner=False,
                )
                run.assert_not_called()

        grant = json.loads((self.action_root / "target-a.json").read_text())
        grant["profile"] = "relative/profile.json"
        write_json(self.action_root / "target-a.json", grant, mode=0o600)
        with self.assertRaisesRegex(GateError, "absolute paths"), patch(
            "aisoft_release.gate.subprocess.run"
        ) as run:
            run_gate(
                "stage",
                "target-a",
                SHA_A,
                gate_root=self.gate_root,
                enforce_root_owner=False,
            )
            run.assert_not_called()

    def test_writable_or_symlink_grant_is_rejected_before_command(self) -> None:
        grant = self.action_root / "target-a.json"
        os.chmod(grant, 0o644)
        with self.assertRaisesRegex(GateError, "0400 or 0600"), patch(
            "aisoft_release.gate.subprocess.run"
        ) as run:
            run_gate(
                "stage",
                "target-a",
                SHA_A,
                gate_root=self.gate_root,
                enforce_root_owner=False,
            )
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
