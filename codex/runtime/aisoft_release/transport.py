"""Registry and offline transports for one immutable release manifest."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import tarfile
from typing import Mapping

from .contract import ImageSpec, ReleaseFiles, load_offline_inventory
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


class RegistryTransport(ReleaseTransport):
    def preflight(self) -> None:
        # Manifest parsing already proves every reference is digest-pinned.
        return

    def prepare(self) -> None:
        try:
            for image in self.files.manifest.images:
                self.docker.pull_image(image.reference)
                _verify_image(self.docker.inspect_image(image.reference), image)
        except (ContractError, DeploymentError) as exc:
            raise TransportError("registry transport could not verify immutable images") from exc


class OfflineBundleTransport(ReleaseTransport):
    def preflight(self) -> None:
        try:
            load_offline_inventory(self.files)
            _validate_archive_structure(self.files.archive_path)
        except ContractError as exc:
            raise TransportError("offline bundle preflight failed before image load") from exc

    def prepare(self) -> None:
        # Repeat the complete preflight immediately before the only mutation.
        self.preflight()
        try:
            self.docker.load_archive(self.files.archive_path)
            for image in self.files.manifest.images:
                _verify_image(self.docker.inspect_image(image.reference), image)
        except (ContractError, DeploymentError) as exc:
            raise TransportError("offline bundle load or image inspection failed") from exc


def select_transport(kind: str, docker: object, files: ReleaseFiles) -> ReleaseTransport:
    if kind == "registry":
        return RegistryTransport(docker, files)
    if kind == "offline-bundle":
        return OfflineBundleTransport(docker, files)
    raise ContractError("target profile transport is not recognized")


def _verify_image(value: Mapping[str, object], image: ImageSpec) -> None:
    if value.get("Id") != image.image_id:
        raise ContractError(f"image ID does not match manifest for service {image.service}")
    if value.get("Os") != "linux" or value.get("Architecture") != "amd64":
        raise ContractError(f"image platform does not match linux/amd64 for {image.service}")
    repo_digests = value.get("RepoDigests")
    if not isinstance(repo_digests, list) or image.reference not in repo_digests:
        raise ContractError(
            f"image RepoDigests does not contain manifest reference for {image.service}"
        )


def _validate_archive_structure(path: Path) -> None:
    try:
        with tarfile.open(path, mode="r:*") as archive:
            names: set[str] = set()
            manifest_member: tarfile.TarInfo | None = None
            index_member: tarfile.TarInfo | None = None
            for member in archive:
                normalized = _safe_archive_name(member.name)
                if normalized in names:
                    raise ContractError("offline image archive contains duplicate paths")
                names.add(normalized)
                if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                    raise ContractError("offline image archive contains unsafe member types")
                if not (member.isfile() or member.isdir()):
                    raise ContractError("offline image archive contains unsupported member types")
                if normalized == "manifest.json":
                    manifest_member = member
                elif normalized == "index.json":
                    index_member = member
            selected = manifest_member or index_member
            if selected is None or not selected.isfile():
                raise ContractError("offline image archive is missing manifest.json/index.json")
            if selected.size > MAX_ARCHIVE_INDEX_BYTES:
                raise ContractError("offline image archive index exceeds bounded size")
            handle = archive.extractfile(selected)
            if handle is None:
                raise ContractError("offline image archive index cannot be read")
            payload = handle.read(MAX_ARCHIVE_INDEX_BYTES + 1)
            if len(payload) > MAX_ARCHIVE_INDEX_BYTES:
                raise ContractError("offline image archive index exceeds bounded size")
            value = json.loads(payload.decode("utf-8"))
            selected_name = _safe_archive_name(selected.name)
            if selected_name == "manifest.json" and not isinstance(value, list):
                raise ContractError("Docker archive manifest.json must be an array")
            if selected_name == "index.json" and not isinstance(value, Mapping):
                raise ContractError("OCI archive index.json must be an object")
    except ContractError:
        raise
    except (OSError, tarfile.TarError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("offline image archive is invalid or unreadable") from exc


def _safe_archive_name(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        raise ContractError("offline image archive contains an unsafe path")
    candidate = PurePosixPath(name)
    if candidate.is_absolute() or any(part in {"", ".."} for part in candidate.parts):
        raise ContractError("offline image archive contains path traversal")
    return str(candidate)
