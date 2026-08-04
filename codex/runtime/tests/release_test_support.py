from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
from typing import Mapping

from aisoft_release.errors import DeploymentError


SHA_A = "a" * 40
SHA_B = "b" * 40
WEB_DIGEST = "sha256:" + "1" * 64
WEB_IMAGE_ID = "sha256:" + "2" * 64
MIGRATE_DIGEST = "sha256:" + "3" * 64
MIGRATE_IMAGE_ID = "sha256:" + "4" * 64
SOURCE_REPOSITORY = "admin/NewEmaint"
ARCHITECTURE_PROFILE = "linux-node-postgres-v1"
ARCHITECTURE_PROJECT = "newemaint-target-candidate"
CATALOG_REVISION = "2026.08.1"


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def fixture_path(name: str) -> Path:
    return repository_root() / "codex" / "tests" / "fixtures" / "docker-release" / name


def architecture_reference_lock() -> Path:
    return (
        repository_root()
        / "architecture"
        / "reference"
        / "newemaint"
        / "target-candidate"
        / "architecture.lock.json"
    )


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: object, mode: int = 0o644) -> None:
    path.write_bytes(canonical_bytes(value))
    os.chmod(path, mode)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_value(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def refresh_architecture_lock_sha(value: dict[str, object]) -> None:
    payload = deepcopy(value)
    payload.pop("lock_sha256", None)
    value["lock_sha256"] = sha256_value(payload)


def image_specs() -> list[dict[str, str]]:
    return [
        {
            "service": "web",
            "reference": "registry.internal/admin/newemaint-web@" + WEB_DIGEST,
            "digest": WEB_DIGEST,
            "image_id": WEB_IMAGE_ID,
        },
        {
            "service": "migrate",
            "reference": "registry.internal/admin/newemaint-migrate@" + MIGRATE_DIGEST,
            "digest": MIGRATE_DIGEST,
            "image_id": MIGRATE_IMAGE_ID,
        },
    ]


def migration_identity(release_id: str) -> str:
    character = "5" if release_id == SHA_A else "6"
    return "sha256:" + character * 64


def compose_model(release_id: str, *, migration: bool = True) -> dict[str, object]:
    model = json.loads(fixture_path("compose-config-valid.json").read_text())
    services = model["services"]
    assert isinstance(services, dict)
    for name, config in services.items():
        assert isinstance(config, dict)
        labels = config["labels"]
        assert isinstance(labels, dict)
        labels["com.aisoft.release.id"] = release_id
    if not migration:
        services.pop("migrate")
    return model


def create_archive(path: Path, *, unsafe_name: str | None = None) -> None:
    manifest = b"[]\n"
    with tarfile.open(path, mode="w") as archive:
        info = tarfile.TarInfo(unsafe_name or "manifest.json")
        info.size = len(manifest)
        info.mode = 0o644
        archive.addfile(info, io.BytesIO(manifest))
    os.chmod(path, 0o644)


def create_release(
    root: Path,
    release_id: str = SHA_A,
    *,
    transport: str = "registry",
    role: str = "appserver-test",
    migration: bool = True,
) -> tuple[Path, dict[str, object], dict[str, object]]:
    release_root = root / "releases"
    release_dir = release_root / release_id
    release_dir.mkdir(parents=True, mode=0o755)
    os.chmod(release_root, 0o755)
    os.chmod(release_dir, 0o755)

    compose_path = release_dir / "compose.yaml"
    compose_path.write_text("# normalized by fake Docker Compose in tests\n", encoding="utf-8")
    os.chmod(compose_path, 0o644)
    architecture_path = release_dir / "architecture.lock.json"
    architecture = json.loads(architecture_reference_lock().read_text())
    write_json(architecture_path, architecture)

    archive_path = release_dir / "images.tar"
    create_archive(archive_path)
    inventory = {
        "contract_version": "docker-release-offline-inventory/v1",
        "archive_sha256": sha256(archive_path),
        "images": image_specs(),
    }
    if not migration:
        inventory["images"] = image_specs()[:1]
    inventory_path = release_dir / "images.inventory.json"
    write_json(inventory_path, inventory)

    manifest: dict[str, object] = {
        "contract_version": "docker-release/v1",
        "release_id": release_id,
        "source_repository": SOURCE_REPOSITORY,
        "merge_sha": release_id,
        "platform": "linux/amd64",
        "compose": {"path": "compose.yaml", "sha256": sha256(compose_path)},
        "architecture": {
            "path": "architecture.lock.json",
            "profile_id": ARCHITECTURE_PROFILE,
            "catalog_revision": CATALOG_REVISION,
            "sha256": sha256(architecture_path),
        },
        "images": image_specs() if migration else image_specs()[:1],
        "runtime_services": ["web"],
        "migration": (
            {
                "service": "migrate",
                "identity": migration_identity(release_id),
                "destructive": False,
                "database_restore": "manual-only",
            }
            if migration
            else None
        ),
        "offline_bundle": {
            "archive_path": "images.tar",
            "archive_sha256": sha256(archive_path),
            "inventory_path": "images.inventory.json",
            "inventory_sha256": sha256(inventory_path),
        },
    }
    write_json(release_dir / "release.json", manifest)

    env_file = root / "target.env"
    if not env_file.exists():
        env_file.write_text("TEST_ONLY_MARKER=fixture-value\n", encoding="utf-8")
        os.chmod(env_file, 0o600)
    profile = {
        "contract_version": "docker-release-target/v1",
        "profile_id": "newemaint-test",
        "environment": "test",
        "host_role": role,
        "expected_hostname": "test-host",
        "transport": transport,
        "release_root": str(release_root),
        "state_root": str(root / "state"),
        "compose_project": "newemaint-test",
        "env_file": str(env_file),
        "source_repository": SOURCE_REPOSITORY,
        "architecture_profile_id": ARCHITECTURE_PROFILE,
        "architecture_project_id": ARCHITECTURE_PROJECT,
        "catalog_revision": CATALOG_REVISION,
        "wait_timeout_seconds": 30,
    }
    profile_path = root / "target-profile.json"
    write_json(profile_path, profile, mode=0o600)
    return profile_path, compose_model(release_id, migration=migration), manifest


def update_manifest(release_dir: Path, transform: object) -> dict[str, object]:
    path = release_dir / "release.json"
    value = json.loads(path.read_text())
    transform(value)
    write_json(path, value)
    return value


class FakeDocker:
    def __init__(self) -> None:
        self.events: list[tuple[object, ...]] = []
        self.models: dict[str, Mapping[str, object]] = {}
        self.images: dict[str, Mapping[str, object]] = {}
        self.current_release: str | None = None
        self.fail_up_for: set[str] = set()
        self.unhealthy_for: set[str] = set()
        self.fail_migration_for: set[str] = set()

    def register(
        self,
        release_id: str,
        model: Mapping[str, object],
        manifest: Mapping[str, object],
    ) -> None:
        self.models[release_id] = deepcopy(model)
        for image in manifest["images"]:
            assert isinstance(image, Mapping)
            self.images[str(image["reference"])] = {
                "Id": image["image_id"],
                "RepoDigests": [image["reference"]],
                "Os": "linux",
                "Architecture": "amd64",
            }

    @property
    def mutations(self) -> list[tuple[object, ...]]:
        return [
            event
            for event in self.events
            if event[0] in {"pull", "load", "migration", "up"}
        ]

    def compose_config(self, compose_path: Path, project: str) -> Mapping[str, object]:
        release = compose_path.parent.name
        self.events.append(("config", release, project))
        return deepcopy(self.models[release])

    def pull_image(self, reference: str) -> None:
        self.events.append(("pull", reference))

    def load_archive(self, archive_path: Path) -> None:
        self.events.append(("load", archive_path.parent.name))

    def inspect_image(self, reference: str) -> Mapping[str, object]:
        self.events.append(("inspect-image", reference))
        return deepcopy(self.images[reference])

    def run_migration(
        self, compose_path: Path, project: str, env_file: Path, service: str
    ) -> None:
        release = compose_path.parent.name
        self.events.append(("migration", release, project, env_file.name, service))
        if release in self.fail_migration_for:
            raise DeploymentError("fake migration failure")

    def compose_up(
        self,
        compose_path: Path,
        project: str,
        env_file: Path,
        wait_timeout_seconds: int,
    ) -> None:
        release = compose_path.parent.name
        self.events.append(("up", release, project, env_file.name, wait_timeout_seconds))
        if release in self.fail_up_for:
            raise DeploymentError("fake health wait failure")
        self.current_release = release

    def container_ids(
        self, compose_path: Path, project: str, env_file: Path, service: str
    ) -> tuple[str, ...]:
        release = compose_path.parent.name
        self.events.append(("container-ids", release, service))
        if self.current_release != release:
            return ()
        return (release + ":" + service,)

    def inspect_container(self, container_id: str) -> Mapping[str, object]:
        release, service = container_id.split(":", 1)
        self.events.append(("inspect-container", release, service))
        model = self.models[release]
        services = model["services"]
        assert isinstance(services, Mapping)
        config = services[service]
        assert isinstance(config, Mapping)
        labels = config["labels"]
        image_reference = config["image"]
        image = self.images[str(image_reference)]
        return {
            "Image": image["Id"],
            "Config": {"Image": image_reference, "Labels": deepcopy(labels)},
            "State": {
                "Running": True,
                "Health": {
                    "Status": "unhealthy" if release in self.unhealthy_for else "healthy"
                },
            },
        }
