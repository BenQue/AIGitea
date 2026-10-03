# 04 · Matt skills 与 Development Loop 编排

> v3.6 source contract（更新 2026-08-26）。共享 controller 在 PR 提交确认前进入持久 `AWAITING_PR_CONFIRMATION`；manual 路径保持人工合并，repository opt-in 的 routine small 可经独立 merger 与 broker hard gate 合并。每项目安装、credential、live protection、CI 和部署仍分别验收。

## 1. 设计原则

- Analyzer 与 Development Loop 分离。
- Matt `triage → to-spec → to-tickets → implement` 保持原始技能语义，通过 Gitea tracker adapter 对齐平台阶段。
- `needs-analysis` 触发分析，`approved` 触发 Loop。
- Issue、summary 与路由要求的 spec/plan 是不可由 Loop 擅自改写的执行合同。
- Agent 可以按 frontier `Txx` 在 exact `change/N-short-description` 创建本地原子 commit；外层 controller 管状态、锁、commit 后置校验、push、PR、CI、验证和终态。
- Codex 与 Claude Code 只作为 provider adapter，共用同一 controller 和 verifier。
- manual 最终 PR 只有人可以合并；routine small 仅在提交确认、repository opt-in 与最终 hard gate 全部成立时由独立 per-project routine merger 合并。
- 生产部署不由 analyzer、Loop 或 provider 执行。

## 2. 当前运行基线

| 组件 | 当前状态 | v3 处理 |
|---|---|---|
| `provider-poll.sh` | 共享 analyzer/controller poller，provider 默认显式选择 | 不保存项目坐标；只读取当前 profile 指定的 env |
| `project-poll.sh` | 中央 source 已实现 | 校验 profile 名和 mode 400/600，为 state/worktrees 增加项目 namespace，再调用共享 poller |
| Codex analyzer/controller | source 已发布；synthetic 与一个 real complex pilot 通过 | 作为通用 baseline；不因一个 pilot 通过而自动启用其他仓库 |
| Claude adapter | `claude-provider.sh` / `claude-analyzer.sh` / `analyze-claude.sh` 已在中央 source，parity 测试通过 | 与 Codex 共用 controller、verifier、状态与终态；默认 `IMPLEMENT_PROVIDER=none`，启用仍需项目级验收 |
| `aisoft-agent@.service/.timer` | 中央 source 提供禁用模板 | 安装不 enable/start；每个项目验收后由人显式启用对应 instance |

> **profile 边界**：`~/.config/aisoft/projects/<profile>.env` 绑定一个 Gitea owner/repo、clone 和 provider；`~/.local/state/aisoft-loop/projects/<profile>/` 保存该项目的锁、Issue state 与 worktrees。rsdesign-new Issue #8 只是验证证据，不是默认 profile。AISoftPlatform 本身是平台 source/documentation 仓库，不要求应用部署。

## 3. 目标组件

```text
aisoft-agent@<profile>.timer / controlled trigger
  → project-poll <profile>
  → loop-controller
      ├── contract loader
      ├── Matt tracker / workflow adapters
      ├── worktree + issue lock
      ├── Codex adapter
      ├── Claude adapter
      ├── deterministic verifier
      ├── Gitea Issue/PR/CI adapter
      ├── AWAITING_PR_CONFIRMATION state
      ├── routine-small eligibility
      ├── project-scoped broker merger
      └── local state store
```

两个 adapter 等价、可互换，由 `IMPLEMENT_PROVIDER` 显式选择。

第一版在每个项目 profile 内只允许一个 active Issue，使用该 profile 的独立 state、lock 和 worktree。多个 profile 默认都不启用；若后续并行启用，必须另做 VM 容量和 provider 并发验收。不得为项目、Claude 或 Codex 各复制一套状态机。

## 4. Analyzer

Analyzer：

