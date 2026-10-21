# 03 · Issue / Spec / Plan 与单闸门开发流程

> 现行合同：本册定义 Issue 到唯一最终 PR 的绑定、判级与路由、语义文档、标签、两条开发路径、最终 PR 闸门、依赖与合并后终态。Issue 是所有工作的主键；最终 PR merge 是唯一交付硬闸门，只由人合并，部署另行授权。路由取值以 `aisoft-platform` 技能的路由表为准，标签集合以 `codex/config/gitea-labels.json` 为准。

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
- **交付阶段**：manifest 的 `change_control` 为 `development` 的项目，其强制 complex 变更同样不写
  spec/plan，acceptance criteria 改由 Issue 正文提供——门槛不变，只是来源从 spec 换成 Issue。
  未声明该字段的仓库一律按 `production` 处理。`verification` 的取舍两个阶段相同；它只表示本次变更欠一份
  无法由 diff review 与 required CI 重放的验证记录，不表示部署或终态。
- `change_control=production` 的复杂变更必须有映射的 `spec` 和 `plan` 文档；development
  complex 不生成仪式性 spec/plan，会话使用合成 `T01`。
- 部署、迁移以及任何依赖真实环境或一次性观测的变更必须有映射的 `verification` 文档。
- 新 Issue 从分析开始使用单一 `change/N-short-description` 分支；已有 `change/N` 与更早的 `spec/N` 只按历史证据兼容，不作为新 writer 的可选格式。
- 文档与代码进入同一个最终 PR，不强制独立 docs-only spec PR。

### change worktree 的单写者归属

**一个 change worktree 的写者是且只是该 Issue 的会话。** 别的会话发现它需要变基、需要修
冲突、需要重跑验收时，只能**通知**那个会话或**交回**给它，不得代劳——哪怕改动本身是对的。

> 🚩 **Red Flag**：「我顺手把别人那个 worktree 变基一下，反正 main 已经前进了」——停。
> 你正在改写一条**不属于你**的证据链：冲突怎么解的没有归属，验收在谁的环境里跑的读者分不
> 出，而错误会跟着对方的 PR 直达 merge 这道唯一交付闸门。**通知，或者交回。**

`git rebase` / `git commit` / `git checkout` 都是纯本地操作，不经过 broker，平台侧对进入别人的
worktree 零感知（实例见 `06` 踩坑 28）。归属由三样东西支撑：

| 机制 | 命令 / 位置 | 它能回答什么 |
|---|---|---|
| 归属标记 | `$(git rev-parse --git-dir)/aisoft-owner.json` | 这个 worktree 属于哪个 Issue 的哪个会话 |
| 推送闸门 | broker `git.push.change` | **谁**可以推这条分支 |
| 只读扫描 | `aisoft-loop scan-worktrees --repo <checkout>` | 本机哪些 change worktree 的 HEAD 已经离开了它最近一次 push |

建完 worktree 立刻 claim，并在此后每次调 broker 推送时带上同一个会话 id：

```bash
AISOFT_SESSION_ID=<本会话 id> PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli \
  claim-worktree --branch change/N-short-description --worktree /private/tmp/issue-N-short-description
```

会话 id 走环境变量而不是 broker 参数：broker 的 `arguments` 是精确集合，给既有操作加参数
会让全部既有调用方当场 `ARGUMENT_MISMATCH`（`06` 踩坑 26）。没有标记、标记不合法、标记指向
别的分支、`AISOFT_SESSION_ID` 缺失或与标记不符，`git.push.change` 一律 fail closed，四个
错误码分别是 `WORKTREE_UNCLAIMED`、`WORKTREE_CLAIM_INVALID` 与两种
`WORKTREE_OWNER_MISMATCH`，拒绝发生在解析凭据之前，不产生任何网络写。

#### 闸门拦不到什么，以及因此必须做的一步

归属闸门回答「谁可以推」，单独不能保证内容。已发表历史的重写必须在远端写入前拒绝，不能靠事后
回执追认：broker 独立复核 original/current remote tip 的祖先链、提交来源、完整 DAG/tree、合同范围和
fresh main。已安装的 broker 缺少这些能力时停止，不调用 leased rewrite。

逐次检出仍保留两处：

- **推送之后**：`git.push.change` 的返回体带 `pushed_head`（本次推上去的 40 位 SHA）与
  `previous_head`（该分支上一次 push 的 SHA）。**首次 push 核对 `pushed_head` 是否等于
  `AWAITING_PR_CONFIRMATION` 候选中已核验的 exact head；PR summary-only 回填与范围内 CI
  修复的每次后续 push，则比对该次 fresh 本地验证并记录的 exact head。每次比较都是必做步骤。**
  后续 push 前确认本会话归属、exact branch、新增 diff 在已批准合同内、必要验证通过与工作树清洁，
  再记录当前 40 位 lowercase head；不能沿用首次旧 SHA，也不能省略读回校验。`previous_head`
  仅作审计信息，不能替代本次验证锚。提交授权仍绑定 exact Issue/branch/policy，合法回填与范围内
  CI 修复不新增每 commit 确认；范围扩大、他人改写或 `pushed_head` 不匹配立即停止并查明原因，
  不得把未知改写直接登记为新的合法 head。首次候选在确认后变更时先停止并更新候选验证证据。
- **推送之前**：`scan-worktrees` 把同一状态报成 `rewritten`（HEAD 不是最近一次 push 的后代）。
  `unclaimed` 与 `claim-invalid` 同样计入 GAP；`ahead`（有未推送的本地 commit）与 `unpushed`
  照列但不计——否则这条命令在整个实现期都是红的，读者会被训练成忽略它。

### main 整合与发布（稳定规则）

main 整合只用普通 fast-forward，并保留 original/current remote tip 的祖先关系；非法 DAG、tree、范围和并发漂移一律拒绝，禁止 force。会话只在本 Issue 的 exact 分支追加线性本地 commit；冲突时停止并保留前态，不自动覆盖内容。

### 衍生 Issue 的正文与认领

