---
issue: 223
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/223
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - ci-change
  - shared-core
  - platform-governance
depends_on: []
status: approved
branch: change/223-ci-merge-preview-gate
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan：#223 合并预览检查器与过期绿闸门

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `templates/project/ci/` 的 CI workflow 与合并预览脚本参考，进 smoke 静态闸门 | - | pending |
| T02 | `aisoft-project-check.sh` 的 `ci-merge-preview` 只读检查与正反用例 | T01 | pending |
| T03 | `aisoft-project-check.sh` 的 `ci-outdated-branch` 只读检查与正反用例 | - | pending |
| T04 | 平台仓 `.gitea/workflows/ci.yml` 改跑合并预览，context 三要素不变 | T01 | pending |
| T05 | `06` 文档条目与 verification 记录，含 7 仓交接项 | T02, T03, T04 | pending |

T01 先行是因为 T02 的 fixture 与 T04 的 workflow 都引用同一份参考脚本。
T03 与形态判据无关，可与 T02 并行；此处按顺序执行以保持每个 commit 可单独 revert。

## Expected touch points

- T01：`templates/project/ci/ci.yml`（新增）、`templates/project/ci/merge-preview.sh`（新增）、
  `codex/tests/smoke.sh`（`bash -n` 与 ShellCheck 清单各加一行）。
- T02：`codex/tools/aisoft-project-check.sh`、`codex/tests/test-project-check.sh`。
- T03：`codex/tools/aisoft-project-check.sh`、`codex/tests/test-project-check.sh`。
- T04：`.gitea/workflows/ci.yml`。
- T05：`06-运维手册与踩坑集.md`、本 change 目录的 verification 文档。

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-project-check.sh` 新增用例断言 `ci-merge-preview` 三种结论；检查器全程无写操作，diff review |
| AC-2 | 新增用例以 LocalWMS `origin/main` 的真实 `.gitea/workflows/ci.yml` 与 `scripts/ci/merge-preview.sh` 为 fixture，断言 `PASS: ci-merge-preview` |
| AC-3 | 新增用例以本仓改动前的 `ci.yml` 形状为 fixture，断言 `GAP: ci-merge-preview —` 且文案含 workflow 文件名 |
| AC-4 | 新增用例：无 workflow 目录、仅 `push` 触发、`pull_request` 但无 checkout，三种情形均断言 `SKIP: ci-merge-preview` |
| AC-5 | 新增用例：mock 分支保护返回 `false`/`true`，分别断言 GAP 与 PASS；`public-test` 仓库断言 SKIP |
| AC-6 | 新增用例复用既有 mock 的 403 与非 200 路径，断言 SKIP 与 GAP；不带 `--remote` 断言 SKIP |
| AC-7 | `bash -n templates/project/ci/merge-preview.sh`；`shellcheck` 同文件；脚本内 fail 分支 diff review |
| AC-8 | `.gitea/workflows/ci.yml` diff review 确认 `name: CI`、`verify:`、`on: pull_request` 三处逐字未变；本 PR 的 `CI / verify (pull_request)` 真实跑绿，并在日志里读到合并预览的 SHA |
| AC-9 | `06-运维手册与踩坑集.md` diff review |
| AC-10 | `bash codex/tests/smoke.sh` |
| AC-11 | verification 文档的交接项小节，逐仓列出 broker `gitea.protection.read` 的改动前回读值 |

## 部署与回滚

无部署。回滚方式是 `git revert` 本次唯一的最终 PR：新增的检查项、模板目录、
一个 workflow 步骤与一段文档随之全部消失，没有数据、迁移或主机侧残留。

`block_on_outdated_branch` 不由本次变更修改；人若已在 Gitea 打开它，revert 本 PR
不会把它关回去，两者互相独立。
