"""Credential-free, zero-write comparison of the eight installer surfaces (#308).

Installer fingerprints fail closed when copy/delete semantics change. Update their
mapping and acceptance fixtures together; never just advance a fingerprint to get
green. Counts are diagnostic quantities, never a substitute for expected-file bytes.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass, field
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

INSTALLER_PINS = {
    "codex/install-vm.sh": "e208d941e9ac72fa89380523325070adfe0d657c83e99f9c806554c25a4e6b42",
    "codex/install-skills.sh": "d07e38ba51e4f02f57820478626c9fc4d371b10265a0053df230028daafca9c3",
    "codex/install-host-role.sh": "325e5150722e30debc115c0717d9bc4dedac44e1a7552c3a2258df14c4b27c89",
    "codex/install-host-access-broker.sh": "72df0ff5540ab1bc2a6c9a10924fdd87d8854f7fc99eb35fbaa2db62039502f2",
    "architecture/install.sh": "c8f14f0154cad1b7402e527209d0135bab2bdf3bc0024f72fd06994067aa972e",
    "docker-release/install.sh": "3580c1e23b343fe9bbe2d3f9ea1b64b0f95ef1a7ba9c023c282bf5b68a649b13",
    "sync/install.sh": "153f36ef3396a053a4e4cbb8d6022a9f163b75b6f4c25498ba27ae3217d30f10",
    "skill-for-claude/install.sh": "0c1a6692b983fada75a11de250a269f129371880cf41714611c1d59c1a541681",
}
# The versioned snapshot manifest is immutable. Validate content declarations
# below as well; changing either contract requires explicit mapping maintenance.
MATT_MANIFEST_PIN = "a7e1ccccdc1ccc3d0c9af8ec0e7788cf3ac7bc0c308aaaa011ccc493c5d216da"
HELPER_SOURCE_INPUTS = ("go.mod", "go.sum", "build-lock.json", "build.py", "main.go", "helper.go",
                        "helper_test.go", "process_fixture_test.go")
CONTROL_LINE_RE = re.compile(
    r"^(?:#{1,6}\s+|\d+[.)]\s+)"
    r"|\b(?:commit|push|merge|rebase|reset|force-push|deploy|permission|"
    r"network|curl|https?://|tool|script|shell|command|execute|tracker|"
    r"issue|ticket|label)\b", re.I)


class InspectionError(Exception):
    def __init__(self, reason: str, path: Path):
        self.reason, self.path = reason, path
        super().__init__(f"{reason}: {path}")


@contextmanager
def parent_descriptor(path: Path, boundary: Path):
    """Anchor each parent lookup to a directory fd; never follow parent links."""
    if not path.is_relative_to(boundary):
        raise InspectionError("outside-declared-root", path)
    fd = None
    try:
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open(boundary, flags)
        for part in path.relative_to(boundary).parts[:-1]:
            next_fd = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd
    except FileNotFoundError:
        raise InspectionError("missing", path) from None
    except OSError:
        raise InspectionError("unreadable-or-linked-parent", path) from None
    finally:
        if fd is not None:
            os.close(fd)


def checked_stat(path: Path, boundary: Path, *, link=False):
    """Do not follow undeclared parent links or read special files/Secret targets."""
    if not path.is_relative_to(boundary):
        raise InspectionError("outside-declared-root", path)
    try:
        root_stat = boundary.lstat()
    except OSError:
        raise InspectionError("unreadable", path) from None
    if not stat.S_ISDIR(root_stat.st_mode):
        raise InspectionError("symlink-root" if stat.S_ISLNK(root_stat.st_mode) else "not-directory-root", path)
    current = boundary
    for part in path.relative_to(boundary).parts[:-1]:
        current /= part
        try:
            st = current.lstat()
        except FileNotFoundError:
            raise InspectionError("missing", path) from None
        except OSError:
            raise InspectionError("unreadable", path) from None
        if stat.S_ISLNK(st.st_mode):
            raise InspectionError("symlink-parent", path)
        if not stat.S_ISDIR(st.st_mode):
            raise InspectionError("not-directory-parent", path)
    try:
        with parent_descriptor(path, boundary) as fd:
            st = os.stat(path.name, dir_fd=fd, follow_symlinks=False) if path != boundary else os.fstat(fd)
    except FileNotFoundError:
        raise InspectionError("missing", path) from None
    except OSError:
        raise InspectionError("unreadable", path) from None
    if stat.S_ISLNK(st.st_mode) and not link:
        raise InspectionError("symlink", path)
    return st


def read_bytes(path: Path, boundary: Path, *, limit=None) -> bytes:
    st = checked_stat(path, boundary)
    if not stat.S_ISREG(st.st_mode):
        raise InspectionError("not-regular", path)
    if not st.st_mode & 0o444:
        raise InspectionError("unreadable", path)
    try:
        # O_NONBLOCK prevents a concurrent replacement by a FIFO from blocking.
        with parent_descriptor(path, boundary) as parent_fd:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent_fd)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise InspectionError("not-regular", path)
            data = stream.read() if limit is None else stream.read(limit + 1)
            if limit is not None and len(data) > limit:
                raise InspectionError("document-too-large", path)
            return data
    except OSError:
        raise InspectionError("unreadable", path) from None


def read_json(path: Path, boundary: Path):
    try:
        return json.loads(read_bytes(path, boundary))
    except (ValueError, UnicodeError):
        # Never emit JSON contents or an exception containing Secret-like bytes.
        raise InspectionError("invalid-json", path) from None


def strict_document(path: Path, boundary: Path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def invalid_constant(_value):
        raise ValueError("non-JSON constant")

    try:
        return json.loads(read_bytes(path, boundary, limit=1048576),
                          object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise InspectionError("invalid-json", path) from None


def require(condition, reason: str, path: Path):
    if not condition:
        raise InspectionError(reason, path)


def file_digest(path: Path, boundary: Path):
    return hashlib.sha256(read_bytes(path, boundary)).hexdigest()


def sha256_value(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass
class RotationSurface:
    metadata: Path
    binary: Path
    boundary: Path
    files: dict[str, Path]

    def validate_provenance(self, repo: Path, identity, public: Path, descriptor):
        proof = strict_document(public, Path(public.anchor))
        fields = {"schema", "toolchain", "toolchain_input", "platform", "gitea", "sha256",
                  "go_mod_sha256", "go_sum_sha256", "build_info", "source_commit", "source_dirty", "source_sha256"}
        require(isinstance(proof, dict) and set(proof) == fields, "helper-provenance-schema", public)
        helper = repo / "codex/tools/gitea-pat-helper"
        lock = read_json(helper / "build-lock.json", repo)
        require(proof["schema"] == "aisoft-gitea-pat-helper-build/v1"
                and proof["source_commit"] == identity["head"] and proof["source_dirty"] is False
                and proof["toolchain"] == lock["version"] == "go1.26.3"
                and proof["platform"] == descriptor["platform"]
                and proof["gitea"] == lock["gitea"]
                and lock["gitea"]["module"] == "code.gitea.io/gitea"
                and lock["gitea"]["version"] == "v1.26.4"
                and proof["sha256"] == descriptor["sha256"] and isinstance(proof["build_info"], str),
                "helper-provenance-binding", public)
        require(proof["go_mod_sha256"] == file_digest(helper / "go.mod", repo)
                and proof["go_sum_sha256"] == file_digest(helper / "go.sum", repo)
                and proof["source_sha256"] == {p.name: file_digest(p, repo)
                     for p in directory_entries(helper, repo) if p.suffix == ".go"},
                "helper-source-differ", public)
        pins = [item for item in lock["files"] if item["os"] + "/" + item["arch"] == descriptor["platform"]]
        inputs = proof["toolchain_input"]
        require(isinstance(inputs, dict) and set(inputs) == {"filename", "sha256", "extracted_tree_sha256"}
                and len(pins) == 1 and inputs["filename"] == pins[0]["filename"]
                and inputs["sha256"] == pins[0]["sha256"] and sha256_value(inputs["extracted_tree_sha256"]),
                "helper-toolchain-input-differ", public)
        require(file_digest(self.binary, self.boundary) == proof["sha256"], "helper-bytes-differ", self.binary)
        return proof["sha256"]

    def inspect(self, repo: Path, identity, public: Path | None):
        report = {"local_helper": "NOT_VERIFIED", "capability": "NOT_ASSESSED"}
        try:
            record = strict_document(self.metadata, self.boundary)
            require(isinstance(record, dict) and set(record) == {"version", "source_sha", "merged_main", "files", "helper"}
                    and type(record["version"]) is int and record["version"] == 1
                    and type(record["merged_main"]) is bool, "rotation-metadata-schema", self.metadata)
            require(record["source_sha"] == identity["head"] and identity["head"] is not None
                    and record["merged_main"] is True and identity["head_is_cached_main_ancestor"]
                    and identity["managed_source_matches_cached_main"], "rotation-source-binding", self.metadata)
            require(isinstance(record["files"], dict) and set(record["files"]) == set(self.files),
                    "rotation-files-schema", self.metadata)
            for logical, source in self.files.items():
                require(record["files"][logical] == file_digest(source, repo)
                        == file_digest(self.boundary / logical.lstrip("/"), self.boundary),
                        "rotation-file-digest-differ", self.metadata)
            descriptor = record["helper"]
            if descriptor is None:
                report["local_helper"] = "LOCAL_HELPER_NOT_DECLARED"
                require(public is None, "helper-not-selected", self.metadata)
                # The installer preserves a previously copied binary when omitted.
                # Its existence/bytes and remote VM capability are not assessed.
            else:
                require(isinstance(descriptor, dict)
                        and set(descriptor) == {"sha256", "platform", "model", "toolchain"}
                        and sha256_value(descriptor["sha256"])
                        and descriptor["platform"] in {"linux/arm64", "linux/amd64"}
                        and descriptor["model"] == "1.26.4" and descriptor["toolchain"] == "go1.26.3",
                        "rotation-helper-schema", self.metadata)
                require(public is not None, "helper-provenance-required", self.metadata)
                digest = self.validate_provenance(repo, identity, public, descriptor)
                report.update(local_helper="MATCHES_DECLARED_BUILD", sha256=digest,
                              evidence_scope="DECLARED_BUILD_RECEIPT_ONLY")
            return report, []
        except (InspectionError, OSError, ValueError, KeyError, TypeError) as exc:
            return report, [{"reason": exc.reason if isinstance(exc, InspectionError) else "rotation-definition-invalid",
                             "target": str(exc.path) if isinstance(exc, InspectionError) else str(self.metadata)}]


def read_link(path: Path, boundary: Path):
    with parent_descriptor(path, boundary) as fd:
        return os.readlink(path.name, dir_fd=fd)


def directory_entries(path: Path, boundary: Path):
    st = checked_stat(path, boundary)
    if not stat.S_ISDIR(st.st_mode):
        raise InspectionError("not-directory", path)
    if not st.st_mode & 0o444 or not st.st_mode & 0o111:
        raise InspectionError("unreadable", path)
    try:
        with parent_descriptor(path, boundary) as parent_fd:
            fd = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd) if path != boundary else os.dup(parent_fd)
            try:
                return sorted(path / name for name in os.listdir(fd))
            finally:
                os.close(fd)
    except OSError:
        raise InspectionError("unreadable", path) from None


def tree_files(path: Path, boundary: Path):
    files = []
    for p in directory_entries(path, boundary):
        if p.name == "__pycache__" or p.suffix == ".pyc":
            continue
        st = checked_stat(p, boundary)
        if stat.S_ISDIR(st.st_mode):
            files.extend(tree_files(p, boundary))
        elif stat.S_ISREG(st.st_mode):
            files.append(p)
        else:
            raise InspectionError("not-regular", p)
    return files


@dataclass
class Metric:
    expected: object
    kind: str
    targets: list[Path]
    boundary: Path
    key: str = ""
    pattern: str = "*"

    def installed(self):
        if self.kind in {"json-value", "json-length"}:
            doc = read_json(self.targets[0], self.boundary)
            if not isinstance(doc, dict) or self.key not in doc:
                raise InspectionError("missing-json-field", self.targets[0])
            value = doc[self.key]
            if self.kind == "json-length":
                if not isinstance(value, (list, dict)):
                    raise InspectionError("invalid-json-field-type", self.targets[0])
                return len(value)
            if not isinstance(value, str):
                raise InspectionError("invalid-json-field-type", self.targets[0])
            return value
        if self.kind == "link":
            st = checked_stat(self.targets[0], self.boundary, link=True)
            if not stat.S_ISLNK(st.st_mode):
                raise InspectionError("not-symlink", self.targets[0])
            return read_link(self.targets[0], self.boundary)
        if self.kind == "files":
            count = 0
            for p in self.targets:
                try:
                    count += stat.S_ISREG(checked_stat(p, self.boundary).st_mode)
                except InspectionError as exc:
                    if exc.reason != "missing":
                        raise
            return count
        count = 0
        for directory in self.targets:
            try:
                entries = directory_entries(directory, self.boundary)
            except InspectionError as exc:
                if exc.reason == "missing":
                    continue
                raise
            for p in entries:
                if fnmatch.fnmatchcase(p.name, self.pattern):
                    count += stat.S_ISREG(checked_stat(p, self.boundary).st_mode)
        return count


@dataclass
class Surface:
    installer: str
    files: list[tuple[Path, Path, Path]] = field(default_factory=list)
    links: list[tuple[Path, str, Path]] = field(default_factory=list)
    exact_trees: list[tuple[Path, Path, bool]] = field(default_factory=list)
    absent: list[tuple[Path, Path]] = field(default_factory=list)
    metrics: dict[str, Metric] = field(default_factory=dict)
    also_checked_by: list[str] = field(default_factory=list)
    user_owned: list[str] = field(default_factory=list)
    rotation: RotationSurface | None = None


def build_surfaces(repo: Path, home: Path, system: Path, agent: Path, arch: Path):
    names = ("install-vm", "install-skills", "install-host-role", "install-host-access-broker",
             "architecture/install", "docker-release/install", "sync/install", "skill-for-claude/install")
    surfaces = {name: Surface(name) for name in names}
    metadata_sources = {repo / p for p in INSTALLER_PINS}

    def add(name, source, target, boundary):
        surfaces[name].files.append((repo / source, target, boundary))

    def tree(name, source, target, boundary, pattern=None, exact=False, directories=False):
        src = repo / source
        paths = (p for p in directory_entries(src, repo) if fnmatch.fnmatchcase(p.name, pattern)) if pattern else tree_files(src, repo)
        for p in paths:
            if stat.S_ISREG(checked_stat(p, repo).st_mode):
                add(name, str(p.relative_to(repo)), target / p.relative_to(src), boundary)
        if exact:
            surfaces[name].exact_trees.append((target, boundary, directories))

    def json_metric(name, label, source, target, boundary, key, length=True):
        doc = read_json(repo / source, repo)
        metadata_sources.add(repo / source)
        if not isinstance(doc, dict) or key not in doc:
            raise InspectionError("missing-json-field", repo / source)
        expected = doc[key]
        if length:
            if not isinstance(expected, (dict, list)):
                raise InspectionError("invalid-json-field-type", repo / source)
            expected = len(expected)
        elif not isinstance(expected, str):
            raise InspectionError("invalid-json-field-type", repo / source)
        surfaces[name].metrics[label] = Metric(expected, "json-length" if length else "json-value", [target], boundary, key)

    vm = home / ".local/lib/aisoft-loop"
    broker = system / "usr/local/lib/aisoft-host-access"
    share = system / "usr/local/share/aisoft"
    libexec = system / "usr/local/libexec/aisoft"
    for pkg in ("aisoft_loop", "aisoft_host_access", "aisoft_gitea_governance"):
        tree("install-vm", "codex/runtime/" + pkg, vm / pkg, home, "*.py")
    for pkg in ("aisoft_host_access", "aisoft_gitea_governance"):
        tree("install-host-access-broker", "codex/runtime/" + pkg, broker / pkg, system, "*.py")
    for filename in ("aisoft_change_name.py", "aisoft_worktree_owner.py"):
        add("install-vm", "codex/runtime/" + filename, vm / filename, home)
        add("install-host-access-broker", "codex/runtime/" + filename, broker / filename, system)
    surfaces["install-vm"].metrics["runtime modules"] = Metric(len(surfaces["install-vm"].files), "patterns",
        [vm / p for p in ("aisoft_loop", "aisoft_host_access", "aisoft_gitea_governance")] + [vm], home, pattern="*.py")
    for filename in ("host-access-broker.json", "gitea-governance.json"):
        add("install-vm", "codex/config/" + filename, home / ".local/share/aisoft" / filename, home)
    for filename in ("host-access-broker.json", "gitea-governance.json", "gitea-labels.json"):
        add("install-host-access-broker", "codex/config/" + filename, share / filename, system)
    for name, target, boundary in [("install-vm", home / ".local/share/aisoft/host-access-broker.json", home),
                                   ("install-host-access-broker", share / "host-access-broker.json", system)]:
        json_metric(name, "operations", "codex/config/host-access-broker.json", target, boundary, "operations")
    for tool in ("host-access-broker", "git-credential-aisoft-host", "project-profile-migration",
                 "bootstrap-gitea-service-account", "rollback-gitea-routine-pilot", "rotate-gitea-service-account"):
        add("install-host-access-broker", "codex/tools/" + tool + ".sh", libexec / tool, system)
    rotation_files = {
        "/usr/local/share/aisoft/host-access-broker.json": repo / "codex/config/host-access-broker.json",
        "/usr/local/share/aisoft/gitea-governance.json": repo / "codex/config/gitea-governance.json",
        "/usr/local/lib/aisoft-host-access/aisoft_host_access/credential_rotation.py": repo / "codex/runtime/aisoft_host_access/credential_rotation.py",
        "/usr/local/libexec/aisoft/rotate-gitea-service-account": repo / "codex/tools/rotate-gitea-service-account.sh",
    }
    surfaces["install-host-access-broker"].rotation = RotationSurface(
        share / "credential-rotation-source.json", libexec / "gitea-pat-helper", system, rotation_files)
    metadata_sources.update(rotation_files.values())
    helper = repo / "codex/tools/gitea-pat-helper"
    metadata_sources.update(helper / name for name in HELPER_SOURCE_INPUTS)
    metadata_sources.update(p for p in directory_entries(helper, repo) if p.suffix == ".go")
    surfaces["install-host-access-broker"].absent = [(libexec / name, system) for name in ("keychain-acl-audit", "keychain-acl-audit.previous")]
    tree("install-vm", "codex/agent", agent, agent, "*.sh")
    tree("install-vm", "codex/systemd", home / ".config/systemd/user", home, "aisoft-agent@.*")
    for filename in ("gitea-readonly.sh", "ensure-gitea-collaborator.sh"):
        add("install-vm", "codex/tools/" + filename, agent / filename, agent)
    surfaces["install-vm"].also_checked_by = ["install-skills"]
    surfaces["install-vm"].user_owned = [str(home / ".codex/config.toml"), str(home / ".codex/AGENTS.md")]
    add("install-host-role", "codex/tools/verify-host-role.sh", libexec / "verify-host-role", system)
    for filename in ("host-role.schema.json", "host-capabilities.json"):
        add("install-host-role", "codex/config/" + filename, share / filename, system)
    add("install-host-role", "templates/hosts/host-profile.example.json", system / "etc/aisoft/host-profile.example.json", system)
    json_metric("install-host-role", "capabilities", "codex/config/host-capabilities.json", share / "host-capabilities.json", system, "capabilities")

    skills = home / ".agents/skills"
    skill_names = []
    for p in directory_entries(repo / "codex/skills", repo):
        if stat.S_ISDIR(checked_stat(p, repo).st_mode):
            skill_names.append(p.name)
            tree("install-skills", str(p.relative_to(repo)), skills / p.name, home, exact=True)
    skill_names.append("aisoft-platform")
    tree("install-skills", "skill-for-codex", skills / "aisoft-platform", home, exact=True)
    surfaces["install-skills"].metrics["skills"] = Metric(len(skill_names), "files", [skills / n / "SKILL.md" for n in skill_names], home)
    # Derive the fixed version from its pinned installer; never execute the script.
    text = read_bytes(repo / "codex/install-skills.sh", repo).decode("utf-8")
    version = re.search(r'^matt_version="(v[0-9.]+)"$', text, re.M).group(1)
    snapshot = "codex/vendor/mattpocock/" + version
    manifest = read_json(repo / snapshot / "manifest.json", repo)
    if hashlib.sha256(read_bytes(repo / snapshot / "manifest.json", repo)).hexdigest() != MATT_MANIFEST_PIN:
        raise InspectionError("matt-manifest-contract-differ", repo / snapshot / "manifest.json")
    if hashlib.sha256(read_bytes(repo / snapshot / "LICENSE", repo)).hexdigest() != manifest.get("license_sha256"):
        raise InspectionError("matt-license-hash-differ", repo / snapshot / "LICENSE")
    metadata_sources.add(repo / snapshot / "manifest.json")
    entries = manifest.get("skills")
    if manifest.get("tag") != version or not isinstance(entries, list) or len(entries) != manifest.get("skill_count"):
        raise InspectionError("invalid-matt-manifest", repo / snapshot / "manifest.json")
    seen = set()
    vendor = home / ".agents/vendor/mattpocock"
    tree("install-skills", snapshot, vendor / "releases" / version, home, exact=True)
    surfaces["install-skills"].links.append((vendor / "current", "releases/" + version, home))
    surfaces["install-skills"].metrics["matt snapshot"] = Metric("releases/" + version, "link", [vendor / "current"], home)
    for item in entries:
        name, path = item.get("name"), item.get("path")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name in seen:
            raise InspectionError("invalid-matt-manifest", repo / snapshot / "manifest.json")
        seen.add(name)
        if not isinstance(path, str) or not path.startswith("skills/") or not path.endswith("/SKILL.md") or ".." in Path(path).parts:
            raise InspectionError("invalid-matt-manifest", repo / snapshot / "manifest.json")
        skill_file = repo / snapshot / path
        content = read_bytes(skill_file, repo).decode("utf-8")
        controls = "\n".join(line.strip() for line in content.splitlines() if CONTROL_LINE_RE.search(line))
        digest = hashlib.sha256()
        for p in sorted(tree_files(skill_file.parent, repo)):
            relative = p.relative_to(skill_file.parent).as_posix().encode("utf-8")
            data = read_bytes(p, repo)
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        if digest.hexdigest() != item.get("sha256") or hashlib.sha256(controls.encode("utf-8")).hexdigest() != item.get("control_sha256"):
            raise InspectionError("matt-skill-hash-differ", skill_file)
        surfaces["install-skills"].links.append((skills / name, "../vendor/mattpocock/current/" + str(Path(path).parent), home))
    if {p.parent.name for p in (repo / snapshot / "skills").glob("**/SKILL.md")} != seen:
        raise InspectionError("matt-skill-set-mismatch", repo / snapshot / "manifest.json")

    tree("architecture/install", "codex/runtime/aisoft_architecture", arch / "lib/aisoft-architecture/aisoft_architecture", arch, "*.py")
    add("architecture/install", "architecture/bin/aisoft-architecture", arch / "bin/aisoft-architecture", arch)
    add("architecture/install", "architecture/catalog.json", arch / "share/aisoft-architecture/catalog.json", arch)
    for dirname in ("profiles", "schemas", "templates", "decisions"):
        tree("architecture/install", "architecture/" + dirname, arch / "share/aisoft-architecture" / dirname, arch, "*")
    for label, key, length in [("catalog revision", "revision", False), ("components", "components", True)]:
        json_metric("architecture/install", label, "architecture/catalog.json", arch / "share/aisoft-architecture/catalog.json", arch, key, length)
    release = system / "opt/aisoft-docker-release/docker-release-v1"
    tree("docker-release/install", "codex/runtime/aisoft_release", release / "runtime/aisoft_release", system, "*.py")
    for dirname in ("schema", "compatibility"):
        tree("docker-release/install", "docker-release/" + dirname, release / dirname, system, "*.json")
    for filename in ("target-profile.example.json", "action-grant.example.json"):
        add("docker-release/install", "docker-release/templates/" + filename,
            system / "etc/aisoft-docker-release/examples/docker-release-v1" / filename, system)
    for tool in ("aisoft-docker-release", "aisoft-docker-release-gate"):
        add("docker-release/install", "docker-release/bin/" + tool, system / "usr/local/bin" / tool, system)
    json_metric("docker-release/install", "matrix revision", "docker-release/compatibility/image-stores-v1.json",
                release / "compatibility/image-stores-v1.json", system, "matrix_revision", False)
    surfaces["docker-release/install"].metrics["schemas"] = Metric(len(list((repo / "docker-release/schema").glob("*.json"))),
        "patterns", [release / "schema"], system, pattern="*.json")
    sync_targets = []
    for filename in ("inbound-sync.sh", "git-credential-token-file.sh"):
        target = system / "opt/aisoft-sync" / filename
        add("sync/install", "sync/" + filename, target, system)
        sync_targets.append(target)
    add("sync/install", "sync/templates/project.env.example", system / "etc/aisoft-sync/project.env.example", system)
    tree("sync/install", "sync/systemd", system / "etc/systemd/system", system, "*")
    surfaces["sync/install"].metrics["units"] = Metric(2, "files", [system / "etc/systemd/system" / n for n in ("aisoft-inbound-sync@.service", "aisoft-inbound-sync@.timer")], system)
    surfaces["sync/install"].metrics["runtime scripts"] = Metric(2, "files", sync_targets, system)

    metadata_sources.add(repo / "skill-for-claude/skills.manifest")
    declared = {}
    for line in read_bytes(repo / "skill-for-claude/skills.manifest", repo).decode("utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 2 or fields[1] not in {"shared", "none"} or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields[0]) or fields[0] in declared:
            raise InspectionError("invalid-claude-manifest", repo / "skill-for-claude/skills.manifest")
        declared[fields[0]] = fields[1]
    actual = {p.parent.name for p in (repo / "skill-for-claude").glob("*/SKILL.md")}
    if not declared or set(declared) != actual:
        raise InspectionError("claude-skill-set-mismatch", repo / "skill-for-claude/skills.manifest")
    claude = home / ".claude/skills"
    for name, mode in declared.items():
        target = claude / name
        add("skill-for-claude/install", "skill-for-claude/" + name + "/SKILL.md", target / "SKILL.md", home)
        surfaces["skill-for-claude/install"].exact_trees.append((target, home, True))
        if mode == "shared":
            tree("skill-for-claude/install", "skill-for-codex/references", target / "references", home, "*.md")
            label = "references" if name == "aisoft-platform" else "references:" + name
            surfaces["skill-for-claude/install"].metrics[label] = Metric(len(list((repo / "skill-for-codex/references").glob("*.md"))),
                "patterns", [target / "references"], home, pattern="*.md")
    surfaces["skill-for-claude/install"].metrics["skills"] = Metric(len(declared), "files", [claude / n / "SKILL.md" for n in declared], home)
    return list(surfaces.values()), metadata_sources


def validate_source(repo: Path, surfaces: list[Surface]):
    discovered = set()
    candidates = (p for p in repo.rglob("install*.sh")
                  if not ({".git", ".claude", ".agents", ".codex", "archive", "vendor", "tests"}
                          & set(p.relative_to(repo).parts)))
    for p in candidates:
        text = read_bytes(p, repo).decode("utf-8")
        if re.search(r"^\s*aisoft_install_source_guard\s", text, re.M):
            discovered.add(str(p.relative_to(repo)))
    if discovered != set(INSTALLER_PINS):
        raise InspectionError("installer-set-mismatch", repo)
    for relative, pin in INSTALLER_PINS.items():
        if hashlib.sha256(read_bytes(repo / relative, repo)).hexdigest() != pin:
            raise InspectionError("installer-mapping-stale", repo / relative)
    for surface in surfaces:
        if not surface.files:
            raise InspectionError("empty-source-surface", repo)
        for source, _target, _boundary in surface.files:
            read_bytes(source, repo)
    # These are fixed dependencies of the generated/artifact verifier, rather
    # than a legitimate PR adding/removing an optional installed module.
    helper = repo / "codex/tools/gitea-pat-helper"
    for name in HELPER_SOURCE_INPUTS:
        read_bytes(helper / name, repo)
    lock_path = helper / "build-lock.json"
    lock = strict_document(lock_path, repo)
    require(isinstance(lock, dict) and set(lock) == {"version", "files", "gitea"}
            and lock["version"] == "go1.26.3" and isinstance(lock["files"], list),
            "helper-lock-schema", lock_path)
    model = lock["gitea"]
    require(isinstance(model, dict) and set(model) == {"module", "version", "module_sum", "model_path", "model_sha256"}
            and model["module"] == "code.gitea.io/gitea" and model["version"] == "v1.26.4"
            and model["model_path"] == "models/auth/access_token.go"
            and isinstance(model["module_sum"], str) and model["module_sum"].startswith("h1:")
            and sha256_value(model["model_sha256"]), "helper-model-lock-invalid", lock_path)
    platforms = set()
    for item in lock["files"]:
        require(isinstance(item, dict)
                and set(item) == {"filename", "os", "arch", "version", "sha256", "size", "kind"}
                and isinstance(item["os"], str) and isinstance(item["arch"], str)
                and item["version"] == "go1.26.3" and sha256_value(item["sha256"])
                and type(item["size"]) is int and item["size"] > 0 and item["kind"] == "archive"
                and item["filename"] == f"go1.26.3.{item['os']}-{item['arch']}.tar.gz",
                "helper-toolchain-lock-invalid", lock_path)
        platform = item["os"] + "/" + item["arch"]
        require(platform not in platforms, "helper-toolchain-lock-invalid", lock_path)
        platforms.add(platform)
    require({"linux/arm64", "linux/amd64"} <= platforms, "helper-linux-lock-missing", lock_path)


def source_identity(repo: Path, sources: set[Path]):
    # Only local read operations. Disable optional locks, fsmonitor and diff helpers.
    git_env = {key: value for key, value in os.environ.items()
               if not key.startswith("GIT_")}
    git_env.update(GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1")
    def git(*args):
        p = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-c", "credential.helper=",
                            "-C", str(repo), *args], capture_output=True, text=True,
                           env=git_env)
        return p.returncode, p.stdout.strip()
    result = {"checkout": str(repo), "head": None, "cached_origin_main": None,
              "head_is_cached_main_ancestor": False,
              "managed_source_matches_cached_main": False,
              "remote_freshness": "EXTERNAL_EVIDENCE_REQUIRED"}
    try:
        rc, head = git("rev-parse", "--verify", "HEAD")
        if rc == 0:
            result["head"] = head
        rc, cached = git("rev-parse", "--verify", "refs/remotes/origin/main")
        if rc == 0:
            result["cached_origin_main"] = cached
        if result["head"] and result["cached_origin_main"]:
            result["head_is_cached_main_ancestor"] = git("merge-base", "--is-ancestor", head, cached)[0] == 0
            paths = sorted(str(p.relative_to(repo)) for p in sources)
            # Fixed tree roots also cover a wholly removed package/skill; deriving
            # roots from surviving files would silently omit that deletion.
            scopes = {"codex/runtime/" + name for name in ("aisoft_loop", "aisoft_host_access",
                      "aisoft_gitea_governance", "aisoft_architecture", "aisoft_release")}
            scopes.update({"codex/agent", "codex/systemd", "codex/skills", "skill-for-codex",
                           "codex/tools/gitea-pat-helper",
                           "codex/vendor/mattpocock", "docker-release/schema",
                           "docker-release/compatibility", "sync/systemd"})
            scopes.update("architecture/" + name for name in ("profiles", "schemas", "templates", "decisions"))
            # Read raw tree metadata and hash worktree bytes ourselves. git diff
            # can run configured clean filters even with --no-ext-diff/textconv.
            rc, tree = git("ls-tree", "-r", "-z", cached, "--", *sorted(set(paths) | scopes))
            blobs = {}
            for entry in tree.split("\0"):
                if not entry:
                    continue
                metadata, relative = entry.split("\t", 1)
                mode, kind, oid = metadata.split()
                if kind != "blob" or mode not in {"100644", "100755"}:
                    raise ValueError("non-regular source in cached tree")
                blobs[relative] = oid
            matches = rc == 0 and bool(blobs) and set(paths) <= set(blobs)
            for relative, oid in blobs.items():
                data = read_bytes(repo / relative, repo)
                digest = hashlib.sha256() if len(oid) == 64 else hashlib.sha1()
                digest.update(b"blob " + str(len(data)).encode("ascii") + b"\0" + data)
                matches = matches and digest.hexdigest() == oid
            result["managed_source_matches_cached_main"] = matches
    except (OSError, InspectionError, ValueError):
        pass
    result["result"] = "PASS" if result["managed_source_matches_cached_main"] else "GAP"
    return result


def inspect_surface(surface: Surface, repo: Path, identity=None, public=None):
    gaps = []

    def gap(reason, path, **extra):
        gaps.append({"reason": reason, "target": str(path), **extra})

    for source, target, boundary in surface.files:
        try:
            if read_bytes(source, repo) != read_bytes(target, boundary):
                gap("bytes-differ", target, source=str(source))
        except InspectionError as exc:
            gap(exc.reason, target, source=str(source))
    for target, expected, boundary in surface.links:
        try:
            st = checked_stat(target, boundary, link=True)
            if not stat.S_ISLNK(st.st_mode):
                gap("not-symlink", target)
            elif read_link(target, boundary) != expected:
                gap("link-target-differ", target, expected=expected)
        except (InspectionError, OSError) as exc:
            gap(exc.reason if isinstance(exc, InspectionError) else "unreadable", target)
    for target, boundary in surface.absent:
        try:
            checked_stat(target, boundary, link=True)
            gap("retired-target-present", target)
        except InspectionError as exc:
            if exc.reason != "missing":
                gap(exc.reason, target)
    for tree, boundary, check_dirs in surface.exact_trees:
        expected = {target for _source, target, _boundary in surface.files if target.is_relative_to(tree)}
        allowed_dirs = {parent for target in expected for parent in target.parents if parent.is_relative_to(tree)}

        def extras(directory):
            for p in directory_entries(directory, boundary):
                if p.name == "__pycache__" or p.suffix == ".pyc":
                    continue
                st = checked_stat(p, boundary, link=True)
                if stat.S_ISDIR(st.st_mode):
                    if check_dirs and p not in allowed_dirs:
                        gap("unexpected-entry", p)
                    extras(p)
                elif p not in expected:
                    gap("unexpected-entry", p)
        try:
            extras(tree)
        except InspectionError as exc:
            gap(exc.reason, exc.path)
    quantities = {}
    for name, metric in surface.metrics.items():
        actual = None
        try:
            actual = metric.installed()
            if actual != metric.expected:
                gap("quantity-mismatch", metric.targets[0], quantity=name, expected=metric.expected, installed=actual)
        except (InspectionError, OSError) as exc:
            gap(exc.reason if isinstance(exc, InspectionError) else "unreadable", metric.targets[0], quantity=name)
        quantities[name] = {"expected": metric.expected, "installed": actual}
    rotation = {}
    if surface.rotation is not None:
        rotation, rotation_gaps = surface.rotation.inspect(repo, identity, public)
        gaps.extend(rotation_gaps)
    return {"installer": surface.installer, "scope": "INSTALLED", "result": "GAP" if gaps else "PASS",
            "expected_files": len(surface.files), "expected_links": len(surface.links),
            "quantities": quantities, "gaps": gaps, "also_checked_by": surface.also_checked_by,
            "user_owned_not_read": surface.user_owned, **({"rotation": rotation} if surface.rotation else {})}


def absolute(value: str) -> Path:
    if not Path(value).is_absolute():
        raise argparse.ArgumentTypeError("paths must be absolute")
    # Lexical normalization: source-only must not probe declared target roots.
    return Path(os.path.normpath(value))


def public_provenance(value: str) -> Path:
    path = absolute(value)
    if path.name != "gitea-pat-helper.provenance.json" or ".." in Path(value).parts:
        raise argparse.ArgumentTypeError("expected absolute public gitea-pat-helper.provenance.json path")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=absolute, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--target-home", type=absolute, default=Path.home())
    parser.add_argument("--install-root", type=absolute, default=Path("/"))
    parser.add_argument("--agent-dir", type=absolute)
    parser.add_argument("--architecture-prefix", type=absolute)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--pat-helper-provenance", type=public_provenance)
    args = parser.parse_args(argv)
    roots = {"repo": args.repo, "target_home": args.target_home, "install_root": args.install_root,
             "agent_dir": args.agent_dir or args.target_home / "agent",
             "architecture_prefix": args.architecture_prefix or args.install_root / "usr/local"}
    report = {"mode": "source-only" if args.source_only else "installed", "roots": {k: str(v) for k, v in roots.items()}, "installers": []}
    if args.pat_helper_provenance is not None:
        report["public_provenance"] = {"path": str(args.pat_helper_provenance),
                                       "access": "NOT_READ_SOURCE_ONLY" if args.source_only else "DECLARED_INPUT"}
    try:
        surfaces, sources = build_surfaces(*roots.values())
        validate_source(args.repo, surfaces)
        sources.update(source for surface in surfaces for source, _target, _boundary in surface.files)
        identity = source_identity(args.repo, sources)
        report["source"] = identity
        if args.source_only:
            for surface in surfaces:
                report["installers"].append({"installer": surface.installer, "scope": "SOURCE", "result": "PASS",
                    "expected_files": len(surface.files), "quantities": {n: {"expected": m.expected} for n, m in surface.metrics.items()}})
        else:
            report["installers"] = [inspect_surface(s, args.repo, identity, args.pat_helper_provenance) for s in surfaces]
            by_name = {row["installer"]: row for row in report["installers"]}
            for surface in surfaces:
                for dependency in surface.also_checked_by:
                    if by_name[dependency]["result"] == "GAP":
                        by_name[surface.installer]["result"] = "GAP"
                        by_name[surface.installer]["gaps"].append({"reason": "nested-installer-gap", "installer": dependency,
                                                                   "target": str(args.target_home / ".agents/skills")})
        # A valid PR is allowed to change managed source before merge. Source-only
        # gates definition integrity, while retaining main drift as provenance;
        # installed mode still requires that identity as well as installed bytes.
        code = int(not args.source_only and (identity["result"] != "PASS" or
                   any(row["result"] != "PASS" for row in report["installers"])))
    except (InspectionError, OSError, UnicodeError, ValueError, AttributeError) as exc:
        code = 2
        report["error"] = {"reason": exc.reason if isinstance(exc, InspectionError) else "invalid-source-definition",
                           "source": str(exc.path) if isinstance(exc, InspectionError) else str(args.repo)}
    report["result"] = "PASS" if code == 0 else "GAP" if code == 1 else "ERROR"
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print("SOURCE " + json.dumps(report.get("source", report.get("error", {})), ensure_ascii=False))
        print("ROOTS " + json.dumps(report["roots"], ensure_ascii=False))
        if "public_provenance" in report:
            print("PUBLIC_PROVENANCE " + json.dumps(report["public_provenance"], ensure_ascii=False))
        for row in report["installers"]:
            print(f"{row['scope']} {row['result']}: {row['installer']} " + json.dumps(row["quantities"], ensure_ascii=False))
            if "rotation" in row:
                print("  ROTATION " + json.dumps(row["rotation"], ensure_ascii=False))
            for gap in row.get("gaps", []):
                print("  GAP " + json.dumps(gap, ensure_ascii=False))
        print("RESULT " + report["result"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