会话中途发现的新问题一律开新 Issue，不扩本次范围。作者会话必须在**正文**写清四件事：

- 来源：哪个 Issue 的哪次会话发现的；
- 目标项目：这条 Issue 应该在哪个仓库解决；
- 可测验收标准：至少一条可观察、可验证的结果；
- 已知依赖：阻塞它的 Issue 编号，没有就写「无」。

依赖必须落在正文上。会话上下文会被压缩，Issue 不会——只活在上下文里的顺序关系一定会丢。

立案时 `gitea.issue.create` 在创建的同一次写入里带上流程入口标签，取值是 `needs-analysis`
或显式指定的 `triage/needs-triage`。Issue 因此一建出来就站在流程入口上。

**衍生 Issue 的默认认领方是调度会话**：它按「开放 Issue 清扫」逐条判定、派单，或汇总成需裁决
项交给人。没有调度会话时，作者会话在收尾时自己开 Issue 并派卡片。

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
- 修改 `AGENTS.md`、Agent 行为、broker 合同或平台治理规则。
- 失败后不能简单 revert，或数据/运行风险较高。

Issue 作者可以显式选择复杂度，但 `complexity/small` 不能绕过强制复杂规则，`complexity/complex` 不能由 AI 自动降级。标签与实际内容冲突时，AI 依据仓库证据更正并留下理由。信息不足、内容冲突或风险边界无法确定时，Issue 保持 `awaiting-triage` 且不添加 complexity 标签。

### 2.1 Routine small merge（已退出）

routine 自动合并已按 [ADR 0002](docs/adr/0002-deterministic-development-flow.md) D4 退出：broker 没有合并操作，
所有仓库的最终 PR 都只由人合并，提交前确认不区分 merge policy。分类仍是两个标签维度，不新增 merge-policy 维度。
routine 的 manifest 字段与凭据种类已删除，合同拒绝仍声明它们的 manifest；原合同见
[迁出说明](archive/automation-engine-exit-261020.md)。

### 2.2 路由卡

判级之后，会话查 `aisoft-platform` 技能的 [路由表](skills/aisoft-platform/references/route-policy.md)
得到路由卡，写进 summary front matter 的 `route:` 块与判级评论，在确认点 1 候选中显示为「路由」行
（[ADR 0002](docs/adr/0002-deterministic-development-flow.md) D1）。路由卡决定 process、模型档位 tier 与推理强度 effort、
必用技能、method、verify、review，`confirm` 恒为 2。复杂度仍由本节上面的规则判定，路由表只做映射；路由表
是唯一来源，取值、细化规则、必用与禁用都以它为准，本节不复述。

人可以在确认点 1 覆盖任何一格，覆盖写进 `override_reason`；覆盖不能把强制 complex 降成 small。合同只写档位，
型号见 `08` §7.3。判级投影不变：仍是四维标签，不新增 `route/*`。`route:` 是可选块，`check-change-documents`
在它存在时校验取值闭集，以及 `process` 与 `effective_complexity` 一致。

**大需求链**：`change_type: feature`、`contract_effect: add`，或一个阶段要拆成多个 Issue 时，先 Matt `grill-me`
定需求（what），再 `to-spec`；how 仍有多个合理方案、或涉及新架构、数据模型、外部契约时，用 superpowers
`brainstorming`（只问 how，以 grill 结论为输入，结论写进映射 spec 的「方案与决策」节），技术可行性存疑时改用
Matt `prototype`；然后 `to-tickets` 出 Txx 计划，开发按 Txx 顺序执行。`grill-me` 与 `brainstorming` 都在确认点 1
之前完成，它们就是形成合同的过程。

## 3. 文档合同

```text
docs/changes/N-short-description/
├── summary-<slug>-YYMMDD.md       # 必须
├── spec-<slug>-YYMMDD.md          # complex 必须（change_control=production）
├── plan-<slug>-YYMMDD.md          # complex 必须（change_control=production）
└── verification-<slug>-YYMMDD.md  # 按下方「何时声明 `verification`」判定
```

文件名固定为 `<role>-<short-description>-<YYMMDD>.md`：slug 使用 2–4 段 lowercase ASCII `kebab-case`、至少包含一个字母、硬上限 32 字符，完整 basename 不超过 64 字符；分支、目录、worktree、文档和 front matter 必须使用同一 `(N, slug)`。slug 创建后不可修改；纠错应开新 Issue。日期等于各文件首次创建日期，普通更新只修改 `updated`，不重命名。

新 worktree basename 固定为 `issue-N-short-description`。`main`、`master`、`head`、`merge`、`pull`、`pr`、`refs`、`change`、`changes`、`docs`、`worktree`、`tmp`、`temp`、`legacy` 是保留 slug，`tmp-`、`temp-`、`legacy-` 前缀同样禁止。同一 Issue 同时出现 legacy/readable 名称或多个 slug 时必须以 `CHANGE_NAME_CONFLICT` 停止。纯编号名称只在 manifest-fixed remote 或 Git history 已有证据时作读取或维护兼容，调用方不能用 `legacy` 开关绕过这种 evidence-derived 判定，也不得批量重命名或删除历史对象。

所有 change 文档的共同 front matter 至少包含：`issue`、`gitea_url`、`change_type`、`requested_complexity`、`assessed_complexity`、`effective_complexity`、`contract_effect`、`confidence`、`risk_flags`、`branch`、`created`、`updated`。`status` 是 **summary 的** lifecycle 字段：确认点 1 只把 summary 改为 `approved`，spec 与 plan 模板不再带 `status`，已有文档里的 `status` 照旧合法但没有消费者；verification 的 `status` 只描述这份验证记录本身（#408）。`pr_url` 是 **summary 专属**字段（spec/plan/verification 里的复制品没有代码消费者，只会互相漂移），由 `aisoft open-pr` 在 PR 建出后与 `status: pr-open` 一起写入（手工修复用 `aisoft backfill-pr-url`）；complex 的 spec/plan/verification 固定使用 `effective_complexity: complex`。summary 另外完整保存 analyzer schema 的 `reason`、语义 `required_docs`、`documents` 角色到真实 basename 的映射、可选的 `route:` 与 `override_reason`。无法安全判级时，summary 的 `assessed_complexity` 为 `needs-human-decision`，并从 front matter 与 `## AI 判级` YAML 同时省略整个 `effective_complexity` key，不保留空值或 placeholder；其他 complex 文档尚不得创建。

