---
issue: 282
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/282
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - security
depends_on: []
status: pr-open
branch: change/282-ufw-format-compat
created: 2026-09-10
updated: 2026-09-10
reason: UFW解析语法及版本兼容变化，命中外部合同强制complex
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-ufw-format-compat-260910.md
  spec: spec-ufw-format-compat-260910.md
  plan: plan-ufw-format-compat-260910.md
  verification: verification-ufw-format-compat-260910.md
override_reason: ''
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/283
---

## 问题与授权

来源 NewEMaint #79，本会话已批准 UFW 解析兼容修复、测试和治理文档。目标仅 AISoftPlatform。#280 已合并，未完成依赖：无。基点 27b3f1e6fdbda7e26f6d679c17de97961ca198ae。

现场 b5485c58-53e5-4be6-be95-3d73e8ebd36a 只证明 parse-failed，不能锁定具体触发格式。本地固定 a3e7487e017479d4438e720b517cf369661ae3591336fa39ff55c4d53f66714c 复现四策略与25/26/27字符目标列；host_probes=0。

## AI 判级

外部解析语法与版本兼容变化，change/complex。只改 v2 runtime/schema、测试、指南与本目录。既有批准覆盖 spec/plan 的闭合修复范围；最终 PR manual，提交前确认。不修改 Gitea 配置或 UFW，不默认消除 protocol_state=missing GAP。
