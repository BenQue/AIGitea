"""Deterministic verify/deploy/status/rollback state machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import socket
from pathlib import Path
from typing import Mapping

from .compose import RELEASE_LABEL, SERVICE_LABEL, validate_compose_model
from .contract import (
    ReleaseFiles,
    TargetProfile,
    load_release_files,
    load_target_profile,
    require_external_env_file,
)
from .docker import DockerAdapter
from .errors import ContractError, DeploymentError, HostRoleError, ReleaseError
from .state import DeploymentLock, StateStore
from .transport import ReleaseTransport, select_transport


@dataclass(frozen=True)
class VerifiedRelease:
    profile: TargetProfile
    files: ReleaseFiles
    transport: ReleaseTransport


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

    def verify(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
        context = self._verify_context(profile_path, release_id, "verify", require_env=False)
        return {
            "ok": True,
            "action": "verify",
            "profile_id": context.profile.profile_id,
            "release_id": context.files.manifest.release_id,
            "source_repository": context.files.manifest.source_repository,
            "platform": context.files.manifest.platform,
            "transport": context.profile.transport,
            "architecture_profile_id": context.files.manifest.architecture_profile_id,
            "architecture_project_id": context.files.architecture_lock["project_id"],
            "catalog_revision": context.files.manifest.catalog_revision,
        }

    def deploy(self, profile_path: Path | str, release_id: str) -> dict[str, object]:
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
        # Offline checksum/inventory/tar safety is completed before even a
        # read-only Docker config call, so tamper evidence has zero Docker calls.
        transport.preflight()
        model = self.docker.compose_config(files.compose_path, profile.compose_project)
        validate_compose_model(model, files.manifest)
        return VerifiedRelease(profile=profile, files=files, transport=transport)

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

    def _run_migration(
        self,
        context: VerifiedRelease,
        state: dict[str, object],
        store: StateStore,
    ) -> None:
        migration = context.files.manifest.migration
        if migration is None:
            return
        migrations = state["migrations"]
        if not isinstance(migrations, dict):
            raise DeploymentError("deployment migration state is invalid")
        record = migrations.get(migration.identity)
        if isinstance(record, Mapping) and record.get("status") == "completed":
            return
        migrations[migration.identity] = {
            "status": "started",
            "release_id": context.files.manifest.release_id,
        }
        state["last_result"] = "migration-started"
        store.save(state)
        try:
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

    def _start_and_assert(self, context: VerifiedRelease) -> None:
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
            if config.get("Image") != image.reference or value.get("Image") != image.image_id:
                raise DeploymentError(f"runtime service {service} image identity is stale")
            health = state.get("Health")
            if state.get("Running") is not True or not isinstance(health, Mapping):
                raise DeploymentError(f"runtime service {service} is not running and healthy")
            if health.get("Status") != "healthy":
                raise DeploymentError(f"runtime service {service} health is not healthy")

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
        "deploy": {"appserver-test", "appserver-prod"},
        "status": {"appserver-test", "appserver-prod"},
        "rollback": {"appserver-test", "appserver-prod"},
    }
    roles = allowed.get(action)
    if roles is None or profile.host_role not in roles:
        raise HostRoleError(
            f"host role {profile.host_role} is not allowed to perform {action}"
        )
