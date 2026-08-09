from __future__ import annotations

import io
import json
import os
import re
import stat
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from aisoft_host_access.broker import (
    BrokerError,
    CredentialResolver,
    HostAccessBroker,
    ResolvedCredential,
    _parse_credential_protocol,
    credential_from_protocol,
)
from aisoft_host_access.cli import main as host_access_cli_main
from aisoft_host_access.contract import AccessContractError, load_access_contract
from aisoft_host_access.profiles import ProfileMigrator
from aisoft_host_access.runner import GovernedHostRunner


ROOT = Path(__file__).resolve().parents[3]
ACCESS = ROOT / "codex/config/host-access-broker.json"
GOVERNANCE = ROOT / "codex/config/gitea-governance.json"


class StaticCredentials:
    def __init__(self, *, mismatch: bool = False) -> None:
        self.mismatch = mismatch

    def resolve(self, project, operation):
        if operation.identity_route in {"manager-audit", "manager-mutation"}:
            token = "token-manager" if operation.identity_route == "manager-audit" else "token-manager-mutation"
            return ResolvedCredential("aisoft-platform-manager", token)
        identity = "wrong-agent" if self.mismatch else project.project_agent
        return ResolvedCredential(identity, "token-agent")


class HostAccessContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_access_contract(ACCESS, GOVERNANCE)

    def test_exact_projects_profiles_and_no_merge_surface(self) -> None:
        self.assertEqual(len(self.contract.projects), 9)
        profiles = {
            item.repository: item.vm_profile.name
            for item in self.contract.projects
            if item.vm_profile is not None
        }
        self.assertEqual(profiles, {
            "HSDB": "hsdb",
            "NewEMaint": "emaintenance",
            "rsdesign-new": "rsdesign",
            "SFMDigitalBoard": "sfm",
        })
        names = {item.name for item in self.contract.operations}
        self.assertFalse(any("merge" in value or "shell" in value or "url" in value
                             for value in names))
        with self.assertRaises(AccessContractError):
            self.contract.operation("git.push.main")

    def test_governed_issue_and_pull_operations_have_exact_typed_fields(self) -> None:
        expected = {
            "gitea.issue.create": ("title", "body"),
            "gitea.issue.read": ("number",),
            "gitea.issue.update": ("number", "title", "body"),
            "gitea.issue.comment": ("number", "comment"),
            "gitea.pull.create": ("issue", "title", "body"),
            "gitea.pull.read": ("number",),
            "gitea.pull.update": ("number", "issue", "title", "body"),
            "gitea.commit.status.read": ("sha",),
        }
        for name, arguments in expected.items():
            with self.subTest(name=name):
                operation = self.contract.operation(name)
                self.assertEqual(operation.identity_route, "project-agent")
                self.assertEqual(operation.arguments, arguments)
        forbidden_words = ("merge", "url", "owner", "repository", "method", "path", "json")
        for operation in self.contract.operations:
            self.assertFalse(any(word in operation.name for word in forbidden_words))
            self.assertTrue(set(operation.arguments).isdisjoint(forbidden_words))
        audit = self.contract.operation("host.access.audit")
        self.assertEqual(audit.identity_route, "manager-audit")
        self.assertFalse(audit.mutating)
        self.assertEqual(audit.arguments, ())

    def test_identity_routes_are_least_privilege(self) -> None:
        project = self.contract.project("newemaint")
        self.assertEqual(
            self.contract.identity_for(project, self.contract.operation("gitea.repo.read")),
            "newemaint-agent",
        )
        self.assertEqual(
            self.contract.identity_for(project, self.contract.operation("gitea.protection.read")),
            "aisoft-platform-manager",
        )
        self.assertNotEqual(project.project_agent, self.contract.governance.human_merge_identity)

    def test_native_acl_helper_catalog_matches_manifest_projects_exactly(self) -> None:
        source = (
            ROOT / "codex/runtime/aisoft_host_access/keychain_acl_audit.c"
        ).read_text()
        pairs = set(re.findall(
            r'\{"([a-z0-9-]+)", "([a-z0-9-]+-agent)"\}', source
        ))
        self.assertEqual(pairs, {
            (project.project_id, project.project_agent)
            for project in self.contract.projects
        })
        self.assertNotIn('{"ci-bot",', source)

    def test_extra_key_and_project_agent_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "access.json"
            raw = json.loads(ACCESS.read_text())
            raw["unexpected"] = True
            path.write_text(json.dumps(raw))
            with self.assertRaises(AccessContractError):
                load_access_contract(path, GOVERNANCE)
            raw.pop("unexpected")
            raw["projects"][0]["project_agent"] = "hsdb-agent"
            path.write_text(json.dumps(raw))
            with self.assertRaises(AccessContractError):
                load_access_contract(path, GOVERNANCE)

    def test_unknown_project_operation_and_arbitrary_argument_are_denied(self) -> None:
        broker = HostAccessBroker(self.contract, credentials=StaticCredentials())
        with self.assertRaisesRegex(BrokerError, "explicitly managed"):
            broker.execute("unknown", "gitea.repo.read")
        with self.assertRaisesRegex(BrokerError, "allowlisted"):
            broker.execute("hsdb", "shell.run")
        with self.assertRaisesRegex(BrokerError, "arguments"):
            broker.execute("hsdb", "gitea.repo.read", state="all")


class HostAccessBrokerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_access_contract(ACCESS, GOVERNANCE)

    def transport(self, method, url, headers, body):
        self.assertEqual(method, "GET")
        self.assertIsNone(body)
        token = headers["Authorization"].removeprefix("token ")
        if url.endswith("/api/v1/user"):
            login = "aisoft-platform-manager" if token == "token-manager" else "hsdb-agent"
            return 200, {}, json.dumps({"login": login, "is_admin": False}).encode()
        if url.endswith("/branch_protections/main"):
            return 200, {}, b'{"branch_name":"main"}'
        return 200, {}, b'{"name":"HSDB"}'

    def test_project_and_manager_read_routes(self) -> None:
        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=self.transport,
        )
        self.assertEqual(broker.execute("hsdb", "gitea.repo.read")["name"], "HSDB")
        self.assertEqual(
            broker.execute("hsdb", "gitea.protection.read")["branch_name"], "main"
        )

    def test_commit_status_read_is_exact_sha_bound(self) -> None:
        calls = []

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            calls.append(url)
            return 200, {}, b'{"state":"success","statuses":[]}'

        broker = HostAccessBroker(
            self.contract, credentials=StaticCredentials(), transport=transport,
        )
        sha = "a" * 40
        value = broker.execute(
            "aisoft-platform", "gitea.commit.status.read", sha=sha
        )
        self.assertEqual(value["state"], "success")
        self.assertEqual(calls, [
            "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/commits/"
            + sha + "/status"
        ])
        for invalid in ("main", "a" * 39, "a" * 41, "g" * 40, "a" * 40 + "/status"):
            with self.subTest(invalid=invalid), self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "gitea.commit.status.read", sha=invalid
                )
            self.assertEqual(caught.exception.code, "ARGUMENT_INVALID")

    def test_issue_create_update_comment_and_read_use_fixed_typed_routes(self) -> None:
        calls = []

        def transport(method, url, headers, body):
            token = headers["Authorization"].removeprefix("token ")
            if url.endswith("/api/v1/user"):
                return 200, {}, json.dumps({
                    "login": "aisoft-platform-agent" if token == "token-agent" else "unexpected",
                    "is_admin": False,
                }).encode()
            calls.append((method, url, json.loads(body) if body else None))
            number = 70 if url.endswith("/issues") else 70
            return 200, {}, json.dumps({"number": number, "state": "open"}).encode()

        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
        )
        created = broker.execute(
            "aisoft-platform",
            "gitea.issue.create",
            title="governed canary",
            body="Issue body without raw HTTP fields",
        )
        updated = broker.execute(
            "aisoft-platform",
            "gitea.issue.update",
            number=70,
            title="governed canary updated",
            body="Updated body",
        )
        comment = broker.execute(
            "aisoft-platform",
            "gitea.issue.comment",
            number=70,
            comment="governed broker canary",
        )
        read_back = broker.execute("aisoft-platform", "gitea.issue.read", number=70)
        self.assertEqual(created["number"], 70)
        self.assertEqual(updated["number"], 70)
        self.assertEqual(comment["number"], 70)
        self.assertEqual(read_back["number"], 70)
        self.assertEqual(calls, [
            (
                "POST",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/issues",
                {"title": "governed canary", "body": "Issue body without raw HTTP fields"},
            ),
            (
                "PATCH",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/issues/70",
                {"title": "governed canary updated", "body": "Updated body"},
            ),
            (
                "POST",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/issues/70/comments",
                {"body": "governed broker canary"},
            ),
            (
                "GET",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/issues/70",
                None,
            ),
        ])

    def test_issue_typed_fields_reject_unsafe_or_oversized_text_before_credentials(self) -> None:
        class FailIfResolved:
            def resolve(self, project, operation):
                raise AssertionError("credential resolution must not run")

        broker = HostAccessBroker(self.contract, credentials=FailIfResolved())
        invalid = (
            {"title": "", "body": "valid"},
            {"title": "bad\rtitle", "body": "valid"},
            {"title": "valid", "body": "bad\x00body"},
            {"title": "x" * 256, "body": "valid"},
            {"title": "valid", "body": "x" * 65537},
        )
        for fields in invalid:
            with self.subTest(fields=fields), self.assertRaises(BrokerError) as caught:
                broker.execute("aisoft-platform", "gitea.issue.create", **fields)
            self.assertEqual(caught.exception.code, "ARGUMENT_INVALID")

    def test_pull_create_update_and_read_are_deduplicated_and_issue_bound(self) -> None:
        calls = []

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            payload = json.loads(body) if body else None
            calls.append((method, url, payload))
            if url.endswith("/pulls?state=open&limit=50&page=1"):
                return 200, {}, b'[]'
            return 200, {}, json.dumps({
                "number": 71,
                "head": {"ref": "change/70"},
                "base": {"ref": "main"},
                "merged": False,
            }).encode()

        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
        )
        body = "Closes #70\n\nContract: docs/changes/70/summary-governed-host-writes-260809.md"
        created = broker.execute(
            "aisoft-platform", "gitea.pull.create",
            issue=70, title="fix(host-access): governed writes", body=body,
        )
        updated = broker.execute(
            "aisoft-platform", "gitea.pull.update",
            number=71, issue=70, title="fix(host-access): governed writes", body=body,
        )
        read_back = broker.execute("aisoft-platform", "gitea.pull.read", number=71)
        self.assertEqual(created["number"], 71)
        self.assertEqual(updated["number"], 71)
        self.assertEqual(read_back["number"], 71)
        self.assertEqual(calls, [
            (
                "GET",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/pulls?state=open&limit=50&page=1",
                None,
            ),
            (
                "POST",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/pulls",
                {
                    "title": "fix(host-access): governed writes",
                    "body": body,
                    "head": "change/70",
                    "base": "main",
                },
            ),
            (
                "GET",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/pulls/71",
                None,
            ),
            (
                "PATCH",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/pulls/71",
                {"title": "fix(host-access): governed writes", "body": body},
            ),
            (
                "GET",
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform/pulls/71",
                None,
            ),
        ])

    def test_pull_create_returns_existing_unique_open_pr_without_posting(self) -> None:
        calls = []

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            calls.append(method)
            return 200, {}, json.dumps([{
                "number": 71,
                "head": {"ref": "change/70"},
                "base": {"ref": "main"},
                "merged": False,
            }]).encode()

        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
        )
        value = broker.execute(
            "aisoft-platform", "gitea.pull.create", issue=70,
            title="fix(host-access): governed writes",
            body="Closes #70\n\ndocs/changes/70/summary-governed-host-writes-260809.md",
        )
        self.assertEqual(value["number"], 71)
        self.assertEqual(calls, ["GET"])

    def test_pull_body_contract_is_rejected_before_credentials(self) -> None:
        class FailIfResolved:
            def resolve(self, project, operation):
                raise AssertionError("credential resolution must not run")

        broker = HostAccessBroker(self.contract, credentials=FailIfResolved())
        for body in (
            "docs/changes/70/summary-governed-host-writes-260809.md",
            "Closes #70",
            "Closes #71\ndocs/changes/70/summary-governed-host-writes-260809.md",
            "Closes #70\ndocs/changes/71/summary-wrong-change-260809.md",
        ):
            with self.subTest(body=body), self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "gitea.pull.create", issue=70,
                    title="governed write", body=body,
                )
            self.assertEqual(caught.exception.code, "ARGUMENT_INVALID")

    @staticmethod
    def _keychain_audit_payload(*, include_trusted_application: bool = True) -> str:
        application = ["/usr/bin/security"] if include_trusted_application else []
        return json.dumps({
            "status": "PASS",
            "items": [
                {
                    "route": route,
                    "service": service,
                    "account": account,
                    "item_class": "generic-password",
                    "permanence": "default-user-keychain",
                    "password_required": False,
                    "trusted_applications": application,
                }
                for route, service, account in (
                    ("manager_audit", "aisoft.gitea.manager-audit", "aisoft-platform-manager"),
                    ("manager_mutation", "aisoft.gitea.manager-mutation", "aisoft-platform-manager"),
                    ("project_agent", "aisoft.gitea.project-agent", "aisoft-platform-agent"),
                )
            ],
        })

    def test_access_audit_validates_fixed_identities_scopes_permissions_protection_and_acl(self) -> None:
        seen_commands = []

        def runner(argv, **kwargs):
            seen_commands.append(list(argv))
            if argv == [
                "/usr/local/libexec/aisoft/keychain-acl-audit",
                "--project", "aisoft-platform",
            ]:
                return subprocess.CompletedProcess(
                    argv, 0, self._keychain_audit_payload(), ""
                )
            raise AssertionError(f"unexpected command: {argv!r}")

        def transport(method, url, headers, body):
            self.assertEqual(method, "GET")
            self.assertIsNone(body)
            token = headers["Authorization"].removeprefix("token ")
            if url.endswith("/api/v1/user"):
                login = "aisoft-platform-manager" if token.startswith("token-manager") else "aisoft-platform-agent"
                return 200, {}, json.dumps({"login": login, "is_admin": False}).encode()
            if url.endswith("/api/v1/notifications"):
                scopes = {
                    "token-manager": "read:issue,read:repository,read:user",
                    "token-manager-mutation": "write:issue,write:repository,read:user",
                    "token-agent": "write:issue,write:repository,read:user",
                }[token]
                return 403, {}, json.dumps({
                    "message": "token does not have required scope, token scope=" + scopes,
                }).encode()
            if url.endswith("/collaborators/aisoft-platform-manager/permission"):
                return 200, {}, b'{"permission":"admin"}'
            if url.endswith("/collaborators/aisoft-platform-agent/permission"):
                return 200, {}, b'{"permission":"write"}'
            if url.endswith("/branch_protections/main"):
                return 200, {}, json.dumps({
                    "can_push": False,
                    "can_force_push": False,
                    "enable_merge_whitelist": True,
                    "merge_whitelist_usernames": ["admin"],
                    "enable_status_check": False,
                    "status_check_contexts": [],
                    "required_approvals": 0,
                    "block_admin_merge_override": True,
                }).encode()
            raise AssertionError(f"unexpected URL: {url}")

        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
            runner=runner,
        )
        value = broker.execute("aisoft-platform", "host.access.audit")
        self.assertEqual(value["status"], "PASS")
        self.assertEqual(value["repository_permission"], {
            "manager": "admin", "project_agent": "write",
        })
        self.assertEqual(value["token_scopes"], {
            "manager_audit": ["read:issue", "read:repository", "read:user"],
            "manager_mutation": ["read:user", "write:issue", "write:repository"],
            "project_agent": ["read:user", "write:issue", "write:repository"],
        })
        self.assertEqual(value["keychain"], {
            "manager_audit": {
                "account": "aisoft-platform-manager",
                "service": "aisoft.gitea.manager-audit",
                "item_class": "generic-password",
                "permanence": "default-user-keychain",
                "password_required": False,
                "trusted_applications": ["/usr/bin/security"],
            },
            "manager_mutation": {
                "account": "aisoft-platform-manager",
                "service": "aisoft.gitea.manager-mutation",
                "item_class": "generic-password",
                "permanence": "default-user-keychain",
                "password_required": False,
                "trusted_applications": ["/usr/bin/security"],
            },
            "project_agent": {
                "account": "aisoft-platform-agent",
                "service": "aisoft.gitea.project-agent",
                "item_class": "generic-password",
                "permanence": "default-user-keychain",
                "password_required": False,
                "trusted_applications": ["/usr/bin/security"],
            },
        })
        flattened = "\n".join(" ".join(argv) for argv in seen_commands)
        self.assertNotIn("ci-bot", flattened)
        self.assertNotIn(" -A", flattened)
        self.assertNotIn(" -g", flattened)
        self.assertNotIn(" -w", flattened)
        self.assertNotIn("dump-keychain", flattened)
        self.assertNotIn("find-generic-password", flattened)

    def test_access_audit_rejects_allow_any_or_missing_trusted_application_acl(self) -> None:
        def runner(argv, **kwargs):
            return subprocess.CompletedProcess(
                argv, 0,
                self._keychain_audit_payload(include_trusted_application=False), "",
            )

        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=lambda method, url, headers, body: (
                200, {}, b'{"login":"aisoft-platform-manager","is_admin":false}'
            ),
            runner=runner,
        )
        with self.assertRaises(BrokerError) as caught:
            broker.execute("aisoft-platform", "host.access.audit")
        self.assertEqual(caught.exception.code, "KEYCHAIN_ACL_INVALID")

    def test_identity_mismatch_fails_before_target_request(self) -> None:
        calls = []

        def transport(method, url, headers, body):
            calls.append(url)
            return 200, {}, b'{"login":"hsdb-agent","is_admin":false}'

        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(mismatch=True),
            transport=transport,
        )
        with self.assertRaisesRegex(BrokerError, "identity"):
            broker.execute("hsdb", "gitea.repo.read")
        self.assertEqual(len(calls), 1)

    def test_http_401_403_404_are_nonzero_sanitized_failures(self) -> None:
        secret = "SECRET_RESPONSE_BODY_MUST_NOT_LEAK"
        for status in (401, 403, 404):
            with self.subTest(status=status):
                calls = 0

                def transport(method, url, headers, body):
                    nonlocal calls
                    calls += 1
                    if calls == 1:
                        return 200, {}, b'{"login":"hsdb-agent","is_admin":false}'
                    return status, {}, secret.encode()

                broker = HostAccessBroker(
                    self.contract,
                    credentials=StaticCredentials(),
                    transport=transport,
                )
                with self.assertRaises(BrokerError) as caught:
                    broker.execute("hsdb", "gitea.repo.read")
                self.assertEqual(caught.exception.code, f"HTTP_{status}")
                self.assertNotIn(secret, str(caught.exception))
                self.assertNotIn("token-agent", str(caught.exception))

    def test_keychain_secret_is_not_in_command_argv(self) -> None:
        seen = []

        def runner(argv, **kwargs):
            seen.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, "sentinel-secret-token\n", "")

        resolver = CredentialResolver(self.contract, runner=runner)
        credential = resolver.resolve(
            self.contract.project("hsdb"), self.contract.operation("gitea.repo.read")
        )
        self.assertEqual(credential.identity, "hsdb-agent")
        self.assertEqual(credential.token, "sentinel-secret-token")
        self.assertFalse(any("sentinel-secret-token" in value for value in seen[0]))

    def _temporary_checkout_contract(self, checkout: Path):
        project = self.contract.project("aisoft-platform")
        replacement = replace(project, mac_checkout=str(checkout))
        projects = tuple(replacement if item.project_id == project.project_id else item
                         for item in self.contract.projects)
        return replace(self.contract, projects=projects)

    @staticmethod
    def _git(argv, *, cwd: Path | None = None) -> str:
        return subprocess.run(
            ["git", *argv], cwd=cwd, check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.strip()

    def _linked_change_worktree(self, temporary: str):
        canonical = Path(temporary) / "canonical"
        linked = Path(temporary) / "linked"
        self._git(["init", "-q", "-b", "main", str(canonical)])
        self._git(["config", "user.name", "Host Broker Test"], cwd=canonical)
        self._git(["config", "user.email", "host-broker@example.invalid"], cwd=canonical)
        (canonical / "README.md").write_text("baseline\n")
        self._git(["add", "README.md"], cwd=canonical)
        self._git(["commit", "-q", "-m", "baseline"], cwd=canonical)
        self._git([
            "remote", "add", "origin",
            "http://gitea-ci.orb.local:3000/admin/aisoft-platform.git",
        ], cwd=canonical)
        self._git(["update-ref", "refs/remotes/origin/main", "HEAD"], cwd=canonical)
        self._git(["worktree", "add", "-q", "-b", "change/70", str(linked)], cwd=canonical)
        (linked / "change.txt").write_text("change 70\n")
        self._git(["add", "change.txt"], cwd=linked)
        self._git(["commit", "-q", "-m", "change 70"], cwd=linked)
        return canonical, linked

    def test_repo_local_binding_is_idempotent_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "repo"
            subprocess.run(["git", "init", "-q", checkout], check=True)
            remote = "http://gitea-ci.orb.local:3000/admin/aisoft-platform.git"
            subprocess.run(["git", "-C", checkout, "remote", "add", "origin", remote], check=True)
            contract = self._temporary_checkout_contract(checkout)
            broker = HostAccessBroker(
                contract,
                credentials=StaticCredentials(),
                transport=lambda method, url, headers, body: (
                    200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
                ),
            )
            first = broker.execute("aisoft-platform", "mac.git.bind")
            second = broker.execute("aisoft-platform", "mac.git.bind")
            self.assertEqual(first["result"], "updated")
            self.assertEqual(second["result"], "no-op")
            config = subprocess.run(
                ["git", "-C", checkout, "config", "--local", "--list"],
                check=True, text=True, stdout=subprocess.PIPE,
            ).stdout
            self.assertIn("credential.usehttppath=true", config.lower())
            self.assertIn("aisoft-platform-agent", config)
            self.assertIn("git-credential-aisoft-host", config)
            helper_key = f"credential.{remote}.helper"
            helper_values = subprocess.run(
                ["git", "-C", checkout, "config", "--local", "--get-all", helper_key],
                check=True, text=True, stdout=subprocess.PIPE,
            ).stdout.splitlines()
            self.assertEqual(helper_values, ["", "/usr/local/libexec/aisoft/git-credential-aisoft-host"])
            self.assertNotIn("token", config.lower())
            self.assertNotIn("keychain", config.lower())

    def test_main_force_or_arbitrary_refspec_have_no_push_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "repo"
            subprocess.run(["git", "init", "-q", checkout], check=True)
            subprocess.run([
                "git", "-C", checkout, "remote", "add", "origin",
                "http://gitea-ci.orb.local:3000/admin/aisoft-platform.git",
            ], check=True)
            contract = self._temporary_checkout_contract(checkout)
            broker = HostAccessBroker(
                contract,
                credentials=StaticCredentials(),
                transport=lambda method, url, headers, body: (
                    200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
                ),
            )
            for branch in ("main", "change/1:main", "+change/1", "change/0"):
                with self.subTest(branch=branch), self.assertRaises(BrokerError):
                    broker.execute("aisoft-platform", "git.push.change", branch=branch)

    def test_push_uses_current_linked_worktree_and_exact_same_change_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            canonical, linked = self._linked_change_worktree(temporary)
            contract = self._temporary_checkout_contract(canonical)
            commands = []

            def runner(argv, *, cwd=None, env=None):
                commands.append((list(argv), cwd, dict(env or {})))
                if argv[:3] == ["git", "fetch", "origin"]:
                    return subprocess.CompletedProcess(argv, 0, "", "")
                if argv[:3] == ["git", "push", "origin"]:
                    return subprocess.CompletedProcess(argv, 0, "", "")
                return subprocess.run(
                    list(argv), cwd=cwd, env=env, check=False, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )

            broker = HostAccessBroker(
                contract,
                credentials=StaticCredentials(),
                transport=lambda method, url, headers, body: (
                    200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
                ),
                runner=runner,
                invocation_cwd=str(linked),
            )
            value = broker.execute(
                "aisoft-platform", "git.push.change", branch="change/70"
            )
            self.assertEqual(value["checkout"], os.path.realpath(linked))
            pushes = [call for call in commands if call[0][:2] == ["git", "push"]]
            self.assertEqual(len(pushes), 1)
            self.assertEqual(pushes[0][0], [
                "git", "push", "origin",
                "refs/heads/change/70:refs/heads/change/70",
            ])
            self.assertEqual(pushes[0][1], os.path.realpath(linked))
            flattened = "\n".join(" ".join(argv) for argv, _cwd, _env in commands)
            self.assertNotIn("--force", flattened)
            self.assertNotIn(":refs/heads/main", flattened)

    def test_push_rejects_wrong_common_dir_detached_dirty_and_wrong_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            canonical, linked = self._linked_change_worktree(temporary)
            contract = self._temporary_checkout_contract(canonical)

            def broker_for(cwd: Path):
                return HostAccessBroker(
                    contract,
                    credentials=StaticCredentials(),
                    transport=lambda method, url, headers, body: (
                        200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
                    ),
                    invocation_cwd=str(cwd),
                )

            other = Path(temporary) / "other"
            self._git(["init", "-q", "-b", "change/70", str(other)])
            self._git([
                "remote", "add", "origin",
                "http://gitea-ci.orb.local:3000/admin/aisoft-platform.git",
            ], cwd=other)
            with self.assertRaises(BrokerError) as wrong_repo:
                broker_for(other).execute(
                    "aisoft-platform", "git.push.change", branch="change/70"
                )
            self.assertEqual(wrong_repo.exception.code, "TARGET_MISMATCH")

            (linked / "dirty.txt").write_text("dirty\n")
            with self.assertRaises(BrokerError) as dirty:
                broker_for(linked).execute(
                    "aisoft-platform", "git.push.change", branch="change/70"
                )
            self.assertEqual(dirty.exception.code, "WORKTREE_DIRTY")
            (linked / "dirty.txt").unlink()

            self._git(["checkout", "--detach", "-q"], cwd=linked)
            with self.assertRaises(BrokerError) as detached:
                broker_for(linked).execute(
                    "aisoft-platform", "git.push.change", branch="change/70"
                )
            self.assertEqual(detached.exception.code, "TARGET_MISMATCH")

            self._git(["switch", "-q", "change/70"], cwd=linked)
            with self.assertRaises(BrokerError) as wrong_change:
                broker_for(linked).execute(
                    "aisoft-platform", "git.push.change", branch="change/71"
                )
            self.assertEqual(wrong_change.exception.code, "TARGET_MISMATCH")

    def test_credential_protocol_denies_cross_project_and_wrong_identity(self) -> None:
        resolver = StaticCredentials()
        with self.assertRaisesRegex(BrokerError, "exact managed target"):
            credential_from_protocol(
                self.contract,
                "get",
                "protocol=http\nhost=gitea-ci.orb.local:3000\npath=admin/unknown.git\n\n",
                resolver=resolver,
                identity_verifier=lambda credential: None,
            )
        with self.assertRaisesRegex(BrokerError, "username"):
            credential_from_protocol(
                self.contract,
                "get",
                "protocol=http\nhost=gitea-ci.orb.local:3000\npath=admin/HSDB.git\nusername=newemaint-agent\n\n",
                resolver=resolver,
                identity_verifier=lambda credential: None,
            )
        output = credential_from_protocol(
            self.contract,
            "get",
            "protocol=http\nhost=gitea-ci.orb.local:3000\npath=admin/HSDB.git\nusername=hsdb-agent\n\n",
            resolver=resolver,
            identity_verifier=lambda credential: None,
        )
        self.assertEqual(output, "username=hsdb-agent\npassword=token-agent\n")

    def test_credential_protocol_accepts_current_git_multivalue_shape(self) -> None:
        protocol_input = (
            ROOT / "codex/tests/fixtures/host-access/git-credential-get-current.txt"
        ).read_text() + "\n"
        request = _parse_credential_protocol(protocol_input)
        self.assertEqual(request.scalars, {
            "protocol": "http",
            "host": "gitea-ci.orb.local:3000",
            "path": "admin/aisoft-platform.git",
            "username": "aisoft-platform-agent",
        })
        self.assertEqual(
            request.multivalued["capability[]"],
            ("authtype", "state"),
        )
        self.assertEqual(
            request.multivalued["wwwauth[]"],
            ('Basic realm="sanitized-fixture"',),
        )
        output = credential_from_protocol(
            self.contract,
            "get",
            protocol_input,
            resolver=StaticCredentials(),
            identity_verifier=lambda credential: None,
        )
        self.assertEqual(
            output,
            "username=aisoft-platform-agent\npassword=token-agent\n",
        )

    def test_unknown_multivalued_attributes_are_ordered_and_ignored(self) -> None:
        protocol_input = (
            "future-capability[]=first\n"
            "future-capability[]=second\n"
            "protocol=http\n"
            "host=gitea-ci.orb.local:3000\n"
            "path=admin/HSDB.git\n"
            "username=hsdb-agent\n\n"
        )
        request = _parse_credential_protocol(protocol_input)
        self.assertEqual(
            request.multivalued["future-capability[]"],
            ("first", "second"),
        )
        output = credential_from_protocol(
            self.contract,
            "get",
            protocol_input,
            resolver=StaticCredentials(),
            identity_verifier=lambda credential: None,
        )
        self.assertEqual(output, "username=hsdb-agent\npassword=token-agent\n")

    def test_unknown_duplicate_and_malformed_scalar_fields_fail_closed(self) -> None:
        valid = (
            "protocol=http\n"
            "host=gitea-ci.orb.local:3000\n"
            "path=admin/HSDB.git\n"
            "username=hsdb-agent\n"
        )
        cases = {
            "unknown scalar": valid + "authtype=basic\n",
            "duplicate protocol": "protocol=https\n" + valid,
            "duplicate host": valid + "host=gitea-ci.orb.local:3000\n",
            "duplicate path": valid + "path=admin/HSDB.git\n",
            "duplicate username": valid + "username=hsdb-agent\n",
            "missing protocol": valid.removeprefix("protocol=http\n"),
            "missing host": valid.replace("host=gitea-ci.orb.local:3000\n", ""),
            "missing path": valid.replace("path=admin/HSDB.git\n", ""),
            "empty key": valid + "=value\n",
            "empty multivalue key": valid + "[]=value\n",
            "missing equals": valid + "malformed\n",
            "nul byte": valid + "capability[]=bad\x00value\n",
            "carriage return": valid + "capability[]=bad\rvalue\n",
            "nonempty after terminator": valid + "\ncapability[]=late\n",
            "oversized line": valid + "capability[]=" + ("x" * 65536) + "\n",
        }
        for name, protocol_input in cases.items():
            with self.subTest(name=name), self.assertRaises(BrokerError) as caught:
                _parse_credential_protocol(protocol_input)
            self.assertEqual(caught.exception.code, "CREDENTIAL_PROTOCOL_INVALID")

    def test_target_and_identity_mismatch_fail_before_credential_resolution(self) -> None:
        class FailIfResolved:
            def resolve(self, project, operation):
                raise AssertionError("credential resolution must not run")

        cases = (
            "protocol=https\nhost=gitea-ci.orb.local:3000\npath=admin/HSDB.git\n",
            "protocol=http\nhost=attacker.invalid\npath=admin/HSDB.git\n",
            "protocol=http\nhost=gitea-ci.orb.local:3000\npath=admin/unknown.git\n",
            "protocol=http\nhost=gitea-ci.orb.local:3000\npath=admin/HSDB.git\nusername=newemaint-agent\n",
        )
        for protocol_input in cases:
            with self.subTest(protocol_input=protocol_input), self.assertRaises(BrokerError):
                credential_from_protocol(
                    self.contract,
                    "get",
                    protocol_input,
                    resolver=FailIfResolved(),
                    identity_verifier=lambda credential: None,
                )

    def test_cli_credential_helper_supports_current_shape_and_non_get_actions(self) -> None:
        protocol_input = (
            ROOT / "codex/tests/fixtures/host-access/git-credential-get-current.txt"
        ).read_text() + "\n"
        argv = [
            "--access-manifest", str(ACCESS),
            "--governance-manifest", str(GOVERNANCE),
            "credential-helper", "get",
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch("sys.stdin", io.StringIO(protocol_input)),
            patch.object(
                CredentialResolver,
                "resolve",
                return_value=ResolvedCredential("aisoft-platform-agent", "token-agent"),
            ),
            patch.object(HostAccessBroker, "_verify_identity", return_value=None),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            self.assertEqual(host_access_cli_main(argv), 0)
        self.assertEqual(
            stdout.getvalue(),
            "username=aisoft-platform-agent\npassword=token-agent\n",
        )
        self.assertEqual(stderr.getvalue(), "")

        for action in ("store", "erase"):
            with self.subTest(action=action):
                stdout = io.StringIO()
                with (
                    patch("sys.stdin", io.StringIO(protocol_input)),
                    redirect_stdout(stdout),
                ):
                    self.assertEqual(host_access_cli_main(argv[:-1] + [action]), 0)
                self.assertEqual(stdout.getvalue(), "")

    def test_cli_exposes_only_typed_issue_and_pull_fields(self) -> None:
        body = "Closes #70\ndocs/changes/70/summary-governed-host-writes-260809.md"
        argv = [
            "--access-manifest", str(ACCESS),
            "--governance-manifest", str(GOVERNANCE),
            "broker", "--project", "aisoft-platform",
            "--operation", "gitea.pull.create",
            "--issue", "70", "--title", "fix(host-access): governed writes",
            "--body", body,
        ]
        stdout = io.StringIO()
        with (
            patch.object(HostAccessBroker, "execute", return_value={"number": 71}) as execute,
            redirect_stdout(stdout),
        ):
            self.assertEqual(host_access_cli_main(argv), 0)
        execute.assert_called_once_with(
            "aisoft-platform", "gitea.pull.create",
            number=None, state=None, branch=None, issue=70,
            title="fix(host-access): governed writes", body=body, comment=None, sha=None,
        )
        self.assertEqual(json.loads(stdout.getvalue()), {"number": 71})

        for forbidden in ("--url", "--owner", "--repository", "--method", "--raw-body"):
            with self.subTest(forbidden=forbidden), self.assertRaises(SystemExit):
                host_access_cli_main(argv + [forbidden, "attacker.invalid"])


class GovernedHostRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_access_contract(ACCESS, GOVERNANCE)

    def test_fresh_runner_instances_use_only_fixed_broker_and_typed_arguments(self) -> None:
        calls = []

        def command_runner(argv, **kwargs):
            calls.append((list(argv), kwargs))
            payload = {"status": "PASS", "number": 70}
            return subprocess.CompletedProcess(argv, 0, json.dumps(payload) + "\n", "")

        first = GovernedHostRunner(
            self.contract, "aisoft-platform", command_runner=command_runner,
        )
        second = GovernedHostRunner(
            self.contract, "aisoft-platform", command_runner=command_runner,
        )
        self.assertEqual(first.issue_read(70)["number"], 70)
        self.assertEqual(second.issue_comment(70, "fresh-session canary")["number"], 70)
        self.assertEqual(first.push_change(70)["status"], "PASS")
        self.assertEqual([call[0][0] for call in calls], [
            "/usr/local/libexec/aisoft/host-access-broker",
            "/usr/local/libexec/aisoft/host-access-broker",
            "/usr/local/libexec/aisoft/host-access-broker",
        ])
        flattened = "\n".join(" ".join(call[0]) for call in calls)
        self.assertNotIn("curl", flattened)
        self.assertNotIn("/usr/bin/security", flattened)
        self.assertNotIn("git push", flattened)
        self.assertNotIn("ci-bot", flattened)
        self.assertNotIn("--url", flattened)
        self.assertNotIn("--owner", flattened)
        self.assertNotIn("--repository", flattened)

    def test_runner_has_no_merge_or_arbitrary_operation_surface(self) -> None:
        runner = GovernedHostRunner(
            self.contract,
            "aisoft-platform",
            command_runner=lambda argv, **kwargs: subprocess.CompletedProcess(
                argv, 0, '{"status":"PASS"}\n', ""
            ),
        )
        self.assertFalse(hasattr(runner, "merge"))
        self.assertFalse(hasattr(runner, "execute"))
        self.assertFalse(hasattr(runner, "request"))


class ProfileMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.source = self.root / "source"
        self.home.mkdir()
        self.source.mkdir()
        self.contract = load_access_contract(ACCESS, GOVERNANCE)
        self.project = self.contract.project("newemaint")
        self.source_token = self.source / "newemaint-agent-project-agent.token"
        self.source_token.write_text("new-project-token\n")
        self.source_token.chmod(0o600)
        self.profile = self.home / ".config/aisoft/projects/emaintenance.env"
        self.token = self.home / ".config/aisoft/credentials/emaintenance.token"
        self.profile.parent.mkdir(parents=True)
        self.token.parent.mkdir(parents=True)
        self.profile.write_text("legacy-profile-with-inline-token\n")
        self.token.write_text("legacy-token\n")
        self.profile.chmod(0o400)
        self.token.chmod(0o600)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def migrator(self, *, identity="newemaint-agent", replace_fn=os.replace):
        return ProfileMigrator(
            self.contract,
            home=self.home,
            source_credential_root=self.source,
            target_uid=os.getuid(),
            target_gid=os.getgid(),
            source_uid=os.getuid(),
            identity_reader=lambda token: identity,
            replace=replace_fn,
        )

    def test_apply_readback_second_run_noop_and_rollback(self) -> None:
        old_profile = self.profile.read_bytes()
        old_token = self.token.read_bytes()
        migrator = self.migrator()
        result = migrator.apply("newemaint")
        self.assertEqual(result["result"], "applied")
        self.assertNotIn(b"new-project-token", self.profile.read_bytes())
        self.assertIn(b"GITEA_IDENTITY=newemaint-agent", self.profile.read_bytes())
        self.assertEqual(self.token.read_text(), "new-project-token\n")
        self.assertEqual(stat.S_IMODE(self.profile.stat().st_mode), 0o600)
        self.assertEqual(migrator.read_back("newemaint")["result"], "read-back")
        backup = self.home / ".local/state/aisoft-profile-backups/issue-61/newemaint/latest"
        metadata_before = (backup / "metadata.json").read_bytes()
        self.assertEqual(migrator.apply("newemaint")["result"], "no-op")
        self.assertEqual((backup / "metadata.json").read_bytes(), metadata_before)
        self.assertEqual(migrator.rollback("newemaint")["result"], "rolled-back")
        self.assertEqual(self.profile.read_bytes(), old_profile)
        self.assertEqual(self.token.read_bytes(), old_token)
        self.assertEqual(stat.S_IMODE(self.profile.stat().st_mode), 0o400)

    def test_identity_mismatch_fails_before_target_mutation(self) -> None:
        before = (self.profile.read_bytes(), self.token.read_bytes())
        with self.assertRaises(BrokerError) as caught:
            self.migrator(identity="hsdb-agent").apply("newemaint")
        self.assertEqual(caught.exception.code, "IDENTITY_MISMATCH")
        self.assertEqual((self.profile.read_bytes(), self.token.read_bytes()), before)

    def test_source_mode_and_symlink_are_rejected(self) -> None:
        self.source_token.chmod(0o644)
        with self.assertRaises(BrokerError) as caught:
            self.migrator().apply("newemaint")
        self.assertEqual(caught.exception.code, "CREDENTIAL_MODE_INVALID")

    def test_multiline_source_and_target_credentials_are_rejected(self) -> None:
        self.source_token.write_text("new-project-token\nsecond-token\n")
        with self.assertRaises(BrokerError) as caught:
            self.migrator().apply("newemaint")
        self.assertEqual(caught.exception.code, "CREDENTIAL_INVALID")

        self.source_token.write_text("new-project-token\n")
        self.migrator().apply("newemaint")
        self.token.write_text("new-project-token\nsecond-token\n")
        with self.assertRaises(BrokerError) as caught:
            self.migrator().consume_check("newemaint")
        self.assertEqual(caught.exception.code, "CREDENTIAL_INVALID")

    def test_source_owner_mismatch_is_rejected(self) -> None:
        migrator = ProfileMigrator(
            self.contract,
            home=self.home,
            source_credential_root=self.source,
            target_uid=os.getuid(),
            target_gid=os.getgid(),
            source_uid=os.getuid() + 1,
            identity_reader=lambda token: "newemaint-agent",
        )
        with self.assertRaises(BrokerError) as caught:
            migrator.apply("newemaint")
        self.assertEqual(caught.exception.code, "CREDENTIAL_OWNER_INVALID")
        self.source_token.unlink()
        target = self.source / "real-token"
        target.write_text("new-project-token\n")
        target.chmod(0o600)
        self.source_token.symlink_to(target)
        with self.assertRaises(BrokerError) as caught:
            self.migrator().apply("newemaint")
        self.assertEqual(caught.exception.code, "CREDENTIAL_MODE_INVALID")

    def test_partial_replace_failure_restores_both_files(self) -> None:
        before = (self.profile.read_bytes(), self.token.read_bytes())
        failed = False

        def fail_once(source, target):
            nonlocal failed
            if Path(target) == self.profile and not failed:
                failed = True
                raise OSError("synthetic profile replace failure")
            os.replace(source, target)

        with self.assertRaises(BrokerError) as caught:
            self.migrator(replace_fn=fail_once).apply("newemaint")
        self.assertEqual(caught.exception.code, "PROFILE_APPLY_FAILED")
        self.assertEqual((self.profile.read_bytes(), self.token.read_bytes()), before)

    def test_cross_project_source_credential_is_never_selected(self) -> None:
        wrong = self.source / "hsdb-agent-project-agent.token"
        wrong.write_text("hsdb-secret\n")
        wrong.chmod(0o600)
        self.source_token.unlink()
        with self.assertRaises(BrokerError) as caught:
            self.migrator().apply("newemaint")
        self.assertEqual(caught.exception.code, "CREDENTIAL_UNAVAILABLE")
        self.assertNotIn("hsdb-secret", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
