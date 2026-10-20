"""Skill and runbook phrases the session flow depends on.

Moved out of test_routine_merge.py when the routine merge operation left main
(#391, ADR 0002); the routine broker and eligibility tests went with it.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[2]


class SessionContractTests(unittest.TestCase):
    # #379: one skill source for every provider. These pins used to exist twice
    # (an English Codex copy and a Chinese Claude copy); they now guard the
    # single merged text under skills/.
    SESSION_FLOW = "skills/issue-session-flow/SKILL.md"
    PLATFORM = "skills/aisoft-platform/SKILL.md"
    CONFIRM_1 = "## 确认点 1：合同/启动"
    CONFIRM_2 = "## 确认点 2：准备提交最终 PR"
    COMPLETION = "## 收尾（manual 确认已合并，或 routine receipt 后自动执行）"

    def test_session_flow_keeps_only_contract_start_and_pr_confirmations(self):
        content = self._source(self.SESSION_FLOW)
        self.assertIn(self.CONFIRM_1 + "\n", content)
        self.assertIn(self.CONFIRM_2 + "\n", content)
        marker = (
            "当前合同内 CI 修复可继续，最终 head 的 required CI 全绿且全部硬门通过后，"
            "允许受控自动合并。"
        )
        self.assertIn(marker, content)
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
        autonomy = self._section(content, "## approved 之后默认自主推进")
        self._require(
            autonomy,
            "确认点 2 通过后同样不再询问 push、唯一最终 PR 与 PR CI 修复。",
            "只有合同/启动确认不授权 push 或建 PR。",
        )
        before_pr_confirmation = autonomy.split("确认点 2 通过后", 1)[0]
        self.assertNotRegex(
            before_pr_confirmation.lower(), r"push|(?<![a-z])pr(?![a-z])|pull request"
        )
        self._require(
            self._section(content, self.CONFIRM_1),
            "它只授权合同内实现、测试和修复，不授权提交 PR、merge 或 deploy。",
        )
        self._require(
            self._section(content, self.CONFIRM_2),
            "重复 poll 不调用 provider、不 push、不建 PR。",
            "manual 文本不得包含自动合并 marker。",
            "routine hard gate 失败只返回一个稳定原因，零 merge POST、零权限降级、零 fallback。",
            "routine `AUTO_MERGED` receipt 直接进入收尾，不再询问第三次。",
        )

    def _assert_classification_readback(self, content):
        self._require(
            self._section(content, self.CONFIRM_2),
            "codex/tools/apply-classification-labels.sh --repo <checkout> --verify N",
            "用 exact Issue 编号，不用 `--range`。",
            "不是 `projected` 就不要进入待合并",
            "读到 `projection-missing` 或 `projection-mismatch` 就修复合同内的投影",
            "其它不可读结果作为 blocker 报告。",
            "`projection-window-closed` 是遗漏的证据，不是补写或覆盖的许可。",
        )
        self._require(self._section(content, self.COMPLETION), "不补写、不加 override")

    def _assert_terminal_apply(self, content):
        self._require(
            self._section(content, self.COMPLETION),
            "确认 merge commit **真实存在**于 `origin/main`。",
            "codex/tools/mark-completed-issues.sh --repo <checkout> --project <id> --range <range>",
            "`commits` 是这个 range 实际覆盖的 merge",
            "逐 Issue 行的 `commit` 是产出它的那条",
            "核对它就是第 1 步认定的那个 merge",
            "不是就说明范围瞄错了，重跑之前不要往下走",
            "用计划回给的 `pinned` 编号，不再传 `--range`",
            "--apply <pinned>",
            "`required_docs`",
            "`deployment_lifecycle`",
            "两个条件都由工具读取，不要自己判断该写 `completed` 还是 `deployed`",
            "计划里出现你不认识的 `reason` 时读 `detail`，它写着依据，绝不推断已部署。",
        )

    def _assert_backfill_paths(self, content):
        backfill = self._section(content, "## PR URL 回填的两条路径")
        self.assertIn("Controller 托管的运行", backfill)
        self.assertIn("Mac 交互会话", backfill)
        controller = backfill.split("Controller 托管的运行", 1)[1].split("Mac 交互会话", 1)[0]
        interactive = backfill.split("Mac 交互会话", 1)[1]
        self._require(
            controller,
            "把这个 PR 的 URL 写进 change summary 的 `pr_url` front matter 字段，"
            "并把 summary 的 `status` 推进到 `pr-open`，只提交这一份文档并推送",
            "不要重复它的回填步骤，也不要把这次额外 commit 当成 provider 的工作。",
            "`pr_url` 只写在 summary 里（#142），spec、plan 与 verification 不带它。",
            "summary 没有声明 `pr_url`，或已经声明了另一个值时，Controller fail closed "
            "并返回 `NEEDS_HUMAN_DECISION`，不覆盖也不跳过",
        )
        self._require(
            interactive,
            "直接用 broker `gitea.pull.create` 建 PR 时",
            "backfill-pr-url N --repo <checkout> --pr-url <实际 PR URL>",
            "只提交映射的 summary，并经 broker 推送同一个 change 分支。",
            "单独的 `gitea.pull.create` 调用不会运行 Controller 的自动回填。",
            "PR 存在之前 `pr_url` 留空、保持真实的 PR 前状态",
            "回填后对更新过的 checkout 运行 `check-change-documents`。",
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

    def test_session_flow_requires_exact_classification_readback_before_pr(self):
        content = self._source(self.SESSION_FLOW)
        self._assert_confirmation_permissions(content)
        self._assert_classification_readback(content)

    def test_session_flow_pins_the_verified_merge_before_terminal_apply(self):
        self._assert_terminal_apply(self._source(self.SESSION_FLOW))

    def test_platform_skill_separates_controller_and_interactive_pr_backfill(self):
        self._assert_backfill_paths(self._source(self.PLATFORM))

    def test_shared_onboarding_keeps_second_confirmation_and_manifest_lifecycle(self):
        self._assert_shared_onboarding(self._source("skills/aisoft-platform/references/onboarding-runbook.md"))

    def test_shared_provider_document_requires_single_writer_claim_and_push_readback(self):
        self._assert_single_writer_push_readback(self._source("08-双工具共存与实施.md"))

    def test_confirmation_contract_rejects_early_push_authorization(self):
        self._assert_rejects_mutations(
            self._assert_confirmation_permissions,
            self._source(self.SESSION_FLOW),
            (
                ("必需的更宽闸门、判级投影。", "必需的更宽闸门、判级投影、push 与唯一最终 PR。"),
                ("只有合同/启动确认不授权 push 或建 PR。", ""),
                ("不授权提交 PR、merge 或 deploy。", "也授权提交 PR、merge 与 deploy。"),
            ),
        )

    def test_classification_contract_rejects_unprojected_or_closed_writes(self):
        self._assert_rejects_mutations(
            self._assert_classification_readback,
            self._source(self.SESSION_FLOW),
            (
                ("不是 `projected` 就不要进入待合并", "任一维度可读就进入待合并"),
                ("用 exact Issue 编号，不用 `--range`。", "用会移动的 `--range`。"),
                ("不是补写或覆盖的许可。", "可以补写或覆盖。"),
                ("不补写、不加 override", "补写并加 override"),
            ),
        )

    def test_terminal_contract_rejects_unproved_or_floating_merge(self):
        self._assert_rejects_mutations(
            self._assert_terminal_apply,
            self._source(self.SESSION_FLOW),
            (
                ("`commits` 是这个 range 实际覆盖的 merge", "commit 数量对得上即可"),
                ("重跑之前不要往下走", "继续往下走"),
                ("--apply <pinned>", "--apply --range <range>"),
                ("不再传 `--range`", "仍然传 `--range`"),
                ("`required_docs`", "可选文档"),
                ("`deployment_lifecycle`", "provider 推断"),
                ("两个条件都由工具读取，不要自己判断", "两个条件由 provider 推断，自行决定"),
                ("时读 `detail`", "时自行猜测标签"),
                ("绝不推断已部署", "可以推断已部署"),
            ),
        )

    def test_backfill_contract_rejects_ambiguous_ownership(self):
        self._assert_rejects_mutations(
            self._assert_backfill_paths,
            self._source(self.PLATFORM),
            (
                ("只提交这一份文档并推送", "提交所有文档并推送"),
                ("`pr_url` 只写在 summary 里", "`pr_url` 写在任意文档里"),
                ("只提交映射的 summary，并经 broker 推送同一个 change 分支。", "提交全部文件并直接推送。"),
                ("不会运行 Controller 的自动回填。", "会运行 Controller 的自动回填。"),
                ("`pr_url` 留空、保持真实的 PR 前状态", "`pr_url` 填好并设为 pr-open"),
            ),
        )

    def test_shared_onboarding_contract_rejects_provider_or_lifecycle_shortcuts(self):
        self._assert_rejects_mutations(
            self._assert_shared_onboarding,
            self._source("skills/aisoft-platform/references/onboarding-runbook.md"),
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


if __name__ == "__main__":
    unittest.main()
