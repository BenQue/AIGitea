from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from aisoft_company_delivery.cli import main
from aisoft_company_delivery.contract import (
    EVIDENCE_VERSION,
    HANDOFF_VERSION,
    INVENTORY_VERSION,
    CompanyDeliveryError,
    load_evidence,
    load_handoff,
    load_inventory,
)


SHA = "1" * 40
DIGEST = "2" * 64


class CompanyDeliveryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_json(self, name: str, value: object, *, mode: int = 0o600) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        path.chmod(mode)
        return path

    def inventory(self) -> dict[str, object]:
        return {
            "contract_version": INVENTORY_VERSION,
            "collector_version": "1.0.0",
            "collected_at": "2026-08-16T08:00:00Z",
            "role": "scm-ci",
            "scope": "company-candidate",
            "outcome": "PASS",
            "host": {
                "hostname_sha256": "sha256:" + DIGEST,
                "machine_id_sha256": "sha256:" + DIGEST,
                "os_id": "ubuntu",
                "os_version": "24.04",
                "kernel_version": "6.8.0",
                "architecture": "amd64",
                "cpu_count": 4,
                "memory_bytes": 8_589_934_592,
                "root_free_bytes": 53_687_091_200,
            },
            "tools": [
                {
                    "name": "docker-engine",
                    "status": "PASS",
                    "version": "29.7.1",
                    "reason": None,
                }
            ],
            "units": [
                {
                    "name": "docker.service",
                    "enabled": "enabled",
                    "active": "active",
                }
            ],
            "pending": [],
        }

    def evidence(self) -> dict[str, object]:
        return {
            "contract_version": EVIDENCE_VERSION,
            "evidence_id": "CDP-120-STAGE-00-001",
            "stage": "00",
            "scope": "local-fake",
            "recorded_at": "2026-08-16T08:00:00Z",
            "operator_version": "1.0.0",
            "source_git_sha": SHA,
            "release_id": SHA,
            "outcome": "PASS",
            "observed": [
                {
                    "code": "BUNDLE_PRESENT",
                    "status": "PASS",
                    "detail": "Fake bundle exists.",
                    "artifacts": ["handoff-manifest.json"],
                }
            ],
            "changed": [],
            "verified": [],
            "pending": [],
        }

    def handoff(self) -> dict[str, object]:
        return {
            "contract_version": HANDOFF_VERSION,
            "operator_version": "1.0.0",
            "created_at": "2026-08-16T08:00:00Z",
            "source": {
                "repository": "admin/aisoft-platform",
                "git_sha": SHA,
                "transport": "approved-bundle",
            },
            "release": {
                "contract_version": "docker-release/v2",
                "release_id": SHA,
                "manifest_path": "release/release.json",
                "manifest_sha256": DIGEST,
                "platform": "linux/amd64",
                "transport": "offline-bundle",
            },
            "compatibility": {
                "matrix_path": "operator/compatibility/newemaint-company-pilot-v1.json",
                "matrix_sha256": DIGEST,
                "required_roles": ["scm-ci", "appserver-prod"],
            },
            "payloads": [
                {
                    "path": "operator/VERSION",
                    "sha256": DIGEST,
                    "size_bytes": 6,
                    "mode": "0644",
                }
            ],
        }

    def test_valid_contract_documents(self) -> None:
        self.assertEqual(load_inventory(self.write_json("inventory.json", self.inventory()))["role"], "scm-ci")
        self.assertEqual(load_evidence(self.write_json("evidence.json", self.evidence()))["stage"], "00")
        self.assertEqual(
            load_handoff(
                self.write_json("handoff.json", self.handoff()),
                bundle_root=None,
                verify_payloads=False,
            )["source"]["git_sha"],
            SHA,
        )

    def test_repository_templates_and_compatibility_are_parseable(self) -> None:
        repository = Path(__file__).resolve().parents[3]
        delivery = repository / "company-delivery"
        inventory = load_inventory(
            delivery / "templates/inventory.example.json",
            require_protected=False,
        )
        evidence = load_evidence(
            delivery / "templates/evidence.not-run.example.json",
            require_protected=False,
        )
        handoff = load_handoff(
            delivery / "templates/handoff-manifest.example.json",
            bundle_root=None,
            verify_payloads=False,
            require_protected=False,
        )
        compatibility = json.loads(
            (delivery / "compatibility/newemaint-company-pilot-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(inventory["outcome"], "NOT RUN")
        self.assertEqual(evidence["outcome"], "NOT RUN")
        self.assertEqual(handoff["release"]["platform"], "linux/amd64")
        self.assertEqual(compatibility["topology"]["company_vm_count"], 2)
        self.assertEqual(
            compatibility["policy"]["intranet_rebuild_without_isolated_test"],
            "BLOCKED",
        )

    def test_unknown_fields_short_sha_and_unsafe_payload_paths_fail(self) -> None:
        inventory = self.inventory()
        inventory["unexpected"] = True
        with self.assertRaises(CompanyDeliveryError):
            load_inventory(self.write_json("unknown.json", inventory))

        evidence = self.evidence()
        evidence["source_git_sha"] = "1234"
        with self.assertRaises(CompanyDeliveryError):
            load_evidence(self.write_json("short-sha.json", evidence))

        for index, unsafe in enumerate(("/absolute", "../escape", "nested/../../escape")):
            handoff = self.handoff()
            handoff["payloads"][0]["path"] = unsafe
            with self.subTest(path=unsafe), self.assertRaises(CompanyDeliveryError):
                load_handoff(
                    self.write_json(f"unsafe-{index}.json", handoff),
                    bundle_root=None,
                    verify_payloads=False,
                )

    def test_sensitive_content_is_rejected_without_echo(self) -> None:
        sentinel = "never-print-this-value"
        for field, value in (
            ("token", sentinel),
            ("detail", f"Authorization: Bearer {sentinel}"),
            ("detail", f"postgresql://user:{sentinel}@db/app"),
            ("detail", f"-----BEGIN PRIVATE KEY----- {sentinel}"),
        ):
            evidence = self.evidence()
            if field == "token":
                evidence[field] = value
            else:
                evidence["observed"][0][field] = value
            path = self.write_json(f"sensitive-{len(list(self.root.iterdir()))}.json", evidence)
            with self.subTest(field=field), self.assertRaises(CompanyDeliveryError) as caught:
                load_evidence(path)
            self.assertNotIn(sentinel, str(caught.exception))

    def test_protected_file_mode_and_symlink_are_fail_closed(self) -> None:
        permissive = self.write_json("permissive.json", self.inventory(), mode=0o644)
        with self.assertRaises(CompanyDeliveryError):
            load_inventory(permissive)

        target = self.write_json("target.json", self.inventory())
        link = self.root / "link.json"
        link.symlink_to(target)
        with self.assertRaises(CompanyDeliveryError):
            load_inventory(link)

    def test_cli_failure_is_machine_readable_and_sanitized(self) -> None:
        sentinel = "never-print-this-value"
        evidence = self.evidence()
        evidence["observed"][0]["detail"] = f"password={sentinel}"
        path = self.write_json("cli-sensitive.json", evidence)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["verify-evidence", "--input", str(path)])
        self.assertEqual(result, 2)
        value = json.loads(stderr.getvalue())
        self.assertFalse(value["ok"])
        self.assertEqual(value["error_code"], "SENSITIVE_CONTENT")
        self.assertNotIn(sentinel, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
