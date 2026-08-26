---
issue: 207
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/207
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - ci
  - shared-core
depends_on: []
status: approved
branch: change/207-codex-primary-readiness
created: 2026-08-26
updated: 2026-08-26
---

# Codex 主处理就绪规格

## 目标与原因

让 Codex 能按同一平台合同独立完成 Issue 分析、实现、验证、PR 与 CI 修复，减少合同内
的重复确认；同时修复 development complex 的真实执行阻塞，并让 source、installed、
live 三层状态可以只读辨认。

## Acceptance criteria

- [ ] AC-1：`development + complex` 合同没有 plan 时，Controller 确定性返回 `T01`；
  `production + complex` 没有 plan 时仍拒绝执行。
- [ ] AC-2：Controller/contract 回归测试覆盖 development 成功、production 拒绝以及
  带 plan 的既有 ticket graph 行为。
- [ ] AC-3：Codex、Claude、模板和主流程文档统一到 canonical 10 个 change type、
  27 个 label、同一 verification 判据与 development/production 文档规则。
- [ ] AC-4：新增 Codex 原生 `issue-session-flow`，明确合同获批后实现、测试与 CI 修复
  自动推进，只有合同冲突、范围扩张、安全/破坏性决策、外部阻塞或重复同根失败才停下；
  当前最终 PR 仍由人合并。
- [ ] AC-5：只读 readiness 工具分别报告 source、installed Codex/Claude skills 与
  live repo/protection；不可达和未安装不得伪装成 PASS，工具不得执行安装或 live mutation。
- [ ] AC-6：本 Issue 的真实 PR workflow 成功运行，并从 Gitea 读回准确 context；只有
  该证据成立后，`codex/config/gitea-governance.json` 才声明该 required context。
- [ ] AC-7：`bash codex/tests/smoke.sh` 全量通过；新增/修改 shell 通过 `bash -n`，
  ShellCheck 在可用时通过。
- [ ] AC-8：唯一最终 PR 可简单回滚；skills/runtime 安装、live branch protection apply
  和部署均保持 `NOT RUN`，等待独立授权。

## 接口、数据与兼容性影响

- `Contract` 增加显式 `change_control` 事实，缺省保持 `production`，现有调用兼容。
- `select_frontier_ticket` 只对 development complex 无 plan 路径返回合成 `T01`；
  production 与现有 graph 解析不变。
- 新增只读 shell CLI，不改变 broker API，不增加写操作。
- canonical governance manifest 的 required context 仅在真实成功读回后更新；live 保护规则
  不在本 PR 内应用。

本规格授权修改以下非治理中枢文件；不授权修改 `AGENTS.md`：

- `codex/runtime/aisoft_loop/contract.py`
- `codex/runtime/aisoft_loop/controller.py`
- `codex/runtime/tests/test_contract.py`
- `codex/runtime/tests/test_controller.py`
- `codex/skills/gitea-analyze-change/SKILL.md`
- `codex/skills/gitea-spec-plan/SKILL.md`
- `codex/skills/gitea-development-loop/SKILL.md`
- `codex/skills/aisoft-matt-workflow/SKILL.md`
- `codex/skills/issue-session-flow/SKILL.md`（新增）
- `skill-for-codex/SKILL.md`
- `skill-for-codex/references/onboarding-runbook.md`
- `skill-for-codex/references/project-align.md`
- `skill-for-claude/aisoft-platform/SKILL.md`
- `skill-for-claude/issue-session-flow/SKILL.md`
- `03-Issue-Spec-Plan与单闸门开发流程.md`
- `04-Agent编排与定时任务.md`
- `08-Codex双工具共存与实施.md`
- `codex/check-drift.sh`（新增）
- `codex/tools/aisoft-platform-readiness.sh`（新增）
- `codex/tests/test-codex-drift.sh`（新增）
- `codex/tests/test-platform-readiness.sh`（新增）
- `codex/tests/smoke.sh`
- `codex/config/gitea-governance.json`（仅 AC-6 证据成立后）
- 本 Issue 映射的 summary/spec/plan/verification。

## 风险与回滚约束

- 所有 production 对照测试必须先于放宽路径合并。
- readiness 工具输出只保留非凭据状态字段，不打印 token、认证配置或完整响应。
- 若真实 PR context 未成功读回，不更新 governance manifest，并把 AC-6 记为未完成。
- 回滚单一 PR 可恢复原行为；live 未应用，因此无 live 回滚步骤。

## 非目标

- 不启用 routine PR 自动合并；该工作由 #208 处理。
- 不安装或更新 `$HOME/.agents/skills`、`$HOME/.claude/skills` 或 VM runtime。
- 不修改 live Gitea 分支保护、身份、权限、runner 或部署环境。
- 不重写历史 change 文档。

## 未决问题

无。
