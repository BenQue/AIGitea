# 03 · Issue / Spec / Plan 与单闸门开发流程

> v3 当前文档契约（更新 2026-08-26）。Issue 是所有工作的主键；小变更允许从明确的 Issue 直接进入 Development Loop，production complex 必须先完成 spec/plan，development complex 使用 Issue 正文中的验收合同。最终 PR 合并是唯一交付硬闸门。Issue #75 已把 readable branch/directory 合同合并进 protected `main`；既有固定数字路径只作证据驱动的 legacy 兼容。

## 1. 绑定模型

```text
Issue #N
  ↔ change/N-short-description
  ↔ docs/changes/N-short-description/<role>-<short-description>-<YYMMDD>.md
  ↔ final PR（Closes #N）
  ↔ commit / CI / deployment SHA
```

- 所有变更必须有 Issue 和映射的 `summary` 文档。
- 小变更可以不写 spec/plan，但 Issue 必须有可验证的 acceptance criteria。
- **交付阶段（Issue #134）**：manifest 的 `change_control` 为 `development` 的项目，其
  强制 complex 变更同样不写 spec/plan，acceptance criteria 改由 Issue 正文提供——门槛
  不变，只是来源从 spec 换成 Issue。未声明该字段的仓库一律按 `production` 处理，行为不变。
  `verification` 的取舍两个阶段完全相同（由 analyzer 决定）；它只表示本次变更欠一份
  无法由 diff review 与 required CI 重放的验证记录，不表示部署或终态。
- `change_control=production` 的复杂变更必须有映射的 `spec` 和 `plan` 文档；development
  complex 不生成仪式性 spec/plan，由 Controller 使用合成 `T01`。
- 部署、迁移以及任何依赖真实环境或一次性观测的变更必须有映射的 `verification` 文档。
- 新 Issue 从分析开始使用单一 `change/N-short-description` 分支；已有 `change/N` 与更早的 `spec/N` 只按历史证据兼容，不作为新 writer 的可选格式。
- 文档与代码进入同一个最终 PR，不再强制独立 docs-only spec PR。

## 2. AI 判级与路由

AI 先判断变更对产品合同的作用，再结合 Issue 显式要求和强制风险规则判定有效复杂度：

```text
restore / unchanged  → small 候选
add / change         → complex
unclear              → awaiting-triage，等待人澄清

强制复杂风险规则
  > Issue 明确要求 complexity/complex
  > Issue 要求 complexity/small 且通过 AI 校验
  > AI 根据 Issue 与仓库证据自动判级
```

small 候选包括恢复既有明确行为的 Bug 修复、纯文档修正、只补充或修正测试，以及不改变外部行为的局部重构或维护。候选还必须目标清楚、范围局部、可简单 revert，且不触发任何强制复杂规则。

出现以下任一项即强制 complex：

- 新增任何产品功能，或改变既有功能、业务规则、用户交互和其他外部可观察行为。
- 存在多个合理方案或未收敛的业务/技术决策。
- 涉及 schema、历史数据迁移、兼容窗口、API 或数据格式。
- 涉及认证、权限、安全、外部系统契约或共享核心组件。
- 跨模块、跨服务或影响核心业务流程。
- 修改 CI、制品、部署、健康检查、备份或回滚。
- 修改 `AGENTS.md`、Agent 行为、自动化 controller 或平台治理规则。
- 失败后不能简单 revert，或数据/运行风险较高。

Issue 作者可以显式选择复杂度，但 `complexity/small` 不能绕过强制复杂规则，`complexity/complex` 不能由 AI 自动降级。标签与实际内容冲突时，AI 依据仓库证据更正并留下理由。信息不足、内容冲突或风险边界无法确定时，Issue 保持 `awaiting-triage` 且不添加 complexity 标签。

## 3. 文档合同

```text
docs/changes/N-short-description/
├── summary-<slug>-YYMMDD.md       # 必须
├── spec-<slug>-YYMMDD.md          # complex 必须（change_control=production）
├── plan-<slug>-YYMMDD.md          # complex 必须（change_control=production）
└── verification-<slug>-YYMMDD.md  # 按下方「何时声明 `verification`」判定
```

