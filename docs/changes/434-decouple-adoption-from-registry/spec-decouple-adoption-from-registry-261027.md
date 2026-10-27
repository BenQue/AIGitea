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
  - agent-governance
  - platform-governance
  - external-contract
depends_on: []
branch: change/434-decouple-adoption-from-registry
created: 2026-10-27
updated: 2026-10-27
---

# Spec：通用流程采用与中央项目登记解耦

## 目标与原因

平台交付的是方法、流程、模板与通用工具。项目自主导入这些东西，项目参数与采用记录留在项目自身。

一个项目要采用通用流程，所需的只有三样：使用发布包、技能，以及项目检出里的 `aisoft` 工具。它不需要在平台仓新增任何记录。

平台两份 manifest 里的项目登记保留，但含义改为可选的 **broker 加固访问**：

- 想把 Git/Gitea 凭据与会话隔离开的项目，才去登记。
- 登记后，远端操作经 broker 进行。

这样做直接消除接入既有项目时的三类问题：

- 项目内容误立到平台仓。
- 登记前没有路由，只能走 admin 例外。
- 导入步骤临场发挥。

### 三层职责（AC-1）

| 层 | 内容 | 归属 | 是否需要平台登记 |
|---|---|---|---|
| 通用流程采用 | 使用发布包、技能、`aisoft` 工具、change 命名与文档、判级、两个确认点、人工合并 | 平台提供，项目采用 | 否 |
| 项目自身配置 | 仓库与默认分支、受保护 `main`、required CI、标签集合、项目身份与凭据、runner 依赖、`AGENTS.md` 项目事实、`.aisoft/access.json` | 项目 | 否 |
| 可选运行环境访问控制 | broker、governance manifest、manager 校准、project-agent 凭据隔离、host-role 闸门 | 平台站点 | 是，仅限选用者 |

## 已批准决定

- **D1 注册表位置**：留在平台仓 `codex/config/` 的两份 manifest，不迁站点本地，不做项目自注册（负责人选方案 A）。
- **D2 解耦**：登记不再是采用前置。会话工具支持两种传输，broker 与 direct（负责人选 A+，2026-10-27）。
- **D3 传输选择**：由项目侧文件 `.aisoft/access.json` 声明。
  - 合法形状只有两种：`{"transport": "direct"}`，以及 `{"transport": "broker", "project_id": "<id>"}`。
  - 未知键或未知取值一律拒绝。
  - 文件缺失时走兼容路径：按现有 `aisoft-project-target.sh` 从 manifest 解析。解析成功即用 broker；解析失败时报错，并提示两种声明写法，不自动降级成 direct。
- **D4 同一组 typed 操作**：两种传输实现同一个闭集，取会话工具今天实际调用的 broker 操作，名称与参数照搬 broker：
  - Git：`git.fetch.main`、`git.push.change`。
  - Issue：`gitea.issue.read`、`gitea.issue.create`、`gitea.issue.comment`。
  - Issue 标签：`gitea.issue.labels.read`、`gitea.issue.labels.classify`、`gitea.issue.labels.set`。
  - 仓库标签：`gitea.labels.read`、`gitea.labels.provision`。
  - PR：`gitea.pulls.read`、`gitea.pull.create`。
  - 保护规则：`gitea.protection.read`。
  
  闭集里没有 merge、没有对 `main` 的 push、没有 force。本地前置校验共用一份实现，两种传输行为一致：
  - exact `change/N-slug` 分支等于当前分支；
  - 工作树干净；
  - PR 正文合同；
  - 标签属于 canonical 集合。
- **D5 direct 传输的凭据边界**：
  - Git 远端用检出里已配置的 remote（缺省 `origin`，可由 `access.json` 的 `git_remote_name` 指定）和本机已配置的 Git 凭据助手。
  - Gitea API 的 token 由 `git credential fill` 针对该 remote 的 exact URL 取得，只在进程内使用。它经 mode 600 临时文件或 stdin 交给 HTTP 客户端，不进命令行、环境变量、日志或输出。
  - 工具不读 `.env`，不接受 token 参数。
  - Gitea base URL 与 owner/repo 只从 remote URL 推出，调用方不能传。
- **D6 保护规则由服务端承担，工具读回**：
  - direct 模式下，直推 `main`、强推与合并的拦截只能靠仓库自己的保护规则。
  - `aisoft project-check` 新增 `access` 检查：
    - 读回 `main` 受保护、禁止直推与强推、合并 allowlist 不含所用项目身份；
    - 读回 required CI context 存在；
    - 读不到或不满足时一律报 GAP。
  - 技能要求 direct 模式使用非管理员的项目身份。
