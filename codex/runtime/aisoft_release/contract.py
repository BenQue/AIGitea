"""Strict release/profile parsing and all mutation-free contract checks."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Mapping, Sequence
from urllib.parse import urlsplit

from .errors import ContractError


RELEASE_VERSION = "docker-release/v1"
PROFILE_VERSION = "docker-release-target/v1"
ARCHITECTURE_LOCK_SCHEMA = "./architecture/schemas/architecture-lock-v1.schema.json"
ARCHITECTURE_LOCK_SCHEMA_VERSION = "1.0"
OFFLINE_INVENTORY_VERSION = "docker-release-offline-inventory/v1"
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ARCHITECTURE_ID = re.compile(r"^[a-z0-9][a-z0-9-]+$")
ARCHITECTURE_COMPONENT = re.compile(r"^[a-z0-9][a-z0-9.-]+$")
ARCHITECTURE_REVISION = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[0-9]+$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SERVICE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
IMAGE_REFERENCE = re.compile(
    r"^[a-z0-9][a-z0-9./:_-]*@sha256:[0-9a-f]{64}$"
)
HOSTNAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$")
COMPOSE_PROJECT = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
SENSITIVE_KEY = re.compile(
    r"(?:^|[_-])(?:auth|authorization|token|password|secret|credential|"
    r"connection[_-]?string|certificate|ssh[_-]?key)(?:$|[_-])",
    re.IGNORECASE,
)
MAX_JSON_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class ImageSpec:
    service: str
    reference: str
    digest: str
    image_id: str


@dataclass(frozen=True)
class MigrationSpec:
    service: str
    identity: str
    destructive: bool
    database_restore: str


@dataclass(frozen=True)
class OfflineBundleSpec:
    archive_path: str
    archive_sha256: str
    inventory_path: str
    inventory_sha256: str


@dataclass(frozen=True)
class ReleaseManifest:
    contract_version: str
    release_id: str
    source_repository: str
    merge_sha: str
    platform: str
    compose_path: str
    compose_sha256: str
    architecture_path: str
    architecture_profile_id: str
    catalog_revision: str
    architecture_lock_sha256: str
    images: tuple[ImageSpec, ...]
    runtime_services: tuple[str, ...]
    migration: MigrationSpec | None
    offline_bundle: OfflineBundleSpec

    def image_for(self, service: str) -> ImageSpec:
        for image in self.images:
            if image.service == service:
                return image
        raise ContractError(f"manifest does not declare image for service {service}")


@dataclass(frozen=True)
class TargetProfile:
    path: Path
    contract_version: str
    profile_id: str
    environment: str
    host_role: str
    expected_hostname: str
    transport: str
    release_root: Path
    state_root: Path
    compose_project: str
    env_file: Path
    source_repository: str
    architecture_profile_id: str
    catalog_revision: str
    wait_timeout_seconds: int


@dataclass(frozen=True)
class ReleaseFiles:
    directory: Path
    manifest_path: Path
    compose_path: Path
    architecture_lock_path: Path
    archive_path: Path
    inventory_path: Path
    manifest: ReleaseManifest
    architecture_lock: Mapping[str, object]


def load_target_profile(path: Path | str, *, require_protected: bool = True) -> TargetProfile:
    profile_path = Path(path)
    if require_protected:
        _require_protected_file(profile_path, "target profile")
    value = _load_json_object(profile_path, "target profile")
    _reject_sensitive_keys(value, "target profile")
    _expect_keys(
        value,
        {
            "contract_version",
            "profile_id",
            "environment",
            "host_role",
            "expected_hostname",
            "transport",
            "release_root",
            "state_root",
            "compose_project",
            "env_file",
            "source_repository",
            "architecture_profile_id",
            "catalog_revision",
            "wait_timeout_seconds",
        },
        "target profile",
    )
    contract_version = _string(value, "contract_version", "target profile")
    if contract_version != PROFILE_VERSION:
        raise ContractError(f"target profile contract_version must be {PROFILE_VERSION}")
    profile_id = _matching_string(value, "profile_id", IDENTIFIER, "target profile")
    environment = _string(value, "environment", "target profile")
    if environment not in {"test", "production"}:
        raise ContractError("target profile environment must be test or production")
    host_role = _string(value, "host_role", "target profile")
    if host_role not in {"scm-ci", "appserver-test", "appserver-prod"}:
        raise ContractError("target profile host_role is not recognized")
    expected_hostname = _matching_string(
        value, "expected_hostname", HOSTNAME, "target profile"
    )
    transport = _string(value, "transport", "target profile")
    if transport not in {"registry", "offline-bundle"}:
        raise ContractError("target profile transport is not recognized")
    release_root = _absolute_path(value, "release_root", "target profile")
    state_root = _absolute_path(value, "state_root", "target profile")
    env_file = _absolute_path(value, "env_file", "target profile")
    _reject_path_overlap(release_root, state_root, "release_root", "state_root")
    if _is_within(env_file, release_root) or _is_within(env_file, state_root):
        raise ContractError("target profile env_file must be outside release and state roots")
    compose_project = _matching_string(
        value, "compose_project", COMPOSE_PROJECT, "target profile"
    )
    source_repository = _matching_string(
        value, "source_repository", REPOSITORY, "target profile"
    )
    architecture_profile_id = _matching_string(
        value, "architecture_profile_id", IDENTIFIER, "target profile"
    )
    catalog_revision = _matching_string(
        value, "catalog_revision", IDENTIFIER, "target profile"
    )
    wait_timeout = value.get("wait_timeout_seconds")
    if isinstance(wait_timeout, bool) or not isinstance(wait_timeout, int):
        raise ContractError("target profile wait_timeout_seconds must be an integer")
    if not 1 <= wait_timeout <= 900:
        raise ContractError("target profile wait_timeout_seconds must be between 1 and 900")
    return TargetProfile(
        path=profile_path.resolve(),
        contract_version=contract_version,
        profile_id=profile_id,
        environment=environment,
        host_role=host_role,
        expected_hostname=expected_hostname,
        transport=transport,
        release_root=release_root,
        state_root=state_root,
        compose_project=compose_project,
        env_file=env_file,
        source_repository=source_repository,
        architecture_profile_id=architecture_profile_id,
        catalog_revision=catalog_revision,
        wait_timeout_seconds=wait_timeout,
    )


def load_release_files(profile: TargetProfile, release_id: str) -> ReleaseFiles:
    if not isinstance(release_id, str) or not GIT_SHA.fullmatch(release_id):
        raise ContractError("release_id must be a lowercase 40-character Git SHA")
    release_root = profile.release_root
    directory = release_root / release_id
    _require_directory(directory, "release directory")
    if directory.is_symlink():
        raise ContractError("release directory must not be a symlink")
    _assert_within(directory.resolve(), release_root.resolve(), "release directory")
    manifest_path = _release_file(directory, "release.json", "release manifest")
    raw = _load_json_object(manifest_path, "release manifest")
    _reject_sensitive_keys(raw, "release manifest")
    manifest = _parse_manifest(raw, release_id)
    if manifest.source_repository != profile.source_repository:
        raise ContractError("release source_repository does not match target profile")
    if manifest.architecture_profile_id != profile.architecture_profile_id:
        raise ContractError("release architecture profile does not match target profile")
    if manifest.catalog_revision != profile.catalog_revision:
        raise ContractError("release catalog revision does not match target profile")
    compose_path = _release_file(directory, manifest.compose_path, "Compose file")
    architecture_path = _release_file(
        directory, manifest.architecture_path, "architecture lock"
    )
    archive_path = _release_path(directory, manifest.offline_bundle.archive_path)
    inventory_path = _release_path(directory, manifest.offline_bundle.inventory_path)
    _validate_release_inventory(
        directory,
        {
            manifest_path,
            compose_path,
            architecture_path,
            archive_path,
            inventory_path,
        },
    )
    _require_checksum(compose_path, manifest.compose_sha256, "Compose file")
    _require_checksum(
        architecture_path,
        manifest.architecture_lock_sha256,
        "architecture lock",
    )
    architecture_lock = _load_json_object(architecture_path, "architecture lock")
    _reject_sensitive_keys(architecture_lock, "architecture lock")
    _validate_architecture_lock(architecture_lock, manifest)
    return ReleaseFiles(
        directory=directory.resolve(),
        manifest_path=manifest_path,
        compose_path=compose_path,
        architecture_lock_path=architecture_path,
        archive_path=archive_path,
        inventory_path=inventory_path,
        manifest=manifest,
        architecture_lock=architecture_lock,
    )


def _validate_architecture_lock(
    lock: Mapping[str, object], manifest: ReleaseManifest
) -> None:
    context = "architecture lock"
    _expect_keys(
        lock,
        {
            "$schema",
            "schema_version",
            "project_id",
            "profile_id",
            "profile_version",
            "catalog_revision",
            "delivery_contract",
            "resolved_components",
            "exception_ids",
            "source_checksums",
            "lock_sha256",
        },
        context,
    )
    schema_ref = _string(lock, "$schema", context)
    if schema_ref != ARCHITECTURE_LOCK_SCHEMA:
        raise ContractError(
            f"architecture lock $schema must be {ARCHITECTURE_LOCK_SCHEMA}"
        )
    schema_version = _string(lock, "schema_version", context)
    if schema_version != ARCHITECTURE_LOCK_SCHEMA_VERSION:
        raise ContractError(
            "architecture lock schema_version must be "
            + ARCHITECTURE_LOCK_SCHEMA_VERSION
        )
    _matching_string(lock, "project_id", ARCHITECTURE_ID, context)
    profile_id = _matching_string(lock, "profile_id", ARCHITECTURE_ID, context)
    _matching_string(lock, "profile_version", SEMVER, context)
    catalog_revision = _matching_string(
        lock, "catalog_revision", ARCHITECTURE_REVISION, context
    )
    delivery_contract = _string(lock, "delivery_contract", context)
    if delivery_contract != RELEASE_VERSION:
        raise ContractError(
            f"architecture lock delivery_contract must be {RELEASE_VERSION}"
        )

    raw_components = lock.get("resolved_components")
    if not isinstance(raw_components, list) or not raw_components:
        raise ContractError("architecture lock resolved_components must be a non-empty array")
    component_ids: list[str] = []
    for index, raw_component in enumerate(raw_components):
        component_context = f"architecture lock resolved_components[{index}]"
        if not isinstance(raw_component, Mapping):
            raise ContractError(f"{component_context} must be an object")
        _expect_required_and_optional_keys(
            raw_component,
            {"component_id", "version", "state", "source_url"},
            {"digest", "migration_issue"},
            component_context,
        )
        component_id = _matching_string(
            raw_component, "component_id", ARCHITECTURE_COMPONENT, component_context
        )
        _string(raw_component, "version", component_context)
        state = _string(raw_component, "state", component_context)
        if state not in {"preferred", "supported", "sunset"}:
            raise ContractError(f"{component_context} state is not recognized")
        source_url = _string(raw_component, "source_url", component_context)
        _require_https_source_url(source_url, component_context)
        if "digest" in raw_component:
            _matching_string(raw_component, "digest", DIGEST, component_context)
        if "migration_issue" in raw_component:
            migration_issue = _string(raw_component, "migration_issue", component_context)
            if len(migration_issue) < 2:
                raise ContractError(
                    f"{component_context} migration_issue must contain at least two characters"
                )
        component_ids.append(component_id)
    if component_ids != sorted(component_ids):
        raise ContractError("architecture lock resolved_components must be sorted")
    if len(component_ids) != len(set(component_ids)):
        raise ContractError("architecture lock resolved_components contains duplicates")

    raw_exceptions = lock.get("exception_ids")
    if not isinstance(raw_exceptions, list):
        raise ContractError("architecture lock exception_ids must be an array")
    exception_ids: list[str] = []
    for index, exception_id in enumerate(raw_exceptions):
        if not isinstance(exception_id, str) or not exception_id:
            raise ContractError(
                f"architecture lock exception_ids[{index}] must be a non-empty string"
            )
        if any(ord(character) < 32 for character in exception_id):
            raise ContractError(
                f"architecture lock exception_ids[{index}] contains control characters"
            )
        exception_ids.append(exception_id)
    if exception_ids != sorted(exception_ids):
        raise ContractError("architecture lock exception_ids must be sorted")
    if len(exception_ids) != len(set(exception_ids)):
        raise ContractError("architecture lock exception_ids contains duplicates")

    source_checksums = _mapping(lock, "source_checksums", context)
    _expect_keys(
        source_checksums,
        {"catalog_sha256", "profile_sha256", "declaration_sha256"},
        "architecture lock source_checksums",
    )
    for key in ("catalog_sha256", "profile_sha256", "declaration_sha256"):
        _matching_string(
            source_checksums,
            key,
            SHA256_HEX,
            "architecture lock source_checksums",
        )

    declared_lock_sha = _matching_string(lock, "lock_sha256", SHA256_HEX, context)
    hash_payload = dict(lock)
    hash_payload.pop("lock_sha256")
    if declared_lock_sha != _canonical_sha256(hash_payload):
        raise ContractError("architecture lock lock_sha256 is invalid")
    if profile_id != manifest.architecture_profile_id:
        raise ContractError("architecture lock profile_id does not match release manifest")
    if catalog_revision != manifest.catalog_revision:
        raise ContractError("architecture lock catalog_revision does not match release manifest")


def load_offline_inventory(files: ReleaseFiles) -> Mapping[str, object]:
    spec = files.manifest.offline_bundle
    inventory_path = _release_file(
        files.directory, spec.inventory_path, "offline inventory"
    )
    archive_path = _release_file(files.directory, spec.archive_path, "offline image archive")
    _require_checksum(inventory_path, spec.inventory_sha256, "offline inventory")
    _require_checksum(archive_path, spec.archive_sha256, "offline image archive")
    inventory = _load_json_object(inventory_path, "offline inventory")
    _reject_sensitive_keys(inventory, "offline inventory")
    _expect_keys(
        inventory,
        {"contract_version", "archive_sha256", "images"},
        "offline inventory",
    )
    if inventory.get("contract_version") != OFFLINE_INVENTORY_VERSION:
        raise ContractError(
            f"offline inventory contract_version must be {OFFLINE_INVENTORY_VERSION}"
        )
    if inventory.get("archive_sha256") != spec.archive_sha256:
        raise ContractError("offline inventory archive checksum does not match manifest")
    raw_images = inventory.get("images")
    if not isinstance(raw_images, list) or not raw_images:
        raise ContractError("offline inventory images must be a non-empty array")
    parsed = tuple(
        _parse_image(item, f"offline inventory images[{index}]")
        for index, item in enumerate(raw_images)
    )
    _require_unique_images(parsed, "offline inventory")
    if parsed != files.manifest.images:
        raise ContractError("offline inventory images do not exactly match release manifest")
    return inventory


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ContractError(f"cannot read file for checksum: {path.name}") from exc
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    try:
        payload = (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("architecture lock is not canonical JSON") from exc
    return hashlib.sha256(payload).hexdigest()


def _require_https_source_url(value: str, context: str) -> None:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
    except ValueError as exc:
        raise ContractError(f"{context} source_url is invalid") from exc
    if parsed.scheme != "https" or not hostname:
        raise ContractError(f"{context} source_url must use https")
    if parsed.username is not None or parsed.password is not None:
        raise ContractError(f"{context} source_url must not contain credentials")


def require_external_env_file(profile: TargetProfile) -> None:
    _require_protected_file(profile.env_file, "external env file")


def _parse_manifest(value: Mapping[str, object], requested_release: str) -> ReleaseManifest:
    _expect_keys(
        value,
        {
            "contract_version",
            "release_id",
            "source_repository",
            "merge_sha",
            "platform",
            "compose",
            "architecture",
            "images",
            "runtime_services",
            "migration",
            "offline_bundle",
        },
        "release manifest",
    )
    contract_version = _string(value, "contract_version", "release manifest")
    if contract_version != RELEASE_VERSION:
        raise ContractError(f"release contract_version must be {RELEASE_VERSION}")
    release_id = _matching_string(value, "release_id", GIT_SHA, "release manifest")
    merge_sha = _matching_string(value, "merge_sha", GIT_SHA, "release manifest")
    if release_id != requested_release or merge_sha != release_id:
        raise ContractError("release_id, merge_sha and release directory must be identical")
    source_repository = _matching_string(
        value, "source_repository", REPOSITORY, "release manifest"
    )
    platform = _string(value, "platform", "release manifest")
    if platform != "linux/amd64":
        raise ContractError("release platform must be linux/amd64")

    compose = _mapping(value, "compose", "release manifest")
    _expect_keys(compose, {"path", "sha256"}, "release manifest compose")
    compose_path = _relative_path(compose, "path", "release manifest compose")
    compose_sha = _matching_string(
        compose, "sha256", SHA256_HEX, "release manifest compose"
    )

    architecture = _mapping(value, "architecture", "release manifest")
    _expect_keys(
        architecture,
        {"path", "profile_id", "catalog_revision", "sha256"},
        "release manifest architecture",
    )
    architecture_path = _relative_path(
        architecture, "path", "release manifest architecture"
    )
    architecture_profile = _matching_string(
        architecture, "profile_id", IDENTIFIER, "release manifest architecture"
    )
    catalog_revision = _matching_string(
        architecture, "catalog_revision", IDENTIFIER, "release manifest architecture"
    )
    architecture_sha = _matching_string(
        architecture, "sha256", SHA256_HEX, "release manifest architecture"
    )

    raw_images = value.get("images")
    if not isinstance(raw_images, list) or not raw_images:
        raise ContractError("release manifest images must be a non-empty array")
    images = tuple(
        _parse_image(item, f"release manifest images[{index}]")
        for index, item in enumerate(raw_images)
    )
    _require_unique_images(images, "release manifest")

    runtime_services = _string_array(
        value.get("runtime_services"), SERVICE, "release manifest runtime_services"
    )
    if not runtime_services:
        raise ContractError("release manifest runtime_services must not be empty")
    if len(set(runtime_services)) != len(runtime_services):
        raise ContractError("release manifest runtime_services contains duplicates")
    image_services = {item.service for item in images}
    unknown_runtime = sorted(set(runtime_services) - image_services)
    if unknown_runtime:
        raise ContractError(
            "runtime_services missing image declarations: " + ", ".join(unknown_runtime)
        )

    raw_migration = value.get("migration")
    migration: MigrationSpec | None
    if raw_migration is None:
        migration = None
    else:
        if not isinstance(raw_migration, Mapping):
            raise ContractError("release manifest migration must be an object or null")
        _expect_keys(
            raw_migration,
            {"service", "identity", "destructive", "database_restore"},
            "release manifest migration",
        )
        migration_service = _matching_string(
            raw_migration, "service", SERVICE, "release manifest migration"
        )
        migration_identity = _matching_string(
            raw_migration, "identity", DIGEST, "release manifest migration"
        )
        destructive = raw_migration.get("destructive")
        if not isinstance(destructive, bool):
            raise ContractError("release manifest migration destructive must be boolean")
        restore = _string(raw_migration, "database_restore", "release manifest migration")
        if restore != "manual-only":
            raise ContractError("database_restore must be manual-only")
        if migration_service not in image_services:
            raise ContractError("migration service is missing an image declaration")
        if migration_service in runtime_services:
            raise ContractError("migration service must not also be a runtime service")
        if destructive:
            raise ContractError("destructive migration requires an independent human gate")
        migration = MigrationSpec(
            service=migration_service,
            identity=migration_identity,
            destructive=destructive,
            database_restore=restore,
        )

    offline = _mapping(value, "offline_bundle", "release manifest")
    _expect_keys(
        offline,
        {"archive_path", "archive_sha256", "inventory_path", "inventory_sha256"},
        "release manifest offline_bundle",
    )
    offline_bundle = OfflineBundleSpec(
        archive_path=_relative_path(
            offline, "archive_path", "release manifest offline_bundle"
        ),
        archive_sha256=_matching_string(
            offline, "archive_sha256", SHA256_HEX, "release manifest offline_bundle"
        ),
        inventory_path=_relative_path(
            offline, "inventory_path", "release manifest offline_bundle"
        ),
        inventory_sha256=_matching_string(
            offline, "inventory_sha256", SHA256_HEX, "release manifest offline_bundle"
        ),
    )
    release_paths = {
        compose_path,
        architecture_path,
        offline_bundle.archive_path,
        offline_bundle.inventory_path,
    }
    if len(release_paths) != 4 or "release.json" in release_paths:
        raise ContractError("release file paths must be distinct")
    return ReleaseManifest(
        contract_version=contract_version,
        release_id=release_id,
        source_repository=source_repository,
        merge_sha=merge_sha,
        platform=platform,
        compose_path=compose_path,
        compose_sha256=compose_sha,
        architecture_path=architecture_path,
        architecture_profile_id=architecture_profile,
        catalog_revision=catalog_revision,
        architecture_lock_sha256=architecture_sha,
        images=images,
        runtime_services=runtime_services,
        migration=migration,
        offline_bundle=offline_bundle,
    )


def _parse_image(value: object, context: str) -> ImageSpec:
    if not isinstance(value, Mapping):
        raise ContractError(f"{context} must be an object")
    _expect_keys(value, {"service", "reference", "digest", "image_id"}, context)
    service = _matching_string(value, "service", SERVICE, context)
    reference = _matching_string(value, "reference", IMAGE_REFERENCE, context)
    digest = _matching_string(value, "digest", DIGEST, context)
    image_id = _matching_string(value, "image_id", DIGEST, context)
    if not reference.endswith("@" + digest):
        raise ContractError(f"{context} reference does not end with its declared digest")
    return ImageSpec(service=service, reference=reference, digest=digest, image_id=image_id)


def _require_unique_images(images: Sequence[ImageSpec], context: str) -> None:
    services = [item.service for item in images]
    references = [item.reference for item in images]
    if len(set(services)) != len(services):
        raise ContractError(f"{context} contains duplicate image services")
    if len(set(references)) != len(references):
        raise ContractError(f"{context} contains duplicate image references")


def _load_json_object(path: Path, context: str) -> Mapping[str, object]:
    _require_regular_file(path, context)
    try:
        size = path.stat().st_size
        if size > MAX_JSON_BYTES:
            raise ContractError(f"{context} exceeds the maximum JSON size")
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except ContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{context} is not valid strict JSON") from exc
    if not isinstance(value, Mapping):
        raise ContractError(f"{context} root must be an object")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, nested in pairs:
        if key in value:
            raise ContractError(f"duplicate JSON field is forbidden: {key}")
        value[key] = nested
    return value


def _expect_keys(value: Mapping[str, object], required: set[str], context: str) -> None:
    actual = set(value)
    missing = sorted(required - actual)
    unknown = sorted(actual - required)
    if missing:
        raise ContractError(f"{context} is missing fields: {', '.join(missing)}")
    if unknown:
        raise ContractError(f"{context} contains unknown fields: {', '.join(unknown)}")


def _expect_required_and_optional_keys(
    value: Mapping[str, object],
    required: set[str],
    optional: set[str],
    context: str,
) -> None:
    actual = set(value)
    missing = sorted(required - actual)
    unknown = sorted(actual - required - optional)
    if missing:
        raise ContractError(f"{context} is missing fields: {', '.join(missing)}")
    if unknown:
        raise ContractError(f"{context} contains unknown fields: {', '.join(unknown)}")


def _mapping(value: Mapping[str, object], key: str, context: str) -> Mapping[str, object]:
    nested = value.get(key)
    if not isinstance(nested, Mapping):
        raise ContractError(f"{context} {key} must be an object")
    return nested


def _string(value: Mapping[str, object], key: str, context: str) -> str:
    raw = value.get(key)
    if not isinstance(raw, str) or not raw:
        raise ContractError(f"{context} {key} must be a non-empty string")
    if any(ord(character) < 32 for character in raw):
        raise ContractError(f"{context} {key} contains control characters")
    return raw


def _matching_string(
    value: Mapping[str, object], key: str, pattern: re.Pattern[str], context: str
) -> str:
    raw = _string(value, key, context)
    if not pattern.fullmatch(raw):
        raise ContractError(f"{context} {key} has an invalid format")
    return raw


def _string_array(value: object, pattern: re.Pattern[str], context: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ContractError(f"{context} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not pattern.fullmatch(item):
            raise ContractError(f"{context}[{index}] has an invalid format")
        result.append(item)
    return tuple(result)


def _relative_path(value: Mapping[str, object], key: str, context: str) -> str:
    raw = _string(value, key, context)
    if "\\" in raw or len(raw) > 255:
        raise ContractError(f"{context} {key} is not a safe relative path")
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ContractError(f"{context} {key} is not a safe relative path")
    return raw


def _absolute_path(value: Mapping[str, object], key: str, context: str) -> Path:
    raw = _string(value, key, context)
    candidate = Path(raw)
    if not candidate.is_absolute() or ".." in candidate.parts or "\x00" in raw:
        raise ContractError(f"{context} {key} must be a normalized absolute path")
    if str(candidate) != raw:
        raise ContractError(f"{context} {key} must be a normalized absolute path")
    return candidate


def _release_path(directory: Path, relative: str) -> Path:
    candidate = directory / PurePosixPath(relative)
    resolved_parent = candidate.parent.resolve(strict=False)
    _assert_within(resolved_parent, directory.resolve(), "release file")
    current = directory
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ContractError(f"release file must not traverse symlink: {relative}")
    return candidate


def _release_file(directory: Path, relative: str, context: str) -> Path:
    path = _release_path(directory, relative)
    _require_regular_file(path, context)
    return path.resolve()


def _validate_release_inventory(directory: Path, allowed: set[Path]) -> None:
    root = directory.resolve()
    allowed_files = {path.resolve(strict=False) for path in allowed}
    allowed_directories = {root}
    for path in allowed_files:
        parent = path.parent
        while parent != root:
            _assert_within(parent, root, "release file")
            allowed_directories.add(parent)
            parent = parent.parent
    try:
        entries = tuple(directory.rglob("*"))
    except OSError as exc:
        raise ContractError("release directory inventory is unreadable") from exc
    for entry in entries:
        try:
            info = entry.lstat()
        except OSError as exc:
            raise ContractError("release directory inventory changed during validation") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ContractError("release directory inventory must not contain symlinks")
        resolved = entry.resolve(strict=False)
        if stat.S_ISDIR(info.st_mode):
            if resolved not in allowed_directories:
                raise ContractError("release directory contains an undeclared directory")
            continue
        if not stat.S_ISREG(info.st_mode) or resolved not in allowed_files:
            raise ContractError("release directory contains an undeclared file")
        if info.st_mode & 0o022:
            raise ContractError("release files must not be group/world writable")


def _require_directory(path: Path, context: str) -> None:
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise ContractError(f"{context} is unavailable") from exc
    if not stat.S_ISDIR(mode):
        raise ContractError(f"{context} must be a directory")
    if mode & 0o022:
        raise ContractError(f"{context} must not be group/world writable")


def _require_regular_file(path: Path, context: str) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ContractError(f"{context} is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ContractError(f"{context} must be a regular non-symlink file")
    if info.st_mode & 0o022:
        raise ContractError(f"{context} must not be group/world writable")


def _require_protected_file(path: Path, context: str) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ContractError(f"{context} is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ContractError(f"{context} must be a regular non-symlink file")
    mode = stat.S_IMODE(info.st_mode)
    if mode not in {0o400, 0o600}:
        raise ContractError(f"{context} mode must be 0400 or 0600")
    if info.st_uid not in {0, os.geteuid()}:
        raise ContractError(f"{context} owner must be root or the current caller")


def _require_checksum(path: Path, expected: str, context: str) -> None:
    if sha256_file(path) != expected:
        raise ContractError(f"{context} checksum does not match release manifest")


def _reject_sensitive_keys(value: object, context: str, path: str = "") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            field_path = f"{path}.{key_text}" if path else key_text
            if SENSITIVE_KEY.search(key_text):
                raise ContractError(f"{context} contains forbidden sensitive field {field_path}")
            _reject_sensitive_keys(nested, context, field_path)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_sensitive_keys(nested, context, f"{path}[{index}]")


def _reject_path_overlap(first: Path, second: Path, first_name: str, second_name: str) -> None:
    first_resolved = first.resolve(strict=False)
    second_resolved = second.resolve(strict=False)
    if _is_within(first_resolved, second_resolved) or _is_within(second_resolved, first_resolved):
        raise ContractError(f"target profile {first_name} and {second_name} must not overlap")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _assert_within(path: Path, root: Path, context: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ContractError(f"{context} escapes the configured release root") from exc
