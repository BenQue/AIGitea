# AGENTS.md · AISoftPlatform v3

本仓库记录并维护基于 Gitea 的软件开发与自动化运维平台。Claude Code 与 Codex 共用同一套平台契约。

## 工作原则

- 先读 `README.md` 和与任务相关的编号分册，再修改文档或脚本。
- Issue 是所有需求、缺陷和平台变更的追踪主键；所有 Issue 生成 `00-summary.md`，复杂变更必须补齐关联的 `01-spec.md` 和 `02-plan.md`。
- AI 根据 Issue 声明、仓库证据、产品合同影响和强制风险规则判定最终有效复杂度；只有信息不足、内容冲突或风险边界无法确定时才停在 `awaiting-triage` 请求人澄清。
- small 只适用于恢复或保持既有产品合同的候选：Bug 修复、纯文档修正、只补测试、不改变外部行为的局部重构或维护；仍须满足范围局部、可简单 revert 且不触发强制复杂规则。
- 新增功能、功能性更改、schema/数据迁移、外部契约、认证/权限/安全、共享核心组件、跨模块/服务、CI/制品/部署/回滚，以及 Agent 或平台治理变更一律按 complex 处理。
- `approved` 表示合同已明确、允许启动 Development Loop，不表示批准合并或部署；最终 PR 合并是唯一交付硬闸门。
- Development Loop 可以在既定合同内自主实现、测试、修复和处理 CI 反馈；遇到合同冲突、范围扩张、破坏性迁移、安全决策、外部阻塞或重复失败时必须停止并升级给人。
- 只有 complex 变更的 `01-spec.md` 明确授权时，Loop 才能修改 `AGENTS.md`、Agent 行为、controller、CI/部署脚本或其他治理文件；判级或执行同一变更的运行不得修改本次运行正在遵循的 `AGENTS.md`。
- AI 可以参与开发/测试环境的部署设计、首次部署、调试和回滚验收；生产环境只运行已经验证、版本化、可回滚的确定性脚本。
- 保持受保护的 `main`、现有 CI context、测试硬门、不可变制品和可回滚流程。
- Claude 与 Codex 配置独立保存；新增一个提供者时不得破坏或删除另一个。
- 不提交或打印 token、密码、`.env`、`auth.json`、Git credentials 等凭据。
- 运维变更必须说明回滚方式，并用真实命令验证；未运行的测试不得写成通过。
- 修改 shell 脚本后运行 `bash codex/tests/smoke.sh` 和相应的 `bash -n`/ShellCheck（若环境可用）。

## 目录

- `01`–`07`：现有平台 as-built 文档。
- `08-Codex双工具共存与实施.md`：Codex 方案、实施步骤与验收状态。
- `09-v3平台简化与Loop-Engineering文档改造规划.md`：v3 决策、文档迁移、Loop 与部署边界。
- `codex/skills/`：可部署到 `$HOME/.agents/skills/` 的 Codex 原生 skills 源。
- `codex/agent/`：VM 上与 Claude 脚本并存的 Codex agent 与 provider router。
- `codex/install-vm.sh`：安装 skills/agent 脚本，不复制凭据。
- `templates/docs/changes/_template/`：新项目可复制的 v3 summary/spec/plan/verification 模板。

## Git

- 只提交与当前平台任务有关的文件。
- 不直接修改试点应用或 Gitea 的受保护 `main`；应用变更走独立分支和 PR。
