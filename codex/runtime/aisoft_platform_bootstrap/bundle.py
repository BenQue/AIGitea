"""Reproducible archive builder and verification without extracting untrusted tar."""
from __future__ import annotations

import gzip
import io
import os
from pathlib import Path
import re
import stat
import subprocess
import tarfile

from .contract import (BootstrapError, SCHEMAS, VERSION, canonical, digest,
                       document, parse, read_regular, require, safe_path, write_new)


ARCHIVE = "platform-bootstrap.tar.gz"
LIMIT = 16 * 1024 * 1024
PACKAGE_FILES = ["VERSION", "README.md", "runbook.md", "actions.json",
                 "bin/aisoft-platform-bootstrap",
                 "templates/approval.example.json", "templates/inventory.example.json",
                 "templates/target.example.json"] + [f"schema/{kind}-v1.schema.json" for kind in SCHEMAS]
RUNTIME_FILES = ["__init__.py", "contract.py", "bundle.py", "workflow.py", "cli.py"]
MAPPINGS = {f"platform-bootstrap/{name}": name for name in PACKAGE_FILES}
MAPPINGS.update({f"codex/runtime/aisoft_platform_bootstrap/{name}":
                f"runtime/aisoft_platform_bootstrap/{name}" for name in RUNTIME_FILES})
DESTINATIONS = set(MAPPINGS.values())


def git(repository: Path, *args: str) -> bytes:
    environment = {"PATH": os.environ.get("PATH", os.defpath), "LC_ALL": "C",
                   "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
                   "GIT_CONFIG_NOSYSTEM": "1", "GIT_NO_REPLACE_OBJECTS": "1",
                   "GIT_OPTIONAL_LOCKS": "0", "GIT_LITERAL_PATHSPECS": "1"}
    try:
        result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
                                "-c", "status.submoduleSummary=false", "-c", "submodule.recurse=false",
                                "-C", str(repository), *args], capture_output=True,
                                check=False, timeout=30, env=environment)
    except subprocess.TimeoutExpired as exc:
        raise BootstrapError("SOURCE_TIMEOUT") from exc
    require(result.returncode == 0, "SOURCE_INVALID")
    return result.stdout


