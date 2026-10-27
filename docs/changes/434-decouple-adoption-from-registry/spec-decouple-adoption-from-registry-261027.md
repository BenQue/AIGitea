---
issue: 434
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/434
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authorization
  - authentication
  - shared-core
  - agent-governance
  - platform-governance
  - external-contract
  - artifact
depends_on: []
branch: change/434-decouple-adoption-from-registry
created: 2026-10-27
updated: 2026-10-27
---

# Spec：通用流程采用与中央项目登记解耦

## 目标与原因

平台交付的是方法、流程、模板与通用工具，由项目自主导入，项目参数与采用记录留在项目自身。

一个项目要采用通用流程，只需要三样东西：使用发布包、技能，以及项目检出里的 `aisoft` 工具。它不需要往平台仓新增任何记录。

平台两份 manifest 里的项目登记保留下来，但含义改为可选的**站点加固访问**：凭据放在受保护文件里，会话拿不到；由 manager 校准权限与保护规则。

这样做直接消除接入既有项目时出现的三类问题：

- 项目内容误立到平台仓。
- 登记前没有路由，只能走 admin 例外。
- 导入步骤临场发挥。

### 三层职责（AC-1）

| 层 | 内容 | 归属 | 是否需要平台登记 |
|---|---|---|---|
| 通用流程采用 | 使用发布包、技能、`aisoft` 工具、typed 操作引擎、change 命名与文档、判级、两个确认点、人工合并 | 平台提供，项目采用 | 否 |
| 项目自身配置 | 仓库与默认分支、受保护 `main`、required CI、标签集合、项目身份与凭据、runner 依赖、`AGENTS.md` 项目事实、`.aisoft/project.json` | 项目 | 否 |
| 可选站点加固访问 | 已安装 broker、两份平台 manifest、受保护凭据文件、manager 校准、host-role 闸门 | 平台站点 | 是，仅限选用者 |

## 决定

### 已由负责人裁决

- **D1 注册表位置**：留在平台仓 `codex/config/` 的两份 manifest。不迁到站点本地，也不做项目自注册（方案 A）。
- **D2 解耦方向**：登记不再是采用前置，项目可以用自己的 Git 凭据跑完整流程（A+，2026-10-27）。

### 待确认点 1 一并确认

- **D3 同一个引擎，两种来源**：不另写一套 direct 传输，而是给现有 broker 引擎 `codex/runtime/aisoft_host_access` 增加「项目自声明」来源，现有的「站点登记」来源保持不变。
  - 两种来源跑同一份校验代码：worktree 归属与会话、fresh main、fetch/push URL 核对、完整历史与 `git_scope`、写后读回、身份读回、PR 正文合同、标签集合。
  - 项目自声明来源下，引擎随使用发布包装进 `.aisoft/lib`，以当前用户身份非特权运行。
  - 站点登记来源仍是 root 安装的 `/usr/local/libexec/aisoft/host-access-broker`。
- **D4 项目自声明文件 `.aisoft/project.json`**：这个文件归项目所有，不是发布包成员；发布包只提供模板与 schema。
  - 内容是一个项目条目。字段、派生值与消费者见下文「项目上下文映射」。
  - schema 是精确键集合。未知键、缺键或取值越界一律拒绝。
  - 站点级值（manager、site admin、human merge identity、visibility）不进这个文件，项目来源也不使用依赖它们的模型。
- **D5 两个入口，来源固定**：
  - 已安装的站点 wrapper `/usr/local/libexec/aisoft/host-access-broker` 永远只用站点登记来源；cwd 里有没有 `project.json` 都不切换。
  - 项目工具入口新增 `.aisoft/bin/aisoft-access`，随发布包分发，只用项目自声明来源，并要求检出里有 `project.json`。
  - `aisoft` 会话工具选择入口的规则：
    - 检出有 `project.json`，调项目入口；
    - 没有时，按现有 `aisoft-project-target.sh` 解析，调站点 wrapper；
    - 两者都不成立，报错并提示两种写法，不降级，不猜；
    - 两种来源都命中但仓库不同，停止。
  - 引擎为项目来源新增一个单项目加载函数，按映射表构造项目上下文。站点来源的 `load_access_contract` 与 manifest 交叉校验不改。不做通用来源插件框架。
