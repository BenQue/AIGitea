from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aisoft_host_access.broker import (
    BrokerError,
    CredentialResolver,
    HostAccessBroker,
    ResolvedCredential,
    credential_from_protocol,
)
from aisoft_host_access.contract import AccessContractError, load_access_contract
from aisoft_host_access.profiles import ProfileMigrator


ROOT = Path(__file__).resolve().parents[3]
ACCESS = ROOT / "codex/config/host-access-broker.json"
GOVERNANCE = ROOT / "codex/config/gitea-governance.json"


class StaticCredentials:
    def __init__(self, *, mismatch: bool = False) -> None:
        self.mismatch = mismatch

    def resolve(self, project, operation):
        if operation.identity_route == "manager-audit":
            return ResolvedCredential("aisoft-platform-manager", "token-manager")
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
