from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from aisoft_release.contract import load_target_profile
from aisoft_release.errors import ContractError, DeploymentError, HostRoleError
from aisoft_release.runner import ReleaseRuntime, _host_role_preflight

from tests.release_test_support import (
    FakeDocker,
    SHA_A,
    SHA_B,
    create_release,
    migration_identity,
    write_json,
)

from tests.test_release_transport import CrossStoreDocker, replace_with_oci_archive


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

    def test_cross_store_status_revalidates_image_and_exact_container_identity(self):
        for drift in ("local-id", "local-digest", "local-tag", "container-id", "container-reference", "release-label", "service-label"):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                profile, model, manifest = create_release(root)
                release_dir = root / "releases" / SHA_A
                manifest = replace_with_oci_archive(release_dir, manifest, image_store="containerd")
                docker = CrossStoreDocker()
                docker.register_cross_store(SHA_A, model, manifest, release_dir)
                runtime = ReleaseRuntime(docker, hostname="test-host")
                runtime.stage(profile, SHA_A)
                runtime.migrate(profile, SHA_A)
                runtime.activate(profile, SHA_A)
                self.assertTrue(runtime.status(profile, SHA_A)["ok"])
                image = manifest["images"][0]
                local = docker.images[image["runtime_reference"]]
                if drift == "local-id":
                    local["Id"] = "sha256:" + "f" * 64
                elif drift == "local-digest":
                    local["RepoDigests"] = []
                elif drift == "local-tag":
                    local["RepoTags"] = []
                elif drift == "container-id":
                    original = docker.inspect_container
                    def stale(container_id):
                        # Source/native ID is graph-valid but differs from local config ID.
                        return {**original(container_id), "Image": image["image_id"]}
                    docker.inspect_container = stale
                elif drift == "container-reference":
                    docker.tamper_container_reference_for.add(SHA_A)
                elif drift == "release-label":
                    docker.tamper_container_release_label_for.add(SHA_A)
                else:
                    original = docker.inspect_container
                    def wrong_service(container_id):
                        value = original(container_id)
                        value["Config"]["Labels"]["com.aisoft.release.service"] = "other"
                        return value
                    docker.inspect_container = wrong_service
                mutations = len(docker.mutations)
                self.assertFalse(runtime.status(profile, SHA_A)["ok"])
                self.assertEqual(len(docker.mutations), mutations)

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
                current_profile = json.loads(self.profile.read_text())
                data = json.loads(profile.read_text())
                data.update(
                    host_role=current_profile["host_role"],
                    environment=current_profile["environment"],
                )
                write_json(profile, data, mode=0o600)
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

    def test_scm_ci_production_can_verify_but_cannot_deploy_before_docker_call(self) -> None:
        profile = json.loads(self.profile.read_text())
        profile["host_role"] = "scm-ci"
        profile["environment"] = "production"
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


class ScmCiReleaseRunnerTests(ReleaseRunnerTests):
    """Run the existing lifecycle and failure regressions on the co-located role."""

    def setUp(self) -> None:
        super().setUp()
        profile = json.loads(self.profile.read_text())
        profile.update(host_role="scm-ci", environment="test")
        write_json(self.profile, profile, mode=0o600)

    def test_explicit_phases_preserve_receipts_and_mutation_boundaries(self) -> None:
        with self.assertRaisesRegex(DeploymentError, "staging receipt"):
            self.runtime.migrate(self.profile, SHA_A)
        self.assertEqual(self.docker.mutations, [])
        self.assertEqual(self.runtime.stage(self.profile, SHA_A)["action"], "staged")
        self.docker.events.clear()
        with self.assertRaisesRegex(DeploymentError, "migration receipt"):
            self.runtime.activate(self.profile, SHA_A)
        self.assertEqual(self.docker.mutations, [])
        self.assertEqual(
            self.runtime.migrate(self.profile, SHA_A)["action"], "migration-completed"
        )
        self.assertEqual([event[0] for event in self.docker.mutations], ["migration"])
        self.docker.events.clear()
        self.assertEqual(self.runtime.activate(self.profile, SHA_A)["action"], "activated")
        self.assertEqual([event[0] for event in self.docker.mutations], ["up"])
        self.assertTrue(self.runtime.status(self.profile, SHA_A)["ok"])


