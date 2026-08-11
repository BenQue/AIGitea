---
issue: 85
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/85
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
depends_on: []
status: contract-drafting
branch: change/85-codex-skill-matt-alignment
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Spec

## 目标与原因

复合技能 `skill-for-codex/SKILL.md` 与其 onboarding runbook 仍描述 #57/#60/#75 之前的开发合同
（gitea-* 为主路由、`change/N`、`00-summary.md` 数字命名、八标签无 triage 维度、复制已不存在的
数字模板文件），与 AGENTS.md / codex/global-AGENTS.md 现行合同冲突，形成 #60 预警的
「两套主流程」。本变更把该技能对齐到现行合同。

## Acceptance criteria

- [ ] AC-1 SKILL.md 含 `$aisoft-matt-workflow` 与 `$triage #N` → `$to-spec #N` → `$to-tickets #N` → `$implement #N Txx` 主路径；`gitea-*` 五技能以 compatibility adapter 语义出现（labels/语义文档/Controller/legacy 调用方；`gitea-platform-ops` 独立）。
- [ ] AC-2 SKILL.md 与 runbook 的新写入指引全部使用 readable 元组（`change/N-short-description`、`docs/changes/N-short-description/`、`<role>-<short-description>-<YYMMDD>.md`、`documents` 映射）；数字名仅以 pre-#57 legacy 兼容形式出现。
- [ ] AC-3 标签表述含 Matt triage 维度与 24-label manifest；`triage/ready-for-agent` ≠ `approved` 写明。
- [ ] AC-4 runbook 模板复制清单与 `templates/docs/changes/_template/` 实际文件名（summary/spec/plan/verification.md）逐一存在。
- [ ] AC-5 smoke 既有断言字符串保留：SKILL.md 含 ``private-repository `404` `` 与 `AISOFT_ONBOARDING_MODE=software-repository`；runbook 含 `ensure-gitea-collaborator.sh` 与 `gitea-governance.json`。
- [ ] AC-6 `bash codex/tests/smoke.sh` 全绿（#82 修复已合并则直接运行；否则按 #77 先例临时叠加验证后还原）。

## 接口/数据/兼容影响

仅 Agent 指令文档；不改 runtime、labels JSON、脚本或部署。`#35 治理清单`、`ci-bot 迁移兼容 gate`、
`host-role gate`、`architecture onboarding` 等章节保持不变。

## 治理授权

本 spec 明确授权修改：`skill-for-codex/SKILL.md`、`skill-for-codex/references/onboarding-runbook.md`。
不授权修改 `AGENTS.md`、`codex/global-AGENTS.md`、`codex/skills/*`、任何脚本或 Claude 侧文件。

## 非目标

- 不重写 `references/private-gitea-access.md`（无数字命名残留）。
- 不改变 governance/host-role/architecture 各 gate 的任何语义。
- 不安装或部署技能（安装属 #57 既定流程与后续变更）。