1. 读取 Issue、`AGENTS.md`、仓库和相关测试。自动化运行时 `aisoft_loop.cli get-issue` 写出的 Issue JSON 在原始 `comments` 计数之外带上完整评论线程 `issue_comments`（按时间顺序，投影为 `id/author/created_at/body`，与 broker `gitea.issue.comments.read` 同形），走同一条只读 project-agent token 路径；后出现的修订/收窄/推翻正文范围的评论对判级优先于正文，`render-analysis` 对缺少 `issue_comments` 的 payload fail-closed（#180）。
2. 只读分析产品代码，识别主要 type、产品合同影响、风险和有效复杂度，输出固定结构；模型不得直接修改 Issue 标签。
3. 外层 wrapper 先校验 analyzer 输出的 slug，再创建 `change/N-short-description`、`issue-N-short-description` worktree 与同名文档目录，写 summary、提交、推送和评论；legacy Issue 仅从已有远端/历史证据解析。
4. 不实现代码、不创建最终 PR、不启动部署。

所有 Issue 都经过 analyzer；是否需要 spec/plan 由有效复杂度决定。Analyzer 至少输出：

```yaml
change_type: bugfix # bugfix | feature | docs | test | refactor | maintenance | platform | security | reliability | data
requested_complexity: auto # auto | small | complex
assessed_complexity: small # small | complex | needs-human-decision
effective_complexity: small # small | complex；needs-human-decision 时省略
contract_effect: restore # restore | unchanged | add | change | unclear
reason: 恢复已经明确的既有行为
risk_flags: []
required_docs:
  - summary
document_slug: restore-login-flow
confidence: high # high | medium | low
override_reason:
```

Wrapper 必须按强制风险规则和显式标签优先级复核结果，再执行互斥标签变更：

- 明确 small：只保留一个 `type/*` 和 `complexity/small`；合同完整时写入 `approved`，否则进入 `awaiting-triage`。
- 明确 complex：只保留一个 `type/*` 和 `complexity/complex`；production 进入 `spec-drafting`，
  spec/plan 合同完整后才可写入 `approved`；development 由 Issue 正文提供可测验收标准，
  不生成 spec/plan，合同完整后可写入 `approved`。
- `assessed_complexity: needs-human-decision`、`contract_effect: unclear`、低置信度冲突或风险边界不明：移除两个 complexity 标签，保持 `awaiting-triage`。
- Issue 显式要求 `complexity/complex` 时不得降级；显式 `complexity/small` 触发强制复杂规则时必须覆盖为 complex，并在 summary 和 Issue 评论记录 `override_reason`。

每项目的 analyzer 运行时由 `codex/config/host-access-broker.json` 中 `projects[].vm_profile.analysis_provider` 声明
（#164/#178），安装时渲染为该 VM profile 的 `ANALYSIS_PROVIDER`；`aisoft_host_access/contract.py` 只接受三个取值，
其它值在 manifest 加载时 fail closed：

| 取值 | 含义 |
|---|---|
| `codex` | 该 VM 用 Codex CLI 经 `codex/agent/analyze-codex.sh` 跑 analyzer |
| `claude` | 该 VM 用 Claude Code CLI 经 `codex/agent/analyze-claude.sh` 跑 analyzer |
| `none` | 该项目不跑自动 analyzer；判级由 Mac 上的交互式会话（Claude Code 或 Codex）按本节合同完成 |

取值必须是该 VM **服务层**真实可执行的运行时——登录 shell 里能跑不算证据（#164 把 localwms 改为 `codex`、#178 把
emaintenance 改为 `none`，都是因为 systemd 层的 `claude` 不可达）。同一 profile 的 `implement_provider` 迁移期固定 `none`，
启用是每项目独立验收门。

## 5. Loop 启动条件

每次收到启动信号时，controller 都必须从 Issue、有效评论、summary 和当前路由所需文档重新计算合同有效性，不能把现有 `approved` 当作充分证据。启动前必须满足：

- Issue 为 open 且带 `approved`。
- exact change branch、同 `(N, slug)` 文档目录和唯一映射的 `summary` 存在；新合同必须通过 `documents` 映射解析，legacy 合同才允许固定数字目录/basename。
- 恰有一个由当前证据支持的 `complexity/small` 或 `complexity/complex` 标签，且 type、复杂度和强制风险规则无冲突。
- `complexity/small` 时 Issue 有可测验收标准，summary 字段完整，且没有强制复杂风险。
- `complexity/complex` 时，production 要求映射的 `spec` 和 `plan` 完整、验收映射明确、
  Ticket graph 有可执行 frontier 且无未决问题；development 要求 Issue 正文有可测验收标准，
  Controller 使用合成 `T01`。
