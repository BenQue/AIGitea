from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
import unittest

from aisoft_architecture.errors import ArchitectureError
from aisoft_architecture.jsonio import canonical_bytes, load_json
from aisoft_architecture.lockfile import build_lock
from aisoft_architecture.validator import validate_catalog, validate_profile


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"
TODAY = date(2026, 8, 5)


class ArchitectureTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(ARCH / "catalog.json")
        self.catalog_schema = load_json(ARCH / "schemas/catalog-v1.schema.json")
        self.profile = load_json(
            ARCH / "profiles/linux-node-postgres-v1.json"
        )
        self.profile_schema = load_json(ARCH / "schemas/profile-v1.schema.json")
        self.project = load_json(ARCH / "fixtures/valid/linux-project.json")
        self.project_schema = load_json(
            ARCH / "schemas/project-architecture-v1.schema.json"
        )
        self._sync_project_identity()

    def _sync_project_identity(self) -> None:
        self.project["profile_version"] = self.profile["version"]
        self.project["catalog_revision"] = self.catalog["revision"]

    def _component(self, component_id: str) -> dict:
        return next(
            item for item in self.catalog["components"] if item["id"] == component_id
        )

    def _requirement(self, component_id: str) -> dict:
        return next(
            item
            for item in self.profile["required_components"]
            if item["component_id"] == component_id
        )

    def _declare_transition(
        self,
        preferred_id: str,
        transition_id: str,
        *,
        migration_issue: str = "https://gitea.example/projects/app/issues/101",
        created_at: str = "2026-08-04",
        expires_at: str = "2026-12-01",
    ) -> None:
        component = self._component(transition_id)
        declaration = {
            "component_id": transition_id,
            "version": component["version"],
            "migration_issue": migration_issue,
        }
        if component["pin"]["strategy"] == "oci-digest":
            declaration["digest"] = component["pin"]["value"]
        for index, declared in enumerate(self.project["components"]):
            if declared["component_id"] == preferred_id:
                self.project["components"][index] = declaration
                break
        else:
            raise AssertionError(f"missing preferred declaration: {preferred_id}")
        self.project["exceptions"].append(
            {
                "id": f"ARCH-EX-2026-{len(self.project['exceptions']) + 1:03d}",
                "component_id": transition_id,
                "owner": "fixture-owner",
                "reason": "Exercise the governed transition path.",
                "risk": "The older major may miss preferred behavior or support.",
                "controls": ["Pinned bytes and component-scoped migration controls."],
                "created_at": created_at,
                "expires_at": expires_at,
                "migration_issue": migration_issue,
            }
        )

    def _build(self) -> dict:
        return build_lock(
            self.catalog,
            self.catalog_schema,
            self.profile,
            self.profile_schema,
            self.project,
            self.project_schema,
            TODAY,
        )

    def _assert_error(self, code: str) -> None:
        with self.assertRaises(ArchitectureError) as caught:
            self._build()
        self.assertEqual(caught.exception.diagnostic.code, code)

    def test_preferred_path_remains_valid_without_exception(self) -> None:
        lock = self._build()
        self.assertEqual(lock["exception_ids"], [])
        self.assertTrue(
            all(item["state"] == "preferred" for item in lock["resolved_components"])
        )

    def test_supported_transition_binds_issue_exception_and_expiry_in_lock(self) -> None:
        self._declare_transition(
            "database.postgresql.18", "database.postgresql.16"
        )
        lock = self._build()
        component = next(
            item
            for item in lock["resolved_components"]
            if item["component_id"] == "database.postgresql.16"
        )
        self.assertEqual(component["state"], "supported")
        self.assertEqual(
            component["migration_issue"],
            "https://gitea.example/projects/app/issues/101",
        )
        self.assertEqual(component["exception_id"], "ARCH-EX-2026-001")
        self.assertEqual(component["exception_expires_at"], "2026-12-01")
        self.assertEqual(lock["exception_ids"], ["ARCH-EX-2026-001"])
        self.assertEqual(canonical_bytes(lock), canonical_bytes(self._build()))

    def test_multiple_transitions_may_share_one_umbrella_issue(self) -> None:
        umbrella_issue = "https://gitea.example/projects/app/issues/152"
        self._declare_transition(
            "runtime.node.24",
            "runtime.node.22",
            migration_issue=umbrella_issue,
        )
        self._declare_transition(
            "database.postgresql.18",
            "database.postgresql.16",
            migration_issue=umbrella_issue,
        )

        lock = self._build()
        transitions = [
            item
            for item in lock["resolved_components"]
            if item["component_id"]
            in {"runtime.node.22", "database.postgresql.16"}
        ]
        self.assertEqual(len(transitions), 2)
        self.assertEqual(
            {item["migration_issue"] for item in transitions},
            {umbrella_issue},
        )
        self.assertEqual(
            {item["exception_id"] for item in transitions},
            {"ARCH-EX-2026-001", "ARCH-EX-2026-002"},
        )

    def test_profile_transition_contract_fails_closed(self) -> None:
        components = validate_catalog(self.catalog, self.catalog_schema, TODAY)
        cases: list[tuple[dict, str]] = []

        unknown = deepcopy(self.profile)
        self._requirement_from(unknown, "runtime.node.24")["transitions"] = [
            {"component_id": "runtime.node.999", "allowed_states": ["sunset"]}
        ]
        cases.append((unknown, "PROFILE_TRANSITION_UNKNOWN"))

        cross_category = deepcopy(self.profile)
        self._requirement_from(cross_category, "runtime.node.24")["transitions"] = [
            {
                "component_id": "database.postgresql.16",
                "allowed_states": ["supported"],
            }
        ]
        cases.append((cross_category, "PROFILE_TRANSITION_CATEGORY"))

        duplicate = deepcopy(self.profile)
        self._requirement_from(duplicate, "runtime.node.24")["transitions"] = [
            {"component_id": "runtime.node.22", "allowed_states": ["sunset"]},
            {
                "component_id": "runtime.node.22",
                "allowed_states": ["supported", "sunset"],
            },
        ]
        cases.append((duplicate, "PROFILE_TRANSITION_DUPLICATE"))

        preferred_conflict = deepcopy(self.profile)
        self._requirement_from(preferred_conflict, "runtime.node.24")[
            "transitions"
        ] = [
            {"component_id": "runtime.node.24", "allowed_states": ["sunset"]}
        ]
        cases.append((preferred_conflict, "PROFILE_TRANSITION_CONFLICT"))

        wrong_state = deepcopy(self.profile)
        self._requirement_from(wrong_state, "runtime.node.24")["transitions"] = [
            {"component_id": "runtime.node.22", "allowed_states": ["supported"]}
        ]
        cases.append((wrong_state, "PROFILE_TRANSITION_STATE"))

        prohibited = deepcopy(self.profile)
        self._requirement_from(prohibited, "framework.next.16")["transitions"] = [
            {"component_id": "framework.next.14", "allowed_states": ["sunset"]}
        ]
        cases.append((prohibited, "PROFILE_TRANSITION_STATE"))

        unknown_field = deepcopy(self.profile)
        self._requirement_from(unknown_field, "runtime.node.24")["transitions"][0][
            "bypass"
        ] = True
        cases.append((unknown_field, "SCHEMA_UNKNOWN_FIELD"))

        for candidate, code in cases:
            with self.subTest(code=code), self.assertRaises(
                ArchitectureError
            ) as caught:
                validate_profile(
                    candidate,
                    self.profile_schema,
                    self.catalog,
                    components,
                )
            self.assertEqual(caught.exception.diagnostic.code, code)

    @staticmethod
    def _requirement_from(profile: dict, component_id: str) -> dict:
        return next(
            item
            for item in profile["required_components"]
            if item["component_id"] == component_id
        )

    def test_project_cannot_declare_preferred_and_transition_for_one_slot(self) -> None:
        transition = self._component("database.postgresql.16")
        self.project["components"].append(
            {
                "component_id": transition["id"],
                "version": transition["version"],
                "migration_issue": "https://gitea.example/projects/app/issues/101",
            }
        )
        self.project["exceptions"].append(
            {
                "id": "ARCH-EX-2026-001",
                "component_id": transition["id"],
                "owner": "fixture-owner",
                "reason": "Ambiguity fixture.",
                "risk": "Two components could resolve one slot.",
                "controls": ["Validator must reject before lock generation."],
                "created_at": "2026-08-04",
                "expires_at": "2026-12-01",
                "migration_issue": "https://gitea.example/projects/app/issues/101",
            }
        )
        self._assert_error("PROFILE_COMPONENT_AMBIGUOUS")

    def test_project_cannot_declare_multiple_transitions_for_one_slot(self) -> None:
        alternatives = (
            "framework.aspnet-core.10",
            "framework.iis.server-2025",
        )
        requirement = self._requirement("framework.next.16")
        requirement["transitions"] = []
        for component_id in alternatives:
            component = self._component(component_id)
            component["state"] = "supported"
            requirement["transitions"].append(
                {"component_id": component_id, "allowed_states": ["supported"]}
            )
        self.project["components"] = [
            item
            for item in self.project["components"]
            if item["component_id"] != "framework.next.16"
        ]
        for index, component_id in enumerate(alternatives, start=1):
            component = self._component(component_id)
            issue = f"https://gitea.example/fixtures/app/issues/{100 + index}"
            self.project["components"].append(
                {
                    "component_id": component_id,
                    "version": component["version"],
                    "migration_issue": issue,
                }
            )
            self.project["exceptions"].append(
                {
                    "id": f"ARCH-EX-2026-{index:03d}",
                    "component_id": component_id,
                    "owner": "fixture-owner",
                    "reason": "Multiple transition ambiguity fixture.",
                    "risk": "Two components could resolve one slot.",
                    "controls": ["Validator must reject before lock generation."],
                    "created_at": "2026-08-04",
                    "expires_at": "2026-12-01",
                    "migration_issue": issue,
                }
            )
        self._assert_error("PROFILE_COMPONENT_AMBIGUOUS")

    def test_transition_requires_absolute_issue_and_one_matching_exception(self) -> None:
        self._declare_transition(
            "database.postgresql.18", "database.postgresql.16"
        )

        missing_issue = deepcopy(self.project)
        missing_issue["components"][4].pop("migration_issue")
        self.project = missing_issue
        self._assert_error("TRANSITION_MIGRATION_REQUIRED")

        self.setUp()
        self._declare_transition(
            "database.postgresql.18",
            "database.postgresql.16",
            migration_issue="#51",
        )
        self._assert_error("TRANSITION_MIGRATION_ISSUE_INVALID")

        self.setUp()
        self._declare_transition(
            "database.postgresql.18",
            "database.postgresql.16",
            migration_issue="https://user:password@gitea.example/app/issues/101",
        )
        self._assert_error("TRANSITION_MIGRATION_ISSUE_INVALID")

        self.setUp()
        self._declare_transition(
            "database.postgresql.18", "database.postgresql.16"
        )
        self.project["exceptions"] = []
        self._assert_error("TRANSITION_EXCEPTION_REQUIRED")

        self.setUp()
        self._declare_transition(
            "database.postgresql.18", "database.postgresql.16"
        )
        duplicate = deepcopy(self.project["exceptions"][0])
        duplicate["id"] = "ARCH-EX-2026-002"
        self.project["exceptions"].append(duplicate)
        self._assert_error("EXCEPTION_COMPONENT_DUPLICATE")

        self.setUp()
        self._declare_transition(
            "database.postgresql.18", "database.postgresql.16"
        )
        self.project["exceptions"][0]["migration_issue"] = (
            "https://gitea.example/projects/app/issues/102"
        )
        self._assert_error("TRANSITION_EXCEPTION_MIGRATION_MISMATCH")

    def test_exception_time_bounds_fail_closed(self) -> None:
        self._declare_transition(
            "database.postgresql.18",
            "database.postgresql.16",
            expires_at="2027-02-01",
        )
        self._assert_error("EXCEPTION_DURATION_EXCEEDED")

        self.setUp()
        self._declare_transition(
            "orm.prisma.7",
            "orm.prisma.5",
            expires_at="2026-11-03",
        )
        self._assert_error("EXCEPTION_AFTER_MIGRATE_BY")

        self.setUp()
        self._declare_transition(
            "database.postgresql.18",
            "database.postgresql.16",
            expires_at="2026-08-04",
        )
        self._assert_error("EXCEPTION_EXPIRED")


if __name__ == "__main__":
    unittest.main()