新合同只使用 `summary`、`spec`、`plan`、`verification` 角色；resolver 严格读取 `documents` 映射并校验角色、slug、日期、目录边界和唯一性，不使用无约束 glob。没有映射的历史 summary 仅回退到 `00-summary.md`、`01-spec.md`、`02-plan.md`、`03-verification.md`，新 writer 不再生成这些名称，也不批量重命名历史文件。

映射的 spec 必须定义目标、可测验收标准、接口/数据/兼容影响和非目标。映射的 plan 必须把每条验收标准映射到 `Txx` 垂直切片、`blocked_by`、预期 touch points 和验证命令。会话不得自行修改已经确认的 acceptance criteria 或扩大范围。

### 声明与实际文件共用一个校验结果

- summary front matter 的 `required_docs` 是文档义务的唯一声明事实源，`documents` 是新格式角色到安全 basename 的唯一路径事实源。共用受限 Python 解析器，拒绝空、未知、重复或混合角色与 legacy 文件名的列表，首项必须为 summary。
- `route.required_docs` 给出阶段与复杂度的最低合同要求；`check-change-documents` 检查声明满足这些要求，不得用路由生成的列表替换声明或丢掉额外角色。development 不强制 spec/plan，production complex 仍必须有 spec/plan；任何路由都不能让已声明 verification 的文件义务消失。
- 新格式 `documents` 的每个显式映射均须指向本 Issue 目录内可读取的普通文件，且通过既有角色、slug、日期、front matter 与路径边界校验；即使角色不在 required_docs 里也一样。缺文件或符号链接逃逸必须报错，诊断包含 Issue/change、role 与真实 basename。required_docs 的每一项必须有映射和实际文件。
- `resolve-documents N --repo <checkout>` 成功时返回角色到 basename 的 JSON，并拒绝不存在的显式映射；只读 `resolve-required-documents N --repo <checkout>` 返回 `required_docs`（规范化语义角色数组）和 `documents`（角色映射）。`check-change-documents` 与 `mark-completed-issues.sh` 共用同一解析和校验结果；resolver 或 JSON 失败不能回退为成功。
- legacy 固定映射是历史推断；未声明的可选 spec/plan/verification 不要求生成。显式 required_docs 中的历史 basename 必须有实际文件，并规范化为相应语义角色（如 `03-verification.md` → `verification`）。缺 required_docs 报明确 GAP；不新增 legacy 开关，不批量重命名或改写历史文档。
- 合同草稿首次写入使用受限 publisher：`publish-spec`/`publish-plan` 可在 open Issue 的 exact branch 上首次创建自己映射的目标，继续执行路径、日期、front matter 与 Ticket graph 硬门；不向 reader 暴露通用 skip-existence 参数。草稿尚未齐全时，严格 resolver、文档检查与终态检查仍须拒绝交付；会话在确认点 2 前运行 `check-change-documents`。
- `mark-completed-issues.sh` 的 dry-run 遇无效声明或缺文件时输出可搜索的 skip 原因和诊断，apply 对该 Issue 零 broker 写入。合法合同时，再按 §11 的 `deployment_lifecycle` 判终态。文件存在与可解析不证明 verification 内每项现场动作已执行。

### 何时声明 `verification`

`required_docs` 含不含 `verification` 回答的是「这次变更**欠不欠一份验证记录**」，
不是「这次变更要不要部署」（后一个问题由 §11 的仓库属性 `deployment_lifecycle` 回答）。
判据落在**验收证据的来源**上，而不是变更的题材：

| 全部验收标准的证据来源 | 声明 `verification` |
|---|---|
| diff review 与 required CI 就能复现 | 否 |
| 存在只能在真实环境里执行、或只能一次性观测到的证据 | 是 |

落在第二行的典型形态：部署、迁移、安装与主机侧生效；改动前的基线观测与改动前后
对比；故意失败与回滚的现场；required CI 不跑的确定性命令（跨仓扫描、`--dry-run`
计划、只在本地可达的环境）。部署与迁移必然落在第二行，所以它们始终必须声明，
但它们不是唯一落在第二行的变更。

声明 `verification` **不隐含要部署**，也不改变终态判定：声明了 `verification` 的变更在**三档
`deployment_lifecycle` 下都到得了终态**——不部署的仓库与按需部署的仓库当场到 `completed`，
声明「合并即部署」的仓库等一次必然到来的部署。作者不必为了让 Issue 能收尾而少声明一份该写的验证记录。

不部署时什么算合格的验证记录：每条 acceptance criterion 都有一条真实执行过的命令
或一次真实观测支撑，命令与输出照实抄，不可达的环境与未执行项显式写明。模板见
`templates/docs/changes/_template/verification.md`，其中 `## 部署验收` 一节只适用于
实际部署或迁移的变更，不部署时整节删除而不是保留标题填「无」。

### 模板是 vendored 副本：改动必须由上游广播

`templates/docs/changes/_template/` 是合同源，每个接入项目在 `docs/changes/_template/`
里持有一份**逐字节相同的副本**，`aisoft-project-check.sh` 的 `change-templates` 查的就是
这个相等关系。对齐检查里只有它的判据横跨两个仓库，因此也只有它会**因为上游前进而
自发变红**，与下游是否有任何提交无关。版本与持有者这样声明：

| 要回答的问题 | 声明位置 |
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

不带参数运行是只读的现状核对，可随时重跑：

```bash
bash codex/tools/change-template-sync.sh
```

它的 `current` / `stale` / `missing` 取自**本机 checkout 的工作树**，不是该仓库 `main` 的
状态；checkout 停在别的分支时会在行尾标注。`unverified` 表示本机读不到那个 checkout，
不表示已同步。