### 项目上下文映射

项目来源下，引擎需要的每个值都按下表取得。表外的站点值，项目来源一律不读。

| 值 | 输入或派生 | 消费者 | 拒绝条件 |
|---|---|---|---|
| `repository` | `project.json` 输入，形如 `owner/name` | Gitea API 路径、remote 核对 | 不是恰好两段，或任一段不合 Gitea 名称规则 |
| owner、仓库名 | 由 `repository` 拆出。引擎的仓库字段沿用「只放仓库名」的现有形状 | `ProjectContract.repository`、API 路径 | 同上 |
| `project_id` | 等于仓库名。只用于回执与日志，不参与授权 | 回执 | 无 |
| base URL | 由 remote URL 推出 `scheme://host[:port]`。路径必须恰好是 `/owner/name` 或 `/owner/name.git`，不支持子路径部署 | API 请求、凭据请求 | 非 `http(s)`；路径不符；与 `repository` 不一致 |
| canonical checkout | 调用时 `git rev-parse --git-common-dir` 所在仓库的主工作树，每次调用现取 | worktree 归属、cwd 核对 | cwd 不在该仓库或其已登记 worktree 内 |
| `git_remote_name` | `project.json` 输入，缺省 `origin` | Git 远端操作 | remote 不存在，或不满足 D6 |
| 默认分支 | 固定 `main`，与引擎现状一致。本票不支持其它默认分支，`project.json` 不设此键 | fetch main、推送基线 | 远端没有 `main` |
| `project_agent` | `project.json` 输入，项目身份的登录名 | 身份读回 | 与读回登录名不一致 |
| `deployment_lifecycle` | `project.json` 输入，取值闭集同 governance manifest | `aisoft complete` 判终态 | 越界 |
| `change_control` | `project.json` 输入，缺省 `production`，取值闭集同 governance manifest | 路由（`route_policy`、`change_control`） | 越界 |
| `classification` | `project.json` 输入，取值闭集同 governance manifest | `project-check` | 越界 |
| `status_check_contexts` | `project.json` 输入，非空字符串列表 | `project-check` 的 CI 检查、人工保护证据比对 | 空列表或重复 |
| `protection_evidence` | `project.json` 输入，项目仓 Issue 编号，记录人工保护读回（D7） | `project-check` | 不是正整数 |
| 标签集合 | 发布包内的 canonical `gitea-labels.json` | 标签对齐、判级投影、终态 | 文件缺失或校验失败 |
| `git_scope` | 不进 `project.json`。沿用现有来源，即候选 HEAD 中映射 spec 的 `git_scope` | 推送闸门 | 沿用现有规则 |

`git_scope` 里有一个模板持有特例：推送 canonical 模板路径时，需要核对安装面与两份 manifest。项目来源不支持这个特例，遇到时报错并说明「模板持有变更只能走站点来源」，不静默放行。

