"""Synthetic project and Gitea for the project-declared source tests (#434).

Nothing here touches a real Gitea or a real project: the remote is a local bare
repository reached through a runner that rewrites only the network-bound Git
commands, and FakeGitea answers the REST paths the engine requests from an
in-memory store.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from aisoft_worktree_owner import claim as claim_worktree


ROOT = Path(__file__).resolve().parents[3]
LABELS = ROOT / "codex/config/gitea-labels.json"
BASE = "http://gitea.test:3000"
OWNER, NAME, AGENT = "acme", "widget", "widget-agent"
REMOTE_URL = f"{BASE}/{OWNER}/{NAME}.git"
SENTINEL = "sentinel0token0value0434"
SESSION = "project-source-session"
BRANCH = "change/7-demo-change"


def git(argv, *, cwd=None) -> str:
    return subprocess.run(["git", *argv], cwd=cwd, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def declaration(**overrides) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1, "repository": f"{OWNER}/{NAME}", "project_agent": AGENT,
        "deployment_lifecycle": "none", "classification": "internal-application",
        "status_check_contexts": ["CI / test (pull_request)"], "protection_evidence": 1,
    }
    value.update(overrides)
    return {key: item for key, item in value.items() if item is not None}


def write_declaration(checkout: Path, **overrides) -> None:
    (checkout / ".aisoft").mkdir(exist_ok=True)
    (checkout / ".aisoft/project.json").write_text(json.dumps(declaration(**overrides)) + "\n")


def build_project(temporary: str, *, remote_url: str = REMOTE_URL, with_declaration: bool = True):
    """Canonical checkout, linked change worktree with an approved git_scope, bare remote."""
    remote = Path(temporary) / "remote.git"
    canonical = Path(temporary) / "canonical"
    linked = Path(temporary) / "linked"
    git(["init", "-q", "--bare", "-b", "main", str(remote)])
    git(["init", "-q", "-b", "main", str(canonical)])
    git(["config", "user.name", "Project Source Test"], cwd=canonical)
    git(["config", "user.email", "project-source@example.invalid"], cwd=canonical)
    (canonical / "README.md").write_text("baseline\n")
    if with_declaration:
        write_declaration(canonical)
    git(["add", "-A"], cwd=canonical)
    git(["commit", "-q", "-m", "baseline"], cwd=canonical)
    git(["remote", "add", "origin", remote_url], cwd=canonical)
    git(["push", "-q", str(remote), "refs/heads/main:refs/heads/main"], cwd=canonical)
    git(["update-ref", "refs/remotes/origin/main", "HEAD"], cwd=canonical)
    git(["worktree", "add", "-q", "-b", BRANCH, str(linked)], cwd=canonical)
    (linked / "change.txt").write_text("change 7\n")
    directory = linked / "docs/changes/7-demo-change"
    directory.mkdir(parents=True)
    summary, spec = "summary-demo-change-261027.md", "spec-demo-change-261027.md"
    paths = ["change.txt", f"docs/changes/7-demo-change/{summary}", f"docs/changes/7-demo-change/{spec}"]
    (directory / summary).write_text(f"---\nissue: 7\nbranch: {BRANCH}\nstatus: approved\n"
                                     f"documents:\n  spec: {spec}\n---\n")
    (directory / spec).write_text(f"---\nissue: 7\nbranch: {BRANCH}\nstatus: approved\ngit_scope:\n"
                                  + "".join(f"  - {path}\n" for path in paths) + "---\n")
    git(["add", "-A"], cwd=linked)
    git(["commit", "-q", "-m", "#7 T01: demo change"], cwd=linked)
    claim_worktree(git(["rev-parse", "--absolute-git-dir"], cwd=linked), branch=BRANCH,
                   session=SESSION, worktree=linked)
    return remote, canonical, linked


def remote_runner(remote: Path, commands: list):
    """Real Git, with only the network-bound commands pointed at the bare repo."""
    def runner(argv, *, cwd=None, env=None):
        argv = list(argv)
        commands.append((argv, dict(env or {})))
        if argv[:2] in (["git", "fetch"], ["git", "push"], ["git", "ls-remote"]):
            argv = [str(remote) if token == "origin" else token for token in argv]
        return subprocess.run(argv, cwd=cwd, env=env, check=False, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return runner


class FakeGitea:
    """In-memory REST answers for exactly one repository."""

    def __init__(self, *, user=None, permissions=None):
        self.user = user if user is not None else {"login": AGENT, "is_admin": False}
        self.permissions = permissions if permissions is not None else {
            "admin": False, "push": True, "pull": True}
        self.labels: list[dict[str, object]] = []
        self.issues: dict[int, dict[str, object]] = {}
        self.comments: dict[int, list[dict[str, object]]] = {}
        self.pulls: dict[int, dict[str, object]] = {}
        self.requests: list[tuple[str, str, dict, bytes | None]] = []
        self.options: list[dict] = []
        self._next = 1

    def _id(self) -> int:
        self._next += 1
        return self._next

    def add_issue(self, number: int, title: str = "demo", labels=()) -> None:
        self.issues[number] = {
            "number": number, "title": title, "body": "AC", "state": "open",
            "created_at": "2026-10-27T00:00:00Z", "updated_at": "2026-10-27T00:00:00Z",
            "labels": [self._label(name) for name in labels], "pull_request": None,
        }

    def _label(self, name: str) -> dict[str, object]:
        for item in self.labels:
            if item["name"] == name:
                return item
        raise KeyError(name)

    def provision(self) -> None:
        manifest = json.loads(LABELS.read_text(encoding="utf-8"))
        for entry in manifest["canonical"]:
            self.labels.append({"id": self._id(), **entry})

    def __call__(self, method, url, headers, body, **options):
        self.requests.append((method, url, dict(headers), body))
        self.options.append(dict(options))
        parsed = urlparse(url)
        if f"{parsed.scheme}://{parsed.netloc}" != BASE:
            return 404, (), b"{}"
        path, query = parsed.path, parse_qs(parsed.query)
        payload = json.loads(body) if body else None
        status, value = self.route(method, path, query, payload)
        if isinstance(value, bytes):
            return status, (("Content-Type", "text/plain"),), value
        headers = [("Content-Type", "application/json")]
        if path.endswith("/pulls") and method == "GET":
            state = query["state"][0]
            total = sum(1 for item in self.pulls.values() if state in {"all", item["state"]})
            headers.append(("X-Total-Count", str(total)))
        return status, tuple(headers), json.dumps(value).encode()

    def route(self, method, path, query, payload):
        if path == "/api/v1/user":
            return 200, self.user
        repo = f"/api/v1/repos/{OWNER}/{NAME}"
        if path == repo:
            return 200, {"full_name": f"{OWNER}/{NAME}", "permissions": self.permissions}
        if not path.startswith(repo + "/"):
            return 404, {}
        rest = path[len(repo) + 1:]
        page = int(query.get("page", ["1"])[0])
        if rest == "labels":
            if method == "POST":
                item = {"id": self._id(), **payload}
                self.labels.append(item)
                return 201, item
            return 200, self.labels if page == 1 else []
        if match := re.fullmatch(r"labels/(\d+)", rest):
            item = next(label for label in self.labels if label["id"] == int(match.group(1)))
            item.update(payload)
            return 200, item
        if rest == "issues":
            if method == "POST":
                number = max([*self.issues, *self.pulls, 0]) + 1
                self.add_issue(number, payload["title"])
                ids = set(payload.get("labels", []))
                self.issues[number]["labels"] = [l for l in self.labels if l["id"] in ids]
                return 201, self.issues[number]
            state = query["state"][0]
            values = [item for item in self.issues.values() if state in {"all", item["state"]}]
            return 200, values if page == 1 else []
        if match := re.fullmatch(r"issues/(\d+)", rest):
            item = self.issues[int(match.group(1))]
            if method == "PATCH":
                item.update(payload)
            return 200, item
        if match := re.fullmatch(r"issues/(\d+)/comments", rest):
            number = int(match.group(1))
            if method == "POST":
                comment = {"id": self._id(), "body": payload["body"], "user": {"login": AGENT},
                           "created_at": "2026-10-27T00:00:00Z", "updated_at": "2026-10-27T00:00:00Z"}
                self.comments.setdefault(number, []).append(comment)
                return 201, comment
            return 200, self.comments.get(number, []) if page == 1 else []
        if match := re.fullmatch(r"issues/(\d+)/labels", rest):
            item = self.issues[int(match.group(1))]
            if method == "PUT":
                item["labels"] = [label for label in self.labels if label["id"] in payload["labels"]]
            return 200, item["labels"]
        if rest == "pulls":
            if method == "POST":
                number = max([*self.issues, *self.pulls, 0]) + 1
                pull = {"number": number, "title": payload["title"], "body": payload["body"],
                        "state": "open", "merged": False,
                        "html_url": f"{BASE}/{OWNER}/{NAME}/pulls/{number}",
                        "head": {"ref": payload["head"], "sha": "0" * 40},
                        "base": {"ref": payload["base"], "repo": {"full_name": f"{OWNER}/{NAME}"}}}
                self.pulls[number] = pull
                return 201, pull
            state = query["state"][0]
            values = [item for item in self.pulls.values() if state in {"all", item["state"]}]
            return 200, values if page == 1 else []
        if match := re.fullmatch(r"pulls/(\d+)", rest):
            return 200, self.pulls[int(match.group(1))]
        if match := re.fullmatch(r"commits/([0-9a-f]{40})/status", rest):
            return 200, {"state": "success", "sha": match.group(1), "statuses": []}
        if rest.startswith("actions/runs") and "jobs" not in rest:
            return 200, {"workflow_runs": [], "total_count": 0}
        if match := re.fullmatch(r"actions/jobs/(\d+)/logs", rest):
            return 200, b"log line\n"
        return 404, {}
