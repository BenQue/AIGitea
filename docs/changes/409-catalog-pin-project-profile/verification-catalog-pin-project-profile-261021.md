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
status: pending
branch: change/409-catalog-pin-project-profile
created: 2026-10-21
updated: 2026-10-21
---

# R12 验证记录

## 基线与范围

- 基线：`origin/main` = `38ddc920`（R11 PR 405 合并后）。
- 2026-10-21 基线 project-check（平台源码检查器，项目本地检出只读）：NewEMaint `change-documents` GAP 16 条、
  `architecture-lock` GAP（`PROJECT_CATALOG_MISMATCH`）；SFM `change-documents` GAP 54 条、`architecture-lock`
  GAP（`DOCKERFILE_DECLARATION_REQUIRED`）；HSDB 无 `.aisoft/architecture.json`。
- 预研：以 git 中 2026.08.3 的 catalog 与 profile 重建 NewEMaint lock（跳过 Dockerfile 规则），与其已提交 lock
  逐字段相等；SFM 在当前 catalog 下同样相等。两者剩余唯一失败是 `DOCKERFILE_DECLARATION_REQUIRED`。

## 结果

NOT RUN（实现尚未开始）。