**明确不做的事：不在任何下游项目引入阻塞式 required check。** 下游 CI 要跑这条比对就得
每个 PR 去 clone 平台仓，等于把上游演进变成下游全部在途 PR 的阻塞，而这条 GAP 的修复代价
只是一次复制覆盖。约束由 `change-template-sync.json` 的 `downstream_required_check: forbidden`
与 smoke 一起钉住。

**版本化使用发布包。** change 模板四件套连同使用合同、项目指针与技能一起组成
`usage/bundle.json` 声明的使用发布包。项目在 `.aisoft/platform-usage.lock.json` pin 版本后，
`change-templates` 与 `pointer-sections` 按 pin 版本记录的摘要核对，平台前进不再让它自发变红；
没有 lock 的项目仍对照最新版本。改动任何发布包成员的平台变更必须在同一次变更里运行
`bash codex/tools/usage-bundle.sh --release <新版本> --today <日期> --compatibility <级别> --notes <一句话>`，否则 smoke 的 `--verify` 变红；
`origin/main` 上已发布的版本不可改。

**会话工具随发布包分发（#402）。** 发布包另带项目内会话工具 `.aisoft/bin/aisoft` 与 `.aisoft/lib/`
（平台仓同源入口 `codex/tools/aisoft`），归入核对项 `tool-provenance`：项目会话的文档检查、判级投影、
终态与对齐检查都经 `aisoft <子命令>`，不再需要平台检出。被工具包收录的平台文件（`usage/bundle.json`
里 `check: tool-provenance` 的成员，含 `aisoft_loop`、被包装的三个工具与 architecture 校验器）因此也是
发布包成员，改它们同样要发新版本。`--release` 从 #402 起必须带 `--compatibility patch|minor|major` 与
一句 `--notes`；pin 落后的项目在落后区间含 `major` 时 `platform-pin` 记 GAP，否则只 NOTE。采用新版本由
平台维护者用 `usage-bundle.sh --adopt <项目 change worktree>` 生成改动，经项目自己的 Issue 与唯一 PR 合入。

<a id="canonical-模板的精确-git-scope-合同360"></a>

### Canonical 模板的精确 Git scope 合同

`docs/changes/_template/summary.md`、`docs/changes/_template/spec.md`、
`docs/changes/_template/plan.md`、`docs/changes/_template/verification.md` 是四个共享 vendored
资源身份，与另一 Issue 的 `docs/changes/N-short-description/` 文档区分。
平台原件仍在 `templates/docs/changes/_template/`，不自动获得这个消费者例外。

只有 canonical access/governance 绑定的已知目标仓库为合法 holder
（复用 `RepositoryContract.vendors_change_templates` 及未声明取 true 的规则），并且
exact committed mapped summary/spec 的 issue、branch、status 合法、`git_scope` 明确逐项列出
目标资源时，才允许相应模板路径。holder 或模板目录存在本身不授权任何文件；未列出的其余模板
不得隐含加入。summary 仅接受 `approved` 或同仓合法 `pr-open`；spec 只核对 issue 与 branch 绑定，不读 `status`（#408）。

reader、会话工具与 broker 共用同一资源分类与有限项目/holder 上下文，不另建 policy 框架、动态白名单、
manifest schema 或 typed operation。上下文不得来自候选项目的伪 manifest 或任意 caller override；
复用现有 canonical 来源、owner 与 source/installed 一致性检查。
只允许四个精确路径的普通模板文件；继续拒绝 other-Issue docs、任意子目录、未批模板、
路径穿越/别名、symlink/gitlink、非法类型或删除/越界 rename。

`git_history_paths` 同样受资源分类和可达 exact history anchor 限制，逐提交完整 delta 检查保留；
不能靠净 diff、add→revert、缩小实际 scope 或历史列表漂白越界内容。R0/R/M/H 祖先、标准
`[Issue tip,main]` 整合与 tree 验证、ordinary single-ref FF、固定 guard、no-op 重验、required CI 与唯一
manual PR 第二确认都保持不变。并发 owner/HEAD/remote/main/输入来源漂移时停止并保全证据。source 合并、平台工具真实安装与项目采用分别验收、分别授权。

## 4. 平台三维标签与 Matt triage

每个 Issue 的标签分为三个正交维度：

| 维度 | 标签 | 语义 |
|---|---|---|
| 类型 | `type/bugfix`、`type/feature`、`type/docs`、`type/test`、`type/refactor`、`type/maintenance`、`type/platform`、`type/security`、`type/reliability`、`type/data` | 变更是什么；每个 Issue 最多一个主要类型 |
| 复杂度 | `complexity/small`、`complexity/complex` | AI 判定需要哪条流程；互斥，无法判定时都不写 |
| 流程状态 | `needs-analysis`、`awaiting-triage`、`spec-drafting`、`spec-review`、`approved`、`pr-open`、`completed`、`deployed` | Issue 当前阶段 |

类型的默认关系是：`type/bugfix`、`type/docs`、`type/test`、不改变外部行为的 `type/refactor` 是 small 候选；`type/feature` 和改变平台行为或治理合同的 `type/platform` 强制 complex；`type/maintenance` 由 AI 按实际合同影响判定。另外三个类型按同一套强制规则判定：

| 类型 | 判定证据 | 复杂度默认 |
|---|---|---|
| `type/security` | 安全缺陷、凭据处理、认证/授权或权限边界变更。证据是变更触及 token/credential 存储与传递、权限模型、broker/CI 的信任边界，或修复可被利用的缺陷 | 强制 complex（AGENTS.md「认证/权限/安全」） |
| `type/data` | 数据模型、schema 或数据迁移变更。证据是变更改动表/字段/索引定义、迁移脚本，或既有数据的读写语义 | 强制 complex（AGENTS.md「schema/数据迁移」） |
| `type/reliability` | 可用性、韧性或故障恢复变更。证据是变更针对超时/重试/降级/健康检查/回滚路径，或修复只在故障态下暴露的行为 | 按 `contract_effect` 判定：恢复既有行为（`restore`/`unchanged`）是 small 候选，`add`/`change` 走 complex |

