# AGENTS.md · AISoftPlatform 平台维护层

本文件只写维护平台仓自身的稳定规则（上限 5 KB）。边界见 [ADR 0001](docs/adr/0001-platform-boundary.md)，路由合同与执行引擎见 [ADR 0002](docs/adr/0002-deterministic-development-flow.md)，流程细节见 `03`，Matt 编排见 `04`，双工具见 `08`。项目使用平台的规则不写在这里。改动前先读 `README.md` 与相关分册。

## 边界

- 平台只交付标准流程、自定义技能、外部技能 pin 和 ADR 0001 的五类内核代码。项目名与项目专属值只出现在 ADR D3 允许的位置。
- 项目需求先回答：换成任意一个已注册项目还成立吗？不成立就退回项目仓，或先抽象成扩展点。
- 本地 Gitea 与本机仓库是事实来源，GitHub 只是镜像。
- Claude 与 Codex 对等维护平台，配置独立保存，新增提供者不得破坏另一个。complex 平台变更的最终 PR 由未参与实现的一方独立审查。

## Issue 与命名

- Issue 是唯一追踪主键。新 Change 绑定 exact `change/N-short-description`、`docs/changes/N-short-description/`、worktree `issue-N-short-description` 与唯一最终 PR；新文档名 `<role>-<short-description>-<YYMMDD>.md`，summary 的 `documents` 映射语义角色（细则见 `03`）。
- 已存在的 `change/N`、`docs/changes/N/` 和 `00-summary.md`、`01-spec.md`、`02-plan.md`、`03-verification.md` 只作读取与维护兼容，新写入不得创建。

## 判级与确认

- AI 依证据判级。small 只用于恢复或保持既有合同、局部且可简单 revert 的改动；新增功能、功能性更改、schema/数据迁移、外部契约、认证/权限/安全、共享核心、跨模块、CI/制品/部署/回滚、Agent 与平台治理一律 complex。信息不足或冲突时停在 `awaiting-triage`。
- 只有两个确认点：`approved`（确认合同并启动，不批准合并或部署）与提交唯一最终 PR 前确认。`triage/ready-for-agent` 不等于 `approved`。merge 后收尾按确定性流程完成。
- 确认点 1 之后，会话在合同内自主实现、测试和修 CI；遇到合同冲突、范围扩张、破坏性迁移、安全决策、外部阻塞或重复失败时停下升级。

## 开发编排

- 开发方式以[路由表](skills/aisoft-platform/references/route-policy.md)为准：`$triage #N` → `$to-spec #N` → `$to-tickets #N` → 按计划执行（Claude/Cursor 用 superpowers `executing-plans`，Codex 用 `$implement #N Txx`）；大需求先 `grill-me`，small 跳过 spec/plan。`$aisoft-matt-workflow` 把 Matt 接入平台合同；初始化调用 `$setup-matt-pocock-skills`，tracker 选择 `Other`，使用 `templates/docs/agents/issue-tracker.md`、`templates/docs/agents/triage-labels.md`、`templates/docs/agents/domain.md`。
- `gitea-analyze-change`、`gitea-spec-plan`、`gitea-development-loop`、`gitea-implement-change` 只是兼容 adapter；`gitea-platform-ops` 处理诊断、非生产部署与回滚规划。
- 会话只在 exact 分支追加线性本地 commit；确认点 2 之后复核范围与验证，经 broker 普通 fast-forward push 并开唯一最终 PR。本批在路线图与 E2E 表的行在同一 PR 写成合并后状态（`03` §7）。

## Git、合并与部署

- 保持受保护 `main`、现有 CI context、测试硬门、不可变制品与可回滚流程。只提交与当前任务有关的文件；应用变更走项目自己的分支和 PR。
- 禁止直推受保护 `main`、force-push、静默安装或更新全局 skills、未授权改 live 标签。
- 最终 PR 只由人合并；routine 自动合并与 VM 上的 Development Loop 已按 ADR 0002 退出，自动化最多止于 PR 候选。PR merge 不传递部署授权。
- AI 可参与开发/测试环境的首次部署与回滚验收；生产环境只运行已验证、版本化、可回滚的确定性脚本。

## 治理文件

- 只有 complex spec 明确授权才能改 `AGENTS.md`、技能、Agent 行为、broker 合同或 CI/部署脚本；治理文件由独立受控步骤应用后停止，fresh run 重读后再改 runtime。
- 单张 Issue 的合同、授权与状态只写在它的 `docs/changes/` 目录，不写进本文件、技能或 `docs/agents/`。

## 凭据与验证

- 不提交或打印 token、密码、`.env`、`auth.json`、Git credentials。
- 运维变更写明回滚方式并真实验证；未运行的测试不得写成通过。改 shell 后跑 `bash codex/tests/smoke.sh` 与 `bash -n`/ShellCheck。

## 目录

`01`–`08` 维护层分册 · `docs/adr/` 决策 · `docs/governance/` 整改路线 · `12`–`15` 参考文档 · `architecture/` 架构 schema 与校验 · `codex/` runtime、broker、工具与 vendor 快照 · `skills/` 唯一技能源 · `skill-for-claude/` Claude 侧安装脚本 · `sync/`、`platform-bootstrap/` 站点引导 · `templates/` 下发给项目的模板 · `docs/changes/` 每个 Issue 的证据 · `archive/` 只读历史。完整目录见 `README.md`。
