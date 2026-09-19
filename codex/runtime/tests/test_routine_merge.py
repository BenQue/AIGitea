import base64
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse

from aisoft_host_access.broker import (
    BrokerError, HostAccessBroker, ResolvedCredential,
)
from aisoft_host_access.contract import load_access_contract
from aisoft_loop.routine_merge import evaluate_routine_eligibility


ROOT = Path(__file__).parents[2]


def newemaint_required_contexts() -> list[str]:
    """What this platform declares as NewEMaint's required contexts.

    The merge gate compares the live protection against the manifest and then
    demands every one of these contexts be successful at the exact head, so a
    fixture that hand-copies the strings stops standing for the live protection
    the moment a project gains a required context (#312).
    """
    raw = json.loads(
        (ROOT / "config/gitea-governance.json").read_text(encoding="utf-8")
    )
    entry = next(
        item for item in raw["repositories"] if item["name"] == "NewEMaint"
    )
    return list(entry["status_check_contexts"])


def routine_token_scopes() -> list[str]:
    """What this platform declares as the routine merger PAT scopes.

    Gitea gates every `/api/v1/user` request behind the user scope category, and
    the broker verifies the routine identity there before it probes scopes at
    all. A fixture that hand-writes the scope string can therefore describe a
    token that passes here and is rejected by the real server, which is exactly
    how the manifest kept a scope set that could never pass its own identity
    gate (#313). Reading the manifest keeps the contradiction visible.
    """
    raw = json.loads(
        (ROOT / "config/gitea-governance.json").read_text(encoding="utf-8")
    )
    return list(raw["routine_merge_agent_policy"]["token_scopes"])



def extended_permission(identity: str, permission: str) -> dict[str, object]:
    return {
        "permission": permission,
        "role_name": permission,
        "user": {
            "login": identity,
            "username": identity,
            "is_admin": False,
        },
    }


