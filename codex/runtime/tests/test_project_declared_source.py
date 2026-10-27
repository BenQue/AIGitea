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
    AGENT, BASE, BRANCH, LABELS, REMOTE_URL, ROOT, SENTINEL, SESSION, FakeGitea, build_project,
    declaration, git, remote_runner, write_declaration,
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
        listed = broker.execute(None, "gitea.pulls.read", state="open")
        self.assertEqual([item["number"] for item in listed], [created["number"]])

    def test_git_credential_reaches_git_only_through_the_injected_helper(self) -> None:
        broker = self.broker()
        broker.execute(None, "git.push.change", branch=BRANCH)
        for argv, env in self.commands:
            self.assertNotIn(SENTINEL, " ".join(argv))
            self.assertFalse(any(SENTINEL in value for value in env.values()))
            self.assertFalse(any(key.startswith("GIT_TRACE") for key in env))
        helpers = {value for _argv, env in self.commands for value in env.values()
                   if value.startswith("!f() {")}
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

    def test_template_owning_changes_need_the_site_source(self) -> None:
        self.assertRefused("SCOPE_DENIED",
                           lambda: self.broker()._template_context(self.broker().contract.projects[0]))

    def _remote_branch(self) -> str:
        result = subprocess.run(["git", "rev-parse", "--verify", "-q", BRANCH], cwd=self.remote,
                                text=True, stdout=subprocess.PIPE, check=False)
        return result.stdout.strip()


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