- **D6 项目自声明来源的凭据边界**：
  - **remote**：只接受 `http(s)` URL，并且同时满足：
    - fetch 与 push URL 相同，且只有一个；
    - 不含 userinfo；
    - 不受 `insteadOf` / `pushInsteadOf` 改写；
    - 推出的 `owner/name` 等于 `repository`。
    
    SSH remote 不支持，因为 API 凭据要按 exact URL 取得。每次写操作前重新核对，操作期间配置漂移即停止。
  - **token**：每次调用只取一次，经本机 `git credential fill` 针对 exact remote URL 取得，只放在内存里。
    - **同一份凭据**：身份读回、API 写入和 Git 写入用的是同一份内存凭据。
    - **Git 子进程**：仍按现有隔离环境运行，禁用全局 Git 配置。引擎只给它注入一个自带的凭据助手，助手从继承的管道读出同一份凭据，因此 Git 写入不会另行询问本机助手。
    - **不外泄**：token 不进 argv、环境变量、日志与输出；子进程禁用 `GIT_TRACE*` 与 curl verbose；错误回显先脱敏。
    - **不落盘**：不落临时文件。必须落盘时用 mode 600，并在 finally 中删除。
    - **重定向**：完整 origin（scheme、host、port）一变就拒绝，降级到 http 也拒绝。
  - **PAT scope**：项目凭据至少需要 `read:user`、`write:issue`、`write:repository`。scope 不足时，Gitea 返回的错误照原文报告。`usage/USER-GUIDE.md` 写明这一要求。
  - **身份读回**：只在项目来源下执行，每次写操作前经 `/user` 与 `GET /repos/{owner}/{name}` 读回。以下任一情况都拒绝写入：
    - 登录名与 `project_agent` 不一致；
    - `is_admin` 不是 `False`；
    - `permissions.admin` 不是 `False`；
    - `permissions.push` 不是 `True`；
    - 字段缺失、类型不符或读取失败。
    
    站点来源的现有身份校验保持原样，不叠加这组检查。依据是 Gitea 1.26.4 源码：Write 级身份可以读 `/user` 与仓库 permissions，这一点 live 尚未验收，见 AC-8。
  - **操作闭集**：项目来源只开放下表中的操作，其余操作一律拒绝，包括 `host.*`、`orbstack.*`、`mac.git.bind`、`gitea.credential.rotate`、`gitea.labels.extension.define`、`gitea.issue.labels.extension.set`、`gitea.protection.read`。

| 调用入口 | 操作 |
|---|---|
| `aisoft open-pr` | `git.push.change`、`gitea.pull.create`（同 change 已有开放 PR 时返回原 PR）；建完用 `gitea.pulls.read` 读回编号 |
| `aisoft classify`（`apply-classification-labels.sh`） | `gitea.issue.read`、`gitea.issue.labels.read`、`gitea.issue.labels.classify` |
| `aisoft complete`（`mark-completed-issues.sh`） | `gitea.issue.labels.set` |
| `prepare-ticket` / `review-candidate` | `gitea.issue.read` |
| `aisoft project-check --remote`（项目来源；站点来源保持现有 `.agent.env` 直读） | `gitea.repo.read`、`gitea.labels.read` |
| 新增 `aisoft labels-provision` | `gitea.labels.read`、`gitea.labels.provision` |
| 技能直接调用：`aisoft-access` | `gitea.issue.create`、`gitea.issue.read`、`gitea.issue.list`、`gitea.issue.comment`、`gitea.issue.comments.read`、`gitea.issue.update`、`git.fetch.main`、`git.fetch.change`、`git.push.change`、`gitea.pull.read`、`gitea.commit.status.read`、`gitea.actions.run.read`、`gitea.actions.job.logs.read` |

  `aisoft-access` 的参数与站点 wrapper 的 `--operation` 形式一致，但不接受 `--project`，项目由 `project.json` 决定。闭集以本表为准，T02 的成功路径测试逐行覆盖。表里各入口的实际调用如果与源码核对不一致，以源码为准修订本表，并在 verification 记录差异。
- **D7 保护规则证据**：
  - Write 级的项目身份读不到 Gitea 分支保护，引擎也不为此提升权限。
  - 保护规则包括：受保护 `main`、禁止直推与强推、合并只许人、required CI 启用。采用时由人用自己的管理员会话读回一次，证据写成项目仓采用 Issue 中的一条评论，`project.json` 的 `protection_evidence` 指向这个 Issue。
  - 证据至少记录：仓库完整地址、分支、项目身份、观测时间、required contexts、合并 allowlist 是否启用及其用户与团队授权、是否禁止直推与强推。项目身份或保护规则变化后要重新读回。
  - `aisoft project-check` 两种来源分开处理：
    - **站点来源**：行为与本批前完全一致，包括继续读取 `.agent.env` 和现有保护检查。
    - **项目来源**：
      - 身份非管理员这一项可以机读，按 D6 判 PASS 或 GAP。
      - 依赖保护 API 的检查（`main-protection`、`ci-context`、`ci-outdated-branch` 等）一律输出新结果值 `MANUAL`，附 `protection_evidence` 引用；没有引用时报 GAP。
      - `MANUAL` 不计入 PASS，汇总行单独计数。
      - 工具只报告「人工证据已登记」或「缺失」，不声称实时有效。
  - 这是 A+ 的固有取舍：
    - 站点加固访问下，会话拿不到凭据，裸 `git push` 也会失败；
    - 项目自声明来源下，本机凭据助手对任何 git 命令都可用，最后一道防线是服务端保护。
    
    确认点 1 需要确认这一取舍。
