# AISoft 平台使用合同

> 这是平台交付给**项目使用层**的唯一合同入口（ADR 0001 D6）。它随版本化使用发布包下发，
> 项目把本文件复制为 `.aisoft/platform-usage.md`，并在 `.aisoft/platform-usage.lock.json` 记下
> 所用的发布包版本。本文件只写流程与项目必须自己声明的扩展点；任何项目的构建、发布、部署
> 步骤都不在这里。平台自身的维护规则在平台仓 `AGENTS.md`，不属于本合同。

## 1. 版本与跟进

- 项目使用哪一版平台合同，以本仓 `.aisoft/platform-usage.lock.json` 的 `bundle_version` 为准。
  平台仓前进不改变已 pin 版本的含义，也不让项目的对齐检查自发变红。
- 升级到新版本是项目自己的 Issue：用平台 `codex/tools/usage-bundle.sh --build <目录>` 导出最新版本，
  按 project-align 复制到本仓，经项目自己的判级与唯一 PR 合入。
- 发布包里的文件分四类：逐字节副本（本文件、`CLAUDE.md`、change 模板四件套）、`AGENTS.md` 的
  常驻指针两节、初始化种子（`docs/agents/` 三件套、CI 示例，项目可改）、技能（装到各工具的
  技能目录）。前两类由平台的对齐检查按 pin 的版本核对。
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
  `production`（未声明时的默认）先 `$to-spec #N` → `$to-tickets #N` → `$implement #N Txx`；
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
| 部署方案、脚本、参数与环境差异 | 项目自己的 `docs/` 或脚本目录 |
| 发布 producer（`local` 或 `github`，只能一种）与 transport | `AGENTS.md` 项目事实 |
| 禁改边界（受保护路径、数据、配置） | `AGENTS.md` 项目事实 |
| 选用的工具与 required CI contexts | `AGENTS.md` 项目事实与平台 governance manifest 中本项目的注册条目 |

平台仓里的交付参考实现与各环境分册只是可选参考，不是项目部署步骤的事实源；项目采用与否、
如何裁剪，在项目仓声明与实现，并自带所需副本，不在运行时依赖平台仓的某个提交。

## 5. 对齐检查

平台 `codex/tools/aisoft-project-check.sh --repo <checkout>` 只读核对本仓与 pin 版本的一致性
（`platform-pin`、`pointer-sections`、`change-templates` 等）以及项目声明是否齐全。缺口在项目仓
逐条建 Issue 修复；检查器不改任何状态，也不授权合并或部署。
