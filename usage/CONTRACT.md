# AISoft 平台使用合同

> 这是平台交付给**项目使用层**的唯一合同入口（ADR 0001 D6）。它随版本化使用发布包下发，
> 项目把本文件复制为 `.aisoft/platform-usage.md`，并在 `.aisoft/platform-usage.lock.json` 记下
> 所用的发布包版本。本文件只写流程与项目必须自己声明的扩展点；任何项目的构建、发布、部署
> 步骤都不在这里。平台自身的维护规则在平台仓 `AGENTS.md`，不属于本合同。

## 1. 版本与跟进

- 项目使用哪一版平台合同，以本仓 `.aisoft/platform-usage.lock.json` 的 `bundle_version` 为准。
  平台仓前进不改变已 pin 版本的含义，也不让项目的对齐检查自发变红。
- 升级到新版本是项目自己的 Issue：平台维护者用平台侧 `usage-bundle.sh --adopt` 把最新版本写进本仓的
  change worktree，经项目自己的判级与唯一 PR 合入。每个版本带一句 `notes` 与兼容级别
  `compatibility`（`patch`/`minor`/`major`）；落后区间含 `major` 时对齐检查记 GAP，否则只提示。
- 发布包里的文件分六类：逐字节副本（本文件、`CLAUDE.md`、change 模板四件套）、会话工具（`.aisoft/bin/aisoft`
  与 `.aisoft/lib/`，见 §5）、`AGENTS.md` 的
  常驻指针两节、初始化种子（`docs/agents/` 三件套、CI 示例，项目可改）、平台技能（装到各工具的
  技能目录）、外部技能包快照（平台 pin 的 Matt 与 superpowers 原文：两包都到 `.cursor/skills/`，
  Matt 另到 `.agents/skills/`；Claude 与 Codex 的 superpowers 来自各自官方 marketplace）。
  逐字节副本、会话工具与指针由对齐检查按 pin 的版本核对；外部技能包由 `check-external-skill-versions.sh --repo` 核对。
- 项目对平台的需求以平台 Issue 提出。平台按准入规则判断：换成任意一个已注册项目还成立才进入
  平台；不成立的留在项目仓，或先由平台抽象成扩展点，项目数据留在项目侧。

## 2. 流程不变量

- **Issue 是唯一主键。** 任何需求、缺陷、变更先建 Issue。新变更使用可读元组：分支
  `change/N-短描述`、目录 `docs/changes/N-短描述/`、文档 `<role>-<短描述>-<YYMMDD>.md`
  （summary front matter `documents` 映射语义角色）、唯一 PR（正文 `Closes #N`）。纯数字名称只对
  已存在的历史对象作读取或维护兼容。
- **判级依证据。** 先判合同影响：恢复或保持既有合同才是 small 候选；新增或改变合同是 complex；
  说不清停在 `awaiting-triage`。功能新增或变更、schema 与数据迁移、外部契约、认证权限安全、
  共享核心、跨模块、CI/制品/部署/回滚、Agent 与治理一律 complex。small 还要范围局部、可简单
  revert、验收可测。
- **编排路径。** `$triage #N` → 判级。complex 按 governance manifest 中本仓的 `change_control`：
  `production`（未声明时的默认）先 `$to-spec #N` → `$to-tickets #N` → 按计划执行（开发方式以路由表为准：Claude 与 Cursor
  用 superpowers `executing-plans`，Codex 用 `$implement #N Txx`）；
  `development` 不写 spec/plan，验收标准取自 Issue 正文，以合成 `T01` 实现。small 默认不要求
  spec/plan。所有路由都要交付 summary `required_docs` 声明的文档（例如欠验证记录时的 `verification`）。
  三者都要 `approved` 复核后才进入实现；`triage/ready-for-agent` 不等于 `approved`。
- **两个确认点。** 人确认 Issue 合同并启动开发；本地实现与验证完成后，人确认提交唯一最终 PR，
  并固定 exact Issue 与分支。两点之间 AI 在合同内自主实现、测试和
  修复 CI；合同冲突、范围扩张、破坏性迁移、安全决策、外部阻塞或同因三次失败时停下升级。
  merge 后的终态核对、文档检查与清理按确定性流程完成。
- **单闸门。** 最终 PR merge 是唯一交付硬闸门，只由人合并。会话与项目 agent 不 merge、
  不直推受保护 `main`。PR merge 不传递任何部署授权。
- **远端写路径。** Gitea 与 Git 的写操作走 host-access broker 的 typed 操作，不拼 raw token、
  不传 URL 或 refspec。并行会话各用自己的 change worktree。
- **没有无人值守引擎。** 自动化最多止于 PR 候选（平台 ADR 0002）；项目选用的每个工具
  （Claude、Codex、Cursor）各自完成使用层验收。

## 3. 部署流程不变量

平台只规定所有交付形态共同遵守的流程，不规定步骤：

- 不可变制品：一次构建，带版本、完整 merge SHA 与校验和；producer 工具链钉版本，依赖 lock
  文件进仓，restore 用 locked-mode。
