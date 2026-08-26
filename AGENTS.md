# AGENTS.md · AISoftPlatform v3

本仓库记录并维护基于 Gitea 的软件开发与自动化运维平台。Claude Code 与 Codex 共用同一套平台契约。

## 工作原则

- 先读 `README.md` 和与任务相关的编号分册，再修改文档或脚本。
- Issue 是所有需求、缺陷和平台变更的追踪主键；新 Change 绑定同一个 exact `N-short-description`：branch 使用 `change/N-short-description`，semantic docs 使用 `docs/changes/N-short-description/`，worktree basename 使用 `issue-N-short-description`，并且只有一个最终 PR。编号仍是唯一主键，slug 只用于人类识别。
- `short-description` 使用 2–4 个 lowercase ASCII kebab-case segment、最长 32 字符，并至少包含一个字母；branch、目录、worktree、文档 basename 与 front matter 的编号和 slug 必须完全一致。新 change 文档使用 `<role>-<short-description>-<YYMMDD>.md`；`summary` front matter 的 `documents` 必须把 `summary`、`spec`、`plan`、`verification` 等语义角色显式映射到真实 basename。
- 已在 manifest-fixed remote 或 Git history 中存在的 `change/N`、`docs/changes/N/` 与 Issue #57 之前的 `00-summary.md`、`01-spec.md`、`02-plan.md`、`03-verification.md` 只作读取或维护兼容；新 writer、first push 和 first PR 不得创建纯编号名称，也不得批量重命名或删除历史对象。调用方不能用 `legacy` 开关绕过 evidence-derived compatibility。
- AI 根据 Issue 声明、仓库证据、产品合同影响和强制风险规则判定最终有效复杂度；只有信息不足、内容冲突或风险边界无法确定时才停在 `awaiting-triage` 请求人澄清。
- small 只适用于恢复或保持既有产品合同的候选：Bug 修复、纯文档修正、只补测试、不改变外部行为的局部重构或维护；仍须满足范围局部、可简单 revert 且不触发强制复杂规则。
- 新增功能、功能性更改、schema/数据迁移、外部契约、认证/权限/安全、共享核心组件、跨模块/服务、CI/制品/部署/回滚，以及 Agent 或平台治理变更一律按 complex 处理。
- `approved` 表示人已确认合同并允许启动 Development Loop，不表示批准合并或部署。日常会话默认只保留两个确认点：合同/启动确认；提交唯一最终 PR 前确认。merge 后的终态核对、文档检查、worktree/本地分支清理与会话归档按确定性流程完成，不再增加确认点。
- Development Loop 可以在既定合同内自主实现、测试、修复和处理 CI 反馈；遇到合同冲突、范围扩张、破坏性迁移、安全决策、外部阻塞或重复失败时必须停止并升级给人。
- 只有 complex 变更映射的 `spec` 明确授权时，才能修改 `AGENTS.md`、Agent 行为、controller、CI/部署脚本或其他治理文件。判级或普通 implementation run 不得修改本次运行正在遵循的 `AGENTS.md`；治理文件必须先由独立、只修改治理合同的受控步骤应用并停止，后续 fresh run 重新读取后才能实施 runtime。
- AI 可以参与开发/测试环境的部署设计、首次部署、调试和回滚验收；生产环境只运行已经验证、版本化、可回滚的确定性脚本。
- 保持受保护的 `main`、现有 CI context、测试硬门、不可变制品和可回滚流程。
- Claude 与 Codex 配置独立保存；新增一个提供者时不得破坏或删除另一个。
- 不提交或打印 token、密码、`.env`、`auth.json`、Git credentials 等凭据。
- 运维变更必须说明回滚方式，并用真实命令验证；未运行的测试不得写成通过。
- 修改 shell 脚本后运行 `bash codex/tests/smoke.sh` 和相应的 `bash -n`/ShellCheck（若环境可用）。

## 初始化与开发编排

