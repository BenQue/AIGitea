from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any

from aisoft_gitea_governance.client import ApiError
from aisoft_gitea_governance.cli import _read_token
from aisoft_gitea_governance.contract import ContractError, load_contract
from aisoft_gitea_governance.reconcile import (
    apply_repository,
    audit_cross_project_writes,
    capture_snapshot,
    desired_protection,
    planned_actions,
    rollback_repository,
)
from aisoft_gitea_governance.service_policy import read_policy, render_policy


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "codex/config/gitea-governance.json"


class FakeClient:
    def __init__(self, contract):
        self.contract = contract
        self.authenticated = contract.platform_manager
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []
        self.users = {
            contract.human_merge_identity: {"login": contract.human_merge_identity, "is_admin": True},
            contract.platform_manager: {"login": contract.platform_manager, "is_admin": False},
        }
        self.repos: dict[str, dict[str, Any]] = {}
        self.collaborators: dict[str, dict[str, str]] = {}
        self.protections: dict[str, dict[str, Any] | None] = {}
        for repository in contract.repositories:
            full_name = contract.full_name(repository)
            self.users[repository.project_agent] = {
                "login": repository.project_agent,
                "is_admin": False,
            }
            self.repos[full_name] = {
                "full_name": full_name,
                "private": repository.private,
                "default_branch": "main",
                "default_delete_branch_after_merge": True,
            }
            self.collaborators[full_name] = {
                contract.platform_manager: "admin",
                repository.project_agent: "write",
                contract.shared_bot: "write",
            }
            self.protections[full_name] = desired_protection(contract, repository, None)

    def _full_name(self, path: str) -> str:
        parts = path.split("?")[0].split("/")
        return f"{parts[2]}/{parts[3]}"

    def get(self, path: str, operation: str):
        self.calls.append(("GET", path, None))
        if path == "/user":
            return copy.deepcopy(self.users[self.authenticated])
        if path.startswith("/users/"):
            username = path.split("/")[2]
            if username not in self.users:
                raise ApiError(operation, 404)
            return copy.deepcopy(self.users[username])
        full_name = self._full_name(path)
        if "/collaborators?" in path:
            return [{"login": username} for username in self.collaborators[full_name]]
        if "/collaborators/" in path and path.endswith("/permission"):
            username = path.split("/collaborators/", 1)[1].rsplit("/permission", 1)[0]
            if username not in self.collaborators[full_name]:
                raise ApiError(operation, 404)
            return {"permission": self.collaborators[full_name][username]}
        if "/branch_protections/" in path:
            value = self.protections[full_name]
            if value is None:
                raise ApiError(operation, 404)
            return copy.deepcopy(value)
        return copy.deepcopy(self.repos[full_name])

    def put(self, path: str, payload: dict[str, Any], operation: str):
        self.calls.append(("PUT", path, copy.deepcopy(payload)))
        full_name = self._full_name(path)
        username = path.split("/collaborators/", 1)[1]
        self.collaborators[full_name][username] = payload["permission"]

    def patch(self, path: str, payload: dict[str, Any], operation: str):
        self.calls.append(("PATCH", path, copy.deepcopy(payload)))
        full_name = self._full_name(path)
        if "/branch_protections/" in path:
            self.protections[full_name] = copy.deepcopy(payload)
        else:
            self.repos[full_name].update(payload)

    def post(self, path: str, payload: dict[str, Any], operation: str):
        self.calls.append(("POST", path, copy.deepcopy(payload)))
        full_name = self._full_name(path)
        self.protections[full_name] = copy.deepcopy(payload)

    def delete(self, path: str, operation: str):
        self.calls.append(("DELETE", path, None))
        full_name = self._full_name(path)
        if "/branch_protections/" in path:
            self.protections[full_name] = None
            return
        username = path.split("/collaborators/", 1)[1]
        if username not in self.collaborators[full_name]:
            raise ApiError(operation, 404)
        del self.collaborators[full_name][username]


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract(MANIFEST)

    def _write_mutation(self, mutation) -> Path:
        raw = copy.deepcopy(self.contract.raw)
        mutation(raw)
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        json.dump(raw, handle)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_manifest_is_exact_and_private_by_default(self):
        self.assertEqual(len(self.contract.repositories), 9)
        self.assertEqual(
            self.contract.raw["repository_policy"]["public_allowlist"],
            ["admin/aisoft-platform", "admin/myapp", "admin/smoke-test"],
        )
        private = {
            repository.name
            for repository in self.contract.repositories
            if repository.private
        }
        self.assertEqual(private, {
            "HSDB", "NewEMaint", "rsdesign-new", "SapTableMigrate",
            "SFMDigitalBoard", "WMPDA",
        })

    def test_rejects_implicit_public_repository(self):
        path = self._write_mutation(
            lambda raw: raw["repositories"][1].update({
                "classification": "public-test",
                "visibility": "public",
            })
        )
        with self.assertRaisesRegex(ContractError, "public_allowlist"):
            load_contract(path)

    def test_rejects_project_agent_reuse(self):
        path = self._write_mutation(
            lambda raw: raw["repositories"][1].update({
                "project_agent": raw["repositories"][0]["project_agent"]
            })
        )
        with self.assertRaisesRegex(ContractError, "reused"):
            load_contract(path)

    def test_rejects_manager_site_admin(self):
        path = self._write_mutation(
            lambda raw: raw["platform_manager"].update({"site_admin": True})
        )
        with self.assertRaisesRegex(ContractError, "must not be a site admin"):
            load_contract(path)

    def test_token_file_requires_narrow_mode_and_raw_value(self):
        with tempfile.TemporaryDirectory() as directory:
            token_path = Path(directory) / "token"
            token_path.write_text("safe-token\n", encoding="utf-8")
            token_path.chmod(0o600)
            self.assertEqual(_read_token(str(token_path)), "safe-token")
            token_path.chmod(0o644)
            with self.assertRaisesRegex(ContractError, "mode"):
                _read_token(str(token_path))


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract(MANIFEST)
        self.repository = self.contract.repository("rsdesign-new")
        self.client = FakeClient(self.contract)

    def test_desired_protection_preserves_reviews_and_blocks_merge_bypass(self):
        current = desired_protection(self.contract, self.repository, None)
        current.update({
            "block_on_rejected_reviews": True,
            "protected_file_patterns": "release/**",
            "approvals_whitelist_username": ["reviewer"],
        })
        desired = desired_protection(self.contract, self.repository, current)
        self.assertTrue(desired["block_on_rejected_reviews"])
        self.assertEqual(desired["protected_file_patterns"], "release/**")
        self.assertEqual(desired["approvals_whitelist_username"], ["reviewer"])
        self.assertFalse(desired["enable_push"])
        self.assertFalse(desired["enable_force_push"])
        self.assertTrue(desired["enable_merge_whitelist"])
        self.assertEqual(desired["merge_whitelist_usernames"], ["admin"])
        self.assertTrue(desired["block_admin_merge_override"])

    def test_plan_detects_visibility_agent_and_protection_drift(self):
        full_name = self.contract.full_name(self.repository)
        self.client.repos[full_name]["private"] = False
        self.client.repos[full_name]["default_delete_branch_after_merge"] = False
        del self.client.collaborators[full_name][self.repository.project_agent]
        self.client.protections[full_name]["enable_merge_whitelist"] = False
        snapshot = capture_snapshot(self.client, self.contract, self.repository)
        plan = planned_actions(self.contract, self.repository, snapshot)
        self.assertEqual(plan["blockers"], [])
        self.assertEqual(set(plan["planned_actions"]), {
            "set-project-agent-write",
            "set-private",
            "enable-delete-branch-after-merge",
            "update-main-protection",
        })

    def test_status_context_drift_blocks_apply(self):
        full_name = self.contract.full_name(self.repository)
        self.client.protections[full_name]["status_check_contexts"] = ["wrong"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ContractError, "protection drift"):
                apply_repository(self.client, self.contract, self.repository, Path(directory))

    def test_apply_converges_and_second_run_is_noop(self):
        full_name = self.contract.full_name(self.repository)
        self.client.repos[full_name]["private"] = False
        self.client.repos[full_name]["default_delete_branch_after_merge"] = False
        del self.client.collaborators[full_name][self.repository.project_agent]
        self.client.protections[full_name]["enable_merge_whitelist"] = False
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            result = apply_repository(self.client, self.contract, self.repository, Path(first))
            self.assertEqual(result["result"], "applied")
            protection_patches = [
                payload
                for method, path, payload in self.client.calls
                if method == "PATCH" and "/branch_protections/" in path
            ]
            self.assertTrue(protection_patches)
            self.assertNotIn("rule_name", protection_patches[-1])
            result = apply_repository(self.client, self.contract, self.repository, Path(second))
            self.assertEqual(result["result"], "no-op")
            self.assertEqual(oct((Path(first) / "rsdesign-new-pre.json").stat().st_mode & 0o777),
                             "0o600")

    def test_cross_project_write_is_reported_and_blocks_apply(self):
        other = self.contract.repository("HSDB")
        self.client.collaborators[self.contract.full_name(other)][
            self.repository.project_agent
        ] = "write"
        violations = audit_cross_project_writes(self.client, self.contract)
        self.assertEqual(violations, [{
            "repository": "admin/HSDB",
            "project_agent": self.repository.project_agent,
            "permission": "write",
        }])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ContractError, "cross-project"):
                apply_repository(self.client, self.contract, self.repository, Path(directory))

    def test_rollback_restores_private_collaborators_and_missing_protection(self):
        full_name = self.contract.full_name(self.repository)
        self.client.repos[full_name]["private"] = False
        self.client.repos[full_name]["default_delete_branch_after_merge"] = False
        del self.client.collaborators[full_name][self.repository.project_agent]
        self.client.protections[full_name] = None
        snapshot = capture_snapshot(self.client, self.contract, self.repository)
        self.client.repos[full_name]["private"] = True
        self.client.repos[full_name]["default_delete_branch_after_merge"] = True
        self.client.collaborators[full_name][self.repository.project_agent] = "write"
        self.client.protections[full_name] = desired_protection(self.contract, self.repository, None)
        result = rollback_repository(self.client, self.contract, self.repository, snapshot)
        self.assertEqual(result["result"], "rollback-applied")
        self.assertFalse(self.client.repos[full_name]["private"])
        self.assertFalse(self.client.repos[full_name]["default_delete_branch_after_merge"])
        self.assertNotIn(self.repository.project_agent, self.client.collaborators[full_name])
        self.assertIsNone(self.client.protections[full_name])


class ServicePolicyTests(unittest.TestCase):
    def test_render_changes_only_target_policy_and_preserves_unrelated_values(self):
        contract = load_contract(MANIFEST)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "app.ini"
            output = Path(directory) / "candidate.ini"
            source.write_text(
                "[database]\nPASSWD = value-with-#-and-;\n\n"
                "[service]\nDISABLE_REGISTRATION = false\n\n"
                "[repository]\nDEFAULT_PRIVATE = last\nFORCE_PRIVATE = false\n",
                encoding="utf-8",
            )
            render_policy(source, output, contract.raw["server_policy"])
            self.assertEqual(read_policy(output), contract.raw["server_policy"])
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("PASSWD = value-with-#-and-;", rendered)
            self.assertIn("REQUIRE_SIGNIN_VIEW = false", rendered)

    def test_duplicate_target_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "app.ini"
            source.write_text(
                "[service]\nDISABLE_REGISTRATION = false\nDISABLE_REGISTRATION = true\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "duplicate"):
                read_policy(source)


if __name__ == "__main__":
    unittest.main()