- 没有另一个 active Issue 占用第一版 controller。

任一条件不满足时 controller 必须拒绝启动、由 wrapper 修正到 `awaiting-triage` 或 `spec-drafting`，并输出 `NEEDS_HUMAN_DECISION` 或 `BLOCKED_EXTERNAL`；不得猜测合同，也不得因 `approved` 已存在而跳过复核。

## 6. 每轮执行

```text
加载合同和持久化状态
  → 从 plan Ticket graph 选择第一个未阻塞 frontier Txx；development complex 无 plan 时使用 T01
  → provider 显式调用 $implement，在隔离 worktree 实现并本地提交
  → controller 校验 branch、ancestry、commit subject、改动范围与 clean tree
  → verifier 独立运行要求的命令
  → 未完成 frontier：记录进度并进入下一项
  → 全部本地完成：生成 policy-specific PR candidate，持久化 AWAITING_PR_CONFIRMATION
  → 明确确认后：controller push/create unique final PR，继续 CI repair
  → manual: READY_FOR_REVIEW；routine-auto: broker final-head hard gates → AUTO_MERGED
  → 失败：归因并把真实输出反馈给下一轮
  → 判断完成、继续或升级
```

普通 lint、类型、测试、构建和范围内 review 失败不能立即转人工。禁止通过删除测试、弱化断言、隐藏错误或改验收标准制造假绿。

### #327 Controller 专属的 main 整合与发布

治理合同已明确；runtime、installed 和 live 能力仍需分别验收。provider 的本地 commit 检查继续
拒绝 merge；整合只能由外层 Controller 在批准合同内、本人 worktree、验证后的第一父链上构造。
两 parent 精确为 `[本 Issue 已核验末端, 本次 fresh manifest main]`，tree 必须可独立复算且无冲突。
original/current remote tip 必须保留为候选祖先；未知来源、反序/octopus/foreign merge、tree额外内容、
冲突、范围扩张或不支持的 Git 状态停止，不能 rebase/amend 已发表历史。

broker 独立检查完整 DAG/tree/scope 与 exact head/remote tip；普通 FF 发表前还要拒绝传输竞态，
包括并发 tip 恰好是候选祖先的情形。成功必须读回真实 remote head 并核对本次验证锚。
main 在发表后前进则记录已落地 head 与新 main，停止 READY_FOR_REVIEW，重新整合/验证；
网络或回执不明不得假称零写入。没有 force/lease-force、任意 hook 或身份 fallback。

治理应用必须是只改批准合同映射文本的独立步骤，commit 后停止；fresh run 重读才进入 runtime
frontier。旧 installed 缺能力时禁止沿用 leased publish；#327 本身使用负责人本人 UI 自举卡，
Agent 不代提交。PR/两机安装仍各遵守具体确认与验收，source merge 不证明 installed 生效。

**#327 T04 可信证据治理合同（尚未实现/启用）**：trusted-critical Controller 的冻结上下文、受控执行/观察、限定整合和记录由固定 installed verification authority 保管；authority 实际 EUID=0，仅执行已审计平台代码。provider/项目 verifier 以登记非 root UID/GID 在真实 OS 隔离内运行，不能访问 protected ledger、broker credential 或控制入口；只降低 UID、root-owned 文件或 peer UID 不证明程序/批准身份。缺隔离、可信工具链或记录均 fail closed/GAP，不用环境、source wrapper 或身份 fallback。

