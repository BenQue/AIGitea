"""Deterministic operator + exact docker-release/v2 handoff bundle builder."""

from __future__ import annotations

from datetime import date, datetime, timezone
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tarfile
from typing import Mapping

from aisoft_release.contract import load_release_artifact
from aisoft_release.errors import ReleaseError
from aisoft_release.runner import ReleaseRuntime

from .contract import (
    GIT_SHA,
    HANDOFF_VERSION,
    CompanyDeliveryError,
    contains_sensitive_text,
    load_handoff,
    sha256_file,
)


SOURCE_REPOSITORY = "admin/aisoft-platform"
COMPATIBILITY_PATH = "operator/compatibility/newemaint-company-pilot-v1.json"
SOURCE_TRANSPORTS = {"approved-bundle", "allowlisted-github-ref"}

SOURCE_MAPPINGS = (
    ("company-delivery", "operator"),
    ("codex/runtime/aisoft_company_delivery", "operator/runtime/aisoft_company_delivery"),
    ("codex/runtime/aisoft_release", "operator/runtime/aisoft_release"),
    ("sync", "operator/dependencies/sync"),
    ("docker-release", "operator/dependencies/docker-release"),
    ("codex/config/host-capabilities.json", "operator/dependencies/host-role/host-capabilities.json"),
    ("codex/config/host-role.schema.json", "operator/dependencies/host-role/host-role.schema.json"),
    ("codex/tools/verify-host-role.sh", "operator/dependencies/host-role/verify-host-role.sh"),
)


def build_bundle(
    *,
    repository_root: Path | str,
    source_sha: str,
    release_root: Path | str,
    release_id: str,
    output_directory: Path | str,
    created_at: str,
    source_transport: str,
) -> dict[str, object]:
    repository = Path(repository_root)
    release_parent = Path(release_root)
    output = Path(output_directory)
    if GIT_SHA.fullmatch(source_sha) is None:
        raise CompanyDeliveryError("INVALID_ARGUMENT", "source SHA must be a lowercase 40-character Git SHA")
    if GIT_SHA.fullmatch(release_id) is None:
        raise CompanyDeliveryError("INVALID_ARGUMENT", "release ID must be a lowercase 40-character Git SHA")
    if source_transport not in SOURCE_TRANSPORTS:
        raise CompanyDeliveryError("INVALID_ARGUMENT", "source transport is outside the allowlist")
    timestamp = _parse_timestamp(created_at)
    _validate_repository(repository, source_sha)
    _validate_output_directory(output)
    tracked = _mapped_tracked_files(repository)
    release_files = _verified_release(release_parent, release_id, timestamp.date())
    _scan_release_metadata(release_files.directory, release_files.archive_path)
    version = _operator_version(repository / "company-delivery/VERSION")
    bundle_name = f"aisoft-company-delivery-{version}-{source_sha}"
    bundle_root = output / bundle_name
    archive_name = bundle_name + ".tar.gz"
    archive_path = output / archive_name
    sidecar_path = output / (archive_name + ".sha256")
    for target in (bundle_root, archive_path, sidecar_path):
        if os.path.lexists(target):
            raise CompanyDeliveryError("UNSAFE_PATH", "bundle output target already exists")

    try:
        bundle_root.mkdir(mode=0o700)
        _copy_tracked(bundle_root, tracked)
        release_destination = bundle_root / "release" / release_id
        _mkdirs(release_destination)
        for source in sorted(release_files.directory.iterdir(), key=lambda item: item.name):
            _copy_regular(source, release_destination / source.name)

        payloads = _payload_inventory(bundle_root)
        manifest_relative = f"release/{release_id}/release.json"
        manifest_digest = sha256_file(bundle_root / manifest_relative)
        compatibility_digest = sha256_file(bundle_root / COMPATIBILITY_PATH)
        manifest: dict[str, object] = {
            "contract_version": HANDOFF_VERSION,
            "operator_version": version,
            "created_at": created_at,
            "source": {
                "repository": SOURCE_REPOSITORY,
                "git_sha": source_sha,
                "transport": source_transport,
            },
            "release": {
                "contract_version": "docker-release/v2",
                "release_id": release_id,
                "manifest_path": manifest_relative,
                "manifest_sha256": manifest_digest,
                "platform": "linux/amd64",
                "transport": "offline-bundle",
            },
            "compatibility": {
                "matrix_path": COMPATIBILITY_PATH,
                "matrix_sha256": compatibility_digest,
                "required_roles": ["scm-ci", "appserver-prod"],
            },
            "payloads": payloads,
        }
        manifest_path = bundle_root / "handoff-manifest.json"
        _write_new_file(manifest_path, _canonical_json(manifest), 0o600)
        checksum_entries = [(item["path"], item["sha256"]) for item in payloads]
        checksum_entries.append(("handoff-manifest.json", sha256_file(manifest_path)))
        checksum_text = "".join(
            f"{digest}  {relative}\n" for relative, digest in sorted(checksum_entries)
        )
        _write_new_file(bundle_root / "SHA256SUMS", checksum_text.encode("ascii"), 0o600)
        verify_bundle(manifest_path, bundle_root)
        _write_deterministic_archive(bundle_root, archive_path, int(timestamp.timestamp()))
        archive_path.chmod(0o600)
        archive_digest = sha256_file(archive_path)
        _write_new_file(
            sidecar_path,
            f"{archive_digest}  {archive_name}\n".encode("ascii"),
            0o600,
        )
        return {
            "archive_name": archive_name,
            "archive_path": archive_path,
            "archive_sha256": archive_digest,
            "bundle_name": bundle_name,
            "bundle_root": bundle_root,
            "contract_version": HANDOFF_VERSION,
            "release_id": release_id,
            "source_sha": source_sha,
        }
    except Exception:
        if bundle_root.exists():
            shutil.rmtree(bundle_root)
        for target in (archive_path, sidecar_path):
            try:
                target.unlink()
            except OSError:
                pass
        raise


