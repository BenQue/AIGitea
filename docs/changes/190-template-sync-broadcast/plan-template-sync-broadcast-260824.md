---
issue: 190
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/190
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - ci-change
depends_on: []
status: approved
branch: change/190-template-sync-broadcast
created: 2026-08-24
updated: 2026-08-24
---

# Implementation plan：change 模板的上游同步广播

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | holder 声明：`vendors_change_templates` 进 governance manifest 与 contract，含缺省与 fail-closed 校验 | - | done |
| T02 | 版本号：`change-template-sync.json` 与覆盖「文件名 + 内容」的 digest 计算 | T01 | done |
| T03 | 广播工具：plan / `--verify-digest` / `--refresh-digest`，含 `unverified` 与非 `main` 分支标注 | T02 | done |
| T04 | 平台侧 CI 闸门：smoke 接入 digest 校验、非阻塞约束断言与行为测试 | T03 | done |
| T05 | 合同文档：`03` §3 新节与两份 skill reference 指针 | T03 | done |
| T06 | 真实模板改动端到端验证并回滚 | T04, T05 | done |

每个 ticket 都是可独立验收的垂直切片：T01 单靠 Python 测试可验，T02/T03 单靠 shell
行为测试可验，T04 靠 smoke 全跑，T06 是一次真实改动的端到端演练。

## Expected touch points

- T01：`codex/config/gitea-governance.json`、
  `codex/runtime/aisoft_gitea_governance/contract.py`、
  `codex/runtime/tests/test_vendored_change_templates.py`
- T02：`codex/config/change-template-sync.json`
- T03：`codex/tools/change-template-sync.sh`、`codex/tests/test-change-template-sync.sh`
- T04：`codex/tests/smoke.sh`
- T05：`03-Issue-Spec-Plan与单闸门开发流程.md`、
  `skill-for-codex/references/project-align.md`、
  `skill-for-codex/references/onboarding-runbook.md`
- T06：无新增文件（改动后回滚）

范围提示，不授权扩大 spec。特别地：**不触碰任何下游仓库**，**不改 `AGENTS.md`**。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 裁决落文 | review：summary「### 方向裁决」+ `03` §3 新节 |
| AC-2 holder 是声明 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_vendored_change_templates` |
| AC-3 模板有版本号 | `test-change-template-sync.sh` case 1/2/10（占位 digest 红、刷新后绿、缺一份模板硬错） |
| AC-4 不广播过不了 CI | `bash codex/tests/smoke.sh`；T06 的真实改动使该步变红 |
| AC-5 清单不依赖 checkout | `test-change-template-sync.sh` case 5/6/8（`holder-absent` 恒在清单内且为 `unverified`） |
| AC-6 逐项状态可分辨 | `test-change-template-sync.sh` case 5/7；真实运行里 rsdesign-new 的分支标注 |
| AC-7 非阻塞被钉住 | `test-change-template-sync.sh` case 10/11；smoke 的 `jq -e` 与文档 `grep` |
| AC-8 真实模板改动验证 | T06 三步：改模板 → `--verify-digest` 退 3 → `--refresh-digest` 出清单 → 回滚转绿 |
| AC-9 不改下游 | `git status --porcelain` 与 diff review：改动全部落在平台仓库内 |

## 部署与回滚

无部署影响。回滚即 revert 本次 PR：`vendors_change_templates` 未声明时的缺省与该键
不存在时的行为一致，`change-template-sync.json` 与新工具随之删除，
`aisoft-project-check.sh` 的 `change-templates` 语义自始至终未被改动。
