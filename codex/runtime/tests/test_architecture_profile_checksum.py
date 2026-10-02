from copy import deepcopy
from datetime import date
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from aisoft_architecture.errors import ArchitectureError
from aisoft_architecture.jsonio import canonical_bytes, load_json, sha256_value
from aisoft_architecture.lockfile import build_lock, validate_lock


ARCH = Path(__file__).resolve().parents[3] / "architecture"
TODAY = date(2026, 9, 5)


class ProfileChecksumTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(ARCH / "catalog.json")
        self.catalog_schema = load_json(ARCH / "schemas/catalog-v1.schema.json")
        self.profile_schema = load_json(ARCH / "schemas/profile-v1.schema.json")
        self.project_schema = load_json(ARCH / "schemas/project-architecture-v1.schema.json")
        self.project = load_json(ARCH / "fixtures/valid/node-sqlite-native-project.json")
        self.before = load_json(ARCH / "fixtures/profile-checksum/before-prose.json")
        self.after = load_json(ARCH / "fixtures/profile-checksum/after-prose.json")

    def build(self, profile=None, **kwargs) -> dict:
        return build_lock(
            self.catalog, self.catalog_schema,
            self.after if profile is None else profile, self.profile_schema,
            self.project, self.project_schema, TODAY, **kwargs,
        )

    def validate(self, lock: dict, expected: dict) -> None:
        name = "architecture-lock-v1.schema.json" if lock["schema_version"] == "1.0" else "architecture-lock-v2.schema.json"
        validate_lock(lock, load_json(ARCH / "schemas" / name), expected)

    def assert_drift(self, lock: dict, expected: dict) -> None:
        with self.assertRaises(ArchitectureError) as caught:
            self.validate(lock, expected)
        self.assertEqual(caught.exception.diagnostic.code, "LOCK_DRIFT")

    def test_new_writer_uses_explicit_v2_and_retains_source_hashes(self) -> None:
        lock = self.build()
        self.assertEqual(lock["schema_version"], "2.0")
        self.assertEqual(lock["$schema"], "./architecture/schemas/architecture-lock-v2.schema.json")
        self.assertEqual(lock["profile_checksum_contract"], "profile-machine-v1")
        self.assertEqual(lock["source_checksums"]["catalog_sha256"], sha256_value(self.catalog))
        self.assertEqual(lock["source_checksums"]["declaration_sha256"], sha256_value(self.project))
        self.validate(lock, lock)

    def test_historical_prose_change_is_stable_for_existing_v2_lock(self) -> None:
        old = self.build(self.before)
        new = self.build(self.after)
        self.assertEqual(canonical_bytes(old), canonical_bytes(new))
        self.validate(old, new)
        for field in ("description", "compatibility_rules"):
            profile = deepcopy(self.after)
            if field == "description":
                profile[field] += " Explanation clarified."
            else:
                profile[field].append("Another explanation.")
            with self.subTest(field=field):
                candidate = self.build(profile)
                self.assertEqual(canonical_bytes(old), canonical_bytes(candidate))
                self.validate(old, candidate)

    def test_valid_machine_changes_drift_without_version_bump(self) -> None:
        baseline = self.build()
        profiles = {}
        p = deepcopy(self.after)
        p["delivery_contracts"].remove("docker-release/v1")
        profiles["delivery"] = p
        p = deepcopy(self.after)
        p["status"] = "reference"
        profiles["status"] = p
        p = deepcopy(self.after)
        p["constraints"]["backup"] += " Keep checksums."
        profiles["constraints"] = p
        p = deepcopy(self.after)
        p["required_components"] = list(reversed(p["required_components"]))
        profiles["slots_order"] = p
        p = deepcopy(self.after)
        p["required_components"] = p["required_components"][1:]
        profiles["slot_removed"] = p
        p = deepcopy(self.after)
        p["delivery_contracts"] = list(reversed(p["delivery_contracts"]))
        profiles["delivery_order"] = p
        p = deepcopy(self.after)
        node = next(x for x in p["required_components"] if x["component_id"] == "runtime.node.24")
        node["transitions"][0]["allowed_states"].append("supported")
        profiles["transition_states"] = p
        for field, profile in profiles.items():
            with self.subTest(field=field):
                self.assertEqual(profile["version"], self.after["version"])
                expected = self.build(profile)
                self.assertNotEqual(baseline["source_checksums"]["profile_sha256"], expected["source_checksums"]["profile_sha256"])
                self.assert_drift(baseline, expected)

    def test_invalid_machine_changes_fail_at_policy_boundary(self) -> None:
        for field in ("slot", "allowed_states", "transition", "unknown"):
            p = deepcopy(self.after)
            if field == "slot":
                p["required_components"][0]["component_id"] = "os.unknown"
                code = "PROFILE_COMPONENT_UNKNOWN"
            elif field == "allowed_states":
                p["required_components"][0]["allowed_states"] = ["supported"]
                code = "PROFILE_COMPONENT_STATE"
            elif field == "transition":
                node = next(x for x in p["required_components"] if x["component_id"] == "runtime.node.24")
                node["transitions"][0]["component_id"] = "runtime.unknown"
                code = "PROFILE_TRANSITION_UNKNOWN"
            else:
                p["unapproved_field"] = True
                code = "SCHEMA_UNKNOWN_FIELD"
            with self.subTest(field=field), self.assertRaises(ArchitectureError) as caught:
                self.build(p)
            self.assertEqual(caught.exception.diagnostic.code, code)

    def test_legacy_lock_retains_full_hash_and_prose_drift(self) -> None:
        old = self.build(self.before, schema_version="1.0")
        new = self.build(self.after, schema_version="1.0")
        self.assertNotIn("profile_checksum_contract", old)
        self.assertEqual(old["source_checksums"]["profile_sha256"], "6eb2458f72b363308f619710b45e4420ce6d265d63223d5a97f9db29dae85a95")
        self.assertEqual(new["source_checksums"]["profile_sha256"], "7ed962a29060d62b57be5f983335136778b9ad2126fca93d0f84b975125a6418")
        self.validate(old, old)
        self.assert_drift(old, new)

    def test_v2_checksum_tampering_and_marker_mixing_fail(self) -> None:
        baseline = self.build()
        p = deepcopy(baseline)
        p["resolved_components"][0]["version"] = "changed"
        with self.assertRaises(ArchitectureError) as caught:
            self.validate(p, baseline)
        self.assertEqual(caught.exception.diagnostic.code, "LOCK_CHECKSUM_TAMPERED")
        for mutation, code in (("missing", "SCHEMA_REQUIRED"), ("unknown", "SCHEMA_CONST"), ("extra", "SCHEMA_UNKNOWN_FIELD")):
            p = deepcopy(baseline)
            if mutation == "missing":
                p.pop("profile_checksum_contract")
            elif mutation == "unknown":
                p["profile_checksum_contract"] = "unknown"
            else:
                p["unapproved_field"] = True
            with self.subTest(mutation=mutation), self.assertRaises(ArchitectureError) as caught:
                self.validate(p, baseline)
            self.assertEqual(caught.exception.diagnostic.code, code)
        old = self.build(schema_version="1.0")
        mixed = deepcopy(old)
        mixed["profile_checksum_contract"] = "profile-machine-v1"
        with self.assertRaises(ArchitectureError) as caught:
            self.validate(mixed, old)
        self.assertEqual(caught.exception.diagnostic.code, "SCHEMA_UNKNOWN_FIELD")

    def test_v2_generation_is_offline_and_does_not_mutate_inputs(self) -> None:
        original = canonical_bytes(self.after)
        with patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            first = self.build()
            second = self.build()
        self.assertEqual(canonical_bytes(first), canonical_bytes(second))
        self.assertEqual(canonical_bytes(self.after), original)

    def test_new_schema_approved_machine_fields_enter_hash_by_default(self) -> None:
        self.profile_schema["properties"]["future_machine_rule"] = {"type": "boolean"}
        baseline = self.build()
        profile = deepcopy(self.after)
        profile["future_machine_rule"] = True
        self.assert_drift(baseline, self.build(profile))


if __name__ == "__main__":
    unittest.main()
