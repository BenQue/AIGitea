---
issue: 420
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/420
change_type: docs
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/420-onboarding-guide
created: 2026-10-22
updated: 2026-10-22
---

# 新用户上手指南与简明使用手册

## 目标与原因

让一个新用户在自己的 Mac 上，用 Claude Code、Codex 或 Cursor 中任一种，按平台现行合同准备好环境并开始一个新项目的开发；
并且这条路径能由 AI 工具读着指南逐步带用户走完，每一步都有可执行的核对与明确的停下条件。

## 方案与决策

- **两份文件，各管一件事**：
  - `skills/aisoft-platform/references/getting-started.md`：AI 执行用的上手指南，随技能装到 Claude 与 Codex，并随发布包导出到项目级
    `.claude/skills/`、`.agents/skills/`、`.cursor/skills/`。用户对 AI 说「带我上手 AISoft 平台」即可触发。
  - `usage/USER-GUIDE.md`：给人读的简明手册，一屏读完的概念与三种工具的对照表，详细步骤只链接到指南。
    它是平台仓文档，不进发布包，避免为人读材料新增对齐检查项。
- **指南结构**（每步：做什么、谁做、核对命令、预期结果、失败时停下报告什么）：
  1. 认清角色：维护者做的（broker 安装、项目登记、发布包采用）与开发者做的分开；需要 sudo 或注册的步骤交给维护者，AI 不代执行。
  2. 本机环境，按工具分节：
     - 共用：平台检出位置约束、host-access broker 由维护者安装后的只读读回。
     - Claude Code：登录；技能来源（项目级 `.claude/skills/`，平台维护者另有 `skill-for-claude/install.sh`）；Matt 插件来源核对
       `check-plugin-pin.sh` 读回 `PIN_CLEAN`；superpowers 走 Claude 官方市场。
     - Codex：登录；项目级 `.agents/skills/`（含 Matt 快照与 `aisoft-matt-workflow`）；superpowers 走 Codex 官方市场。
     - Cursor：登录；只用项目级 `.cursor/skills/`（含 Matt 与 superpowers 快照）与 `.cursor/rules/aisoft-platform.mdc`，平台不往用户目录装任何东西。
     - 版本核对：`check-external-skill-versions.sh` 的读法（`PIN_DRIFT` 先过适配清单）。
  3. 新项目登记：只说明需要维护者完成什么、完成的判据是什么，步骤链接 onboarding-runbook，不复述。
  4. 采用使用发布包：维护者 `usage-bundle.sh --adopt` 进项目 change worktree（按所选工具传 `--tools`），经项目 PR 合入；
     开发者读回 `aisoft version`、`aisoft bundle status`、`aisoft project-check`。
  5. 第一张 Issue：建 Issue → `$triage` 判级与路由卡 → 确认点 1 回「确认」→ 实现与测试 → 确认点 2 回「开」→ 人合并 → 收尾；
     模型按路由卡 tier 选，映射链接 08 §7.3。
  6. 常见卡点：只列有平台证据的几条（broker `REQUEST_DENIED` 是操作表陈旧、私有 Gitea 匿名 404 不说明不存在、
     `PIN_NOT_INSTALLED` 的含义）。
- **范围 B（负责人 10-22 在项目频道同意从 #419 并入）**：把「`\$implement #N Txx` 是唯一实现入口」的旧写法改成与 #419 合并后
  `AGENTS.md` 开发编排段一致——开发方式以路由表为准，按计划执行时 Claude 与 Cursor 用 superpowers `executing-plans`，Codex 用
  `\$implement #N Txx`。涉及四处：`skills/aisoft-platform/SKILL.md` 的「Matt 主路径」条、`usage/CONTRACT.md` §2「编排路径」、
  `templates/project/AGENTS.md` 的每 Issue 开发路径段、`templates/docs/agents/issue-tracker.md` 与平台仓自用副本
  `docs/agents/issue-tracker.md` 的 `\$implement` 条。只改实现入口的措辞，判级、`change_control`、`approved` 与两个确认点语义不变。
- **只写指针不复述合同**：流程合同只链接 `.aisoft/platform-usage.md` 与 `03`；命令与参数照抄现行源码。

## Acceptance criteria

- [ ] AC-1 指南按 Claude Code、Codex、Cursor 各有一节完整路径，每步有核对命令与预期结果；引用的每个脚本、子命令、参数在本 head 的源码中存在（逐条 rg 核对记入 verification）。
- [ ] AC-2 指南明确区分维护者步骤与开发者步骤，需要 sudo、注册 marketplace 或改 manifest 的步骤标为维护者动作，AI 不代执行。
- [ ] AC-3 简明手册单独成文；README 文档导航、指南与 SKILL.md 三处都能到达它或指南。
- [ ] AC-4 两份文件不含站点值与个人路径；`bash codex/tests/smoke.sh` 全绿，反向证明：在临时副本里往指南写入站点主机名，守卫变红。
- [ ] AC-5 `usage/bundle.json` 登记新 reference 并发布 1.13.0（带 notes 与 compatibility），`usage-bundle.sh --verify` 通过；`--build` 导出的三处项目级技能落点都含新指南。
- [ ] AC-7 上述四处（五个文件）对实现入口的说法与 `AGENTS.md` 开发编排段一致，仍保留 `\$implement #N Txx` 作为 Codex 入口；`rg` 不再找到把它写成唯一入口的旧句；smoke 全绿，发布包 1.13.0 同时覆盖这些成员。
- [ ] AC-6 未参与实现的 Codex 对候选 head 只读交叉审查得到 PASS，记入 verification 与 review-evidence-index。

## 接口、数据与兼容性影响

新增文件与导航行；范围 B 只校正实现入口措辞使其与已合并的 AGENTS.md 一致，不改流程语义、工具行为或 manifest。发布包 minor 升级（`compatibility: minor`），已 pin 的项目不变红。

## 风险与回滚约束

纯文档与发布包新版本；回滚即 revert 本 PR，已发布版本号不复用。

## 非目标

- 不改 onboarding-runbook 与 AGENTS.md；`usage/CONTRACT.md` 只改 §2「编排路径」一条的实现入口措辞（范围 B）。
- 不新增上手技能、不改安装器、不注册任何 marketplace、不在任何机器上安装或重装。
- 不改 #419 已合并的行。

## 未决问题

无。
