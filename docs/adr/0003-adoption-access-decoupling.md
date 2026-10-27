# ADR 0003 · 通用流程采用与站点访问控制解耦

## 状态

已采纳（Issue #434，负责人 2026-10-27 确认）。补充 [ADR 0001](0001-platform-boundary.md) 与 [ADR 0002](0002-deterministic-development-flow.md)，两者的决定都不撤销。本 ADR 只改一件事：平台登记从「采用通用流程的前置」降为「可选的站点加固访问」。

## 日期

2026-10-27

## 依据

**要回答的问题**：采用平台的通用方法和流程，是否必须先在平台仓登记具体项目？如果是，平台的职责就从提供方法扩大到了管理具体项目。

**事实**（Issue #434 映射 spec 的入口清单）：

| 事实 | 证据 |
|---|---|
| 会话工具的远端步骤只有 broker 一条路径，broker 只服务两份平台 manifest 里登记的项目 | `aisoft open-pr`、`apply-classification-labels.sh`、`mark-completed-issues.sh`、`aisoft-project-target.sh` |
| 技能、上手指南第 3 步、onboarding runbook §1.1 都把「先在平台仓走 Issue/PR 登记」写成采用前置 | 本 ADR 之前的 `aisoft-platform` 技能与 references |
| 一次既有项目接入中，项目内容被立成平台仓 Issue；登记前没有路由，约 16 次 admin 例外；私有仓迁移、首个 CI、runner 依赖都靠临场处理 | 平台线程取证报告（项目库） |

## 决定

### D1 三层职责

| 层 | 内容 | 归属 | 是否需要平台登记 |
|---|---|---|---|
| 通用流程采用 | 使用发布包、技能、`aisoft` 工具、typed 操作引擎、change 命名与文档、判级、两个确认点、人工合并 | 平台提供，项目采用 | 否 |
| 项目自身配置 | 仓库与默认分支、受保护 `main`、required CI、标签集合、项目身份与凭据、runner 依赖、`AGENTS.md` 项目事实、`.aisoft/project.json` | 项目 | 否 |
| 可选站点加固访问 | 已安装 broker、两份平台 manifest、受保护凭据文件、manager 校准、host-role 闸门 | 平台站点 | 是，仅限选用者 |

### D2 注册表留在平台仓

站点加固访问的登记仍是 `codex/config/` 下的两份 manifest，经平台 Issue/PR 由人合并，然后重装 broker。不迁到站点本地，也不做项目自注册。原因是这几行条目就是 broker 的授权边界，让项目自己写，等于项目给自己授权。

### D3 同一个引擎，两种来源

broker 引擎 `aisoft_host_access` 接受两种项目来源，两者跑同一份校验：

- **站点登记来源**：入口是已安装的 `/usr/local/libexec/aisoft/host-access-broker`，读平台 manifest。行为与本 ADR 之前一致，cwd 里有没有 `project.json` 都不改变它。
- **项目自声明来源**：入口是随使用发布包分发的 `.aisoft/bin/aisoft-access`，读项目仓的 `.aisoft/project.json`，以当前用户身份非特权运行，凭据来自本机 Git 凭据助手。

会话工具 `aisoft` 的选择规则：检出里有 `project.json` 就用项目入口；没有就按原规则解析已安装 manifest；两者都没有就报错，不降级；两者都命中但仓库不同就停止。

### D4 项目来源的边界

- 字段是精确键集合，见 #434 spec「项目上下文映射」。站点级值不进 `project.json`；默认分支固定为 `main`。
- remote 只接受 `http(s)`：fetch 与 push URL 相同，不含 userinfo，不受 URL 改写，推出的仓库必须等于声明。
- token 每次调用只取一次，只放在内存里；身份读回、API 写入与 Git 写入都用这同一份。token 不进 argv、环境变量、日志与输出。
- 每次写操作之前读回身份。登录名不符、管理员身份、仓库 admin 权限、没有 push 权限，或者读取失败，一律拒绝写入。
- 操作只开放 #434 spec 的闭集表，维护层操作一律拒绝。模板持有路径的推送只能走站点来源。

### D5 保护规则由服务端承担，证据由人读回

项目来源下，本机凭据对任何 git 命令都可用，所以直推 `main`、强推与合并的最后一道防线是仓库自己的保护规则。

Write 级项目身份读不到分支保护，也不为此提升权限。采用时由人用自己的管理员会话读回一次，证据写在项目仓的采用 Issue 里，`project.json` 的 `protection_evidence` 指向它。

`aisoft project-check` 对依赖保护 API 的检查输出 `MANUAL`，不计入 PASS；缺证据时报 GAP。

### D6 平台仓 Issue 的适用范围

接入既有项目时，私有仓迁移、历史导入核对、首个 CI 与 runner 依赖、标签对齐、保护证据与首个 canary，都由项目仓自己的 Issue 承载。

平台仓 Issue 只用于两种情形：登记站点加固访问；在采用中发现通用能力缺陷。

## 取代的旧条款

| 旧条款 | 现在 |
|---|---|
| `aisoft-platform` 技能「一切 Gitea/Git/OrbStack 访问走 broker」 | 远端访问一律经 typed 操作引擎，从站点或项目两种来源中选一个 |
| 技能「每个本地 Gitea 软件仓库必须先登记在 governance manifest」 | 只有选用站点加固访问的仓库才登记 |
| getting-started 第 3 步「新项目登记（维护者）」 | 改为可选步骤；新项目的默认路径是项目自声明 |
| onboarding runbook §1「新项目仍必须先通过独立 AISoftPlatform Issue/PR 更新两份 manifest」 | 只适用于站点加固访问 |
| 使用合同「选用的工具与 required CI contexts」取自平台注册条目 | 来自项目 `AGENTS.md` 项目事实与 `project.json`，已登记项目继续兼容读取 manifest |

历史 change 证据与 `archive/` 保持原文。

## 后果

- 新项目不改平台仓也能完整采用流程，平台仓不再出现新的项目名，符合 ADR 0001 D3。
- 已登记项目不需要任何动作，要不要迁到项目来源由各项目自定。
- 引擎代码变化后，需要在 Mac 与 gitea-ci VM 两台重装 broker，已登记项目才会用上同一份新引擎。重装由维护者执行。
- 项目来源下，凭据隔离弱于站点来源。需要隔离的项目继续选用站点加固访问。
