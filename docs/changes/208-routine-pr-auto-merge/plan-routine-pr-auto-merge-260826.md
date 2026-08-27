---
issue: 208
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/208
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - security
  - shared-core
  - ci
depends_on:
  - 207
status: approved
branch: change/208-routine-pr-auto-merge
created: 2026-08-26
updated: 2026-08-26
---

# Routine PR 受控自动合并实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | mapped summary/spec/plan/verification 与完整授权边界 | - | completed |
| T02 | governance-only 两确认点、manual exclusions 与独立 merger 合同；完成即停止 | T01 | completed |
| T03 | fresh-run governance manifest、broker hard gate、Controller 分流与全套回归 | T02 | completed |
| T04 | 全量验证、真实 source/installed/live 分层记录、PR-ready 人工闸门材料 | T03 | completed |

## Expected touch points

- T01：仅 `docs/changes/208-routine-pr-auto-merge/`。
- T02：spec 授权的 `AGENTS.md`、README、03/04/08/09、Codex/Claude session/platform/Matt skills、
  global/template AGENTS 与 private access/onboarding/project-align references；不得改 runtime/config/tests。
- T03：`codex/config/gitea-governance.json`、`host-access-broker.json`、`gitea-labels.json`；
  `aisoft_gitea_governance` contract/reconcile/CLI；`aisoft_host_access` contract/credentials/broker/runner/CLI；
  `aisoft_loop` eligibility/controller/state/CLI；相应 bootstrap/install/shell/Python tests。
- T04：本 Issue plan/summary/verification；只收口真实证据，不创建最终 PR。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1、AC-10、AC-11 | 双工具 skill 内容断言、安装 byte parity/drift tests、session handoff review |
| AC-2 | Controller state/CLI tests：确认后 CI 修复、resume、重复 poll、最终 head pin |
| AC-3、AC-4 | auto-merge eligibility matrix：routine small 正例及 complex/#208/major/phase/security/data/shared-core/CI/artifact/deploy/rollback/governance 负例 |
| AC-5 | governance contract/reconcile tests：identity distinct、非 admin、exact repo、no ordinary Git/cross-project、allowlist read-back |
| AC-6、AC-7、AC-8、AC-9 | host-access broker tests：typed args、全 hard-gate failure matrix、一次 exact merge POST、Gitea `head_commit_id` 与无 force/schedule/deploy |
| AC-12 | Git commit/diff review：T02 只含 governance contract；T03 commit 的 parent 为 T02 且 fresh agent 重新读取 `AGENTS.md` |
| AC-13 | 相关定向 unittest；`bash codex/tests/smoke.sh`；修改 shell 的 `bash -n`/ShellCheck；`check-change-documents`；broker read-only source/installed/live 对照 |

## 实施顺序

1. T01 在 exact worktree 完成、校验、原子 commit。
2. 独立 governance execution 只实现 T02，运行文档/skill drift 检查并 commit，然后停止。
3. fresh runtime execution 从 T02 head 重读 `AGENTS.md` 和本 spec/plan，完成 T03；普通测试/CI
   失败在合同内自主修复，hard-gate/权限/范围冲突立即升级。
4. T04 跑定向与全量测试，填写 verification 与最终 diff/rollback/NOT RUN 事实，提交本地原子 commit，停在 `AWAITING_PR_CONFIRMATION`；本次不 push、不创建 PR。
5. 输出拟议 PR title/body 与 branch/head/commits/tests/diff/rollback；停止在“提交最终 PR”确认点。

## 部署与回滚

无部署。本 Issue 不安装、不 provision credential、不 apply live protection。Source 通过 revert 唯一 PR 回滚；
若未来独立授权 live apply，其 disable → human-only allowlist → credential/collaborator revoke → read-back
回滚顺序由本 spec 固定，但不在本计划执行。
