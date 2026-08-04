from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from aisoft_release.docker import DockerAdapter
from aisoft_release.errors import DeploymentError, StateError
from aisoft_release.state import DeploymentLock

from tests.release_test_support import WEB_DIGEST


class DockerAdapterSafetyTests(unittest.TestCase):
    def test_subprocess_failure_never_exposes_output_or_sensitive_environment(self) -> None:
        adapter = DockerAdapter()
        reference = "registry.internal/admin/app@" + WEB_DIGEST
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=42,
            stdout=b"token=fixture-secret\n",
            stderr=b"DATABASE_PASSWORD=fixture-secret\n",
        )
        with patch.dict(
            os.environ,
            {"DATABASE_PASSWORD": "fixture-secret", "DOCKER_HOST": "unix:///safe.sock"},
            clear=False,
        ), patch("aisoft_release.docker.subprocess.run", return_value=completed) as run:
            with self.assertRaises(DeploymentError) as caught:
                adapter.pull_image(reference)
        self.assertNotIn("fixture-secret", str(caught.exception))
        self.assertNotIn("token", str(caught.exception).lower())
        kwargs = run.call_args.kwargs
        self.assertIs(kwargs["shell"], False)
        self.assertNotIn("DATABASE_PASSWORD", kwargs["env"])
        self.assertEqual(kwargs["env"]["DOCKER_HOST"], "unix:///safe.sock")

    def test_compose_config_uses_non_interpolating_json_validation_flags(self) -> None:
        adapter = DockerAdapter()
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'{"services":{}}\n', stderr=b""
        )
        with patch("aisoft_release.docker.subprocess.run", return_value=completed) as run:
            adapter.compose_config(Path("/tmp/release/compose.yaml"), "app-test")
        args = run.call_args.args[0]
        self.assertIn("--format", args)
        self.assertIn("json", args)
        self.assertIn("--no-interpolate", args)
        self.assertIn("--no-env-resolution", args)
        self.assertNotIn("--env-file", args)


class DeploymentLockTests(unittest.TestCase):
    def test_second_process_lock_holder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            with DeploymentLock(root):
                with self.assertRaises(StateError):
                    with DeploymentLock(root):
                        self.fail("second lock holder must not enter")


if __name__ == "__main__":
    unittest.main()
