---
issue: 409
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/409
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - shared-core
  - external-contract
  - artifact
  - platform-governance
depends_on:
  - 402
status: approved
branch: change/409-catalog-pin-project-profile
created: 2026-10-21
updated: 2026-10-21
---

# R12 实施计划

## Ticket graph

| Ticket | 内容 | 依赖 |
|---|---|---|
| T01 | change_audit LEGACY 登记 + usage lock 可选键（读取与 `--adopt` 保留）+ 单测 | — |
| T02 | architecture CLI：`--catalog-releases`、可重复 `--profiles-dir`、pin 快照 review 降级 + 2026.08.3 快照 + installer + 单测与合成项目 profile 夹具 | — |
| T03 | `aisoft-project-check.sh`：LEGACY 行、catalog 落后 NOTE、项目 profile 目录、GAP 带诊断码 + test-project-check | T01, T02 |
| T04 | 文档（architecture/README、usage/CONTRACT、ADR D5）+ 发布包发版 + smoke 钉子棘轮 | T03 |
| T05 | 真实检出验收（NewEMaint、SFM、HSDB 临时副本）+ 全量 smoke + Codex 审查 + verification | T04 |

顺序执行，单写者。

## Expected touch points

见 spec `git_scope`。

## 数据库迁移

无。

## 测试与验收映射

| 验收 | 证据 |
|---|---|
| AC1/AC2 | T05 在临时副本上的 project-check 前后输出 |
| AC3 | 按裁决；默认 GAP 文案带 `DOCKERFILE_DECLARATION_REQUIRED` |
| AC4 | T05 HSDB profile validate/lock/validate --lock 输出 |
| AC5 | T01–T03 单测与 T05 手工反向证明 |
| AC6 | 全量 smoke 日志、`codex-review-409.md` |

## 回滚

revert 本 PR 并发新发布包版本；不涉及 live 配置。
