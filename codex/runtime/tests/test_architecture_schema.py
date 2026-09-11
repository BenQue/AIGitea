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
TODAY = date(2026, 9, 5)


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
        self.assertEqual(len(components), 31)
        profile_ids = []
        for path in sorted((ARCH / "profiles").glob("*.json")):
            profile = load_json(path)
            validate_profile(profile, self.profile_schema, self.catalog, components)
            profile_ids.append(profile["profile_id"])
        self.assertEqual(len(profile_ids), 5)
        self.assertEqual(len(profile_ids), len(set(profile_ids)))

    def test_systemd_native_profile_has_no_container_or_frontend_slot(self) -> None:
        components = validate_catalog(self.catalog, self.catalog_schema, TODAY)
        profile = load_json(ARCH / "profiles/linux-node-systemd-postgres-v1.json")
        validate_profile(profile, self.profile_schema, self.catalog, components)
        self.assertEqual(profile["delivery_contracts"], ["systemd-native/v1"])
        slots = [item["component_id"] for item in profile["required_components"]]
        self.assertEqual(
            slots,
            [
                "os.ubuntu.24-04-4",
                "runtime.node.24",
                "package.npm.11",
                "database.postgresql.18",
                "toolchain.typescript.6",
                "framework.fastify.5",
                "orm.kysely.0-29",
            ],
        )
        # The point of this profile is still the slots it does not force. #154
        # deliberately added the framework and ORM slots so that Fastify and
        # Kysely majors show up as drift in a project lock; without a slot the
        # catalog entry is unreachable from the declaration side. A container,
        # OCI, proxy or frontend slot would still silently re-break the
        # systemd-native consumer this profile was created for, so those
        # categories stay pinned as excluded here.
        categories = {components[slot]["category"] for slot in slots}
        self.assertTrue(
            categories.isdisjoint(
                {
                    "container-engine",
                    "container-compose",
                    "oci-image",
                    "proxy",
                    "frontend",
                }
            )
        )
        fixture = load_json(ARCH / "fixtures/valid/linux-systemd-project.json")
        self.assertEqual(fixture["profile_id"], profile["profile_id"])
        self.assertEqual(fixture["delivery_contract"], "systemd-native/v1")

    def test_node_sqlite_profile_slots_and_multi_environment_contracts(self) -> None:
        components = validate_catalog(self.catalog, self.catalog_schema, TODAY)
        profile = load_json(ARCH / "profiles/linux-node-sqlite-v1.json")
        validate_profile(profile, self.profile_schema, self.catalog, components)
        slots = [item["component_id"] for item in profile["required_components"]]
        self.assertEqual(
            slots,
            [
                "os.ubuntu.24-04-4",
                "runtime.node.24",
                "package.npm.11",
                "database.sqlite.3",
                "framework.next.16",
                "frontend.react.19",
                "orm.prisma.7",
                "toolchain.typescript.6",
            ],
        )
        # The profile exists because no other one pairs an embedded database
        # with a frontend framework. Forcing a client-server database, a proxy
        # or a container runtime would re-break exactly the shape it was
        # created for, so those categories stay excluded.
        categories = {components[slot]["category"] for slot in slots}
        self.assertTrue(
            categories.isdisjoint(
                {"container-engine", "container-compose", "oci-image", "proxy"}
            )
        )
        self.assertNotIn("database.postgresql.18", slots)

        # 裁决 A: one repository whose environments differ in delivery
        # ownership writes one declaration per environment, each naming a
        # single contract, rather than one declaration naming several.
        self.assertEqual(
            profile["delivery_contracts"],
            ["embedded-sqlite/v1", "pm2-legacy", "docker-release/v1"],
        )
        contracts = set()
        for name in ("node-sqlite-native-project", "node-sqlite-container-project"):
            fixture = load_json(ARCH / f"fixtures/valid/{name}.json")
            self.assertEqual(fixture["profile_id"], profile["profile_id"])
            self.assertIsInstance(fixture["delivery_contract"], str)
            self.assertIn(fixture["delivery_contract"], profile["delivery_contracts"])
            contracts.add(fixture["delivery_contract"])
        self.assertEqual(contracts, {"pm2-legacy", "docker-release/v1"})

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

    def test_react_stable_release_contract_fails_closed(self) -> None:
        react_index = next(
            index
            for index, component in enumerate(self.catalog["components"])
            if component["id"] == "frontend.react.19"
        )

        unavailable = deepcopy(self.catalog)
        unavailable["components"][react_index]["version"] = "19.3.0"
        unavailable["components"][react_index]["pin"]["value"] = "19.3.0"

        canary = deepcopy(self.catalog)
        canary["components"][react_index]["package_release"]["channel"] = "canary"

        canary_version = deepcopy(self.catalog)
        canary_version["components"][react_index]["version"] = "19.3.0-canary-deadbeef"
        canary_version["components"][react_index]["pin"]["value"] = "19.3.0-canary-deadbeef"
        for package in canary_version["components"][react_index]["package_release"]["packages"]:
            package["version"] = "19.3.0-canary-deadbeef"
            package["registry_url"] = f"https://registry.npmjs.org/{package['name']}/19.3.0-canary-deadbeef"

        mutable = deepcopy(self.catalog)
        mutable["components"][react_index]["version"] = "latest"
        mutable["components"][react_index]["pin"]["value"] = "latest"

        range_pin = deepcopy(self.catalog)
        range_pin["components"][react_index]["pin"]["value"] = "^19.2.8"

        dom_mismatch = deepcopy(self.catalog)
        dom = next(
            package
            for package in dom_mismatch["components"][react_index]["package_release"]["packages"]
            if package["name"] == "react-dom"
        )
        dom["version"] = "19.2.7"
        dom["registry_url"] = "https://registry.npmjs.org/react-dom/19.2.7"

        missing_package = deepcopy(self.catalog)
        missing_package["components"][react_index]["package_release"]["packages"].pop()

        extra_package = deepcopy(self.catalog)
        extra_package["components"][react_index]["package_release"]["packages"].append(
            {
                "name": "react-server-dom-webpack",
                "version": "19.2.8",
                "registry_url": "https://registry.npmjs.org/react-server-dom-webpack/19.2.8",
                "integrity": "sha512-fixture",
                "released_at": "2026-07-21",
            }
        )

        cases = [
            (unavailable, "REACT_STABLE_RELEASE_UNAVAILABLE"),
            (canary, "REACT_RELEASE_CHANNEL_INVALID"),
            (canary_version, "REACT_PACKAGE_VERSION_NOT_EXACT"),
            (mutable, "VERSION_NOT_EXACT"),
            (range_pin, "PIN_NOT_IMMUTABLE"),
            (dom_mismatch, "REACT_DOM_VERSION_MISMATCH"),
            (missing_package, "REACT_PACKAGE_SET_INVALID"),
            (extra_package, "REACT_PACKAGE_SET_INVALID"),
        ]
        for candidate, code in cases:
            with self.subTest(code=code), self.assertRaises(ArchitectureError) as caught:
                validate_catalog(candidate, self.catalog_schema, TODAY)
            self.assertEqual(caught.exception.diagnostic.code, code)

    def test_next_stable_release_contract_fails_closed(self) -> None:
        next_index = next(
            index
            for index, component in enumerate(self.catalog["components"])
            if component["id"] == "framework.next.16"
        )

        missing_metadata = deepcopy(self.catalog)
        del missing_metadata["components"][next_index]["package_release"]

        old_version = deepcopy(self.catalog)
        old_version["components"][next_index]["version"] = "16.2.11"
        old_version["components"][next_index]["pin"]["value"] = "16.2.11"

        mutable_channel = deepcopy(self.catalog)
        mutable_channel["components"][next_index]["package_release"]["channel"] = "latest"

        canary = deepcopy(self.catalog)
        component = canary["components"][next_index]
        component["version"] = "16.3.1-canary.4"
        component["pin"]["value"] = "16.3.1-canary.4"
        package = component["package_release"]["packages"][0]
        package["version"] = "16.3.1-canary.4"
        package["registry_url"] = "https://registry.npmjs.org/next/16.3.1-canary.4"

        mutable_package = deepcopy(self.catalog)
        package = mutable_package["components"][next_index]["package_release"]["packages"][0]
        package["version"] = "latest"
        package["registry_url"] = "https://registry.npmjs.org/next/latest"

        extra_package = deepcopy(self.catalog)
        extra_package["components"][next_index]["package_release"]["packages"].append(
            {
                "name": "next-canary",
                "version": "16.3.0",
                "registry_url": "https://registry.npmjs.org/next-canary/16.3.0",
                "integrity": "sha512-fixture",
                "released_at": "2026-08-03",
            }
        )

        bad_registry = deepcopy(self.catalog)
        bad_registry["components"][next_index]["package_release"]["packages"][0][
            "registry_url"
        ] = "https://registry.npmjs.org/next/latest"

        future = deepcopy(self.catalog)
        future["components"][next_index]["package_release"]["retrieved_at"] = "2026-09-06"

        cases = [
            (missing_metadata, "NEXT_RELEASE_METADATA_REQUIRED"),
            (old_version, "NEXT_STABLE_RELEASE_UNAVAILABLE"),
            (mutable_channel, "NEXT_RELEASE_CHANNEL_INVALID"),
            (canary, "NEXT_PACKAGE_VERSION_NOT_EXACT"),
            (mutable_package, "NEXT_PACKAGE_VERSION_NOT_EXACT"),
            (extra_package, "NEXT_PACKAGE_SET_INVALID"),
            (bad_registry, "NEXT_REGISTRY_SOURCE_INVALID"),
            (future, "NEXT_RELEASE_FROM_FUTURE"),
        ]
        for candidate, code in cases:
            with self.subTest(code=code), self.assertRaises(ArchitectureError) as caught:
                validate_catalog(candidate, self.catalog_schema, TODAY)
            self.assertEqual(caught.exception.diagnostic.code, code)

    def test_prisma_stable_release_contract_fails_closed(self) -> None:
        prisma_index = next(
            index
            for index, component in enumerate(self.catalog["components"])
            if component["id"] == "orm.prisma.7"
        )

        old_version = deepcopy(self.catalog)
        old_version["components"][prisma_index]["version"] = "7.8.0"
        old_version["components"][prisma_index]["pin"]["value"] = "7.8.0"

        mutable_channel = deepcopy(self.catalog)
        mutable_channel["components"][prisma_index]["package_release"]["channel"] = "latest"

        client_mismatch = deepcopy(self.catalog)
        client = next(
            package
            for package in client_mismatch["components"][prisma_index]["package_release"]["packages"]
            if package["name"] == "@prisma/client"
        )
        client["version"] = "7.8.0"
        client["registry_url"] = "https://registry.npmjs.org/%40prisma%2Fclient/7.8.0"

        missing_package = deepcopy(self.catalog)
        missing_package["components"][prisma_index]["package_release"]["packages"].pop()

        canary = deepcopy(self.catalog)
        adapter = next(
            package
            for package in canary["components"][prisma_index]["package_release"]["packages"]
            if package["name"] == "@prisma/adapter-pg"
        )
        adapter["version"] = "7.10.0-dev.49"
        adapter["registry_url"] = "https://registry.npmjs.org/%40prisma%2Fadapter-pg/7.10.0-dev.49"

        bad_registry = deepcopy(self.catalog)
        client = next(
            package
            for package in bad_registry["components"][prisma_index]["package_release"]["packages"]
            if package["name"] == "@prisma/client"
        )
        client["registry_url"] = "https://registry.npmjs.org/@prisma/client/7.9.1"

        future = deepcopy(self.catalog)
        future["components"][prisma_index]["package_release"]["packages"][0][
            "released_at"
        ] = "2026-09-06"

        cases = [
            (old_version, "PRISMA_PACKAGE_VERSION_MISMATCH"),
            (mutable_channel, "PRISMA_RELEASE_CHANNEL_INVALID"),
            (client_mismatch, "PRISMA_PACKAGE_VERSION_MISMATCH"),
            (missing_package, "PRISMA_PACKAGE_SET_INVALID"),
            (canary, "PRISMA_PACKAGE_VERSION_NOT_EXACT"),
            (bad_registry, "PRISMA_REGISTRY_SOURCE_INVALID"),
            (future, "PRISMA_RELEASE_FROM_FUTURE"),
        ]
        for candidate, code in cases:
            with self.subTest(code=code), self.assertRaises(ArchitectureError) as caught:
                validate_catalog(candidate, self.catalog_schema, TODAY)
            self.assertEqual(caught.exception.diagnostic.code, code)


if __name__ == "__main__":
    unittest.main()