class SessionContractTests(unittest.TestCase):
    def test_codex_and_claude_keep_only_contract_start_and_pr_confirmations(self):
        codex = (ROOT / "skills/issue-session-flow/SKILL.md").read_text(encoding="utf-8")
        claude = (ROOT.parent / "skill-for-claude/issue-session-flow/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("contract/start confirmation", codex)
        self.assertIn("final-PR submission confirmation", codex)
        self.assertIn("## 确认点 1：合同/启动", claude)
        self.assertIn("## 确认点 2：准备提交最终 PR", claude)
        marker = (
            "当前合同内 CI 修复可继续，最终 head 的 required CI 全绿且全部硬门通过后，"
            "允许受控自动合并。"
        )
        self.assertIn(marker, codex)
        self.assertIn(marker, claude)
        for content in (codex, claude):
            self.assertNotIn("是否确认归档", content)
            self.assertNotIn("confirm archival", content)


class EligibilityTests(unittest.TestCase):
    def eligible(self, **overrides):
        values = {
            "issue_number": 44,
            "change_type": "bugfix",
            "effective_complexity": "small",
            "contract_effect": "restore",
            "local_scope": True,
            "reversible": True,
            "risk_flags": (),
            "major": False,
            "phase_or_milestone_completion": False,
            "repository_classification": "internal-application",
            "repository_opt_in": True,
            "required_contexts": ("CI / test (pull_request)",),
        }
        values.update(overrides)
        return evaluate_routine_eligibility(**values)

    def test_positive_and_manual_failure_matrix(self):
        self.assertTrue(self.eligible().eligible)
        failures = (
            {"issue_number": 208},
            {"change_type": "feature"},
            {"change_type": "security"},
            {"change_type": "data"},
            {"change_type": "platform"},
            {"effective_complexity": "complex"},
            {"contract_effect": "change"},
            {"local_scope": False},
            {"reversible": False},
            {"risk_flags": ("security",)},
            {"risk_flags": ("data-migration",)},
            {"risk_flags": ("shared-core",)},
            {"risk_flags": ("cross-module",)},
            {"risk_flags": ("ci-change",)},
            {"risk_flags": ("artifact",)},
            {"risk_flags": ("deployment",)},
            {"risk_flags": ("rollback",)},
            {"risk_flags": ("agent-governance",)},
            {"major": True},
            {"phase_or_milestone_completion": True},
            {"repository_classification": "public-platform"},
            {"repository_opt_in": False},
            {"required_contexts": ()},
        )
        for mutation in failures:
            with self.subTest(mutation=mutation):
                self.assertFalse(self.eligible(**mutation).eligible)


class StaticRoutineCredential:
    def resolve(self, project, operation):
        return ResolvedCredential(project.routine_merge_agent, "routine-token")


class RoutineBrokerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.governance = root / "governance.json"
        self.governance.write_bytes(
            (ROOT / "config/gitea-governance.json").read_bytes()
        )
        self.access = root / "access.json"
        self.access.write_bytes((ROOT / "config/host-access-broker.json").read_bytes())
        self.contract = load_access_contract(self.access, self.governance)
        self.sha = "a" * 40
        self.issue = 74
        self.branch = "change/74-fix-parser-bug"
        self.summary_path = (
            "docs/changes/74-fix-parser-bug/summary-fix-parser-bug-260826.md"
        )
        self.summary = f"""---
issue: 74
change_type: bugfix
requested_complexity: auto
assessed_complexity: small
effective_complexity: small
contract_effect: restore
risk_flags: []
depends_on: []
branch: {self.branch}
---
"""
        self.body = (
            f"Closes #74\n\n"
            f"AISoft-Submit-Authorization: issue=74; branch={self.branch}; policy=routine-auto\n\n"
            f"Change documents:\n- {self.summary_path}\n"
        )
        self.posts = []

    def tearDown(self):
        self.temporary.cleanup()

    def transport(self, method, url, headers, body):
        path = urlparse(url).path
        query = urlparse(url).query
        scopes = routine_token_scopes()
        if path == "/api/v1/user":
            # Gitea answers a missing scope category with 403, not 401 (#313).
            if "read:user" not in scopes and "write:user" not in scopes:
                return self.response({
                    "message": (
                        "token does not have at least one of required scope(s), "
                        "token scope=" + ",".join(scopes)
                    ),
                }, status=403)
            return self.response({"login": "newemaint-routine-merger", "is_admin": False})
        if path == "/api/v1/notifications":
            return self.response({
                "message": (
                    "token does not have required scope, "
                    "token scope=" + ",".join(scopes)
                ),
            }, status=403)
        if path.endswith("/pulls/7/merge"):
            self.posts.append((method, json.loads(body)))
            return self.response({"sha": "b" * 40})
        if path.endswith("/pulls/7"):
            return self.response(self.pull())
        if path.endswith("/contents/" + self.summary_path):
            self.assertEqual(query, "ref=" + self.sha)
            return self.response({
                "encoding": "base64",
                "content": base64.b64encode(self.summary.encode()).decode(),
            })
        if path.endswith("/issues/74"):
            return self.response({
                "number": 74,
                "state": "open",
                "labels": [
                    {"name": "type/bugfix"},
                    {"name": "complexity/small"},
                    {"name": "pr-open"},
                ],
            })
        if path.endswith("/pulls"):
            return self.response([self.pull()])
        if path.endswith("/branch_protections/main"):
            return self.response({
                "enable_push": False,
                "enable_push_whitelist": False,
                "push_whitelist_usernames": [],
                "push_whitelist_teams": [],
                "push_whitelist_deploy_keys": False,
                "enable_force_push": False,
                "enable_force_push_allowlist": False,
                "force_push_allowlist_usernames": [],
                "force_push_allowlist_teams": [],
                "force_push_allowlist_deploy_keys": False,
                "enable_merge_whitelist": True,
                "merge_whitelist_usernames": ["admin", "newemaint-routine-merger"],
                "enable_status_check": True,
                "status_check_contexts": newemaint_required_contexts(),
                "required_approvals": 0,
                "block_admin_merge_override": True,
            })
        if path.endswith("/collaborators/newemaint-routine-merger/permission"):
            return self.response(extended_permission(
                "newemaint-routine-merger", "write"
            ))
        if path.endswith("/commits/" + self.sha + "/status"):
            return self.response({"statuses": [
                {"context": context, "status": "success"}
                for context in newemaint_required_contexts()
            ]})
        if path.endswith("/pulls/7/reviews"):
            return self.response([])
        if path.endswith("/pulls/7/files"):
            return self.response([{"filename": "src/parser.py", "status": "modified"}])
        raise AssertionError((method, url, body))

    @staticmethod
    def response(value, status=200):
        return status, {"content-type": "application/json"}, json.dumps(value).encode()

    def pull(self, *, sha=None):
        return {
            "number": 7,
            "state": "open",
            "merged": False,
            "body": self.body,
            "head": {"ref": self.branch, "sha": sha or self.sha},
            "base": {"ref": "main"},
        }

    def broker(self, transport=None):
        return HostAccessBroker(
            self.contract,
            credentials=StaticRoutineCredential(),
            transport=transport or self.transport,
        )

    def test_exact_payload_one_post_and_receipt(self):
        result = self.broker().execute(
            "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha
        )
        self.assertEqual(result["status"], "AUTO_MERGED")
        self.assertEqual(len(self.posts), 1)
        method, payload = self.posts[0]
        self.assertEqual(method, "POST")
        self.assertEqual(payload, {
            "do": "merge",
            "head_commit_id": self.sha,
            "force_merge": False,
            "merge_when_checks_succeed": False,
            "delete_branch_after_merge": True,
        })

    def test_extended_permission_user_schema_fails_closed_before_merge_post(self):
        def invalid_transport(method, url, headers, body):
            path = urlparse(url).path
            if path.endswith(
                "/collaborators/newemaint-routine-merger/permission"
            ):
                payload = extended_permission(
                    "newemaint-routine-merger", "write"
                )
                payload["user"] = {**payload["user"], "unknown": True}
                return self.response(payload)
            return self.transport(method, url, headers, body)

        with self.assertRaises(BrokerError) as caught:
            self.broker(transport=invalid_transport).execute(
                "newemaint",
                "gitea.pull.merge.routine",
                number=7,
                sha=self.sha,
            )
        self.assertEqual(caught.exception.code, "RESPONSE_SCHEMA_INVALID")
        self.assertEqual(self.posts, [])

    def test_head_drift_is_first_stable_failure_and_zero_post(self):
        def drift(method, url, headers, body):
            path = urlparse(url).path
            if path.endswith("/pulls/7"):
                return self.response(self.pull(sha="c" * 40))
            return self.transport(method, url, headers, body)

        with self.assertRaises(BrokerError) as caught:
            self.broker(drift).execute(
                "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha
            )
        self.assertEqual(caught.exception.code, "ROUTINE_HEAD_DRIFT")
        self.assertEqual(self.posts, [])

    def test_exact_scope_is_required_before_any_merge_post(self):
        scenarios = (
            (200, {"ok": True}),
            (403, {"message": "token scope=read:repository"}),
            (403, {"message": "token scope=write:repository"}),
            (403, {"message": "token scope=write:repository,read:user,read:issue"}),
            (403, {"message": "scope evidence missing"}),
        )
        for status, value in scenarios:
            with self.subTest(status=status, value=value):
                self.posts.clear()

                def unsafe_scope(method, url, headers, body, *, status=status, value=value):
                    if urlparse(url).path == "/api/v1/notifications":
                        return self.response(value, status=status)
                    return self.transport(method, url, headers, body)

                with self.assertRaises(BrokerError) as caught:
                    self.broker(unsafe_scope).execute(
                        "newemaint", "gitea.pull.merge.routine",
                        number=7, sha=self.sha,
                    )
                self.assertEqual(caught.exception.code, "ROUTINE_TOKEN_SCOPE_MISMATCH")
                self.assertEqual(self.posts, [])

    def test_routine_identity_requires_is_admin_exact_false_before_post(self):
        for unsafe in (None, True, 0, "false", []):
            with self.subTest(is_admin=unsafe):
                self.posts.clear()

                def identity_drift(method, url, headers, body, *, unsafe=unsafe):
                    if urlparse(url).path == "/api/v1/user":
                        value = {"login": "newemaint-routine-merger"}
                        if unsafe is not None:
                            value["is_admin"] = unsafe
                        return self.response(value)
                    return self.transport(method, url, headers, body)

                with self.assertRaises(BrokerError) as caught:
                    self.broker(identity_drift).execute(
                        "newemaint", "gitea.pull.merge.routine",
                        number=7, sha=self.sha,
                    )
                self.assertEqual(caught.exception.code, "IDENTITY_MISMATCH")
                self.assertEqual(self.posts, [])

    def test_pilot_rejects_every_non_canary_issue_with_zero_post(self):
        original_body = self.body
        self.body = self.body.replace("#74", "#75").replace("issue=74", "issue=75")
        try:
            with self.assertRaises(BrokerError) as caught:
                self.broker().execute(
                    "newemaint", "gitea.pull.merge.routine",
                    number=7, sha=self.sha,
                )
        finally:
            self.body = original_body
        self.assertEqual(caught.exception.code, "ROUTINE_CANARY_ONLY")
        self.assertEqual(self.posts, [])

    def test_final_head_reread_closes_toctou_and_zero_post(self):
        pull_reads = 0

        def drift_on_final_read(method, url, headers, body):
            nonlocal pull_reads
            path = urlparse(url).path
            if path.endswith("/pulls/7"):
                pull_reads += 1
                if pull_reads == 2:
                    return self.response(self.pull(sha="c" * 40))
            return self.transport(method, url, headers, body)

        with self.assertRaises(BrokerError) as caught:
            self.broker(drift_on_final_read).execute(
                "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha
            )
        self.assertEqual(caught.exception.code, "ROUTINE_HEAD_DRIFT")
        self.assertEqual(self.posts, [])

    def test_authorization_requires_one_marker_and_one_exact_closes_line(self):
        bodies = (
            self.body.replace("AISoft-Submit-Authorization:", "AISoft-Authorization:"),
            self.body + "\nCloses #45\n",
            self.body.replace("policy=routine-auto", "policy=manual"),
        )
        for value in bodies:
            with self.subTest(body=value):
                self.posts.clear()
                original = self.body
                self.body = value
                try:
                    with self.assertRaises(BrokerError) as caught:
                        self.broker().execute(
                            "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha
                        )
                finally:
                    self.body = original
                self.assertEqual(caught.exception.code, "ROUTINE_AUTHORIZATION_INVALID")
                self.assertEqual(self.posts, [])

    def test_extra_arguments_are_rejected_before_credentials(self):
        with self.assertRaises(BrokerError) as caught:
            self.broker().execute(
                "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha,
                branch=self.branch,
            )
        self.assertEqual(caught.exception.code, "ARGUMENT_MISMATCH")

    def test_hard_gate_failure_matrix_never_posts_or_falls_back(self):
        scenarios = (
            ("push enabled", "ROUTINE_PROTECTION_DRIFT",
                "/branch_protections/main",
                {"enable_push": True},
            ),
            ("merger appears in push allowlist", "ROUTINE_PROTECTION_DRIFT",
                "/branch_protections/main",
                {"push_whitelist_usernames": ["newemaint-routine-merger"]},
            ),
            ("merger has Admin", "ROUTINE_PROTECTION_DRIFT",
                "/collaborators/newemaint-routine-merger/permission",
                {"permission": "admin"},
            ),
            # Every required context has to be green, not just the first one:
            # #312 added NewEMaint's mobile-verify, and a gate that stopped at
            # one context would have let a red mobile build merge itself.
            ("last required context failed", "ROUTINE_CI_NOT_GREEN",
                "/commits/" + self.sha + "/status",
                {"statuses": [
                    {
                        "context": context,
                        "status": (
                            "failure"
                            if context == newemaint_required_contexts()[-1]
                            else "success"
                        ),
                    }
                    for context in newemaint_required_contexts()
                ]},
            ),
            ("a required context is absent", "ROUTINE_CI_NOT_GREEN",
                "/commits/" + self.sha + "/status",
                {"statuses": [{
                    "context": newemaint_required_contexts()[0],
                    "status": "success",
                }]},
            ),
            ("review rejected", "ROUTINE_REVIEW_REJECTED",
                "/pulls/7/reviews",
                [{"state": "REQUEST_CHANGES"}],
            ),
            ("scope expanded", "ROUTINE_SCOPE_EXPANDED",
                "/pulls/7/files",
                [{"filename": ".gitea/workflows/ci.yml", "status": "modified"}],
            ),
        )
        for label, expected, suffix, value in scenarios:
            with self.subTest(label=label, expected=expected):
                self.posts.clear()

                def failing(method, url, headers, body, *, suffix=suffix, value=value):
                    if urlparse(url).path.endswith(suffix):
                        return self.response(value)
                    return self.transport(method, url, headers, body)

                with self.assertRaises(BrokerError) as caught:
                    self.broker(failing).execute(
                        "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha
                    )
                self.assertEqual(caught.exception.code, expected)
                self.assertEqual(self.posts, [])

    def test_duplicate_issue_pull_is_rejected_with_zero_post(self):
        duplicate = self.pull()
        duplicate["number"] = 8
        duplicate["head"] = {"ref": "change/74-other-fix", "sha": "d" * 40}

        def duplicated(method, url, headers, body):
            if urlparse(url).path.endswith("/pulls"):
                return self.response([self.pull(), duplicate])
            return self.transport(method, url, headers, body)

        with self.assertRaises(BrokerError) as caught:
            self.broker(duplicated).execute(
                "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha
            )
        self.assertEqual(caught.exception.code, "ROUTINE_PR_NOT_UNIQUE")
        self.assertEqual(self.posts, [])

    def test_dismissed_or_stale_rejection_is_not_an_effective_rejection(self):
        for review in (
            {"state": "REQUEST_CHANGES", "dismissed": True, "stale": False},
            {"state": "REQUEST_CHANGES", "dismissed": False, "stale": True},
        ):
            with self.subTest(review=review):
                self.posts.clear()

                def inactive(method, url, headers, body, *, review=review):
                    if urlparse(url).path.endswith("/pulls/7/reviews"):
                        return self.response([review])
                    return self.transport(method, url, headers, body)

                result = self.broker(inactive).execute(
                    "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha
                )
                self.assertEqual(result["status"], "AUTO_MERGED")
                self.assertEqual(len(self.posts), 1)

    def test_dependency_block_is_stable_and_zero_post(self):
        self.summary = self.summary.replace("depends_on: []", "depends_on:\n  - 43")

        def dependency(method, url, headers, body):
            if urlparse(url).path.endswith("/issues/43"):
                return self.response({"state": "open", "labels": []})
            return self.transport(method, url, headers, body)

        with self.assertRaises(BrokerError) as caught:
            self.broker(dependency).execute(
                "newemaint", "gitea.pull.merge.routine", number=7, sha=self.sha
            )
        self.assertEqual(caught.exception.code, "ROUTINE_DEPENDENCY_BLOCKED")
        self.assertEqual(self.posts, [])


if __name__ == "__main__":
    unittest.main()
