"""Project-declared source of the typed access engine (#434, ADR 0003)."""
from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from aisoft_host_access.broker import BrokerError, HostAccessBroker
from aisoft_host_access.contract import EXPECTED_OPERATIONS
from aisoft_host_access import project_source
from aisoft_host_access.project_source import (
    PROJECT_OPERATIONS, ProjectCredentials, ProjectSourceBroker, load_project_declaration,
)
from aisoft_worktree_owner import SESSION_ENV

from tests.project_source_fixture import (
    AGENT, BASE, BRANCH, LABELS, NAME, REMOTE_URL, ROOT, SENTINEL, SESSION, TEMPLATE_PATHS,
    FakeGitea, build_project, declaration, git, remote_runner, template_documents, template_main,
    write_declaration,
)


def static_fill(token=SENTINEL, username=AGENT):
    calls = []

    def fill(_declaration):
        calls.append(1)
        return username, token
    fill.calls = calls
    return fill


class ProjectSourceCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.remote, self.canonical, self.linked = build_project(self.temporary.name)
        session = patch.dict(os.environ, {SESSION_ENV: SESSION})
        session.start()
        self.addCleanup(session.stop)
        self.gitea = FakeGitea()
        self.gitea.provision()
        self.gitea.add_issue(7, "demo change", labels=("needs-analysis",))
        self.commands: list = []

    def broker(self, *, fill=None, gitea=None, cwd=None):
        declared = load_project_declaration(str(cwd or self.linked))
        return ProjectSourceBroker(
            declared, credentials=ProjectCredentials(declared, fill=fill or static_fill()),
            transport=gitea or self.gitea, runner=remote_runner(self.remote, self.commands),
            label_manifest_path=str(LABELS), invocation_cwd=str(cwd or self.linked),
        )

    def assertRefused(self, code, call):
        with self.assertRaises(BrokerError) as caught:
            call()
        self.assertEqual(caught.exception.code, code, str(caught.exception))
        return caught.exception


class DeclarationTest(ProjectSourceCase):
    def test_valid_declaration_derives_the_project_context(self) -> None:
        declared = load_project_declaration(str(self.linked))
        self.assertEqual((declared.owner, declared.repository, declared.base_url),
                         ("acme", "widget", BASE))
        self.assertEqual(declared.canonical, os.path.realpath(self.canonical))
        self.assertEqual(declared.change_control, "production")
        self.assertEqual(declared.git_remote_name, "origin")

    def test_schema_is_an_exact_key_set_with_closed_values(self) -> None:
        cases = {
            "unknown key": {"extra": 1},
            "missing key": {"protection_evidence": None},
            "repository": {"repository": "acme"},
            "lifecycle": {"deployment_lifecycle": "sometimes"},
            "change control": {"change_control": "staging"},
            "classification": {"classification": "secret"},
            "contexts": {"status_check_contexts": []},
            "duplicate contexts": {"status_check_contexts": ["a", "a"]},
            "evidence": {"protection_evidence": 0},
            "boolean evidence": {"protection_evidence": True},
            "schema": {"schema_version": 2},
            "agent": {"project_agent": "not a login"},
        }
        for label, override in cases.items():
            with self.subTest(label):
                write_declaration(self.linked, **override)
                self.assertRefused("PROJECT_DECLARATION_INVALID",
                                   lambda: load_project_declaration(str(self.linked)))

    def test_missing_declaration_is_refused(self) -> None:
        (self.linked / ".aisoft/project.json").unlink()
        self.assertRefused("PROJECT_DECLARATION_INVALID",
                           lambda: load_project_declaration(str(self.linked)))

    def test_remote_must_be_one_plain_http_url_for_the_declared_repository(self) -> None:
        cases = {
            "userinfo": ["remote", "set-url", "origin", f"http://u:p@gitea.test:3000/acme/widget.git"],
            "ssh": ["remote", "set-url", "origin", "git@gitea.test:acme/widget.git"],
            "other repository": ["remote", "set-url", "origin", f"{BASE}/acme/other.git"],
            "subpath": ["remote", "set-url", "origin", f"{BASE}/git/acme/widget.git"],
            "split push": ["remote", "set-url", "--push", "origin", f"{BASE}/acme/widget-fork.git"],
            "second url": ["remote", "set-url", "--add", "origin", f"{BASE}/acme/widget.git"],
            "insteadOf": ["config", f"url.{BASE}/elsewhere/.insteadOf", f"{BASE}/acme/"],
        }
        for label, command in cases.items():
            with self.subTest(label):
                git(command, cwd=self.canonical)
                self.assertRefused("TARGET_MISMATCH",
                                   lambda: load_project_declaration(str(self.linked)))
                subprocess.run(["git", "config", "--unset-all", "remote.origin.pushurl"],
                               cwd=self.canonical, check=False)
                subprocess.run(["git", "config", "--remove-section", f"url.{BASE}/elsewhere/"],
                               cwd=self.canonical, check=False, stderr=subprocess.DEVNULL)
                git(["config", "--replace-all", "remote.origin.url", REMOTE_URL], cwd=self.canonical)
        load_project_declaration(str(self.linked))


