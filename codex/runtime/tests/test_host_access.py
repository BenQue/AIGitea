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

    def test_manifest_fixed_remote_defaults_and_rejects_unsafe_names(self) -> None:
        gitea_remote_projects = {"newemaint", "rsdesign-new", "sfm-digital-board"}
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
        for project_id in ("newemaint", "hsdb", "rsdesign-new"):
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
            "sfm-digital-board": ["/opt/node22/bin", "/home/coder/.local/bin"],
            "newemaint": None,
            "hsdb": None,
            "rsdesign-new": None,
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
            "enable_status_check": False,
            "status_check_contexts": [],
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
                "enable_status_check": False,
                "status_check_contexts": [],
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
                if argv[:3] in (["git", "fetch", "gitea"], ["git", "push", "gitea"]):
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
                "git", "push", "gitea",
                "refs/heads/change/70:refs/heads/change/70",
            ], commands)

    def test_readable_first_push_is_allowed_but_conflicting_remote_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            canonical, linked = self._linked_change_worktree(temporary)
            self._git(["branch", "-m", "change/70-readable-change-name"], cwd=linked)
            contract = self._temporary_checkout_contract(canonical)

            def make_broker(remote_output: str):
                def runner(argv, *, cwd=None, env=None):
                    if argv[:3] == ["git", "fetch", "origin"]:
                        return subprocess.CompletedProcess(argv, 0, "", "")
                    if argv[:4] == ["git", "ls-remote", "--heads", "origin"]:
                        return subprocess.CompletedProcess(argv, 0, remote_output, "")
                    if argv[:3] == ["git", "push", "origin"]:
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
            lifecycle=None,
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
            title=None, body=None, comment=None, sha=None, lifecycle="completed",
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