`type/security` 与 `type/data` 的强制不依赖 analyzer 是否填了对应 `risk_flags`：risk flag 是可能被遗漏的分析输出，类型标签是 Issue 上不可省略的事实，两条路径都强制才没有缝隙。`type/reliability` 刻意不强制——可用性修复常常正是「恢复既有产品行为」，判定权交给 `contract_effect`。

`awaiting-triage` 只表示 AI 无法安全判级、内容冲突或合同不完整，阻止自动路由。`approved` 是合同完整后的运行控制信号，不是 spec 审批闸门，也不授权合并或部署。受控 wrapper 可以在合同完整时自动写入 `approved`，但会话开始实现前必须重新验证合同，不能只信任标签。

Matt triage 另有两个正交维度：category 使用 `triage/bug` 或 `triage/enhancement`，state 使用 `triage/needs-triage`、`triage/needs-info`、`triage/ready-for-agent`、`triage/ready-for-human`、`triage/wontfix`。每个已 triage Issue 恰好一个 category 和一个 state。`triage/ready-for-agent` 只允许 Agent 处理下一阶段，永远不替代 `approved`；`triage/wontfix` 关闭 Issue，但不得写入 `completed` 或 `deployed`。所有标签 mutation 通过同一个 projector，更新一个维度时保留其他维度和非受管标签。

## 5. 小变更路径

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/small + approved（合同完整）
  → 会话实现与验证
  → AWAITING_PR_CONFIRMATION
  → 人确认提交唯一最终 PR
  → final PR + CI repair
  → READY_FOR_REVIEW → 人工合并
  → 部署另行授权
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
  → 会话按 Txx 实现与验证
  → AWAITING_PR_CONFIRMATION
  → 人确认提交唯一最终 PR
  → final PR + CI → READY_FOR_REVIEW
  → 人工合并
  → 部署另行授权
```

统一路由合同：

```text
Issue + needs-analysis
  → analyzer identifies type and contract_effect
  → forced-risk and explicit-label checks
  → complexity/small + approved, or complexity/complex + spec-drafting
  → unresolved input: awaiting-triage with no complexity label
```

### 6.1 服务账号 PAT 轮换

**scope 合同变更 = 必须轮换受影响的 PAT。** 合并 scope 声明、重装代码和 Secret 轮换是三份不同证据；
source/local/CI PASS 或 Issue closed/completed 不证明凭据已更新。先证明 exact scope 合同已合并，
并逐台核对安装字节，再在独立 Secret 授权下轮换；真实 identity/scope/audit 读回与第二次 no-op
是现场验收，未运行一律 `NOT RUN`。

轮换只处理 canonical manifests 已管理的 non-site-admin 服务账号，保持账号、协作者、分支保护和其它项目
身份不变，入口是 operator-only typed broker operation `gitea.credential.rotate`，授权 grant 独立于 project
agent 与 manager PAT。缺授权、身份/版本/marker/路径不符或未知 schema 时零 Secret mutation；不能用环境变量
自行授予权限，不能 fallback 到 admin HTTP 凭据、通用 SQL、任意账号/路径/shell 或更宽身份。目标与 grant 的
绑定、固定 Mac canonical store（manifest `site.credential_root_mac`）与 VM helper、事务顺序和恢复表都在
[06 §4.1](06-运维手册与踩坑集.md)，轮换周期见 `06` §4。

治理合同变更与 runtime 实施分阶段：治理步骤单独 commit 后停止，fresh run 重读批准的合同后再改 runtime。
启动确认只授权合同内源码工作，不授予 PR 提交、merge、安装或实际 Secret 操作权限。

## 7. 最终 PR、提交确认与 merge policy

PR 必须：

- body 恰有一行 `Closes #N`，不能额外关闭其他 Issue。
- head 精确为 `change/N-short-description`，并链接 `docs/changes/N-short-description/` 中同 slug 的 summary 与要求文档。
- 说明验收标准与测试证据。
- 说明迁移、部署和回滚影响（若适用）。
- 通过受保护 `main` 要求的 `CI / test (pull_request)`。

PR 合并是唯一交付硬闸门，只由人合并；会话、协调者和 CI 都不得合并 PR。

提交前 handoff 固定包含 Issue、branch、真实验证、判级读回和未执行项。确认允许合同内 CI 修复，
required CI 全绿后停在 `READY_FOR_REVIEW`；不授权部署。确认绑定 Issue/branch，不绑定当时 SHA。

### 交叉审核（平台仓 complex，ADR 0001 D6）

平台仓的 complex 变更在进入确认点 2 之前，由未参与实现的另一方提供者对候选 head 做一次只读独立审查。
**实现方 ≠ 审查方**：当前默认 Claude 实现、Codex 只读审查（负责人 2026-10-20 决定，#408 确认）；改由 Codex 实现的批次就由
Claude 审。审查方只读、不写 worktree，按 spec 的验收标准与本次 diff 给出 PASS 或 FAIL 与发现清单；实现方修复 FAIL 项后对新
head 重审，直到 PASS 或升级给人。这一步不增加人的确认点，也不替代 required CI 与人的合并；项目仓不适用本节（项目使用层按自己的合同）。

**记录**：每轮一行，写进该 Issue 映射 `verification-*` 的固定节 `## 交叉审查`，表头
`| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |`，`exact head` 写 40 位 SHA。同一批在
`docs/governance/review-evidence-index.md` 追加一行（批次、Issue、实现方、审查方、各轮 head 与结论、来源），在本批自己的
PR 里写，不等合并。确认点 2 的候选带一行交叉审查结论。

### 治理表回写（平台仓）

