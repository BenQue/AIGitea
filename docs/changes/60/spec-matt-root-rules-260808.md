---
issue: 60
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/60
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on:
  - 57
status: approved
branch: change/60
pr_url:
created: 2026-08-08
updated: 2026-08-08
---

# Matt root instruction spec

## 目标与原因

把 Issue #57 已合并的 Matt 开发编排合同写入 AISoftPlatform 的两份主要 Agent 指令，使仓库初始化和
每 Issue 开发默认使用完整 Matt skills，同时继续由 AISoftPlatform 控制 Issue、合同、标签、
Controller、CI、PR、部署授权和人工合并。

本轮只起草和评审合同，不修改当前正在遵循的根级指令。合同经人工批准后，指令应用作为独立的
`change/60` implementation pass 执行。

## Acceptance criteria

- [x] **AC-1** 根级 `AGENTS.md` 使用语义 `summary`、`spec`、`plan`、`verification` 角色和 summary
  `documents` 显式映射描述新 change 文档；新文件采用
  `<role>-<short-slug>-<YYMMDD>.md`，并明确 Issue #57 之前的数字 basename 只作读取兼容。
- [x] **AC-2** 根级与 VM 全局指令把仓库初始化路由到 `$aisoft-matt-workflow` 和
  `$setup-matt-pocock-skills`；tracker 选择 Other，并使用 `templates/docs/agents/issue-tracker.md`、
  `triage-labels.md` 与 `domain.md`，不得另建一套 Gitea 模板。
- [x] **AC-3** 每 Issue 的主要开发路径明确为
  `$triage #N → $to-spec #N → $to-tickets #N → $implement #N Txx`；small 变更可按平台合同跳过
  spec/plan，但仍须先完成 triage、summary、判级和 `approved` 校验。
- [x] **AC-4** `gitea-analyze-change`、`gitea-spec-plan`、`gitea-development-loop` 与
  `gitea-implement-change` 在指令中只作为 Gitea label、文档 resolver/publisher、Controller 和旧调用方
  的兼容 adapter，不与 Matt skills 竞争主流程；`gitea-platform-ops` 继续独立处理运维边界。
- [x] **AC-5** 两份指令继续明确：Agent 仅在 exact `change/N` 创建本地原子 commit；Controller 才能
  fast-forward push、创建或更新唯一最终 PR、读取 CI 并投影状态；最终 merge 只由人操作，部署需要
  独立授权，`IMPLEMENT_PROVIDER=none` 仍是初始默认值。
- [x] **AC-6** 指令不得把 `triage/ready-for-agent` 当作平台 `approved`，不得允许自动 merge、直接 push
  `main`、force-push、静默安装或更新全局 skills、live 标签变更或生产部署。
- [x] **AC-7** 更新相关静态 smoke 断言，验证新命名、三份初始化模板、Matt 主路径、兼容 adapter、人工
  merge 与默认 provider 边界；完整 Python suite、`bash codex/tests/smoke.sh`、相关 `bash -n`、
  ShellCheck（若可用）、`git diff --check` 和 Secret 检查通过。
- [ ] **AC-8** Change 只产生一个 `Closes #60` PR，并停止在人工 merge gate；不执行应用部署。

## 接口、数据与兼容性影响

- 不新增 runtime API、schema 或标签；只更新人和 Agent 读取的 instruction contract。
- 新 change 文档必须依赖 summary 中的 `documents` mapping；旧四个数字 basename 保持只读兼容。
- Matt skills 保持 vendored upstream 原样；平台行为通过 `$aisoft-matt-workflow` 与现有窄 adapter 表达。
- Claude 与 Codex 配置仍独立，两个 provider 共享外层治理而不互相覆盖凭据或配置。

## 风险与回滚约束

- 根级指令变更必须在合同批准后的独立执行阶段完成；合同起草阶段不得提前应用。
- 指令文本与 smoke 断言必须在同一 commit 保持一致，避免只有文档宣告而无回归保护。
- 回滚为 revert 最终 PR；Issue #57 的 runtime、vendor snapshot 和 legacy reader 均不回滚。

## 非目标

- 不安装、更新或删除本机或 VM 的全局 Matt、GSD、Superpowers 或 Claude plugins。
- 不 provision/read-back live triage labels，不启用真实 provider，不启动 timer。
- 不修改 Matt vendored snapshot、runtime、Controller、业务项目、数据库、Secret 或部署环境。
- 不自动合并 PR，也不执行部署或生产操作。

## 未决问题

无；用户已于 2026-08-08 明确批准本 spec 与 plan。