class SchemaDocumentTest(unittest.TestCase):
    def test_schema_and_template_match_the_loader(self) -> None:
        from aisoft_gitea_governance.contract import CHANGE_CONTROL_PHASES, DEPLOYMENT_LIFECYCLES
        schema = json.loads((ROOT / "codex/config/project-declaration.schema.json").read_text())
        self.assertEqual(set(schema["required"]), set(project_source.REQUIRED_KEYS))
        self.assertEqual(set(schema["properties"]),
                         set(project_source.REQUIRED_KEYS | project_source.OPTIONAL_KEYS))
        properties = schema["properties"]
        self.assertEqual(set(properties["deployment_lifecycle"]["enum"]), set(DEPLOYMENT_LIFECYCLES))
        self.assertEqual(set(properties["change_control"]["enum"]), set(CHANGE_CONTROL_PHASES))
        self.assertEqual(set(properties["classification"]["enum"]), set(project_source.CLASSIFICATIONS))
        template = json.loads((ROOT / "templates/project/aisoft-project.json").read_text())
        self.assertEqual(set(template), set(properties))


class ClosedSetTest(ProjectSourceCase):
    def test_closed_set_comes_from_the_site_operation_table(self) -> None:
        for name in PROJECT_OPERATIONS:
            with self.subTest(name):
                self.assertEqual(EXPECTED_OPERATIONS[name][0], "project-agent")
        self.assertEqual(len(set(PROJECT_OPERATIONS)), len(PROJECT_OPERATIONS))

    def test_maintenance_operations_are_refused_before_any_credential(self) -> None:
        fill = static_fill()
        broker = self.broker(fill=fill)
        for name in sorted(set(EXPECTED_OPERATIONS) - set(PROJECT_OPERATIONS)):
            with self.subTest(name):
                self.assertRefused("REQUEST_DENIED", lambda: broker.execute(None, name))
        for name in ("gitea.protection.read", "host.access.audit", "mac.git.bind",
                     "gitea.credential.rotate", "gitea.labels.extension.define",
                     "gitea.issue.labels.extension.set", "orbstack.vm.status"):
            self.assertNotIn(name, PROJECT_OPERATIONS)
        self.assertEqual(fill.calls, [])
        self.assertEqual(self.gitea.requests, [])