平台批次在 `docs/governance/remediation-roadmap.md` 有一行，或要在 `docs/governance/platform-e2e-acceptance.md` 追加、补全一行时，
在本批自己的 PR 里把这些行写成合并后的状态，不留给下一批顺手改：路线图写 `已完成（#N，发布包 X）`（不发版本就省略版本，PR 编号与
合并 SHA 可在后续批次补），E2E 行写本批已经拿到的读回。行与改动同一次 merge 进入 `main`，PR 不合并时行也不会出现；开工时可以先写
`进行中（#N）`。

确认点 2 之前核对这些行与本批事实一致；与并行批次集成后版本号顺延的，同步改行里的版本。收尾时读回 `origin/main` 上这些行，不符
（例如表格冲突时被另一侧覆盖）就写进收尾报告并开 Issue 修正。在项目仓发生、不属于任何平台批次的事件（部署链、恢复演练、采用后的
main 读回），由把它明确写进合同范围的平台批次追加或补全。表格状态由会话按读回手写，不由工具生成。

## 8. 升级给人的条件

会话只有在合同冲突、必须扩范围、破坏性迁移、安全/权限决策、缺凭据或外部服务、同一根因连续失败三次、验证不可靠或达到预算上限时才停止并请求人决定。普通编译、测试、构建和范围内 review 失败由会话自主处理。

## 9. 证据边界

- 标签集合：platform 维度 20 个（10 `type/*`、2 `complexity/*`、8 生命周期），Matt 另加 7 个 namespaced `triage/*`；准确集合以 `codex/config/gitea-labels.json` 的 `canonical` 为准。外部状态可能漂移，部署到每个仓库前必须用 broker `gitea.labels.provision` 同步并读回。
- 旧 Issue 与历史文档不重命名；新 writer 只产生语义 basename，并要求目录、branch、worktree 与同一 slug 一致。
- `AWAITING_PR_CONFIRMATION` 与 `READY_FOR_REVIEW` 是会话流程的两个持久状态；VM 上没有无人值守的执行引擎（ADR 0002）。
- source 合并、本机安装、项目采用与现场运行是各自独立的证据层，不能互相推断。

## 10. 依赖 Issue

summary 可用可选字段 `depends_on` 声明本仓 Issue 编号或下述仓库限定引用；缺省或 `[]`
表示没有结构化依赖。裸数字没有外仓身份，不得把外仓编号填作本仓依赖，也不得从标题或正文猜仓库。
依赖是 PR 就绪门，不改变分支或 CI：当前 PR 的 CI 通过后，会话核对全部依赖 Issue 必须同时为
closed 且带有 `completed` 或 `deployed` 生命周期终态，才能进入 `READY_FOR_REVIEW` 等人合并。
否则停在等待依赖，只重查 CI 与依赖，不创建第二个 PR。

### 跨仓依赖引用

- 整数及数字 scalar 只表示本仓；严格的 `owner/repo#N` scalar 表示外仓，
  仅支持同一 manifest-fixed Gitea host。URL、object、任意 host/owner/repo 与路径输入不支持。
- 目标必须精确命中 canonical manifest 与 source 项目的 `dependency_read_targets`，
  缺省只允许本仓。typed dependency read 只接受 reference，通过该映射后才构造 request；
  `gitea.issue.read(number)` 不扩参数。
- 外仓 GET 在 broker 内使用 manager-audit 只读路由，project-agent
  credential 不得用于外仓；无 admin、mutation-token 或 direct-client fallback，不扩 ACL。
- canonical identity 为 repository identity 与 Issue number。本仓整数/限定形式重合须报重复，
  自依赖按完整身份判定；外仓同号不是自依赖。本仓同号终态不能满足外仓前置。
- 会话与终态工具共用受控读取与终态规则，返回仅包含目标身份、编号、state、
  labels 和 reference；核身份并拒绝 PR。越界/schema 错误停 `NEEDS_HUMAN_DECISION`；
  已授权但网络、ACL、404 或响应不可验证停 `BLOCKED_EXTERNAL`。
- 依赖引用在 Issue 正文、summary 与 PR 展示中保留仓库身份；只在全部依赖真实终态时
  才通过就绪门。

已安装 runtime 不认 qualified 输入时拒绝，不能降成数字或删依赖求绿；安装、凭据、ACL 与 live apply 各自独立授权。

## 11. 合批关闭与交付终态

合批 PR 可在 merge message body 中逐行列出多个 `Closes #N`。部署成功后的确定性
工具必须处理全部编号并去重，不能只从 subject 猜一个 Issue。更新标签时必须保留
type、complexity 和非生命周期标签。最终 PR 已合并、且没有一次必然到来的部署会认领它时
使用 `completed`；确定性部署与验证成功后使用 `deployed`，它比 `completed` 强，会覆盖
`completed`（反向降级是人的决定）。两者互斥，都不授权合并；Gitea `Closed` 本身
也不证明部署成功。

### 谁推进 `completed`

`deployed` 由应用部署链路在健康检查成功后回写（`02` §9）。会话在人确认 merge 后
执行终态 plan/apply：先验证 exact merge，再用 pinned Issue 编号调用 `codex/tools/mark-completed-issues.sh`：

```bash
codex/tools/mark-completed-issues.sh --range 'origin/main~5..origin/main'   # 读计划
codex/tools/mark-completed-issues.sh --apply <pinned 编号>                  # 用计划回给的编号写入
# 在别的项目仓上运行时目标由 checkout 判定，判定不出才需要显式 --project：
codex/tools/mark-completed-issues.sh --repo <项目 checkout> --range '...'
```

默认只输出逐 Issue 的判定计划、不做任何写入；确定性验证计划瞄准 exact merge 后加 `--apply` 才经
broker `gitea.issue.labels.set` 写入。已经是 `deployed` 的 Issue 不会被降级为
`completed`。终态、文档、cleanup 与会话归档在 merge 后按确定性流程完成，不再增加人工确认点。

### 范围锚不能是会移动的 ref

`origin/main~N` 在**工具启动那一刻**求值，不是在 `git.fetch.main` 那一刻，也不是在人
点头那一刻。于是有两个窗口，任何一个里 `origin/main` 前进一次，范围就整体后移，
写到别人刚合并的 Issue 上而不报错：

