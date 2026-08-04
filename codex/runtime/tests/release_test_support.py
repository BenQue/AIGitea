from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
from typing import Mapping

from aisoft_release.compatibility import CompatibilityDecision, DockerCapability
from aisoft_release.errors import DeploymentError


SHA_A = "a" * 40
SHA_B = "b" * 40
WEB_DIGEST = "sha256:" + "1" * 64
WEB_IMAGE_ID = "sha256:" + "2" * 64
MIGRATE_DIGEST = "sha256:" + "3" * 64
MIGRATE_IMAGE_ID = "sha256:" + "4" * 64
SOURCE_REPOSITORY = "admin/NewEmaint"
ARCHITECTURE_PROFILE = "linux-node-postgres-v1"
CATALOG_REVISION = "2026.08.0"


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


def runtime_reference(service: str, release_id: str) -> str:
    return f"aisoft.local/admin/newemaint/{service}:{release_id}"


def image_specs(
    release_id: str = SHA_A, *, identity_version: str = "v2"
) -> list[dict[str, str]]:
    images = json.loads(fixture_path("newemaint-v2-images.json").read_text())
    for image in images:
        image.pop("platform")
        image["transport_reference"] = runtime_reference(image["service"], release_id)
        image["runtime_reference"] = runtime_reference(image["service"], release_id)
    if identity_version == "v2":
        return images
    if identity_version == "legacy":
        for image in images:
            image.pop("transport_reference")
            image.pop("runtime_reference")
        return images
    raise ValueError("identity_version must be v2 or legacy")


def migration_identity(release_id: str) -> str:
    character = "5" if release_id == SHA_A else "6"
    return "sha256:" + character * 64


def compose_model(
    release_id: str,
    *,
    migration: bool = True,
    identity_version: str = "v2",
) -> dict[str, object]:
    model = json.loads(fixture_path("compose-config-valid.json").read_text())
    services = model["services"]
    assert isinstance(services, dict)
    references = {
        image["service"]: image.get("runtime_reference") or image["reference"]
        for image in image_specs(release_id, identity_version=identity_version)
    }
    for name, config in services.items():
        assert isinstance(config, dict)
        labels = config["labels"]
        assert isinstance(labels, dict)
        labels["com.aisoft.release.id"] = release_id
        config["image"] = references[str(name)]
    if not migration:
        services.pop("migrate")
    return model


def create_archive(
    path: Path,
    images: list[dict[str, str]],
    *,
    unsafe_name: str | None = None,
) -> None:
    with tarfile.open(path, mode="w") as archive:
        if unsafe_name is not None:
            manifest_bytes = b"[]\n"
            info = tarfile.TarInfo(unsafe_name)
            info.size = len(manifest_bytes)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(manifest_bytes))
            os.chmod(path, 0o644)
            return
        manifest: list[dict[str, object]] = []
        repositories: dict[str, dict[str, str]] = {}
        for index, image in enumerate(images):
            image_hex = image["image_id"].removeprefix("sha256:")
            layer_path = f"layers/{index}/layer.tar"
            config_path = image_hex + ".json"
            tag = image.get("transport_reference")
            repo_tags = [tag] if tag is not None else []
            manifest.append(
                {"Config": config_path, "RepoTags": repo_tags, "Layers": [layer_path]}
            )
            for member_name, payload in (
                (config_path, b"{}\n"),
                (layer_path, b"fixture-layer\n"),
            ):
                member = tarfile.TarInfo(member_name)
                member.size = len(payload)
                member.mode = 0o644
                archive.addfile(member, io.BytesIO(payload))
            if tag is not None:
                repository, nested_tag = tag.rsplit(":", 1)
                repositories.setdefault(repository, {})[nested_tag] = str(index)
        manifest_bytes = canonical_bytes(manifest)
        info = tarfile.TarInfo("manifest.json")
        info.size = len(manifest_bytes)
        info.mode = 0o644
        archive.addfile(info, io.BytesIO(manifest_bytes))
        if repositories:
            repositories_bytes = canonical_bytes(repositories)
            repositories_info = tarfile.TarInfo("repositories")
            repositories_info.size = len(repositories_bytes)
            repositories_info.mode = 0o644
            archive.addfile(repositories_info, io.BytesIO(repositories_bytes))
    os.chmod(path, 0o644)


