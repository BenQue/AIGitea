"""As-built version exceptions (Issue #284, 裁决 B).

Exact equality against the catalog pin stays the default. A project that
genuinely runs a different build inside the same major may declare it, but
only behind the same owner/risk/expiry exception machinery that governs
state transitions, so the deviation is recorded and time-bounded instead of
silently blessed.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
import unittest

from aisoft_architecture.errors import ArchitectureError
from aisoft_architecture.jsonio import canonical_bytes, load_json
from aisoft_architecture.lockfile import build_lock


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"
TODAY = date(2026, 9, 5)


class AsBuiltVersionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(ARCH / "catalog.json")
        self.catalog_schema = load_json(ARCH / "schemas/catalog-v1.schema.json")
        self.profile_schema = load_json(ARCH / "schemas/profile-v1.schema.json")
        self.project_schema = load_json(
            ARCH / "schemas/project-architecture-v1.schema.json"
        )
        self.profile = load_json(ARCH / "profiles/small-embedded-sqlite-v1.json")
        self.project = load_json(ARCH / "fixtures/valid/sqlite-project.json")

    def build(self) -> dict:
        return build_lock(
            self.catalog,
            self.catalog_schema,
            self.profile,
            self.profile_schema,
            self.project,
            self.project_schema,
            TODAY,
        )

    def declare_as_built(
        self,
        component_id: str,
        version: str,
        *,
        with_exception: bool = True,
        exception_id: str = "ARCH-EX-2026-001",
    ) -> None:
        declared = next(
            item
            for item in self.project["components"]
            if item["component_id"] == component_id
        )
        declared["version"] = version
        declared["as_built"] = True
        if with_exception:
            self.project["exceptions"].append(
                {
                    "id": exception_id,
                    "component_id": component_id,
                    "owner": "fixture-owner",
                    "reason": "The deployed build differs from the catalog pin.",
                    "risk": "The project runs bytes the platform has not pinned.",
                    "controls": [
                        "Exact as-built version, bounded expiry and a migration Issue."
                    ],
                    "created_at": "2026-08-04",
                    "expires_at": "2026-12-01",
                    "migration_issue": "http://gitea.example:3000/app/issues/284",
                }
            )

    def assert_code(self, code: str) -> None:
        with self.assertRaises(ArchitectureError) as caught:
            self.build()
        self.assertEqual(caught.exception.diagnostic.code, code)

    def test_as_built_records_the_declared_version_not_the_catalog_pin(self) -> None:
        self.declare_as_built("database.sqlite.3", "3.53.1")
        lock = self.build()
        component = next(
            item
            for item in lock["resolved_components"]
            if item["component_id"] == "database.sqlite.3"
        )
        self.assertEqual(component["version"], "3.53.1")
        # Issue #65 freezes the release runtime, and it rejects any lock key it
        # does not already know. So the deviation is carried by the recorded
        # build plus its exception, not by a new lock field, and every
        # as-built project stays releasable.
        self.assertNotIn("as_built", component)
        self.assertEqual(component["exception_id"], "ARCH-EX-2026-001")
        self.assertEqual(component["exception_expires_at"], "2026-12-01")
        self.assertEqual(lock["exception_ids"], ["ARCH-EX-2026-001"])

    def test_as_built_lock_is_byte_identical_on_repeat(self) -> None:
        self.declare_as_built("database.sqlite.3", "3.53.1")
        self.assertEqual(canonical_bytes(self.build()), canonical_bytes(self.build()))

    def test_as_built_without_an_exception_fails_closed(self) -> None:
        self.declare_as_built("database.sqlite.3", "3.53.1", with_exception=False)
        self.assert_code("AS_BUILT_EXCEPTION_REQUIRED")

    def test_as_built_cannot_cross_a_major_boundary(self) -> None:
        self.declare_as_built("database.sqlite.3", "4.0.1")
        self.assert_code("AS_BUILT_MAJOR_MISMATCH")

    def test_as_built_equal_to_the_pin_is_rejected_so_exceptions_do_not_rot(
        self,
    ) -> None:
        self.declare_as_built("database.sqlite.3", "3.53.3")
        self.assert_code("AS_BUILT_NOT_REQUIRED")

    def test_as_built_requires_a_parseable_leading_major(self) -> None:
        self.declare_as_built("database.sqlite.3", "trunk-build")
        self.assert_code("AS_BUILT_VERSION_UNPARSED")

    def test_as_built_on_a_zero_major_also_pins_the_minor(self) -> None:
        self.profile = load_json(
            ARCH / "profiles/linux-node-systemd-postgres-v1.json"
        )
        self.project = load_json(ARCH / "fixtures/valid/linux-systemd-project.json")
        self.declare_as_built("orm.kysely.0-29", "0.30.1")
        self.assert_code("AS_BUILT_MAJOR_MISMATCH")

        self.setUp()
        self.profile = load_json(
            ARCH / "profiles/linux-node-systemd-postgres-v1.json"
        )
        self.project = load_json(ARCH / "fixtures/valid/linux-systemd-project.json")
        self.declare_as_built("orm.kysely.0-29", "0.29.2")
        lock = self.build()
        component = next(
            item
            for item in lock["resolved_components"]
            if item["component_id"] == "orm.kysely.0-29"
        )
        self.assertEqual(component["version"], "0.29.2")

    def test_as_built_is_forbidden_on_a_digest_pinned_image(self) -> None:
        self.profile = load_json(ARCH / "profiles/linux-node-postgres-v1.json")
        self.project = load_json(ARCH / "fixtures/valid/linux-project.json")
        self.declare_as_built(
            "oci.node.24-bookworm-slim", "24.18.1-bookworm-slim"
        )
        self.assert_code("AS_BUILT_DIGEST_FORBIDDEN")

    def test_without_as_built_the_exact_pin_still_governs(self) -> None:
        declared = next(
            item
            for item in self.project["components"]
            if item["component_id"] == "database.sqlite.3"
        )
        declared["version"] = "3.53.1"
        self.assert_code("PROJECT_VERSION_DRIFT")

    def test_as_built_still_obeys_exception_expiry_and_duration_bounds(self) -> None:
        self.declare_as_built("database.sqlite.3", "3.53.1")
        self.project["exceptions"][0]["expires_at"] = "2026-08-04"
        self.assert_code("EXCEPTION_EXPIRED")

        self.setUp()
        self.declare_as_built("database.sqlite.3", "3.53.1")
        self.project["exceptions"][0]["expires_at"] = "2027-06-01"
        self.assert_code("EXCEPTION_DURATION_EXCEEDED")

    def test_as_built_false_is_not_an_accepted_form(self) -> None:
        declared = next(
            item
            for item in self.project["components"]
            if item["component_id"] == "database.sqlite.3"
        )
        declared["as_built"] = False
        self.assert_code("SCHEMA_CONST")

    def test_one_exception_covers_a_transition_that_is_also_as_built(self) -> None:
        self.profile = load_json(
            ARCH / "profiles/linux-node-systemd-postgres-v1.json"
        )
        self.project = load_json(ARCH / "fixtures/valid/linux-systemd-project.json")
        issue = "http://gitea.example:3000/app/issues/284"
        components = self.project["components"]
        for index, declared in enumerate(components):
            if declared["component_id"] == "runtime.node.24":
                components[index] = {
                    "component_id": "runtime.node.22",
                    "version": "22.22.0",
                    "as_built": True,
                    "migration_issue": issue,
                }
                break
        self.project["exceptions"].append(
            {
                "id": "ARCH-EX-2026-001",
                "component_id": "runtime.node.22",
                "owner": "fixture-owner",
                "reason": "Legacy runtime major and an older build of it.",
                "risk": "Both the major and the build trail the platform pin.",
                "controls": ["One bounded exception covers both deviations."],
                "created_at": "2026-08-04",
                "expires_at": "2026-12-01",
                "migration_issue": issue,
            }
        )
        lock = self.build()
        component = next(
            item
            for item in lock["resolved_components"]
            if item["component_id"] == "runtime.node.22"
        )
        self.assertEqual(component["version"], "22.22.0")
        self.assertEqual(component["state"], "sunset")
        self.assertEqual(component["exception_id"], "ARCH-EX-2026-001")
        self.assertEqual(lock["exception_ids"], ["ARCH-EX-2026-001"])


class ContainerDeliveryBaseImageTests(unittest.TestCase):
    """A container delivery contract must name a digest-pinned base image.

    The profile cannot express this: `required_components` is unconditional, so
    a slot would also force the native delivery contracts to declare an image
    they do not have. Stating it only in `compatibility_rules` left it fail
    open -- deleting the component validated clean. It is therefore a platform
    rule keyed on the delivery contract, not a profile slot.
    """

    def setUp(self) -> None:
        self.catalog = load_json(ARCH / "catalog.json")
        self.catalog_schema = load_json(ARCH / "schemas/catalog-v1.schema.json")
        self.profile_schema = load_json(ARCH / "schemas/profile-v1.schema.json")
        self.project_schema = load_json(
            ARCH / "schemas/project-architecture-v1.schema.json"
        )

    def build(self, project: dict) -> dict:
        profile = load_json(ARCH / f"profiles/{project['profile_id']}.json")
        return build_lock(
            self.catalog,
            self.catalog_schema,
            profile,
            self.profile_schema,
            project,
            self.project_schema,
            TODAY,
        )

    def _categories(self) -> dict:
        return {item["id"]: item["category"] for item in self.catalog["components"]}

    def test_container_declaration_without_a_base_image_fails_closed(self) -> None:
        project = load_json(
            ARCH / "fixtures/valid/node-sqlite-container-project.json"
        )
        categories = self._categories()
        project["components"] = [
            item
            for item in project["components"]
            if categories.get(item["component_id"]) != "oci-image"
        ]
        project["exceptions"] = [
            item
            for item in project["exceptions"]
            if categories.get(item["component_id"]) != "oci-image"
        ]
        with self.assertRaises(ArchitectureError) as caught:
            self.build(project)
        self.assertEqual(
            caught.exception.diagnostic.code, "DELIVERY_BASE_IMAGE_REQUIRED"
        )

    def test_native_delivery_contracts_are_untouched(self) -> None:
        for name in ("node-sqlite-native-project", "sqlite-project",
                     "linux-systemd-project", "windows-project"):
            with self.subTest(fixture=name):
                project = load_json(ARCH / f"fixtures/valid/{name}.json")
                self.assertNotEqual(project["delivery_contract"], "docker-release/v1")
                self.build(project)

    def test_every_existing_container_declaration_already_complies(self) -> None:
        categories = self._categories()
        checked = 0
        for path in sorted(ARCH.rglob("*.json")):
            if "lock" in path.name or path.parent.name == "schemas":
                continue
            try:
                project = load_json(path)
            except Exception:  # pragma: no cover - non-declaration inputs
                continue
            if not isinstance(project, dict):
                continue
            if project.get("delivery_contract") != "docker-release/v1":
                continue
            images = [
                item["component_id"]
                for item in project.get("components", [])
                if categories.get(item["component_id"]) == "oci-image"
            ]
            with self.subTest(path=path.name):
                self.assertTrue(images, f"{path} declares no base image")
            checked += 1
        self.assertGreaterEqual(checked, 4)

    def test_the_keyed_contract_set_tracks_the_schema_enum(self) -> None:
        """A later docker-release major must not silently skip the rule."""
        from aisoft_architecture.validator import CONTAINER_DELIVERY_CONTRACTS

        enum = set(self.project_schema["properties"]["delivery_contract"]["enum"])
        self.assertEqual(
            CONTAINER_DELIVERY_CONTRACTS,
            {value for value in enum if value.startswith("docker-release/")},
        )


if __name__ == "__main__":
    unittest.main()