文件名固定为 `<role>-<short-description>-<YYMMDD>.md`：slug 使用 2–4 段 lowercase ASCII `kebab-case`、至少包含一个字母、硬上限 32 字符，完整 basename 不超过 64 字符；分支、目录、worktree、文档和 front matter 必须使用同一 `(N, slug)`。slug 创建后不可修改；纠错应开新 Issue。日期等于各文件首次创建日期，普通更新只修改 `updated`，不重命名。

新 worktree basename 固定为 `issue-N-short-description`。`main`、`master`、`head`、`merge`、`pull`、`pr`、`refs`、`change`、`changes`、`docs`、`worktree`、`tmp`、`temp`、`legacy` 是保留 slug，`tmp-`、`temp-`、`legacy-` 前缀同样禁止。同一 Issue 同时出现 legacy/readable 名称或多个 slug 时必须以 `CHANGE_NAME_CONFLICT` 停止。

所有 change 文档的共同 front matter 至少包含：`issue`、`gitea_url`、`change_type`、`requested_complexity`、`assessed_complexity`、`effective_complexity`、`contract_effect`、`confidence`、`risk_flags`、`status`、`branch`、`created`、`updated`；`pr_url` 是 **summary 专属**字段，只写在 summary（#142：spec/plan/verification 里的复制品没有任何代码消费者，四份复制只会互相漂移），由 `aisoft-loop backfill-pr-url` 在 PR 建出后与 `status: pr-open` 一起写入；complex 的 spec/plan/verification 固定使用 `effective_complexity: complex`。summary 另外完整保存 analyzer schema 的 `reason`、语义 `required_docs`、`documents` 角色到真实 basename 的映射和 `override_reason`。无法安全判级时，summary 的 `assessed_complexity` 为 `needs-human-decision`，并从 front matter 与 `## AI 判级` YAML 同时省略整个 `effective_complexity` key，不保留空值或 placeholder；其他 complex 文档尚不得创建。

新合同只使用 `summary`、`spec`、`plan`、`verification` 角色；Controller 严格读取 `documents` 映射并校验角色、slug、日期、目录边界和唯一性，不使用无约束 glob。没有映射的历史 summary 仅回退到 `00-summary.md`、`01-spec.md`、`02-plan.md`、`03-verification.md`，新 writer 不再生成这些名称，也不批量重命名历史文件。

映射的 spec 必须定义目标、可测验收标准、接口/数据/兼容影响和非目标。映射的 plan 必须把每条验收标准映射到 `Txx` 垂直切片、`blocked_by`、预期 touch points 和验证命令。Loop 不得自行修改已经确认的 acceptance criteria 或扩大范围。

### 何时声明 `verification`

`required_docs` 含不含 `verification` 回答的是「这次变更**欠不欠一份验证记录**」，
不是「这次变更要不要部署」（§11 的合取表已经把后一个问题交给仓库属性
`deployment_lifecycle`）。判据因此落在**验收证据的来源**上，而不是变更的题材：

| 全部验收标准的证据来源 | 声明 `verification` |
|---|---|
| diff review 与 required CI 就能复现 | 否 |
| 存在只能在真实环境里执行、或只能一次性观测到的证据 | 是 |

落在第二行的典型形态：部署、迁移、安装与主机侧生效；改动前的基线观测与改动前后
对比；故意失败与回滚的现场；required CI 不跑的确定性命令（跨仓扫描、`--dry-run`
计划、只在本地可达的环境）。部署与迁移必然落在第二行，所以它们始终必须声明——
但它们不是唯一落在第二行的变更，这正是旧判据（按题材）漏掉的那一半。

声明 `verification` **不隐含要部署**，也不改变终态判定：合并后的终态由 §11 的
合取表决定，声明了 `verification` 的变更在**三档 `deployment_lifecycle` 下都到得了
终态**——不部署的仓库与按需部署的仓库当场到 `completed`，声明「合并即部署」的仓库
等一次必然到来的部署。作者不必为了让 Issue 能收尾而少声明一份该写的验证记录
（#163、#168、#192）。

不部署时什么算合格的验证记录：每条 acceptance criterion 都有一条真实执行过的命令
或一次真实观测支撑，命令与输出照实抄，不可达的环境与未执行项显式写明。模板见
`templates/docs/changes/_template/verification.md`，其中 `## 部署验收` 一节只适用于
实际部署或迁移的变更，不部署时整节删除而不是保留标题填「无」。

### 模板是 vendored 副本：改动必须由上游广播（#190）