def scan(data: bytes) -> None:
    # Only audited source files are copied, never arbitrary workspace or Git metadata.
    # This catches accidental concrete credential literals; it is not DLP certification.
    require((b"-----BEGIN " + b"PRIVATE KEY-----") not in data and
            (b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----") not in data, "SENSITIVE_CONTENT")
    require(re.search(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{24,})", data) is None,
            "SENSITIVE_CONTENT")
    require(re.search(rb"(?im)^\s*(?:token|password|secret|api_key)\s*[:=]\s*['\"]?[A-Za-z0-9+/=_-]{8,}",
                      data) is None, "SENSITIVE_CONTENT")


def _archive(files: dict[str, bytes], modes: dict[str, int]) -> bytes:
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", filename="", mtime=0, compresslevel=9) as zipped:
        with tarfile.open(fileobj=zipped, mode="w", format=tarfile.USTAR_FORMAT) as tar:
            for name in sorted(files):
                entry = tarfile.TarInfo(name)
                entry.size, entry.mode = len(files[name]), modes.get(name, 0o644)
                entry.mtime, entry.uid, entry.gid = 0, 0, 0
                entry.uname = entry.gname = ""
                tar.addfile(entry, io.BytesIO(files[name]))
    return out.getvalue()


def build(repository: Path, approval_path: Path, output: Path) -> dict:
    safe_path(repository)
    safe_path(output)
    approval_data = read_regular(approval_path)
    approval = parse(approval_data, "approval")
    require(repository.is_dir(), "SOURCE_INVALID")
    require(git(repository, "rev-parse", "--show-toplevel").decode().strip() == str(repository),
            "SOURCE_INVALID")
    require(git(repository, "rev-parse", "HEAD").decode().strip() == approval["source_sha"],
            "IDENTITY_MISMATCH")
    require(not git(repository, "status", "--porcelain", "--untracked-files=all"), "SOURCE_DIRTY")
    require(output.is_dir() and not list(output.iterdir()) and
            output.stat().st_mode & 0o777 == 0o700 and repository not in output.parents,
            "OUTPUT_INVALID")
    source_sha = approval["source_sha"]
    tracked = set(git(repository, "ls-tree", "-r", "--name-only", "-z", source_sha, "--",
                      "platform-bootstrap", "codex/runtime/aisoft_platform_bootstrap")
                  .decode().strip("\0").split("\0"))
    require(tracked == set(MAPPINGS), "COMPONENT_ALLOWLIST_MISMATCH")
    files, modes, entries = {}, {}, []
    for source, target in sorted(MAPPINGS.items(), key=lambda pair: pair[1]):
        metadata = safe_path(repository / source).lstat()
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1, "UNSAFE_PATH")
        mode = 0o755 if target.startswith("bin/") else 0o644
        tree_entry = git(repository, "ls-tree", source_sha, "--", source).decode().split()
        require(tree_entry and tree_entry[0] == ("100755" if mode == 0o755 else "100644"),
                "SOURCE_MODE_INVALID")
        require(int(git(repository, "cat-file", "-s", tree_entry[2])) <= 4 * 1024 * 1024,
                "RESOURCE_LIMIT")
        # The pinned immutable blob is authoritative, never a moving HEAD or working file.
        content = git(repository, "cat-file", "blob", tree_entry[2])
        require(content and len(content) <= 4 * 1024 * 1024, "SOURCE_INVALID")
        scan(content)
        files[target], modes[target] = content, mode
        entries.append({"path": target, "sha256": digest(content), "size": len(content), "mode": mode})
    require(files["VERSION"] == (VERSION + "\n").encode(), "VERSION_MISMATCH")
    parse(files["actions.json"], "actions")
    manifest = document({"contract_version": "platform-bootstrap/v1", "bundle_version": VERSION,
        "source_repository": "admin/aisoft-platform", "source_sha": approval["source_sha"],
        "host_role": approval["host_role"], "components": approval["components"],
        "approval_reference": approval["reference"], "approval_sha256": digest(approval_data),
        "rollback": approval["rollback"], "payload_sha256": digest(canonical(entries)),
        "payloads": entries}, "manifest")
    files["bundle-manifest.json"] = canonical(manifest)
    archive = _archive(files, modes)
    require(len(archive) <= LIMIT, "RESOURCE_LIMIT")
    handoff = document({"contract_version": "platform-bootstrap-handoff/v1",
        "source_sha": approval["source_sha"], "manifest_sha256": digest(files["bundle-manifest.json"]),
        "archive_name": ARCHIVE, "archive_sha256": digest(archive)}, "handoff")
    # Validate complete bytes before any output is published.
    _verify_archive(archive, handoff)
    require(git(repository, "rev-parse", "HEAD").decode().strip() == source_sha and
            not git(repository, "status", "--porcelain", "--untracked-files=all"), "SOURCE_DIRTY")
    created = []
    try:
        for name, data in [(ARCHIVE, archive), ("handoff.json", canonical(handoff))]:
            write_new(output / name, data)
            created.append(output / name)
        write_new(output / "handoff.sha256", (digest(canonical(handoff)) + "  handoff.json\n").encode())
    except OSError:
        for path in created:
            path.unlink()
        raise
    return {"status": "PASS", "evidence_layer": "local", "source_sha": approval["source_sha"],
            "archive_sha256": handoff["archive_sha256"], "handoff_sha256": digest(canonical(handoff)),
            "target_facts": "NOT_READ"}


def _verify_archive(archive: bytes, handoff: dict) -> dict:
    require(digest(archive) == handoff["archive_sha256"], "CHECKSUM_MISMATCH")
    # Bound decompression before tarfile can allocate buffers from attacker sizes.
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(archive), mode="rb") as zipped:
            tar_data = zipped.read(LIMIT + 1)
        require(len(tar_data) <= LIMIT, "RESOURCE_LIMIT")
        files, modes = {}, {}
        with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:") as tar:
            for entry in tar:
                require(entry.name in DESTINATIONS | {"bundle-manifest.json"} and
                        entry.name not in files and entry.isfile() and not entry.pax_headers,
                        "ARCHIVE_INVALID")
                require(0 < entry.size <= 4 * 1024 * 1024 and entry.uid == entry.gid == entry.mtime == 0
                        and entry.uname == entry.gname == "", "ARCHIVE_INVALID")
                stream = tar.extractfile(entry)
                require(stream is not None, "ARCHIVE_INVALID")
                content = stream.read(4 * 1024 * 1024 + 1)
                require(len(content) == entry.size, "ARCHIVE_INVALID")
                files[entry.name], modes[entry.name] = content, entry.mode
    except (OSError, EOFError, tarfile.TarError, ValueError) as exc:
        if isinstance(exc, BootstrapError):
            raise
        raise BootstrapError("ARCHIVE_INVALID") from exc
    require(set(files) == DESTINATIONS | {"bundle-manifest.json"}, "COMPONENT_ALLOWLIST_MISMATCH")
    require(digest(files["bundle-manifest.json"]) == handoff["manifest_sha256"], "CHECKSUM_MISMATCH")
    manifest = parse(files["bundle-manifest.json"], "manifest")
    require(manifest["source_sha"] == handoff["source_sha"], "IDENTITY_MISMATCH")
    require(files["VERSION"] == (VERSION + "\n").encode(), "VERSION_MISMATCH")
    parse(files["actions.json"], "actions")
    expected = []
    for name in sorted(DESTINATIONS):
        scan(files[name])
        require(modes[name] == (0o755 if name.startswith("bin/") else 0o644), "ARCHIVE_INVALID")
        expected.append({"path": name, "sha256": digest(files[name]), "size": len(files[name]),
                         "mode": modes[name]})
    require(modes["bundle-manifest.json"] == 0o644 and manifest["payloads"] == expected and
            manifest["payload_sha256"] == digest(canonical(expected)), "CHECKSUM_MISMATCH")
    return manifest


def verify(handoff_path: Path, archive_path: Path, expected_handoff_sha256: str) -> dict:
    require(re.fullmatch(r"[0-9a-f]{64}", expected_handoff_sha256) is not None, "IDENTITY_MISMATCH")
    handoff_data = read_regular(handoff_path)
    require(digest(handoff_data) == expected_handoff_sha256, "CHECKSUM_MISMATCH")
    handoff = parse(handoff_data, "handoff")
    require(archive_path.name == ARCHIVE, "IDENTITY_MISMATCH")
    return _verify_archive(read_regular(archive_path, LIMIT), handoff)
