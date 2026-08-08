from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

from aisoft_release.errors import ContractError, DeploymentError, StateError
from aisoft_release.runner import ReleaseRuntime
from aisoft_release.state import STATE_VERSION_V2, StateStore

from tests.release_test_support import (
    FakeDocker,
    SHA_A,
    SHA_B,
    create_release,
    migration_identity,
    write_json,
)


class ReleasePhaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.profile, model_a, manifest_a = create_release(self.root, SHA_A)
        _, model_b, manifest_b = create_release(self.root, SHA_B)
        self.docker = FakeDocker()
        self.docker.register(SHA_A, model_a, manifest_a)
        self.docker.register(SHA_B, model_b, manifest_b)
        self.runtime = ReleaseRuntime(self.docker, hostname="test-host")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @property
    def release_root(self) -> Path:
        return self.root / "releases"

    def state(self) -> dict[str, object]:
        return json.loads((self.root / "state" / "state.json").read_text())

    def mutation_names(self) -> list[str]:
        return [str(event[0]) for event in self.docker.mutations]

    def test_artifact_verification_has_zero_docker_calls_or_target_inputs(self) -> None:
        self.profile.unlink()
        (self.root / "target.env").unlink()
        result = self.runtime.verify_artifact(self.release_root, SHA_A)
        self.assertEqual(result["action"], "verify-artifact")
        self.assertEqual(result["contract_version"], "docker-release/v2")
        self.assertEqual(result["target_facts"], "NOT_READ")
        self.assertEqual(self.docker.events, [])

    def test_artifact_tamper_fails_with_zero_docker_calls(self) -> None:
        model_path = self.release_root / SHA_A / "compose.model.json"
        model = json.loads(model_path.read_text())
        model["services"]["web"]["image"] = "unsafe:latest"
        write_json(model_path, model)
        with self.assertRaises(ContractError):
            self.runtime.verify_artifact(self.release_root, SHA_A)
        self.assertEqual(self.docker.events, [])

    def test_target_readiness_is_read_only_and_compares_producer_model(self) -> None:
        result = self.runtime.verify_target(self.profile, SHA_A)
        self.assertEqual(result["action"], "verify-target")
        self.assertEqual(
            [event[0] for event in self.docker.events], ["capability", "config"]
        )
        self.assertEqual(self.docker.mutations, [])

        self.docker.events.clear()
        self.docker.models[SHA_A] = deepcopy(self.docker.models[SHA_A])
        self.docker.models[SHA_A]["name"] = "drifted-project"
        with self.assertRaisesRegex(ContractError, "does not match producer"):
            self.runtime.verify_target(self.profile, SHA_A)
        self.assertEqual(self.docker.mutations, [])

    def test_stage_needs_no_env_and_has_zero_database_or_activation_calls(self) -> None:
        (self.root / "target.env").unlink()
        result = self.runtime.stage(self.profile, SHA_A)
        self.assertEqual(result["action"], "staged")
        names = self.mutation_names()
        self.assertIn("pull", names)
        self.assertIn("tag", names)
        self.assertNotIn("migration", names)
        self.assertNotIn("up", names)
        record = self.state()["staged_releases"][SHA_A]
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["transport"], "registry")
        self.assertEqual(set(record["image_ids"]), {"web", "migrate"})

    def test_stage_readiness_failure_has_zero_transport_or_later_mutations(self) -> None:
        self.docker.capability_error = DeploymentError("unsupported fake capability")
        with self.assertRaises(DeploymentError):
            self.runtime.stage(self.profile, SHA_A)
        self.assertEqual(self.docker.mutations, [])

    def test_migrate_requires_staging_and_never_stages_or_activates(self) -> None:
        with self.assertRaisesRegex(DeploymentError, "staging receipt"):
            self.runtime.migrate(self.profile, SHA_A)
        self.assertEqual(self.docker.mutations, [])

        self.runtime.stage(self.profile, SHA_A)
        self.docker.events.clear()
        result = self.runtime.migrate(self.profile, SHA_A)
        self.assertEqual(result["action"], "migration-completed")
        self.assertEqual(self.mutation_names(), ["migration"])
        self.assertEqual(
            self.state()["migrations"][migration_identity(SHA_A)]["status"],
            "completed",
        )

    def test_activate_requires_receipts_and_has_no_transport_or_migration_calls(self) -> None:
        self.runtime.stage(self.profile, SHA_A)
        self.docker.events.clear()
        with self.assertRaisesRegex(DeploymentError, "migration receipt"):
            self.runtime.activate(self.profile, SHA_A)
        self.assertEqual(self.docker.mutations, [])

        self.runtime.migrate(self.profile, SHA_A)
        self.docker.events.clear()
        result = self.runtime.activate(self.profile, SHA_A)
        self.assertEqual(result["action"], "activated")
        self.assertEqual(self.mutation_names(), ["up"])
        self.assertEqual(self.state()["current_release"], SHA_A)

    def test_v2_rollback_uses_recorded_local_images_without_transport_or_migration(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        self.docker.events.clear()
        result = self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(result["action"], "rolled-back")
        self.assertEqual(self.mutation_names(), ["up"])

    def test_phase_activation_failure_rolls_back_without_transport_or_migration(self) -> None:
        self.runtime.stage(self.profile, SHA_A)
        self.runtime.migrate(self.profile, SHA_A)
        self.runtime.activate(self.profile, SHA_A)
        self.runtime.stage(self.profile, SHA_B)
        self.runtime.migrate(self.profile, SHA_B)
        self.docker.events.clear()
        self.docker.unhealthy_for.add(SHA_B)
        with self.assertRaisesRegex(DeploymentError, "previous container release"):
            self.runtime.activate(self.profile, SHA_B)
        self.assertEqual(self.mutation_names(), ["up", "up"])
        self.assertEqual(self.state()["current_release"], SHA_A)

    def test_legacy_v1_remains_available_only_through_compatibility_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model, manifest = create_release(
                root, SHA_A, contract_version="docker-release/v1"
            )
            docker = FakeDocker()
            docker.register(SHA_A, model, manifest)
            runtime = ReleaseRuntime(docker, hostname="test-host")
            self.assertTrue(runtime.verify(profile, SHA_A)["ok"])
            docker.events.clear()
            with self.assertRaisesRegex(ContractError, "requires docker-release/v2"):
                runtime.verify_artifact(root / "releases", SHA_A)
            self.assertEqual(docker.events, [])

    def test_legacy_v1_rollback_retains_transport_prepare_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile, model_a, manifest_a = create_release(
                root, SHA_A, contract_version="docker-release/v1"
            )
            _, model_b, manifest_b = create_release(
                root, SHA_B, contract_version="docker-release/v1"
            )
            docker = FakeDocker()
            docker.register(SHA_A, model_a, manifest_a)
            docker.register(SHA_B, model_b, manifest_b)
            runtime = ReleaseRuntime(docker, hostname="test-host")
            runtime.deploy(profile, SHA_A)
            runtime.deploy(profile, SHA_B)
            docker.events.clear()
            runtime.rollback(profile, SHA_A)
            self.assertIn("pull", [event[0] for event in docker.mutations])
            self.assertNotIn("migration", [event[0] for event in docker.mutations])


class ReleaseStateMigrationTests(unittest.TestCase):
    def test_v1_state_is_deterministically_loaded_as_v2(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.mkdir(exist_ok=True)
            os.chmod(root, 0o700)
            write_json(
                root / "state.json",
                {
                    "contract_version": "docker-release-state/v1",
                    "profile_id": "newemaint-test",
                    "current_release": SHA_A,
                    "previous_release": None,
                    "migrations": {},
                    "last_result": "deployed",
                },
                mode=0o600,
            )
            value = StateStore(root, "newemaint-test").load()
            self.assertEqual(value["contract_version"], STATE_VERSION_V2)
            self.assertEqual(value["staged_releases"], {})

    def test_malformed_staging_receipt_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.mkdir(exist_ok=True)
            os.chmod(root, 0o700)
            store = StateStore(root, "newemaint-test")
            value = store.empty()
            value["staged_releases"] = {
                SHA_A: {
                    "status": "completed",
                    "transport": "registry",
                    "image_ids": {"web": "sha256:" + "x" * 64},
                }
            }
            with self.assertRaisesRegex(StateError, "image_id"):
                store.save(value)


if __name__ == "__main__":
    unittest.main()