def create_release(
    root: Path,
    release_id: str = SHA_A,
    *,
    transport: str = "registry",
    role: str = "appserver-test",
    migration: bool = True,
    identity_version: str = "v2",
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
    images = image_specs(release_id, identity_version=identity_version)
    if not migration:
        images = images[:1]
    create_archive(archive_path, images)
    inventory = {
        "contract_version": (
            "docker-release-offline-inventory/v2"
            if identity_version == "v2"
            else "docker-release-offline-inventory/v1"
        ),
        "archive_sha256": sha256(archive_path),
        "images": deepcopy(images),
    }
    if identity_version == "v2":
        for image in inventory["images"]:
            image["platform"] = "linux/amd64"
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
        "images": images,
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
            **(
                {"contract_version": "docker-release-offline-bundle/v2"}
                if identity_version == "v2"
                else {}
            ),
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
        "catalog_revision": CATALOG_REVISION,
        "wait_timeout_seconds": 30,
    }
    profile_path = root / "target-profile.json"
    write_json(profile_path, profile, mode=0o600)
    return (
        profile_path,
        compose_model(
            release_id,
            migration=migration,
            identity_version=identity_version,
        ),
        manifest,
    )


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
        self.manifests: dict[str, Mapping[str, object]] = {}
        self.current_release: str | None = None
        self.fail_up_for: set[str] = set()
        self.unhealthy_for: set[str] = set()
        self.fail_migration_for: set[str] = set()
        self.tamper_container_image_for: set[str] = set()
        self.tamper_container_reference_for: set[str] = set()
        self.tamper_container_release_label_for: set[str] = set()
        self.wrong_loaded_image_for: set[str] = set()
        self.omit_runtime_tag_on_load_for: set[str] = set()
        self.capability_error: DeploymentError | None = None

    def register(
        self,
        release_id: str,
        model: Mapping[str, object],
        manifest: Mapping[str, object],
    ) -> None:
        self.models[release_id] = deepcopy(model)
        self.manifests[release_id] = deepcopy(manifest)
        for image in manifest["images"]:
            assert isinstance(image, Mapping)
            self.images[str(image["reference"])] = {
                "Id": image["image_id"],
                "RepoDigests": [image["reference"]],
                "RepoTags": [],
                "Os": "linux",
                "Architecture": "amd64",
            }

    @property
    def mutations(self) -> list[tuple[object, ...]]:
        return [
            event
            for event in self.events
            if event[0] in {"pull", "tag", "save", "load", "migration", "up"}
        ]

    def assert_runtime_compatible(self) -> CompatibilityDecision:
        capability = DockerCapability(
            engine_version="29.0.1",
            compose_version="2.40.3",
            os="linux",
            architecture="amd64",
            image_store="containerd",
        )
        self.events.append(("capability", "containerd", "fake-supported-row"))
        if self.capability_error is not None:
            raise self.capability_error
        return CompatibilityDecision(
            matrix_revision="test.fake.1",
            row_id="fake-supported-row",
            capability=capability,
        )

    def compose_config(self, compose_path: Path, project: str) -> Mapping[str, object]:
        release = compose_path.parent.name
        self.events.append(("config", release, project))
        return deepcopy(self.models[release])

    def pull_image(self, reference: str) -> None:
        self.events.append(("pull", reference))

    def tag_image(self, source_reference: str, target_reference: str) -> None:
        self.events.append(("tag", source_reference, target_reference))
        source = deepcopy(self.images[source_reference])
        source["RepoTags"] = [target_reference]
        self.images[target_reference] = source

    def save_images(self, references: list[str], archive_path: Path) -> None:
        self.events.append(("save", tuple(references), archive_path.name))

    def load_archive(self, archive_path: Path) -> None:
        release = archive_path.parent.name
        self.events.append(("load", release))
        manifest = self.manifests[release]
        for image in manifest["images"]:
            assert isinstance(image, Mapping)
            runtime = str(image.get("runtime_reference") or image["reference"])
            self.images[runtime] = {
                "Id": (
                    "sha256:" + "e" * 64
                    if release in self.wrong_loaded_image_for
                    else image["image_id"]
                ),
                "RepoDigests": [],
                "RepoTags": (
                    [] if release in self.omit_runtime_tag_on_load_for else [runtime]
                ),
                "Os": "linux",
                "Architecture": "amd64",
            }

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
        inspected_labels = deepcopy(labels)
        if release in self.tamper_container_release_label_for:
            inspected_labels["com.aisoft.release.id"] = "f" * 40
        return {
            "Image": (
                "sha256:" + "f" * 64
                if release in self.tamper_container_image_for
                else image["Id"]
            ),
            "Config": {
                "Image": (
                    "aisoft.local/admin/newemaint/wrong:" + release
                    if release in self.tamper_container_reference_for
                    else image_reference
                ),
                "Labels": inspected_labels,
            },
            "State": {
                "Running": True,
                "Health": {
                    "Status": "unhealthy" if release in self.unhealthy_for else "healthy"
                },
            },
        }