class SharedMigrationIdentityTests(unittest.TestCase):
    """#305: the receipt answers "has this migration set run on this database".

    A release that ships no new migration declares the identity an earlier
    release already applied. Before this Issue, `migrate` and `activate` both
    compared the receipt's `release_id` to the current manifest and refused, so
    no such release could ever reach an already-deployed target -- which is most
    releases of a live project. The receipt's `release_id` is audit only: it
    records which release actually ran the migration.
    """

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.profile, model_a, manifest_a = create_release(self.root, SHA_A)
        _, model_b, manifest_b = create_release(
            self.root, SHA_B, shares_migration_with=SHA_A
        )
        self.identity = migration_identity(SHA_A)
        self.assertEqual(manifest_a["migration"]["identity"], self.identity)
        self.assertEqual(manifest_b["migration"]["identity"], self.identity)
        self.assertNotEqual(manifest_a["release_id"], manifest_b["release_id"])
        self.docker = FakeDocker()
        self.docker.register(SHA_A, model_a, manifest_a)
        self.docker.register(SHA_B, model_b, manifest_b)
        self.runtime = ReleaseRuntime(self.docker, hostname="test-host")

    def state(self) -> dict[str, object]:
        return json.loads((self.root / "state" / "state.json").read_text())

    def receipt(self) -> object:
        return self.state()["migrations"].get(self.identity)

    def migration_runs(self) -> list[object]:
        return [event for event in self.docker.events if event[0] == "migration"]

    def deploy_first_release(self) -> None:
        self.assertEqual(self.runtime.stage(self.profile, SHA_A)["action"], "staged")
        self.assertEqual(
            self.runtime.migrate(self.profile, SHA_A)["action"], "migration-completed"
        )
        self.assertEqual(self.runtime.activate(self.profile, SHA_A)["action"], "activated")
        self.assertEqual(self.receipt(), {"status": "completed", "release_id": SHA_A})

    def interrupt_first_migration(self) -> None:
        """Leave the receipt `started`: the process died inside the container run."""

        self.assertEqual(self.runtime.stage(self.profile, SHA_A)["action"], "staged")
        original = self.docker.run_migration

        def crash(*args: object, **kwargs: object) -> None:
            raise RuntimeError("interrupted before the migration reported an outcome")

        self.docker.run_migration = crash
        try:
            with self.assertRaises(RuntimeError):
                self.runtime.migrate(self.profile, SHA_A)
        finally:
            self.docker.run_migration = original
        self.assertEqual(self.receipt(), {"status": "started", "release_id": SHA_A})

    def fail_first_migration(self) -> None:
        self.assertEqual(self.runtime.stage(self.profile, SHA_A)["action"], "staged")
        self.docker.fail_migration_for.add(SHA_A)
        try:
            with self.assertRaisesRegex(DeploymentError, "migration failed"):
                self.runtime.migrate(self.profile, SHA_A)
        finally:
            self.docker.fail_migration_for.discard(SHA_A)
        self.assertEqual(self.receipt(), {"status": "failed", "release_id": SHA_A})

    def test_completed_receipt_makes_a_same_migration_release_a_noop(self) -> None:
        self.deploy_first_release()
        self.assertEqual(self.runtime.stage(self.profile, SHA_B)["action"], "staged")
        self.docker.events.clear()
        self.assertEqual(
            self.runtime.migrate(self.profile, SHA_B)["action"], "migration-noop"
        )
        # No migration container, no database write, and no state rewrite: the
        # receipt keeps naming the release that actually applied the migration.
        self.assertEqual(self.migration_runs(), [])
        self.assertEqual(self.docker.mutations, [])
        self.assertEqual(self.receipt(), {"status": "completed", "release_id": SHA_A})
        self.assertEqual(self.runtime.activate(self.profile, SHA_B)["action"], "activated")
        self.assertEqual([event[0] for event in self.docker.mutations], ["up"])
        self.assertEqual(self.receipt(), {"status": "completed", "release_id": SHA_A})
        state = self.state()
        self.assertEqual(state["current_release"], SHA_B)
        self.assertEqual(state["previous_release"], SHA_A)
        self.assertTrue(self.runtime.status(self.profile, SHA_B)["ok"])

    def test_uncertain_or_failed_receipt_still_refuses_a_same_migration_release(self) -> None:
        for status, arrange in (
            ("started", self.interrupt_first_migration),
            ("failed", self.fail_first_migration),
        ):
            with self.subTest(status=status):
                self.setUp()
                arrange()
                self.assertEqual(self.runtime.stage(self.profile, SHA_B)["action"], "staged")
                self.docker.events.clear()
                with self.assertRaisesRegex(DeploymentError, "uncertain or failed"):
                    self.runtime.migrate(self.profile, SHA_B)
                with self.assertRaisesRegex(DeploymentError, "completed exact migration receipt"):
                    self.runtime.activate(self.profile, SHA_B)
                self.assertEqual(self.migration_runs(), [])
                self.assertEqual(self.docker.mutations, [])
                self.assertEqual(self.receipt(), {"status": status, "release_id": SHA_A})

    def test_missing_receipt_still_refuses_activation_and_runs_the_migration(self) -> None:
        self.assertEqual(self.runtime.stage(self.profile, SHA_B)["action"], "staged")
        self.assertIsNone(self.receipt())
        self.docker.events.clear()
        with self.assertRaisesRegex(DeploymentError, "completed exact migration receipt"):
            self.runtime.activate(self.profile, SHA_B)
        self.assertEqual(self.docker.mutations, [])
        self.assertEqual(
            self.runtime.migrate(self.profile, SHA_B)["action"], "migration-completed"
        )
        self.assertEqual([event[0] for event in self.docker.mutations], ["migration"])
        self.assertEqual(self.receipt(), {"status": "completed", "release_id": SHA_B})
        self.assertEqual(self.runtime.activate(self.profile, SHA_B)["action"], "activated")


