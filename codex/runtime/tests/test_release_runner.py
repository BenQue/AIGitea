from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from aisoft_release.errors import DeploymentError, HostRoleError
from aisoft_release.runner import ReleaseRuntime

from tests.release_test_support import (
    FakeDocker,
    SHA_A,
    SHA_B,
    create_release,
    migration_identity,
    write_json,
)


class ReleaseRunnerTests(unittest.TestCase):
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

    def state(self) -> dict[str, object]:
        return json.loads((self.root / "state" / "state.json").read_text())

    def test_deploy_orders_transport_migration_up_and_persists_atomic_state(self) -> None:
        result = self.runtime.deploy(self.profile, SHA_A)
        self.assertEqual(result["action"], "deployed")
        state = self.state()
        self.assertEqual(state["current_release"], SHA_A)
        self.assertIsNone(state["previous_release"])
        self.assertEqual(
            state["migrations"][migration_identity(SHA_A)]["status"], "completed"
        )
        names = [str(event[0]) for event in self.docker.events]
        self.assertLess(names.index("capability"), names.index("pull"))
        self.assertLess(names.index("pull"), names.index("migration"))
        self.assertLess(names.index("tag"), names.index("migration"))
        self.assertLess(names.index("migration"), names.index("up"))
        migration_index = names.index("migration")
        self.assertTrue(
            any(
                event[0] == "inspect-image"
                and event[1] == "aisoft.local/admin/newemaint/migrate:" + SHA_A
                for event in self.docker.events[:migration_index]
            )
        )
        self.assertEqual((self.root / "state" / "state.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.root / "state").stat().st_mode & 0o777, 0o700)
        self.assertEqual(list((self.root / "state").glob("*.tmp")), [])

    def test_same_sha_healthy_deploy_is_noop_and_migration_runs_once(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        mutation_count = len(self.docker.mutations)
        result = self.runtime.deploy(self.profile, SHA_A)
        self.assertEqual(result["action"], "healthy-noop")
        self.assertEqual(len(self.docker.mutations), mutation_count)
        self.assertEqual(
            len([event for event in self.docker.events if event[0] == "migration"]), 1
        )

    def test_health_failure_restores_previous_release_without_database_restore(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.docker.unhealthy_for.add(SHA_B)
        with self.assertRaisesRegex(DeploymentError, "previous container release"):
            self.runtime.deploy(self.profile, SHA_B)
        state = self.state()
        self.assertEqual(state["current_release"], SHA_A)
        self.assertEqual(
            state["migrations"][migration_identity(SHA_B)]["status"], "completed"
        )
        up_releases = [event[1] for event in self.docker.events if event[0] == "up"]
        self.assertEqual(up_releases[-2:], [SHA_B, SHA_A])
        self.assertEqual(self.docker.current_release, SHA_A)

    def test_post_start_container_identity_toctou_mismatch_rolls_back(self) -> None:
        for mismatch in ("image-id", "config-image", "release-label"):
            with self.subTest(mismatch=mismatch), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile, model_a, manifest_a = create_release(root, SHA_A)
                _, model_b, manifest_b = create_release(root, SHA_B)
                docker = FakeDocker()
                docker.register(SHA_A, model_a, manifest_a)
                docker.register(SHA_B, model_b, manifest_b)
                runtime = ReleaseRuntime(docker, hostname="test-host")
                runtime.deploy(profile, SHA_A)
                if mismatch == "image-id":
                    docker.tamper_container_image_for.add(SHA_B)
                elif mismatch == "config-image":
                    docker.tamper_container_reference_for.add(SHA_B)
                else:
                    docker.tamper_container_release_label_for.add(SHA_B)
                with self.assertRaisesRegex(DeploymentError, "previous container release"):
                    runtime.deploy(profile, SHA_B)
                state = json.loads((root / "state" / "state.json").read_text())
                self.assertEqual(state["current_release"], SHA_A)
                self.assertEqual(
                    state["migrations"][migration_identity(SHA_B)]["status"],
                    "completed",
                )
                up_releases = [
                    event[1] for event in docker.events if event[0] == "up"
                ]
                self.assertEqual(up_releases[-2:], [SHA_B, SHA_A])

    def test_migration_failure_is_recorded_and_never_automatically_retried(self) -> None:
        self.docker.fail_migration_for.add(SHA_A)
        with self.assertRaisesRegex(DeploymentError, "automatic retry"):
            self.runtime.deploy(self.profile, SHA_A)
        state = self.state()
        self.assertEqual(
            state["migrations"][migration_identity(SHA_A)]["status"], "failed"
        )
        self.assertFalse(any(event[0] == "up" for event in self.docker.events))
        pull_count = len([event for event in self.docker.events if event[0] == "pull"])
        with self.assertRaisesRegex(DeploymentError, "automatic rerun"):
            self.runtime.deploy(self.profile, SHA_A)
        self.assertEqual(
            len([event for event in self.docker.events if event[0] == "pull"]), pull_count
        )

    def test_explicit_rollback_only_accepts_previous_and_does_not_run_migration(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        self.runtime.deploy(self.profile, SHA_B)
        migration_count = len(
            [event for event in self.docker.events if event[0] == "migration"]
        )
        result = self.runtime.rollback(self.profile, SHA_A)
        self.assertEqual(result["action"], "rolled-back")
        state = self.state()
        self.assertEqual(state["current_release"], SHA_A)
        self.assertEqual(state["previous_release"], SHA_B)
        self.assertEqual(
            len([event for event in self.docker.events if event[0] == "migration"]),
            migration_count,
        )
        self.assertEqual(result["database_restore"], "NOT_RUN_MANUAL_ONLY")

    def test_scm_ci_role_can_verify_but_cannot_deploy_before_docker_call(self) -> None:
        profile = json.loads(self.profile.read_text())
        profile["host_role"] = "scm-ci"
        write_json(self.profile, profile, mode=0o600)
        self.assertTrue(self.runtime.verify(self.profile, SHA_A)["ok"])
        self.docker.events.clear()
        with self.assertRaises(HostRoleError):
            self.runtime.deploy(self.profile, SHA_A)
        self.assertEqual(self.docker.events, [])

    def test_hostname_mismatch_fails_before_docker_call(self) -> None:
        other = ReleaseRuntime(self.docker, hostname="wrong-host")
        with self.assertRaises(HostRoleError):
            other.deploy(self.profile, SHA_A)
        self.assertEqual(self.docker.events, [])

    def test_status_checks_exact_release_and_secret_marker_is_not_persisted(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        status = self.runtime.status(self.profile, SHA_A)
        self.assertTrue(status["ok"])
        serialized = (self.root / "state" / "state.json").read_text()
        self.assertNotIn("fixture-value", serialized)
        self.assertNotIn("fixture-value", json.dumps(self.docker.events))
        self.docker.unhealthy_for.add(SHA_A)
        self.assertFalse(self.runtime.status(self.profile, SHA_A)["ok"])


if __name__ == "__main__":
    unittest.main()
