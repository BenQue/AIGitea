---
issue: 408
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/408
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - artifact
depends_on:
  - 392
  - 402
status: spec-review
branch: change/408-peer-review-evidence
created: 2026-10-21
updated: 2026-10-21
---

# R15 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理步骤：`03` §3/§7（approval 只写 summary、审查方与记录规则）、`08` §7.1 最小能力集表、四份技能与 `usage/CONTRACT.md` 改写建 PR 步骤为 `aisoft open-pr`；单独 commit 后停止，fresh 重读 | - | pending |
| T02 | 能力集读回：`check-external-skill-versions.py` 三行 `CAPABILITY` 与外部原因登记，测试与反向证明 | T01 | pending |
| T03 | broker 推送闸门：`aisoft_main_integration.py` 不读 spec 状态，测试与反向证明 | T01 | pending |
| T04 | `aisoft open-pr`：正文本地校验、首推、建 PR、回填、提交、再推；假 broker 测试（正常、零请求、重跑幂等） | T03 | pending |
| T05 | 模板：verification 固定「交叉审查」表，spec/plan 去 `status`；`--refresh-digest`；发布下一空闲版本 | T04 | pending |
| T06 | `docs/governance/review-evidence-index.md` 回填，路线图 R15 行 | T01 | pending |
| T07 | SFM Cursor 会话 small Issue（按未决问题 3 的决定）；E2E 表「工具」列 | T05 | pending |
| T08 | 全量 smoke、`check-change-documents`、本批 verification、Codex 只读交叉审查直到 PASS | T02–T07 | pending |

按 superpowers `executing-plans` 依 Txx 顺序内联执行，同一时刻一个写者；每张 ticket 至少一个原子 commit，主题含 `#408 Txx`。

## Expected touch points

- T01：`03-Issue-Spec-Plan与单闸门开发流程.md`、`08-双工具共存与实施.md`、`skills/aisoft-platform/SKILL.md`、`skills/aisoft-platform/references/onboarding-runbook.md`、`skills/issue-session-flow/SKILL.md`、`skills/gitea-development-loop/SKILL.md`、`usage/CONTRACT.md`、`codex/runtime/tests/test_session_contract.py`
- T02：`codex/tools/check-external-skill-versions.py`、`codex/tests/test-external-skill-versions.sh`
- T03：`codex/runtime/aisoft_main_integration.py`、`codex/runtime/tests/test_main_integration.py`
- T04：`codex/tools/aisoft`、`codex/tests/test-aisoft-entry.sh`
- T05：`templates/docs/changes/_template/{spec,plan,verification}.md`、`codex/config/change-template-sync.json`、`usage/bundle.json`
- T06：`docs/governance/review-evidence-index.md`、`docs/governance/remediation-roadmap.md`
- T07：`docs/governance/platform-e2e-acceptance.md`；SFM 仓自己的 change 目录与采用文件
- T08：`codex/tests/smoke.sh`、`codex/tests/smoke-pin-baseline.json`（新钉子同 PR 抬基线）、本目录 verification

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-external-skill-versions.sh`（三种结论、删登记项反向证明）；本机 `check-external-skill-versions.sh --repo <SFM>` 读回 |
| AC-2 | 索引逐行对照 verification、PR 正文与项目库 `codex-review-*.md` |
| AC-3 | 模板 diff；`03` §7 diff；本批 verification 的交叉审查表 |
| AC-4 | `python3 -m unittest` 跑 `test_main_integration.py` 新增用例（含反向证明） |
| AC-5 | `bash codex/tests/test-aisoft-entry.sh` 新增用例；本批 PR 由 `aisoft open-pr` 开出 |
| AC-6 | SFM Issue、PR 与项目侧 verification 链接；E2E 表 |
| AC-7 | `bash codex/tests/smoke.sh`、`usage-bundle.sh --verify`、`change-template-sync.sh --verify-digest`、`codex-review-408.md` |

## 部署与回滚

无应用部署。合并后负责人两台重装 broker 与技能，会话读回 `check-installed-drift`。回滚：整 PR revert 后再重装；SFM PR 单独 revert。