`templates/docs/changes/_template/` 是合同源，但每个接入项目在 `docs/changes/_template/`
里持有一份**逐字节相同的副本**，`aisoft-project-check.sh` 的 `change-templates` 查的就是
这个相等关系。八条对齐检查里只有它的判据横跨两个仓库，因此也只有它会**因为上游前进而
自发变红**，与下游是否有任何提交无关（LocalWMS #78 / PR #81 是第一次真实复发）。

副本原先既没有版本号也没有依赖声明，下游无从知道自己何时过期。现在这两样都有了：

| 缺的东西 | 补法 |
|---|---|
| 谁持有副本 | `gitea-governance.json` 每个仓库的 `vendors_change_templates`；未声明取 `true` |
| 模板是哪一版 | `codex/config/change-template-sync.json` 的 `template_digest` |

改动模板的变更因此必须在**同一次变更里**刷新 digest：

```bash
bash codex/tools/change-template-sync.sh --refresh-digest
```

不刷新，平台自己的 required CI（`codex/tests/smoke.sh`）就在 `--verify-digest` 这一步变红；
刷新时工具打印完整的下游同步清单——按声明枚举全部 holder，本机有没有那个项目的 checkout
都一样列出。清单里每一项走目标仓自己的 Issue → change 分支 → PR，复制覆盖即可。

不带参数运行是只读的现状核对，可随时重跑，也适合将来挂成非阻塞的定期任务：

```bash
bash codex/tools/change-template-sync.sh
```

它的 `current` / `stale` / `missing` 取自**本机 checkout 的工作树**，不是该仓库 `main` 的
状态；checkout 停在别的分支时会在行尾标注。`unverified` 表示本机读不到那个 checkout，
不表示已同步。

**明确不做的事：不在任何下游项目引入阻塞式 required check。** 下游 CI 要跑这条比对就得
每个 PR 去 clone 平台仓，等于把上游演进变成下游全部在途 PR 的阻塞——包括与模板毫不相干
的那些——而这条 GAP 的修复代价只是一次复制覆盖。这也是 `change-templates` 至今只是一条
GAP 提示而不是错误的原因。约束由 `change-template-sync.json` 的
`downstream_required_check: forbidden` 与 smoke 一起钉住：改掉它，工具停机、CI 变红。

## 4. 平台三维标签与 Matt triage

每个 Issue 的标签分为三个正交维度：

| 维度 | 标签 | 语义 |
|---|---|---|
| 类型 | `type/bugfix`、`type/feature`、`type/docs`、`type/test`、`type/refactor`、`type/maintenance`、`type/platform`、`type/security`、`type/reliability`、`type/data` | 变更是什么；每个 Issue 最多一个主要类型 |
| 复杂度 | `complexity/small`、`complexity/complex` | AI 判定需要哪条流程；互斥，无法判定时都不写 |
| 流程状态 | `needs-analysis`、`awaiting-triage`、`spec-drafting`、`spec-review`、`approved`、`pr-open`、`completed`、`deployed` | Issue 当前阶段 |

类型的默认关系是：`type/bugfix`、`type/docs`、`type/test`、不改变外部行为的 `type/refactor` 是 small 候选；`type/feature` 和改变平台行为或治理合同的 `type/platform` 强制 complex；`type/maintenance` 由 AI 按实际合同影响判定。

Issue #108 增加的三个类型按同一套既有强制规则判定，不新增判级规则：

| 类型 | 判定证据 | 复杂度默认 |
|---|---|---|
| `type/security` | 安全缺陷、凭据处理、认证/授权或权限边界变更。证据是变更触及 token/credential 存储与传递、权限模型、broker/CI 的信任边界，或修复可被利用的缺陷 | 强制 complex（AGENTS.md「认证/权限/安全」） |
| `type/data` | 数据模型、schema 或数据迁移变更。证据是变更改动表/字段/索引定义、迁移脚本，或既有数据的读写语义 | 强制 complex（AGENTS.md「schema/数据迁移」） |
| `type/reliability` | 可用性、韧性或故障恢复变更。证据是变更针对超时/重试/降级/健康检查/回滚路径，或修复只在故障态下暴露的行为 | 按 `contract_effect` 判定：恢复既有行为（`restore`/`unchanged`）是 small 候选，`add`/`change` 走 complex |

