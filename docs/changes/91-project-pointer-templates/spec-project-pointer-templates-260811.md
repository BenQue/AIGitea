---
issue: 91
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/91
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: contract-drafting
branch: change/91-project-pointer-templates
pr_url:
created: 2026-08-11
updated: 2026-08-11
---

# Spec

## 目标与原因

「两个 AI 在具体项目里主动使用平台」依赖项目仓库内每会话必然注入的常驻指针
（Claude 读 `CLAUDE.md`，Codex 读 `AGENTS.md`）。平台缺项目级模板，9 个治理仓库各自手写，
指针覆盖与强度不受控（2026-08-11 审核核心建议第一层）。

## Acceptance criteria

- [ ] AC-1 `templates/project/AGENTS.md` 存在，含四段：平台声明（Issue 主键、readable 元组、
      单闸门、broker）、每 Issue 开发路径（Matt 四步 + small 跳过条件 + 升级条件）、
      工具分工（Claude=开发/设计，Codex=维护/部署；默认偏好非硬规则，provider 中立），
      项目事实占位（含「交付形态按项目 delivery profile 决定、流程不变量统一」表述）。
- [ ] AC-2 `templates/project/CLAUDE.md` 仅一行 `@AGENTS.md`。
- [ ] AC-3 runbook §2 指向 `templates/project/`，并写明存量仓库逐仓回补程序（独立 Issue/
      小 PR，不批量脚本改写）。
- [ ] AC-4 smoke 全绿；既有断言串保留。
- [ ] AC-5 不修改任何业务仓库、不改平台 AGENTS.md。

## 接口/数据/兼容影响

纯模板与 runbook 文档；不改 runtime/标签/部署。

## 治理授权

本 spec 明确授权：新增 `templates/project/{AGENTS.md,CLAUDE.md}`；修改
`skill-for-codex/references/onboarding-runbook.md` §2 的项目契约清单。

## 非目标

- 9 仓实际回补（逐仓独立 Issue，由本变更定义程序后另行执行）。
- 不定义项目级 CI/部署细节（由各项目 delivery profile 决定）。