- 仓库初始化先完成 AISoftPlatform onboarding，并用 `$aisoft-matt-workflow` 校验 Issue、权限、受保护 `main`、required CI、文档和部署边界；随后调用 `$setup-matt-pocock-skills`，tracker 选择 `Other`，直接使用 `templates/docs/agents/issue-tracker.md`、`templates/docs/agents/triage-labels.md` 和 `templates/docs/agents/domain.md`，不得另建一套 Gitea 模板。
- 每个 Issue 的主要开发路径是 `$triage #N` → `$to-spec #N` → `$to-tickets #N` → `$implement #N Txx`。small 变更可按平台合同跳过 spec/plan，但仍须先完成 triage、映射的 summary、AI 判级和 `approved` 复核。
- `$aisoft-matt-workflow` 负责把完整 Matt skills 接入平台合同。`gitea-analyze-change`、`gitea-spec-plan`、`gitea-development-loop` 和 `gitea-implement-change` 只保留为 Gitea label、语义文档 resolver/publisher、Controller 和旧调用方的兼容 adapter，不定义第二套开发方法；`gitea-platform-ops` 独立处理诊断、非生产首次部署、事件证据和回滚规划。
- Agent 只能在 exact `change/N-short-description` 创建符合 plan frontier 的本地原子 commit；existing legacy `change/N` 只有在 Controller 读回 remote/history evidence 后才能维护。Controller 在复核编号/slug、唯一 active branch/docs/PR、提交、范围和验证后，才能 fast-forward push、准备唯一最终 PR、读取 CI 并投影状态；提交 PR 必须先取得绑定 exact Issue、branch 与 `manual|routine-auto` policy 的确认，范围内 CI 修复不重复询问。
- routine auto 只适用于 repository manifest 分类为 `internal-application`、显式启用、required contexts 非空且最终仍满足 `effective_complexity=small`、`contract_effect=restore|unchanged`、局部可逆、无 forced risk、非阶段/里程碑完结的 PR。`aisoft-platform`、public-platform 与 contexts 为空的仓库固定 disabled。它必须由独立 per-project routine merger 经唯一 broker typed operation 对最终 exact head SHA 重跑全部硬门后合并。complex/major、阶段或里程碑完结、安全、数据、共享核心、跨模块/服务、CI/制品/部署/回滚和 Agent/平台治理一律 manual；Issue #208 自身不得自动合并。
- manual 最终 PR 仍只由人合并；provider、project agent、platform manager、shared bot 和 site admin 都不得成为 routine merger。Gitea 1.26.4 没有 merge-only ACL；routine identity 的 ordinary Git 禁令由 broker-exclusive credential custody、typed operation、canonical manifest binding、final-head gates 与 zero fallback 保证，且该 identity 不在 main push/force allowlist。routine hard gate 失败必须 fail closed，不能降级到更宽权限身份、force/scheduled merge 或自动 fallback。PR merge 不传递部署授权。
- `triage/ready-for-agent` 不等于平台 `approved`。禁止直接 push 受保护的 `main`、force-push、静默安装或更新全局 skills、未经合同授权修改 live 标签，以及未经独立授权部署；生产环境不得由 AI 执行临时命令。
- `IMPLEMENT_PROVIDER=none` 是文档、skill 工作和项目初始 profile 的默认值；每个项目必须完成自己的 acceptance matrix 后才能显式启用 provider。

## 目录

- `01`–`07`：现有平台 as-built 文档（03 流程、04 Matt 编排与 Loop、06 运维踩坑、07 内网平移）。
- `08-Codex双工具共存与实施.md`：Codex 方案、实施步骤与验收状态。
- `09-v3平台简化与Loop-Engineering文档改造规划.md`：v3 决策、文档迁移、Loop 与部署边界。
- `12-Linux-GitHub-Gitea-双服务器自动部署方案.md`：Linux 内网三角色交付合同（文件名保留早期「双服务器」提案以维持链接）。
- `12-Windows平台自动部署方案.md`、`13-项目结果迁移与内网切换实施手册.md`、`14-Windows部署与迁移验收清单.md`、`15-VMware-Fusion-Windows-ARM原型实施手册.md`：Windows 与内网迁移线（尚未实施）。
- `architecture/`：技术架构 catalog/profiles/schemas/lock 的唯一平台事实源与 CLI。
- `docker-release/`：Docker-first 发布合同（release manifest、transport、capability gate、CLI）。
- `sync/`：GitHub 入站同步的 scm-ci 侧脚本与 systemd 单元。
- `codex/skills/`：可部署到 `$HOME/.agents/skills/` 的 Codex 原生 skills 源（含 `aisoft-matt-workflow`）。
- `codex/vendor/mattpocock/`：固定版本的 Matt Pocock skills 上游快照与 manifest。
- `codex/runtime/`：`aisoft_loop`、`aisoft_release`、`aisoft_architecture`、`aisoft_host_access`、`aisoft_gitea_governance` Python 运行时与测试。
- `codex/agent/`：VM 上与 Claude 脚本并存的 Codex agent 与 provider router。
- `codex/tools/`、`codex/config/`：治理/运维工具与 canonical manifests（labels、gitea-governance、host-access-broker、host-role）。
- `codex/install-vm.sh`、`codex/install-skills.sh`、`codex/install-host-role.sh`、`codex/install-host-access-broker.sh`：安装 runtime/skills/guard/broker，不复制凭据。
- `skill-for-codex/`：复合 `aisoft-platform` skill（Codex 版）与 onboarding/private-access references。
- `templates/docs/changes/_template/`：v3 summary/spec/plan/verification 模板；`templates/docs/agents/`：Matt tracker/triage/domain 配置模板；`templates/agent/`、`templates/hosts/`、`templates/loop/`：profile 与 verifier 示例。
- `archive/`：历史实施记录与旧方案（含 10/11），只读参考，不作当前配置来源。

## Git

- 只提交与当前平台任务有关的文件。
- 不直接修改试点应用或 Gitea 的受保护 `main`；应用变更走独立分支和 PR。
