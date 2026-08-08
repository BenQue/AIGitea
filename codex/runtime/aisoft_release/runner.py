"""Deterministic, separately gated Docker release lifecycle phases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import socket
from typing import Mapping

from .compatibility import CompatibilityDecision
from .compose import RELEASE_LABEL, SERVICE_LABEL, validate_compose_model
from .contract import (
    RELEASE_VERSION_V2,
    ReleaseFiles,
    TargetProfile,
    load_release_artifact,
    load_release_files,
    load_target_profile,
    require_external_env_file,
)
from .docker import DockerAdapter
from .errors import ContractError, DeploymentError, HostRoleError, ReleaseError
from .state import DeploymentLock, StateStore
from .transport import ReleaseTransport, select_transport, validate_offline_artifact


@dataclass(frozen=True)
class VerifiedArtifact:
    files: ReleaseFiles


@dataclass(frozen=True)
class VerifiedRelease:
    profile: TargetProfile
    files: ReleaseFiles
    transport: ReleaseTransport
    compatibility: CompatibilityDecision


class ReleaseRuntime:
    def __init__(
        self,
        docker: object | None = None,
        *,
        hostname: str | None = None,
        today: date | None = None,
    ) -> None:
        self.docker = docker or DockerAdapter()
        self.hostname = hostname or socket.gethostname()
        self.today = today

    def verify_artifact(
        self, release_root: Path | str, release_id: str
    ) -> dict[str, object]:
        artifact = self._verify_artifact(release_root, release_id)
        manifest = artifact.files.manifest
        return {
            "ok": True,
            "action": "verify-artifact",
            "release_id": manifest.release_id,
            "source_repository": manifest.source_repository,
            "platform": manifest.platform,
            "contract_version": manifest.contract_version,
            "architecture_profile_id": manifest.architecture_profile_id,
            "architecture_project_id": artifact.files.architecture_lock["project_id"],
            "catalog_revision": manifest.catalog_revision,
            "target_facts": "NOT_READ",
            "docker_calls": 0,
        }

    def verify_target(
        self, profile_path: Path | str, release_id: str
    ) -> dict[str, object]:
        context = self._verify_target_context(
            profile_path, release_id, "verify-target", require_env=False
        )
        return self._verification_result(context, "verify-target")

    def stage(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
        context = self._verify_target_context(
            profile_path, release_id, "stage", require_env=False
        )
        store = StateStore(context.profile.state_root, context.profile.profile_id)
        with DeploymentLock(context.profile.state_root):
            state = store.load()
            if self._staging_receipt_matches(context, state):
                context.transport.assert_local_images()
                state["last_result"] = "staged-noop"
                store.save(state)
                return self._result(context, "staged-noop", state)
            context.transport.prepare()
            context.transport.assert_local_images()
            self._record_staged(context, state)
            state["last_result"] = "staged"
            store.save(state)
            return self._result(context, "staged", state)

    def migrate(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
        context = self._verify_target_context(
            profile_path, release_id, "migrate", require_env=True
        )
        store = StateStore(context.profile.state_root, context.profile.profile_id)
        with DeploymentLock(context.profile.state_root):
            state = store.load()
            self._require_staged(context, state)
            self._ensure_migration_not_uncertain(context, state)
            outcome = self._run_migration(context, state, store)
            state["last_result"] = outcome
            store.save(state)
            return self._result(context, outcome, state)

    def activate(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
        context = self._verify_target_context(
            profile_path, release_id, "activate", require_env=True
        )
        store = StateStore(context.profile.state_root, context.profile.profile_id)
        with DeploymentLock(context.profile.state_root):
            state = store.load()
            self._require_staged(context, state)
            self._require_migration_completed(context, state)
            current = state["current_release"]
            if current == release_id and self._is_exact_healthy(context):
                state["last_result"] = "healthy-noop"
                store.save(state)
                return self._result(context, "healthy-noop", state)
            try:
                self._start_and_assert(context)
            except ReleaseError as activation_error:
                if isinstance(current, str):
                    try:
                        previous = self._verify_target_context(
                            profile_path, current, "activate", require_env=True
                        )
                        self._require_staged(previous, state)
                        self._start_and_assert(previous)
                    except ReleaseError as rollback_error:
                        raise DeploymentError(
                            "activation failed and automatic container rollback failed"
                        ) from rollback_error
                raise DeploymentError(
                    "activation failed; previous container release was preserved or restored"
                ) from activation_error
            if current != release_id:
                state["previous_release"] = current
                state["current_release"] = release_id
            state["last_result"] = "activated"
            store.save(state)
            return self._result(context, "activated", state)

    def verify(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
        """Backward-compatible target-coupled verification entry point."""

        context = self._verify_context(profile_path, release_id, "verify", require_env=False)
        return self._verification_result(context, "verify")

    def deploy(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
        """Backward-compatible orchestration of stage, migrate and activate."""

        context = self._verify_context(profile_path, release_id, "deploy", require_env=True)
        store = StateStore(context.profile.state_root, context.profile.profile_id)
        with DeploymentLock(context.profile.state_root):
            state = store.load()
            current = state["current_release"]
            if current == release_id and self._is_exact_healthy(context):
                state["last_result"] = "healthy-noop"
                store.save(state)
                return self._result(context, "healthy-noop", state)
            self._ensure_migration_not_uncertain(context, state)
            context.transport.prepare()
            context.transport.assert_local_images()
            self._record_staged(context, state)
            store.save(state)
            self._run_migration(context, state, store)
            try:
                self._start_and_assert(context)
            except ReleaseError as deploy_error:
                if isinstance(current, str):
                    try:
                        previous = self._verify_context(
                            profile_path, current, "deploy", require_env=True
                        )
                        self._start_and_assert(previous)
                    except ReleaseError as rollback_error:
                        raise DeploymentError(
                            "deployment failed and automatic container rollback failed"
                        ) from rollback_error
                raise DeploymentError(
                    "deployment failed; previous container release was preserved or restored"
                ) from deploy_error
            if current != release_id:
                state["previous_release"] = current
                state["current_release"] = release_id
            state["last_result"] = "deployed"
            store.save(state)
            return self._result(context, "deployed", state)

    def status(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
        context = self._verify_context(profile_path, release_id, "status", require_env=True)
        store = StateStore(context.profile.state_root, context.profile.profile_id)
        with DeploymentLock(context.profile.state_root):
            state = store.load()
            healthy = state["current_release"] == release_id and self._is_exact_healthy(context)
            result = self._result(context, "healthy" if healthy else "not-exact-healthy", state)
            result["ok"] = healthy
            return result

    def rollback(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
        context = self._verify_context(profile_path, release_id, "rollback", require_env=True)
        store = StateStore(context.profile.state_root, context.profile.profile_id)
        with DeploymentLock(context.profile.state_root):
            state = store.load()
            current = state["current_release"]
            previous = state["previous_release"]
            if not isinstance(current, str):
                raise DeploymentError("rollback requires a currently deployed release")
            if previous != release_id:
                raise DeploymentError("rollback release_id must equal recorded previous_release")
            if context.files.manifest.contract_version == RELEASE_VERSION_V2:
                self._require_staged(context, state)
            else:
                context.transport.prepare()
            try:
                self._start_and_assert(context)
            except ReleaseError as rollback_error:
                try:
                    current_context = self._verify_context(
                        profile_path, current, "rollback", require_env=True
                    )
                    self._start_and_assert(current_context)
                except ReleaseError as restore_error:
                    raise DeploymentError(
                        "explicit rollback failed and current release restoration failed"
                    ) from restore_error
                raise DeploymentError(
                    "explicit rollback failed; current release was restored"
                ) from rollback_error
            state["current_release"] = release_id
            state["previous_release"] = current
            state["last_result"] = "rolled-back"
            store.save(state)
            return self._result(context, "rolled-back", state)

    def _verify_artifact(
        self, release_root: Path | str, release_id: str
    ) -> VerifiedArtifact:
        files = load_release_artifact(release_root, release_id, today=self.today)
        if files.manifest.contract_version != RELEASE_VERSION_V2:
            raise ContractError(
                "verify-artifact requires docker-release/v2; legacy v1 remains available through verify"
            )
        if files.compose_model is None:
            raise ContractError("docker-release/v2 normalized Compose model is missing")
        validate_compose_model(files.compose_model, files.manifest)
        validate_offline_artifact(files)
        return VerifiedArtifact(files=files)

    def _verify_target_context(
        self,
        profile_path: Path | str,
        release_id: str,
        action: str,
        *,
        require_env: bool,
    ) -> VerifiedRelease:
        profile = load_target_profile(profile_path, require_protected=True)
        _host_role_preflight(profile, action, self.hostname)
        files = load_release_files(profile, release_id, today=self.today)
        self._verify_artifact(profile.release_root, release_id)
        if require_env:
            require_external_env_file(profile)
        transport = select_transport(profile.transport, self.docker, files)
        compatibility = self.docker.assert_runtime_compatible()
        target_model = self.docker.compose_config(files.compose_path, profile.compose_project)
        validate_compose_model(target_model, files.manifest)
        if target_model != files.compose_model:
            raise ContractError(
                "target-side Compose render does not match producer normalized model"
            )
        return VerifiedRelease(profile, files, transport, compatibility)

    def _verify_context(
        self,
        profile_path: Path | str,
        release_id: str,
        action: str,
        *,
        require_env: bool,
    ) -> VerifiedRelease:
        profile = load_target_profile(profile_path, require_protected=True)
        _host_role_preflight(profile, action, self.hostname)
        files = load_release_files(profile, release_id, today=self.today)
        if require_env:
            require_external_env_file(profile)
        transport = select_transport(profile.transport, self.docker, files)
        transport.preflight()
        compatibility = self.docker.assert_runtime_compatible()
        model = self.docker.compose_config(files.compose_path, profile.compose_project)
        validate_compose_model(model, files.manifest)
        return VerifiedRelease(profile, files, transport, compatibility)

    def _staging_receipt_matches(
        self, context: VerifiedRelease, state: Mapping[str, object]
    ) -> bool:
        staged = state.get("staged_releases")
        if not isinstance(staged, Mapping):
            return False
        record = staged.get(context.files.manifest.release_id)
        if not isinstance(record, Mapping):
            return False
        return (
            record.get("status") == "completed"
            and record.get("transport") == context.profile.transport
            and record.get("image_ids")
            == {
                image.service: image.image_id
                for image in context.files.manifest.images
            }
        )

    def _record_staged(
        self, context: VerifiedRelease, state: dict[str, object]
    ) -> None:
        staged = state.get("staged_releases")
        if not isinstance(staged, dict):
            raise DeploymentError("deployment staging state is invalid")
        staged[context.files.manifest.release_id] = {
            "status": "completed",
            "transport": context.profile.transport,
            "image_ids": {
                image.service: image.image_id
                for image in context.files.manifest.images
            },
        }

    def _require_staged(
        self, context: VerifiedRelease, state: Mapping[str, object]
    ) -> None:
        if not self._staging_receipt_matches(context, state):
            raise DeploymentError(
                "operation requires a completed exact image staging receipt"
            )
        context.transport.assert_local_images()

    def _ensure_migration_not_uncertain(
        self, context: VerifiedRelease, state: Mapping[str, object]
    ) -> None:
        migration = context.files.manifest.migration
        if migration is None:
            return
        migrations = state.get("migrations")
        if not isinstance(migrations, Mapping):
            raise DeploymentError("deployment migration state is invalid")
        record = migrations.get(migration.identity)
        if isinstance(record, Mapping) and record.get("status") in {"started", "failed"}:
            raise DeploymentError(
                "migration outcome is uncertain or failed; automatic rerun is forbidden"
            )

    def _require_migration_completed(
        self, context: VerifiedRelease, state: Mapping[str, object]
    ) -> None:
        migration = context.files.manifest.migration
        if migration is None:
            return
        migrations = state.get("migrations")
        record = migrations.get(migration.identity) if isinstance(migrations, Mapping) else None
        if not isinstance(record, Mapping) or record.get("status") != "completed":
            raise DeploymentError(
                "activation requires a completed exact migration receipt"
            )
        if record.get("release_id") != context.files.manifest.release_id:
            raise DeploymentError("activation migration receipt release identity is stale")

    def _run_migration(
        self,
        context: VerifiedRelease,
        state: dict[str, object],
        store: StateStore,
    ) -> str:
        migration = context.files.manifest.migration
        if migration is None:
            return "migration-not-required"
        migrations = state["migrations"]
        if not isinstance(migrations, dict):
            raise DeploymentError("deployment migration state is invalid")
        record = migrations.get(migration.identity)
        if isinstance(record, Mapping) and record.get("status") == "completed":
            if record.get("release_id") != context.files.manifest.release_id:
                raise DeploymentError("migration receipt release identity is stale")
            return "migration-noop"
        migrations[migration.identity] = {
            "status": "started",
            "release_id": context.files.manifest.release_id,
        }
        state["last_result"] = "migration-started"
        store.save(state)
        try:
            context.transport.assert_local_images()
            self.docker.run_migration(
                context.files.compose_path,
                context.profile.compose_project,
                context.profile.env_file,
                migration.service,
            )
        except ReleaseError as exc:
            migrations[migration.identity] = {
                "status": "failed",
                "release_id": context.files.manifest.release_id,
            }
            state["last_result"] = "migration-failed"
            store.save(state)
            raise DeploymentError(
                "migration failed; automatic retry and database restore are forbidden"
            ) from exc
        migrations[migration.identity] = {
            "status": "completed",
            "release_id": context.files.manifest.release_id,
        }
        state["last_result"] = "migration-completed"
        store.save(state)
        return "migration-completed"

    def _start_and_assert(self, context: VerifiedRelease) -> None:
        context.transport.assert_local_images()
        self.docker.compose_up(
            context.files.compose_path,
            context.profile.compose_project,
            context.profile.env_file,
            context.profile.wait_timeout_seconds,
        )
        self._assert_exact_healthy(context)

    def _is_exact_healthy(self, context: VerifiedRelease) -> bool:
        try:
            self._assert_exact_healthy(context)
            return True
        except ReleaseError:
            return False

    def _assert_exact_healthy(self, context: VerifiedRelease) -> None:
        manifest = context.files.manifest
        for service in manifest.runtime_services:
            identifiers = self.docker.container_ids(
                context.files.compose_path,
                context.profile.compose_project,
                context.profile.env_file,
                service,
            )
            if len(identifiers) != 1:
                raise DeploymentError(
                    f"runtime service {service} must have exactly one container"
                )
            value = self.docker.inspect_container(identifiers[0])
            config = value.get("Config")
            state = value.get("State")
            if not isinstance(config, Mapping) or not isinstance(state, Mapping):
                raise DeploymentError(f"runtime service {service} inspect data is invalid")
            labels = config.get("Labels")
            if not isinstance(labels, Mapping):
                raise DeploymentError(f"runtime service {service} is missing release labels")
            if labels.get(RELEASE_LABEL) != manifest.release_id:
                raise DeploymentError(f"runtime service {service} release label is stale")
            if labels.get(SERVICE_LABEL) != service:
                raise DeploymentError(f"runtime service {service} service label is stale")
            image = manifest.image_for(service)
            if config.get("Image") != image.runtime_reference or value.get("Image") != image.image_id:
                raise DeploymentError(f"runtime service {service} image identity is stale")
            health = state.get("Health")
            if state.get("Running") is not True or not isinstance(health, Mapping):
                raise DeploymentError(f"runtime service {service} is not running and healthy")
            if health.get("Status") != "healthy":
                raise DeploymentError(f"runtime service {service} health is not healthy")

    @staticmethod
    def _verification_result(
        context: VerifiedRelease, action: str
    ) -> dict[str, object]:
        return {
            "ok": True,
            "action": action,
            "profile_id": context.profile.profile_id,
            "release_id": context.files.manifest.release_id,
            "source_repository": context.files.manifest.source_repository,
            "platform": context.files.manifest.platform,
            "transport": context.profile.transport,
            "architecture_profile_id": context.files.manifest.architecture_profile_id,
            "architecture_project_id": context.files.architecture_lock["project_id"],
            "catalog_revision": context.files.manifest.catalog_revision,
            "image_store": context.compatibility.capability.image_store,
            "compatibility_matrix_revision": context.compatibility.matrix_revision,
            "compatibility_row": context.compatibility.row_id,
        }

    @staticmethod
    def _result(
        context: VerifiedRelease, outcome: str, state: Mapping[str, object]
    ) -> dict[str, object]:
        return {
            "ok": True,
            "action": outcome,
            "profile_id": context.profile.profile_id,
            "release_id": context.files.manifest.release_id,
            "current_release": state.get("current_release"),
            "previous_release": state.get("previous_release"),
            "database_restore": "NOT_RUN_MANUAL_ONLY",
        }


def _host_role_preflight(profile: TargetProfile, action: str, hostname: str) -> None:
    if hostname != profile.expected_hostname:
        raise HostRoleError("target hostname does not match protected target profile")
    allowed = {
        "verify": {"scm-ci", "appserver-test", "appserver-prod"},
        "verify-target": {"scm-ci", "appserver-test", "appserver-prod"},
        "deploy": {"appserver-test", "appserver-prod"},
        "stage": {"appserver-test", "appserver-prod"},
        "migrate": {"appserver-test", "appserver-prod"},
        "activate": {"appserver-test", "appserver-prod"},
        "status": {"appserver-test", "appserver-prod"},
        "rollback": {"appserver-test", "appserver-prod"},
    }
    roles = allowed.get(action)
    if roles is None or profile.host_role not in roles:
        raise HostRoleError(
            f"host role {profile.host_role} is not allowed to perform {action}"
        )