class ReviewFindingsTest(ProjectSourceCase):
    """Implementation cross-review findings (#434 round 1), each pinned here."""

    def test_pulls_read_is_outside_the_closed_set(self) -> None:
        self.assertNotIn("gitea.pulls.read", PROJECT_OPERATIONS)

    def test_injected_helper_refuses_any_other_target(self) -> None:
        broker = self.broker()
        credential = broker.credentials.resolve(broker.contract.projects[0],
                                                broker.contract.operation("git.push.change"))
        env = broker._git_credential_environment(credential)
        try:
            for request in ("protocol=http\nhost=evil.test:3000\npath=acme/widget.git\n\n",
                            "protocol=https\nhost=gitea.test:3000\npath=acme/widget.git\n\n",
                            "protocol=http\nhost=gitea.test:3000\npath=acme/other.git\n\n"):
                with self.subTest(request):
                    result = subprocess.run(["git", "credential", "fill"], cwd=self.linked, env=env,
                                            text=True, input=request, capture_output=True, check=False)
                    self.assertNotIn(SENTINEL, result.stdout)
            self.assertIn(("http.followRedirects", "false"), git_config_pairs(env))
        finally:
            broker._drop_credential_file()

    def test_helper_path_with_shell_metacharacters_stays_inert(self) -> None:
        marker = self.linked / "injected"
        hostile = Path(self.temporary.name) / "it's $(touch injected); `touch injected`"
        hostile.mkdir()
        broker = self.broker()
        credential = broker.credentials.resolve(broker.contract.projects[0],
                                                broker.contract.operation("git.push.change"))
        with patch.object(project_source.tempfile, "mkdtemp", lambda prefix: str(hostile)):
            env = broker._git_credential_environment(credential)
        try:
            result = subprocess.run(["git", "credential", "fill"], cwd=self.linked, env=env, text=True,
                                    input="protocol=http\nhost=gitea.test:3000\npath=acme/widget.git\n\n",
                                    capture_output=True, check=False)
            self.assertFalse(marker.exists())
            self.assertIn(f"password={SENTINEL}", result.stdout)
        finally:
            broker._drop_credential_file()

    def test_credential_fill_asks_for_the_exact_repository_path(self) -> None:
        record = Path(self.temporary.name) / "helper-request"
        git(["config", "credential.helper",
             f"!f() {{ cat > '{record}'; printf 'username={AGENT}\\npassword={SENTINEL}\\n'; }}; f"],
            cwd=self.canonical)
        username, token = project_source.credential_fill(load_project_declaration(str(self.linked)))
        self.assertEqual((username, token), (AGENT, SENTINEL))
        self.assertIn("path=acme/widget.git", record.read_text())

    def test_git_redirect_never_carries_the_credential(self) -> None:
        import http.server
        import threading
        seen: list[str] = []

        class Challenge(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def do_GET(self):
                seen.append(self.headers.get("Authorization", ""))
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="x"')
                self.send_header("Content-Length", "0")
                self.end_headers()

        target = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Challenge)
        port = target.server_address[1]

        class Redirect(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{port}{self.path}")
                self.send_header("Content-Length", "0")
                self.end_headers()

        origin = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
        for server in (target, origin):
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{origin.server_address[1]}/acme/widget.git"
        git(["remote", "set-url", "origin", url], cwd=self.canonical)
        declared = load_project_declaration(str(self.linked))
        broker = ProjectSourceBroker(declared, credentials=ProjectCredentials(declared, fill=static_fill()),
                                     transport=self.gitea_for(declared.base_url),
                                     label_manifest_path=str(LABELS), invocation_cwd=str(self.linked))
        with self.assertRaises(BrokerError):
            broker.execute(None, "git.fetch.main")
        self.assertFalse(any(value for value in seen), seen)

    def gitea_for(self, base):
        gitea = FakeGitea(base=base)

        def transport(method, url, headers, body, **options):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return gitea(method, "http://gitea.test:3000" + parsed.path, headers, body, **options)
        return transport

    def test_global_rewrite_of_the_declared_remote_is_refused(self) -> None:
        home = Path(self.temporary.name) / "home"
        home.mkdir()
        (home / ".gitconfig").write_text(f'[url "{BASE}/elsewhere/"]\n\tinsteadOf = {BASE}/acme/\n')
        with patch.dict(os.environ, {"HOME": str(home), "XDG_CONFIG_HOME": str(home)}):
            self.assertRefused("TARGET_MISMATCH", lambda: load_project_declaration(str(self.linked)))
        (home / ".gitconfig").write_text('[url "https://mirror.invalid/"]\n\tinsteadOf = https://github.com/\n')
        with patch.dict(os.environ, {"HOME": str(home), "XDG_CONFIG_HOME": str(home)}):
            load_project_declaration(str(self.linked))

    def test_url_specific_redirect_override_is_refused(self) -> None:
        git(["config", f"http.{BASE}/.followRedirects", "true"], cwd=self.canonical)
        self.assertRefused("TARGET_MISMATCH", lambda: load_project_declaration(str(self.linked)))

    def test_entry_refuses_abbreviated_internal_options(self) -> None:
        entry = ROOT / "codex/tools/aisoft-access"
        result = subprocess.run([str(entry), "--label-m", "/tmp/other.json", "--operation",
                                 "gitea.labels.read"], cwd=self.linked, text=True,
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("unrecognized arguments", result.stderr)


def git_config_pairs(env):
    count = int(env.get("GIT_CONFIG_COUNT", "0"))
    return [(env[f"GIT_CONFIG_KEY_{i}"], env[f"GIT_CONFIG_VALUE_{i}"]) for i in range(count)]


class IdentityTest(ProjectSourceCase):
    def test_identity_is_read_back_before_any_request(self) -> None:
        cases = {
            "site admin": FakeGitea(user={"login": AGENT, "is_admin": True}),
            "admin missing": FakeGitea(user={"login": AGENT}),
            "other login": FakeGitea(user={"login": "someone", "is_admin": False}),
            "repository admin": FakeGitea(permissions={"admin": True, "push": True}),
            "no push": FakeGitea(permissions={"admin": False, "push": False}),
            "permissions missing": FakeGitea(permissions={}),
            "admin is a string": FakeGitea(permissions={"admin": "false", "push": True}),
        }
        for label, gitea in cases.items():
            with self.subTest(label):
                gitea.add_issue(7)
                self.assertRefused("IDENTITY_MISMATCH", lambda: self.broker(gitea=gitea).execute(
                    None, "gitea.issue.read", number=7))
                touched = {urlpath(url) for _method, url, _h, _b in gitea.requests}
                self.assertNotIn("/api/v1/repos/acme/widget/issues/7", touched)

    def test_helper_returning_another_username_is_refused(self) -> None:
        self.assertRefused("IDENTITY_MISMATCH", lambda: self.broker(
            fill=static_fill(username="someone")).execute(None, "gitea.issue.read", number=7))

    def test_invalid_or_empty_token_is_refused(self) -> None:
        for token in ("", "has space", "x" * 5000):
            with self.subTest(len(token)):
                self.assertRefused("CREDENTIAL_INVALID", lambda: self.broker(
                    fill=static_fill(token=token)).execute(None, "gitea.issue.read", number=7))

    def test_redirects_are_never_followed(self) -> None:
        self.broker().execute(None, "gitea.issue.read", number=7)
        self.assertTrue(self.gitea.options)
        self.assertTrue(all(options.get("follow_redirects") is False for options in self.gitea.options))

    def test_credential_is_fetched_once_per_invocation(self) -> None:
        fill = static_fill()
        broker = self.broker(fill=fill)
        broker.execute(None, "gitea.issue.read", number=7)
        broker.execute(None, "gitea.issue.labels.read", number=7)
        self.assertEqual(fill.calls, [1])


def urlpath(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).path


class OperationsTest(ProjectSourceCase):
    """Every row of the spec D6 table succeeds through the project source."""

    def test_gitea_operations_succeed_with_the_project_credential(self) -> None:
        broker = self.broker()
        calls = [
            ("gitea.repo.read", {}),
            ("gitea.labels.provision", {}),
            ("gitea.labels.read", {}),
            ("gitea.issue.create", {"title": "new", "body": "AC", "entry_label": "triage/needs-triage"}),
            ("gitea.issue.read", {"number": 7}),
            ("gitea.issue.list", {"state": "open"}),
            ("gitea.issue.update", {"number": 7, "title": "demo change", "body": "AC 2"}),
            ("gitea.issue.comment", {"number": 7, "comment": "noted"}),
            ("gitea.issue.comments.read", {"number": 7}),
            ("gitea.issue.labels.read", {"number": 7}),
            ("gitea.issue.labels.classify", {"number": 7, "change_type": "feature", "complexity": "complex"}),
            ("gitea.issue.labels.set", {"number": 7, "lifecycle": "approved"}),
            ("gitea.commit.status.read", {"sha": "a" * 40}),
            ("gitea.actions.run.read", {"sha": "a" * 40}),
            ("gitea.actions.job.logs.read", {"job": 3}),
        ]
        for name, arguments in calls:
            with self.subTest(name):
                broker.execute(None, name, **arguments)
        labels = {label["name"] for label in self.gitea.issues[7]["labels"]}
        self.assertTrue({"type/feature", "complexity/complex", "approved"} <= labels)
        self.assertNotIn("needs-analysis", labels)
        for _method, _url, headers, _body in self.gitea.requests:
            self.assertEqual(headers["Authorization"], f"token {SENTINEL}")

    def test_git_publication_and_pull_request_flow(self) -> None:
        broker = self.broker()
        fetched = broker.execute(None, "git.fetch.main")
        self.assertEqual(fetched["status"], "PASS")
        absent = broker.execute(None, "git.fetch.change", branch=BRANCH)
        self.assertIsNone(absent["remote_head"])
        pushed = broker.execute(None, "git.push.change", branch=BRANCH)
        self.assertEqual(pushed["code"], "PUBLISHED")
        head = git(["rev-parse", "HEAD"], cwd=self.linked)
        self.assertEqual(git(["rev-parse", BRANCH], cwd=self.remote), head)
        again = broker.execute(None, "git.fetch.change", branch=BRANCH)
        self.assertEqual(again["remote_head"], head)
        body = ("Closes #7\n\nSummary: docs/changes/7-demo-change/summary-demo-change-261027.md\n")
        created = broker.execute(None, "gitea.pull.create", issue=7, title="demo", body=body)
        self.assertEqual(created["head"]["ref"], BRANCH)
        same = broker.execute(None, "gitea.pull.create", issue=7, title="demo", body=body)
        self.assertEqual(same["number"], created["number"])
        self.assertEqual(broker.execute(None, "gitea.pull.read", number=created["number"])["number"],
                         created["number"])
        self.assertRefused("REQUEST_DENIED", lambda: broker.execute(None, "gitea.pulls.read", state="open"))

    def test_git_credential_reaches_git_only_through_the_injected_helper(self) -> None:
        broker = self.broker()
        broker.execute(None, "git.push.change", branch=BRANCH)
        for argv, env in self.commands:
            self.assertNotIn(SENTINEL, " ".join(argv))
            self.assertFalse(any(SENTINEL in value for value in env.values()))
            self.assertFalse(any(key.startswith("GIT_TRACE") for key in env))
        helpers = {value for _argv, env in self.commands for value in env.values()
                   if value.startswith("!") and "project_git_helper.py" in value}
        self.assertEqual(len(helpers), 1)
        self.assertIn("aisoft-access-", helpers.pop())
        leftovers = [path for path in Path(tempfile.gettempdir()).glob("aisoft-access-*")]
        self.assertEqual(leftovers, [])

    def test_injected_helper_answers_git_with_the_verified_credential(self) -> None:
        broker = self.broker()
        credential = broker.credentials.resolve(broker.contract.projects[0],
                                                broker.contract.operation("git.push.change"))
        env = broker._git_credential_environment(credential)
        try:
            result = subprocess.run(["git", "credential", "fill"], cwd=self.linked, env=env, text=True,
                                    input="protocol=http\nhost=gitea.test:3000\npath=acme/widget.git\n\n",
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.assertIn(f"password={SENTINEL}", result.stdout)
            self.assertIn(f"username={AGENT}", result.stdout)
            secret = Path(broker._credential_dir) / "credential"
            self.assertEqual(secret.stat().st_mode & 0o777, 0o600)
            self.assertEqual(Path(broker._credential_dir).stat().st_mode & 0o777, 0o700)
        finally:
            directory = broker._credential_dir
            broker._drop_credential_file()
        self.assertFalse(Path(directory).exists())

    def test_push_refusals_still_apply(self) -> None:
        broker = self.broker()
        self.assertRefused("ARGUMENT_MISMATCH", lambda: broker.execute(None, "git.push.change"))
        self.assertRefused("REQUEST_DENIED", lambda: broker.execute(None, "git.push.change", branch="main"))
        self.assertRefused("TARGET_MISMATCH", lambda: broker.execute(None, "git.push.change",
                                                                    branch="change/8-other-change"))
        (self.linked / "dirty.txt").write_text("dirty\n")
        self.assertRefused("WORKTREE_DIRTY", lambda: broker.execute(None, "git.push.change", branch=BRANCH))
        (self.linked / "dirty.txt").unlink()
        (self.linked / "outside.txt").write_text("outside scope\n")
        git(["add", "outside.txt"], cwd=self.linked)
        git(["commit", "-q", "-m", "#7 T01: outside scope"], cwd=self.linked)
        error = self.assertRefused("SCOPE_DENIED", lambda: broker.execute(None, "git.push.change",
                                                                         branch=BRANCH))
        self.assertNotIn(SENTINEL, str(error))
        self.assertEqual(self._remote_branch(), "")

    def test_wrong_session_cannot_push(self) -> None:
        with patch.dict(os.environ, {SESSION_ENV: "another-session"}):
            self.assertRefused("WORKTREE_OWNER_MISMATCH", lambda: self.broker().execute(
                None, "git.push.change", branch=BRANCH))

    def test_pull_body_contract_still_applies(self) -> None:
        self.assertRefused("ARGUMENT_INVALID", lambda: self.broker().execute(
            None, "gitea.pull.create", issue=7, title="demo", body="no closing line"))

    def test_template_context_needs_a_verified_git_operation(self) -> None:
        # #445: outside a credential-verified Git operation there is no fresh
        # main to bind, so no template context exists at all.
        self.assertRefused("SCOPE_DENIED",
                           lambda: self.broker()._template_context(self.broker().contract.projects[0]))

    def _remote_branch(self) -> str:
        result = subprocess.run(["git", "rev-parse", "--verify", "-q", BRANCH], cwd=self.remote,
                                text=True, stdout=subprocess.PIPE, check=False)
        return result.stdout.strip()


class ProjectTemplateScopeTest(unittest.TestCase):
    """#445: the project source updates only templates already canonical on fresh main."""

    SUMMARY, SPEC = TEMPLATE_PATHS[0], TEMPLATE_PATHS[1]

    def build(self, selected=(TEMPLATE_PATHS[0], TEMPLATE_PATHS[1]), *, main_roles=None,
              changed=None, issue_url=None, prepare_main=None) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        session = patch.dict(os.environ, {SESSION_ENV: SESSION})
        session.start()
        self.addCleanup(session.stop)
        options = {} if issue_url is None else {"issue_url": issue_url}
        prepare = prepare_main or (template_main() if main_roles is None else template_main(main_roles))
        self.remote, self.canonical, self.linked = build_project(
            self.temporary.name, prepare_main=prepare,
            documents=template_documents(selected, changed=changed, **options))
        self.commands: list = []
        self.gitea = FakeGitea()

    def broker(self, runner=None):
        declared = load_project_declaration(str(self.linked))
        return ProjectSourceBroker(
            declared, credentials=ProjectCredentials(declared, fill=static_fill()), transport=self.gitea,
            runner=runner or remote_runner(self.remote, self.commands),
            label_manifest_path=str(LABELS), invocation_cwd=str(self.linked))

    def push(self, runner=None):
        return self.broker(runner).execute(None, "git.push.change", branch=BRANCH)

    def refused(self, code, runner=None) -> BrokerError:
        with self.assertRaises(BrokerError) as caught:
            self.push(runner)
        self.assertEqual(caught.exception.code, code, str(caught.exception))
        self.assertNotIn(SENTINEL, str(caught.exception))
        return caught.exception

    def remote_branch(self) -> str:
        return subprocess.run(["git", "rev-parse", "--verify", "-q", BRANCH], cwd=self.remote,
                              text=True, stdout=subprocess.PIPE, check=False).stdout.strip()

    def commit(self, message: str) -> None:
        git(["add", "-A"], cwd=self.linked)
        git(["commit", "-q", "-m", message], cwd=self.linked)

    def advance_main(self) -> None:
        (self.canonical / "main.txt").write_text("moved\n")
        git(["add", "main.txt"], cwd=self.canonical)
        git(["commit", "-q", "-m", "main moved"], cwd=self.canonical)
        git(["push", "-q", str(self.remote), "HEAD:refs/heads/main"], cwd=self.canonical)

    def moving_runner(self, *, after_main_reads: int):
        """Move remote main once the engine has read it `after_main_reads` times."""
        inner = remote_runner(self.remote, self.commands)
        reads = []

        def runner(argv, *, cwd=None, env=None):
            result = inner(argv, cwd=cwd, env=env)
            if list(argv[:2]) == ["git", "ls-remote"] and "refs/heads/main" in argv:
                reads.append(1)
                if len(reads) == after_main_reads:
                    self.advance_main()
            return result
        runner.reads = reads
        return runner

    # AC-1 -------------------------------------------------------------
    def test_declared_update_of_existing_templates_is_published(self) -> None:
        self.build()
        pushed = self.push()
        self.assertEqual(pushed["code"], "PUBLISHED")
        self.assertEqual(self.remote_branch(), git(["rev-parse", "HEAD"], cwd=self.linked))

    def test_partial_update_of_one_existing_template_is_published(self) -> None:
        self.build(selected=(self.SUMMARY,))
        self.assertEqual(self.push()["code"], "PUBLISHED")
        # A second, later update in the same scope publishes as an ordinary FF.
        path = self.linked / self.SUMMARY
        path.write_text(path.read_text() + "second\n")
        self.commit("#7 T02: second template update")
        self.assertEqual(self.push()["code"], "PUBLISHED")
        self.assertEqual(self.remote_branch(), git(["rev-parse", "HEAD"], cwd=self.linked))

    def test_site_manifests_are_never_read(self) -> None:
        self.build()
        with patch("aisoft_main_integration.template_scope_context",
                   side_effect=AssertionError("site template binding used")):
            self.assertEqual(self.push()["code"], "PUBLISHED")

    # AC-2 / AC-3 refusals ---------------------------------------------
    def test_first_time_add_is_refused_when_main_lacks_any_target(self) -> None:
        for roles in ((), ("spec",), ("summary", "plan")):
            with self.subTest(main_roles=roles):
                self.build(main_roles=roles)
                self.refused("SCOPE_DENIED")
                self.assertEqual(self.remote_branch(), "")

    def test_non_canonical_main_types_are_refused(self) -> None:
        def executable(canonical: Path) -> None:
            template_main()(canonical)
            (canonical / self.SUMMARY).chmod(0o755)

        def linked_file(canonical: Path) -> None:
            template_main(("spec", "plan", "verification"))(canonical)
            (canonical / self.SUMMARY).symlink_to("spec.md")

        def linked_parent(canonical: Path) -> None:
            real = canonical / "docs/real-template"
            real.mkdir(parents=True)
            for role in ("summary", "spec", "plan", "verification"):
                (real / f"{role}.md").write_text(role + "\n")
            (canonical / "docs/changes").mkdir(parents=True)
            (canonical / "docs/changes/_template").symlink_to("../real-template", target_is_directory=True)

        def file_parent(canonical: Path) -> None:
            (canonical / "docs/changes").mkdir(parents=True)
            (canonical / "docs/changes/_template").write_text("not a directory\n")

        for name, prepare in (("executable", executable), ("symlink", linked_file),
                              ("linked-parent", linked_parent), ("file-parent", file_parent)):
            with self.subTest(main=name):
                try:
                    self.build(selected=(self.SUMMARY,), prepare_main=prepare, changed=())
                except subprocess.CalledProcessError:
                    self.fail(f"fixture {name} could not be built")
                with self.assertRaises(BrokerError) as caught:
                    self.push()
                self.assertIn(caught.exception.code, {"SCOPE_DENIED", "GIT_OBJECT_DENIED"})
                self.assertEqual(self.remote_branch(), "")

    def test_main_baseline_type_is_checked_even_when_head_is_canonical(self) -> None:
        """Review R1 P2: HEAD repairs the type, so only the fresh-main check can refuse."""
        def executable(canonical: Path) -> None:
            template_main()(canonical)
            (canonical / self.SUMMARY).chmod(0o755)

        def linked_file(canonical: Path) -> None:
            template_main(("spec", "plan", "verification"))(canonical)
            (canonical / self.SUMMARY).symlink_to("spec.md")

        for name, prepare in (("executable", executable), ("symlink", linked_file)):
            with self.subTest(main=name):
                self.build(selected=(self.SUMMARY,), prepare_main=prepare, changed=())
                target = self.linked / self.SUMMARY
                target.unlink()
                target.write_text("canonical regular template\n")
                target.chmod(0o644)
                self.commit("#7 T02: repair template type")
                self.assertEqual(git(["ls-tree", "HEAD", "--", self.SUMMARY], cwd=self.linked).split()[0],
                                 "100644")
                error = self.refused("SCOPE_DENIED")
                self.assertIn("already canonical on fresh main", str(error))
                self.assertFalse(any(argv[:2] == ["git", "push"] for argv, _env in self.commands))
                self.assertEqual(self.remote_branch(), "")

    def test_history_paths_cannot_carry_a_template_outside_the_current_scope(self) -> None:
        """Review R1 P1: git_history_paths never widens the project-source template set."""
        self.build(selected=(self.SUMMARY,))
        anchor = git(["rev-parse", "HEAD"], cwd=self.linked)
        spec = self.linked / "docs/changes/7-demo-change/spec-demo-change-261027.md"
        text = spec.read_text()
        own = [line for line in text.split("git_scope:\n", 1)[1].split("---\n", 1)[0].splitlines()
               if self.SUMMARY not in line]
        spec.write_text(text.split("git_scope:\n", 1)[0] + f"git_history_head: {anchor}\n"
                        + "git_history_paths:\n" + text.split("git_scope:\n", 1)[1].split("---\n", 1)[0]
                        + "git_scope:\n" + "".join(line + "\n" for line in own) + "---\n")
        self.commit("#7 T02: move the template into history only")
        error = self.refused("SCOPE_DENIED")
        self.assertIn("outside the current exact scope", str(error))
        self.assertEqual(self.remote_branch(), "")

    def test_undeclared_template_change_is_refused(self) -> None:
        self.build(selected=(self.SUMMARY,), changed=(self.SUMMARY, self.SPEC))
        self.refused("SCOPE_DENIED")
        self.assertEqual(self.remote_branch(), "")

    def test_wrong_repository_binding_is_refused(self) -> None:
        for url in (f"{BASE}/other/{NAME}/issues/7", f"{BASE}/acme/other/issues/7",
                    f"{BASE}/acme/{NAME}/issues/8", "http://elsewhere.test:3000/acme/widget/issues/7"):
            with self.subTest(url=url):
                self.build(issue_url=url)
                self.refused("SCOPE_UNKNOWN")
                self.assertEqual(self.remote_branch(), "")

    def test_mid_history_delete_or_type_change_then_restore_is_refused(self) -> None:
        for kind in ("delete", "executable", "symlink"):
            with self.subTest(kind=kind):
                self.build(selected=(self.SUMMARY,))
                target = self.linked / self.SUMMARY
                original = target.read_bytes()
                target.unlink()
                if kind == "executable":
                    target.write_bytes(original)
                    target.chmod(0o755)
                elif kind == "symlink":
                    target.symlink_to("spec.md")
                self.commit("#7 T02: invalid template kind")
                if target.exists() or target.is_symlink():
                    target.unlink()
                target.write_bytes(original)
                self.commit("#7 T02: restore template")
                self.refused("SCOPE_DENIED")
                self.assertEqual(self.remote_branch(), "")

    def test_main_moving_before_transport_is_refused_without_a_write(self) -> None:
        # Reads: 1 engine baseline, 2 template baseline, 3+ template verify.
        for moment in (1, 2, 3):
            with self.subTest(after_main_reads=moment):
                self.build()
                runner = self.moving_runner(after_main_reads=moment)
                with self.assertRaises(BrokerError) as caught:
                    self.push(runner)
                self.assertIn(caught.exception.code, {"BASE_BRANCH_STALE", "GIT_OBJECT_DENIED"})
                self.assertNotIn("possible_write\":true", str(caught.exception))
                self.assertFalse(any(argv[:2] == ["git", "push"] for argv, _env in self.commands))
                self.assertEqual(self.remote_branch(), "")

    def test_main_moving_after_transport_reports_a_possible_write(self) -> None:
        self.build()
        probe = self.moving_runner(after_main_reads=10 ** 6)
        self.push(probe)
        total = len(probe.reads)
        # Rebuild and move main on the last read, the one after the transport.
        # The last two reads follow the transport: the engine's own post-push
        # main read, then the template baseline re-check. Either one reports
        # that the remote may already hold H and stops PR preparation.
        for moment, code in ((total - 2, "BASE_ADVANCED_AFTER_PUSH"), (total - 1, "BASE_BRANCH_STALE")):
            with self.subTest(after_main_reads=moment):
                self.build()
                error = self.refused(code, self.moving_runner(after_main_reads=moment))
                self.assertIn('"possible_write":true', str(error))
                self.assertIn('"write_status":"PUBLISHED"', str(error))
                self.assertEqual(self.remote_branch(), git(["rev-parse", "HEAD"], cwd=self.linked))

    def test_main_unreadable_for_the_template_baseline_is_refused(self) -> None:
        self.build()
        inner = remote_runner(self.remote, self.commands)
        reads = []

        def runner(argv, *, cwd=None, env=None):
            if list(argv[:2]) == ["git", "ls-remote"] and "refs/heads/main" in argv:
                reads.append(1)
                if len(reads) == 2:
                    return subprocess.CompletedProcess(argv, 128, "", "fatal: unreachable")
            return inner(argv, cwd=cwd, env=env)
        with self.assertRaises(BrokerError):
            self.push(runner)
        self.assertEqual(self.remote_branch(), "")


class SourceSelectionTest(ProjectSourceCase):
    def test_site_broker_ignores_a_project_declaration_in_the_checkout(self) -> None:
        from aisoft_host_access.contract import load_access_contract
        contract = load_access_contract(ROOT / "codex/tests/fixtures/manifests/host-access-broker.json",
                                        ROOT / "codex/tests/fixtures/manifests/gitea-governance.json")
        broker = HostAccessBroker(contract, credentials=object(), transport=self.gitea,
                                  invocation_cwd=str(self.linked))
        self.assertRefused("REQUEST_DENIED", lambda: broker.execute("widget", "gitea.issue.read", number=7))
        self.assertEqual(self.gitea.requests, [])

    def test_entry_refuses_project_and_requires_a_declaration(self) -> None:
        entry = ROOT / "codex/tools/aisoft-access"
        refused = subprocess.run([str(entry), "--project", "widget", "--operation", "git.fetch.main"],
                                 cwd=self.linked, text=True, capture_output=True, check=False)
        self.assertEqual(refused.returncode, 20)
        self.assertEqual(json.loads(refused.stderr)["code"], "ARGUMENT_MISMATCH")
        (self.linked / ".aisoft/project.json").unlink()
        missing = subprocess.run([str(entry), "--operation", "git.fetch.main"], cwd=self.linked,
                                 text=True, capture_output=True, check=False)
        self.assertEqual(missing.returncode, 20)
        self.assertEqual(json.loads(missing.stderr)["code"], "PROJECT_DECLARATION_INVALID")


if __name__ == "__main__":
    unittest.main()
