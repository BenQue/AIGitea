"""#327 direct Git history, merge-tree and ordinary single-ref publication.

These are cooperative Git/contract checks. Neither a marker nor this module
proves physical authorship, human approval, root custody or OS isolation.
The standalone pre-push entry has only standard-library dependencies.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile


ZERO = "0" * 40
SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_GIT_OUTPUT = 16 * 1024 * 1024
MODULE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class GitError(ValueError):
    def __init__(self, code, message, receipt=None):
        super().__init__(message)
        self.code = code
        self.receipt = receipt


def require(condition, message, code="GIT_OBJECT_DENIED"):
    if not condition:
        raise GitError(code, message)


def oid(value, optional=False):
    if optional and value is None:
        return None
    require(type(value) is str and SHA.fullmatch(value), "exact SHA-1 required")
    return value


def valid_path(value):
    require(type(value) is str and 0 < len(value.encode()) <= 1024
            and not value.startswith("/") and not any(c in value for c in "\\\0\r\n\t*?[")
            and not any(p in {"", ".", "..", ".git"} for p in value.split("/")),
            "invalid exact scope path", "SCOPE_DENIED")
    return value


def git_environment(extra=None, config=()):
    """Discard caller Git/SSH/Python settings; retain only explicit overrides."""
    env = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_ATTR_NOSYSTEM": "1",
           "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0",
           "GIT_OPTIONAL_LOCKS": "0", "GIT_ASKPASS": "/usr/bin/false"}
    fixed = [("core.hooksPath", "/dev/null"), ("core.fsmonitor", "false"),
             ("core.attributesFile", "/dev/null"), ("push.followTags", "false"),
             ("push.default", "nothing"), ("commit.gpgSign", "false")]
    fixed.extend((("push.recurseSubmodules", "no"), ("submodule.recurse", "false"),
                  ("push.gpgSign", "false")))
    # A broker supplies the manifest-bound credential override, never a caller
    # environment. Keep the original ordering (empty helper, then fixed helper).
    if extra:
        count = int(extra.get("GIT_CONFIG_COUNT", "0"))
        require(0 <= count <= 64, "invalid fixed Git configuration")
        for i in range(count):
            fixed.append((extra["GIT_CONFIG_KEY_" + str(i)], extra["GIT_CONFIG_VALUE_" + str(i)]))
    fixed.extend(config)
    env["GIT_CONFIG_COUNT"] = str(len(fixed))
    for i, (key, value) in enumerate(fixed):
        env["GIT_CONFIG_KEY_" + str(i)] = key
        env["GIT_CONFIG_VALUE_" + str(i)] = value
    return env


def _runner(argv, *, cwd=None, env=None):
    return subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True,
                          timeout=60, check=False)


@dataclass(frozen=True)
class Commit:
    sha: str
    tree: str
    parents: tuple[str, ...]


@dataclass(frozen=True)
class Scope:
    paths: tuple[str, ...]
    history_head: str | None = None
    history_paths: tuple[str, ...] = ()


class GitRepository:
    def __init__(self, repo, *, runner=None, env=None):
        self.repo = Path(repo).resolve()
        self.runner = runner or _runner
        self.env = git_environment(env)

    def run(self, *args, allowed=(0,), env=None):
        try:
            result = self.runner(["git", *args], cwd=str(self.repo), env=env or self.env)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GitError("GIT_CAPABILITY_GAP", "fixed Git operation unavailable") from exc
        require(len(result.stdout.encode()) <= MAX_GIT_OUTPUT
                and len(result.stderr.encode()) <= 65536, "Git output exceeds bound")
        require(result.returncode in allowed, "Git rejected objects/operation")
        return result

    def text(self, *args, **kwargs):
        return self.run(*args, **kwargs).stdout.strip()

    def assert_supported(self):
        common = Path(self.text("rev-parse", "--git-common-dir"))
        if not common.is_absolute():
            common = self.repo / common
        require(self.text("rev-parse", "--show-object-format") == "sha1", "unsupported object format")
        require(self.text("rev-parse", "--is-shallow-repository") == "false", "shallow repository denied")
        require(not self.text("for-each-ref", "--format=%(refname)", "refs/replace"), "replace refs denied")
        for name in ("info/grafts", "objects/info/alternates", "info/attributes", "shallow"):
            require(not (common / name).exists(), "graft/alternate/attributes/shallow denied")
        # Include the active config.worktree when standard worktreeConfig is
        # enabled. The extension itself is valid; unsafe per-worktree settings
        # are rejected by the same rules as common repository configuration.
        keys = self.text("config", "--name-only", "--list").lower().splitlines()
        for key in keys:
            require(not (key.startswith(("include.", "includeif.", "filter."))
                         or key.endswith((".driver", ".receivepack", ".uploadpack", ".proxy", ".vcs"))
                         or key in {"core.gitproxy", "core.sshcommand", "core.worktree"}),
                    "unsupported Git configuration", "GIT_CONFIG_DENIED")

    def commit(self, sha):
        oid(sha)
        raw = self.run("cat-file", "commit", sha).stdout
        tree = None
        parents = []
        for line in raw.split("\n\n", 1)[0].splitlines():
            if line.startswith("tree "):
                require(tree is None, "duplicate tree")
                tree = oid(line[5:])
            elif line.startswith("parent "):
                parents.append(oid(line[7:]))
        require(tree is not None and len(parents) <= 2, "unsupported commit parent shape", "DAG_DENIED")
        return Commit(sha, tree, tuple(parents))

    def ancestor(self, before, after):
        oid(before); oid(after)
        return self.run("merge-base", "--is-ancestor", before, after, allowed=(0, 1)).returncode == 0

    def delta_paths(self, before, after):
        oid(before); oid(after)
        # Every commit, including an add subsequently reverted, is inspected.
        out = self.run("diff", "--no-ext-diff", "--no-renames", "--name-only", "-z", before, after, "--").stdout
        paths = tuple(p for p in out.split("\0") if p)
        for name in paths:
            valid_path(name)
            entry = self.text("ls-tree", after, "--", name)
            require(not entry or entry.startswith(("100644 blob ", "100755 blob ")),
                    "changed symlink/submodule denied", "SCOPE_DENIED")
        return paths

    def reject_merge_attributes(self, sha):
        names = self.run("ls-tree", "-r", "-z", "--name-only", sha).stdout.split("\0")
        for name in names:
            if name.rsplit("/", 1)[-1] == ".gitattributes":
                require("merge" not in self.run("show", sha + ":" + name).stdout,
                        "custom/unsupported merge attributes", "MERGE_DRIVER_DENIED")

    def merge_tree(self, first, main):
        oid(first); oid(main)
        bases = self.text("merge-base", "--all", first, main).splitlines()
        require(len(bases) == 1, "multiple/no merge base denied", "MERGE_BASE_DENIED")
        for sha in (first, main, bases[0]):
            self.reject_merge_attributes(sha)
        # merge-tree writes only into an owned temporary object directory.
        # It never edits the worktree, index, refs or shared object database.
        common = Path(self.text("rev-parse", "--git-common-dir"))
        if not common.is_absolute():
            common = self.repo / common
        with tempfile.TemporaryDirectory(prefix="aisoft-merge-tree-") as directory:
            env = dict(self.env, GIT_OBJECT_DIRECTORY=directory,
                       GIT_ALTERNATE_OBJECT_DIRECTORIES=str((common / "objects").resolve()))
            result = self.run("merge-tree", "--write-tree", "--no-messages", first, main,
                              allowed=(0, 1), env=env)
            require(result.returncode == 0, "main integration conflicts", "MERGE_CONFLICT")
            return oid(result.stdout.strip())

    def verify_history(self, *, head, main, original, remote, paths,
                       history_head=None, history_paths=(), require_main=True):
        self.assert_supported()
        oid(head); oid(main); oid(original, True); oid(remote, True)
        allowed = set(map(valid_path, paths))
        historical = set(map(valid_path, history_paths))
        require(allowed, "approved exact scope missing", "SCOPE_UNKNOWN")
        for anchor in (main if require_main else None, original, remote, history_head):
            if anchor is not None:
                require(self.ancestor(anchor, head), "required history lost", "NON_FAST_FORWARD")
        # Independently check reachable objects. Rev-list alone can omit a
        # missing blob or mislead a check that considers only the final diff.
        # Check object hashes/connectivity for the exact anchors. The typed
        # route and guard verify our refs separately; unrelated local ref-db
        # housekeeping (e.g. Finder's .DS_Store) is outside this Issue DAG.
        # Git versions lacking this explicit mode fail closed.
        self.run("fsck", "--strict", "--no-reflogs", "--no-dangling", "--no-references", head, main)
        relevant = set(self.text("rev-list", head, "^" + main).splitlines())
        require(len(relevant) <= 4096, "relevant history exceeds supported bound")
        chain = []
        cursor = head
        while cursor in relevant:
            commit = self.commit(cursor)
            require(commit.parents and cursor not in {c.sha for c in chain}, "invalid first-parent chain", "DAG_DENIED")
            if len(commit.parents) == 2:
                first, second = commit.parents
                require(not self.ancestor(first, main) and self.ancestor(second, main),
                        "integration parents are not [Issue tip, manifest main]", "FOREIGN_MERGE_DENIED")
                require(not self.ancestor(second, first), "redundant/out-of-order main integration", "DAG_DENIED")
                require(commit.tree == self.merge_tree(first, second),
                        "integration tree contains extra content", "MERGE_TREE_DENIED")
            else:
                permitted = historical if history_head and self.ancestor(cursor, history_head) else allowed
                changed = self.delta_paths(commit.parents[0], cursor)
                require(set(changed) <= permitted, "per-commit delta exceeds approved exact scope", "SCOPE_DENIED")
            chain.append(commit)
            cursor = commit.parents[0]
        require({c.sha for c in chain} == relevant, "candidate includes an unexamined side history", "DAG_DENIED")
        return tuple(reversed(chain))

    def scope(self, head, branch):
        """Read the machine projection of the approved mapped spec from Git.

        This is contract data, not a grant, creator identity or approval proof.
        A missing projection fails closed; no directory-wide fallback is used.
        """
        match = re.fullmatch(r"change/([1-9][0-9]*)(?:-([a-z0-9]+(?:-[a-z0-9]+){1,3}))?", branch)
        require(match is not None, "invalid change branch", "SCOPE_UNKNOWN")
        number = match[1]
        directory = "docs/changes/" + branch.removeprefix("change/") + "/"
        names = self.text("ls-tree", "-r", "--name-only", head, "--", directory).splitlines()
        summaries = [name for name in names if Path(name).name == "00-summary.md" or Path(name).name.startswith("summary-")]
        require(len(summaries) == 1, "exact mapped summary missing", "SCOPE_UNKNOWN")
        summary = self.run("show", head + ":" + summaries[0]).stdout
        require(summary.startswith("---\n") and "\n---\n" in summary,
                "summary front matter missing", "SCOPE_UNKNOWN")
        summary_front = summary.split("\n---\n", 1)[0]
        for key, expected in (("issue", number), ("branch", branch), ("status", "approved")):
            require(re.findall(r"^" + key + r": (.+)$", summary_front, re.M) == [expected],
                    "mapped summary binding/status differs", "SCOPE_UNKNOWN")
        spec_names = re.findall(r"^  spec: ([A-Za-z0-9._-]+)\s*$", summary_front, re.M)
        spec_name = spec_names[0] if len(spec_names) == 1 else "01-spec.md" if match[2] is None else ""
        require(spec_name and directory + spec_name in names, "exact mapped spec missing", "SCOPE_UNKNOWN")
        spec = self.run("show", head + ":" + directory + spec_name).stdout
        require(spec.startswith("---\n") and "\n---\n" in spec, "spec front matter missing", "SCOPE_UNKNOWN")
        front = spec.split("\n---\n", 1)[0]
        for key, expected in (("issue", number), ("branch", branch), ("status", "approved")):
            require(re.findall(r"^" + key + r": (.+)$", front, re.M) == [expected],
                    "mapped spec binding/status differs", "SCOPE_UNKNOWN")
        def paths(key):
            value = re.findall(r"^" + key + r":\n((?:  - [^\n]+\n?)+)", front, re.M)
            require(len(value) <= 1, "duplicate scope projection", "SCOPE_UNKNOWN")
            result = tuple(line[4:] for line in value[0].splitlines()) if value else ()
            require(len(result) <= 256 and len(result) == len(set(result)), "invalid scope projection", "SCOPE_UNKNOWN")
            for name in result:
                valid_path(name)
                require(not name.startswith("docs/changes/") or name.startswith(directory),
                        "scope crosses another Issue", "SCOPE_DENIED")
            return result
        scope = paths("git_scope")
        old = re.findall(r"^git_history_head: ([0-9a-f]{40})$", front, re.M)
        require(scope and len(old) <= 1, "approved exact Git scope missing", "SCOPE_UNKNOWN")
        return Scope(scope, old[0] if old else None, paths("git_history_paths"))


def validate_pre_push(data, *, branch, head, remote):
    """Verify the actual advertised old-id, including first-ref all-zeroes."""
    oid(head); oid(remote, True)
    require(type(data) is bytes and len(data) <= 4096, "invalid hook input", "GUARD_DENIED")
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise GitError("GUARD_DENIED", "invalid hook encoding") from exc
    require(len(lines) == 1, "exactly one advertised update required", "REMOTE_BRANCH_MOVED")
    fields = lines[0].split()
    require(fields == [head, head, "refs/heads/" + branch, remote or ZERO],
            "advertised head/ref/old-id moved", "REMOTE_BRANCH_MOVED")
    return hashlib.sha256(data).hexdigest()


class PushGuard:
    """Fixed code/argv copied from this module, never an editable repo hook."""
    def __init__(self, repository, branch, head, remote, *, remote_name="origin"):
        self.repository = repository
        self.branch = branch
        self.head = oid(head)
        self.remote = oid(remote, True)
        self.remote_name = remote_name

    def __enter__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aisoft-pre-push-")
        self.directory = Path(self.temporary.name)
        self.program = self.directory / "guard.py"
        self.program.write_bytes(Path(__file__).read_bytes())
        self.program.chmod(0o400)
        self.program_hash = hashlib.sha256(self.program.read_bytes()).hexdigest()
        require(self.program_hash == MODULE_SHA256, "loaded guard module changed", "GUARD_DRIFT")
        self.receipt_path = self.directory / "receipt.json"
        self.nonce = secrets.token_hex(32)
        args = ["/usr/bin/python3", "-I", "-S", "-B", str(self.program), "_pre_push",
                str(self.repository.repo), self.branch, self.head, self.remote or ZERO,
                str(self.receipt_path), self.nonce, self.program_hash]
        # These strings are broker-owned values; quote every shell literal.
        def quote(value):
            return "'" + value.replace("'", "'\"'\"'") + "'"
        self.guard_argv = args
        self.hook = self.directory / "pre-push"
        self.hook.write_text("#!/bin/sh\nexec " + " ".join(map(quote, args)) + ' "$@"\n')
        self.hook.chmod(0o500)
        self.hook_hash = hashlib.sha256(self.hook.read_bytes()).hexdigest()
        self.env = git_environment(self.repository.env, config=(("core.hooksPath", str(self.directory)),
                                   ("remote." + self.remote_name + ".mirror", "false")))
        self.argv = ["git", "push", "--porcelain", self.remote_name,
                     self.head + ":refs/heads/" + self.branch]
        return self

    def assert_pinned(self):
        require(self.program.is_file() and self.hook.is_file()
                and hashlib.sha256(self.program.read_bytes()).hexdigest() == self.program_hash
                and hashlib.sha256(self.hook.read_bytes()).hexdigest() == self.hook_hash,
                "fixed guard code drift", "GUARD_DRIFT")

    def run(self, runner=None):
        self.assert_pinned()
        return (runner or self.repository.runner)(self.argv, cwd=str(self.repository.repo), env=self.env)

    def receipt(self):
        if not self.receipt_path.is_file():
            return None
        require(self.receipt_path.stat().st_size <= 8192, "guard receipt exceeds bound", "GUARD_DENIED")
        try:
            data = json.loads(self.receipt_path.read_text())
        except (ValueError, OSError) as exc:
            raise GitError("GUARD_DENIED", "guard receipt unreadable") from exc
        require(data.get("nonce") == self.nonce and data.get("head") == self.head
                and data.get("remote") == self.remote and data.get("program_sha256") == self.program_hash,
                "guard receipt binding differs", "GUARD_DENIED")
        return data

    def __exit__(self, *_args):
        self.temporary.cleanup()


def ordinary_push(repository, *, remote_name, branch, head, remote, read_remote, runner=None):
    """One attempt only. Preserve an actual/possible write on every failure."""
    receipt = {"head": oid(head), "previous_head": oid(remote, True),
               "observed_remote_head": None, "possible_write": False,
               "guard_executed": False, "write_status": "NOT_ATTEMPTED"}
    with PushGuard(repository, branch, head, remote, remote_name=remote_name) as guard:
        receipt.update(argv=guard.argv, guard_program_sha256=guard.program_hash,
                       guard_hook_sha256=guard.hook_hash, guard_argv=guard.guard_argv)
        guard.assert_pinned()
        receipt["possible_write"] = True
        receipt["write_status"] = "UNKNOWN"
        try:
            result = guard.run(runner)
            guard.assert_pinned()
            executed = guard.receipt()
            receipt["guard_executed"] = executed is not None
            if executed is not None and executed.get("code") != "PASS":
                receipt.update(possible_write=False, write_status="REFUSED")
                raise GitError(executed["code"], "pre-push guard refused transport")
            receipt["observed_remote_head"] = oid(read_remote(), True)
            require(executed is not None, "fixed guard was not executed", "GUARD_NOT_EXECUTED")
            require(result.returncode == 0, "ordinary push refused/transport failed", "REMOTE_BRANCH_MOVED")
            statuses = [line.split("\t") for line in result.stdout.splitlines()
                        if len(line) >= 2 and line[1] == "\t"]
            require(len(statuses) == 1 and statuses[0][0] in {" ", "*"}
                    and statuses[0][1] == head + ":refs/heads/" + branch,
                    "transport did not perform the verified ref update", "PUSH_STATUS_INVALID")
            require(receipt["observed_remote_head"] == head, "remote readback differs", "PUSH_READBACK_UNKNOWN")
            receipt["write_status"] = "PUBLISHED"
            return receipt
        except Exception as exc:
            if receipt["observed_remote_head"] is None:
                try:
                    receipt["observed_remote_head"] = oid(read_remote(), True)
                except Exception:
                    pass
            code = getattr(exc, "code", "PUSH_READBACK_UNKNOWN")
            raise GitError(code, str(exc), dict(receipt)) from exc


def qualified_broker_environment():
    """Read-only cooperative version binding before the installed Git write.

    This checks the dispatch and FF modules, not root custody or OS closure.
    Old/mixed surfaces stop before invoking the wrapper. No installation.
    """
    wrapper = Path("/usr/local/libexec/aisoft/host-access-broker")
    installed = Path("/usr/local/lib/aisoft-host-access")
    source = Path(__file__).resolve().parent
    pairs = [(source / name, installed / name) for name in (
        "aisoft_main_integration.py", "aisoft_worktree_owner.py", "aisoft_change_name.py",
        "aisoft_host_access/__init__.py", "aisoft_host_access/cli.py",
        "aisoft_host_access/broker.py", "aisoft_host_access/contract.py")]
    def digest(path):
        import stat
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_size <= 4 * 1024 * 1024,
                "broker file missing/nonregular/oversized", "BROKER_SURFACE_GAP")
        return hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        require(digest(wrapper) == "88c663af3a3e3b710cc271e7ff671e279d38fc357657330682a338d6ba3f4135",
                "installed wrapper version differs", "BROKER_SURFACE_GAP")
        require(all(digest(a) == digest(b) for a, b in pairs),
                "installed dispatch/FF surface is old or mixed", "BROKER_SURFACE_GAP")
        require(digest(source / "aisoft_main_integration.py") == MODULE_SHA256,
                "loaded Git module changed", "BROKER_SURFACE_GAP")
    except OSError as exc:
        raise GitError("BROKER_SURFACE_GAP", "installed FF surface is unavailable") from exc
    from aisoft_worktree_owner import caller_session, SESSION_RE
    session = caller_session()
    require(SESSION_RE.fullmatch(session or ""), "owner session missing/invalid", "BROKER_SURFACE_GAP")
    env = git_environment()
    env["AISOFT_SESSION_ID"] = session
    env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONSAFEPATH="1")
    return env


def publication_projection(value, head, *, started=True):
    """Bounded non-secret audit fields; an invalid reply cannot prove zero write."""
    result = {"head": oid(head), "possible_write": bool(started), "outcome": "UNKNOWN"}
    if type(value) is not dict:
        return result
    for key in ("head", "pushed_head", "observed_remote_head", "previous_head",
                "original_remote_head", "main", "observed_main"):
        item = value.get(key)
        if item is None or (type(item) is str and SHA.fullmatch(item)):
            if key != "head" or item == head:
                result[key] = item
    for key in ("code", "write_status"):
        item = value.get(key)
        if type(item) is str and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", item):
            result[key] = item
    # Only a complete exact-H receipt can lower possible_write for a no-op.
    if (value.get("status") == "PASS" and value.get("operation") == "git.push.change"
            and value.get("code") in {"PUBLISHED", "NOOP"}
            and value.get("pushed_head") == head and value.get("observed_remote_head") == head):
        result["outcome"] = value["code"]
        result["possible_write"] = value["code"] == "PUBLISHED"
    return result


def publication_message(message, receipt):
    return message + "; publication=" + json.dumps(receipt, sort_keys=True, separators=(",", ":"))


def publication_reference(message):
    """Read the non-secret projection carried through the existing CLI error."""
    marker = "; publication="
    if marker not in message:
        return None
    try:
        data = json.loads(message.split(marker, 1)[1])
        require(type(data) is dict and type(data.get("possible_write")) is bool,
                "invalid publication projection")
        oid(data.get("head")); oid(data.get("observed_remote_head"), True)
        return data
    except (ValueError, TypeError):
        return None


def _pre_push(argv):
    require(len(argv) == 9, "invalid fixed pre-push argv", "GUARD_DENIED")
    repo, branch, head, remote, output, nonce, program_hash, _name, _url = argv
    remote = None if remote == ZERO else remote
    result = {"nonce": nonce, "head": head, "remote": remote, "program_sha256": program_hash}
    try:
        require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == program_hash,
                "guard program drift", "GUARD_DRIFT")
        data = sys.stdin.buffer.read(4097)
        result["input_sha256"] = validate_pre_push(data, branch=branch, head=head, remote=remote)
        repository = GitRepository(repo)
        require(repository.text("symbolic-ref", "--short", "HEAD") == branch
                and repository.text("rev-parse", "HEAD") == head,
                "local HEAD moved before transport", "HEAD_MOVED")
        require(not repository.text("status", "--porcelain"), "local worktree became dirty", "WORKTREE_DIRTY")
        result["code"] = "PASS"
    except GitError as exc:
        result["code"] = exc.code
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(result, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if result["code"] == "PASS" else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "_pre_push":
        raise SystemExit(_pre_push(sys.argv[2:]))
    raise SystemExit("only the fixed pre-push entry is executable")
