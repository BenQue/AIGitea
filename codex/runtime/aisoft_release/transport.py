"""Registry and offline transports for one immutable release manifest."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
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
OCI_INDEX_MEDIA_TYPE = "application/vnd.oci.image.index.v1+json"
OCI_MANIFEST_MEDIA_TYPE = "application/vnd.oci.image.manifest.v1+json"
OCI_ATTESTATION_TYPE = "attestation-manifest"


@dataclass(frozen=True)
class _DockerArchiveImage:
    image: ImageSpec
    config: str
    layers: tuple[str, ...]


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


def validate_offline_artifact(files: ReleaseFiles) -> None:
    """Validate the producer bundle without constructing or calling Docker."""

    OfflineBundleTransport(object(), files).preflight()


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
            docker_members, docker_images = _validate_docker_manifest(
                manifest, images, archive, members
            )
            allowed_members.update(docker_members)
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
                allowed_members.update(
                    _validate_oci_index_references(
                        index, docker_images, archive, members
                    )
                )
            else:
                _validate_docker_only_image_ids(docker_images)
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
            unexpected_files = {
                name
                for name, member in members.items()
                if member.isfile() and name not in allowed_members
            }
            if unexpected_files:
                allowed_members.update(
                    _validate_classic_layer_metadata(
                        archive, members, unexpected_files, docker_images
                    )
                )
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
    archive: tarfile.TarFile,
    members: Mapping[str, tarfile.TarInfo],
) -> tuple[set[str], dict[str, _DockerArchiveImage]]:
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
    archive_images: dict[str, _DockerArchiveImage] = {}
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
        if not isinstance(config, str) or _safe_archive_name(config) != config:
            raise ContractError(f"{context} Config reference is invalid")
        config_member = members.get(config)
        if config_member is None or not config_member.isfile():
            raise ContractError(f"{context} Config member is missing")
        referenced_members.add(config)
        layers = item.get("Layers")
        if not isinstance(layers, list) or not layers:
            raise ContractError(f"{context} Layers must be a non-empty array")
        normalized_layers: list[str] = []
        for layer in layers:
            if not isinstance(layer, str) or _safe_archive_name(layer) != layer:
                raise ContractError(f"{context} contains an unsafe layer reference")
            layer_member = members.get(layer)
            if layer_member is None or not layer_member.isfile():
                raise ContractError(f"{context} references a missing layer")
            normalized_layers.append(layer)
            referenced_members.add(layer)
            layer_path = PurePosixPath(layer)
            if layer_path.name == "layer.tar":
                referenced_members.add(str(layer_path.with_name("VERSION")))
                referenced_members.add(str(layer_path.with_name("json")))
        layer_sources = item.get("LayerSources")
        if layer_sources is not None:
            if not isinstance(layer_sources, Mapping):
                raise ContractError(f"{context} LayerSources must be an object")
            expected_layer_digests = {
                "sha256:" + PurePosixPath(layer).name
                for layer in normalized_layers
                if layer.startswith("blobs/sha256/")
            }
            if set(layer_sources) != expected_layer_digests:
                raise ContractError(
                    f"{context} LayerSources do not exactly match Layers"
                )
            for digest, descriptor in layer_sources.items():
                if (
                    not isinstance(digest, str)
                    or not isinstance(descriptor, Mapping)
                    or descriptor.get("digest") != digest
                ):
                    raise ContractError(
                        f"{context} LayerSources descriptor is invalid"
                    )
                _verified_digest, member_name = _validated_descriptor_member(
                    archive, members, descriptor, f"{context} LayerSources"
                )
                if member_name not in normalized_layers:
                    raise ContractError(
                        f"{context} LayerSources references a non-layer blob"
                    )
        archive_images[tag] = _DockerArchiveImage(
            image=image,
            config=config,
            layers=tuple(normalized_layers),
        )
    if seen != set(expected):
        raise ContractError("Docker archive manifest.json is missing transport tags")
    return (
        {name for name in referenced_members if name in members},
        archive_images,
    )


def _validate_docker_only_image_ids(
    images: Mapping[str, _DockerArchiveImage],
) -> None:
    for entry in images.values():
        image_hex = entry.image.image_id.removeprefix("sha256:")
        if entry.config != image_hex + ".json":
            raise ContractError(
                "Docker archive Config does not match the declared image ID "
                f"for {entry.image.service}"
            )


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


def _validate_classic_layer_metadata(
    archive: tarfile.TarFile,
    members: Mapping[str, tarfile.TarInfo],
    names: set[str],
    images: Mapping[str, _DockerArchiveImage],
) -> set[str]:
    expected_unique_layers = {
        layer for entry in images.values() for layer in entry.layers
    }
    if len(names) != len(expected_unique_layers):
        raise ContractError(
            "Docker classic archive layer metadata count is inconsistent"
        )
    nodes: dict[str, tuple[str | None, str, bool]] = {}
    allowed_fields = {
        "architecture",
        "config",
        "container_config",
        "created",
        "id",
        "os",
        "parent",
    }
    required_fields = {"container_config", "created", "id", "os"}
    for name in names:
        if not name.startswith("blobs/sha256/"):
            raise ContractError(
                "Docker classic archive metadata path is not content-addressed"
            )
        member = members[name]
        digest = "sha256:" + PurePosixPath(name).name
        _digest, verified_name = _validated_descriptor_member(
            archive,
            members,
            {"digest": digest, "size": member.size},
            "Docker classic archive layer metadata",
        )
        if verified_name != name:
            raise ContractError("Docker classic archive metadata path is inconsistent")
        value = _read_archive_json(archive, member, name)
        if (
            not isinstance(value, Mapping)
            or not required_fields.issubset(value)
            or not set(value).issubset(allowed_fields)
            or not isinstance(value.get("created"), str)
            or not isinstance(value.get("container_config"), Mapping)
            or value.get("os") != "linux"
        ):
            raise ContractError("Docker classic archive layer metadata is invalid")
        architecture = value.get("architecture")
        if architecture is not None and architecture != "amd64":
            raise ContractError(
                "Docker classic archive layer metadata platform is invalid"
            )
        if "config" in value and not isinstance(value.get("config"), Mapping):
            raise ContractError(
                "Docker classic archive layer metadata config is invalid"
            )
        identifier = value.get("id")
        parent = value.get("parent")
        if not _is_hex64(identifier) or (
            parent is not None and not _is_hex64(parent)
        ):
            raise ContractError(
                "Docker classic archive layer metadata identity is invalid"
            )
        if identifier in nodes:
            raise ContractError(
                "Docker classic archive layer metadata contains duplicate IDs"
            )
        nodes[identifier] = (parent, name, "config" in value)
    for parent, _name, _has_config in nodes.values():
        if parent is not None and parent not in nodes:
            raise ContractError(
                "Docker classic archive layer metadata parent is missing"
            )
    roots = {
        identifier for identifier, (parent, _name, _has_config) in nodes.items()
        if parent is None
    }
    parents = {
        parent for parent, _name, _has_config in nodes.values()
        if parent is not None
    }
    leaves = set(nodes) - parents
    configured = {
        identifier
        for identifier, (_parent, _name, has_config) in nodes.items()
        if has_config
    }
    if (
        not roots
        or len(roots) > len(leaves)
        or configured != leaves
        or len(leaves) != len(images)
    ):
        raise ContractError(
            "Docker classic archive layer metadata graph shape is invalid"
        )
    chain_lengths: list[int] = []
    visited: set[str] = set()
    for leaf in leaves:
        current: str | None = leaf
        chain: set[str] = set()
        while current is not None:
            if current in chain:
                raise ContractError(
                    "Docker classic archive layer metadata graph contains a cycle"
                )
            chain.add(current)
            visited.add(current)
            current = nodes[current][0]
        chain_lengths.append(len(chain))
    if visited != set(nodes) or sorted(chain_lengths) != sorted(
        len(entry.layers) for entry in images.values()
    ):
        raise ContractError(
            "Docker classic archive layer metadata graph does not match image layers"
        )
    return {name for _parent, name, _has_config in nodes.values()}


def _validate_oci_index_references(
    value: object,
    images: Mapping[str, _DockerArchiveImage],
    archive: tarfile.TarFile,
    members: Mapping[str, tarfile.TarInfo],
) -> set[str]:
    if not isinstance(value, Mapping) or value.get("schemaVersion") != 2:
        raise ContractError("OCI archive index.json must be an object")
    manifests = value.get("manifests")
    if not isinstance(manifests, list) or len(manifests) != len(images):
        raise ContractError("OCI archive index.json manifests count is invalid")
    seen: set[str] = set()
    referenced_members: set[str] = set()
    for item in manifests:
        if not isinstance(item, Mapping):
            raise ContractError("OCI archive index.json manifest is invalid")
        annotations = item.get("annotations")
        if not isinstance(annotations, Mapping):
            raise ContractError("OCI archive index.json annotations are invalid")
        reference = _oci_transport_reference(annotations, set(images))
        if reference in seen:
            raise ContractError("OCI archive index.json contains duplicate transport tags")
        seen.add(reference)
        entry = images[reference]
        digest, descriptor_member = _validated_descriptor_member(
            archive, members, item, "OCI archive index.json manifest"
        )
        referenced_members.add(descriptor_member)
        descriptor = _read_archive_json(
            archive, members[descriptor_member], descriptor_member
        )
        media_type = item.get("mediaType")
        if not isinstance(descriptor, Mapping) or descriptor.get("mediaType") != media_type:
            raise ContractError("OCI archive descriptor media type is inconsistent")
        if media_type == OCI_MANIFEST_MEDIA_TYPE:
            referenced_members.update(
                _validate_oci_manifest_graph(
                    descriptor,
                    archive,
                    members,
                    expected=entry,
                    context=f"OCI image manifest for {entry.image.service}",
                )
            )
            config_digest = _oci_config_digest(descriptor)
            if entry.image.image_id != config_digest:
                raise ContractError(
                    "OCI image manifest Config does not match the declared image ID "
                    f"for {entry.image.service}"
                )
        elif media_type == OCI_INDEX_MEDIA_TYPE:
            if entry.image.image_id != digest:
                raise ContractError(
                    "OCI image index digest does not match the declared image ID "
                    f"for {entry.image.service}"
                )
            referenced_members.update(
                _validate_nested_oci_index(
                    descriptor, entry, archive, members
                )
            )
        else:
            raise ContractError("OCI archive index.json media type is unsupported")
    if seen != set(images):
        raise ContractError("OCI archive index.json is missing transport tags")
    return referenced_members


def _oci_transport_reference(
    annotations: Mapping[str, object], expected: set[str]
) -> str:
    full_name = annotations.get("io.containerd.image.name")
    ref_name = annotations.get("org.opencontainers.image.ref.name")
    if full_name is None:
        if not isinstance(ref_name, str) or ref_name not in expected:
            raise ContractError("OCI archive index.json contains a non-allowlisted tag")
        return ref_name
    if not isinstance(full_name, str) or full_name not in expected:
        raise ContractError("OCI archive index.json contains a non-allowlisted image name")
    exact_tag = full_name.rsplit(":", 1)[-1]
    if not isinstance(ref_name, str) or ref_name not in {full_name, exact_tag}:
        raise ContractError("OCI archive index.json reference annotations disagree")
    return full_name


def _validate_nested_oci_index(
    value: Mapping[str, object],
    expected: _DockerArchiveImage,
    archive: tarfile.TarFile,
    members: Mapping[str, tarfile.TarInfo],
) -> set[str]:
    if value.get("schemaVersion") != 2 or value.get("mediaType") != OCI_INDEX_MEDIA_TYPE:
        raise ContractError("OCI image index is invalid")
    descriptors = value.get("manifests")
    if not isinstance(descriptors, list) or not descriptors:
        raise ContractError("OCI image index manifests must be a non-empty array")
    runnable: tuple[str, Mapping[str, object]] | None = None
    attestations: list[tuple[Mapping[str, object], str, Mapping[str, object]]] = []
    referenced: set[str] = set()
    for descriptor in descriptors:
        if not isinstance(descriptor, Mapping):
            raise ContractError("OCI image index contains an invalid descriptor")
        digest, member_name = _validated_descriptor_member(
            archive, members, descriptor, "OCI image index descriptor"
        )
        referenced.add(member_name)
        child = _read_archive_json(archive, members[member_name], member_name)
        if (
            not isinstance(child, Mapping)
            or descriptor.get("mediaType") != OCI_MANIFEST_MEDIA_TYPE
            or child.get("mediaType") != OCI_MANIFEST_MEDIA_TYPE
        ):
            raise ContractError("OCI image index child media type is unsupported")
        platform = descriptor.get("platform")
        annotations = descriptor.get("annotations")
        if platform == {"architecture": "amd64", "os": "linux"}:
            if runnable is not None or (
                isinstance(annotations, Mapping)
                and annotations.get("vnd.docker.reference.type") is not None
            ):
                raise ContractError("OCI image index runnable manifest is ambiguous")
            runnable = (digest, child)
            continue
        if (
            platform != {"architecture": "unknown", "os": "unknown"}
            or not isinstance(annotations, Mapping)
            or annotations.get("vnd.docker.reference.type") != OCI_ATTESTATION_TYPE
        ):
            raise ContractError("OCI image index contains a non-allowlisted child")
        attestations.append((descriptor, digest, child))
    if runnable is None:
        raise ContractError("OCI image index is missing linux/amd64 manifest")
    runnable_digest, runnable_manifest = runnable
    referenced.update(
        _validate_oci_manifest_graph(
            runnable_manifest,
            archive,
            members,
            expected=expected,
            context=f"OCI runnable manifest for {expected.image.service}",
        )
    )
    for descriptor, _digest, attestation in attestations:
        annotations = descriptor["annotations"]
        if annotations.get("vnd.docker.reference.digest") != runnable_digest:
            raise ContractError("OCI attestation does not reference the runnable manifest")
        referenced.update(
            _validate_oci_manifest_graph(
                attestation,
                archive,
                members,
                expected=None,
                context=f"OCI attestation manifest for {expected.image.service}",
            )
        )
    return referenced


def _validate_oci_manifest_graph(
    value: Mapping[str, object],
    archive: tarfile.TarFile,
    members: Mapping[str, tarfile.TarInfo],
    *,
    expected: _DockerArchiveImage | None,
    context: str,
) -> set[str]:
    if value.get("schemaVersion") != 2 or value.get("mediaType") != OCI_MANIFEST_MEDIA_TYPE:
        raise ContractError(f"{context} is invalid")
    config = value.get("config")
    layers = value.get("layers")
    if not isinstance(config, Mapping) or not isinstance(layers, list) or not layers:
        raise ContractError(f"{context} config or layers are invalid")
    _config_digest, config_member = _validated_descriptor_member(
        archive, members, config, f"{context} config"
    )
    layer_members: list[str] = []
    for layer in layers:
        if not isinstance(layer, Mapping):
            raise ContractError(f"{context} contains an invalid layer descriptor")
        _digest, member_name = _validated_descriptor_member(
            archive, members, layer, f"{context} layer"
        )
        layer_members.append(member_name)
    if expected is not None and (
        config_member != expected.config
        or tuple(layer_members) != expected.layers
    ):
        raise ContractError(
            f"{context} does not match Docker manifest Config and layers"
        )
    return {config_member, *layer_members}


def _oci_config_digest(value: Mapping[str, object]) -> str:
    config = value.get("config")
    if not isinstance(config, Mapping):
        raise ContractError("OCI image manifest config is invalid")
    digest = config.get("digest")
    if not _is_sha256_digest(digest):
        raise ContractError("OCI image manifest config digest is invalid")
    return digest


def _validated_descriptor_member(
    archive: tarfile.TarFile,
    members: Mapping[str, tarfile.TarInfo],
    descriptor: Mapping[str, object],
    context: str,
) -> tuple[str, str]:
    digest = descriptor.get("digest")
    size = descriptor.get("size")
    if (
        not _is_sha256_digest(digest)
        or not isinstance(size, int)
        or isinstance(size, bool)
        or size < 0
    ):
        raise ContractError(f"{context} digest or size is invalid")
    member_name = "blobs/sha256/" + digest.removeprefix("sha256:")
    member = members.get(member_name)
    if member is None or not member.isfile() or member.size != size:
        raise ContractError(f"{context} blob is missing or has the wrong size")
    handle = archive.extractfile(member)
    if handle is None:
        raise ContractError(f"{context} blob cannot be read")
    actual = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        actual.update(chunk)
    if actual.hexdigest() != digest.removeprefix("sha256:"):
        raise ContractError(f"{context} blob digest is invalid")
    return digest, member_name


def _is_sha256_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    payload = value.removeprefix("sha256:")
    return len(payload) == 64 and all(character in "0123456789abcdef" for character in payload)


def _is_hex64(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


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
