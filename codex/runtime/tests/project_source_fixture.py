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


def build_project(temporary: str, *, remote_url: str = REMOTE_URL, with_declaration: bool = True,
                  remote_path: Path | None = None, documents=None, prepare_main=None):
    """Canonical checkout, linked change worktree with an approved git_scope, bare remote."""
    remote = remote_path or Path(temporary) / "remote.git"
    canonical = Path(temporary) / "canonical"
    linked = Path(temporary) / "linked"
    git(["init", "-q", "--bare", "-b", "main", str(remote)])
    git(["init", "-q", "-b", "main", str(canonical)])
    git(["config", "user.name", "Project Source Test"], cwd=canonical)
    git(["config", "user.email", "project-source@example.invalid"], cwd=canonical)
    (canonical / "README.md").write_text("baseline\n")
    (canonical / ".gitignore").write_text(".superpowers/\n")
    if with_declaration:
        write_declaration(canonical)
    git(["add", "-A"], cwd=canonical)
    git(["commit", "-q", "-m", "baseline"], cwd=canonical)
    if prepare_main is not None:
        prepare_main(canonical)
        git(["add", "-A"], cwd=canonical)
        git(["commit", "-q", "-m", "adopt the usage bundle"], cwd=canonical)
    git(["remote", "add", "origin", remote_url], cwd=canonical)
    git(["push", "-q", str(remote), "refs/heads/main:refs/heads/main"], cwd=canonical)
    git(["update-ref", "refs/remotes/origin/main", "HEAD"], cwd=canonical)
    git(["worktree", "add", "-q", "-b", BRANCH, str(linked)], cwd=canonical)
    (linked / "change.txt").write_text("change 7\n")
    directory = linked / "docs/changes/7-demo-change"
    directory.mkdir(parents=True)
    if documents is not None:
        documents(directory)
    else:
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

    def __init__(self, *, user=None, permissions=None, base=BASE, remote: Path | None = None):
        self.base = base
        # With a bare remote, PR heads and commit statuses follow its real tips.
        self.remote = remote
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

    def _tips(self) -> set[str]:
        lines = git(["for-each-ref", "--format=%(objectname)", "refs/heads"], cwd=self.remote)
        return set(lines.split())

    def _id(self) -> int:
        self._next += 1
        return self._next

    def add_issue(self, number: int, title: str = "demo", labels=()) -> None:
        self.issues[number] = {
            "number": number, "title": title, "body": "AC", "state": "open",
            "created_at": "2026-10-27T00:00:00Z", "updated_at": "2026-10-27T00:00:00Z",
            "labels": [self._label(name) for name in labels], "pull_request": None,
            "html_url": f"{self.base}/{OWNER}/{NAME}/issues/{number}",
            "repository": {"name": NAME, "owner": OWNER, "full_name": f"{OWNER}/{NAME}"},
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
                        "html_url": f"{self.base}/{OWNER}/{NAME}/pulls/{number}",
                        "head": {"ref": payload["head"], "sha": "0" * 40},
                        "base": {"ref": payload["base"], "repo": {"full_name": f"{OWNER}/{NAME}"}}}
                self.pulls[number] = pull
                return 201, pull
            state = query["state"][0]
            values = [item for item in self.pulls.values() if state in {"all", item["state"]}]
            return 200, values if page == 1 else []
        if match := re.fullmatch(r"pulls/(\d+)", rest):
            pull = self.pulls[int(match.group(1))]
            if self.remote is not None:
                pull["head"]["sha"] = git(["rev-parse", pull["head"]["ref"]], cwd=self.remote)
            return 200, pull
        if match := re.fullmatch(r"commits/([0-9a-f]{40})/status", rest):
            if self.remote is not None and match.group(1) not in self._tips():
                return 404, {}
            return 200, {"state": "success", "sha": match.group(1), "statuses": []}
        if rest.startswith("actions/runs") and "jobs" not in rest:
            return 200, {"workflow_runs": [], "total_count": 0}
        if match := re.fullmatch(r"actions/jobs/(\d+)/logs", rest):
            return 200, b"log line\n"
        return 404, {}