class ScmCiOfflineRunnerTests(unittest.TestCase):
    def test_offline_deploy_noop_and_health_failure_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = FakeDocker()
            for sha in (SHA_A, SHA_B):
                profile, model, manifest = create_release(
                    root, sha, transport="offline-bundle", role="scm-ci"
                )
                docker.register(sha, model, manifest)
            runtime = ReleaseRuntime(docker, hostname="test-host")
            self.assertEqual(runtime.deploy(profile, SHA_A)["action"], "deployed")
            self.assertTrue(any(event[0] == "load" for event in docker.events))
            self.assertFalse(any(event[0] == "pull" for event in docker.events))
            mutations = list(docker.mutations)
            self.assertEqual(runtime.deploy(profile, SHA_A)["action"], "healthy-noop")
            self.assertEqual(docker.mutations, mutations)
            docker.unhealthy_for.add(SHA_B)
            with self.assertRaisesRegex(DeploymentError, "previous container release"):
                runtime.deploy(profile, SHA_B)
            self.assertEqual(docker.current_release, SHA_A)
            state = json.loads((root / "state/state.json").read_text())
            self.assertEqual(state["current_release"], SHA_A)
            self.assertEqual([event[1] for event in docker.events if event[0] == "up"][-2:],
                             [SHA_B, SHA_A])
            self.assertEqual(len([event for event in docker.events if event[0] == "migration"]), 2)