- **D8 已登记项目不动**：现有 manifest 条目、凭据与保护规则不改、不删。没有 `project.json` 的已登记项目继续走站点登记来源；要不要迁移，由各项目自愿决定。
- **D9 接入既有项目**：onboarding 参考拆成两部分。
  - 「采用（项目自主）」：由项目仓自己的 Issue 承载，包括私有仓迁移或历史导入核对、首个 CI 与 runner 依赖、标签对齐、保护证据、首个 canary。
  - 「可选站点加固访问（维护层）」：保留现有 §1.1。
  - 平台仓 Issue 只在两种情形下使用：登记站点加固访问；在采用中发现通用能力缺陷。
- **D10 范围承接**：Issue #434 正文把本票限定为调查与方案讨论。确认点 1 的「确认」把本票扩展为按本 spec 实施，扩展记录写在 summary。确认之前不实施。

## Acceptance criteria

- [ ] **AC-1 职责界定**：
  - 新 ADR 0003 写明三层职责与 D3–D9，并列出它取代的旧条款。
  - 下列活文档与 ADR 一致：技能 `aisoft-platform`、`execution-adapter`、getting-started、onboarding-runbook、project-align，以及 `issue-session-flow`、`usage/CONTRACT.md`、`usage/USER-GUIDE.md`、`templates/project/AGENTS.md`。
  - 没有任何活文档再把平台登记写成采用前置。
- [ ] **AC-2 入口清单**：verification 列出「调用入口 → 操作 → 来源」表，每一行都写明处置：两种来源通用，或者仅站点。至少覆盖：
  - `aisoft open-pr`、`aisoft classify`、`aisoft complete`、`aisoft project-check --remote`
  - `prepare-ticket` / `review-candidate`（经 `ticket_execution.read_issue`）
  - `aisoft-project-target.sh`
  - 技能与 `issue-session-flow` 里调用的 `gitea.issue.list`、`git.fetch.change`、`gitea.pull.read`、`gitea.commit.status.read`、`gitea.actions.run.read`、`gitea.actions.job.logs.read`
- [ ] **AC-3 无平台记录即可走完流程**：
  - 前提：合成样例项目只在项目侧有 `.aisoft/project.json`，合成夹具 manifest 里没有它；运行环境没有平台检出、没有已安装 broker、没有 `.agent.env`。
  - 用导出的项目工具包，在合成 Gitea 上依次走通：
    1. 标签对齐；
    2. 建 Issue 并读回；
    3. `prepare-ticket`；
    4. 判级投影的 apply 与 verify；
    5. `review-candidate`；
    6. `aisoft open-pr`（首推、建 PR、回填、再推）；
    7. 读 PR head 与 commit status；
    8. 在 API 桩中把 PR 置为已合并的夹具状态，然后执行 `aisoft complete --apply`，读回标签，并重复执行一次，验证幂等；`deployment_lifecycle` 取 `none` 与需部署两个分支各跑一遍；
    9. 声明 `change_control: development` 的样例，`prepare-ticket` 的路由读回为 `complex-development`。
  - 测试断言全程没有访问平台安装面。
