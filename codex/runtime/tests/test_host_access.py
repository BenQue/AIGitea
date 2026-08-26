from __future__ import annotations

import io
import json
import os
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
LABELS = ROOT / "codex/config/gitea-labels.json"


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
        self.assertEqual(len(self.contract.projects), 10)
        profiles = {
            item.repository: item.vm_profile.name
            for item in self.contract.projects
            if item.vm_profile is not None
        }
        self.assertEqual(profiles, {
            "aisoft-platform": "aisoft-platform",
            "HSDB": "hsdb",
            "LocalWMS": "localwms",
            "NewEMaint": "emaintenance",
            "rsdesign-new": "rsdesign",
            "SFMDigitalBoard": "sfm",
        })
        names = {item.name for item in self.contract.operations}
        self.assertFalse(any("merge" in value or "shell" in value or "url" in value
                             for value in names))
        with self.assertRaises(AccessContractError):
            self.contract.operation("git.push.main")

    def test_manifest_fixed_remote_defaults_and_rejects_unsafe_names(self) -> None:
        gitea_remote_projects = {"newemaint", "sfm-digital-board"}
        remotes = {project.project_id: project.git_remote_name
                   for project in self.contract.projects}
        for project_id in gitea_remote_projects:
            self.assertEqual(remotes[project_id], "gitea")
        self.assertTrue(all(
            remote == "origin" for project_id, remote in remotes.items()
            if project_id not in gitea_remote_projects
        ))
        raw = json.loads(ACCESS.read_text())
        for project_id in gitea_remote_projects:
            declared = next(
                project for project in raw["projects"]
                if project["project_id"] == project_id
            )
            self.assertEqual(declared["git_remote_name"], "gitea")
        self.assertTrue(all(
            "git_remote_name" not in project for project in raw["projects"]
            if project["project_id"] not in gitea_remote_projects
        ))

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "access.json"
            for invalid in (
                "", "../gitea", "https://attacker.invalid", "gitea remote",
                "+gitea", "gitea..backup", "gitea.lock",
            ):
                with self.subTest(invalid=invalid):
                    candidate = json.loads(ACCESS.read_text())
                    next(
                        project for project in candidate["projects"]
                        if project["project_id"] == "newemaint"
                    )["git_remote_name"] = invalid
                    path.write_text(json.dumps(candidate))
                    with self.assertRaises(AccessContractError):
                        load_access_contract(path, GOVERNANCE)

    def test_governed_issue_and_pull_operations_have_exact_typed_fields(self) -> None:
        expected = {
            "gitea.issue.create": ("title", "body"),
            "gitea.issue.read": ("number",),
            "gitea.issue.update": ("number", "title", "body"),
            "gitea.issue.comment": ("number", "comment"),
            "gitea.issue.comments.read": ("number",),
            "gitea.pull.create": ("issue", "title", "body"),
            "gitea.pull.read": ("number",),
            "gitea.pull.update": ("number", "issue", "title", "body"),
            "gitea.commit.status.read": ("sha",),
            "gitea.actions.run.read": ("sha",),
            "gitea.actions.job.logs.read": ("job",),
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
        onboarding = self.contract.operation("host.onboarding.check")
        self.assertEqual(onboarding.identity_route, "manager-audit")
        self.assertFalse(onboarding.mutating)
        self.assertEqual(onboarding.arguments, ())

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
        self.assertEqual(
            self.contract.change_branch("change/75-readable-change-names"),
            "change/75-readable-change-names",
        )

    def test_mac_credentials_are_project_scoped_protected_files(self) -> None:
        bindings = self.contract.raw["identity_bindings"]
        self.assertEqual(bindings["manager_audit"], {
            "identity": "aisoft-platform-manager",
            "credential_kind": "protected-file",
            "relative_path": "manager/audit.token",
        })
        self.assertEqual(bindings["manager_mutation"], {
            "identity": "aisoft-platform-manager",
            "credential_kind": "protected-file",
            "relative_path": "manager/mutation.token",
        })
        self.assertEqual(bindings["project_agent"], {
            "credential_kind": "protected-file",
            "relative_path_template": "projects/{project_id}/project-agent.token",
            "account_source": "manifest-project-agent",
        })
        mac = self.contract.raw["mac_host"]
        self.assertEqual(
            mac["credential_root"],
            "/Users/benque/Library/Application Support/AISoftPlatform/credentials",
        )
        self.assertEqual(mac["credential_owner"], "benque")
        self.assertEqual(mac["credential_directory_mode"], "700")
        self.assertEqual(mac["credential_file_mode"], "600")

        runtime = "\n".join(
            path.read_text() for path in
            (ROOT / "codex/runtime/aisoft_host_access").glob("*")
            if path.is_file()
        )
        self.assertNotIn("/usr/bin/security", runtime)
        self.assertNotIn("SecKeychain", runtime)
        self.assertNotIn("SecItemCopyMatching", runtime)
        self.assertNotIn("macos-keychain", runtime)

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

    def test_keychain_or_arbitrary_credential_file_contract_is_rejected(self) -> None:
        mutations = (
            ("identity_bindings", "manager_audit", "credential_kind", "macos-keychain"),
            ("identity_bindings", "manager_audit", "relative_path", "../audit.token"),
            ("identity_bindings", "project_agent", "relative_path_template", "{project_id}.token"),
            ("mac_host", "credential_root", None, "/Users/benque/MyDocs/AISoftPlatform/.git/token"),
            ("mac_host", "credential_directory_mode", None, "755"),
            ("mac_host", "credential_file_mode", None, "644"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "access.json"
            for mutation in mutations:
                with self.subTest(mutation=mutation):
                    raw = json.loads(ACCESS.read_text())
                    if mutation[0] == "identity_bindings":
                        raw[mutation[0]][mutation[1]][mutation[2]] = mutation[3]
                    else:
                        raw[mutation[0]][mutation[1]] = mutation[3]
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


class VmProfilePathPrependContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_access_contract(ACCESS, GOVERNANCE)

    def test_declared_and_undeclared_projects_parse_exactly(self) -> None:
        sfm = self.contract.project("sfm-digital-board")
        assert sfm.vm_profile is not None
        self.assertEqual(sfm.vm_profile.path_prepend,
                         ("/opt/node22/bin", "/home/coder/.local/bin"))
        for project_id in ("newemaint", "hsdb", "rsdesign-new", "localwms"):
            with self.subTest(project_id=project_id):
                project = self.contract.project(project_id)
                assert project.vm_profile is not None
                self.assertEqual(project.vm_profile.path_prepend, ())
        raw = json.loads(ACCESS.read_text())
        declared = {
            project["project_id"]: project["vm_profile"].get("path_prepend")
            for project in raw["projects"] if project["vm_profile"] is not None
        }
        self.assertEqual(declared, {
            "aisoft-platform": None,
            "sfm-digital-board": ["/opt/node22/bin", "/home/coder/.local/bin"],
            "newemaint": None,
            "hsdb": None,
            "rsdesign-new": None,
            "localwms": None,
        })

    def test_invalid_path_prepend_declarations_fail_closed(self) -> None:
        invalid_values = (
            [],
            "not-a-list",
            {"prepend": "/opt/node22/bin"},
            [42],
            [""],
            ["relative/bin"],
            ["/opt/../bin"],
            ["/opt/./bin"],
            ["/opt/node:22/bin"],
            ["/opt/node 22/bin"],
            ["/opt/node22/bin/"],
            ["/"],
            ["//opt/node22/bin"],
            ["/opt/$HOME/bin"],
            ["/opt/node22/bin", "/opt/node22/bin"],
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "access.json"
            for invalid in invalid_values:
                with self.subTest(invalid=invalid):
                    raw = json.loads(ACCESS.read_text())
                    sfm = next(project for project in raw["projects"]
                               if project["project_id"] == "sfm-digital-board")
                    sfm["vm_profile"]["path_prepend"] = invalid
                    path.write_text(json.dumps(raw))
                    with self.assertRaises(AccessContractError):
                        load_access_contract(path, GOVERNANCE)

    def test_unknown_vm_profile_key_still_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "access.json"
            raw = json.loads(ACCESS.read_text())
            sfm = next(project for project in raw["projects"]
                       if project["project_id"] == "sfm-digital-board")
            sfm["vm_profile"]["path_append"] = ["/opt/node22/bin"]
            path.write_text(json.dumps(raw))
            with self.assertRaises(AccessContractError):
                load_access_contract(path, GOVERNANCE)

    def test_profile_spec_projects_path_prepend(self) -> None:
        expectations = {
            "aisoft-platform": [],
            "sfm": ["/opt/node22/bin", "/home/coder/.local/bin"],
            "emaintenance": [],
        }
        for profile_name, expected in expectations.items():
            with self.subTest(profile_name=profile_name):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    code = host_access_cli_main([
                        "--access-manifest", str(ACCESS),
                        "--governance-manifest", str(GOVERNANCE),
                        "profile-spec", "--profile-name", profile_name,
                    ])
                self.assertEqual(code, 0)
                payload = json.loads(buffer.getvalue())
                self.assertEqual(payload["path_prepend"], expected)

    def test_aisoft_platform_profile_is_analyzer_only(self) -> None:
        project = self.contract.project("aisoft-platform")
        self.assertIsNotNone(project.vm_profile)
        assert project.vm_profile is not None
        self.assertEqual(project.vm_profile.name, "aisoft-platform")
        self.assertEqual(project.vm_profile.repo_dir, "work/AISoftPlatform")
        self.assertEqual(project.vm_profile.analysis_provider, "codex")
        self.assertEqual(project.vm_profile.implement_provider, "none")
        self.assertIsNone(project.vm_profile.timer_unit)
        self.assertEqual(project.vm_profile.path_prepend, ())

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = host_access_cli_main([
                "--access-manifest", str(ACCESS),
                "--governance-manifest", str(GOVERNANCE),
                "profile-spec", "--profile-name", "aisoft-platform",
            ])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload, {
            "analysis_provider": "codex",
            "gitea_url": "http://gitea-ci.orb.local:3000",
            "identity": "aisoft-platform-agent",
            "implement_provider": "none",
            "owner": "admin",
            "path_prepend": [],
            "profile_name": "aisoft-platform",
            "project_id": "aisoft-platform",
            "repo_dir": "/home/coder/work/AISoftPlatform",
            "repository": "aisoft-platform",
            "token_file": "/home/coder/.config/aisoft/credentials/aisoft-platform.token",
        })

    def test_localwms_profile_is_analyzer_only_without_a_timer(self) -> None:
        # #152 unlocks the analyzer canary for LocalWMS and nothing else: the
        # Development Loop stays out of scope, so implement_provider must remain
        # disabled and timer_unit must stay unset. Installing a timer template is
        # not the same as enabling one.
        #
        # analysis_provider is codex since #164. #152 picked claude by analogy
        # with the other three internal-application profiles, not from evidence
        # that the chain could run; the canary then proved it never had. On
        # gitea-ci the claude CLI is off coder's PATH and unauthenticated, so
        # claude-analyzer.sh:13 (command -v claude || exit 2) fails on its first
        # line, while codex is the one analyzer chain with a produced artifact.
        # A provider named here must be a runtime that exists on that host.
        project = self.contract.project("localwms")
        self.assertIsNotNone(project.vm_profile)
        assert project.vm_profile is not None
        self.assertEqual(project.vm_profile.name, "localwms")
        self.assertEqual(project.vm_profile.repo_dir, "work/LocalWMS")
        self.assertEqual(project.vm_profile.analysis_provider, "codex")
        self.assertEqual(project.vm_profile.implement_provider, "none")
        self.assertIsNone(project.vm_profile.timer_unit)
        self.assertEqual(project.vm_profile.path_prepend, ())

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = host_access_cli_main([
                "--access-manifest", str(ACCESS),
                "--governance-manifest", str(GOVERNANCE),
                "profile-spec", "--profile-name", "localwms",
            ])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload, {
            "analysis_provider": "codex",
            "gitea_url": "http://gitea-ci.orb.local:3000",
            "identity": "localwms-agent",
            "implement_provider": "none",
            "owner": "admin",
            "path_prepend": [],
            "profile_name": "localwms",
            "project_id": "localwms",
            "repo_dir": "/home/coder/work/LocalWMS",
            "repository": "LocalWMS",
            "token_file": "/home/coder/.config/aisoft/credentials/localwms.token",
        })


class MattRepositoryAdapterTests(unittest.TestCase):
    def test_agent_configuration_matches_canonical_templates(self) -> None:
        for name in ("issue-tracker.md", "triage-labels.md", "domain.md"):
            with self.subTest(name=name):
                self.assertEqual(
                    (ROOT / "docs/agents" / name).read_bytes(),
                    (ROOT / "templates/docs/agents" / name).read_bytes(),
                )

    def test_claude_has_one_aisoft_agent_skills_block(self) -> None:
        content = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(content.count("## Agent skills"), 1)
        for expected in (
            "AISoftPlatform Gitea",
            "docs/agents/issue-tracker.md",
            "namespaced Matt triage labels",
            "docs/agents/triage-labels.md",
            "single-context",
            "docs/agents/domain.md",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, content)


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

    def _label_broker(self, remote: list[dict[str, object]], calls: list[tuple]):
        """Broker wired to an in-memory label repository."""

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            payload = json.loads(body) if body else None
            calls.append((method, url, payload))
            if method == "GET":
                page = int(url.rsplit("page=", 1)[1])
                start = (page - 1) * 50
                return 200, {}, json.dumps(remote[start:start + 50]).encode()
            if method == "POST":
                stored = dict(payload)
                stored["id"] = len(remote) + 1
                remote.append(stored)
                return 200, {}, json.dumps(stored).encode()
            if method == "PATCH":
                label_id = int(url.rsplit("/", 1)[1])
                for index, item in enumerate(remote):
                    if item["id"] == label_id:
                        remote[index] = dict(payload) | {"id": label_id}
                        return 200, {}, json.dumps(remote[index]).encode()
                raise AssertionError("PATCH targeted an unknown label id")
            raise AssertionError(f"unexpected method {method}")

        return HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
            label_manifest_path=str(LABELS),
        )

    def test_label_provision_is_idempotent_and_never_deletes(self) -> None:
        manifest = json.loads(LABELS.read_text())
        canonical = manifest["canonical"]
        remote: list[dict[str, object]] = []
        calls: list[tuple] = []
        broker = self._label_broker(remote, calls)

        first = broker.execute("aisoft-platform", "gitea.labels.provision")
        self.assertEqual(first["created"], len(canonical))
        self.assertEqual(first["updated"], 0)
        self.assertEqual(first["unchanged"], 0)
        self.assertEqual(first["retired_present"], [])
        self.assertEqual(len(remote), len(canonical))

        calls.clear()
        second = broker.execute("aisoft-platform", "gitea.labels.provision")
        self.assertEqual(
            (second["created"], second["updated"], second["unchanged"]),
            (0, 0, len(canonical)),
        )
        self.assertEqual({method for method, _url, _payload in calls}, {"GET"})

        # Gitea may echo a color back with a '#' prefix and different case, and
        # may pad the description. None of that is drift; treating it as drift
        # would rewrite every label on every run.
        remote[0]["color"] = "#" + str(remote[0]["color"]).upper()
        remote[0]["description"] = "  " + str(remote[0]["description"]) + "  "
        calls.clear()
        cosmetic = broker.execute("aisoft-platform", "gitea.labels.provision")
        self.assertEqual(cosmetic["updated"], 0)
        self.assertEqual({method for method, _url, _payload in calls}, {"GET"})

        # Real drift is repaired in place, addressed by id.
        remote[1]["color"] = "ffffff"
        remote[2]["description"] = "drifted"
        calls.clear()
        repaired = broker.execute("aisoft-platform", "gitea.labels.provision")
        self.assertEqual(repaired["updated"], 2)
        patched = [url for method, url, _payload in calls if method == "PATCH"]
        self.assertEqual(len(patched), 2)
        for url in patched:
            self.assertRegex(url, r"/labels/\d+$")
        self.assertEqual(remote[1]["color"], canonical[1]["color"])

        # And it converges: the run after a repair writes nothing.
        calls.clear()
        converged = broker.execute("aisoft-platform", "gitea.labels.provision")
        self.assertEqual(converged["updated"], 0)
        self.assertEqual({method for method, _url, _payload in calls}, {"GET"})

        # Retired values are reported, kept, and never deleted.
        retired_name = manifest["retired"][0]["name"]
        remote.append({
            "id": 9001,
            "name": retired_name,
            "color": "cccccc",
            "description": "legacy",
        })
        reported = broker.execute("aisoft-platform", "gitea.labels.provision")
        self.assertEqual(reported["retired_present"], [retired_name])
        self.assertIn(retired_name, [item["name"] for item in remote])

        self.assertNotIn(
            "DELETE", {method for method, _url, _payload in calls}
        )

    def test_label_read_paginates_and_validates_entries(self) -> None:
        remote = [
            {"id": i, "name": f"label-{i}", "color": "aabbcc", "description": "d"}
            for i in range(1, 76)
        ]
        calls: list[tuple] = []
        broker = self._label_broker(remote, calls)
        value = broker.execute("aisoft-platform", "gitea.labels.read")
        self.assertEqual(len(value), 75)
        self.assertEqual(len([c for c in calls if c[0] == "GET"]), 2)

        remote[0] = {"id": 1, "name": "bad", "color": 7, "description": "d"}
        with self.assertRaises(BrokerError) as caught:
            broker.execute("aisoft-platform", "gitea.labels.read")
        self.assertEqual(caught.exception.code, "RESPONSE_SCHEMA_INVALID")

    def test_label_surface_has_no_delete_and_requires_a_configured_manifest(self) -> None:
        broker = HostAccessBroker(self.contract, credentials=StaticCredentials())
        for denied in (
            "gitea.labels.delete",
            "gitea.label.delete",
            "gitea.labels.remove",
        ):
            with self.subTest(denied=denied), self.assertRaises(BrokerError) as caught:
                broker.execute("aisoft-platform", denied)
            self.assertEqual(caught.exception.code, "REQUEST_DENIED")

        self.assertNotIn(
            "gitea.labels.delete",
            {operation.name for operation in self.contract.operations},
        )

        # An install that never shipped the manifest must fail closed rather
        # than provision an empty or guessed label set.
        unconfigured = self._label_broker([], [])
        unconfigured.label_manifest_path = None
        with self.assertRaises(BrokerError) as caught:
            unconfigured.execute("aisoft-platform", "gitea.labels.provision")
        self.assertEqual(caught.exception.code, "REQUEST_DENIED")

    def _issue_comment_broker(self, comments: list[dict[str, object]], calls: list[tuple]):
        """Broker wired to an in-memory comment collection with real paging."""

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            payload = json.loads(body) if body else None
            calls.append((method, url, payload))
            if method == "GET" and "/comments?" in url:
                page = int(url.rsplit("page=", 1)[1])
                start = (page - 1) * 50
                return 200, {}, json.dumps(comments[start:start + 50]).encode()
            raise AssertionError(f"unexpected {method} {url}")

        return HostAccessBroker(
            self.contract, credentials=StaticCredentials(), transport=transport
        )

    @staticmethod
    def _gitea_comment(index: int) -> dict[str, object]:
        """A comment shaped like Gitea's, noise included.

        The noise is the point: the projection must drop it, so the governed
        read surface does not change shape when Gitea's does.
        """
        return {
            "id": 900 + index,
            "body": f"comment body {index}",
            "created_at": "2026-08-22T09:44:42+08:00",
            "updated_at": "2026-08-22T09:44:42+08:00",
            "html_url": "http://gitea-ci.orb.local:3000/x#issuecomment-1",
            "issue_url": "http://gitea-ci.orb.local:3000/y",
            "assets": [],
            "user": {
                "login": "localwms-agent",
                "id": 13,
                "email": "localwms-agent@aisoft.local",
                "avatar_url": "http://gitea-ci.orb.local:3000/avatars/873a5ad1",
                "is_admin": False,
            },
        }

    def test_issue_comments_read_projects_and_is_number_bound(self) -> None:
        calls: list[tuple] = []
        broker = self._issue_comment_broker([self._gitea_comment(1)], calls)

        value = broker.execute("aisoft-platform", "gitea.issue.comments.read", number=6)

        self.assertEqual(
            value,
            [{
                "id": 901,
                "author": "localwms-agent",
                "created_at": "2026-08-22T09:44:42+08:00",
                "body": "comment body 1",
            }],
        )
        self.assertEqual(
            [url for method, url, _ in calls if method == "GET"],
            ["http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform"
             "/issues/6/comments?limit=50&page=1"],
        )
        # A read must not mutate: no request leaves the GET verb.
        self.assertEqual({method for method, _, _ in calls}, {"GET"})

    def test_issue_comments_read_pages_past_the_first_fifty(self) -> None:
        """A silent first-page-only read makes a partial discussion look whole."""
        calls: list[tuple] = []
        broker = self._issue_comment_broker(
            [self._gitea_comment(index) for index in range(1, 73)], calls
        )

        value = broker.execute("aisoft-platform", "gitea.issue.comments.read", number=6)

        self.assertEqual(len(value), 72)
        self.assertEqual([item["id"] for item in value], list(range(901, 973)))
        self.assertEqual(
            [url.rsplit("page=", 1)[1] for method, url, _ in calls if method == "GET"],
            ["1", "2"],
        )

    def test_issue_comments_read_rejects_a_malformed_entry(self) -> None:
        broken = self._gitea_comment(1)
        del broken["body"]
        broker = self._issue_comment_broker([broken], [])

        with self.assertRaises(BrokerError) as caught:
            broker.execute("aisoft-platform", "gitea.issue.comments.read", number=6)
        self.assertEqual(caught.exception.code, "RESPONSE_SCHEMA_INVALID")

    def test_issue_comments_read_takes_only_a_positive_number(self) -> None:
        calls: list[tuple] = []
        broker = self._issue_comment_broker([self._gitea_comment(1)], calls)

        # Absent and present-but-invalid are different failures, and the broker
        # already separates them everywhere else: a missing typed argument is
        # ARGUMENT_MISMATCH, a supplied nonsense value is ARGUMENT_INVALID.
        with self.assertRaises(BrokerError) as missing:
            broker.execute("aisoft-platform", "gitea.issue.comments.read")
        self.assertEqual(missing.exception.code, "ARGUMENT_MISMATCH")

        for rejected in (0, -1):
            with self.subTest(number=rejected), self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "gitea.issue.comments.read", number=rejected
                )
            self.assertEqual(caught.exception.code, "ARGUMENT_INVALID")

        # comment belongs to the write half of the pair, not to this one.
        with self.assertRaises(BrokerError) as extra:
            broker.execute(
                "aisoft-platform", "gitea.issue.comments.read", number=6, comment="x"
            )
        self.assertEqual(extra.exception.code, "ARGUMENT_MISMATCH")

        # Nothing above reached the network.
        self.assertEqual(calls, [])

    def test_comment_surface_has_no_typed_update_or_delete(self) -> None:
        """Rewriting or erasing someone else's comment stays a human action."""
        names = {operation.name for operation in self.contract.operations}
        self.assertIn("gitea.issue.comments.read", names)
        for absent in (
            "gitea.issue.comment.update",
            "gitea.issue.comment.delete",
            "gitea.issue.comments.delete",
        ):
            self.assertNotIn(absent, names)

    # --- Actions run and job log reads (#143) --------------------------------

    ACTIONS_SHA = "b" * 40

    def _actions_broker(
        self,
        runs: list[dict[str, object]],
        jobs: dict[int, list[dict[str, object]]],
        calls: list[tuple],
        log: bytes | None = None,
    ):
        """Broker wired to an in-memory Actions run/job/log collection."""

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            calls.append((method, url, headers.get("Accept")))
            if "/actions/runs?" in url:
                page = int(url.rsplit("page=", 1)[1])
                start = (page - 1) * 50
                window = runs[start:start + 50]
                return 200, {}, json.dumps(
                    {"total_count": len(runs), "workflow_runs": window}
                ).encode()
            if "/actions/runs/" in url and "/jobs?" in url:
                run_id = int(url.split("/actions/runs/", 1)[1].split("/", 1)[0])
                page = int(url.rsplit("page=", 1)[1])
                start = (page - 1) * 50
                window = jobs.get(run_id, [])[start:start + 50]
                return 200, {}, json.dumps(
                    {"total_count": len(jobs.get(run_id, [])), "jobs": window}
                ).encode()
            if "/actions/jobs/" in url and url.endswith("/logs"):
                if log is None:
                    return 404, {}, b"not found"
                return 200, {}, log
            raise AssertionError(f"unexpected {method} {url}")

        return HostAccessBroker(
            self.contract, credentials=StaticCredentials(), transport=transport
        )

    @staticmethod
    def _gitea_run() -> dict[str, object]:
        """A run shaped like Gitea's, embedded objects included.

        The embedded repository and user objects are the point: the projection
        must drop them, so a governed read surface does not change shape — or
        start disclosing identities — when Gitea's does.
        """
        return {
            "id": 493,
            "path": ".gitea/workflows/ci.yml",
            "display_title": "feat: something",
            "event": "pull_request",
            "head_branch": "change/16-build-hygiene-gates",
            "head_sha": "b" * 40,
            "run_number": 12,
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-08-22T09:44:42+08:00",
            "completed_at": "2026-08-22T09:44:59+08:00",
            "html_url": "http://gitea-ci.orb.local:3000/admin/LocalWMS/actions/runs/493",
            "repository": {"id": 9, "full_name": "admin/LocalWMS"},
            "actor": {"login": "localwms-agent", "email": "x@aisoft.local", "is_admin": False},
            "trigger_actor": {"login": "localwms-agent", "is_admin": False},
        }

    @staticmethod
    def _gitea_job() -> dict[str, object]:
        return {
            "id": 493,
            "name": "test",
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-08-22T09:44:42+08:00",
            "completed_at": "2026-08-22T09:44:59+08:00",
            "runner_name": "gitea-ci-host",
            "run_id": 493,
            "head_sha": "b" * 40,
            "labels": ["host"],
            "steps": [
                {
                    "number": 1,
                    "name": "Set up job",
                    "status": "completed",
                    "conclusion": "success",
                    "started_at": "2026-08-22T09:44:42+08:00",
                    "completed_at": "2026-08-22T09:44:43+08:00",
                },
                {
                    "number": 2,
                    "name": "npm ci",
                    "status": "completed",
                    "conclusion": "success",
                    "started_at": "2026-08-22T09:44:43+08:00",
                    "completed_at": "2026-08-22T09:44:52+08:00",
                },
                {
                    "number": 3,
                    "name": "run tests",
                    "status": "completed",
                    "conclusion": "skipped",
                    "started_at": None,
                    "completed_at": None,
                },
            ],
        }

    def test_actions_run_read_projects_step_level_conclusions(self) -> None:
        """The question #143 exists for: which steps ran, and for how long."""
        calls: list[tuple] = []
        broker = self._actions_broker(
            [self._gitea_run()], {493: [self._gitea_job()]}, calls
        )

        value = broker.execute(
            "aisoft-platform", "gitea.actions.run.read", sha=self.ACTIONS_SHA
        )

        self.assertEqual(value["total_count"], 1)
        run = value["runs"][0]
        self.assertEqual(run["duration_seconds"], 17)
        # The embedded repository and user objects must not survive projection.
        self.assertNotIn("repository", run)
        self.assertNotIn("actor", run)
        steps = run["jobs"][0]["steps"]
        self.assertEqual(
            [(step["name"], step["conclusion"], step["duration_seconds"]) for step in steps],
            [
                ("Set up job", "success", 1),
                ("npm ci", "success", 9),
                # An unfinished or skipped step reports None, not 0: "took no
                # measurable time" and "never ran" are different answers, and
                # conflating them reproduces the unverifiable number #143 names.
                ("run tests", "skipped", None),
            ],
        )
        self.assertEqual({method for method, _, _ in calls}, {"GET"})

    def test_actions_run_read_is_project_scoped_and_sha_keyed(self) -> None:
        calls: list[tuple] = []
        broker = self._actions_broker([self._gitea_run()], {493: []}, calls)

        broker.execute(
            "aisoft-platform", "gitea.actions.run.read", sha=self.ACTIONS_SHA
        )

        first = [url for _, url, _ in calls][0]
        self.assertTrue(
            first.startswith(
                "http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform"
                "/actions/runs?head_sha=" + self.ACTIONS_SHA
            ),
            first,
        )

    def test_actions_run_read_separates_no_runs_from_a_failed_read(self) -> None:
        """The reading trap #143 names, closed from both sides."""
        calls: list[tuple] = []
        broker = self._actions_broker([], {}, calls)

        value = broker.execute(
            "aisoft-platform", "gitea.actions.run.read", sha=self.ACTIONS_SHA
        )
        # A well-formed SHA with nothing to show is an empty list, and it is
        # shaped nothing like the BrokerError a failed read raises.
        self.assertEqual(value, {"sha": self.ACTIONS_SHA, "total_count": 0, "runs": []})

    def test_actions_run_read_rejects_an_abbreviated_sha_before_any_request(self) -> None:
        """gitea.commit.status.read answers an abbreviated SHA with a fake success."""
        calls: list[tuple] = []
        broker = self._actions_broker([self._gitea_run()], {493: []}, calls)

        for rejected in ("b" * 7, "B" * 40, "", "b" * 41):
            with self.subTest(sha=rejected), self.assertRaises(BrokerError) as caught:
                broker.execute("aisoft-platform", "gitea.actions.run.read", sha=rejected)
            self.assertEqual(caught.exception.code, "ARGUMENT_INVALID")

        with self.assertRaises(BrokerError) as missing:
            broker.execute("aisoft-platform", "gitea.actions.run.read")
        self.assertEqual(missing.exception.code, "ARGUMENT_MISMATCH")

        self.assertEqual(calls, [])

    def test_actions_run_read_pages_past_the_first_fifty(self) -> None:
        calls: list[tuple] = []
        runs = []
        for index in range(72):
            run = self._gitea_run()
            run["id"] = 1000 + index
            runs.append(run)
        broker = self._actions_broker(runs, {}, calls)

        value = broker.execute(
            "aisoft-platform", "gitea.actions.run.read", sha=self.ACTIONS_SHA
        )

        self.assertEqual(value["total_count"], 72)
        run_pages = [
            url.rsplit("page=", 1)[1] for _, url, _ in calls if "/actions/runs?" in url
        ]
        self.assertEqual(run_pages, ["1", "2"])

    def test_actions_run_read_rejects_a_malformed_entry(self) -> None:
        broken = self._gitea_run()
        broken["id"] = "493"
        broker = self._actions_broker([broken], {}, [])

        with self.assertRaises(BrokerError) as caught:
            broker.execute(
                "aisoft-platform", "gitea.actions.run.read", sha=self.ACTIONS_SHA
            )
        self.assertEqual(caught.exception.code, "RESPONSE_SCHEMA_INVALID")

    def test_actions_job_logs_read_redacts_credentials(self) -> None:
        """The negative verification #143 requires: a planted credential is masked."""
        log = (
            "Authorization: token planted-header-credential\n"
            "git clone https://ci:planted-url-password@gitea.example/x.git\n"
            "NPM_TOKEN=planted-assignment-credential\n"
            "ghp_plantedgithubtoken0123456789\n"
            "-----BEGIN RSA PRIVATE KEY-----\nplantedkeymaterial\n"
            "-----END RSA PRIVATE KEY-----\n"
            "using credential token-agent to authenticate\n"
            "checked out 0123456789abcdef0123456789abcdef01234567\n"
        ).encode()
        broker = self._actions_broker([], {}, [], log=log)

        value = broker.execute(
            "aisoft-platform", "gitea.actions.job.logs.read", job=493
        )

        for planted in (
            "planted-header-credential",
            "planted-url-password",
            "planted-assignment-credential",
            "plantedgithubtoken0123456789",
            "plantedkeymaterial",
            # The credential this very request authenticated with — the exact
            # match rule, which needs no pattern to recognise a leak.
            "token-agent",
        ):
            with self.subTest(planted=planted):
                self.assertNotIn(planted, value["log"])
        self.assertGreaterEqual(value["redactions"], 6)
        # A commit SHA is bare 40-hex and must survive: masking it would trade a
        # certain loss of the most useful field in a CI log for nothing.
        self.assertIn("0123456789abcdef0123456789abcdef01234567", value["log"])

    def test_actions_job_logs_read_marks_truncation_instead_of_hiding_it(self) -> None:
        tail = "the failing assertion is printed last\n"
        log = (("x" * 79 + "\n") * 2000 + tail).encode()
        broker = self._actions_broker([], {}, [], log=log)

        value = broker.execute(
            "aisoft-platform", "gitea.actions.job.logs.read", job=493
        )

        self.assertTrue(value["truncated"])
        self.assertEqual(value["original_bytes"], len(log))
        self.assertLessEqual(value["returned_bytes"], len(log))
        self.assertIn("truncated", value["log"].splitlines()[0])
        # Tail-biased: a failing step prints its error last, so a head-biased
        # cut would reliably discard the only part worth reading.
        self.assertIn(tail.strip(), value["log"])

    def test_actions_job_logs_read_leaves_a_short_log_untouched(self) -> None:
        broker = self._actions_broker([], {}, [], log=b"all good\n")

        value = broker.execute(
            "aisoft-platform", "gitea.actions.job.logs.read", job=493
        )

        self.assertFalse(value["truncated"])
        self.assertEqual(value["redactions"], 0)
        self.assertEqual(value["log"], "all good\n")
        self.assertEqual(value["original_bytes"], value["returned_bytes"])

    def test_actions_job_logs_read_takes_only_a_positive_job(self) -> None:
        calls: list[tuple] = []
        broker = self._actions_broker([], {}, calls, log=b"")

        with self.assertRaises(BrokerError) as missing:
            broker.execute("aisoft-platform", "gitea.actions.job.logs.read")
        self.assertEqual(missing.exception.code, "ARGUMENT_MISMATCH")

        for rejected in (0, -1):
            with self.subTest(job=rejected), self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "gitea.actions.job.logs.read", job=rejected
                )
            self.assertEqual(caught.exception.code, "ARGUMENT_INVALID")

        # sha belongs to the other half of the pair, not to this one.
        with self.assertRaises(BrokerError) as extra:
            broker.execute(
                "aisoft-platform",
                "gitea.actions.job.logs.read",
                job=493,
                sha=self.ACTIONS_SHA,
            )
        self.assertEqual(extra.exception.code, "ARGUMENT_MISMATCH")

        self.assertEqual(calls, [])

    def test_actions_job_logs_read_surfaces_an_unknown_job_as_a_failure(self) -> None:
        """A job id from another repository 404s against this project's URL."""
        broker = self._actions_broker([], {}, [], log=None)

        with self.assertRaises(BrokerError) as caught:
            broker.execute(
                "aisoft-platform", "gitea.actions.job.logs.read", job=999999
            )
        self.assertEqual(caught.exception.code, "HTTP_404")

    def test_actions_surface_has_no_typed_write(self) -> None:
        """Triggering or re-running CI stays a human action."""
        names = {operation.name for operation in self.contract.operations}
        self.assertIn("gitea.actions.run.read", names)
        self.assertIn("gitea.actions.job.logs.read", names)
        for operation in self.contract.operations:
            if operation.name.startswith("gitea.actions."):
                self.assertFalse(operation.mutating, operation.name)
        for absent in (
            "gitea.actions.run.rerun",
            "gitea.actions.run.cancel",
            "gitea.actions.workflow.dispatch",
            "gitea.actions.workflow.enable",
            "gitea.actions.workflow.disable",
        ):
            self.assertNotIn(absent, names)

    def _issue_label_broker(
        self,
        repository_labels: list[dict[str, object]],
        issue_labels: list[dict[str, object]],
        calls: list[tuple],
    ):
        """Broker wired to an in-memory Issue attached to a label repository.

        Repository label definitions (#108) and Issue label attachments (#115)
        are two different endpoints on the same names, so the fake keeps them as
        two structures that only the PUT projection is allowed to connect.
        """

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            payload = json.loads(body) if body else None
            calls.append((method, url, payload))
            if method == "GET" and "/labels?" in url:
                page = int(url.rsplit("page=", 1)[1])
                start = (page - 1) * 50
                return 200, {}, json.dumps(repository_labels[start:start + 50]).encode()
            if method == "GET" and url.endswith("/labels"):
                return 200, {}, json.dumps(issue_labels).encode()
            if method == "PUT" and url.endswith("/labels"):
                by_id = {item["id"]: item for item in repository_labels}
                issue_labels[:] = [by_id[value] for value in payload["labels"]]
                return 200, {}, json.dumps(issue_labels).encode()
            raise AssertionError(f"unexpected {method} {url}")

        return HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
            label_manifest_path=str(LABELS),
        )

    @staticmethod
    def _provisioned_labels() -> list[dict[str, object]]:
        return [
            {"id": index, "name": entry["name"], "color": entry["color"],
             "description": entry["description"]}
            for index, entry in enumerate(
                json.loads(LABELS.read_text())["canonical"], start=1
            )
        ]

    def test_issue_label_read_is_number_bound(self) -> None:
        repository = self._provisioned_labels()
        attached = [item for item in repository if item["name"] == "pr-open"]
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, attached, calls)

        value = broker.execute("aisoft-platform", "gitea.issue.labels.read", number=115)
        self.assertEqual([item["name"] for item in value], ["pr-open"])
        self.assertEqual(
            [url for method, url, _ in calls if method == "GET"],
            ["http://gitea-ci.orb.local:3000/api/v1/repos/admin/aisoft-platform"
             "/issues/115/labels"],
        )

    def test_issue_label_set_accepts_only_manifest_lifecycle_values(self) -> None:
        """AC-1: the accepted values are derived from the installed manifest.

        argparse choices or a literal tuple here would be another copy of the
        eight names (#115 AC-7), and it would accept a value the deployed
        manifest no longer declares.
        """
        repository = self._provisioned_labels()
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, [], calls)

        for rejected in (
            "bogus",
            "type/feature",      # a real label, but not the lifecycle dimension
            "complexity/small",
            "triage/ready-for-agent",
            "area/web",          # a declared project extension prefix
            "",
            "Completed",         # names are exact, not case-insensitive
        ):
            with self.subTest(rejected=rejected), self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "gitea.issue.labels.set",
                    number=115, lifecycle=rejected,
                )
            self.assertEqual(caught.exception.code, "ARGUMENT_MISMATCH")
        self.assertEqual([method for method, _, _ in calls if method == "PUT"], [])

        # Every lifecycle name the manifest declares is accepted.
        for accepted in ("needs-analysis", "approved", "completed", "deployed"):
            with self.subTest(accepted=accepted):
                broker.execute(
                    "aisoft-platform", "gitea.issue.labels.set",
                    number=115, lifecycle=accepted,
                )

    def test_lifecycle_argument_belongs_only_to_issue_label_set(self) -> None:
        repository = self._provisioned_labels()
        broker = self._issue_label_broker(repository, [], [])

        with self.assertRaises(BrokerError) as missing:
            broker.execute("aisoft-platform", "gitea.issue.labels.set", number=115)
        self.assertEqual(missing.exception.code, "ARGUMENT_MISMATCH")

        for operation in ("gitea.issue.labels.read", "gitea.issue.read"):
            with self.subTest(operation=operation), self.assertRaises(BrokerError) as extra:
                broker.execute(
                    "aisoft-platform", operation, number=115, lifecycle="completed"
                )
            self.assertEqual(extra.exception.code, "ARGUMENT_MISMATCH")

    def test_issue_label_set_fails_closed_when_the_label_is_not_provisioned(self) -> None:
        """AC-3: attaching is not defining.

        The repository is missing completed, so there is no id to attach. The
        broker points at gitea.labels.provision rather than creating the label:
        definition and attachment are two operation surfaces on purpose.
        """
        repository = [
            item for item in self._provisioned_labels() if item["name"] != "completed"
        ]
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, [], calls)

        with self.assertRaises(BrokerError) as caught:
            broker.execute(
                "aisoft-platform", "gitea.issue.labels.set",
                number=115, lifecycle="completed",
            )
        self.assertEqual(caught.exception.code, "TARGET_MISMATCH")
        self.assertIn("gitea.labels.provision", str(caught.exception))
        self.assertEqual([method for method, _, _ in calls if method == "PUT"], [])

    def test_issue_label_set_replaces_only_the_lifecycle_dimension(self) -> None:
        """AC-2: the other four label dimensions survive the write untouched.

        The failure this guards against is a set that assigns a label list
        instead of replacing one dimension, which would silently strip the
        analyzer's type/ and complexity/ output, Matt's triage/ state, and the
        project's own area/ extension the first time it ran.
        """
        repository = self._provisioned_labels()
        repository.append(
            {"id": 900, "name": "area/web", "color": "cccccc", "description": "ext"}
        )
        by_name = {str(item["name"]): item for item in repository}
        attached = [
            by_name["type/platform"],
            by_name["complexity/complex"],
            by_name["triage/ready-for-agent"],
            by_name["area/web"],
            by_name["pr-open"],
        ]
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, attached, calls)

        value = broker.execute(
            "aisoft-platform", "gitea.issue.labels.set",
            number=115, lifecycle="completed",
        )

        self.assertEqual(value["result"], "updated")
        self.assertEqual(
            set(value["before"]) - set(value["after"]), {"pr-open"}
        )
        self.assertEqual(
            set(value["after"]) - set(value["before"]), {"completed"}
        )
        self.assertEqual(
            sorted(str(item["name"]) for item in attached),
            ["area/web", "completed", "complexity/complex", "triage/ready-for-agent",
             "type/platform"],
        )
        puts = [payload for method, _url, payload in calls if method == "PUT"]
        self.assertEqual(len(puts), 1)
        self.assertIn(900, puts[0]["labels"])

    def test_issue_label_set_refuses_to_downgrade_deployed_to_completed(self) -> None:
        """AC-4: deployed and completed are mutually exclusive, deployed is stronger.

        Demoting a shipped change back to completed is a human decision about
        what actually happened, so it must not be reachable through the tool
        that walks merged Issues.
        """
        repository = self._provisioned_labels()
        by_name = {str(item["name"]): item for item in repository}
        attached = [by_name["type/platform"], by_name["deployed"]]
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, attached, calls)

        with self.assertRaises(BrokerError) as caught:
            broker.execute(
                "aisoft-platform", "gitea.issue.labels.set",
                number=115, lifecycle="completed",
            )
        self.assertEqual(caught.exception.code, "REQUEST_DENIED")
        self.assertEqual([method for method, _, _ in calls if method == "PUT"], [])
        self.assertEqual(
            sorted(str(item["name"]) for item in attached),
            ["deployed", "type/platform"],
        )

        # The guard is specific to that demotion, not to touching a deployed
        # Issue at all: re-asserting deployed still resolves as a no-op.
        repeat = broker.execute(
            "aisoft-platform", "gitea.issue.labels.set",
            number=115, lifecycle="deployed",
        )
        self.assertEqual(repeat["result"], "no-op")

    def test_issue_label_set_is_idempotent(self) -> None:
        """AC-5: already-there is a no-op with no PUT, and repeats are identical."""
        repository = self._provisioned_labels()
        by_name = {str(item["name"]): item for item in repository}
        attached = [by_name["type/docs"], by_name["completed"]]
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, attached, calls)

        first = broker.execute(
            "aisoft-platform", "gitea.issue.labels.set",
            number=115, lifecycle="completed",
        )
        self.assertEqual(first["result"], "no-op")
        self.assertEqual(first["before"], first["after"])
        self.assertEqual([method for method, _, _ in calls if method == "PUT"], [])

        second = broker.execute(
            "aisoft-platform", "gitea.issue.labels.set",
            number=115, lifecycle="completed",
        )
        self.assertEqual(first, second)

        # A second lifecycle label on the same Issue is not a no-op even when
        # the target is already among them: the point of the operation is that
        # the dimension ends up holding exactly one value.
        attached.append(by_name["pr-open"])
        calls.clear()
        converge = broker.execute(
            "aisoft-platform", "gitea.issue.labels.set",
            number=115, lifecycle="completed",
        )
        self.assertEqual(converge["result"], "updated")
        self.assertEqual(
            sorted(str(item["name"]) for item in attached), ["completed", "type/docs"]
        )
        self.assertEqual(len([m for m, _, _ in calls if m == "PUT"]), 1)

    def test_issue_label_classify_projects_both_analyzer_dimensions(self) -> None:
        """#160 AC-1: the analyzer dimensions land, everything else survives.

        The gap this closes is that apply-analysis, the only writer of type/ and
        complexity/, runs inside the Development Loop, so an Issue opened from
        an interactive session carried neither.
        """
        repository = self._provisioned_labels()
        # A project extension label (declared prefix, value not enumerated by
        # the platform) has to survive a dimension replacement.
        repository.append({"id": 900, "name": "area/web", "color": "ededed",
                           "description": "project extension"})
        by_name = {str(item["name"]): item for item in repository}
        attached = [by_name["pr-open"], by_name["triage/ready-for-agent"],
                    by_name["area/web"]]
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, attached, calls)

        value = broker.execute(
            "aisoft-platform", "gitea.issue.labels.classify",
            number=160, change_type="platform", complexity="complex",
        )
        self.assertEqual(value["result"], "updated")
        self.assertEqual(
            value["before"], ["area/web", "pr-open", "triage/ready-for-agent"]
        )
        self.assertEqual(
            value["after"],
            ["area/web", "complexity/complex", "pr-open", "triage/ready-for-agent",
             "type/platform"],
        )
        self.assertEqual(len([m for m, _, _ in calls if m == "PUT"]), 1)

    def test_issue_label_classify_accepts_only_manifest_analyzer_values(self) -> None:
        """#160 AC-2: both dimensions are checked against the installed manifest.

        The values arrive bare, exactly as the summary front matter spells them,
        and the broker namespaces them. A retired value fails here rather than
        being attached, which is the whole reason the check is against canonical
        rather than against the prefix.
        """
        repository = self._provisioned_labels()
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, [], calls)

        for change_type in (
            "bogus",
            "type/platform",   # already namespaced: the caller passes bare values
            "completed",       # a real label, but not this dimension
            "Platform",        # names are exact, not case-insensitive
            "",
        ):
            with self.subTest(change_type=change_type), self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "gitea.issue.labels.classify",
                    number=160, change_type=change_type, complexity="complex",
                )
            self.assertEqual(caught.exception.code, "ARGUMENT_MISMATCH")

        for complexity in ("bogus", "standard", "complexity/small", "Small", ""):
            with self.subTest(complexity=complexity), self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "gitea.issue.labels.classify",
                    number=160, change_type="platform", complexity=complexity,
                )
            self.assertEqual(caught.exception.code, "ARGUMENT_MISMATCH")

        self.assertEqual([method for method, _, _ in calls if method == "PUT"], [])

        # Every change type the manifest declares, against both complexities.
        declared = {
            str(entry["name"]).removeprefix("type/")
            for entry in json.loads(LABELS.read_text())["canonical"]
            if str(entry["name"]).startswith("type/")
        }
        self.assertIn("platform", declared)
        for change_type in sorted(declared):
            for complexity in ("small", "complex"):
                with self.subTest(change_type=change_type, complexity=complexity):
                    broker.execute(
                        "aisoft-platform", "gitea.issue.labels.classify",
                        number=160, change_type=change_type, complexity=complexity,
                    )

    def test_classification_arguments_require_both_dimensions(self) -> None:
        """#160 AC-3: half a classification is not expressible.

        A (type, complexity) pair is one judgement. The typed arguments tuple is
        what enforces it, so there is no code path that writes one dimension and
        leaves the other reading as an older analysis.
        """
        repository = self._provisioned_labels()
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, [], calls)

        for kwargs in (
            {"number": 160, "change_type": "platform"},
            {"number": 160, "complexity": "complex"},
            {"number": 160},
            {"change_type": "platform", "complexity": "complex"},
        ):
            with self.subTest(kwargs=sorted(kwargs)), self.assertRaises(BrokerError) as caught:
                broker.execute("aisoft-platform", "gitea.issue.labels.classify", **kwargs)
            self.assertEqual(caught.exception.code, "ARGUMENT_MISMATCH")

        # And they belong to this operation alone.
        for operation in ("gitea.issue.labels.set", "gitea.issue.labels.read"):
            with self.subTest(operation=operation), self.assertRaises(BrokerError) as extra:
                broker.execute(
                    "aisoft-platform", operation,
                    number=160, lifecycle="completed",
                    change_type="platform", complexity="complex",
                )
            self.assertEqual(extra.exception.code, "ARGUMENT_MISMATCH")

        self.assertEqual(calls, [])

    def test_issue_label_classify_fails_closed_when_the_label_is_not_provisioned(self) -> None:
        """#160 AC-4: attaching is not defining, same rule as the lifecycle write."""
        repository = [
            item for item in self._provisioned_labels()
            if item["name"] != "complexity/complex"
        ]
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, [], calls)

        with self.assertRaises(BrokerError) as caught:
            broker.execute(
                "aisoft-platform", "gitea.issue.labels.classify",
                number=160, change_type="platform", complexity="complex",
            )
        self.assertEqual(caught.exception.code, "TARGET_MISMATCH")
        self.assertIn("gitea.labels.provision", str(caught.exception))
        self.assertEqual([method for method, _, _ in calls if method == "PUT"], [])

    def test_issue_label_classify_is_idempotent_and_converges_the_dimensions(self) -> None:
        """#160 AC-5: no PUT when already right; one PUT when a value is stale.

        The retired complexity/standard is the interesting case. It is not
        writable — the accepted values come from canonical — but an Issue still
        wearing it has to lose it, because the dimension it belongs to is the
        namespace, not the canonical list.
        """
        repository = self._provisioned_labels()
        repository.append({"id": 901, "name": "complexity/standard", "color": "ededed",
                           "description": "retired"})
        by_name = {str(item["name"]): item for item in repository}
        attached = [by_name["type/platform"], by_name["complexity/complex"],
                    by_name["pr-open"]]
        calls: list[tuple] = []
        broker = self._issue_label_broker(repository, attached, calls)

        first = broker.execute(
            "aisoft-platform", "gitea.issue.labels.classify",
            number=160, change_type="platform", complexity="complex",
        )
        self.assertEqual(first["result"], "no-op")
        self.assertEqual(first["before"], first["after"])
        self.assertEqual([method for method, _, _ in calls if method == "PUT"], [])
        self.assertEqual(
            first,
            broker.execute(
                "aisoft-platform", "gitea.issue.labels.classify",
                number=160, change_type="platform", complexity="complex",
            ),
        )

        # Re-projection after the summary was re-judged: one dimension moves,
        # the lifecycle label does not.
        calls.clear()
        rejudged = broker.execute(
            "aisoft-platform", "gitea.issue.labels.classify",
            number=160, change_type="bugfix", complexity="small",
        )
        self.assertEqual(rejudged["result"], "updated")
        self.assertEqual(
            rejudged["after"], ["complexity/small", "pr-open", "type/bugfix"]
        )
        self.assertEqual(len([m for m, _, _ in calls if m == "PUT"]), 1)

        # An Issue carrying the retired value converges onto the current one.
        attached.append(by_name["complexity/standard"])
        calls.clear()
        converged = broker.execute(
            "aisoft-platform", "gitea.issue.labels.classify",
            number=160, change_type="bugfix", complexity="small",
        )
        self.assertEqual(converged["result"], "updated")
        self.assertEqual(
            converged["after"], ["complexity/small", "pr-open", "type/bugfix"]
        )
        self.assertEqual(len([m for m, _, _ in calls if m == "PUT"]), 1)

    def test_analyzer_dimension_write_is_one_typed_operation_per_dimension(self) -> None:
        """#160: the surface stays dimension-shaped, never a label-set write."""
        classify = self.contract.operation("gitea.issue.labels.classify")
        self.assertEqual(classify.identity_route, "project-agent")
        self.assertTrue(classify.mutating)
        self.assertEqual(classify.arguments, ("number", "change_type", "complexity"))

        names = {operation.name for operation in self.contract.operations}
        for absent in (
            "gitea.issue.labels.add",
            "gitea.issue.labels.replace",
            "gitea.issue.labels.triage",
            "gitea.issue.labels.delete",
        ):
            self.assertNotIn(absent, names)
        for operation in self.contract.operations:
            self.assertNotIn("labels", operation.arguments)

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
                "head": {"ref": "change/70-governed-host-writes"},
                "base": {"ref": "main"},
                "merged": False,
            }).encode()

        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
        )
        body = "Closes #70\n\nContract: docs/changes/70-governed-host-writes/summary-governed-host-writes-260809.md"
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
                    "head": "change/70-governed-host-writes",
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
                "head": {"ref": "change/70-governed-host-writes"},
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
            body="Closes #70\n\ndocs/changes/70-governed-host-writes/summary-governed-host-writes-260809.md",
        )
        self.assertEqual(value["number"], 71)
        self.assertEqual(calls, ["GET"])

    def test_pull_create_rejects_legacy_and_conflicting_open_name(self) -> None:
        class FailIfResolved:
            def resolve(self, project, operation):
                raise AssertionError("credential resolution must not run for legacy body")

        legacy = HostAccessBroker(self.contract, credentials=FailIfResolved())
        with self.assertRaises(BrokerError) as caught:
            legacy.execute(
                "aisoft-platform",
                "gitea.pull.create",
                issue=70,
                title="legacy first PR",
                body="Closes #70\n\ndocs/changes/70/00-summary.md",
            )
        self.assertEqual(caught.exception.code, "ARGUMENT_INVALID")

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            if url.endswith("/pulls?state=open&limit=50&page=1"):
                return 200, {}, json.dumps([{
                    "number": 72,
                    "head": {"ref": "change/70-other-change-name"},
                    "base": {"ref": "main"},
                    "merged": False,
                }]).encode()
            raise AssertionError("conflict must stop before PR creation")

        conflict = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
        )
        with self.assertRaises(BrokerError) as caught:
            conflict.execute(
                "aisoft-platform",
                "gitea.pull.create",
                issue=70,
                title="readable first PR",
                body=(
                    "Closes #70\n\n"
                    "docs/changes/70-governed-host-writes/"
                    "summary-governed-host-writes-260809.md"
                ),
            )
        self.assertEqual(caught.exception.code, "CHANGE_NAME_CONFLICT")

    def test_pull_body_contract_is_rejected_before_credentials(self) -> None:
        class FailIfResolved:
            def resolve(self, project, operation):
                raise AssertionError("credential resolution must not run")

        broker = HostAccessBroker(self.contract, credentials=FailIfResolved())
        for body in (
            "docs/changes/70-governed-host-writes/summary-governed-host-writes-260809.md",
            "Closes #70",
            "Closes #71\ndocs/changes/70-governed-host-writes/summary-governed-host-writes-260809.md",
            "Closes #70\ndocs/changes/71/summary-wrong-change-260809.md",
            "Closes #70\nCloses #70\ndocs/changes/70-governed-host-writes/summary-governed-host-writes-260809.md",
            "Closes #70\nother/docs/changes/70-governed-host-writes/summary-governed-host-writes-260809.md",
        ):
            with self.subTest(body=body), self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "gitea.pull.create", issue=70,
                    title="governed write", body=body,
                )
            self.assertEqual(caught.exception.code, "ARGUMENT_INVALID")

    def test_existing_legacy_pull_can_be_updated_from_read_back_evidence(self) -> None:
        calls = []

        def transport(method, url, headers, body):
            if url.endswith("/api/v1/user"):
                return 200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            calls.append((method, url, json.loads(body) if body else None))
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
        value = broker.execute(
            "aisoft-platform",
            "gitea.pull.update",
            number=71,
            issue=70,
            title="maintain historical PR",
            body="Closes #70\n\ndocs/changes/70/00-summary.md",
        )
        self.assertEqual(value["number"], 71)
        self.assertEqual([call[0] for call in calls], ["GET", "PATCH"])

    def test_access_audit_validates_identities_scopes_permissions_protection_and_file_contract(self) -> None:
        seen_commands = []
        protection = {
            "enable_push": False,
            "enable_force_push": False,
            "enable_merge_whitelist": True,
            "merge_whitelist_usernames": ["admin"],
            "enable_status_check": True,
            "status_check_contexts": ["CI / verify (pull_request)"],
            "required_approvals": 0,
            "block_admin_merge_override": True,
        }

        def runner(argv, **kwargs):
            seen_commands.append(list(argv))
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
                return 200, {}, json.dumps(protection).encode()
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
        self.assertEqual(value["credential_store"], {
            "manager_audit": {
                "identity": "aisoft-platform-manager",
                "kind": "protected-file",
                "scope": "platform-manager-audit",
            },
            "manager_mutation": {
                "identity": "aisoft-platform-manager",
                "kind": "protected-file",
                "scope": "platform-manager-mutation",
            },
            "project_agent": {
                "identity": "aisoft-platform-agent",
                "kind": "protected-file",
                "scope": "project:aisoft-platform",
            },
            "directory_mode": "700",
            "file_mode": "600",
            "path_disclosure": "DENIED",
        })
        for field in ("enable_push", "enable_force_push"):
            with self.subTest(field=field, drift="enabled"):
                protection[field] = True
                with self.assertRaises(BrokerError) as caught:
                    broker.execute("aisoft-platform", "host.access.audit")
                self.assertEqual(caught.exception.code, "PROTECTION_MISMATCH")
                protection[field] = False
            with self.subTest(field=field, drift="missing"):
                protection.pop(field)
                with self.assertRaises(BrokerError) as caught:
                    broker.execute("aisoft-platform", "host.access.audit")
                self.assertEqual(caught.exception.code, "PROTECTION_MISMATCH")
                protection[field] = False
        flattened = "\n".join(" ".join(argv) for argv in seen_commands)
        self.assertNotIn("ci-bot", flattened)
        self.assertNotIn("security", flattened)

    def _credential_contract(self, root: Path):
        raw = json.loads(json.dumps(self.contract.raw))
        raw["mac_host"]["credential_root"] = str(root)
        return replace(self.contract, raw=raw)

    @staticmethod
    def _write_credential(root: Path, relative: str, token: str) -> Path:
        root.mkdir(mode=0o700)
        current = root
        parts = Path(relative).parts
        for component in parts[:-1]:
            current /= component
            current.mkdir(mode=0o700)
        target = current / parts[-1]
        target.write_text(token + "\n")
        target.chmod(0o600)
        return target

    def test_credential_resolver_reads_only_fixed_protected_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "credentials"
            target = self._write_credential(
                root, "projects/aisoft-platform/project-agent.token", "sentinel-secret-token"
            )
            resolver = CredentialResolver(
                self._credential_contract(root), expected_uid=os.getuid(),
            )
            credential = resolver.resolve(
                self.contract.project("aisoft-platform"),
                self.contract.operation("gitea.issue.read"),
            )
            self.assertEqual(credential.identity, "aisoft-platform-agent")
            self.assertEqual(credential.token, "sentinel-secret-token")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

    def test_credential_resolver_rejects_file_and_directory_drift_without_secret_leak(self) -> None:
        secret = "sentinel-secret-token"
        cases = (
            "missing", "file-mode", "directory-mode", "symlink", "ancestor-symlink",
            "hardlink", "owner", "multiline",
        )
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                temporary_root = Path(temporary).resolve()
                root = temporary_root / "credentials"
                target = self._write_credential(
                    root, "projects/aisoft-platform/project-agent.token", secret
                )
                contract_root = root
                expected_uid = os.getuid()
                if case == "missing":
                    target.unlink()
                elif case == "file-mode":
                    target.chmod(0o644)
                elif case == "directory-mode":
                    target.parent.chmod(0o755)
                elif case == "symlink":
                    target.unlink()
                    target.symlink_to(Path(temporary) / "elsewhere")
                elif case == "ancestor-symlink":
                    real_parent = temporary_root / "real-parent"
                    real_parent.mkdir(mode=0o700)
                    root.rename(real_parent / "credentials")
                    linked_parent = temporary_root / "linked-parent"
                    linked_parent.symlink_to(real_parent, target_is_directory=True)
                    contract_root = linked_parent / "credentials"
                elif case == "hardlink":
                    os.link(target, Path(temporary) / "second-link")
                elif case == "owner":
                    expected_uid += 1
                elif case == "multiline":
                    target.write_text(secret + "\nsecond-line\n")
                resolver = CredentialResolver(
                    self._credential_contract(contract_root), expected_uid=expected_uid,
                )
                with self.assertRaises(BrokerError) as caught:
                    resolver.resolve(
                        self.contract.project("aisoft-platform"),
                        self.contract.operation("gitea.issue.read"),
                    )
                self.assertNotIn(secret, str(caught.exception))
                self.assertNotIn(str(root), str(caught.exception))

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

    def _temporary_project_checkout_contract(self, project_id: str, checkout: Path):
        project = self.contract.project(project_id)
        replacement = replace(project, mac_checkout=str(checkout))
        projects = tuple(replacement if item.project_id == project.project_id else item
                         for item in self.contract.projects)
        return replace(self.contract, projects=projects)

    def _temporary_checkout_contract(self, checkout: Path):
        return self._temporary_project_checkout_contract("aisoft-platform", checkout)

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

    def test_newemaint_uses_gitea_remote_and_preserves_github_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "repo"
            self._git(["init", "-q", "-b", "main", str(checkout)])
            github = "https://github.com/BenQue/NewEmaint.git"
            gitea = "http://gitea-ci.orb.local:3000/admin/NewEMaint.git"
            self._git(["remote", "add", "origin", github], cwd=checkout)
            self._git(["remote", "add", "gitea", gitea], cwd=checkout)
            contract = self._temporary_project_checkout_contract("newemaint", checkout)
            commands = []

            def runner(argv, *, cwd=None, env=None):
                commands.append(list(argv))
                if argv[:3] == ["git", "fetch", "gitea"]:
                    return subprocess.CompletedProcess(argv, 0, "", "")
                return subprocess.run(
                    list(argv), cwd=cwd, env=env, check=False, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )

            broker = HostAccessBroker(
                contract,
                credentials=StaticCredentials(),
                transport=lambda method, url, headers, body: (
                    200, {}, b'{"login":"newemaint-agent","is_admin":false}'
                ),
                runner=runner,
                invocation_cwd=str(checkout),
            )
            fetched = broker.execute("newemaint", "git.fetch.main")
            fetched_change = broker.execute(
                "newemaint", "git.fetch.change", branch="change/73"
            )
            first = broker.execute("newemaint", "mac.git.bind")
            second = broker.execute("newemaint", "mac.git.bind")

            self.assertEqual(fetched["remote_name"], "gitea")
            self.assertEqual(fetched_change["remote_name"], "gitea")
            self.assertEqual(first["result"], "updated")
            self.assertEqual(second["result"], "no-op")
            self.assertIn([
                "git", "fetch", "gitea",
                "refs/heads/main:refs/remotes/gitea/main",
            ], commands)
            self.assertIn([
                "git", "fetch", "gitea",
                "refs/heads/change/73:refs/remotes/gitea/change/73",
            ], commands)
            self.assertEqual(self._git(["remote", "get-url", "origin"], cwd=checkout), github)
            self.assertEqual(self._git(["remote", "get-url", "gitea"], cwd=checkout), gitea)
            self.assertEqual(
                self._git([
                    "config", "--local", "--get",
                    f"credential.{gitea}.username",
                ], cwd=checkout),
                "newemaint-agent",
            )

    def test_remote_fetch_or_push_url_drift_fails_before_credentials(self) -> None:
        class FailIfResolved:
            def resolve(self, project, operation):
                raise AssertionError("credential resolution must not run")

        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "repo"
            self._git(["init", "-q", "-b", "main", str(checkout)])
            expected = "http://gitea-ci.orb.local:3000/admin/NewEMaint.git"
            self._git(["remote", "add", "origin", "https://github.com/BenQue/NewEmaint.git"], cwd=checkout)
            self._git(["remote", "add", "gitea", expected], cwd=checkout)
            self._git([
                "remote", "set-url", "--add", "--push", "gitea",
                "http://attacker.invalid/admin/NewEMaint.git",
            ], cwd=checkout)
            contract = self._temporary_project_checkout_contract("newemaint", checkout)
            broker = HostAccessBroker(
                contract,
                credentials=FailIfResolved(),
                invocation_cwd=str(checkout),
            )
            before = self._git(["config", "--local", "--list"], cwd=checkout)
            with self.assertRaises(BrokerError) as caught:
                broker.execute("newemaint", "git.fetch.main")
            self.assertEqual(caught.exception.code, "TARGET_MISMATCH")
            self.assertEqual(self._git(["config", "--local", "--list"], cwd=checkout), before)

    def test_onboarding_check_combines_access_remote_and_repo_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "repo"
            self._git(["init", "-q", "-b", "main", str(checkout)])
            remote = "http://gitea-ci.orb.local:3000/admin/aisoft-platform.git"
            self._git(["remote", "add", "origin", remote], cwd=checkout)
            contract = self._temporary_checkout_contract(checkout)
            protection = {
                "enable_push": False,
                "enable_force_push": False,
                "enable_merge_whitelist": True,
                "merge_whitelist_usernames": ["admin"],
                "enable_status_check": True,
                "status_check_contexts": ["CI / verify (pull_request)"],
                "required_approvals": 0,
                "block_admin_merge_override": True,
            }

            def transport(method, url, headers, body):
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
                    return 403, {}, json.dumps({"message": "token scope=" + scopes}).encode()
                if url.endswith("/collaborators/aisoft-platform-manager/permission"):
                    return 200, {}, b'{"permission":"admin"}'
                if url.endswith("/collaborators/aisoft-platform-agent/permission"):
                    return 200, {}, b'{"permission":"write"}'
                if url.endswith("/branch_protections/main"):
                    return 200, {}, json.dumps(protection).encode()
                raise AssertionError(f"unexpected URL: {url}")

            broker = HostAccessBroker(
                contract,
                credentials=StaticCredentials(),
                transport=transport,
                invocation_cwd=str(checkout),
            )
            broker.execute("aisoft-platform", "mac.git.bind")
            config_before = self._git(["config", "--local", "--list"], cwd=checkout)
            value = broker.execute("aisoft-platform", "host.onboarding.check")
            self.assertEqual(value["status"], "PASS")
            self.assertEqual(value["checkout"]["remote_name"], "origin")
            self.assertEqual(value["checkout"]["remote_url"], remote)
            self.assertEqual(value["checkout"]["binding"], "PASS")
            self.assertEqual(value["access"]["status"], "PASS")
            self.assertEqual(self._git(["config", "--local", "--list"], cwd=checkout), config_before)

            self._git([
                "config", "--local", "--replace-all",
                f"credential.{remote}.username", "wrong-agent",
            ], cwd=checkout)
            with self.assertRaises(BrokerError) as caught:
                broker.execute("aisoft-platform", "host.onboarding.check")
            self.assertEqual(caught.exception.code, "ONBOARDING_MISMATCH")

    def test_null_mac_checkout_onboarding_check_is_target_unavailable(self) -> None:
        """`mac_checkout: null` is a complete declaration, not onboarding drift."""

        def transport(method, url, headers, body):
            raise AssertionError("transport must not run")

        self.assertIsNone(self.contract.project("myapp").mac_checkout)
        broker = HostAccessBroker(
            self.contract,
            credentials=StaticCredentials(),
            transport=transport,
        )
        with self.assertRaises(BrokerError) as caught:
            broker.execute("myapp", "host.onboarding.check")
        self.assertEqual(caught.exception.code, "TARGET_UNAVAILABLE")
        self.assertEqual(str(caught.exception), "project has no approved Mac checkout")

    def test_null_mac_checkout_is_decided_before_credentials(self) -> None:
        """The declared absence of a Mac path outranks any credential finding."""

        class FailIfResolved:
            def resolve(self, project, operation):
                raise AssertionError("credential resolution must not run")

        broker = HostAccessBroker(self.contract, credentials=FailIfResolved())
        with self.assertRaises(BrokerError) as caught:
            broker.execute("myapp", "host.onboarding.check")
        self.assertEqual(caught.exception.code, "TARGET_UNAVAILABLE")

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
                if argv[:4] == ["git", "ls-remote", "--heads", "origin"]:
                    return subprocess.CompletedProcess(
                        argv, 0, "a" * 40 + "\trefs/heads/change/70\n", ""
                    )
                if argv[:2] == ["git", "push"]:
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
                "git", "push",
                "--force-with-lease=refs/heads/change/70:" + "a" * 40,
                "origin",
                "refs/heads/change/70:refs/heads/change/70",
            ])
            self.assertEqual(pushes[0][1], os.path.realpath(linked))
            tokens = [token for argv, _cwd, _env in commands for token in argv]
            self.assertNotIn("--force", tokens)
            self.assertNotIn("-f", tokens)
            flattened = "\n".join(" ".join(argv) for argv, _cwd, _env in commands)
            self.assertNotIn(":refs/heads/main", flattened)

    def test_newemaint_push_uses_manifest_gitea_remote(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            canonical, linked = self._linked_change_worktree(temporary)
            self._git(["remote", "rename", "origin", "gitea"], cwd=canonical)
            self._git([
                "remote", "set-url", "gitea",
                "http://gitea-ci.orb.local:3000/admin/NewEMaint.git",
            ], cwd=canonical)
            contract = self._temporary_project_checkout_contract("newemaint", canonical)
            commands = []

            def runner(argv, *, cwd=None, env=None):
                commands.append(list(argv))
                if argv[:3] == ["git", "fetch", "gitea"] or argv[:2] == ["git", "push"]:
                    return subprocess.CompletedProcess(argv, 0, "", "")
                if argv[:4] == ["git", "ls-remote", "--heads", "gitea"]:
                    return subprocess.CompletedProcess(
                        argv, 0, "a" * 40 + "\trefs/heads/change/70\n", ""
                    )
                return subprocess.run(
                    list(argv), cwd=cwd, env=env, check=False, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )

            broker = HostAccessBroker(
                contract,
                credentials=StaticCredentials(),
                transport=lambda method, url, headers, body: (
                    200, {}, b'{"login":"newemaint-agent","is_admin":false}'
                ),
                runner=runner,
                invocation_cwd=str(linked),
            )
            value = broker.execute(
                "newemaint", "git.push.change", branch="change/70"
            )
            self.assertEqual(value["remote_name"], "gitea")
            self.assertIn([
                "git", "fetch", "gitea",
                "refs/heads/main:refs/remotes/gitea/main",
            ], commands)
            self.assertIn([
                "git", "push",
                "--force-with-lease=refs/heads/change/70:" + "a" * 40,
                "gitea",
                "refs/heads/change/70:refs/heads/change/70",
            ], commands)

    def test_readable_first_push_is_allowed_but_conflicting_remote_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            canonical, linked = self._linked_change_worktree(temporary)
            self._git(["branch", "-m", "change/70-readable-change-name"], cwd=linked)
            contract = self._temporary_checkout_contract(canonical)

            pushes: list[list[str]] = []

            def make_broker(remote_output: str):
                def runner(argv, *, cwd=None, env=None):
                    if argv[:3] == ["git", "fetch", "origin"]:
                        return subprocess.CompletedProcess(argv, 0, "", "")
                    if argv[:4] == ["git", "ls-remote", "--heads", "origin"]:
                        return subprocess.CompletedProcess(argv, 0, remote_output, "")
                    if argv[:2] == ["git", "push"]:
                        pushes.append(list(argv))
                        return subprocess.CompletedProcess(argv, 0, "", "")
                    return subprocess.run(
                        list(argv), cwd=cwd, env=env, check=False, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    )

                return HostAccessBroker(
                    contract,
                    credentials=StaticCredentials(),
                    transport=lambda method, url, headers, body: (
                        200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
                    ),
                    runner=runner,
                    invocation_cwd=str(linked),
                )

            value = make_broker("").execute(
                "aisoft-platform",
                "git.push.change",
                branch="change/70-readable-change-name",
            )
            self.assertEqual(value["status"], "PASS")
            self.assertEqual(pushes, [[
                "git", "push",
                "--force-with-lease=refs/heads/change/70-readable-change-name:",
                "origin",
                "refs/heads/change/70-readable-change-name"
                ":refs/heads/change/70-readable-change-name",
            ]])

            conflict = "a" * 40 + "\trefs/heads/change/70-other-change-name\n"
            with self.assertRaises(BrokerError) as caught:
                make_broker(conflict).execute(
                    "aisoft-platform",
                    "git.push.change",
                    branch="change/70-readable-change-name",
                )
            self.assertEqual(caught.exception.code, "CHANGE_NAME_CONFLICT")

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

    LEASE_BRANCH = "change/70-lease-regression-branch"

    def _remote_backed_change_worktree(self, temporary: str):
        """Build a change worktree whose origin is a real bare repository.

        The manifest pins origin to an http URL, so the remote-URL binding check
        must keep seeing that URL. Only the commands that would go over the
        network are redirected onto the bare repo by ``_remote_backed_runner``,
        which leaves git itself in charge of the lease semantics under test.
        """
        remote = Path(temporary) / "remote.git"
        canonical = Path(temporary) / "canonical"
        linked = Path(temporary) / "linked"
        self._git(["init", "-q", "--bare", "-b", "main", str(remote)])
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
        self._git([
            "push", "-q", str(remote), "refs/heads/main:refs/heads/main",
        ], cwd=canonical)
        self._git(["update-ref", "refs/remotes/origin/main", "HEAD"], cwd=canonical)
        self._git([
            "worktree", "add", "-q", "-b", self.LEASE_BRANCH, str(linked),
        ], cwd=canonical)
        (linked / "change.txt").write_text("change 70\n")
        self._git(["add", "change.txt"], cwd=linked)
        self._git(["commit", "-q", "-m", "change 70"], cwd=linked)
        return remote, canonical, linked

    def _remote_backed_runner(self, remote: Path, commands: list, after_ls_remote=None):
        def runner(argv, *, cwd=None, env=None):
            argv = list(argv)
            commands.append(argv)
            if argv[:2] in (["git", "fetch"], ["git", "push"], ["git", "ls-remote"]):
                argv = [str(remote) if token == "origin" else token for token in argv]
            result = subprocess.run(
                argv, cwd=cwd, env=env, check=False, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if after_ls_remote is not None and argv[:2] == ["git", "ls-remote"]:
                after_ls_remote()
            return result

        return runner

    def _remote_backed_broker(self, canonical: Path, linked: Path, runner):
        return HostAccessBroker(
            self._temporary_checkout_contract(canonical),
            credentials=StaticCredentials(),
            transport=lambda method, url, headers, body: (
                200, {}, b'{"login":"aisoft-platform-agent","is_admin":false}'
            ),
            runner=runner,
            invocation_cwd=str(linked),
        )

    def _remote_sha(self, remote: Path, branch: str) -> str:
        line = self._git(["ls-remote", "--heads", str(remote), f"refs/heads/{branch}"])
        return line.split("\t")[0] if line else ""

    def _advance_remote_main(self, remote: Path, canonical: Path, message: str) -> None:
        """Simulate a human merging some other Issue's PR into the protected main."""
        (canonical / f"{message}.md").write_text(f"{message}\n")
        self._git(["add", f"{message}.md"], cwd=canonical)
        self._git(["commit", "-q", "-m", message], cwd=canonical)
        self._git([
            "push", "-q", str(remote), "refs/heads/main:refs/heads/main",
        ], cwd=canonical)

    def test_push_survives_main_advancing_and_a_rebase(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            remote, canonical, linked = self._remote_backed_change_worktree(temporary)
            commands: list = []
            broker = self._remote_backed_broker(
                canonical, linked, self._remote_backed_runner(remote, commands)
            )

            first = broker.execute(
                "aisoft-platform", "git.push.change", branch=self.LEASE_BRANCH
            )
            self.assertEqual(first["status"], "PASS")
            pushed = self._remote_sha(remote, self.LEASE_BRANCH)
            self.assertEqual(pushed, self._git(["rev-parse", "HEAD"], cwd=linked))

            self._advance_remote_main(remote, canonical, "other-issue-merged")
            with self.assertRaises(BrokerError) as stale:
                broker.execute(
                    "aisoft-platform", "git.push.change", branch=self.LEASE_BRANCH
                )
            self.assertEqual(stale.exception.code, "BASE_BRANCH_STALE")

            self._git(["rebase", "-q", "origin/main"], cwd=linked)
            rebased = self._git(["rev-parse", "HEAD"], cwd=linked)
            self.assertNotEqual(rebased, pushed)
            self.assertNotEqual(
                subprocess.run(
                    ["git", "merge-base", "--is-ancestor", pushed, rebased],
                    cwd=linked, check=False,
                ).returncode,
                0,
                "the rebase must make the push a genuine non-fast-forward",
            )

            second = broker.execute(
                "aisoft-platform", "git.push.change", branch=self.LEASE_BRANCH
            )
            self.assertEqual(second["status"], "PASS")
            self.assertEqual(self._remote_sha(remote, self.LEASE_BRANCH), rebased)
            tokens = [token for argv in commands for token in argv]
            self.assertNotIn("--force", tokens)
            self.assertNotIn("-f", tokens)

    def test_remote_branch_moved_after_the_lease_was_read_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            remote, canonical, linked = self._remote_backed_change_worktree(temporary)
            commands: list = []
            broker = self._remote_backed_broker(
                canonical, linked, self._remote_backed_runner(remote, commands)
            )
            broker.execute(
                "aisoft-platform", "git.push.change", branch=self.LEASE_BRANCH
            )

            intruder = Path(temporary) / "intruder"
            self._git(["clone", "-q", "--branch", self.LEASE_BRANCH, str(remote), str(intruder)])
            self._git(["config", "user.name", "Someone Else"], cwd=intruder)
            self._git(["config", "user.email", "someone@example.invalid"], cwd=intruder)
            self._git(["commit", "-q", "--allow-empty", "-m", "written by someone else"], cwd=intruder)

            moved: list = []

            def move_remote_branch() -> None:
                if moved:
                    return
                moved.append(True)
                self._git([
                    "push", "-q", str(remote),
                    f"refs/heads/{self.LEASE_BRANCH}:refs/heads/{self.LEASE_BRANCH}",
                ], cwd=intruder)

            races: list = []
            racing = self._remote_backed_broker(
                canonical,
                linked,
                self._remote_backed_runner(remote, races, after_ls_remote=move_remote_branch),
            )
            leased = self._remote_sha(remote, self.LEASE_BRANCH)
            self._git(["commit", "-q", "--allow-empty", "-m", "local follow-up"], cwd=linked)
            with self.assertRaises(BrokerError) as caught:
                racing.execute(
                    "aisoft-platform", "git.push.change", branch=self.LEASE_BRANCH
                )
            self.assertEqual(caught.exception.code, "REMOTE_BRANCH_MOVED")
            self.assertEqual(
                self._remote_sha(remote, self.LEASE_BRANCH),
                self._git(["rev-parse", "HEAD"], cwd=intruder),
                "the lease must refuse rather than overwrite the other writer",
            )
            self.assertEqual(
                [argv[2] for argv in races if argv[:2] == ["git", "push"]],
                [f"--force-with-lease=refs/heads/{self.LEASE_BRANCH}:{leased}"],
                "the refusal must come from the pre-move lease, not from luck",
            )

    def test_stale_base_branch_is_rejected_before_the_push_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            remote, canonical, linked = self._remote_backed_change_worktree(temporary)
            self._advance_remote_main(remote, canonical, "merged-elsewhere")
            commands: list = []
            broker = self._remote_backed_broker(
                canonical, linked, self._remote_backed_runner(remote, commands)
            )
            with self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "git.push.change", branch=self.LEASE_BRANCH
                )
            self.assertEqual(caught.exception.code, "BASE_BRANCH_STALE")
            self.assertEqual([argv for argv in commands if argv[:2] == ["git", "push"]], [])
            self.assertEqual(self._remote_sha(remote, self.LEASE_BRANCH), "")

    def test_merge_commit_is_rejected_before_the_push_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            remote, canonical, linked = self._remote_backed_change_worktree(temporary)
            self._advance_remote_main(remote, canonical, "merged-elsewhere")
            self._git(["fetch", "-q", str(remote), "refs/heads/main:refs/remotes/origin/main"], cwd=linked)
            self._git(["merge", "-q", "--no-ff", "-m", "merge main", "origin/main"], cwd=linked)
            self.assertEqual(
                subprocess.run(
                    ["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"],
                    cwd=linked, check=False,
                ).returncode,
                0,
                "the merge must clear the base-freshness check so the merge rule is what bites",
            )
            commands: list = []
            broker = self._remote_backed_broker(
                canonical, linked, self._remote_backed_runner(remote, commands)
            )
            with self.assertRaises(BrokerError) as caught:
                broker.execute(
                    "aisoft-platform", "git.push.change", branch=self.LEASE_BRANCH
                )
            self.assertEqual(caught.exception.code, "MERGE_COMMIT_DENIED")
            self.assertEqual([argv for argv in commands if argv[:2] == ["git", "push"]], [])
            self.assertEqual(self._remote_sha(remote, self.LEASE_BRANCH), "")

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
            job=None, lifecycle=None, change_type=None, complexity=None,
        )
        self.assertEqual(json.loads(stdout.getvalue()), {"number": 71})

        # --lifecycle is a typed field like the rest: it reaches execute as a
        # plain string with no path, URL or shell fragment attached, and the
        # broker is the only thing that decides which values are legal (#115).
        lifecycle_argv = [
            "--access-manifest", str(ACCESS),
            "--governance-manifest", str(GOVERNANCE),
            "broker", "--project", "aisoft-platform",
            "--operation", "gitea.issue.labels.set",
            "--number", "115", "--lifecycle", "completed",
        ]
        stdout = io.StringIO()
        with (
            patch.object(HostAccessBroker, "execute", return_value={"result": "updated"}) as execute,
            redirect_stdout(stdout),
        ):
            self.assertEqual(host_access_cli_main(lifecycle_argv), 0)
        execute.assert_called_once_with(
            "aisoft-platform", "gitea.issue.labels.set",
            number=115, state=None, branch=None, issue=None,
            title=None, body=None, comment=None, sha=None, job=None, lifecycle="completed",
            change_type=None, complexity=None,
        )

        # --change-type / --complexity are typed fields on the same terms
        # (#160): bare front matter values, no path, URL or shell fragment, and
        # the broker alone decides which values are legal.
        classify_argv = [
            "--access-manifest", str(ACCESS),
            "--governance-manifest", str(GOVERNANCE),
            "broker", "--project", "aisoft-platform",
            "--operation", "gitea.issue.labels.classify",
            "--number", "160", "--change-type", "platform", "--complexity", "complex",
        ]
        stdout = io.StringIO()
        with (
            patch.object(HostAccessBroker, "execute", return_value={"result": "updated"}) as execute,
            redirect_stdout(stdout),
        ):
            self.assertEqual(host_access_cli_main(classify_argv), 0)
        execute.assert_called_once_with(
            "aisoft-platform", "gitea.issue.labels.classify",
            number=160, state=None, branch=None, issue=None,
            title=None, body=None, comment=None, sha=None, job=None, lifecycle=None,
            change_type="platform", complexity="complex",
        )

        for forbidden in (
            "--url", "--owner", "--repository", "--method", "--raw-body",
            "--remote", "--remote-name", "--refspec", "--command",
        ):
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
        self.assertEqual(first.onboarding_check()["status"], "PASS")
        self.assertEqual([call[0][0] for call in calls], [
            "/usr/local/libexec/aisoft/host-access-broker",
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

    def test_undeclared_profile_bytes_are_byte_identical_to_pre_112_shape(self) -> None:
        self.migrator().apply("newemaint")
        expected = (
            "AISOFT_PROJECT_ID=newemaint\n"
            "GITEA_URL=http://gitea-ci.orb.local:3000\n"
            "GITEA_OWNER=admin\n"
            "GITEA_REPO=NewEMaint\n"
            "GITEA_IDENTITY=newemaint-agent\n"
            f"GITEA_TOKEN_FILE={self.home}/.config/aisoft/credentials/emaintenance.token\n"
            f"AGENT_REPO_DIR={self.home}/work/NewEMaint\n"
            "ANALYSIS_PROVIDER=claude\n"
            "IMPLEMENT_PROVIDER=none\n"
        ).encode("utf-8")
        self.assertEqual(self.profile.read_bytes(), expected)

    def test_declared_path_prepend_is_generated_and_drift_fails_read_back(self) -> None:
        source = self.source / "sfm-board-agent-project-agent.token"
        source.write_text("sfm-project-token\n")
        source.chmod(0o600)
        migrator = self.migrator(identity="sfm-board-agent")
        self.assertEqual(migrator.apply("sfm-digital-board")["result"], "applied")
        profile = self.home / ".config/aisoft/projects/sfm.env"
        content = profile.read_text()
        path_line = "PATH=/opt/node22/bin:/home/coder/.local/bin:$PATH"
        self.assertTrue(content.endswith(f"IMPLEMENT_PROVIDER=none\n{path_line}\n"))
        self.assertEqual(content.count("\nPATH="), 1)
        self.assertEqual(migrator.read_back("sfm-digital-board")["result"], "read-back")
        self.assertEqual(migrator.consume_check("sfm-digital-board")["result"],
                         "consumer-ready")
        self.assertEqual(migrator.apply("sfm-digital-board")["result"], "no-op")

        profile.write_text(content.replace(path_line, "PATH=/usr/bin:$PATH"))
        with self.assertRaises(BrokerError) as caught:
            migrator.read_back("sfm-digital-board")
        self.assertEqual(caught.exception.code, "READ_BACK_MISMATCH")

        profile.write_text(content.replace(f"{path_line}\n", ""))
        with self.assertRaises(BrokerError) as caught:
            migrator.read_back("sfm-digital-board")
        self.assertEqual(caught.exception.code, "READ_BACK_MISMATCH")

    def test_undeclared_project_with_injected_path_line_fails_read_back(self) -> None:
        migrator = self.migrator()
        migrator.apply("newemaint")
        self.profile.write_text(self.profile.read_text() + "PATH=/opt/evil/bin:$PATH\n")
        with self.assertRaises(BrokerError) as caught:
            migrator.read_back("newemaint")
        self.assertEqual(caught.exception.code, "READ_BACK_MISMATCH")

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


class VmProfilePreflightTests(unittest.TestCase):
    """The VM profile tool is installed separately from the Mac broker entrypoint.

    A missing VM installation must be reported as itself, not collapsed into the
    generic HOST_COMMAND_FAILED that every other host failure produces.
    """

    def setUp(self) -> None:
        self.contract = load_access_contract(ACCESS, GOVERNANCE)
        self.tool = self.contract.raw["mac_host"]["vm_profile_tool"]

    def _broker(self, runner):
        return HostAccessBroker(
            self.contract, credentials=StaticCredentials(), runner=runner
        )

    @staticmethod
    def _completed(argv, returncode, stdout="", stderr=""):
        return subprocess.CompletedProcess(list(argv), returncode, stdout, stderr)

    def _recording_runner(
        self, *, probe_rc: int, run_rc: int = 0, stdout: str = "", stderr: str = ""
    ):
        calls: list[list[str]] = []

        def runner(argv, *, cwd=None, env=None):
            calls.append(list(argv))
            if "/usr/bin/test" in argv:
                return self._completed(argv, probe_rc)
            return self._completed(argv, run_rc, stdout, stderr)

        return runner, calls

    def test_missing_vm_tool_is_reported_as_itself(self) -> None:
        runner, calls = self._recording_runner(probe_rc=1)
        with self.assertRaises(BrokerError) as caught:
            self._broker(runner).execute("newemaint", "vm.profile.read-back")
        self.assertEqual(caught.exception.code, "VM_TOOL_UNAVAILABLE")
        self.assertNotEqual(caught.exception.code, "HOST_COMMAND_FAILED")
        # The probe short-circuits: the privileged sudo invocation never runs.
        self.assertEqual(len(calls), 1)
        self.assertIn("/usr/bin/test", calls[0])
        self.assertNotIn("/usr/bin/sudo", calls[0])

    def test_missing_vm_tool_message_leaks_no_command_output(self) -> None:
        def runner(argv, *, cwd=None, env=None):
            return self._completed(argv, 1, "")

        with self.assertRaises(BrokerError) as caught:
            self._broker(runner).execute("newemaint", "vm.profile.plan")
        message = str(caught.exception)
        self.assertIn("install-host-access-broker.sh", message)
        for secret in ("token", "GITEA_TOKEN", "command not found", "sudo:"):
            self.assertNotIn(secret, message)

    def test_present_vm_tool_returns_payload(self) -> None:
        payload = {"project": "newemaint", "action": "read-back", "status": "PASS"}
        runner, calls = self._recording_runner(probe_rc=0, stdout=json.dumps(payload))
        result = self._broker(runner).execute("newemaint", "vm.profile.read-back")
        self.assertEqual(result["project"], "newemaint")
        # Probe first, then the real invocation.
        self.assertEqual(len(calls), 2)
        self.assertIn("/usr/bin/test", calls[0])
        self.assertIn("/usr/bin/sudo", calls[1])
        self.assertIn("read-back", calls[1])

    def test_present_vm_tool_execution_failure_stays_host_command_failed(self) -> None:
        runner, _ = self._recording_runner(probe_rc=0, run_rc=1)
        with self.assertRaises(BrokerError) as caught:
            self._broker(runner).execute("newemaint", "vm.profile.read-back")
        self.assertEqual(caught.exception.code, "HOST_COMMAND_FAILED")

    def test_profile_tool_governed_error_is_surfaced(self) -> None:
        tool_error = {
            "code": "READ_BACK_MISMATCH",
            "message": "profile read-back bytes mismatch",
            "status": "BLOCKED_EXTERNAL",
        }
        # The tool writes its error contract to stderr and leaves stdout empty.
        runner, _ = self._recording_runner(
            probe_rc=0, run_rc=1, stderr=json.dumps(tool_error)
        )
        with self.assertRaises(BrokerError) as caught:
            self._broker(runner).execute("newemaint", "vm.profile.read-back")
        self.assertEqual(caught.exception.code, "READ_BACK_MISMATCH")

    def test_malformed_profile_tool_error_fails_closed(self) -> None:
        for payload in (
            {"code": "lowercase", "message": "x"},
            {"code": "OK", "message": "too short a code"},
            {"code": "VALID_CODE", "message": ""},
            {"code": "VALID_CODE", "message": "multi\nline"},
            {"code": "VALID_CODE", "message": "x" * 201},
            {"code": "VALID_CODE"},
            ["not", "a", "dict"],
        ):
            with self.subTest(payload=payload):
                runner, _ = self._recording_runner(
                    probe_rc=0, run_rc=1, stderr=json.dumps(payload)
                )
                with self.assertRaises(BrokerError) as caught:
                    self._broker(runner).execute("newemaint", "vm.profile.read-back")
                self.assertEqual(caught.exception.code, "HOST_COMMAND_FAILED")

    def test_non_json_stderr_on_failure_fails_closed(self) -> None:
        runner, _ = self._recording_runner(
            probe_rc=0, run_rc=1, stderr="sudo: a raw diagnostic line"
        )
        with self.assertRaises(BrokerError) as caught:
            self._broker(runner).execute("newemaint", "vm.profile.read-back")
        self.assertEqual(caught.exception.code, "HOST_COMMAND_FAILED")
        self.assertNotIn("sudo", str(caught.exception))

    def test_present_vm_tool_target_mismatch_is_unchanged(self) -> None:
        runner, _ = self._recording_runner(
            probe_rc=0, stdout=json.dumps({"project": "hsdb"})
        )
        with self.assertRaises(BrokerError) as caught:
            self._broker(runner).execute("newemaint", "vm.profile.read-back")
        self.assertEqual(caught.exception.code, "TARGET_MISMATCH")

    def test_present_vm_tool_invalid_json_is_unchanged(self) -> None:
        runner, _ = self._recording_runner(probe_rc=0, stdout="not json")
        with self.assertRaises(BrokerError) as caught:
            self._broker(runner).execute("newemaint", "vm.profile.read-back")
        self.assertEqual(caught.exception.code, "RESPONSE_SCHEMA_INVALID")

    def test_project_without_vm_profile_never_probes(self) -> None:
        calls: list[list[str]] = []

        def runner(argv, *, cwd=None, env=None):
            calls.append(list(argv))
            return self._completed(argv, 0)

        with self.assertRaises(BrokerError) as caught:
            self._broker(runner).execute("myapp", "vm.profile.read-back")
        self.assertEqual(caught.exception.code, "TARGET_UNAVAILABLE")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
