---
issue: 299
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/299
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
  - ci-change
depends_on: []
status: pending
branch: change/299-outdated-branch-ruling
created: 2026-09-16
updated: 2026-09-16
---

# 验证记录

## 基线与范围

- Commit SHA: 7c7a80e（本记录提交前的最后一个实现 commit）
- 基线：`origin/main` = 9a2fa11
- 环境: Mac 交互会话；Gitea 1.26.4（`gitea-ci.orb.local:3000`）；broker 只读操作；
  bash 3.2 本机 + 平台 required CI（`CI / verify (pull_request)`）
- 本记录负责证明的 acceptance criteria: AC-1、AC-2、AC-3（切换前读回；切换后读回待负责人操作）、AC-4

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `gitea.protection.read`（切换前，2026-09-16） | PASS | aisoft-platform / localwms / newemaint：`block_on_outdated_branch: true`，`updated_at 2026-09-05T23:07:43+08:00`；sfm-digital-board：`true`，`updated_at 2026-08-08T18:03:01+08:00` |
| `bash codex/tests/test-project-check.sh`（改动前基线） | PASS | `project check tests passed (58 cases)` |
| `bash codex/tests/test-project-check.sh`（改动后） | PASS | `project check tests passed (61 cases)`：新增有合并预览 fixture 的 `false`/缺键 → SKIP 两例、无预览仍 GAP 一例、平台仓 GAP/PASS 两例；aligned fixture 的 `result:` 计数行不变 |
| `shellcheck -S warning` 两个脚本 + `bash -n` | PASS | 无输出 |
| `bash codex/tests/smoke.sh`（gating 前的 e4b3743 之前树，1e2db91+c1214f7） | PASS | `Codex platform static smoke checks passed.` exit=0 |
| `bash codex/tests/smoke.sh`（最终树 7c7a80e） | PASS | `Codex platform static smoke checks passed.` exit=0 |
| `check-change-documents --repo .` | PASS | `PASS: change-documents` / `PASS: change-pr-url`，`result: changes=136 pass=2 gap=0` |
| `git diff --check origin/main..HEAD` | PASS | 无输出 |
| `apply-classification-labels.sh --verify 299` | PASS | `result: projected`，`type/platform` + `complexity/complex` |
| `curl /api/v1/version` | PASS | `{"version":"1.26.4"}` |
| swagger `pulls/{index}/update` 与 `BranchProtection` 字段 | PASS | 仅手动更新端点 `POST .../pulls/{index}/update?style=`；保护字段仅 `block_on_outdated_branch`；无自动更新字段、无 merge queue |
| `aisoft-project-check.sh --repo <checkout>`（本地段，三个 internal-application，workflow 已与远端 main 比对一致） | PASS | NewEMaint `PASS: ci-merge-preview`；LocalWMS `PASS: ci-merge-preview`；SFMDigitalBoard `GAP: ci-merge-preview — .gitea/workflows/ci.yml 在 pull_request 上跑的是 PR head` |
| 三仓 `main` 的 ci.yml `on:` 触发 | PASS | NewEMaint、LocalWMS、SFMDigitalBoard 都有 `push: branches: [main]`；平台仓只有 `pull_request` |
| `aisoft-project-check.sh --remote`（Mac 上对真实仓） | NOT RUN | Mac 没有 `AGENT_ENV_FILE`（凭据只在 VM/broker），remote 段固定 GAP「AGENT_ENV_FILE 缺失」；remote 段语义由 test-project-check.sh 的 mock 证明 |
| `gitea.protection.read`（负责人切换后） | NOT RUN | 待负责人在 Gitea 界面关闭 NewEMaint 与 LocalWMS 后读回四仓，结果补写到本表并评论 Issue |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `06` 踩坑 29 新条目（裁决、否定裁决 B/C、残余风险、关闭前提、SFM 读回）；踩坑 22 对策列收窄指针；`grep -n "#299"` 命中两行 |
| AC-2 | PASS | 上表 test-project-check 61 例与 smoke；`public-test`、不在 manifest、403、未 `--remote` 四条既有用例原样通过 |
| AC-3 | PARTIAL | 切换前读回已记录；切换后读回 NOT RUN，等负责人操作 |
| AC-4 | NOT RUN | PR 尚未创建；`git diff --stat origin/main..HEAD` 不含 `.gitea/workflows/` |

## 遗留风险与未完成项

- 切换后读回与 Issue 评论待负责人在 Gitea 界面操作 NewEMaint、LocalWMS 后补做；SFMDigitalBoard
  保留 `true`，直到其自己的 Issue 采纳合并预览（`ci-merge-preview` PASS）。
- 平台仓 ci.yml 没有 push-main 触发，平台仓因此保留开关；若将来要一并关闭，先另立 Issue 加 push 触发。
- 踩坑 29 的编号假定 #298 先合并占用 28；顺序反了由合并者改号。