def verify_bundle(manifest_path: Path | str, bundle_root: Path | str) -> dict[str, object]:
    root = Path(bundle_root)
    manifest = load_handoff(manifest_path, bundle_root=root)
    release = manifest["release"]
    assert isinstance(release, Mapping)
    release_id = str(release["release_id"])
    created = _parse_timestamp(str(manifest["created_at"]))
    _verified_release(root / "release", release_id, created.date())
    return {
        "contract_version": HANDOFF_VERSION,
        "docker_calls": 0,
        "ok": True,
        "release_id": release_id,
        "target_facts": "NOT_READ",
    }


def _verified_release(release_root: Path, release_id: str, today: date):
    if not release_root.is_absolute():
        raise CompanyDeliveryError("UNSAFE_PATH", "release root must be absolute")
    try:
        result = ReleaseRuntime(hostname="artifact-only", today=today).verify_artifact(
            release_root, release_id
        )
        files = load_release_artifact(release_root, release_id, today=today)
    except ReleaseError as exc:
        raise CompanyDeliveryError(
            "ARTIFACT_INVALID", "docker-release/v2 artifact-only verification failed"
        ) from exc
    if result.get("ok") is not True or result.get("docker_calls") != 0 or result.get("target_facts") != "NOT_READ":
        raise CompanyDeliveryError("ARTIFACT_INVALID", "artifact-only verification crossed its safety boundary")
    return files