`type/security` 与 `type/data` 的强制不依赖 analyzer 是否填了对应 `risk_flags`：risk flag 是可能被遗漏的分析输出，类型标签是 Issue 上不可省略的事实，两条路径都强制才没有缝隙。`type/reliability` 刻意不强制——可用性修复常常正是「恢复既有产品行为」，一律 complex 会把真实的 small 修复挡在流程外，判定权交给 `contract_effect`。

`awaiting-triage` 只表示 AI 无法安全判级、内容冲突或合同不完整，阻止自动路由。`approved` 是合同完整后的运行控制信号，不是 spec 审批闸门，也不授权合并或部署。受控 wrapper 可以在合同完整时自动写入 `approved`，但 controller 启动前必须重新验证合同，不能只信任标签。

Matt triage 另有两个正交维度：category 使用 `triage/bug` 或 `triage/enhancement`，state 使用 `triage/needs-triage`、`triage/needs-info`、`triage/ready-for-agent`、`triage/ready-for-human`、`triage/wontfix`。每个已 triage Issue 恰好一个 category 和一个 state。`triage/ready-for-agent` 只允许 Agent 处理下一阶段，永远不替代 `approved`；`triage/wontfix` 关闭 Issue，但不得写入 `completed` 或 `deployed`。所有标签 mutation 通过同一个 projector，更新一个维度时保留其他维度和非受管标签。

## 5. 小变更路径

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/small + approved（合同完整）
  → Development Loop
  → final PR + CI
  → 人工合并
  → 确定性部署
```

## 6. 复杂变更路径

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/complex + spec-drafting
  → 人与 AI 完成映射的 spec + plan
  → spec-review（可选，不是硬闸门）
  → approved（合同完整）
  → Development Loop
  → final PR + CI
  → 人工合并
  → 确定性部署
```

统一路由合同：

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/small + approved, or complexity/complex + spec-drafting
  → unresolved input: awaiting-triage with no complexity label
```

## 7. 最终 PR

PR 必须：

- body 恰有一行 `Closes #N`，不能额外关闭其他 Issue。
- head 精确为 `change/N-short-description`，并链接 `docs/changes/N-short-description/` 中同 slug 的 summary 与要求文档。
- 说明验收标准与测试证据。
- 说明迁移、部署和回滚影响（若适用）。
- 通过受保护 `main` 要求的 `CI / test (pull_request)`。

PR 合并是唯一交付硬闸门。Analyzer、Loop、provider wrapper 和 CI 都不得合并 PR。

## 8. 升级给人的条件

Loop 只有在合同冲突、必须扩范围、破坏性迁移、安全/权限决策、缺凭据或外部服务、同一根因连续失败三次、验证不可靠或达到预算上限时才停止并请求人决定。普通编译、测试、构建和范围内 review 失败由 Loop 自主处理。

## 9. 当前实施状态

- Issue #57/#60 已把文档 resolver、writer、Matt triage projector、frontier ticket、Agent commit 后置校验、固定 upstream snapshot 与根级路由合并进 source；Issue #75 又统一了 readable branch/directory/worktree/PR 绑定。
- platform canonical taxonomy 为 20 个（Issue #108 把 `type/*` 扩为 10 个），Matt 另加 7 个 namespaced `triage/*`，source manifest 共 27 个；准确集合以 `codex/config/gitea-labels.json` 的 `canonical` 为准。外部状态可能漂移，部署到每个仓库前必须用 broker `gitea.labels.provision` 同步并读回。
- 旧 Issue 与历史文档不重命名；新 writer 只产生语义 basename，并从 Issue #75 起要求目录、branch、worktree 与同一 slug 一致。
- Provider 默认仍为 `IMPLEMENT_PROVIDER=none`；每个项目必须在独立 profile 完成真实验收后才能启用。
- `READY_FOR_REVIEW` 仍停止在人工 merge gate；本次治理变更不部署。
## 10. 依赖 Issue

映射的 summary 可用可选字段 `depends_on` 声明 Issue 编号列表；缺省或 `[]`
表示没有依赖。依赖只影响 PR 就绪门，不改变分支、CI 或人工合并规则：
当前 PR 的 CI 通过后，全部依赖 Issue 必须同时为 closed 且带有 `completed` 或
`deployed` 生命周期终态，Loop 才能进入 `READY_FOR_REVIEW`。否则保存
`awaiting_dependencies`，后续轮询只重查 CI 与依赖，不再次调用 provider、
不创建第二个 PR，也不自动合并。