人类合同/最终 PR 确认须经另获 exact 授权的非 Agent operator 登记为 protected grant/PR授权；local approved、owner marker、commit subject 和 caller PASS 均不是可信根。grant 冻结 exact tuple、scope/内容目的、graph、required verifier、source/policy pin 和 R0，记录由 authority 自己观察执行并逐对象验证；已有/未知或跨 Issue 对象须明确 adoption，来源只指已验证/采用对象，不声称物理创作分支。broker 仍独立重算完整 DAG/tree/delta，核对 sealed checkpoint、PR授权与 strict remote tip，再普通 FF；不重置 R0 或弱化原 per-push/readback 门。

新 public 操作仅 `git.change.begin(branch,ticket)`、`git.change.verify(branch,ticket,sha)`；`git.push.change(branch)` 参数不变。无 public approve/merge、自由 command/path/socket/UID/PASS 入口。代码/config/service 的 exact source 范围及固定路径以 #327 映射 spec 为准，默认 disabled、UID/GID 空、provider none、服务描述 inert。原治理 T04 只应用映射文本、验证/local commit 后 STOP；后续 fresh run 重读才实施 T02。source 合并后的 I01 文件安装与 I02 每主机 exact 权限绑定、注册/启停、真实隔离/FF/rollback 各依独立 operator 卡；不继承 T01、路线选择或 #316，不自动 provision/启动。AC-7/AC-9/AC-10/AC-11 未闭合保持实际未完成，不把 mock/source/自动 closed 当 installed/live 验收。

**#327 T05 资源与工具链治理合同（source 已批准；installed/live 未验收）**：critical 入口由固定 installed native bootstrap 在任何 Python 平台模块导入前核验完整 toolchain closure 与角色绑定；范围包括 interpreter/stdlib/late import/native loader/library/Git transport/helper/OS delegate、OS alias 与 Mac dyld shared cache/subcache。完整目录/build dependency inventory及静态/显式动态解析为基线，loaded-module集合或一次trace不能证明完整；未知依赖/漂移/未注册一律GAP。严格清env/FD、canonical regular最终程序、无source/PATH/未知shim fallback；bootstrap自身OS loader为冻结TCB，不声称main前无库执行。exact source、固定incoming path/FD、build/descriptor与默认disabled空host registry遵映射spec，不自动安装新工具链或以root构建项目。

Mac scratch固定64 MiB UDIF/UDRW/HFSX无分区模板，root Git暂存256 MiB；模板create仅未来exact I02 operator，runtime不格式化任意设备。真实ownership/容量/nodev/nosuid/noexec/nobrowse与镜像→device→mount映射须读回，单scratch/单readonly input、最多两个对象卷；CONTEXT/temp/复制双份窗口全部创建前预留并计入8 GiB保留预算、64 MiB平台元数据上限，input≤256 MiB/4096entries/depth16。Linux同等scratch/对象tmpfs上限及inode/namespace隔离须真实验收。每verifier新own-lease，descendant未退出、busy、device复用、未知映射、崩溃/断电均保留预算/证据并quarantine；不force/resize/hosttmp fallback/盲重试/递归清理user卷/自动删除历史。只依protected exact FD清单和确认own detach后的readback回收；R0不重pin。Mac noexec不支持scratch中新产native binary执行，能力不足明确GAP，不泛称SDK/build可用。

public policy仍`change-verification/v1`四key、public仅begin/verify且push仅branch；private grant/record/operator为v2并绑定closure/resource/lease digest，v1只作历史只读，不自动迁移/清空。publish先持久pending再transport，断线/重启/重入只poll既有attempt、不重复推送；真实possible-write/已落地H保留，不能把传输失败写为零mutation。T05仅原14治理文本+四角色（18文件）独立应用/验证/local commit后STOP，后续fresh重读才继续既有T02 WIP；不混runtime。I01只惰性文件安装/hash-mode-owner、installer no-op与文件失败rollback；I02每主机exact卡独立批准registry/模板/own-device/服务启停/真实权限、FF/publish no-op/reject与运行资源rollback，AC-7要求不减。默认none/disabled，不provision账户/凭据/grant/全局SDK/provider。AC-7/9/10/11未闭合不把source/mock/自动closed当实际完成，不提前cleanup/归档，不继承#316或路线选择权限。

## 7. Verifier

