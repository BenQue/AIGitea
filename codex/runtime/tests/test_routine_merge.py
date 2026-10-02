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


    def _source(self, relative_path):
        return (ROOT.parent / relative_path).read_text(encoding="utf-8")

    def _section(self, content, heading):
        self.assertIn(heading + "\n", content)
        return content.split(heading + "\n", 1)[1].split("\n## ", 1)[0]

    def _require(self, content, *rules):
        normalized = " ".join(content.split())
        for rule in rules:
            self.assertIn(rule, normalized)

    def _assert_confirmation_permissions(self, content):
        autonomy = self._section(content, "## Default autonomy after approval")
        self._require(
            autonomy,
            "After final-PR submission confirmation, continue through branch push, the one final PR "
            "and in-contract PR CI repair",
            "Contract/start approval alone does not authorize push or PR creation.",
        )
        before_pr_confirmation = autonomy.split("After final-PR submission confirmation", 1)[0]
        self.assertNotRegex(
            before_pr_confirmation.lower(), r"\b(?:push|pull request|pr creation|final pr)\b"
        )
        confirmation = self._section(content, "## Two default confirmation points")
        self._require(
            confirmation,
            "It authorizes in-scope implementation and repair, not PR submission, merge, or deploy.",
            "Repeated polls in that state must not call a provider, push, or create a PR.",
            "The manual text must not contain the controlled-auto-merge marker.",
            "A routine hard-gate failure returns one stable reason with zero merge POST and no silent fallback.",
            "A routine `AUTO_MERGED` receipt immediately enters deterministic post-merge completion "
            "without a third confirmation.",
        )

    def _assert_classification_readback(self, content):
        confirmation = self._section(content, "## Two default confirmation points")
        self._require(
            confirmation,
            "codex/tools/apply-classification-labels.sh --repo <checkout> --verify N",
            "using the exact Issue number, never `--range`",
            "only when both classification dimensions read back as `projected`",
            "For `projection-missing` or `projection-mismatch`, repair the in-contract projection and re-read it",
            "report a `broker-operation-missing` or other unreadable result as a blocker",
            "`projection-window-closed` is evidence of an omission, never permission to backfill or override it.",
        )
        self._require(
            self._section(content, "## Post-merge completion"),
            "do not backfill closed Issues or add an override.",
        )

    def _assert_terminal_apply(self, content):
        completion = self._section(content, "## Post-merge completion")
        self._require(
            completion,
            "Fetch and prove that the exact merge commit is on `origin/main`.",
            "Dry-run `codex/tools/mark-completed-issues.sh --repo <checkout> --range <range>`",
            "Check the first `selector: range` row's `commits` and each Issue row's `commit` "
            "against the exact merge from step 1",
            "Stop if the plan targets another merge.",
            "Apply the checked plan with `codex/tools/mark-completed-issues.sh --repo <checkout> --apply <pinned>`",
            "using the plan's immutable Issue numbers; never re-use `--range` for the apply.",
            "Let the tool decide from mapped summary `required_docs` and the manifest's `deployment_lifecycle`.",
            "Read an unfamiliar reason's detail rather than guessing a lifecycle label; never infer deployment.",
        )

    def _assert_backfill_paths(self, content):
        development = self._section(content, "## Preserve the Development Loop boundary")
        self.assertIn("In a Controller-managed run", development)
        self.assertIn("In a Mac interactive session", development)
        controller = development.split("In a Controller-managed run", 1)[1].split(
            "In a Mac interactive session", 1
        )[0]
        interactive = development.split("In a Mac interactive session", 1)[1]
        self._require(
            controller,
            "the Controller writes that PR's URL into the change summary's `pr_url` front matter field "
            "and advances the summary's `status` to `pr-open`, commits exactly that one document, and pushes it",
            "do not duplicate its backfill step or treat the extra commit as provider work",
            "`pr_url` lives in the summary only (#142); spec, plan and verification documents do not carry it.",
            "If the summary does not declare `pr_url`, or already declares a different one, the Controller "
            "fails closed and returns `NEEDS_HUMAN_DECISION` rather than overwriting or skipping",
        )
        self._require(
            interactive,
            "creates the PR with broker `gitea.pull.create` without invoking the Controller",
            "backfill-pr-url N --repo <checkout> --pr-url <actual PR URL>",
            "commit exactly the mapped summary and push the same change branch through the broker.",
            "The standalone `gitea.pull.create` call does not run the Controller's automatic backfill.",
            "Before the PR exists, leave `pr_url` empty and keep the real pre-PR status",
            "run `check-change-documents` on the updated checkout.",
        )

    def _assert_shared_onboarding(self, content):
        development = self._section(content, "## 7. Development Loop 接入")
        self._require(
            development,
            "所选 provider 的 skills/adapter 验证完成后启用",
            "第二确认点（最终 PR 提交确认）明确授权并通过 final-head 全硬门",
            "第一确认点仅批准合同/启动，不授权 push、PR、merge 或部署",
        )
        self.assertNotIn("eligible routine-small 只有在第一确认点", development)
        acceptance = self._section(content, "## 8. 接入验收")
        self._require(
            acceptance,
            "每个所选 provider 的 adapter 独立完成至少一个明确标注的真实 pilot",
            "一侧验收不替代另一侧",
        )
        completion = acceptance.split("### 合并后收尾\n", 1)[1].split("\n### ", 1)[0]
        self._require(
            completion,
            "证明 exact merge commit 已在主干后",
            "核对第一行 `commits` 与逐 Issue 的 `commit` 就是本次 exact merge",
            "用计划回给的 `pinned` Issue 编号运行",
            "--apply <pinned>",
            "不再传 `--range`",
            "终态判定由工具读取映射 summary 的 `required_docs` 与 manifest 的 `deployment_lifecycle`",
            "只有前者含 `verification` 且后者为 `application-deploy` 才等待部署",
            "`none` 与缺省 `application-deploy-selective` 到 `completed`",
            "`verification` 不等于部署",
        )

    def _assert_single_writer_push_readback(self, content):
        configuration = self._section(content, "## 3. 配置与认证")
        self._require(
            configuration,
            "每个 change 使用自己的 `issue-N-short-description` 隔离 worktree",
            "任何 commit 前 `git branch --show-current` 必须等于 exact `change/N-short-description`",
            "创建后立即用 `claim-worktree --branch <branch> --worktree <worktree>` 绑定本会话",
            "每次 broker push 透传同一个 `AISOFT_SESSION_ID`",
            "push 后必须核对返回的 `pushed_head` 与确认点 2 已验证的 SHA 相等，任何不匹配立即停止",
            "另一会话不得替该 worktree rebase/commit/checkout",
            "`scan-worktrees --repo <checkout>` 只读盘点",
        )

    def _assert_rejects_mutations(self, validator, content, mutations):
        for rule, replacement in mutations:
            with self.subTest(rule=rule, replacement=replacement):
                self.assertIn(rule, content)
                mutated = content.replace(rule, replacement, 1)
                self.assertNotEqual(mutated, content)
                with self.assertRaises(AssertionError):
                    validator(mutated)

    def test_source_skills_require_exact_classification_readback_before_pr(self):
        codex = self._source("codex/skills/issue-session-flow/SKILL.md")
        self._assert_confirmation_permissions(codex)
        self._assert_classification_readback(codex)
        claude = self._source("skill-for-claude/issue-session-flow/SKILL.md")
        self._require(
            self._section(claude, "## 确认点 2：准备提交最终 PR"),
            "apply-classification-labels.sh --verify N",
            "不是 `projected` 就不要进入待合并",
            "窗口随之永久关闭，之后没有任何工具会补写 `type/*` 与 `complexity/*`",
        )
        self._require(
            self._section(claude, "## 收尾（manual 确认已合并，或 routine receipt 后自动执行）"),
            "projection-window-closed",
            "不补写、不加 override",
        )

    def test_source_skills_pin_the_verified_merge_before_terminal_apply(self):
        self._assert_terminal_apply(self._source("codex/skills/issue-session-flow/SKILL.md"))
        claude = self._source("skill-for-claude/issue-session-flow/SKILL.md")
        self._require(
            self._section(claude, "## 收尾（manual 确认已合并，或 routine receipt 后自动执行）"),
            "`commits` 是这个 range 实际覆盖的 merge",
            "逐 Issue 行的 `commit` 是产出它的那条",
            "核对它就是第 1 步认定的那个 merge",
            "不是就说明范围瞄错了，重跑之前不要往下走",
            "用计划回给的 `pinned` 编号，不再传 `--range`",
            "--apply <pinned>",
            "required_docs",
            "deployment_lifecycle",
        )

    def test_codex_separates_controller_and_interactive_pr_backfill(self):
        self._assert_backfill_paths(self._source("skill-for-codex/SKILL.md"))

    def test_shared_onboarding_keeps_second_confirmation_and_manifest_lifecycle(self):
        self._assert_shared_onboarding(self._source("skill-for-codex/references/onboarding-runbook.md"))

    def test_shared_provider_document_requires_single_writer_claim_and_push_readback(self):
        self._assert_single_writer_push_readback(self._source("08-双工具共存与实施.md"))

    def test_confirmation_contract_rejects_early_push_authorization(self):
        self._assert_rejects_mutations(
            self._assert_confirmation_permissions,
            self._source("codex/skills/issue-session-flow/SKILL.md"),
            (
                ("- classification projection.", "- classification projection, branch push, the one final PR and PR CI repair."),
                ("Contract/start approval alone does not authorize push or PR creation.", ""),
                ("not PR submission, merge, or deploy.", "including PR submission, merge, and deploy."),
            ),
        )

    def test_classification_contract_rejects_unprojected_or_closed_writes(self):
        self._assert_rejects_mutations(
            self._assert_classification_readback,
            self._source("codex/skills/issue-session-flow/SKILL.md"),
            (
                ("both classification dimensions read back as `projected`", "either dimension is readable"),
                ("using the exact Issue number, never\n`--range`", "using a moving `--range`"),
                ("never permission to backfill or override it.", "permission to backfill or override it."),
                ("do not backfill closed Issues or add an override.", "backfill closed Issues with an override."),
            ),
        )

    def test_terminal_contract_rejects_unproved_or_floating_merge(self):
        self._assert_rejects_mutations(
            self._assert_terminal_apply,
            self._source("codex/skills/issue-session-flow/SKILL.md"),
            (
                ("row's `commits` and each Issue row's `commit`", "row's commit count"),
                ("Stop if the plan targets another merge.", "Continue if the plan targets another merge."),
                ("--apply <pinned>", "--apply --range <range>"),
                ("never re-use `--range` for the apply.", "re-use `--range` for the apply."),
                ("`required_docs`", "optional documents"),
                ("`deployment_lifecycle`", "provider inference"),
            ),
        )

    def test_backfill_contract_rejects_ambiguous_ownership(self):
        self._assert_rejects_mutations(
            self._assert_backfill_paths,
            self._source("skill-for-codex/SKILL.md"),
            (
                ("commits exactly that one\ndocument", "commits every document"),
                ("`pr_url` lives in the summary only", "`pr_url` lives in any document"),
                ("commit exactly the mapped summary and push the same change branch through the broker.", "commit all files and push directly."),
                ("does not run the Controller's automatic backfill.", "runs the Controller's automatic backfill."),
                ("empty and keep the real pre-PR status", "filled and set pr-open"),
            ),
        )

    def test_shared_onboarding_contract_rejects_provider_or_lifecycle_shortcuts(self):
        self._assert_rejects_mutations(
            self._assert_shared_onboarding,
            self._source("skill-for-codex/references/onboarding-runbook.md"),
            (
                ("第二确认点（最终 PR 提交确认）明确授权", "第一确认点明确授权"),
                ("一侧验收不替代另一侧", "一侧验收替代另一侧"),
                ("独立完成至少一个明确标注的真实 pilot", "继承共享 synthetic 结果"),
                ("`deployment_lifecycle`", "provider inference"),
                ("且后者为 `application-deploy`", "或后者为 `application-deploy`"),
                ("不再传 `--range`", "仍然传 `--range`"),
            ),
        )

    def test_shared_provider_contract_rejects_unverified_push(self):
        self._assert_rejects_mutations(
            self._assert_single_writer_push_readback,
            self._source("08-双工具共存与实施.md"),
            (
                ("claim-worktree --branch <branch> --worktree <worktree>", "claim-worktree"),
                ("每次 broker push 透传同一个 `AISOFT_SESSION_ID`", "每次 push 创建新 session id"),
                ("SHA 相等，任何不匹配立即停止", "SHA 可不同，继续创建 PR"),
            ),
        )


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