- **D7 已登记项目不动**：现有 manifest 条目、凭据与保护不改不删。没有 `access.json` 的已登记项目继续按兼容路径走 broker。迁移是可选的，由各项目自行决定。
- **D8 接入既有项目**：onboarding 参考拆成两部分。
  - 「采用（项目自主）」：项目仓自己的 Issue 承载私有仓迁移或历史导入核对、首个 CI 与 runner 依赖、标签对齐、首个 canary。
  - 「可选 broker 加固访问（维护层）」：保留现有 §1.1 流程。
  - 平台仓 Issue 只用于两件事：登记 broker，或者在采用中发现通用能力缺陷。

## Acceptance criteria

- [ ] **AC-1 职责界定**：新 ADR 0003 写明上表三层职责与 D1–D8。技能 `aisoft-platform` 的「现行合同」「目标项目与 governance manifest」两节，以及 getting-started 与 onboarding-runbook 的对应段落，与 ADR 一致。任何活文档都不再把平台登记写成采用前置。
- [ ] **AC-2 入口清单与自主采用**：verification 列出本批前所有要求中央登记的入口及其处置，至少包括：`aisoft open-pr`、`aisoft classify`、`aisoft complete`、`aisoft project-check` 远端段、`aisoft-project-target.sh`、getting-started 第 3 步、runbook §1.1、技能里「一切访问走 broker」。每个入口要么改为传输无关，要么明确标为仅 broker 模式。
- [ ] **AC-3 无平台记录即可走完流程**：一个合成样例项目在平台 manifest 里没有任何条目，平台仓也没有任何 diff。它采用使用发布包并声明 `{"transport": "direct"}` 后，在合成 Gitea 上依次走通八步：
  1. 标签对齐；
  2. 建 Issue；
  3. 读 Issue；
  4. 判级投影 apply 与 verify；
  5. 推 change 分支；
  6. `aisoft open-pr`；
  7. summary 回填；
  8. 再推。
  
  同时必须证明三项拒绝：推 `main`、推非当前分支、正文不合合同。token 不出现在任何输出、argv 或环境变量里。
- [ ] **AC-4 安全验证保留**：
  - broker 模式的现有回归全部保持通过。
  - direct 模式下 `project-check` 的 `access` 检查对四种缺失分别报 GAP：无保护、允许直推、允许强推、所用身份在合并 allowlist。
  - 闭集之外的操作在两种传输下都被拒绝。
- [ ] **AC-5 兼容迁移**：
  - 没有 `access.json` 的已登记项目（用合成夹具 manifest 表示）行为与本批前一致，仍走 broker。
  - 非法 `access.json` 被拒绝。
  - verification 给出现有使用者的迁移说明：不需要动作；可选择改为 direct，并给出改法与回退方法。
- [ ] **AC-6 接入既有项目一节**：onboarding 参考新增「接入既有项目」，按序列出项目仓 Issue 应承载的步骤，并写明平台仓 Issue 的两种适用情形（D8）。上手指南的新项目路径不再要求先改平台 manifest。
- [ ] **AC-7 发布**：使用发布包包含 `access.json` 模板与 canonical 标签集合，并按发布规则升版本。`aisoft version` 与 `project-check` 的 `tool-provenance` 读回新版本。

## 接口、数据与兼容性影响

- 新文件 `.aisoft/access.json` 归项目所有，不属于发布包成员。发布包只提供模板和 schema。
- `aisoft` 子命令的参数不变。新增的只有 `aisoft labels-provision`；它在 broker 模式下转调现有 `gitea.labels.provision`。
- broker 的 manifest、操作表与安装字节都不变，所以不需要重装 broker。这是本批的刻意约束：凡需要改 broker 的设计，先停下升级。
- direct 传输只调用 Gitea 公共 REST API，最低版本以 governance manifest 的 `gitea_version` 为准。

## 风险与回滚约束

- 安全取舍（D5/D6）：direct 模式下，会话进程能用到项目凭据。服务端保护缺失时，误操作可能直推 `main`。缓解有三点：闭集里没有危险操作；`access` 检查把缺失保护报成 GAP；技能要求非管理员身份。broker 模式的隔离保持不变，供需要的项目选用。
- 回滚：revert 本批 PR 即可，因为不改 manifest、不改 broker、不迁移数据。已改用 direct 的项目删除 `access.json` 就回到兼容路径。

## 非目标

- 不把注册表移出平台仓，不实现项目自注册，不改 broker manifest 或已登记项目的条目。
- 不新建或轮换任何凭据，不改 live 标签或保护规则，不安装任何东西。
- 不清理 #433 的遗留分支与 worktree，也不处理已移交项目仓的那张 Issue，由负责人另行决定。
- 不改 governance 工具与 manager 校准流程。
- 不改部署合同。

## 未决问题

- 无。
