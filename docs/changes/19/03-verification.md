---
issue: 19
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/19
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
depends_on: []
status: verified-local
branch: change/19
pr_url:
created: 2026-07-26
updated: 2026-07-26
---

# Verification

## 环境与版本

- Source baseline：`origin/main@7f4ce0ab089289717a182312367aea4aaa6348c1`
- Candidate branch：`change/19`
- Gitea：`admin/aisoft-platform`

## 执行结果

| Command | Result | Evidence |
|---|---|---|
| `bash codex/tests/test-sync-gitea-labels.sh` | PASS | 第一次创建 17 个，第二次创建 0 个；token 未进入 argv/stdout/stderr |
| `bash codex/tests/test-mark-deployed-issues.sh` | PASS | 输入含 `completed` 时输出只保留 type、complexity、非 managed label 与 `deployed` |
| 定向 Python contract/Gitea/controller tests | PASS | 40 项；覆盖 `completed` 合法终态、互斥和 dependency readiness |
| `bash -n`（全部本次修改 shell） | PASS | 无语法错误 |
| `shellcheck`（全部本次修改 shell） | PASS | 无诊断 |
| `bash codex/tests/smoke.sh` | PASS | 105 项 Python runtime tests、全部 shell mocks 与 static smoke 通过 |
| `git diff --check` | PASS | 无空白错误 |

PR 合并前只记录本地、mock 和 CI 候选证据；真实标签目录与 Issue metadata 迁移必须在
人工合并后单独补充。

## Acceptance criteria 结果

- AC-1：PASS（candidate）；manifest smoke 锁定 17 个唯一标签。
- AC-2：PASS（candidate）；Gitea adapter 接受唯一 `completed`，拒绝
  `completed` + `deployed`。
- AC-3：PASS（candidate）；closed + `completed` 与 closed + `deployed` 均可满足
  dependency，open 或 `pr-open` 不满足。
- AC-4：PASS（candidate）；mark-deployed mock 移除 `completed`。
- AC-5：PASS（candidate）；当前权威文档与 skill 更新，历史 Issue #10 plan 以说明
  保留初始 16-label 事实。
- AC-6：PASS。
- AC-7：NOT RUN；等待 PR 人工合并。
- AC-8：PARTIAL；mock fail-closed 与回滚合同完成，live 快照等待合并。

## 重复执行

- label sync 第一次：PASS（mock），`created=17 existing=17`。
- label sync 第二次：PASS（mock），`created=0 existing=17`。
- live Issue migration：PR 合并前 NOT RUN。

## 故意失败与回滚

- 本地/mock 失败场景：PASS；缺 label、API failure、非法双终态与 token 扫描均保持
  fail-closed 或既有 best-effort 部署语义。
- live rollback snapshot：PR 合并前 NOT RUN。

## 遗留风险与未完成项

- PR 人工合并。
- 合并后的 Gitea label provision、10 个历史 Issue migration 与读回。
