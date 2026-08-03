from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from aisoft_release.compose import validate_compose_model
from aisoft_release.contract import load_release_files, load_target_profile
from aisoft_release.errors import ContractError

from tests.release_test_support import (
    SHA_A,
    compose_model,
    create_release,
    fixture_path,
    refresh_architecture_lock_sha,
    repository_root,
    sha256,
    update_manifest,
    write_json,
)


class ReleaseSchemaTests(unittest.TestCase):
    def test_schema_files_are_strict_json_schema_objects(self) -> None:
        schema_root = repository_root() / "docker-release" / "schema"
        names = (
            "release-manifest-v1.schema.json",
            "target-profile-v1.schema.json",
            "offline-inventory-v1.schema.json",
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
        self.assertEqual(files.manifest.platform, "linux/amd64")
        self.assertEqual(files.architecture_lock["profile_id"], "linux-node-postgres-v1")
        self.assertEqual(files.manifest.runtime_services, ("web",))

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
            "destructive migration": lambda value: value["migration"].update(
                {"destructive": True}
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
        value["project_id"] = "tampered-project"
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


class ComposeSecurityTests(unittest.TestCase):
    def test_valid_compose_model_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, model, _ = create_release(root)
            manifest = load_release_files(load_target_profile(profile_path), SHA_A).manifest
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