| 窗口 | 两端 | 关窗做法 |
|---|---|---|
| W1 | `git.fetch.main` → 跑计划 | 计划第一行 `{"selector":"range","range":<字面量>,"commits":[{"commit":<sha>,"subject":…,"issues":[N,…]}],"pinned":"N …"}`，逐 Issue 行另带 `commit`；核对 `commits` 就是自己那次 merge |
| W2 | 跑计划 → 跑 `--apply` | `--apply` 用计划回给的 `pinned`（Issue 编号）重跑，不再传 `--range` |

范围命中 0 个 commit、或命中的 commit 一个 Issue 都不提，各自报独立的错误。
`codex/tools/apply-classification-labels.sh` 的 `--range` 面同样处置，包括 `--verify`：
一次被滑走的 `--verify` 会读回别人的 Issue 并报 `projected` 退 0。**`--verify N` 一律用编号。**

`codex/tools/mark-deployed-issues.sh` **不接受 `--range`**：它是部署链路的 hook，运行在部署已经
checkout 的那个 commit 上，锚是 `HEAD` 或显式的 `MERGE_MESSAGE_FILE`；它的姿态是任何缺失前提都
warn + exit 0、绝不让已成功的部署失败，那里没有人读计划。该事实由 `codex/tests/test-mark-deployed-issues.sh` 钉住。

判定是一个**合取**，两个条件都取自仓库证据，都不接受人工传入的终态判断。下表只适用于已经通过
文档声明与实际文件校验的合同：工具通过 §3 的共享 resolver 取得规范化 required_docs，缺失的
verification 不能作为“含 verification”的有效合同进入此表。

| 该 Issue 映射 summary 的 `required_docs` 含 `verification` | 该项目的 `deployment_lifecycle` | 终态 |
|---|---|---|
| 否 | 任意 | `completed` |
| 是 | `application-deploy` | 跳过并给出 `requires-deployment`，等部署链路写 `deployed` |
| 是 | `application-deploy-selective`（**缺省**） | `completed`，`reason` 记为 `deployment-not-guaranteed` |
| 是 | `none` | `completed`，`reason` 记为 `no-deployment-chain` |

两个条件回答两个不同的问题：`required_docs` 说的是「这次变更欠不欠一份验证记录」，
`deployment_lifecycle` 说的是「这个仓库的部署链路会不会覆盖到本次 merge」。

### 「跳过等待」必须有一个会到来的写入者

跳过是把 Issue 停在原地等 `deployed`，所以要成立的是「会有一次部署覆盖**本次 merge**」。
`application-deploy` 的含义因此是「**每一次 merge 都会被这条链路部署**」，只有它保留「跳过等待」；
不保证覆盖每次 merge 的仓库用 `application-deploy-selective`，终态当场写 `completed`。
**缺省取后者，因为两个方向的错并不对称**：

- 写早了会被纠正：`mark-deployed-issues.sh` 剥掉 Issue 的整个生命周期维度再写 `deployed`，
  所以「先 `completed`、后来真部署了」的终点仍然是 `deployed`。
- 写早了也盖不掉真部署：broker 的 `_set_issue_lifecycle` 对「已经 `deployed` 却要写
  `completed`」直接 `REQUEST_DENIED`。
- 漏写没人纠正：没有任何组件处在能观察到合并的位置上。

**声明 `application-deploy` 等于承诺这条链路覆盖每一次 merge**——不确定就不要声明，缺省不会落到它上面。

### 哪些仓库的部署链路覆盖每一次 merge

由 `codex/config/gitea-governance.json` 的仓库条目声明一次，是仓库属性，不是每次变更重新回答：

```json
{ "name": "aisoft-platform", "...": "...", "deployment_lifecycle": "none" }
```

- `application-deploy`：`02` §9 的应用部署链路存在，**且每一次 merge 都会被它部署**，在健康检查
  成功后写 `deployed`。
- `application-deploy-selective`：链路存在，但只覆盖一部分 merge。**未声明时取此值**。
- `none`：没有那条链路，`deployed` 不可达，`completed` 是唯一终态。平台仓声明此值。

各仓库的实际取值以 manifest 为准。工具读到这三个取值以外的任何值都报错退出，不落进任何一档。

`deployment_lifecycle` 只影响合并后的终态记账：它不触发也不抑制任何部署，不改分支保护与必需 CI，
也不改变 `required_docs` 该不该含 `verification`。manifest 读不到或查不到条目时，
工具报错退出而不是静默跳过；只是**没有声明该键**不属此列，按缺省处理。

`--project` 收的是 `codex/config/host-access-broker.json` 里的 **project id**（小写短横线形式），
不是仓库名。governance manifest 按**仓库名**索引，仓库名由 project id 反查得到、不由调用方提供；
两侧任一查不到都报错退出，消息各自指名是哪一份 manifest 少了哪个键。

> 改了 `codex/config/gitea-governance.json` 之后，扁平安装
> （`/usr/local/share/aisoft/gitea-governance.json`）要重装才跟上。工具优先读仓库布局下的
> `codex/config/gitea-governance.json`，所以从平台 checkout 跑收尾时合并即生效。

### 谁投影 `type/*` 与 `complexity/*`

`codex/tools/apply-classification-labels.sh` 在**判级文档写好之后**、合并之前投影两个维度
（会话内的位置见 `aisoft-platform` 技能的会话标准动作）：

```bash
codex/tools/apply-classification-labels.sh N
codex/tools/apply-classification-labels.sh --apply N
codex/tools/apply-classification-labels.sh --verify N
```

与 `mark-completed-issues.sh` 同姿态：默认只输出逐 Issue 的判定计划、不做任何写入；
加 `--apply` 才经 broker `gitea.issue.labels.classify` 写入。两个维度的取值取自该
Issue 映射 summary 的 `change_type` 与 `effective_complexity`，**不接受人工传入标签**；
summary 没有 `effective_complexity`（needs-human-decision 形态）时跳过并说明，不臆造复杂度。
broker 侧再对已安装的 label manifest 逐维校验，retired 的 `complexity/standard` 写不进去。写入
替换的是这两个维度，生命周期标签、`triage/*` 与 `area/`、`priority/` 等项目扩展标签原样保留。