- [ ] **AC-4 安全验证保留**：
  - 站点登记来源的现有回归全部通过。
  - 项目自声明来源下，下列每种情形各有一个反例，并且都被拒绝：
    - 身份问题：管理员身份、仓库 admin 权限、无 push 权限、登录名不符、身份字段缺失或读取失败；
    - 入口问题：站点 wrapper 在含 `project.json` 的 cwd 下仍走站点来源；项目入口在没有 `project.json` 时拒绝；
    - 模板持有路径推送在项目来源下被拒绝；
    - 跨 origin 或降级重定向；
    - remote 问题：fetch/push URL 分离、多个 pushurl、`insteadOf` 改写、userinfo、SSH remote；
    - 推送问题：推 `main`、推非当前分支、越界历史、归属错误；
    - 其他：闭集外操作、正文不合合同、跨主机重定向。
  - 哨兵 token 在 stdout、stderr、argv、环境变量、git trace 和残留临时文件里都零命中。
- [ ] **AC-5 兼容与回滚**：
  - 没有 `project.json` 的已登记夹具项目，行为与本批之前一致。
  - verification 写出迁移与回滚说明：
    - 已登记项目：删除 `project.json` 即回到站点来源；
    - 未登记项目：恢复上一版兼容工具包，无法恢复时停止远端写入；
    - 已创建的正常 Issue/PR 不撤销。
- [ ] **AC-6 接入既有项目一节**：
  - onboarding 参考新增「接入既有项目」，按顺序列出由项目仓 Issue 承载的步骤，并写明平台仓 Issue 的两种适用情形（D9）。
  - getting-started 的新项目路径不再要求先改平台 manifest。
- [ ] **AC-7 发布**：
  - 运行依赖闭包全部进入 `usage/bundle.json` 的成员清单，包括：
    - `aisoft_host_access` 的 `broker.py`、`cli.py`，以及已在包内的 `contract.py`、`dependencies.py`；
    - `aisoft_main_integration.py`、`aisoft_worktree_owner.py`，以及已在包内的 `aisoft_change_name.py`；
    - canonical `gitea-labels.json`；
    - `.aisoft/bin/aisoft-access` 入口；
    - `project.json` 模板与 schema。
  - 每张改动成员的票，都在同票内按现有工具发一个递增版本，不重发同号。
  - `aisoft version` 与 `project-check` 的 `tool-provenance` 都读回新版本。
- [ ] **AC-8 未验证边界如实记录**：
  - 合成 Gitea 桩通过，不能表述为真实 Gitea 上可用。
  - verification 单独列出以下各项，写明证据或 NOT RUN：
    - 真实 Gitea 版本下 `/user` 与 permissions 响应形状的兼容证据；
    - 已安装 broker 的重装；
    - live 读回。

## 接口、数据与兼容性影响

- 引擎增加来源选择与项目条目加载。站点登记来源的 manifest schema、操作表与校验都不变。
- 引擎代码字节变化后，已安装 broker 与源码会不一致，所以合并后需要两台重装 broker；重装之前，漂移检查会报差异。重装由维护者执行，本批记为 NOT RUN。
- 使用发布包新增成员，按发布规则升版本。已 pin 旧版本的项目在主动升级之前不受影响。
- `aisoft` 子命令的参数不变。如果需要新增公开子命令（例如标签对齐、建 Issue），只做薄包装，参数与 broker 同名操作保持一致。

## 风险与回滚约束

- 安全取舍见 D7。站点加固访问的隔离保持不变，供需要的项目选用。
- 共享核心改动：来源选择有缺陷时，可能波及站点登记来源。缓解办法是站点来源的现有回归全量必跑，并对来源选择单独做反向证明。
- 回滚：revert 本批 PR，由维护者把 broker 重装回 revert 后的字节；项目侧按 AC-5 处理。

## 非目标

- 不把注册表移出平台仓，不实现项目自注册，不改已登记项目的 manifest 条目。
- 不新建或轮换凭据，不改 live 标签或保护规则。安装与重装由维护者执行。
- 不清理 #433 的遗留分支与 worktree，也不处理已移交项目仓的那张 Issue。
- 不改 governance 工具与 manager 校准流程，不改部署合同，不改 readiness 的维护层检查。

## 未决问题

- 无。D3–D9 待确认点 1 确认。
