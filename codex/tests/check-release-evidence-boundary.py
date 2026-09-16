"""Issues #290/#296: pin historical evidence and independently test current source."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


BASELINE = "64f1cda0de9735f8782e64a5b07af2ce8460e4c3"
RUNNER = "codex/runtime/aisoft_release/runner.py"
EVIDENCE = "docs/changes/65/issue-65-compose-5.1.4-97445947fff7.json"
HISTORICAL_TEST = "codex/tests/test-docker-release-v2-lifecycle-e2e-harness.sh"
RUNNER_BEFORE = "2d9e9e9db8ec6f3dead2c490f4135473f12b9de80b905bbfb04257703dab9a0e"
RUNNER_AFTER = "95092fbd6deab1a536d53371444c9b9c708b538cff3bc1ac4ebbd7dae3bff195"
EVIDENCE_SHA256 = "b58bb7b57d53a104f922e66c7dc1342bc1b5b133038f60fa8f2ace8d8dbdeb89"
ANCHOR = b"    roles = allowed.get(action)\n"
ADDITION = (
    b"    if (\n"
    b"        roles is not None\n"
    b'        and profile.host_role == "scm-ci"\n'
    b'        and profile.environment == "test"\n'
    b"    ):\n"
    b'        roles = roles | {"scm-ci"}\n'
)
SCOPES = (
    "codex/runtime/aisoft_release",
    "docker-release",
    "codex/tests/integration/test-docker-release-v2-lifecycle-e2e.sh",
    HISTORICAL_TEST,
    "codex/tests/integration/docker-release-v2-lifecycle-driver.py",
    "codex/tests/fixtures/docker-release-v2-lifecycle",
    "codex/tests/fixtures/docker-image-store-e2e",
    "architecture/reference/newemaint/target-candidate/architecture.lock.json",
    EVIDENCE,
)
TRANSPORT = "codex/runtime/aisoft_release/transport.py"
MATRIX = "docker-release/compatibility/image-stores-v1.json"
# Exact reviewed current bytes; never a path/content exemption. These pins are
# advanced only with the corresponding behavior tests and real-E2E evidence.
CURRENT_SOURCE_PINS: dict[str, str] = {
    'codex/runtime/aisoft_release/runner.py': '0f71e8a9e663d51bb72956d7dfd4b46e633b63027b9f0fedf96ea399f24ff7d4',
    'codex/runtime/aisoft_release/transport.py': '66929752efe7515fff425c95083c6593f7eabf6b3105daf2019169d1c6c0bf95',
}
CONTENT_EXEMPT = {"docker-release/README.md", "docker-release/install.sh"}


class BoundaryError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command_env() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("GIT_", "AISOFT_65_", "PYTHON"))
    }
    env.update(
        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
        GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0",
        PYTHONDONTWRITEBYTECODE="1",
    )
    return env


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=root, env=command_env(),
        capture_output=True, check=False, timeout=120,
    )
    if result.returncode:
        raise BoundaryError(f"Git evidence unavailable: {args[0]}")
    return result.stdout


def baseline_files(root: Path) -> dict[str, tuple[str, bytes]]:
    entries = git(root, "ls-tree", "-rz", BASELINE, "--", *SCOPES)
    files = {}
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise BoundaryError("baseline contains an unsupported file type")
        files[path.decode()] = (mode, git(root, "cat-file", "blob", oid))
    if not files:
        raise BoundaryError("baseline scope is empty")
    return files


def disk_files(root: Path) -> set[str]:
    files: set[str] = set()

    def walk(path: Path) -> None:
        mode = path.lstat().st_mode
        if stat.S_ISREG(mode):
            files.add(path.relative_to(root).as_posix())
        elif stat.S_ISDIR(mode):
            for child in path.iterdir():
                walk(child)
        else:
            raise BoundaryError(f"non-regular path: {path.relative_to(root)}")

    for scope in SCOPES:
        path = root / scope
        for parent in path.parents:
            if parent == root:
                break
            if parent.is_symlink():
                raise BoundaryError(f"symlink ancestor: {scope}")
        walk(path)
    return files


def validate(root: Path) -> dict[str, str]:
    files = baseline_files(root)
    old_runner = files[RUNNER][1]
    if digest(old_runner) != RUNNER_BEFORE or old_runner.count(ANCHOR) != 1:
        raise BoundaryError("baseline runner identity mismatch")
    expected_runner = old_runner.replace(ANCHOR, ANCHOR + ADDITION)
    if digest(expected_runner) != RUNNER_AFTER:
        raise BoundaryError("approved runner revision identity mismatch")
    files[RUNNER] = (files[RUNNER][0], expected_runner)
    if digest(files[EVIDENCE][1]) != EVIDENCE_SHA256:
        raise BoundaryError("historical evidence identity mismatch")

    index = {}
    for entry in git(root, "ls-files", "--stage", "-z", "--", *SCOPES).split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, oid, stage = metadata.decode().split()
        if stage != "0" or path.decode() in index:
            raise BoundaryError("unmerged or duplicate index entry")
        index[path.decode()] = (mode, oid)
    if set(index) != set(files) or disk_files(root) != set(files):
        raise BoundaryError("current file set differs from the fixed baseline")

    if not set(CURRENT_SOURCE_PINS).issubset({RUNNER, TRANSPORT, MATRIX}):
        raise BoundaryError("current amendment exceeds its exact file scope")
    if any(len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
           for value in CURRENT_SOURCE_PINS.values()):
        raise BoundaryError("current source pin is not a SHA256")
    actual = []
    for name, (mode, expected) in sorted(files.items()):
        path = root / name
        disk_mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        if disk_mode != mode or index[name][0] != mode:
            raise BoundaryError(f"file mode drift: {name}")
        content = path.read_bytes()
        if name not in CONTENT_EXEMPT:
            expected_hash = CURRENT_SOURCE_PINS.get(name, digest(expected))
            if (digest(content) != expected_hash or
                    digest(git(root, "cat-file", "blob", index[name][1])) != expected_hash):
                raise BoundaryError(f"unapproved source bytes: {name}")
        actual.append([name, mode, digest(content)])
    return {
        "baseline": BASELINE,
        "head_sha": git(root, "rev-parse", "HEAD").decode().strip(),
        "head_tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip(),
        "current_source_sha256": digest(json.dumps(actual, separators=(",", ":")).encode()),
        "runner_sha256": CURRENT_SOURCE_PINS.get(RUNNER, RUNNER_AFTER),
        "historical_role_amendment_sha256": RUNNER_AFTER,
        "historical_evidence_sha256": EVIDENCE_SHA256,
    }


def run_checked(root: Path, argv: list[str], records: list[dict[str, object]]) -> None:
    result = subprocess.run(argv, cwd=root, env=command_env(), check=False, timeout=300)
    records.append({"argv": argv, "exit_code": result.returncode})
    if result.returncode:
        raise BoundaryError(f"regression failed: {Path(argv[0]).name}")


def historical_regression(root: Path, records: list[dict[str, object]]) -> None:
    with tempfile.TemporaryDirectory(prefix="aisoft-290-history-") as temporary:
        snapshot = Path(temporary) / "snapshot"
        # Local object transfer only; no configured remote, fetch, shared index or worktree.
        git(root, "-c", "init.templateDir=", "clone", "--quiet", "--no-local",
            "--no-checkout", "--", str(root), str(snapshot))
        git(snapshot, "checkout", "--quiet", "--detach", BASELINE)
        run_checked(snapshot, ["bash", HISTORICAL_TEST], records)


def current_regression(root: Path, records: list[dict[str, object]]) -> None:
    # -t gives tests their package identity without adding tests/ to sys.path.
    run_checked(root, [sys.executable, "-B", "-m", "unittest", "discover",
                      "-s", "codex/runtime/tests", "-t", "codex/runtime",
                      "-p", "test_release*.py"], records)


def check(root: Path) -> dict[str, object]:
    identity = validate(root)
    records: list[dict[str, object]] = []
    for regression in (historical_regression, current_regression):
        regression(root, records)
        if validate(root) != identity:
            raise BoundaryError("source identity drifted during regression")
    return {
        **identity, "commands": records,
        "current_source_conformance": "PASS", "current_release_regression": "PASS",
        "historical_evidence_binding": "PASS", "historical_harness_fake_regression": "PASS",
        "current_real_e2e": "NOT_RUN", "installed": "NOT_RUN", "company_live": "NOT_RUN",
    }


def main() -> int:
    if len(sys.argv) != 1:
        print("FAIL: this fixed evidence check accepts no overrides", file=sys.stderr)
        return 1
    try:
        print(json.dumps(check(Path(__file__).resolve().parents[2]), sort_keys=True))
        return 0
    except (BoundaryError, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"FAIL: release evidence boundary: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
