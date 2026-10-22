---
issue: 423
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/423
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/423-karpathy-principles
created: 2026-10-22
updated: 2026-10-22
---

# Plan：共享工程原则

本计划只用于交付这份纲领性指导；原则正文不包含本计划的步骤。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 在独立治理步骤应用共享原则、三个入口、使用合同与发布包登记，做局部核验并 commit 后停止 | - | done |
| T02 | fresh run 重读合同，完成导出/回归/场景评审和另一提供者独立审查，形成最终 PR 候选 | T01 | done |

## Expected touch points

- T01：spec 的七份治理/发布文件与本 Issue 文档；原子提交主题包含 `#423 T01`。按负责人已确认的纲领性定位收紧并应用 patch；`usage/bundle.json` 增加 reference 的 skill member，并用既有 `--release` 追加 minor release。
- T02：仅本 Issue 验证记录与审议索引的本 Issue 行；发现超范围实现问题停下升级。禁止为通过检查削弱断言或改 runtime/test/CI。
- 负责人本轮已批准 T01/T02。T01 治理写入在原子 commit 后结束；T02 由 fresh Claude Code 只读进程重新读取合同后独立审议，本会话仅整理证据，不修改 runtime；不新增产品确认点。

T01 同范围返修均独立提交后停止写入。T02 已完成两次完整 smoke、最终文案的定向安装/分发回归、六场景文本审议和三轮 Claude Code 双轴只读审议；R3 均 PASS。精确 head、证据与非阻断建议见 verification，后续只做记录归档。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | 既有 `test-install-skills.sh` / `test-install-claude-skills.sh` / `test-usage-bundle.sh`；隔离 `usage-bundle.sh --build` 后核对三个 provider 的 reference 字节与相对链接 |
| AC-2–4 | 对照六场景和反例审阅；逐块 diff 检查；不称为真实模型验收 |
| AC-5 | `bash codex/tools/aisoft check-change-documents`、既有 targeted tests、`LC_ALL=C bash codex/tests/smoke.sh` |
| AC-6 | `usage-bundle.sh --verify --baseline-ref` 对照实施基线；固定上游 SHA；T01 commit/停止与 fresh run 记录；另一提供者 exact-head 审查 |

T01 局部检查：`git diff --check`、相对链接、bundle verify 与隔离 build；T02 fresh run 执行必需回归。未修改 shell，不新增 shell 专用测试。
完整 smoke 已覆盖的 targeted 测试不无故重复。各检查的准确参数以现有工具入口为准；禁止实际 HOME 安装和项目 `--adopt`。

## 部署与回滚

无部署。治理源码与发布包回滚按 spec，不重写发布历史。最终 PR 前仍须确认点 2，合并由人完成；安装与项目采用单独授权。
