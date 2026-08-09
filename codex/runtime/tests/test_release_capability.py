from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from aisoft_release.compatibility import DockerCapability, require_supported
from aisoft_release.docker import DockerAdapter
from aisoft_release.errors import ContractError, DeploymentError

from tests.release_test_support import repository_root


def completed(stdout: bytes, returncode: int = 0) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=b"")


def matrix(*, status: str = "supported", evidence: object = "default") -> dict[str, object]:
    if evidence == "default":
        evidence = {
            "kind": "real-e2e",
            "evidence_id": "fixture-e2e-1",
            "date": "2026-08-04",
            "source": "test fixture",
        }
    return {
        "contract_version": "docker-image-store-compatibility/v1",
        "matrix_revision": "2026.08.99",
        "rows": [
            {
                "row_id": "fixture-containerd",
                "engine": {"minimum": "29.0.0", "maximum_exclusive": "30.0.0"},
                "compose": {"minimum": "2.27.0", "maximum_exclusive": "3.0.0"},
                "os": "linux",
                "architecture": "amd64",
                "image_store": "containerd",
                "status": status,
                "evidence": evidence,
                "remediation": "run the exact disposable E2E",
            }
        ],
    }


class DockerCapabilityTests(unittest.TestCase):
    def test_containerd_detection_uses_exact_driver_status_marker(self) -> None:
        outputs = [
            completed(b'{"Version":"29.0.1","Os":"linux","Arch":"amd64"}\n'),
            completed(b"v2.40.3\n"),
            completed(b"overlayfs\n"),
            completed(b'[["driver-type","io.containerd.snapshotter.v1"]]\n'),
        ]
        with patch("aisoft_release.docker.subprocess.run", side_effect=outputs) as run:
            capability = DockerAdapter().detect_capability()
        self.assertEqual(capability.image_store, "containerd")
        self.assertEqual(capability.engine_version, "29.0.1")
        self.assertEqual(capability.compose_version, "2.40.3")
        calls = [call.args[0] for call in run.call_args_list]
        self.assertIn("{{json .DriverStatus}}", calls[-1])
        self.assertIn("{{.Driver}}", calls[-2])

    def test_classic_requires_explicit_overlay2_and_no_snapshotter_marker(self) -> None:
        outputs = [
            completed(b'{"Version":"29.0.1","Os":"linux","Arch":"amd64"}\n'),
            completed(b"2.40.3\n"),
            completed(b"overlay2\n"),
            completed(b"null\n"),
        ]
        with patch("aisoft_release.docker.subprocess.run", side_effect=outputs):
            capability = DockerAdapter().detect_capability()
        self.assertEqual(capability.image_store, "classic")

    def test_unknown_conflicting_or_unbounded_metadata_fails_closed(self) -> None:
        variants = (
            (b"overlay2\n", b'[["driver-type","io.containerd.snapshotter.v1"]]\n'),
            (b"overlayfs\n", b"null\n"),
            (b"overlay2\n", b'[["driver-type","unknown"]]\n'),
            (
                b"overlayfs\n",
                b'[["driver-type","io.containerd.snapshotter.v1"],'
                b'["driver-type","io.containerd.snapshotter.v1"]]\n',
            ),
        )
        for driver, status in variants:
            with self.subTest(driver=driver, status=status):
                outputs = [
                    completed(b'{"Version":"29.0.1","Os":"linux","Arch":"amd64"}\n'),
                    completed(b"2.40.3\n"),
                    completed(driver),
                    completed(status),
                ]
                with patch("aisoft_release.docker.subprocess.run", side_effect=outputs):
                    with self.assertRaisesRegex(DeploymentError, "unknown|conflicting"):
                        DockerAdapter().detect_capability()

    def test_supported_matrix_row_requires_real_e2e_evidence(self) -> None:
        capability = DockerCapability("29.0.1", "2.40.3", "linux", "amd64", "containerd")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.json"
            path.write_text(json.dumps(matrix(), separators=(",", ":")) + "\n")
            decision = require_supported(capability, path)
            self.assertEqual(decision.row_id, "fixture-containerd")
            path.write_text(
                json.dumps(matrix(evidence=None), separators=(",", ":")) + "\n"
            )
            with self.assertRaisesRegex(ContractError, "requires real E2E evidence"):
                require_supported(capability, path)
            invalid_date = matrix()
            invalid_date["rows"][0]["evidence"]["date"] = "2026-02-30"  # type: ignore[index]
            path.write_text(json.dumps(invalid_date, separators=(",", ":")) + "\n")
            with self.assertRaisesRegex(ContractError, "evidence date is invalid"):
                require_supported(capability, path)

    def test_committed_containerd_row_is_supported_and_classic_remains_rejected(self) -> None:
        path = (
            repository_root()
            / "docker-release"
            / "compatibility"
            / "image-stores-v1.json"
        )
        decision = require_supported(
            DockerCapability("29.0.1", "2.40.3", "linux", "amd64", "containerd"),
            path,
        )
        self.assertEqual(decision.row_id, "engine-29-containerd-linux-amd64")
        self.assertEqual(decision.matrix_revision, "2026.08.3")
        with self.assertRaisesRegex(DeploymentError, "is rejected"):
            require_supported(
                DockerCapability("29.0.1", "2.40.3", "linux", "amd64", "classic"),
                path,
            )

    def test_committed_compose_514_evidence_row_is_supported(self) -> None:
        path = (
            repository_root()
            / "docker-release"
            / "compatibility"
            / "image-stores-v1.json"
        )
        decision = require_supported(
            DockerCapability("29.7.1", "5.1.4", "linux", "amd64", "containerd"),
            path,
        )
        self.assertEqual(
            decision.row_id,
            "engine-29.7.1-compose-5.1.4-containerd-linux-amd64",
        )
        self.assertEqual(decision.matrix_revision, "2026.08.3")

    def test_committed_compose_514_row_rejects_neighboring_bounds_and_classic(self) -> None:
        path = (
            repository_root()
            / "docker-release"
            / "compatibility"
            / "image-stores-v1.json"
        )
        unsupported = (
            DockerCapability("29.7.1", "5.1.3", "linux", "amd64", "containerd"),
            DockerCapability("29.7.1", "5.1.5", "linux", "amd64", "containerd"),
            DockerCapability("29.7.1", "5.2.0", "linux", "amd64", "containerd"),
            DockerCapability("29.7.0", "5.1.4", "linux", "amd64", "containerd"),
            DockerCapability("29.7.2", "5.1.4", "linux", "amd64", "containerd"),
            DockerCapability("29.7.1", "5.1.4", "linux", "amd64", "classic"),
        )
        for capability in unsupported:
            with self.subTest(capability=capability):
                with self.assertRaisesRegex(DeploymentError, "exactly one"):
                    require_supported(capability, path)

    def test_duplicate_or_overlapping_matrix_rows_fail_closed(self) -> None:
        capability = DockerCapability("29.0.1", "2.40.3", "linux", "amd64", "containerd")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.json"
            duplicate = matrix()
            duplicate["rows"].append(dict(duplicate["rows"][0]))  # type: ignore[union-attr,index]
            path.write_text(json.dumps(duplicate, separators=(",", ":")) + "\n")
            with self.assertRaisesRegex(ContractError, "duplicate row IDs"):
                require_supported(capability, path)

            overlapping = matrix()
            second = dict(overlapping["rows"][0])  # type: ignore[index]
            second["row_id"] = "fixture-containerd-overlap"
            overlapping["rows"].append(second)  # type: ignore[union-attr]
            path.write_text(json.dumps(overlapping, separators=(",", ":")) + "\n")
            with self.assertRaisesRegex(DeploymentError, "exactly one"):
                require_supported(capability, path)


if __name__ == "__main__":
    unittest.main()