class HostRoleMatrixTests(unittest.TestCase):
    ACTIONS = (
        "verify", "verify-target", "stage", "migrate", "activate", "deploy", "status", "rollback"
    )
    DEPLOYMENT_ACTIONS = ("stage", "migrate", "activate", "deploy", "status", "rollback")

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.profile, model, manifest = create_release(self.root, SHA_A)
        self.profile_data = json.loads(self.profile.read_text())
        self.docker = FakeDocker()
        self.docker.register(SHA_A, model, manifest)
        self.runtime = ReleaseRuntime(self.docker, hostname="test-host")

    def test_role_environment_action_matrix(self) -> None:
        for role in ("scm-ci", "appserver-test", "appserver-prod"):
            for environment in ("test", "production"):
                data = dict(self.profile_data, host_role=role, environment=environment)
                write_json(self.profile, data, mode=0o600)
                profile = load_target_profile(self.profile)
                for action in self.ACTIONS:
                    with self.subTest(role=role, environment=environment, action=action):
                        denied = (
                            role == "scm-ci" and environment == "production"
                            and action in self.DEPLOYMENT_ACTIONS
                        )
                        if denied:
                            with self.assertRaises(HostRoleError):
                                _host_role_preflight(profile, action, "test-host")
                        else:
                            _host_role_preflight(profile, action, "test-host")

    def test_public_entrypoints_reject_before_docker_or_state_creation(self) -> None:
        cases = (
            ({"host_role": "scm-ci", "environment": "production"},
             self.DEPLOYMENT_ACTIONS, HostRoleError),
            ({"host_role": "unknown"}, self.ACTIONS, ContractError),
            ({"host_role": "scm-ci", "environment": "unknown"}, self.ACTIONS, ContractError),
            ({"host_role": "scm-ci", "environment": "test", "expected_hostname": "wrong-host"},
             self.ACTIONS, HostRoleError),
        )
        for overrides, actions, error in cases:
            write_json(self.profile, dict(self.profile_data, **overrides), mode=0o600)
            for action in actions:
                with self.subTest(overrides=overrides, action=action):
                    with self.assertRaises(error):
                        getattr(self.runtime, action.replace("-", "_"))(self.profile, SHA_A)
                    self.assertEqual(self.docker.events, [])
                    self.assertFalse((self.root / "state").exists())

    def test_unknown_action_cannot_use_test_exception(self) -> None:
        data = dict(self.profile_data, host_role="scm-ci", environment="test")
        write_json(self.profile, data, mode=0o600)
        for verify in (self.runtime._verify_context, self.runtime._verify_target_context):
            with self.subTest(entrypoint=verify.__name__):
                with self.assertRaises(HostRoleError):
                    verify(self.profile, SHA_A, "unknown", require_env=False)
                self.assertEqual(self.docker.events, [])
                self.assertFalse((self.root / "state").exists())

    def test_production_rejection_preserves_existing_state(self) -> None:
        self.runtime.deploy(self.profile, SHA_A)
        state_path = self.root / "state" / "state.json"
        before = state_path.read_bytes()
        data = dict(self.profile_data, host_role="scm-ci", environment="production")
        write_json(self.profile, data, mode=0o600)
        self.docker.events.clear()
        for action in self.DEPLOYMENT_ACTIONS:
            with self.subTest(action=action):
                with self.assertRaises(HostRoleError):
                    getattr(self.runtime, action)(self.profile, SHA_A)
                self.assertEqual(self.docker.events, [])
                self.assertEqual(state_path.read_bytes(), before)

    def test_scm_verification_is_read_only_in_both_environments(self) -> None:
        for environment in ("test", "production"):
            data = dict(self.profile_data, host_role="scm-ci", environment=environment)
            write_json(self.profile, data, mode=0o600)
            for verify in (self.runtime.verify, self.runtime.verify_target):
                with self.subTest(environment=environment, entrypoint=verify.__name__):
                    self.assertTrue(verify(self.profile, SHA_A)["ok"])
                    self.assertEqual(self.docker.mutations, [])
                    self.assertFalse((self.root / "state").exists())


if __name__ == "__main__":
    unittest.main()
