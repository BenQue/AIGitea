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
ARCHITECTURE_PROJECT = "newemaint-target-candidate"
CATALOG_REVISION = "2026.08.3"


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
    layer_files: list[tuple[str, bytes]] | None = None,
    layer_archive_payload: bytes | None = None,
    config_environment: list[str] | None = None,
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
            config: dict[str, object] = {}
            if config_environment is not None:
                config["config"] = {"Env": list(config_environment)}
            layer_payload = (
                layer_archive_payload
                if layer_archive_payload is not None
                else create_layer_archive_payload(
                    layer_files
                    if layer_files is not None
                    else [("app/fixture.txt", b"fixture-layer\n")]
                )
            )
            for member_name, payload in (
                (config_path, canonical_bytes(config)),
                (layer_path, layer_payload),
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


def create_layer_archive_payload(
    files: list[tuple[str, bytes]],
    *,
    compression: str | None = None,
) -> bytes:
    output = io.BytesIO()
    mode = "w" if compression is None else f"w:{compression}"
    with tarfile.open(fileobj=output, mode=mode) as archive:
        for name, payload in files:
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            member.mode = 0o644
            archive.addfile(member, io.BytesIO(payload))
    return output.getvalue()


def create_oci_archive(
    path: Path,
    images: list[dict[str, str]],
    *,
    image_store: str,
    ref_name_form: str = "tag",
    tamper: str | None = None,
) -> None:
    if image_store not in {"containerd", "containerd-direct", "classic"}:
        raise ValueError(
            "image_store must be containerd, containerd-direct or classic"
        )
    blobs: dict[str, bytes] = {}
    docker_manifest: list[dict[str, object]] = []
    repositories: dict[str, dict[str, str]] = {}
    top_descriptors: list[dict[str, object]] = []

    def add_blob(payload: bytes) -> tuple[str, str]:
        digest = "sha256:" + hashlib.sha256(payload).hexdigest()
        path_name = "blobs/sha256/" + digest.removeprefix("sha256:")
        blobs[path_name] = payload
        return digest, path_name

    for image in images:
        service = image["service"]
        tag = image["transport_reference"]
        config_payload = canonical_bytes(
            {"architecture": "amd64", "fixture_service": service, "os": "linux"}
        )
        config_digest, config_path = add_blob(config_payload)
        layer_payload = create_layer_archive_payload(
            [("app/fixture.txt", (f"fixture-layer:{service}\n").encode("utf-8"))]
        )
        layer_digest, layer_path = add_blob(layer_payload)
        runnable_manifest = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {
                "mediaType": "application/vnd.oci.image.config.v1+json",
                "digest": config_digest,
                "size": len(config_payload),
            },
            "layers": [
                {
                    "mediaType": "application/vnd.oci.image.layer.v1.tar",
                    "digest": layer_digest,
                    "size": len(layer_payload),
                }
            ],
        }
        runnable_bytes = canonical_bytes(runnable_manifest)
        runnable_digest, _runnable_path = add_blob(runnable_bytes)
        runnable_descriptor: dict[str, object] = {
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "digest": runnable_digest,
            "size": len(runnable_bytes),
            "platform": {"architecture": "amd64", "os": "linux"},
        }

        if image_store == "containerd":
            attestation_config = canonical_bytes({})
            attestation_config_digest, _ = add_blob(attestation_config)
            attestation_payload = canonical_bytes(
                {"_type": "https://in-toto.io/Statement/v1", "subject": []}
            )
            attestation_layer_digest, _ = add_blob(attestation_payload)
            attestation_manifest = {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {
                    "mediaType": "application/vnd.oci.empty.v1+json",
                    "digest": attestation_config_digest,
                    "size": len(attestation_config),
                },
                "layers": [
                    {
                        "mediaType": "application/vnd.in-toto+json",
                        "digest": attestation_layer_digest,
                        "size": len(attestation_payload),
                    }
                ],
            }
            attestation_bytes = canonical_bytes(attestation_manifest)
            attestation_digest, _attestation_path = add_blob(attestation_bytes)
            attestation_reference = (
                "sha256:" + "f" * 64
                if tamper == "attestation-reference"
                else runnable_digest
            )
            image_index = {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [
                    runnable_descriptor,
                    {
                        "mediaType": "application/vnd.oci.image.manifest.v1+json",
                        "digest": attestation_digest,
                        "size": len(attestation_bytes),
                        "annotations": {
                            "vnd.docker.reference.digest": attestation_reference,
                            "vnd.docker.reference.type": "attestation-manifest",
                        },
                        "platform": {
                            "architecture": "unknown",
                            "os": "unknown",
                        },
                    },
                ],
            }
            top_bytes = canonical_bytes(image_index)
            top_digest, top_path = add_blob(top_bytes)
            top_media_type = "application/vnd.oci.image.index.v1+json"
            image["image_id"] = top_digest
            image["digest"] = top_digest
            image["reference"] = image["reference"].split("@", 1)[0] + "@" + top_digest
        elif image_store == "containerd-direct":
            top_bytes = runnable_bytes
            top_digest = runnable_digest
            top_path = _runnable_path
            top_media_type = "application/vnd.oci.image.manifest.v1+json"
            image["image_id"] = top_digest
            image["digest"] = top_digest
            image["reference"] = image["reference"].split("@", 1)[0] + "@" + top_digest
        else:
            top_bytes = runnable_bytes
            top_digest = runnable_digest
            top_path = _runnable_path
            top_media_type = "application/vnd.oci.image.manifest.v1+json"
            image["image_id"] = config_digest
            metadata_id = hashlib.sha256(
                ("classic-layer:" + service).encode("utf-8")
            ).hexdigest()
            classic_metadata: dict[str, object] = {
                "architecture": "amd64",
                "config": {},
                "container_config": {},
                "created": "2026-08-08T00:00:00Z",
                "id": metadata_id,
                "os": "linux",
            }
            if tamper == "classic-metadata-parent":
                classic_metadata["parent"] = "f" * 64
            metadata_payload = canonical_bytes(classic_metadata)
            _metadata_digest, metadata_path = add_blob(metadata_payload)
            if tamper == "classic-metadata-content":
                blobs[metadata_path] = metadata_payload + b" "
        if tamper == "top-content":
            blobs[top_path] = top_bytes + b" "

        exact_tag = tag.rsplit(":", 1)[1]
        ref_name = tag if ref_name_form == "full" else exact_tag
        if tamper == "reference":
            ref_name = "b" * 40
        annotations = {
            "io.containerd.image.name": tag,
            "org.opencontainers.image.ref.name": ref_name,
        }
        top_descriptors.append(
            {
                "mediaType": top_media_type,
                "digest": top_digest,
                "size": (
                    True if tamper == "descriptor-size-bool" else len(top_bytes)
                ),
                "annotations": annotations,
            }
        )
        docker_config = config_path
        if tamper == "graph-config":
            _wrong_digest, docker_config = add_blob(
                canonical_bytes({"fixture_service": service, "wrong": True})
            )
        layer_source_size = (
            len(layer_payload) + 1
            if tamper == "layer-source-size"
            else len(layer_payload)
        )
        docker_manifest.append(
            {
                "Config": docker_config,
                "RepoTags": [tag],
                "Layers": [layer_path],
                "LayerSources": {
                    layer_digest: {
                        "digest": layer_digest,
                        "mediaType": "application/vnd.oci.image.layer.v1.tar",
                        "size": layer_source_size,
                    }
                },
            }
        )
        if tamper == "declared-image-id":
            image["image_id"] = "sha256:" + (
                "d" if service == "web" else "e"
            ) * 64
        repository, nested_tag = tag.rsplit(":", 1)
        repositories.setdefault(repository, {})[nested_tag] = layer_digest

    if tamper == "extra-descriptor":
        top_descriptors.append(deepcopy(top_descriptors[0]))
    with tarfile.open(path, mode="w") as archive:
        members = {
            **blobs,
            "manifest.json": canonical_bytes(docker_manifest),
            "repositories": canonical_bytes(repositories),
            "index.json": canonical_bytes(
                {
                    "schemaVersion": (
                        1 if tamper == "index-schema-version" else 2
                    ),
                    "manifests": top_descriptors,
                }
            ),
            "oci-layout": canonical_bytes({"imageLayoutVersion": "1.0.0"}),
        }
        for member_name, payload in members.items():
            member = tarfile.TarInfo(member_name)
            member.size = len(payload)
            member.mode = 0o644
            archive.addfile(member, io.BytesIO(payload))
    os.chmod(path, 0o644)