**已关闭的 Issue 不补写**，工具直接跳过且不提供 override 开关：判级事实已经在合并后的 summary 里
且不可变；改写已经收尾的记录与「retired label 只报告不移除」「`deployed` 不降级为 `completed`」是同一条姿态。

> 新增 typed 操作后 broker 必须在 Mac 与 VM 两台重装才生效，
> 未重装时新操作返回 `REQUEST_DENIED / not allowlisted`（`06` 踩坑 20）。

#### 窗口在合并时关闭

「已关闭不补写」的直接推论：**判级投影的截止时间就是合并**。`--verify` 读回 Issue 当前标签并与映射
summary 比对，逐 Issue 给出 `projected` / `projection-missing` / `projection-mismatch` /
`projection-window-closed`，只有全部 `projected` 才退 0；读不出证据（文档缺失、判级未决、broker
不可用）一律计为失败。它是只读的（`gitea.issue.read` + `gitea.issue.labels.read`），永不调用写操作，
与 `--apply` 互斥。`projection-window-closed` 刻意**不给 `remedy` 字段**——没有可执行的补救就是结论本身。

会话侧的落点在 `issue-session-flow` 的待合并块：`判级:` 一行必须是这条命令的真实读回，
不是 `projected` 就不进入待合并；收尾时再跑一次，把漏掉的情形显式报出来。

#### 目标仓库由 checkout 判定

`--verify` 只有在**读的是正确那个仓库**时才是闸门。目标项目**由 checkout 判定**：从 `--repo` 的
Git remote URL 反查 host access manifest 的 `projects[]`，得到 `project_id` 与 `repository`（构造方式
与 broker 的 `_expected_git_url` 一致，所有 remote 的 fetch 与 push URL 都参与匹配——有的项目 Gitea
remote 名为 `gitea` 而非 `origin`，见 manifest 的 `git_remote_name`）：

| checkout 能否判定 | 是否传 `--project` | 结果 |
|---|---|---|
| 能 | 否 | 用判定出的项目 |
| 能 | 是且一致 | 用该项目 |
| 能 | 是且不一致 | **报错退出**，不产出任何 Issue 行，不调用 broker |
| 否 | 是 | 用传入的项目（唯一可用证据是操作者的声明） |
| 否 | 否 | **报错退出**，提示传 `--project <project_id>` |

`--project` 是「覆盖」不是「默认」，命名空间只认 broker 的 `project_id`。每一行 JSON 输出带 `project`
与 `repository` 两个字段，指名它在谈论哪个仓库。只有 GitHub remote 而没有 Gitea remote 的 checkout
判定不出项目，必须显式传 `--project`——这是 fail-closed 的预期形态。

broker 因操作表陈旧而拒绝时，工具报 `broker-operation-missing`，detail 写明「这是安装期旧表，
不是权限问题」与两台重装的命令（`06` 踩坑 20）。

#### 已经错过窗口的 Issue：处置结论

**接受缺 `type/*` 与 `complexity/*`，不补写、不改写、不加 override。** 判级事实在合并后的 summary 里、
不可变、可由 `resolve-documents` 定位；为它们破例等同于承认一个 override。`--verify` 只保证**窗口关闭前**
被提醒，不回到过去。要读任一已关闭 Issue 的判级，看它映射的 summary，或直接跑 `--verify N`——
`projection-window-closed` 那一行本身就带着 `change_type` 与 `complexity` 两个值。已知错过窗口的 Issue
列在下方来历表。

## 来历

| Issue | 合并 | 一句话 |
|---|---|---|
| #108 | `314153e` | `type/*` 扩为 10 个（加 security、reliability、data），标签共 27 个 |
| #115 | `2a09bb6` | 会话侧 `mark-completed-issues.sh` 推进 `completed` |
| #134 | `97878f9` | `change_control: development` 阶段：development complex 用 Issue 验收合同与合成 `T01` |
| #142 | `74293d7` | `pr_url` 只写在 summary，由 `backfill-pr-url` 回填 |
| #160、#167、#184 | `933323b`、`770d527`、`d73fee4` | 判级投影工具、合并前 `--verify` 闸门、目标仓库由 checkout 判定 |
| #163、#192 | `208b2bf`、`abcfd18` | 终态合取表与 `deployment_lifecycle` 三档，缺省 selective |
| #138、#146、#148、#163、#387 | — | 合并前漏了判级投影，按「已经错过窗口」处置，不补写 |
| #172、#175 | `fa34944`、`ad4aaeb` | `--project` 收 project id；范围锚改为 pinned 编号 |
| #190、#377 | `5e324ac`、`8fa4458` | 模板 digest 与下游广播；版本化使用发布包 |
| #286 | `4020765` | `depends_on` 支持 manifest 限定的跨仓引用 |
| #289 | `16beee0` | `required_docs` 声明与实际文件共用一个校验结果 |
| #298、#327 | `f6e2e50`、`1a86a00` | change worktree 单写者归属；broker 普通 FF 整合与历史重写拒绝 |
| #316 | `dc9aa46` | 服务账号 PAT 轮换合同与 `gitea.credential.rotate` |
| #360 | `06afadf` | canonical 模板的精确 Git scope 例外 |
| #391、#395、#397 | `08be6f4`、`86821cf`、`fb9d8c5` | routine 合并与 VM 执行引擎退出（ADR 0002）；路由卡；routine manifest 字段删除 |
| #403 | — | 本册改为现行合同体，叙事移入本表 |
| #408 | — | approval 只写 summary；`aisoft open-pr` 一步建 PR 与回填；交叉审查固定表与审查证据索引 |
| #412 | — | 平台批次在本批 PR 里回写路线图与 E2E 表的行，收尾读回 `origin/main` |