def _validate_repository(repository: Path, expected_sha: str) -> None:
    if not repository.is_absolute():
        raise CompanyDeliveryError("UNSAFE_PATH", "repository root must be absolute")
    try:
        metadata = repository.lstat()
    except OSError as exc:
        raise CompanyDeliveryError("UNSAFE_PATH", "repository root is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CompanyDeliveryError("UNSAFE_PATH", "repository root must be a non-symlink directory")
    top = _git(repository, ["rev-parse", "--show-toplevel"]).strip()
    try:
        if Path(top).resolve() != repository.resolve():
            raise CompanyDeliveryError("SOURCE_INVALID", "repository root does not match Git top level")
    except OSError as exc:
        raise CompanyDeliveryError("SOURCE_INVALID", "repository root cannot be resolved") from exc
    head = _git(repository, ["rev-parse", "HEAD"]).strip()
    if head != expected_sha:
        raise CompanyDeliveryError("SOURCE_INVALID", "repository HEAD does not match source SHA")
    if _git(repository, ["status", "--porcelain", "--untracked-files=all"]):
        raise CompanyDeliveryError("SOURCE_DIRTY", "repository must be clean before bundle build")


def _validate_output_directory(output: Path) -> None:
    if not output.is_absolute():
        raise CompanyDeliveryError("UNSAFE_PATH", "output directory must be absolute")
    try:
        metadata = output.lstat()
    except OSError as exc:
        raise CompanyDeliveryError("UNSAFE_PATH", "output directory is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise CompanyDeliveryError("UNSAFE_PATH", "output directory must be a non-symlink directory")
    if stat.S_IMODE(metadata.st_mode) != 0o700:
        raise CompanyDeliveryError("UNSAFE_MODE", "output directory mode must be 0700")
    try:
        if any(output.iterdir()):
            raise CompanyDeliveryError("UNSAFE_PATH", "output directory must be empty")
    except OSError as exc:
        raise CompanyDeliveryError("UNSAFE_PATH", "output directory cannot be enumerated") from exc


def _mapped_tracked_files(repository: Path) -> list[tuple[Path, Path]]:
    mapped: list[tuple[Path, Path]] = []
    destinations: set[Path] = set()
    for source_name, destination_name in SOURCE_MAPPINGS:
        source_relative = Path(source_name)
        source_path = repository / source_relative
        output = _git_bytes(repository, ["ls-files", "-z", "--", source_name])
        tracked_names = [name for name in _decode_git(output).split("\0") if name]
        if not tracked_names:
            raise CompanyDeliveryError("SOURCE_INVALID", "required operator source is not tracked")
        source_is_directory = source_path.is_dir()
        for tracked_name in tracked_names:
            tracked = Path(tracked_name)
            if source_is_directory:
                try:
                    suffix = tracked.relative_to(source_relative)
                except ValueError as exc:
                    raise CompanyDeliveryError("SOURCE_INVALID", "tracked source escapes mapping") from exc
                destination = Path(destination_name) / suffix
            else:
                if tracked != source_relative:
                    raise CompanyDeliveryError("SOURCE_INVALID", "tracked source mapping is ambiguous")
                destination = Path(destination_name)
            if destination in destinations:
                raise CompanyDeliveryError("SOURCE_INVALID", "operator source mappings overlap")
            destinations.add(destination)
            mapped.append((repository / tracked, destination))
    return sorted(mapped, key=lambda item: item[1].as_posix())


def _copy_tracked(bundle_root: Path, tracked: list[tuple[Path, Path]]) -> None:
    for source, relative in tracked:
        _copy_regular(source, bundle_root / relative)


def _copy_regular(source: Path, destination: Path) -> None:
    try:
        metadata = source.lstat()
    except OSError as exc:
        raise CompanyDeliveryError("SOURCE_INVALID", "bundle source file is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise CompanyDeliveryError("UNSAFE_PATH", "bundle source must be a regular non-symlink file")
    mode = stat.S_IMODE(metadata.st_mode)
    if mode not in {0o600, 0o644, 0o755}:
        raise CompanyDeliveryError("UNSAFE_MODE", "bundle source file mode is outside the allowlist")
    _mkdirs(destination.parent)
    if os.path.lexists(destination):
        raise CompanyDeliveryError("UNSAFE_PATH", "bundle destination path is duplicated")
    _copy_new_file(source, destination, mode)


def _mkdirs(path: Path) -> None:
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)


def _payload_inventory(root: Path) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for prefix in (root / "operator", root / "release"):
        for path in sorted(prefix.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
            metadata = path.lstat()
            if stat.S_ISDIR(metadata.st_mode):
                if stat.S_IMODE(metadata.st_mode) != 0o700:
                    raise CompanyDeliveryError("UNSAFE_MODE", "bundle directory mode must be 0700")
                continue
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                raise CompanyDeliveryError("UNSAFE_PATH", "bundle payload must be a regular non-symlink file")
            mode = f"{stat.S_IMODE(metadata.st_mode):04o}"
            if mode not in {"0600", "0644", "0755"}:
                raise CompanyDeliveryError("UNSAFE_MODE", "bundle payload mode is outside the allowlist")
            payloads.append(
                {
                    "mode": mode,
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256_file(path),
                    "size_bytes": metadata.st_size,
                }
            )
    return payloads


def _scan_release_metadata(directory: Path, archive_path: Path) -> None:
    for path in sorted(directory.iterdir(), key=lambda item: item.name):
        if path == archive_path:
            continue
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise CompanyDeliveryError("ARTIFACT_INVALID", "release metadata is unavailable") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise CompanyDeliveryError("UNSAFE_PATH", "release metadata must be a regular non-symlink file")
        carry = ""
        try:
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    text = carry + chunk.decode("latin-1")
                    if contains_sensitive_text(text):
                        raise CompanyDeliveryError(
                            "SENSITIVE_CONTENT", "release metadata contains forbidden sensitive content"
                        )
                    carry = text[-256:]
        except CompanyDeliveryError:
            raise
        except OSError as exc:
            raise CompanyDeliveryError("ARTIFACT_INVALID", "release metadata cannot be read") from exc


def _write_deterministic_archive(root: Path, destination: Path, epoch: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    try:
        descriptor = os.open(destination, flags, 0o600)
        with os.fdopen(descriptor, "wb") as raw:
            descriptor = None
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=epoch) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT) as archive:
                    paths = [root] + sorted(
                        root.rglob("*"), key=lambda item: item.relative_to(root.parent).as_posix()
                    )
                    for path in paths:
                        metadata = path.lstat()
                        name = path.relative_to(root.parent).as_posix()
                        info = tarfile.TarInfo(name + ("/" if path.is_dir() else ""))
                        info.mtime = epoch
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        info.mode = stat.S_IMODE(metadata.st_mode)
                        if stat.S_ISDIR(metadata.st_mode):
                            info.type = tarfile.DIRTYPE
                            archive.addfile(info)
                        elif stat.S_ISREG(metadata.st_mode):
                            info.size = metadata.st_size
                            with path.open("rb") as handle:
                                archive.addfile(info, handle)
                        else:
                            raise CompanyDeliveryError(
                                "UNSAFE_PATH", "bundle archive contains a non-regular entry"
                            )
            raw.flush()
            os.fsync(raw.fileno())
    except CompanyDeliveryError:
        raise
    except OSError as exc:
        raise CompanyDeliveryError("OUTPUT_FAILED", "deterministic bundle archive could not be written") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _copy_new_file(source: Path, destination: Path, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    try:
        descriptor = os.open(destination, flags, mode)
        with source.open("rb") as reader, os.fdopen(descriptor, "wb") as writer:
            descriptor = None
            shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
    except OSError as exc:
        try:
            destination.unlink()
        except OSError:
            pass
        raise CompanyDeliveryError("OUTPUT_FAILED", "bundle source could not be copied") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _write_new_file(path: Path, payload: bytes, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags, mode)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        try:
            path.unlink()
        except OSError:
            pass
        raise CompanyDeliveryError("OUTPUT_FAILED", "bundle file could not be written safely") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _operator_version(path: Path) -> str:
    try:
        value = path.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise CompanyDeliveryError("SOURCE_INVALID", "operator VERSION is unavailable") from exc
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value) is None:
        raise CompanyDeliveryError("SOURCE_INVALID", "operator VERSION is invalid")
    return value


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise CompanyDeliveryError("INVALID_ARGUMENT", "created_at must be canonical UTC") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise CompanyDeliveryError("INVALID_ARGUMENT", "created_at must be canonical UTC")
    return parsed


def _git(repository: Path, args: list[str]) -> str:
    return _decode_git(_git_bytes(repository, args))


def _decode_git(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CompanyDeliveryError("SOURCE_INVALID", "Git source inspection returned invalid UTF-8") from exc


def _git_bytes(repository: Path, args: list[str]) -> bytes:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repository,
            shell=False,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise CompanyDeliveryError("SOURCE_INVALID", "Git source inspection failed") from exc
    if result.returncode != 0:
        raise CompanyDeliveryError("SOURCE_INVALID", "Git source inspection failed")
    return result.stdout
