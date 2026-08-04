"""Registry and offline transports for one immutable release manifest."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import tarfile
from typing import Mapping

from .contract import (
    OFFLINE_BUNDLE_V2,
    ImageSpec,
    ReleaseFiles,
    ReleaseManifest,
    load_offline_inventory,
)
from .errors import ContractError, DeploymentError, TransportError


MAX_ARCHIVE_INDEX_BYTES = 8 * 1024 * 1024


class ReleaseTransport:
    def __init__(self, docker: object, files: ReleaseFiles) -> None:
        self.docker = docker
        self.files = files

    def preflight(self) -> None:
        raise NotImplementedError

    def prepare(self) -> None:
        raise NotImplementedError

    def assert_local_images(self) -> None:
        try:
            for image in self.files.manifest.images:
                _verify_local_image(
                    self.docker.inspect_image(image.runtime_reference), image
                )
        except (ContractError, DeploymentError, KeyError) as exc:
            raise TransportError("local runtime image identity verification failed") from exc


class RegistryTransport(ReleaseTransport):
    def preflight(self) -> None:
        # Manifest parsing already proves every reference is digest-pinned.
        return

    def prepare(self) -> None:
        try:
            for image in self.files.manifest.images:
                self.docker.pull_image(image.reference)
                _verify_registry_image(self.docker.inspect_image(image.reference), image)
                if image.is_v2:
                    self.docker.tag_image(image.reference, image.runtime_reference)
                    _verify_local_image(
                        self.docker.inspect_image(image.runtime_reference), image
                    )
        except (ContractError, DeploymentError, KeyError) as exc:
            raise TransportError("registry transport could not verify immutable images") from exc


class OfflineBundleTransport(ReleaseTransport):
    def preflight(self) -> None:
        if self.files.manifest.offline_bundle.contract_version != OFFLINE_BUNDLE_V2:
            raise TransportError(
                "legacy offline bundle must be republished as "
                + OFFLINE_BUNDLE_V2
                + " before image load"
            )
        try:
            load_offline_inventory(self.files)
            _validate_archive_structure(
                self.files.archive_path, self.files.manifest.images
            )
        except ContractError as exc:
            raise TransportError("offline bundle preflight failed before image load") from exc

    def prepare(self) -> None:
        # Repeat the complete preflight immediately before the only mutation.
        self.preflight()
        try:
            self.docker.load_archive(self.files.archive_path)
            for image in self.files.manifest.images:
                _verify_local_image(
                    self.docker.inspect_image(image.runtime_reference), image
                )
        except (ContractError, DeploymentError, KeyError) as exc:
            raise TransportError("offline bundle load or image inspection failed") from exc


def select_transport(kind: str, docker: object, files: ReleaseFiles) -> ReleaseTransport:
    if kind == "registry":
        return RegistryTransport(docker, files)
    if kind == "offline-bundle":
        return OfflineBundleTransport(docker, files)
    raise ContractError("target profile transport is not recognized")


def produce_offline_archive(
    docker: object, manifest: ReleaseManifest, archive_path: Path
) -> None:
    """Pull, tag, verify, then save only v2 release-scoped transport tags."""

    references: list[str] = []
    try:
        for image in manifest.images:
            if not image.is_v2 or image.transport_reference is None:
                raise ContractError(
                    "offline archive production requires v2 image identities"
                )
            docker.pull_image(image.reference)
            _verify_registry_image(docker.inspect_image(image.reference), image)
            docker.tag_image(image.reference, image.transport_reference)
            _verify_local_image(
                docker.inspect_image(image.transport_reference), image
            )
            references.append(image.transport_reference)
        docker.save_images(references, archive_path)
    except (ContractError, DeploymentError, KeyError) as exc:
        raise TransportError(
            "offline archive production failed before a verified tag-only save"
        ) from exc


def _verify_content(value: Mapping[str, object], image: ImageSpec) -> None:
    if value.get("Id") != image.image_id:
        raise ContractError(f"image ID does not match manifest for service {image.service}")
    if value.get("Os") != "linux" or value.get("Architecture") != "amd64":
        raise ContractError(f"image platform does not match linux/amd64 for {image.service}")


def _verify_registry_image(value: Mapping[str, object], image: ImageSpec) -> None:
    _verify_content(value, image)
    repo_digests = value.get("RepoDigests")
    if not isinstance(repo_digests, list) or image.reference not in repo_digests:
        raise ContractError(
            f"image RepoDigests does not contain manifest reference for {image.service}"
        )


def _verify_local_image(value: Mapping[str, object], image: ImageSpec) -> None:
    _verify_content(value, image)
    if not image.is_v2:
        repo_digests = value.get("RepoDigests")
        if not isinstance(repo_digests, list) or image.reference not in repo_digests:
            raise ContractError(
                f"legacy image RepoDigests does not contain manifest reference for {image.service}"
            )
        return
    repo_tags = value.get("RepoTags")
    if not isinstance(repo_tags, list) or image.runtime_reference not in repo_tags:
        raise ContractError(
            f"image RepoTags does not contain runtime reference for {image.service}"
        )


def _validate_archive_structure(path: Path, images: tuple[ImageSpec, ...]) -> None:
    try:
        with tarfile.open(path, mode="r:*") as archive:
            names: set[str] = set()
            manifest_member: tarfile.TarInfo | None = None
            index_member: tarfile.TarInfo | None = None
            repositories_member: tarfile.TarInfo | None = None
            oci_layout_member: tarfile.TarInfo | None = None
            members: dict[str, tarfile.TarInfo] = {}
            for member in archive:
                normalized = _safe_archive_name(member.name)
                if normalized in names:
                    raise ContractError("offline image archive contains duplicate paths")
                names.add(normalized)
                members[normalized] = member
                if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                    raise ContractError("offline image archive contains unsafe member types")
                if not (member.isfile() or member.isdir()):
                    raise ContractError("offline image archive contains unsupported member types")
                if normalized == "manifest.json":
                    manifest_member = member
                elif normalized == "index.json":
                    index_member = member
                elif normalized == "repositories":
                    repositories_member = member
                elif normalized == "oci-layout":
                    oci_layout_member = member
            if manifest_member is None or not manifest_member.isfile():
                raise ContractError("offline image archive is missing manifest.json")
            manifest = _read_archive_json(archive, manifest_member, "manifest.json")
            allowed_members = {"manifest.json"}
            allowed_members.update(
                _validate_docker_manifest(manifest, images, members)
            )
            expected_tags = {
                image.transport_reference
                for image in images
                if image.transport_reference is not None
            }
            if len(expected_tags) != len(images):
                raise ContractError("offline image archive requires v2 transport references")
            if repositories_member is not None:
                repositories = _read_archive_json(
                    archive, repositories_member, "repositories"
                )
                _validate_repositories(repositories, expected_tags)
                allowed_members.add("repositories")
            if index_member is not None:
                index = _read_archive_json(archive, index_member, "index.json")
                allowed_members.add("index.json")
                allowed_members.update(_validate_oci_index_references(index, images))
            if oci_layout_member is not None:
                oci_layout = _read_archive_json(
                    archive, oci_layout_member, "oci-layout"
                )
                if (
                    not isinstance(oci_layout, Mapping)
                    or set(oci_layout) != {"imageLayoutVersion"}
                    or oci_layout.get("imageLayoutVersion") != "1.0.0"
                ):
                    raise ContractError("OCI archive oci-layout is invalid")
                allowed_members.add("oci-layout")
            allowed_directories: set[str] = set()
            for allowed in allowed_members:
                parent = PurePosixPath(allowed).parent
                while str(parent) not in {"", "."}:
                    allowed_directories.add(str(parent))
                    parent = parent.parent
            for name, member in members.items():
                if member.isdir():
                    if name not in allowed_directories:
                        raise ContractError(
                            "offline image archive contains a non-allowlisted directory"
                        )
                elif name not in allowed_members:
                    raise ContractError(
                        "offline image archive contains a non-allowlisted member"
                    )
    except ContractError:
        raise
    except (
        OSError,
        tarfile.TarError,
        UnicodeError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        raise ContractError("offline image archive is invalid or unreadable") from exc


def _read_archive_json(
    archive: tarfile.TarFile, member: tarfile.TarInfo, context: str
) -> object:
    if member.size > MAX_ARCHIVE_INDEX_BYTES:
        raise ContractError(f"offline image archive {context} exceeds bounded size")
    handle = archive.extractfile(member)
    if handle is None:
        raise ContractError(f"offline image archive {context} cannot be read")
    payload = handle.read(MAX_ARCHIVE_INDEX_BYTES + 1)
    if len(payload) > MAX_ARCHIVE_INDEX_BYTES:
        raise ContractError(f"offline image archive {context} exceeds bounded size")
    return json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)


def _validate_docker_manifest(
    value: object,
    images: tuple[ImageSpec, ...],
    members: Mapping[str, tarfile.TarInfo],
) -> set[str]:
    if not isinstance(value, list) or len(value) != len(images):
        raise ContractError("Docker archive manifest.json image count is invalid")
    expected = {
        image.transport_reference: image
        for image in images
        if image.transport_reference is not None
    }
    referenced_members: set[str] = set()
    if len(expected) != len(images):
        raise ContractError("Docker archive manifest requires unique v2 transport tags")
    seen: set[str] = set()
    for index, item in enumerate(value):
        context = f"Docker archive manifest.json[{index}]"
        if not isinstance(item, Mapping):
            raise ContractError(f"{context} must be an object")
        required = {"Config", "RepoTags", "Layers"}
        allowed = required | {"Parent", "LayerSources"}
        if not required.issubset(item) or not set(item).issubset(allowed):
            raise ContractError(f"{context} fields are invalid")
        repo_tags = item.get("RepoTags")
        if (
            not isinstance(repo_tags, list)
            or len(repo_tags) != 1
            or not isinstance(repo_tags[0], str)
            or repo_tags[0] not in expected
            or repo_tags[0] in seen
        ):
            raise ContractError(f"{context} RepoTags are not the exact allowlisted tag")
        tag = repo_tags[0]
        seen.add(tag)
        image = expected[tag]
        config = item.get("Config")
        image_hex = image.image_id.removeprefix("sha256:")
        allowed_configs = {image_hex + ".json", "blobs/sha256/" + image_hex}
        if not isinstance(config, str) or config not in allowed_configs:
            raise ContractError(f"{context} Config does not match the declared image ID")
        config_member = members.get(config)
        if config_member is None or not config_member.isfile():
            raise ContractError(f"{context} Config member is missing")
        referenced_members.add(config)
        layers = item.get("Layers")
        if not isinstance(layers, list) or not layers:
            raise ContractError(f"{context} Layers must be a non-empty array")
        for layer in layers:
            if not isinstance(layer, str) or _safe_archive_name(layer) != layer:
                raise ContractError(f"{context} contains an unsafe layer reference")
            layer_member = members.get(layer)
            if layer_member is None or not layer_member.isfile():
                raise ContractError(f"{context} references a missing layer")
            referenced_members.add(layer)
            layer_path = PurePosixPath(layer)
            if layer_path.name == "layer.tar":
                referenced_members.add(str(layer_path.with_name("VERSION")))
                referenced_members.add(str(layer_path.with_name("json")))
    if seen != set(expected):
        raise ContractError("Docker archive manifest.json is missing transport tags")
    return {
        name for name in referenced_members if name in members
    }


def _validate_repositories(value: object, expected_tags: set[str]) -> None:
    if not isinstance(value, Mapping):
        raise ContractError("Docker archive repositories must be an object")
    actual: set[str] = set()
    for repository, tags in value.items():
        if not isinstance(repository, str) or not isinstance(tags, Mapping):
            raise ContractError("Docker archive repositories entries are invalid")
        for tag, layer in tags.items():
            if not isinstance(tag, str) or not isinstance(layer, str):
                raise ContractError("Docker archive repositories tag entries are invalid")
            actual.add(repository + ":" + tag)
    if actual != expected_tags:
        raise ContractError("Docker archive repositories contains non-allowlisted tags")


def _validate_oci_index_references(
    value: object, images: tuple[ImageSpec, ...]
) -> set[str]:
    if not isinstance(value, Mapping):
        raise ContractError("OCI archive index.json must be an object")
    manifests = value.get("manifests")
    expected = {
        image.transport_reference: image
        for image in images
        if image.transport_reference is not None
    }
    if not isinstance(manifests, list) or len(manifests) != len(expected):
        raise ContractError("OCI archive index.json manifests count is invalid")
    seen: set[str] = set()
    referenced_members: set[str] = set()
    for item in manifests:
        if not isinstance(item, Mapping):
            raise ContractError("OCI archive index.json manifest is invalid")
        annotations = item.get("annotations")
        if not isinstance(annotations, Mapping):
            raise ContractError("OCI archive index.json annotations are invalid")
        ref_name = annotations.get("org.opencontainers.image.ref.name")
        if not isinstance(ref_name, str) or ref_name not in expected or ref_name in seen:
            raise ContractError("OCI archive index.json contains a non-allowlisted tag")
        digest = item.get("digest")
        if digest != expected[ref_name].digest:
            raise ContractError("OCI archive index.json digest does not match manifest")
        seen.add(ref_name)
        referenced_members.add("blobs/sha256/" + expected[ref_name].digest.removeprefix("sha256:"))
    if seen != set(expected):
        raise ContractError("OCI archive index.json is missing transport tags")
    return referenced_members


def _safe_archive_name(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        raise ContractError("offline image archive contains an unsafe path")
    candidate = PurePosixPath(name)
    if candidate.is_absolute() or any(part in {"", ".."} for part in candidate.parts):
        raise ContractError("offline image archive contains path traversal")
    return str(candidate)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result