## 11. 合批关闭与交付终态

合批 PR 可在 merge message body 中逐行列出多个 `Closes #N`。部署成功后的确定性
工具必须处理全部编号并去重，不能只从 subject 猜一个 Issue。更新标签时必须保留
type、complexity 和非生命周期标签。最终 PR 已合并、且没有一次必然到来的部署会认领它时
使用 `completed`；确定性部署与验证成功后使用 `deployed`，它比 `completed` 强，会覆盖
`completed`（反向降级是人的决定，见下）。两者互斥，都不授权合并；Gitea `Closed` 本身
也不证明部署成功。

### 谁推进 `completed`

`deployed` 由应用部署链路在健康检查成功后回写（02 §9）。`completed` 没有对应的
自动触发点：controller 的 lifecycle 写入全在 Development Loop 内，而 Loop 在创建
最终 PR 时就结束了，没有任何组件处在能观察到「合并」的位置上。因此 `completed`
由人在合并后显式运行 `codex/tools/mark-completed-issues.sh` 推进（#115）：

```bash
codex/tools/mark-completed-issues.sh --range 'origin/main~5..origin/main'   # 读计划
codex/tools/mark-completed-issues.sh --apply 167 168                        # 用计划回给的 pinned 编号写入
# 在别的项目仓上运行时目标由 checkout 判定（#184），判定不出才需要显式 --project：
codex/tools/mark-completed-issues.sh --repo ~/Projects/LocalWMS --range '...'  
```

默认只输出逐 Issue 的判定计划、不做任何写入；确认计划无误后加 `--apply` 才经
broker `gitea.issue.labels.set` 写入。已经是 `deployed` 的 Issue 不会被降级为
`completed`：那是对「它到底发生了什么」的判断，必须由人显式做。

### 范围锚不能是会移动的 ref（#175）

`origin/main~N` 在**工具启动那一刻**求值，不是在 `git.fetch.main` 那一刻，也不是在人
点头那一刻。于是有两个窗口，任何一个里 `origin/main` 前进一次，范围就整体后移：

| 窗口 | 两端 |
|---|---|
| W1 | `git.fetch.main` → 跑计划 |
| W2 | 跑计划 → 跑 `--apply`（中间隔着一次人工确认，窗口更长） |

`#167` 收尾时实测到 W1：`git.fetch.main` 取回时 `origin/main` = `770d527`（#167 的 merge），
下一条命令用 `--range 'origin/main~1..origin/main'` 却返回 `{"issue":168,...}`——期间
PR #169 被合进 main，`origin/main~1` 于是等于 `770d527`。写错既不报错也不易发现：错的
对象是别人刚合并的 Issue，而 `completed` 恰恰常常正是它该有的标签。

两条确定性做法，两个窗口各关一个：

- **W1**：使用 `--range` 时，计划的第一行是
  `{"selector":"range","range":<字面量>,"commits":[{"commit":<sha>,"subject":…,"issues":[N,…]}],"pinned":"N …"}`，
  逐 Issue 行另带 `commit`。核对 `commits` 就是自己那次 merge，不必另行 `git log` 反推。
  范围命中 0 个 commit、或命中的 commit 一个 Issue 都不提，都是各自独立的错误，不再复用
  「没给选择器」那句话——那句话说的是参数缺失，与事实不符。
- **W2**：`--apply` 用计划回给的 `pinned`（就是 Issue 编号）重跑，不再传 `--range`。
  Issue 编号不可变，`origin/main` 之后怎么动都不影响写入对象。

`codex/tools/apply-classification-labels.sh` 的 `--range` 面同样处置，包括 `--verify`：
一次被滑走的 `--verify` 会读回别人的 Issue 并报 `projected` 退 0，而这道闸门正是判级窗口
永久关闭前的最后一步（#167），假绿比没有闸门更糟。**`--verify N` 一律用编号。**

`codex/tools/mark-deployed-issues.sh` **不接受 `--range`，本次也没有给它加**：它是部署链路
的 hook，运行在部署已经 checkout 的那个 commit 上，锚是 `HEAD` 或显式的
`MERGE_MESSAGE_FILE`，都是钉死的对象，中间没有第二条命令让 ref 移动；而且它的姿态是任何
缺失前提都 warn + exit 0、绝不让已成功的部署失败，给它加一份需要人读的计划会直接违反那个
姿态——那里没有人在读。该事实由 `codex/tests/test-mark-deployed-issues.sh` 钉住。