- 测试与生产同字节晋级：生产只消费测试环境验收过的同一制品，不重新构建。
- 部署前备份，migration 向后兼容，migration 与应用启动分离。
- 健康检查返回精确 release SHA。
- 回滚路径是版本化脚本的一部分，并已实测。
- 生产 script-only：生产只运行已验证、版本化、可回滚的确定性脚本，不安装或调用 AI。
- AI 只参与非生产首次部署：把成功步骤固化为脚本，连续两次幂等加一次故意失败回滚，真实结果
  写入该 Issue 映射的 `verification`。平台的参考实现、本地 fake PASS 或 PR CI 不能写成项目已部署。

## 4. 项目必须自己声明的扩展点

以下内容写在项目 `AGENTS.md` 的「项目事实」与项目自己的文档、脚本里，平台不提供默认值：

| 扩展点 | 项目侧落点 |
|---|---|
| 技术栈与安装、测试、构建、迁移命令 | `AGENTS.md` 项目事实 |
| 健康端点 | `AGENTS.md` 项目事实 |
| 交付形态（Linux 容器化 / Linux 原生 / Windows / 其它） | `AGENTS.md` 项目事实；`.aisoft/architecture.json` 的 `delivery_contract` |
| 技术栈 profile（平台示例不合用时） | `.aisoft/profiles/<profile_id>.json`，平台只校验 `profile-v1` schema 与 catalog 语义 |
| 部署方案、脚本、参数与环境差异 | 项目自己的 `docs/` 或脚本目录 |
| 发布 producer（`local` 或 `github`，只能一种）与 transport | `AGENTS.md` 项目事实 |
| 禁改边界（受保护路径、数据、配置） | `AGENTS.md` 项目事实 |
| 选用的工具与 required CI contexts | `AGENTS.md` 项目事实与平台 governance manifest 中本项目的注册条目 |

平台仓里的交付参考实现与各环境分册只是可选参考，不是项目部署步骤的事实源；项目采用与否、
如何裁剪，在项目仓声明与实现，并自带所需副本，不在运行时依赖平台仓的某个提交。

## 5. 会话工具

项目会话只用本仓的 `.aisoft/bin/aisoft`，不需要平台检出。它随发布包进仓，字节由 `tool-provenance` 锁定在
pin 的版本，项目不得手改；Gitea 与 Git 访问仍经本机安装的 host-access broker，治理与标签 manifest 读 broker
安装副本。

| 子命令 | 用途 |
|---|---|
| `change-name N slug` | 校验并打印新 change 分支名 |
| `resolve-documents N` | 解析映射的 change 文档名 |
| `check-change-documents` | 核对全部 change 文档的 front matter 合同 |
| `open-pr N --title T --body-file F` | 确认点 2 之后一步完成首推、建 PR、回填 summary 与再推 |
| `backfill-pr-url N --pr-url U` | 手工修复：建 PR 后回填 summary 的 `pr_url` 与 `status` |
| `claim-worktree --branch B` | 把 change worktree 绑定到本会话（`AISOFT_SESSION_ID`） |
| `scan-worktrees` | 只读扫描 change worktree 是否被改写 |
| `classify N`、`classify --apply N`、`classify --verify N` | 判级投影：计划（含路由行）、写入、读回 |
| `complete --project ID --range R` / `--apply N…` | 合并后终态：先 dry-run，再按 pinned 编号写入 |
| `project-check` | 对齐检查（见 §6） |
| `bundle status` | 本仓与 pin 版本的核对结果 |
| `version` | 自报 `bundle_version`、`bundle_digest` 与源 SHA |

缺省仓库是当前 git 顶层；其余参数与平台同名工具一致。

## 6. 对齐检查

`aisoft project-check` 只读核对本仓与 pin 版本的一致性
（`platform-pin`、`tool-provenance`、`pointer-sections`、`change-templates` 等）以及项目声明是否齐全；
`AGENTS.md`「项目事实」超过 2 KB 时 `agents-budget` 提示。缺口在项目仓
逐条建 Issue 修复；检查器不改任何状态，也不授权合并或部署。

- **存量 change 目录**：有历史的项目在 `.aisoft/platform-usage.lock.json` 加一个整数键
  `legacy_changes_before`（例如 `"legacy_changes_before": 120`）。编号小于它的 change 目录（含零填充、
  纯数字等非可读元组的历史名）的文档问题记为 `LEGACY` 登记，不计 GAP；编号不小于它的目录照旧要求现行
  合同。这个键只在采用支持它的版本之后写，旧版本工具会把带它的 lock 判为格式不受支持；`--adopt` 升级时保留它。
- **architecture catalog 的 pin**：`.aisoft/architecture.json` 的 `catalog_revision` 可以停在一个已发布的历史
  revision，检查器按随发布包分发的该 revision 快照校验并出 `NOTE`；升级到新 revision 是项目自己的 Issue。
  快照的 `review_by` 过期只在 NOTE 里提示，组件 EOL、prohibited、例外到期仍是 GAP。
- `architecture-lock` 失败时 GAP 写出诊断码，按诊断码修复后重新生成 lock。

## 7. 编程思想指导

`aisoft-platform` 技能的 `references/engineering-principles.md` 提供纲领性指导：理解问题、简单设计、
聚焦改动和真实验证。它辅助方案、实现与审查中的工程判断，内容随本项目 pin 的发布包版本交付。
