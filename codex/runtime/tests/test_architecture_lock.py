from copy import deepcopy
from datetime import date
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from aisoft_architecture.errors import ArchitectureError
from aisoft_architecture.jsonio import canonical_bytes, load_json
from aisoft_architecture.lockfile import build_lock, validate_lock


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"
TODAY = date(2026, 8, 5)


class ArchitectureLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(ARCH / "catalog.json")
        self.catalog_schema = load_json(ARCH / "schemas/catalog-v1.schema.json")
        self.profile_schema = load_json(ARCH / "schemas/profile-v1.schema.json")
        self.project_schema = load_json(ARCH / "schemas/project-architecture-v1.schema.json")
        self.lock_schema = load_json(ARCH / "schemas/architecture-lock-v1.schema.json")
        self.project = load_json(ARCH / "fixtures/valid/sqlite-project.json")
        self.profile = load_json(ARCH / "profiles/small-embedded-sqlite-v1.json")

    def build(self, *, today: date = TODAY) -> dict:
        return build_lock(
            self.catalog,
            self.catalog_schema,
            self.profile,
            self.profile_schema,
            self.project,
            self.project_schema,
            today,
        )

    def test_repeat_lock_is_byte_identical(self) -> None:
        self.assertEqual(canonical_bytes(self.build()), canonical_bytes(self.build()))

    def test_lock_checksum_and_drift_fail_closed(self) -> None:
        expected = self.build()
        tampered = deepcopy(expected)
        tampered["resolved_components"][0]["version"] = "tampered"
        with self.assertRaises(ArchitectureError) as caught:
            validate_lock(tampered, self.lock_schema, expected)
        self.assertEqual(caught.exception.diagnostic.code, "LOCK_CHECKSUM_TAMPERED")

        drift = deepcopy(expected)
        drift["project_id"] = "different"
        payload = dict(drift)
        payload.pop("lock_sha256")
        from aisoft_architecture.jsonio import sha256_value

        drift["lock_sha256"] = sha256_value(payload)
        with self.assertRaises(ArchitectureError) as caught:
            validate_lock(drift, self.lock_schema, expected)
        self.assertEqual(caught.exception.diagnostic.code, "LOCK_DRIFT")

        fixture = load_json(ARCH / "fixtures/invalid/tampered-lock.json")
        with self.assertRaises(ArchitectureError) as caught:
            validate_lock(fixture, self.lock_schema, expected)
        self.assertEqual(caught.exception.diagnostic.code, "LOCK_CHECKSUM_TAMPERED")

    def test_eol_boundary_is_invalid_on_exact_utc_date(self) -> None:
        component = next(item for item in self.catalog["components"] if item["id"] == "database.sqlite.3")
        component["lifecycle"]["support_end"] = "2026-08-02"
        component["lifecycle"]["eol"] = "2026-08-02"
        component["lifecycle"]["migrate_by"] = "2026-08-01"
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertEqual(caught.exception.diagnostic.code, "COMPONENT_EOL")

    def test_exception_expiry_boundary_is_invalid_on_exact_date(self) -> None:
        self.project = load_json(ARCH / "fixtures/invalid/expired-exception.json")
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertEqual(caught.exception.diagnostic.code, "EXCEPTION_EXPIRED")

    def test_sunset_requires_migration_issue(self) -> None:
        self.profile = load_json(
            ARCH / "profiles/linux-node-postgres-v1.json"
        )
        self.project = load_json(ARCH / "fixtures/valid/linux-project.json")
        node22 = next(
            item
            for item in self.catalog["components"]
            if item["id"] == "runtime.node.22"
        )
        node24_index = next(
            index
            for index, item in enumerate(self.project["components"])
            if item["component_id"] == "runtime.node.24"
        )
        self.project["components"][node24_index] = {
            "component_id": node22["id"],
            "version": node22["version"],
        }
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertEqual(caught.exception.diagnostic.code, "SUNSET_MIGRATION_REQUIRED")

    def test_prohibited_component_and_source_freshness_fail(self) -> None:
        component = next(item for item in self.catalog["components"] if item["id"] == "database.sqlite.3")
        component["state"] = "prohibited"
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertIn(caught.exception.diagnostic.code, {"PROFILE_COMPONENT_STATE", "COMPONENT_PROHIBITED"})

        self.setUp()
        component = next(item for item in self.catalog["components"] if item["id"] == "database.sqlite.3")
        component["provenance"]["review_by"] = "2026-08-01"
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertEqual(caught.exception.diagnostic.code, "SOURCE_REVIEW_OVERDUE")

    def test_runtime_has_no_network_dependency(self) -> None:
        with patch.object(socket, "socket", side_effect=AssertionError("network access attempted")):
            lock = self.build()
        self.assertEqual(lock["project_id"], "fixture-sqlite")

    def test_profile_catalog_and_delivery_mismatches_fail(self) -> None:
        self.profile["catalog_revision"] = "2026.07.9"
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertEqual(caught.exception.diagnostic.code, "PROFILE_CATALOG_MISMATCH")

        self.setUp()
        self.project["delivery_contract"] = "pm2-legacy"
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertEqual(caught.exception.diagnostic.code, "DELIVERY_CONTRACT_INCOMPATIBLE")

    def test_incomplete_exception_fails_schema(self) -> None:
        self.project["exceptions"] = [{"id": "ARCH-EX-2026-002"}]
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertEqual(caught.exception.diagnostic.code, "SCHEMA_REQUIRED")

    def test_committed_reference_locks_cross_check(self) -> None:
        for reference in ("newemaint/target-candidate", "windows", "sqlite"):
            with self.subTest(reference=reference):
                project = load_json(ARCH / "reference" / reference / "architecture.json")
                profile = load_json(ARCH / "profiles" / f"{project['profile_id']}.json")
                expected = build_lock(
                    self.catalog,
                    self.catalog_schema,
                    profile,
                    self.profile_schema,
                    project,
                    self.project_schema,
                    TODAY,
                )
                validate_lock(
                    load_json(ARCH / "reference" / reference / "architecture.lock.json"),
                    self.lock_schema,
                    expected,
                )


if __name__ == "__main__":
    unittest.main()