判定是一个**合取**，两个条件都取自仓库证据，都不接受人工传入的终态判断（#163）：

| 该 Issue 映射 summary 的 `required_docs` 含 `verification` | 该项目的 `deployment_lifecycle` | 终态 |
|---|---|---|
| 否 | 任意 | `completed` |
| 是 | `application-deploy` | 跳过并给出 `requires-deployment`，等部署链路写 `deployed` |
| 是 | `application-deploy-selective`（**缺省**） | `completed`，`reason` 记为 `deployment-not-guaranteed` |
| 是 | `none` | `completed`，`reason` 记为 `no-deployment-chain` |

两个条件回答的是两个不同的问题：`required_docs` 说的是「这次变更欠不欠一份验证记录」，
`deployment_lifecycle` 说的是「这个仓库的部署链路会不会覆盖到本次 merge」。
#163 之前只有前一个条件，它被迫兼答后一个问题，于是声明了 `verification` 的平台变更
两个终态都没人写——#138、#146、#148 三个已合并 closed Issue 因此长期一个标签都没有。

### 「跳过等待」必须有一个会到来的写入者（#192）

#163 给第二个条件的问法是「这个仓库**有没有**那条链路」。那不是跳过所依赖的问题：跳过是把
Issue 停在原地等 `deployed`，所以真正要成立的是「会有一次部署覆盖**本次 merge**」。两者只在
「合并即部署」的仓库上重合；在按需部署的仓库上分叉，落进分叉处的变更两个终态都没人写——
`completed` 因含 `verification` 被排除，`deployed` 因这次不部署而永不写入。

**这不是推演。** 缺省档下的 LocalWMS 有 15 个已合并且声明了 `verification` 的 Issue，其中 5 个
（#13、#23、#29、#34、#35）closed 之后一个标签都没有；另外 10 个的 `completed` 是绕过这条判定
写上去的——当前工具对那 10 个全部判 `skip`。#192 的映射 verification 记录了逐条读回。

因此 `application-deploy` 的含义收紧为「**每一次 merge 都会被这条链路部署**」，只有它保留
「跳过等待」；不保证覆盖每次 merge 的仓库用 `application-deploy-selective`，终态当场写
`completed`。**缺省取后者，因为两个方向的错并不对称**：

- 写早了会被纠正：`mark-deployed-issues.sh` 剥掉 Issue 的整个生命周期维度再写 `deployed`，
  所以「先 `completed`、后来真部署了」的终点仍然是 `deployed`。
- 写早了也盖不掉真部署：broker 的 `_set_issue_lifecycle` 对「已经 `deployed` 却要写
  `completed`」直接 `REQUEST_DENIED`（本节开头那句「不会被降级」就是它）。
- 漏写没人纠正：本节开头已经说了，没有任何组件处在能观察到合并的位置上。

所以 §3 那句「作者不必为了让 Issue 能收尾而少声明一份该写的验证记录」对**三档都成立**：
`application-deploy` 靠该取值自身的定义保证等待有终点，另外两档当场到 `completed`。
反过来说，**声明 `application-deploy` 等于承诺这条链路覆盖每一次 merge**——不确定就不要声明，
缺省不会落到它上面。

### 哪些仓库的部署链路覆盖每一次 merge

由 `codex/config/gitea-governance.json` 的仓库条目声明一次，不是每次变更重新回答——
「这条链路覆盖不覆盖每一次 merge」是仓库属性：平台仓库里没有任何变更走应用部署链路。

```json
{ "name": "aisoft-platform", "...": "...", "deployment_lifecycle": "none" }
```

- `application-deploy`：`02` §9 的应用部署链路存在，**且每一次 merge 都会被它部署**，在健康检查
  成功后写 `deployed`。目前没有任何仓库声明它——声明它就是承诺覆盖每一次 merge。
- `application-deploy-selective`：链路存在，但只覆盖一部分 merge。**未声明时取此值**——可自愈的
  一档（理由见上一节），不是最宽或最严的一档。
