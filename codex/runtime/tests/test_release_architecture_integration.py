from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from aisoft_architecture.jsonio import load_json
from aisoft_architecture.lockfile import build_lock, validate_lock
from aisoft_release.contract import load_release_files, load_target_profile
from aisoft_release.errors import ContractError

from tests.release_test_support import (
    SHA_A,
    create_release,
    refresh_architecture_lock_sha,
    repository_root,
    sha256,
    update_manifest,
    write_json,
)


class ArchitectureReleaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.architecture_root = repository_root() / "architecture"
        cls.catalog = load_json(cls.architecture_root / "catalog.json")
        cls.catalog_schema = load_json(
            cls.architecture_root / "schemas/catalog-v1.schema.json"
        )
        cls.profile = load_json(
            cls.architecture_root / "profiles/linux-node-postgres-v1.json"
        )
        cls.profile_schema = load_json(
            cls.architecture_root / "schemas/profile-v1.schema.json"
        )
        cls.project = load_json(
            cls.architecture_root / "reference/newemaint/architecture.json"
        )
        cls.project_schema = load_json(
            cls.architecture_root / "schemas/project-architecture-v1.schema.json"
        )
        cls.lock_schema = load_json(
            cls.architecture_root / "schemas/architecture-lock-v1.schema.json"
        )

    def test_canonical_architecture_lock_round_trips_into_release(self) -> None:
        generated = build_lock(
            self.catalog,
            self.catalog_schema,
            self.profile,
            self.profile_schema,
            self.project,
            self.project_schema,
            date(2026, 8, 3),
        )
        reference = load_json(
            self.architecture_root / "reference/newemaint/architecture.lock.json"
        )
        self.assertEqual(generated, reference)
        validate_lock(reference, self.lock_schema, generated)

        with tempfile.TemporaryDirectory() as directory:
            profile_path, _, _ = create_release(Path(directory))
            files = load_release_files(load_target_profile(profile_path), SHA_A)
            self.assertEqual(dict(files.architecture_lock), generated)
            self.assertEqual(
                files.architecture_lock["delivery_contract"], "docker-release/v1"
            )
            self.assertEqual(
                files.architecture_lock["catalog_revision"],
                self.catalog["revision"],
            )

    def test_valid_self_hash_cannot_hide_unknown_lock_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path, _, _ = create_release(root)
            lock_path = root / "releases" / SHA_A / "architecture.lock.json"
            lock = json.loads(lock_path.read_text())
            lock["extra"] = "not-governed"
            refresh_architecture_lock_sha(lock)
            write_json(lock_path, lock)
            update_manifest(
                lock_path.parent,
                lambda manifest: manifest["architecture"].update(
                    {"sha256": sha256(lock_path)}
                ),
            )
            with self.assertRaisesRegex(ContractError, "unknown fields"):
                load_release_files(load_target_profile(profile_path), SHA_A)


if __name__ == "__main__":
    unittest.main()
