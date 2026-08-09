from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from aisoft_release.compose import validate_compose_model
from aisoft_release.contract import (
    load_offline_inventory,
    load_release_files,
    load_target_profile,
    runtime_image_reference,
)
from aisoft_release.errors import ContractError

from tests.release_test_support import (
    SHA_A,
    compose_model,
    create_release,
    fixture_path,
    refresh_architecture_lock_sha,
    repository_root,
    sha256,
    update_compose_model,
    update_manifest,
    write_json,
)


class ReleaseSchemaTests(unittest.TestCase):
    def test_schema_files_are_strict_json_schema_objects(self) -> None:
        schema_root = repository_root() / "docker-release" / "schema"
        names = (
            "release-manifest-v1.schema.json",
            "release-manifest-v2.schema.json",
            "target-profile-v1.schema.json",
            "offline-inventory-v1.schema.json",
            "offline-inventory-v2.schema.json",
            "image-store-compatibility-v1.schema.json",
            "state-v2.schema.json",
            "command-gate-v1.schema.json",
        )
        for name in names:
            with self.subTest(name=name):
                value = json.loads((schema_root / name).read_text())
                self.assertEqual(value["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertFalse(value["additionalProperties"])


class ReleaseContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.profile_path, self.model, self.manifest = create_release(self.root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @property
    def release_dir(self) -> Path:
        return self.root / "releases" / SHA_A

    def test_valid_profile_manifest_and_architecture_lock_load(self) -> None:
        profile = load_target_profile(self.profile_path)
        files = load_release_files(profile, SHA_A)
        self.assertEqual(files.manifest.release_id, SHA_A)
        self.assertEqual(files.manifest.contract_version, "docker-release/v2")
        self.assertEqual(
            files.manifest.architecture_project_id,
            "newemaint-target-candidate",
        )
        self.assertEqual(files.compose_model, self.model)
        self.assertEqual(files.manifest.platform, "linux/amd64")
        self.assertEqual(files.architecture_lock["profile_id"], "linux-node-postgres-v1")
        self.assertEqual(files.manifest.runtime_services, ("web",))
        self.assertEqual(
            files.manifest.images[0].runtime_reference,
            "aisoft.local/admin/newemaint/web:" + SHA_A,
        )
        self.assertEqual(
            files.manifest.offline_bundle.contract_version,
            "docker-release-offline-bundle/v2",
        )
        inventory = load_offline_inventory(files)
        self.assertEqual(inventory["contract_version"], "docker-release-offline-inventory/v2")

    def test_legacy_registry_manifest_remains_strictly_readable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, _, _ = create_release(
                root, migration=False, identity_version="legacy"
            )
            files = load_release_files(load_target_profile(profile_path), SHA_A)
            image = files.manifest.images[0]
            self.assertFalse(image.is_v2)
            self.assertEqual(image.runtime_reference, image.reference)
            self.assertIsNone(files.manifest.offline_bundle.contract_version)

    def test_runtime_tag_is_deterministic_and_rejects_unsafe_components(self) -> None:
        self.assertEqual(
            runtime_image_reference("admin/NewEmaint", "web", SHA_A),
            "aisoft.local/admin/newemaint/web:" + SHA_A,
        )
        for repository, service in (
            ("admin/NewEmaint", "unsafe_"),
            ("admin/unsafe--repo", "web"),
        ):
            with self.subTest(repository=repository, service=service), self.assertRaises(
                ContractError
            ):
                runtime_image_reference(repository, service, SHA_A)

    def test_legacy_profile_without_optional_architecture_project_id_loads(self) -> None:
        value = json.loads(self.profile_path.read_text())
        value.pop("architecture_project_id")
        write_json(self.profile_path, value, mode=0o600)
        profile = load_target_profile(self.profile_path)
        self.assertIsNone(profile.architecture_project_id)
        self.assertEqual(load_release_files(profile, SHA_A).manifest.release_id, SHA_A)

    def test_profile_requires_private_mode_and_rejects_unknown_fields(self) -> None:
        os.chmod(self.profile_path, 0o644)
        with self.assertRaisesRegex(ContractError, "0400 or 0600"):
            load_target_profile(self.profile_path)
        os.chmod(self.profile_path, 0o600)
        profile = json.loads(self.profile_path.read_text())
        profile["extra"] = True
        write_json(self.profile_path, profile, mode=0o600)
        with self.assertRaisesRegex(ContractError, "unknown fields"):
            load_target_profile(self.profile_path)

    def test_profile_paths_must_be_absolute_separate_and_normalized(self) -> None:
        value = json.loads(self.profile_path.read_text())
        value["state_root"] = value["release_root"] + "/state"
        write_json(self.profile_path, value, mode=0o600)
        with self.assertRaisesRegex(ContractError, "must not overlap"):
            load_target_profile(self.profile_path)

    def test_duplicate_json_field_is_rejected(self) -> None:
        path = self.release_dir / "release.json"
        raw = path.read_text()
        needle = f'"release_id":"{SHA_A}"'
        path.write_text(raw.replace(needle, needle + "," + needle, 1))
        os.chmod(path, 0o644)
        profile = load_target_profile(self.profile_path)
        with self.assertRaisesRegex(ContractError, "duplicate JSON field"):
            load_release_files(profile, SHA_A)

    def test_invalid_manifest_variants_fail_closed(self) -> None:
        variants = {
            "unknown field": lambda value: value.update({"extra": True}),
            "mutable image": lambda value: value["images"][0].update(
                {"reference": "registry.internal/admin/newemaint-web:latest"}
            ),
            "duplicate service": lambda value: value["images"].append(
                deepcopy(value["images"][0])
            ),
            "path traversal": lambda value: value["compose"].update(
                {"path": "../compose.yaml"}
            ),
            "merge mismatch": lambda value: value.update({"merge_sha": "b" * 40}),
            "checksum mismatch": lambda value: value["compose"].update(
                {"sha256": "0" * 64}
            ),
            "architecture mismatch": lambda value: value["architecture"].update(
                {"profile_id": "different-profile"}
            ),
            "missing architecture project": lambda value: value["architecture"].pop(
                "project_id"
            ),
            "destructive migration": lambda value: value["migration"].update(
                {"destructive": True}
            ),
            "transport release mismatch": lambda value: value["images"][0].update(
                {
                    "transport_reference": "aisoft.local/admin/newemaint/web:"
                    + "b" * 40
                }
            ),
            "runtime transport mismatch": lambda value: value["images"][0].update(
                {
                    "runtime_reference": "aisoft.local/admin/newemaint/other:"
                    + SHA_A
                }
            ),
            "duplicate image id": lambda value: value["images"][1].update(
                {"image_id": value["images"][0]["image_id"]}
            ),
            "mixed v2 legacy image": lambda value: value["images"][0].pop(
                "transport_reference"
            ),
            "v2 images with legacy bundle": lambda value: value["offline_bundle"].pop(
                "contract_version"
            ),
            "unknown offline contract": lambda value: value["offline_bundle"].update(
                {"contract_version": "docker-release-offline-bundle/v3"}
            ),
        }
        for name, transform in variants.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile_path, _, _ = create_release(root)
                update_manifest(root / "releases" / SHA_A, transform)
                profile = load_target_profile(profile_path)
                with self.assertRaises(ContractError):
                    load_release_files(profile, SHA_A)

    def test_missing_or_tampered_architecture_lock_fails(self) -> None:
        profile = load_target_profile(self.profile_path)
        self.release_dir.joinpath("architecture.lock.json").unlink()
        with self.assertRaises(ContractError):
            load_release_files(profile, SHA_A)

    def test_release_directory_rejects_undeclared_dotenv_or_extra_files(self) -> None:
        extra = self.release_dir / ".env"
        extra.write_text("DATABASE_URL=must-not-be-packaged\n")
        os.chmod(extra, 0o600)
        profile = load_target_profile(self.profile_path)
        with self.assertRaisesRegex(ContractError, "undeclared file"):
            load_release_files(profile, SHA_A)

    def test_architecture_lock_profile_and_catalog_are_cross_checked(self) -> None:
        lock_path = self.release_dir / "architecture.lock.json"
        value = json.loads(lock_path.read_text())
        value["catalog_revision"] = "2026.08.1"
        refresh_architecture_lock_sha(value)
        write_json(lock_path, value)
        update_manifest(
            self.release_dir,
            lambda manifest: manifest["architecture"].update(
                {"sha256": sha256(lock_path)}
            ),
        )
        profile = load_target_profile(self.profile_path)
        with self.assertRaisesRegex(ContractError, "catalog_revision"):
            load_release_files(profile, SHA_A)

    def test_architecture_lock_self_hash_is_verified(self) -> None:
        lock_path = self.release_dir / "architecture.lock.json"
        value = json.loads(lock_path.read_text())
        value["source_checksums"]["catalog_sha256"] = "0" * 64
        write_json(lock_path, value)
        update_manifest(
            self.release_dir,
            lambda manifest: manifest["architecture"].update(
                {"sha256": sha256(lock_path)}
            ),
        )
        profile = load_target_profile(self.profile_path)
        with self.assertRaisesRegex(ContractError, "lock_sha256"):
            load_release_files(profile, SHA_A)

    def test_architecture_lock_project_id_is_bound_by_target_profile(self) -> None:
        lock_path = self.release_dir / "architecture.lock.json"
        value = json.loads(lock_path.read_text())
        value["project_id"] = "substituted-project"
        refresh_architecture_lock_sha(value)
        write_json(lock_path, value)
        update_manifest(
            self.release_dir,
            lambda manifest: manifest["architecture"].update(
                {"sha256": sha256(lock_path)}
            ),
        )
        profile = load_target_profile(self.profile_path)
        with self.assertRaisesRegex(ContractError, "project_id"):
            load_release_files(profile, SHA_A)

    def test_architecture_lock_delivery_contract_is_cross_checked(self) -> None:
        lock_path = self.release_dir / "architecture.lock.json"
        value = json.loads(lock_path.read_text())
        value["delivery_contract"] = "pm2-legacy"
        refresh_architecture_lock_sha(value)
        write_json(lock_path, value)
        update_manifest(
            self.release_dir,
            lambda manifest: manifest["architecture"].update(
                {"sha256": sha256(lock_path)}
            ),
        )
        profile = load_target_profile(self.profile_path)
        with self.assertRaisesRegex(ContractError, "delivery_contract"):
            load_release_files(profile, SHA_A)

    def test_architecture_lock_source_url_rejects_credentials(self) -> None:
        lock_path = self.release_dir / "architecture.lock.json"
        value = json.loads(lock_path.read_text())
        value["resolved_components"][0]["source_url"] = (
            "https://user:password@example.invalid/source"
        )
        refresh_architecture_lock_sha(value)
        write_json(lock_path, value)
        update_manifest(
            self.release_dir,
            lambda manifest: manifest["architecture"].update(
                {"sha256": sha256(lock_path)}
            ),
        )
        profile = load_target_profile(self.profile_path)
        with self.assertRaisesRegex(ContractError, "must not contain credentials"):
            load_release_files(profile, SHA_A)

    def test_sensitive_environment_keys_allow_strict_external_references(self) -> None:
        update_compose_model(
            self.release_dir,
            lambda model: model["services"]["web"].update(
                {
                    "environment": {
                        "JWT_SECRET": "${JWT_SECRET:?required}",
                        "DATABASE_URL": "${DATABASE_URL:?required}",
                    }
                }
            ),
        )
        files = load_release_files(load_target_profile(self.profile_path), SHA_A)
        self.assertEqual(
            files.compose_model["services"]["web"]["environment"]["JWT_SECRET"],
            "${JWT_SECRET:?required}",
        )

    def test_sensitive_environment_key_exceptions_fail_closed(self) -> None:
        variants = {
            "literal secret": {"JWT_SECRET": "embedded-secret"},
            "literal password": {"DATABASE_PASSWORD": "embedded-password"},
            "literal token": {"API_TOKEN": "embedded-token"},
            "null sensitive value": {"JWT_SECRET": None},
            "default literal": {"JWT_SECRET": "${JWT_SECRET:-embedded}"},
            "alternate literal": {"JWT_SECRET": "${JWT_SECRET:+embedded}"},
        }
        for name, environment in variants.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile_path, _, _ = create_release(root)
                release_dir = root / "releases" / SHA_A
                update_compose_model(
                    release_dir,
                    lambda model, value=environment: model["services"]["web"].update(
                        {"environment": value}
                    ),
                )
                with self.assertRaisesRegex(ContractError, "forbidden sensitive field"):
                    load_release_files(load_target_profile(profile_path), SHA_A)

    def test_sensitive_field_outside_environment_remains_forbidden(self) -> None:
        update_compose_model(
            self.release_dir,
            lambda model: model["services"]["web"].update(
                {"api_secret": "${API_SECRET:?required}"}
            ),
        )
        with self.assertRaisesRegex(
            ContractError, r"services\.web\.api_secret"
        ):
            load_release_files(load_target_profile(self.profile_path), SHA_A)

    def test_non_compose_sensitive_field_boundaries_remain_forbidden(self) -> None:
        with self.subTest(context="target profile"), tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, _, _ = create_release(root)
            profile = json.loads(profile_path.read_text())
            profile["api_token"] = "${API_TOKEN:?required}"
            write_json(profile_path, profile, mode=0o600)
            with self.assertRaisesRegex(ContractError, "target profile.*api_token"):
                load_target_profile(profile_path)

        with self.subTest(context="release manifest"), tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, _, _ = create_release(root)
            update_manifest(
                root / "releases" / SHA_A,
                lambda manifest: manifest.update(
                    {"api_token": "${API_TOKEN:?required}"}
                ),
            )
            with self.assertRaisesRegex(ContractError, "release manifest.*api_token"):
                load_release_files(load_target_profile(profile_path), SHA_A)

        with self.subTest(context="architecture lock"), tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, _, _ = create_release(root)
            release_dir = root / "releases" / SHA_A
            lock_path = release_dir / "architecture.lock.json"
            lock = json.loads(lock_path.read_text())
            lock["api_token"] = "${API_TOKEN:?required}"
            write_json(lock_path, lock)
            update_manifest(
                release_dir,
                lambda manifest: manifest["architecture"].update(
                    {"sha256": sha256(lock_path)}
                ),
            )
            with self.assertRaisesRegex(ContractError, "architecture lock.*api_token"):
                load_release_files(load_target_profile(profile_path), SHA_A)

        with self.subTest(context="offline inventory"), tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, _, _ = create_release(root)
            release_dir = root / "releases" / SHA_A
            inventory_path = release_dir / "images.inventory.json"
            inventory = json.loads(inventory_path.read_text())
            inventory["api_token"] = "${API_TOKEN:?required}"
            write_json(inventory_path, inventory)
            update_manifest(
                release_dir,
                lambda manifest: manifest["offline_bundle"].update(
                    {"inventory_sha256": sha256(inventory_path)}
                ),
            )
            files = load_release_files(load_target_profile(profile_path), SHA_A)
            with self.assertRaisesRegex(ContractError, "offline inventory.*api_token"):
                load_offline_inventory(files)


class ComposeSecurityTests(unittest.TestCase):
    def test_valid_compose_model_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, model, _ = create_release(root)
            manifest = load_release_files(load_target_profile(profile_path), SHA_A).manifest
            validate_compose_model(model, manifest)

    def test_sensitive_environment_keys_with_strict_references_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, model, _ = create_release(root)
            manifest = load_release_files(load_target_profile(profile_path), SHA_A).manifest
            model["services"]["web"]["environment"] = {
                "JWT_SECRET": "${JWT_SECRET:?required}",
                "DATABASE_URL": "${DATABASE_URL}",
            }
            validate_compose_model(model, manifest)

    def test_unsafe_compose_variants_are_rejected(self) -> None:
        variants = {
            "build": lambda model: model["services"]["web"].update(
                {"build": {"context": "."}}
            ),
            "privileged": lambda model: model["services"]["web"].update(
                {"privileged": True}
            ),
            "root": lambda model: model["services"]["web"].update({"user": "0:0"}),
            "interpolated user": lambda model: model["services"]["web"].update(
                {"user": "${APP_UID}"}
            ),
            "socket": lambda model: model["services"]["web"].update(
                {"volumes": ["/var/run/docker.sock:/var/run/docker.sock"]}
            ),
            "public port": lambda model: model["services"]["web"].update(
                {"ports": [{"published": "3000", "target": 3000}]}
            ),
            "health": lambda model: model["services"]["web"].pop("healthcheck"),
            "read only": lambda model: model["services"]["web"].update(
                {"read_only": False}
            ),
            "writable storage": lambda model: model["services"]["web"].pop("tmpfs"),
            "literal environment": lambda model: model["services"]["web"].update(
                {"environment": {"DATABASE_URL": "postgresql://embedded"}}
            ),
            "literal secret": lambda model: model["services"]["web"].update(
                {"environment": {"JWT_SECRET": "embedded-secret"}}
            ),
            "literal token": lambda model: model["services"]["web"].update(
                {"environment": {"API_TOKEN": "embedded-token"}}
            ),
            "literal password": lambda model: model["services"]["web"].update(
                {"environment": {"DATABASE_PASSWORD": "embedded-password"}}
            ),
            "unsafe default": lambda model: model["services"]["web"].update(
                {"environment": {"JWT_SECRET": "${JWT_SECRET:-embedded}"}}
            ),
            "unsafe alternate": lambda model: model["services"]["web"].update(
                {"environment": {"JWT_SECRET": "${JWT_SECRET:+embedded}"}}
            ),
            "null sensitive value": lambda model: model["services"]["web"].update(
                {"environment": {"JWT_SECRET": None}}
            ),
            "sensitive field outside environment": lambda model: model["services"][
                "web"
            ].update({"api_secret": "${API_SECRET:?required}"}),
            "capabilities": lambda model: model["services"]["web"].update(
                {"cap_drop": []}
            ),
            "resources": lambda model: model["services"]["web"].pop("deploy"),
            "logging": lambda model: model["services"]["web"].pop("logging"),
            "release label": lambda model: model["services"]["web"]["labels"].update(
                {"com.aisoft.release.id": "b" * 40}
            ),
            "network partition": lambda model: model.update(
                {"networks": {"edge": {"internal": False}}}
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, _, _ = create_release(root)
            manifest = load_release_files(load_target_profile(profile_path), SHA_A).manifest
            for name, transform in variants.items():
                with self.subTest(name=name):
                    model = compose_model(SHA_A)
                    transform(model)
                    with self.assertRaises(ContractError):
                        validate_compose_model(model, manifest)


if __name__ == "__main__":
    unittest.main()
