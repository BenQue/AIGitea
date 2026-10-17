---
issue: 364
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/364
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
depends_on: []
status: approved
branch: change/364-platform-boundary-adr
created: 2026-10-17
updated: 2026-10-17
git_scope:
  - docs/changes/364-platform-boundary-adr/summary-platform-boundary-adr-261017.md
  - docs/changes/364-platform-boundary-adr/spec-platform-boundary-adr-261017.md
  - docs/changes/364-platform-boundary-adr/plan-platform-boundary-adr-261017.md
  - docs/adr/0001-platform-boundary.md
  - docs/governance/remediation-roadmap.md
---

## 目标

把平台边界写成一份可引用的决策，并据此给出分批整改路线。合同正文就是
[ADR 0001](../../adr/0001-platform-boundary.md) 的 D1–D10 与 [整改路线](../../governance/remediation-roadmap.md)，本 spec 不重复其内容。

负责人于 2026-10-17 在项目线程“平台治理整改”确认本合同，批准锚为 `eec265d`。

## 验收标准

- AC1：ADR D1、D2、D5 列出允许的内核代码类别、不进平台的内容和每个顶层目录/runtime 包的归类。
- AC2：ADR D3、D4 写出项目数据允许出现的位置和准入问题。
- AC3：ADR D6 写出两层分离的合同入口、安装面、验收和交叉审核规则。
- AC4：ADR D9 写出治理成本预算。
- AC5：路线把评审 §6 A–E 每项落到批次或明确延期，并标出涉及 NewEMaint 的批次。
- AC6：`check-change-documents` 通过；`bash codex/tests/smoke.sh` 相对 main 基线没有新增失败（main `f78e732` 在 macOS 上已有 15 个 #360 canonical 测试失败，并入路线 R1 处理）。

## 边界

- `git_scope` 五个文件是全部范围。
- 本票不修改任何治理文件；ADR 中要求修改 `AGENTS.md`、技能、smoke 和 runtime 的内容，由路线 R1 起的独立 Issue 实施。
- 不改变 NewEMaint 当前依赖的平台能力。