class GiteaServer:
    """FakeGitea plus smart-HTTP Git (git http-backend) on 127.0.0.1.

    Both halves insist on the project credential: the REST half on the token
    header, the Git half on Basic auth, so a passing run proves the credential
    actually reached each of them through the engine.
    """

    def __init__(self, temporary: str, gitea: FakeGitea) -> None:
        import http.server
        import threading

        self.gitea = gitea
        self.project_root = Path(temporary) / "git-root"
        (self.project_root / OWNER).mkdir(parents=True)
        self.git_auth: list[str] = []
        server = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def _body(self) -> bytes:
                length = int(self.headers.get("Content-Length") or 0)
                return self.rfile.read(length) if length else b""

            def _git(self, method: str) -> None:
                import base64
                expected = "Basic " + base64.b64encode(f"{AGENT}:{SENTINEL}".encode()).decode()
                auth = self.headers.get("Authorization", "")
                server.git_auth.append("ok" if auth == expected else ("other" if auth else "none"))
                if auth != expected:
                    self.send_response(401)
                    self.send_header("WWW-Authenticate", 'Basic realm="git"')
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                path, _, query = self.path.partition("?")
                env = {"GIT_PROJECT_ROOT": str(server.project_root), "GIT_HTTP_EXPORT_ALL": "1",
                       "PATH_INFO": path, "QUERY_STRING": query, "REQUEST_METHOD": method,
                       "CONTENT_TYPE": self.headers.get("Content-Type", ""), "REMOTE_USER": AGENT,
                       "REMOTE_ADDR": "127.0.0.1", "PATH": "/usr/bin:/bin",
                       "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.receivepack",
                       "GIT_CONFIG_VALUE_0": "true"}
                body = self._body()
                if self.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    body = gzip.decompress(body)
                result = subprocess.run(["git", "http-backend"], input=body, env=env,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                head, _, payload = result.stdout.partition(b"\r\n\r\n")
                status = 200
                headers = []
                for line in head.decode("latin-1").split("\r\n"):
                    key, _, value = line.partition(":")
                    if key.lower() == "status":
                        status = int(value.strip().split()[0])
                    elif key:
                        headers.append((key, value.strip()))
                self.send_response(status)
                for key, value in headers:
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def _api(self, method: str) -> None:
                body = self._body() or None
                if self.headers.get("Authorization") != f"token {SENTINEL}":
                    status, headers, payload = 401, (), b"{}"
                else:
                    url = f"{BASE}{self.path}"
                    status, headers, payload = server.gitea(method, url, dict(self.headers), body)
                self.send_response(status)
                for key, value in headers:
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def _dispatch(self, method: str) -> None:
                if self.path.startswith(f"/{OWNER}/{NAME}.git/"):
                    self._git(method)
                else:
                    self._api(method)

            def do_GET(self):
                self._dispatch("GET")

            def do_POST(self):
                self._dispatch("POST")

            def do_PUT(self):
                self._dispatch("PUT")

            def do_PATCH(self):
                self._dispatch("PATCH")

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


TEMPLATES = ROOT / "templates/docs/changes/_template"


def export_tool_kit(checkout: Path) -> None:
    """Adopt the latest usage bundle release into a clean checkout, as a maintainer would."""
    subprocess.run(["bash", str(ROOT / "codex/tools/usage-bundle.sh"), "--adopt", str(checkout),
                    "--tools", "claude"], check=True, text=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def contract_documents(issue_url: str, *, verification: bool = False, development: bool = False):
    """Full complex change documents for Issue 7, built from the shipped templates.

    development=True is the change_control: development shape: summary only, the
    git_scope on the summary, and the R2 route card.
    """
    slug, date = "demo-change", "261027"
    if development:
        roles: tuple[str, ...] = ("summary",)
    else:
        roles = ("summary", "spec", "plan", "verification") if verification else ("summary", "spec", "plan")
    names = {role: f"{role}-{slug}-{date}.md" for role in roles}
    scope = ["change.txt", *(f"docs/changes/7-demo-change/{name}" for name in names.values())]
    values = {
        "ISSUE_NUMBER": "7", "ISSUE_URL": issue_url, "CHANGE_TYPE": "refactor",
        "ASSESSED_COMPLEXITY": "complex", "EFFECTIVE_COMPLEXITY": "complex",
        "CONTRACT_EFFECT": "change", "CLASSIFICATION_REASON": "synthetic project source fixture",
        "CONFIDENCE": "high", "ROUTE_PROVIDER": "claude", "ROUTE_PROCESS": "complex-production",
        "ROUTE_TIER": "frontier", "ROUTE_EFFORT": "high",
        "ROUTE_SKILLS": ("verification-before-completion" if development
                         else "to-spec, to-tickets, executing-plans, verification-before-completion"),
        "ROUTE_METHOD": "tdd" if development else "spec-plan", "ROUTE_VERIFY": "full+verification" if verification else "full",
        "ROUTE_REVIEW": "human-merge",
        "SHORT-SLUG": slug, "YYYY-MM-DD": "2026-10-27", "YYMMDD": date,
    }

    def fill(text: str) -> str:
        for key, value in values.items():
            text = text.replace(key, value)
        return text

    def write(directory: Path) -> None:
        summary = fill((TEMPLATES / "summary.md").read_text(encoding="utf-8"))
        summary = summary.replace("status: analyzed", "status: approved")
        summary = summary.replace(
            "required_docs:\n  - summary\ndocuments:\n  summary: summary-demo-change-261027.md\n",
            "required_docs:\n" + "".join(f"  - {role}\n" for role in roles) + "documents:\n"
            + "".join(f"  {role}: {name}\n" for role, name in names.items()))
        summary = summary.replace("required_docs:\n  - summary\nconfidence",
                                  "required_docs:\n" + "".join(f"  - {role}\n" for role in roles)
                                  + "confidence")
        summary = summary.replace("- CLASSIFICATION_EVIDENCE", "- synthetic")
        if development:
            summary = summary.replace("process: complex-production", "process: complex-development")
            summary = summary.replace("depends_on: []\n", "depends_on: []\ngit_scope:\n"
                                      + "".join(f"  - {path}\n" for path in scope), 1)
            (directory / names["summary"]).write_text(summary, encoding="utf-8")
            return
        (directory / names["summary"]).write_text(summary, encoding="utf-8")
        spec = fill((TEMPLATES / "spec.md").read_text(encoding="utf-8"))
        spec = spec.replace("depends_on: []\n", "depends_on: []\ngit_scope:\n"
                            + "".join(f"  - {path}\n" for path in scope), 1)
        (directory / names["spec"]).write_text(spec, encoding="utf-8")
        (directory / names["plan"]).write_text(fill((TEMPLATES / "plan.md").read_text(encoding="utf-8")),
                                               encoding="utf-8")
        if verification:
            (directory / names["verification"]).write_text(
                fill((TEMPLATES / "verification.md").read_text(encoding="utf-8")), encoding="utf-8")
    return write, names
