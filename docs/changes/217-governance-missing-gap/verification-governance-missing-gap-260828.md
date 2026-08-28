---
issue: 217
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/217
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - shared-core
  - platform-governance
depends_on:
  - 215
status: pending
branch: change/217-governance-missing-gap
created: 2026-08-28
updated: 2026-08-28
---

# governance missing collaborator GAP 验证记录

## 基线与范围

- Commit SHA: `78a36de53a063e338cf257dada29ec432637cfee`（#215/PR #216 merge）
- 基线：fresh canonical broker fetch 后 `origin/main=78a36de53a063e338cf257dada29ec432637cfee`
- 环境: macOS Codex managed linked worktree；source/local fake transport；live evidence 只引用委派源任务已完成的 read-only preflight
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-8
- Merge policy: manual

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 完整合同读取 | PASS | `aisoft-platform`、`issue-session-flow`、private-access、AGENTS/README/03/04/06/08/09、#213/#215 docs、governance runtime/manifests/tests 已读 |
| canonical broker `git.fetch.main` | PASS | sandbox 首次 `TRANSPORT_ERROR`；同一 typed operation 在 host context 重试 PASS；HEAD/main/origin/main exact `78a36de...` |
| post-#215 installed live preflight | PASS (defect observed) | source task mutation=0；host.access.audit 返回 expected structured GAP；installed governance check 仍报 `collaborator permission response is invalid`，无可信 plan |
| local exact-404 defect replay | PASS (defect reproduced) | account removed；collaborator inventory保留 exact identity；permission GET=HTTP 404；current `_check` 在 account GET 前抛 `ApiError`，mutating calls=0 |
| semantic docs | NOT RUN | 待执行 mapping/audit |
| targeted/full tests | NOT RUN | 待实现后执行 |
| Controller preflight | NOT RUN | 待 final local head 执行 |
| live account/PAT/credential/collaborator/protection | NOT RUN | 本任务禁止；mutation=0 |
| install/#74/routine merge/manual merge/deploy | NOT RUN | 本任务禁止 |
| push/create PR | NOT RUN | 等待最终 PR 提交确认 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | FAIL before fix | exact missing + permission 404 无法生成 planned action |
| AC-2 | FAIL before fix | call trace 中 account GET 尚未发生，permission 路径已终止 check |
| AC-3 | NOT RUN | 待测试/实现 |
| AC-4 | NOT RUN | 待测试/实现 |
| AC-5 | NOT RUN | 待回归 |
| AC-6 | PASS (pre-change boundary) / NOT RUN (post-change) | defect replay mutating calls=0；apply ordering待回归 |
| AC-7 | NOT RUN | 待diff/test |
| AC-8 | PASS (boundary) / NOT RUN (tests) | live/merge/deploy mutation=0；全量门禁待执行 |

## 遗留风险与未完成项

- 当前只完成合同、fresh baseline 与改前复现；实现、targeted/full smoke、semantic/Controller preflight 均未运行。
- installed/live governance 仍是 blocker；source 修复未合并/安装前不能把 local PASS 推定为 live PASS。
- Codex 宿主 worktree 外层 basename 为 `ca13/AISoftPlatform`，不是 contract 推荐的
  `issue-217-governance-missing-gap`；branch/docs/front matter exact，Controller preflight 必须如实记录该宿主例外。
