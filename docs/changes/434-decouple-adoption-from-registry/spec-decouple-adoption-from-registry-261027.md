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
  - 内容是一个项目条目，字段取引擎今天从两份 manifest 读取的项目级值：
    - `repository`（`owner/name`）
    - `git_remote_name`（缺省 `origin`）
    - `default_branch`
    - `project_agent`（项目身份的登录名）
    - `deployment_lifecycle`
    - `change_control`（缺省 `production`）
    - `status_check_contexts`
  - Gitea base URL 从 remote URL 推出，调用方不能传。
  - schema 是精确键集合。未知键、缺键或取值越界一律拒绝。
  - 站点级值（manager、site admin、human merge identity）不进这个文件。
- **D5 来源选择**：
  - 检出里有 `.aisoft/project.json` 时，用项目自声明来源。
  - 没有这个文件时，按现有 `aisoft-project-target.sh` 从已安装 manifest 解析，即站点登记来源。
  - 两者都没有时报错，并提示两种写法；不降级，也不猜。
  - 同一检出两种来源都命中、但仓库不同时，停止。
- **D6 项目自声明来源的凭据边界**：
  - **remote**：只接受 `http(s)` URL，并且同时满足：
    - fetch 与 push URL 相同，且只有一个；
    - 不含 userinfo；
    - 不受 `insteadOf` / `pushInsteadOf` 改写；
    - 推出的 `owner/name` 等于 `repository`。
    
    SSH remote 不支持，因为 API 凭据要按 exact URL 取得。每次写操作前重新核对，操作期间配置漂移即停止。
  - **token**：经 `git credential fill` 针对 exact remote URL 取得，只在进程内使用：
    - 不进 argv、环境变量、日志和输出；
    - 子进程禁用 `GIT_TRACE*` 与 curl verbose；
    - 错误回显脱敏；
    - 不跟随跨主机重定向；
    - 不落临时文件；必须落盘时用 mode 600，并在 finally 中删除。
  - **身份读回**：每次写操作前，经 `/user` 和仓库 permissions 读回身份。下列任一情况都拒绝写入，规则与站点登记来源一致，取现有 `require_non_admin_exact` 语义：
    - 登录名与 `project_agent` 不一致；
    - `is_admin` 为真；
    - 仓库 permissions 的 `admin` 为真。
  - **操作闭集**：项目自声明来源只开放现有 project-agent 身份的项目级操作。闭集按「调用入口 → 操作」表确定，由 verification 列出。以下维护层操作一律拒绝：
    - `host.*`、`orbstack.*`
    - `mac.git.bind`
    - `gitea.credential.rotate`
    - `gitea.labels.extension.define`
    - `gitea.protection.read`（属于 manager-audit 身份）
- **D7 保护规则证据**：
  - Write 级的项目身份读不到 Gitea 分支保护，引擎也不为此提升权限。
  - 保护规则包括：受保护 `main`、禁止直推与强推、合并只许人、required CI 启用。采用时由人用自己的管理员会话读回一次，证据留在项目仓的采用 Issue。
  - 项目自声明来源下，`aisoft project-check` 报告两项：
    - 身份是否非管理员：可以机读，不满足就报 GAP；
    - 保护证据的位置：没有登记证据位置就报 GAP。
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
    5. `aisoft open-pr`（首推、建 PR、回填、再推）；
    6. 读 PR head 与 commit status；
    7. `aisoft complete` 的 dry-run，用 `deployment_lifecycle` 判定终态。
  - 测试断言全程没有访问平台安装面。
- [ ] **AC-4 安全验证保留**：
  - 站点登记来源的现有回归全部通过。
  - 项目自声明来源下，下列每种情形各有一个反例，并且都被拒绝：
    - 身份问题：管理员身份、仓库 admin 权限、登录名不符；
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
  - 引擎、schema 与 `project.json` 模板进入 `usage/bundle.json` 的成员清单；成员变更与发布记录放在同一切片里完成。
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
