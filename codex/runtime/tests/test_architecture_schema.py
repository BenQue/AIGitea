from copy import deepcopy
from datetime import date
from pathlib import Path
import unittest

from aisoft_architecture.errors import ArchitectureError
from aisoft_architecture.jsonio import load_json
from aisoft_architecture.lockfile import build_lock
from aisoft_architecture.schema import validate_schema
from aisoft_architecture.validator import validate_catalog, validate_profile


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "architecture"
TODAY = date(2026, 8, 4)


class ArchitectureSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_json(ARCH / "catalog.json")
        cls.catalog_schema = load_json(ARCH / "schemas/catalog-v1.schema.json")
        cls.profile_schema = load_json(ARCH / "schemas/profile-v1.schema.json")
        cls.project_schema = load_json(ARCH / "schemas/project-architecture-v1.schema.json")

    def build(self, project_path: Path) -> dict:
        project = load_json(project_path)
        profile = load_json(ARCH / "profiles" / f"{project['profile_id']}.json")
        return build_lock(
            self.catalog,
            self.catalog_schema,
            profile,
            self.profile_schema,
            project,
            self.project_schema,
            TODAY,
        )

    def test_catalog_and_all_profiles_validate(self) -> None:
        components = validate_catalog(self.catalog, self.catalog_schema, TODAY)
        self.assertEqual(len(components), 29)
        profile_ids = []
        for path in sorted((ARCH / "profiles").glob("*.json")):
            profile = load_json(path)
            validate_profile(profile, self.profile_schema, self.catalog, components)
            profile_ids.append(profile["profile_id"])
        self.assertEqual(len(profile_ids), 3)
        self.assertEqual(len(profile_ids), len(set(profile_ids)))

    def test_valid_fixtures_pass_schema_and_runtime(self) -> None:
        for path in sorted((ARCH / "fixtures/valid").glob("*.json")):
            with self.subTest(path=path.name):
                project = load_json(path)
                validate_schema(project, self.project_schema)
                lock = self.build(path)
                self.assertEqual(lock["project_id"], project["project_id"])

    def test_invalid_fixtures_fail_runtime(self) -> None:
        expected = {
            "unknown-field.json": "SCHEMA_UNKNOWN_FIELD",
            "unknown-component.json": "PROJECT_COMPONENT_UNKNOWN",
            "expired-exception.json": "EXCEPTION_EXPIRED",
            "mutable-oci.json": "OCI_DIGEST_REQUIRED",
            "semver-range.json": "PROJECT_VERSION_DRIFT",
        }
        for filename, code in expected.items():
            with self.subTest(filename=filename), self.assertRaises(ArchitectureError) as caught:
                self.build(ARCH / "fixtures/invalid" / filename)
            self.assertEqual(caught.exception.diagnostic.code, code)

    def test_schema_and_runtime_agree_on_unknown_field(self) -> None:
        project = load_json(ARCH / "fixtures/invalid/unknown-field.json")
        with self.assertRaises(ArchitectureError) as schema_error:
            validate_schema(project, self.project_schema)
        with self.assertRaises(ArchitectureError) as runtime_error:
            self.build(ARCH / "fixtures/invalid/unknown-field.json")
        self.assertEqual(schema_error.exception.diagnostic.code, runtime_error.exception.diagnostic.code)

    def test_catalog_negative_contracts_fail_closed(self) -> None:
        cases = []

        missing_source = deepcopy(self.catalog)
        del missing_source["components"][0]["provenance"]["source_url"]
        cases.append((missing_source, "SCHEMA_REQUIRED"))

        duplicate = deepcopy(self.catalog)
        duplicate["components"][1]["id"] = duplicate["components"][0]["id"]
        cases.append((duplicate, "CATALOG_COMPONENT_DUPLICATE"))

        unknown_state = deepcopy(self.catalog)
        unknown_state["components"][0]["state"] = "maybe"
        cases.append((unknown_state, "SCHEMA_ENUM"))

        mutable_version = deepcopy(self.catalog)
        mutable_version["components"][0]["version"] = "latest"
        cases.append((mutable_version, "VERSION_NOT_EXACT"))

        bad_dates = deepcopy(self.catalog)
        bad_dates["components"][0]["lifecycle"]["support_end"] = "2020-01-01"
        cases.append((bad_dates, "LIFECYCLE_DATE_ORDER"))

        for candidate, code in cases:
            with self.subTest(code=code), self.assertRaises(ArchitectureError) as caught:
                validate_catalog(candidate, self.catalog_schema, TODAY)
            self.assertEqual(caught.exception.diagnostic.code, code)


if __name__ == "__main__":
    unittest.main()
