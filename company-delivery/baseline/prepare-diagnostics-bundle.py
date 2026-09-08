#!/usr/bin/env python3
"""Development-side exact-commit diagnostics review bundle builder/verifier (#278)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = "codex/runtime/aisoft_company_baseline_diagnostics_v1.py"
BUILDER = "company-delivery/baseline/prepare-diagnostics-bundle.py"
SOURCE_FILES = {
    "aisoft_company_baseline_diagnostics_v1.py": COLLECTOR,
    "diagnostics-v1.schema.json": "company-delivery/baseline/diagnostics-v1.schema.json",
    "profile-v1.schema.json": "company-delivery/baseline/profile-v1.schema.json",
    "DIAGNOSTICS.md": "company-delivery/baseline/DIAGNOSTICS.md",
}
EXPECTED_REMOTE = "http://gitea-ci.orb.local:3000/admin/aisoft-platform.git"
LIMIT = 1048576


class Invalid(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_regular(path, *, mode=None):
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022 or info.st_size > LIMIT:
            raise Invalid("FILE_UNSAFE")
        if mode is not None and stat.S_IMODE(info.st_mode) != mode:
            raise Invalid("MODE_MISMATCH")
        raw = bytearray()
        while len(raw) <= LIMIT:
            chunk = os.read(descriptor, min(4096, LIMIT + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        if len(raw) > LIMIT:
            raise Invalid("FILE_TOO_LARGE")
        return bytes(raw)
    finally:
        if descriptor is not None:
            os.close(descriptor)


def git(repo, *args):
    result = subprocess.run(["/usr/bin/git", "--no-replace-objects", "-C", str(repo), *args],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1",
                                 "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_NO_REPLACE_OBJECTS": "1"}, timeout=10)
    if result.returncode or len(result.stdout) > LIMIT:
        raise Invalid("GIT_UNAVAILABLE")
    return result.stdout


def blob(repo, source, path):
    entry = git(repo, "ls-tree", source, "--", path).decode("ascii").strip()
    match = re.fullmatch(r"100644 blob ([0-9a-f]{40})\t" + re.escape(path), entry)
    if not match:
        raise Invalid("OBJECT_INVALID")
    raw = git(repo, "cat-file", "blob", match[1])
    if hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest() != match[1]:
        raise Invalid("OBJECT_HASH_MISMATCH")
    return raw


def materialize(repo, source, profile_path, expected_profile):
    if not re.fullmatch(r"[0-9a-f]{40}", source) or not re.fullmatch(r"[0-9a-f]{64}", expected_profile):
        raise Invalid("PIN_INVALID")
    if git(repo, "remote", "get-url", "origin").decode("utf-8").strip() != EXPECTED_REMOTE:
        raise Invalid("REPOSITORY_MISMATCH")
    if git(repo, "rev-parse", "--verify", source + "^{commit}").decode("ascii").strip() != source:
        raise Invalid("COMMIT_MISMATCH")
    files = {name: blob(repo, source, path) for name, path in SOURCE_FILES.items()}
    # The executing validator/builder must be the same reviewed bytes as the pin.
    if files[Path(COLLECTOR).name] != read_regular(ROOT / COLLECTOR):
        raise Invalid("COLLECTOR_SOURCE_DRIFT")
    if blob(repo, source, BUILDER) != read_regular(Path(__file__)):
        raise Invalid("BUILDER_SOURCE_DRIFT")
    spec = importlib.util.spec_from_file_location("diagnostic_bundle_validator", ROOT / COLLECTOR)
    module = importlib.util.module_from_spec(spec)
    # Avoid bytecode writes; this is the verified local source, never a Git-provided import.
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old
    selected = module.load_profile(profile_path)
    raw_profile = module.profile_bytes(selected)
    if sha256(raw_profile) != expected_profile:
        raise Invalid("PROFILE_DIGEST_MISMATCH")
    if (module.decode(files["diagnostics-v1.schema.json"]) != module.schema()
            or module.decode(files["profile-v1.schema.json"]) != module.profile_schema()):
        raise Invalid("SCHEMA_SOURCE_DRIFT")
    files[module.PROFILE_FILENAME] = raw_profile
    manifest = {"contract_version": "company-platform-baseline-diagnostics-review-bundle/v1",
                "source_sha": source, "profile_sha256": expected_profile,
                "collector_sha256": sha256(files[Path(COLLECTOR).name]),
                "environment": "company-scm-ci", "host_role": "scm-ci", "mutation_authorized": False,
                "files": {name: {"sha256": sha256(raw), "mode": "0600", "size": len(raw)}
                          for name, raw in files.items()}}
    files["manifest.json"] = canonical(manifest)
    return files


def verify_bundle(output, files):
    info = output.lstat()
    if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700:
        raise Invalid("DIRECTORY_UNSAFE")
    if set(entry.name for entry in output.iterdir()) != set(files):
        raise Invalid("BUNDLE_FILE_SET_MISMATCH")
    for name, raw in files.items():
        if read_regular(output / name, mode=0o600) != raw:
            raise Invalid("BUNDLE_CONTENT_MISMATCH")
    return {"status": "PASS", "files": len(files), "manifest_sha256": sha256(files["manifest.json"]),
            "mutation_authorized": False}


def build(output, files):
    # No overwrite, no cleanup of a partially written candidate: keep it reviewable.
    output.mkdir(mode=0o700)
    output.chmod(0o700)
    for name, raw in files.items():
        descriptor = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(raw)
    return verify_bundle(output, files)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Invalid("ARGUMENT_INVALID")


def main(argv=None):
    try:
        parser = Parser(description=__doc__, allow_abbrev=False)
        parser.add_argument("command", choices=("build", "verify"))
        parser.add_argument("--repo", type=Path, required=True)
        parser.add_argument("--source-sha", required=True)
        parser.add_argument("--profile", type=Path, required=True)
        parser.add_argument("--profile-sha256", required=True)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args(argv)
        if args.command == "build" and os.path.lexists(args.output):
            raise Invalid("OUTPUT_EXISTS")
        files = materialize(args.repo, args.source_sha, args.profile, args.profile_sha256)
        result = build(args.output, files) if args.command == "build" else verify_bundle(args.output, files)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Invalid, OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        # Even validator exceptions are projected, never echo arbitrary input or paths.
        print(json.dumps({"status": "BLOCKED_EXTERNAL", "code": str(exc) if isinstance(exc, Invalid) else "INPUT_INVALID"}))
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