- `none`：没有那条链路，`deployed` 不可达，`completed` 是唯一终态。目前只有 `aisoft-platform` 声明。

工具读到这三个取值以外的任何值都报错退出，不落进任何一档：它据此写终态标签，一个拼错的声明
落进某一档就会读起来像一次决定。

`deployment_lifecycle` 只影响合并后的终态记账：它不触发也不抑制任何部署，不改分支保护与必需 CI，
也不改变 `required_docs` 该不该含 `verification`。manifest 读不到或查不到条目时，
工具报错退出而不是静默跳过——沉默恰恰是它要修的那个失败模式；只是**没有声明该键**不属此列，
按缺省处理。

`--project` 收的是 `codex/config/host-access-broker.json` 里的 **project id**（`localwms`），
不是仓库名。governance manifest 按**仓库名**（`LocalWMS`）索引，两者只在 10 个项目里的 4 个上
同名，所以仓库名由 project id 反查得到、不由调用方提供（#172）——host-access manifest 已经
声明了这个双射，`aisoft_host_access.contract` 也已经强制它的值都存在于 governance manifest。
两侧任一查不到都报错退出，消息各自指名是哪一份 manifest 少了哪个键。

> manifest 与 broker 同理：改了 `codex/config/gitea-governance.json` 之后，扁平安装
> （`/usr/local/share/aisoft/gitea-governance.json`）要重装才跟上。工具优先读仓库布局下的
> `codex/config/gitea-governance.json`，所以从平台 checkout 跑收尾时合并即生效。

### 谁投影 `type/*` 与 `complexity/*`

同一个缺口的另一半（#160）。`aisoft_loop.cli apply-analysis` 是这两个维度唯一的写入点，
它只在 Development Loop 内运行，所以 Mac 交互会话开出的 Issue 判级只落在 summary
front matter 里，标签始终为空——四维正交合同在这条路径上从来没被满足过。

由人在**判级文档写好之后**运行 `codex/tools/apply-classification-labels.sh` 投影
（会话内的位置见 `aisoft-platform` skill 的会话标准动作）：

```bash
codex/tools/apply-classification-labels.sh 160
codex/tools/apply-classification-labels.sh --apply 160
```

与 `mark-completed-issues.sh` 同姿态：默认只输出逐 Issue 的判定计划、不做任何写入；
确认后加 `--apply` 才经 broker `gitea.issue.labels.classify` 写入。两个维度的取值取自该
Issue 映射 summary 的 `change_type` 与 `effective_complexity`，**不接受人工传入标签**；
summary 没有 `effective_complexity`（`contract_effect: unclear` 的
needs-human-decision 形态）时跳过并说明，不臆造复杂度。broker 侧再对已安装的
label manifest 逐维校验，retired 的 `complexity/standard` 写不进去。写入替换的是这两个
维度，生命周期标签、`triage/*` 与 `area/`、`priority/` 等项目扩展标签原样保留。

**已关闭的 Issue 不补写**，工具直接跳过且不提供 override 开关。依据：
`aisoft_loop.cli list-issues` 的请求是 `state=open`，检索缺口只存在于 open Issue 上；
判级事实已经在合并后的 summary 里且不可变；改写已经收尾的记录与「retired label
只报告不移除」「`deployed` 不降级为 `completed`」是同一条姿态。

> 新增 typed 操作后 broker 必须在 Mac 与 gitea-ci 两台重装才生效，
> 未重装时新操作返回 `REQUEST_DENIED / not allowlisted`（`06` 踩坑 20）。

#### 窗口在合并时关闭（#167）

「已关闭不补写」有一个直接推论：**判级投影有一个截止时间，就是合并**。#160 交付之后它仍然
被漏掉过一次——#163 跑了计划、`--apply` 撞上未重装的 broker、PR 合并、窗口关闭——因为当时
没有任何环节会在关闭前提醒，而工具本身也答不出「这个 Issue 现在到底有没有标签」：计划模式
只报「我会写什么」，对已投影和从没投影过输出逐字相同。

补上的是**读回与闸门**，不是补写能力：

```bash
codex/tools/apply-classification-labels.sh --verify 167
```