按项目和合同选择：format/lint/typecheck、目标单测、集成测试、迁移验证、完整测试、构建、浏览器/API acceptance、diff review 和 PR CI。

Verifier 必须由外层脚本独立运行，不信任模型自述。每条 acceptance criterion 至少映射一个真实验证命令或人工最终 review 项。

## 8. 重试和升级

- 同一根因最多连续尝试三次。
- 时间、token、总轮数在 controller 专项设计中配置。
- 需求冲突、范围扩张、破坏性迁移、安全/权限决策、缺凭据/外部服务、验证不可靠或预算耗尽时停止。
- 升级输出必须包含：已完成、失败验证、根因、已尝试、需要人决定的问题和选项影响。

## 9. 终态

| 终态 | 条件 |
|---|---|
| `AWAITING_PR_CONFIRMATION` | 本地 verifier 通过，PR candidate handoff 已固定，等待人确认提交 unique final PR 与 `manual|routine-auto` policy；重复 poll 不调用 provider 或创建 PR |
| `READY_FOR_REVIEW` | manual 合同满足，本地 verifier 和 PR CI 通过，最终 PR 等待人合并 |
| `AUTO_MERGED` | routine-auto 的最终 head 通过 broker 全部硬门并返回 merge receipt；不表示部署或 `deployed` |
| `awaiting_dependencies` | PR CI 已通过，但一个或多个 `depends_on` Issue 尚未同时 closed 且标记 `completed` 或 `deployed` |
| `NEEDS_HUMAN_DECISION` | 需要需求、架构、安全、范围或破坏性操作决定 |
| `BLOCKED_EXTERNAL` | 缺凭据、服务、网络或外部协调 |
| `FAILED_LIMIT` | 达到重试、时间、token 或总轮数限制 |

`READY_FOR_REVIEW` 只通知人 review/merge。`AUTO_MERGED` 只允许来自唯一
`gitea.pull.merge.routine(number, sha)` operation；它不得调用 deploy 或写 `deployed`。会话随后自动运行
确定性终态 plan/apply、change document check、worktree/local branch cleanup 与归档，不再增加确认点。
routine 任一 hard gate 失败不得自动转成更宽权限的 merge 路径。

## 10. Provider 验证矩阵

1. 静态验证 skills、metadata、sandbox 和禁止参数。
2. 合成 Issue 验证合同读取与终态。
3. 至少一个明确标注的真实 pilot 验证 Git/Gitea/PR/CI 集成；历史 evidence 是 rsdesign-new complex Issue #8，该项目自 #252 起已退出平台治理，其证据只作追溯。
4. small/complex 路由、缺合同、自修复和失败反馈由共享 synthetic 覆盖；每个新 profile 再运行与本项目相符的 real small/complex acceptance。
5. 验证 CI failure feedback。
6. 验证升级条件和三次同因失败。
7. 只有需要部署的应用 profile 才在开发/测试环境验证首次部署和回滚；AISoftPlatform 等文档/source 仓库不适用。
8. 两个 provider 用同一通用矩阵做 parity 验证；项目级 enablement 仍是独立门禁。

## 11. 安全与回滚

- controller 使用专用 `coder` 用户；Gitea 身份是 manifest-declared project agent，经 broker typed 操作使用最小权限。
- Agent/provider 不持有 push、PR、merge 或 deploy credential；独立 routine merger 是 Gitea 1.26.4 的 exact-repo Write identity，服务端没有 merge-only ACL。其 credential 由 broker 独占，唯一 typed merge operation 派生 exact repository/PR/head，main push/force allowlist 均为空；ordinary Git 与 cross-project write 依靠 custody、manifest/final-head gates 和 zero fallback 禁止。commit subject 必须包含 `#N` 与当前 `Txx`，修复使用追加 commit。
- 不打印 `.agent.env`、auth、Git credentials 或应用环境变量。
- 新 profile 默认 `IMPLEMENT_PROVIDER=none`；复制模板、安装 unit 或文档更新都不启用 Loop。
- Loop 试点失败时停止 controller，保留 analyzer，开发回到 Mac 人机交互，不影响 CI 和生产部署。