def create_release(
    root: Path,
    release_id: str = SHA_A,
    *,
    transport: str = "registry",
    role: str = "appserver-test",
    migration: bool = True,
    identity_version: str = "v2",
    contract_version: str | None = None,
) -> tuple[Path, dict[str, object], dict[str, object]]:
    release_root = root / "releases"
    release_dir = release_root / release_id
    release_dir.mkdir(parents=True, mode=0o755)
    os.chmod(release_root, 0o755)
    os.chmod(release_dir, 0o755)

    compose_path = release_dir / "compose.yaml"
    compose_path.write_text("# normalized by fake Docker Compose in tests\n", encoding="utf-8")
    os.chmod(compose_path, 0o644)
    normalized_model = compose_model(
        release_id,
        migration=migration,
        identity_version=identity_version,
    )
    if contract_version is None:
        contract_version = (
            "docker-release/v2" if identity_version == "v2" else "docker-release/v1"
        )
    compose_contract: dict[str, object] = {
        "path": "compose.yaml",
        "sha256": sha256(compose_path),
    }
    if contract_version == "docker-release/v2":
        compose_model_path = release_dir / "compose.model.json"
        write_json(compose_model_path, normalized_model)
        compose_contract.update(
            {
                "model_path": "compose.model.json",
                "model_sha256": sha256(compose_model_path),
            }
        )
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
        "contract_version": contract_version,
        "release_id": release_id,
        "source_repository": SOURCE_REPOSITORY,
        "merge_sha": release_id,
        "platform": "linux/amd64",
        "compose": compose_contract,
        "architecture": {
            "path": "architecture.lock.json",
            "profile_id": ARCHITECTURE_PROFILE,
            **(
                {"project_id": ARCHITECTURE_PROJECT}
                if contract_version == "docker-release/v2"
                else {}
            ),
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
        "architecture_project_id": ARCHITECTURE_PROJECT,
        "catalog_revision": CATALOG_REVISION,
        "wait_timeout_seconds": 30,
    }
    profile_path = root / "target-profile.json"
    write_json(profile_path, profile, mode=0o600)
    return (
        profile_path,
        normalized_model,
        manifest,
    )


def update_manifest(release_dir: Path, transform: object) -> dict[str, object]:
    path = release_dir / "release.json"
    value = json.loads(path.read_text())
    transform(value)
    write_json(path, value)
    return value


def update_compose_model(release_dir: Path, transform: object) -> dict[str, object]:
    path = release_dir / "compose.model.json"
    value = json.loads(path.read_text())
    transform(value)
    write_json(path, value)
    update_manifest(
        release_dir,
        lambda manifest: manifest["compose"].update({"model_sha256": sha256(path)}),
    )
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