`--verify` 读回 Issue 当前标签并与映射 summary 比对，逐 Issue 给出
`projected` / `projection-missing` / `projection-mismatch` / `projection-window-closed`，
只有全部 `projected` 才退 0；读不出证据（文档缺失、判级未决、broker 不可用）一律计为失败，
不输出「看起来没问题」。它是只读的（`gitea.issue.read` + `gitea.issue.labels.read`，都是
既有非 mutating 操作，早于 `gitea.issue.labels.classify` 存在），永不调用写操作，与 `--apply`
互斥。`projection-window-closed` 刻意**不给 `remedy` 字段**——没有可执行的补救就是结论本身。

会话侧的落点在 `issue-session-flow` 的待合并块：`判级:` 一行必须是这条命令的真实读回，
不是 `projected` 就不进入待合并；收尾时再跑一次，把漏掉的情形显式报出来。

#### 目标仓库由 checkout 判定（#184）

`--verify` 只有在**读的是正确那个仓库**时才是闸门。这两个工具此前把 `--project` 默认成
`aisoft-platform` 且从不与 `--repo` 核对：在别的项目仓上漏传 `--project`，判级值取自目标仓
checkout，Issue 状态与标签却取自平台仓的同号 Issue。产出的不是报错，而是一个自洽、格式完好、
**针对另一个仓库**的结论。假失败会虚报「判级已永久丢失」；假通过更致命——平台仓的同号 Issue
只要恰好带着 `type/platform` + `complexity/complex`（那里最常见的一对组合），闸门就干净退 0。

现在目标项目**由 checkout 判定**：从 `--repo` 的 Git remote URL 反查 host access manifest 的
`projects[]`，得到 `project_id` 与 `repository`（构造方式与 broker 的 `_expected_git_url` 一致，
所有 remote 的 fetch 与 push URL 都参与匹配——`newemaint`、`sfm-digital-board` 的 Gitea remote
名为 `gitea` 而非 `origin`）。四种结局：

| checkout 能否判定 | 是否传 `--project` | 结果 |
|---|---|---|
| 能 | 否 | 用判定出的项目 |
| 能 | 是且一致 | 用该项目 |
| 能 | 是且不一致 | **报错退出**，不产出任何 Issue 行，不调用 broker |
| 否 | 是 | 用传入的项目（唯一可用证据是操作者的声明） |
| 否 | 否 | **报错退出**，提示传 `--project <project_id>` |

`--project` 因此从「默认」降级为「覆盖」，命名空间仍只认 broker 的 `project_id`（#172）。
每一行 JSON 输出带 `project` 与 `repository` 两个字段，指名它在谈论哪个仓库。只有 GitHub
remote 而没有 Gitea remote 的 checkout（`rsdesign-new`）判定不出项目，必须显式传 `--project`——
这是 fail-closed 的预期形态，不是回归：在此之前它得到的是一个针对平台仓的错误结论。

broker 因操作表陈旧而拒绝时，工具不再把 `REQUEST_DENIED` 原样透出，而是报
`broker-operation-missing`，detail 里直接写明「这是安装期旧表，不是权限问题」与两台重装的
命令（`06` 踩坑 20）——那句话读成权限问题，正是 #163 错过窗口的直接触发因素。

#### 已经错过窗口的 Issue：处置结论

| Issue | Gitea 实际标签 | 合并后 summary 的判级 |
|---|---|---|
| #138 | `['completed']` | `platform` / `complex` |
| #146 | `['completed']` | `platform` / `complex` |
| #148 | `['completed']` | `platform` / `complex` |
| #163 | `['completed']` | `platform` / `complex` |

（2026-08-24 经 broker `gitea.issue.labels.read` 读回。）

**结论：接受这四个 Issue 缺 `type/*` 与 `complexity/*`，不补写、不改写。** 依据与「已关闭的
Issue 不补写」同源：判级事实已经在合并后的 summary 里、不可变、可由 `resolve-documents`
定位；`list-issues` 只查 `state=open`，四维正交合同要服务的那个检索缺口在这四个 Issue 上
已经不存在；为它们破例等同于承认一个 override，而 override 正是 #167 明确不要的东西。
缺口的代价一次性记在这里，换的是姿态没有例外。

闸门与它们的关系要说清楚：`--verify` 只保证**窗口关闭前**被提醒，不回到过去，也不试图回去。
要读任一已关闭 Issue 的判级，看它映射的 summary，或直接跑 `--verify N`——
`projection-window-closed` 那一行本身就带着 `change_type` 与 `complexity` 两个值。
