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


class EligibilityTests(unittest.TestCase):
    def eligible(self, **overrides):
        values = {
            "issue_number": 44,
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
        governance = json.loads((ROOT / "config/gitea-governance.json").read_text())
        hsdb = next(item for item in governance["repositories"] if item["name"] == "HSDB")
        hsdb["routine_auto_merge_enabled"] = True
        self.governance = root / "governance.json"
        self.governance.write_text(json.dumps(governance))
        self.access = root / "access.json"
        self.access.write_bytes((ROOT / "config/host-access-broker.json").read_bytes())
        self.contract = load_access_contract(self.access, self.governance)
        self.sha = "a" * 40
        self.issue = 44
        self.branch = "change/44-fix-parser-bug"
        self.summary_path = (
            "docs/changes/44-fix-parser-bug/summary-fix-parser-bug-260826.md"
        )
        self.summary = f"""---
issue: 44
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
            f"Closes #44\n\n"
            f"AISoft-Submit-Authorization: issue=44; branch={self.branch}; policy=routine-auto\n\n"
            f"Change documents:\n- {self.summary_path}\n"
        )
        self.posts = []

    def tearDown(self):
        self.temporary.cleanup()

    def transport(self, method, url, headers, body):
        path = urlparse(url).path
        query = urlparse(url).query
        if path == "/api/v1/user":
            return self.response({"login": "hsdb-routine-merger", "is_admin": False})
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
        if path.endswith("/issues/44"):
            return self.response({
                "number": 44,
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
                "enable_force_push": False,
                "enable_force_push_allowlist": False,
                "enable_merge_whitelist": True,
                "merge_whitelist_usernames": ["admin", "hsdb-routine-merger"],
                "enable_status_check": True,
                "status_check_contexts": ["CI / test (pull_request)"],
                "required_approvals": 0,
                "block_admin_merge_override": True,
            })
        if path.endswith("/collaborators/hsdb-routine-merger/permission"):
            return self.response({"permission": "write"})
        if path.endswith("/commits/" + self.sha + "/status"):
            return self.response({"statuses": [{
                "context": "CI / test (pull_request)", "status": "success",
            }]})
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
            "hsdb", "gitea.pull.merge.routine", number=7, sha=self.sha
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

    def test_head_drift_is_first_stable_failure_and_zero_post(self):
        def drift(method, url, headers, body):
            path = urlparse(url).path
            if path.endswith("/pulls/7"):
                return self.response(self.pull(sha="c" * 40))
            return self.transport(method, url, headers, body)

        with self.assertRaises(BrokerError) as caught:
            self.broker(drift).execute(
                "hsdb", "gitea.pull.merge.routine", number=7, sha=self.sha
            )
        self.assertEqual(caught.exception.code, "ROUTINE_HEAD_DRIFT")
        self.assertEqual(self.posts, [])

    def test_extra_arguments_are_rejected_before_credentials(self):
        with self.assertRaises(BrokerError) as caught:
            self.broker().execute(
                "hsdb", "gitea.pull.merge.routine", number=7, sha=self.sha,
                branch=self.branch,
            )
        self.assertEqual(caught.exception.code, "ARGUMENT_MISMATCH")

    def test_hard_gate_failure_matrix_never_posts_or_falls_back(self):
        scenarios = (
            ("push enabled", "ROUTINE_PROTECTION_DRIFT",
                "/branch_protections/main",
                {"enable_push": True},
            ),
            ("merger has Admin", "ROUTINE_PROTECTION_DRIFT",
                "/collaborators/hsdb-routine-merger/permission",
                {"permission": "admin"},
            ),
            ("CI failed", "ROUTINE_CI_NOT_GREEN",
                "/commits/" + self.sha + "/status",
                {"statuses": [{
                    "context": "CI / test (pull_request)", "status": "failure",
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
                        "hsdb", "gitea.pull.merge.routine", number=7, sha=self.sha
                    )
                self.assertEqual(caught.exception.code, expected)
                self.assertEqual(self.posts, [])

    def test_dependency_block_is_stable_and_zero_post(self):
        self.summary = self.summary.replace("depends_on: []", "depends_on:\n  - 43")

        def dependency(method, url, headers, body):
            if urlparse(url).path.endswith("/issues/43"):
                return self.response({"state": "open", "labels": []})
            return self.transport(method, url, headers, body)

        with self.assertRaises(BrokerError) as caught:
            self.broker(dependency).execute(
                "hsdb", "gitea.pull.merge.routine", number=7, sha=self.sha
            )
        self.assertEqual(caught.exception.code, "ROUTINE_DEPENDENCY_BLOCKED")
        self.assertEqual(self.posts, [])


if __name__ == "__main__":
    unittest.main()
