# 03 · Issue / Spec / Plan 与单闸门开发流程

> v3 当前文档契约（更新 2026-08-26）。Issue 是所有工作的主键；小变更允许从明确的 Issue 直接进入 Development Loop，production complex 必须先完成 spec/plan，development complex 使用 Issue 正文中的验收合同。最终 PR merge 是唯一交付硬闸门；manual 集合人工合并，只有显式 opt-in 的 routine small 可在提交确认与最终硬门后受控合并。既有固定数字路径只作证据驱动的 legacy 兼容。

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

### change worktree 的单写者归属（#298）

**一个 change worktree 的写者是且只是该 Issue 的会话。** 别的会话发现它需要变基、需要修
冲突、需要重跑验收时，只能**通知**那个会话或**交回**给它，不得代劳——哪怕改动本身是对的。

> 🚩 **Red Flag**：「我顺手把别人那个 worktree 变基一下，反正 main 已经前进了」——停。
> 你正在改写一条**不属于你**的证据链：冲突怎么解的没有归属，验收在谁的环境里跑的读者分不
> 出，而错误会跟着对方的 PR 直达 merge 这道唯一交付闸门。**通知，或者交回。**

平台此前只约束了「建」没有约束「进」：`git rebase` / `git commit` / `git checkout` 都是纯
本地操作，根本不经过 broker，因此任何会话都能进入任意 change worktree 改写 HEAD，平台侧零
感知。2026-09-16 NewEMaint #96 实际中招——它核验的是 `327fc06`，push 后从 `gitea.pull.read`
读回的 head 却是 `b576525`，多出 61 行它没读过的内容。

现在有三样东西支撑这条归属：

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

#298 的归属闸门回答「谁可以推」，单独不能保证内容。历史实现允许 owner 推送被改写的 HEAD，
再从回执检出；#327 覆盖该发布口径：已发表历史重写必须在远端写入前拒绝，不能靠事后回执追认。
owner 标记与每次 SHA 核对仍为必要步骤；broker 还须独立复核 original/current remote tip 的祖先链、
提交来源、完整 DAG/tree、合同范围和 fresh main。旧 installed 行为没有由文档更新自动改变，
缺少新能力时停止，不能调用 leased rewrite。

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

`BASE_BRANCH_STALE` 按 #327 区分发表前后：未发表且尚未作为验证锚的本地历史，可由本 Issue
owner 在自身 worktree 调整；已发表分支只能保留原 tip 的祖先关系、追加受控 main 整合。
provider 仍不得创建 merge commit；外层 Controller 只有在批准合同内才可构造精确
`[已核验 Issue 第一父链末端, fresh manifest main]`，只支持可复算的无冲突合并。
broker 独立验证 original/current remote tip→候选、fresh main→候选、完整来源/tree/scope，
并绑定传输时 exact remote tip，随后只普通 FF 发布；任意 merge、冲突解决、force/lease-force
或 fallback 均拒绝。整合不改变 owner，不通过重新 claim 掩盖第三方改写。

历史 #298 AC-6 的已发表 rebase-重推，以及 AC-5 的“owner 推送他人改写后才检出”，
和 #136 的 lease 解法，均由上述 #327 治理合同覆盖。历史文档保留追踪；单 writer、错误码、
逐次 `pushed_head` 核对不取消。#327 runtime/installed 未验收前不能把新合同当已可执行能力。
其 first PR 按映射 spec 的负责人本人 UI 自举卡；只有一个 exact branch/manual PR，
不安装 unmerged broker、不 direct Git/API、不代操作 #289/#319，也不阻塞合法人工更新。

**#327 T04 可信证据治理合同（尚未实现/启用）**：trusted-critical Controller 的冻结上下文、受控执行/观察、限定整合和记录由固定 installed verification authority 保管；authority 实际 EUID=0，仅执行已审计平台代码。provider/项目 verifier 以登记非 root UID/GID 在真实 OS 隔离内运行，不能访问 protected ledger、broker credential 或控制入口；只降低 UID、root-owned 文件或 peer UID 不证明程序/批准身份。缺隔离、可信工具链或记录均 fail closed/GAP，不用环境、source wrapper 或身份 fallback。

人类合同/最终 PR 确认须经另获 exact 授权的非 Agent operator 登记为 protected grant/PR授权；local approved、owner marker、commit subject 和 caller PASS 均不是可信根。grant 冻结 exact tuple、scope/内容目的、graph、required verifier、source/policy pin 和 R0，记录由 authority 自己观察执行并逐对象验证；已有/未知或跨 Issue 对象须明确 adoption，来源只指已验证/采用对象，不声称物理创作分支。broker 仍独立重算完整 DAG/tree/delta，核对 sealed checkpoint、PR授权与 strict remote tip，再普通 FF；不重置 R0 或弱化原 per-push/readback 门。

新 public 操作仅 `git.change.begin(branch,ticket)`、`git.change.verify(branch,ticket,sha)`；`git.push.change(branch)` 参数不变。无 public approve/merge、自由 command/path/socket/UID/PASS 入口。代码/config/service 的 exact source 范围及固定路径以 #327 映射 spec 为准，默认 disabled、UID/GID 空、provider none、服务描述 inert。原治理 T04 只应用映射文本、验证/local commit 后 STOP；后续 fresh run 重读才实施 T02。source 合并后的 I01 文件安装与 I02 每主机 exact 权限绑定、注册/启停、真实隔离/FF/rollback 各依独立 operator 卡；不继承 T01、路线选择或 #316，不自动 provision/启动。AC-7/AC-9/AC-10/AC-11 未闭合保持实际未完成，不把 mock/source/自动 closed 当 installed/live 验收。

**#327 T05 资源与工具链治理合同（source 已批准；installed/live 未验收）**：critical 入口由固定 installed native bootstrap 在任何 Python 平台模块导入前核验完整 toolchain closure 与角色绑定；范围包括 interpreter/stdlib/late import/native loader/library/Git transport/helper/OS delegate、OS alias 与 Mac dyld shared cache/subcache。完整目录/build dependency inventory及静态/显式动态解析为基线，loaded-module集合或一次trace不能证明完整；未知依赖/漂移/未注册一律GAP。严格清env/FD、canonical regular最终程序、无source/PATH/未知shim fallback；bootstrap自身OS loader为冻结TCB，不声称main前无库执行。exact source、固定incoming path/FD、build/descriptor与默认disabled空host registry遵映射spec，不自动安装新工具链或以root构建项目。

Mac scratch固定64 MiB UDIF/UDRW/HFSX无分区模板，root Git暂存256 MiB；模板create仅未来exact I02 operator，runtime不格式化任意设备。真实ownership/容量/nodev/nosuid/noexec/nobrowse与镜像→device→mount映射须读回，单scratch/单readonly input、最多两个对象卷；CONTEXT/temp/复制双份窗口全部创建前预留并计入8 GiB保留预算、64 MiB平台元数据上限，input≤256 MiB/4096entries/depth16。Linux同等scratch/对象tmpfs上限及inode/namespace隔离须真实验收。每verifier新own-lease，descendant未退出、busy、device复用、未知映射、崩溃/断电均保留预算/证据并quarantine；不force/resize/hosttmp fallback/盲重试/递归清理user卷/自动删除历史。只依protected exact FD清单和确认own detach后的readback回收；R0不重pin。Mac noexec不支持scratch中新产native binary执行，能力不足明确GAP，不泛称SDK/build可用。

public policy仍`change-verification/v1`四key、public仅begin/verify且push仅branch；private grant/record/operator为v2并绑定closure/resource/lease digest，v1只作历史只读，不自动迁移/清空。publish先持久pending再transport，断线/重启/重入只poll既有attempt、不重复推送；真实possible-write/已落地H保留，不能把传输失败写为零mutation。T05仅原14治理文本+四角色（18文件）独立应用/验证/local commit后STOP，后续fresh重读才继续既有T02 WIP；不混runtime。I01只惰性文件安装/hash-mode-owner、installer no-op与文件失败rollback；I02每主机exact卡独立批准registry/模板/own-device/服务启停/真实权限、FF/publish no-op/reject与运行资源rollback，AC-7要求不减。默认none/disabled，不provision账户/凭据/grant/全局SDK/provider。AC-7/9/10/11未闭合不把source/mock/自动closed当实际完成，不提前cleanup/归档，不继承#316或路线选择权限。

### 衍生 Issue 的正文与认领

会话中途发现的新问题一律开新 Issue，不扩本次范围。作者会话必须在**正文**写清四件事：

- 来源：哪个 Issue 的哪次会话发现的；
- 目标项目：这条 Issue 应该在哪个仓库解决；
- 可测验收标准：至少一条可观察、可验证的结果；
- 已知依赖：阻塞它的 Issue 编号，没有就写「无」。

依赖必须落在正文上。会话上下文会被压缩，Issue 不会——只活在上下文里的顺序关系一定会丢。

立案时 `gitea.issue.create` 在创建的同一次写入里带上流程入口标签，取值是 `needs-analysis`
或显式指定的 `triage/needs-triage`。Issue 因此一建出来就站在流程入口上，而不是停在一个没人
看的收件箱里等人手工盘点。

**衍生 Issue 的默认认领方是调度会话**：它按「开放 Issue 清扫」逐条判定、派单，或汇总成需裁决
项交给人。没有调度会话时，作者会话在收尾时自己开 Issue 并派卡片，不把它留给下一个偶然路过的人。

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

### 2.1 Routine small merge policy

分类与 merge policy 是两个步骤，不新增 label。只有同时满足以下条件才是 `routine-auto` 候选：

- 最终 fresh 重算仍为 `effective_complexity=small`、`contract_effect=restore|unchanged`；
- 范围局部、可简单 revert、无任何 forced-complex risk，且不是 major、阶段或里程碑完结；
- repository manifest 显式 `routine_auto_merge_enabled=true`，声明独立 routine merger，required contexts 非空；
- 提交 PR 前的人工确认绑定 exact Issue、`change/N-short-description` 与 `routine-auto` policy，并明确允许当前合同内 CI 修复后在最终 head required CI 全绿时受控合并。

功能新增/变化、major、阶段/里程碑完结、安全、数据、共享核心、跨模块/服务、CI、制品、部署、
健康检查、备份、回滚、Agent 与平台治理一律 `manual`。Issue #208 自身为 complex/platform，必须人工
合并。routine hard gate 失败只返回稳定原因并停机，不自动切换到 admin、manager、project agent 或
其他更宽权限路径。

人工确认不绑定当时 SHA，避免范围内 CI repair 形成第三个确认点；merge operation 必须绑定最终 40 位
lowercase head SHA，并在 POST 前按固定顺序 fresh 复核 authorization、summary/Gitea 分类、exact tuple、
唯一开放 PR、open/unmerged、base=`main`、head、live protection/manifest、逐 context CI、reviews、
dependencies 与完整 final diff。任何缺失、漂移或未知 schema 都 fail closed，零 merge POST。

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

### 声明与实际文件共用一个校验结果（#289）

本节同步 #289 已合并的治理合同。T01 独立应用合同后，fresh run 的 T02/T03 已完成 runtime 实施与本地验证；[PR #325](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/325) 已进入稳定 main。下述严格行为和新增命令已在 source 实现，installed/live 仍须按实际安装与项目验收证据确认。

- summary front matter 的 `required_docs` 是文档义务的唯一声明事实源，`documents` 是新格式角色到安全 basename 的唯一路径事实源。共用受限 Python 解析器，拒绝空、未知、重复或混合角色与 legacy 文件名的列表，首项必须为 summary。
- `route.required_docs` 给出阶段与复杂度的最低合同要求；Loop 检查声明满足这些要求，不得用路由生成的列表替换声明或丢掉额外角色。development 不强制 spec/plan，production complex 仍必须有 spec/plan；任何路由都不能让已声明 verification 的文件义务消失。
- 新格式 `documents` 的每个显式映射均须指向本 Issue 目录内可读取的普通文件，且通过既有角色、slug、日期、front matter 与路径边界校验；即使角色不在 required_docs 里也一样。缺文件或符号链接逃逸必须报错，诊断包含 Issue/change、role 与真实 basename。required_docs 的每一项必须有映射和实际文件。
- 公共 `resolve-documents N --repo <checkout>` 成功时保留角色到 basename 的 JSON 形状，但必须拒绝不存在的显式映射。新增只读 `resolve-required-documents N --repo <checkout>` 返回 `required_docs`（规范化语义角色数组）和 `documents`（角色映射）。`check-change-documents`、Loop 与 `mark-completed-issues.sh` 共用同一解析和校验结果；终态工具不再用 awk 独立解析原文，resolver 或 JSON 失败不能回退为成功。
- legacy 固定映射是历史推断；未声明的可选 spec/plan/verification 不要求生成。显式 required_docs 中的历史 basename 必须有实际文件，并规范化为相应语义角色（如 `03-verification.md` → `verification`）。缺 required_docs 报明确 GAP；不新增 legacy 开关，不批量重命名或改写历史文档。
- 合同草稿首次写入使用受限 publisher：`publish-spec`/`publish-plan` 可在 open Issue 的 exact branch 上，通过内部声明解析首次创建自己映射的目标，继续执行路径、日期、front matter 与 Ticket graph 硬门。该准备入口不向 reader 暴露通用 skip-existence 参数；草稿尚未齐全时，严格 resolver、文档检查、Loop 与终态检查仍须拒绝交付。
- `mark-completed-issues.sh` 的 dry-run 遇无效声明或缺文件时输出可搜索的 skip 原因和诊断，apply 对该 Issue 零 broker 写入。合法合同时，再按 §11 的独立 deployment_lifecycle 判终态。文件存在与可解析不证明 verification 内每项现场动作已执行。

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
  → AWAITING_PR_CONFIRMATION
  → 人确认提交唯一最终 PR（manual 或 eligible routine-auto）
  → final PR + CI repair
  → manual: READY_FOR_REVIEW → 人工合并
  → routine-auto: final-head hard gates → AUTO_MERGED
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
  → Development Loop
  → AWAITING_PR_CONFIRMATION（Policy: manual）
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

### 6.1 服务账号 PAT 轮换与治理阶段（#316）

**scope 合同变更 = 必须轮换受影响的 PAT。** 合并 scope 声明、重装代码和 Secret 轮换是三份不同证据；
source/local/CI PASS 或 Issue closed/completed 不证明凭据已更新。先证明 exact scope 合同已合并，
并逐台核对安装字节，再在独立 Secret 授权下轮换；真实 identity/scope/audit 读回与第二次 no-op
是现场验收，未运行一律 `NOT RUN`。本节是 #316 的已批准治理合同；T02 helper 本地隔离验证已完成，
交易/typed runtime、后续安装与 live 演练尚未实施，不是现行可执行 runbook。

轮换只处理 canonical manifests 已管理的 non-site-admin 服务账号，保持账号、协作者、分支保护、
routine opt-in 和其它项目身份不变。Agent 的 live 入口须经 operator-only typed broker operation
`gitea.credential.rotate`：目标由 manifest 派生，授权 grant 独立于 project agent、manager PAT 与
routine merger，绑定授权 Issue、已合并 source SHA、exact project/token kind、manifest 固定 Mac store、
VM exact helper 和有效期。缺授权、
身份/版本/marker/路径不符或未知 schema 时零 Secret mutation；不能用环境变量自行授予权限，
不能 fallback 到 admin HTTP 凭据、通用 SQL、任意账号/路径/shell 或更宽身份。

#316 的撤销后台固定 Gitea `v1.26.4` token model，由受控 operator 路径以 Gitea service user 运行，
先校验 exact token 的 UID/账号，再精确撤销并读回不存在。不能沿用未经真实验证的 `/api/v1/token`
self-revoke 假设；不得为轮换升级 server、创建密码或扩大 sudoers/provider 权限。helper 构建、
隔离数据库测试和制品 provenance 必须版本化；其安装、operator grant provision 与 live 使用另行授权。

用户已批准方案 A：仅允许 manifest 固定 Mac canonical store
`/Users/benque/Library/Application Support/AISoftPlatform/credentials` 接收轮换候选。journal、旧凭据
隔离区、候选和原子发布均在该 store 同一受保护文件系统；核对 manifest owner、0700 目录/0600 文件，
拒绝 symlink/逃逸。Gitea CLI/helper 在固定 VM 以现有 git service user 执行，Secret 仅经内部受控
stdin/pipe 传递，不进入 Agent/tool 返回、用户可见 stdout/stderr、argv、日志、审计或 VM 普通临时目录。
caller 不得用 env/path/URL 选择 store/helper；ownership markers 缺失拒绝，不擅自补建。

本次单-store 发布不自动更新或清理既有 VM credential 副本；撤销后旧副本不可继续使用，需要消费
它们的 runtime 须各自明确授权处理。Mac typed audit PASS 不能代表全部消费端验收。

事务顺序固定为：preflight/单目标锁 → 隔离旧 canonical 凭据 → 在受保护交易区生成并验证候选 →
精确撤旧并证明拒绝 → 持久保存 provenance → 最后原子发布新 canonical 凭据 → 验证并清理。
canonical 隔离期间目标 broker 身份 fail closed，未完成不能报 rotated/no-op。同一请求重复执行
必须验证 active identity/scope 与完成 marker 后零 mutation；中断恢复沿用已有 journal/候选，
不盲目签发第二个 PAT。旧 PAT 撤销不可逆，撤旧后的发布失败只能恢复保留候选，不能声称恢复旧 PAT；
撤旧前只有仍有效且符合当前 manifest 的旧凭据才可恢复。细节和验收见
[spec](docs/changes/316-service-pat-rotation/spec-service-pat-rotation-261002.md) 与
[06 §4.1](06-运维手册与踩坑集.md#41-服务账号-pat-轮换合同316)。

治理与 runtime 必须分阶段：本票 T01 与方案 A 的 T02A 各只应用 03/06 治理合同和 mapped docs，
作本地原子 commit 后停止本 turn；T02A 后续 fresh run 重新读取批准的 spec、plan 与治理合同后，
可沿用本次启动批准实施 T03 broker transport、installer、测试/CI，无需重复启动确认。
启动确认只授权合同内源码工作，不授予 PR 提交、merge、后续安装
或实际 Secret 操作权限。AC-2 未真实达成时不声称 #316 已真正解决，不进行完成归档。

## 7. 最终 PR、提交确认与 merge policy

PR 必须：

- body 恰有一行 `Closes #N`，不能额外关闭其他 Issue。
- head 精确为 `change/N-short-description`，并链接 `docs/changes/N-short-description/` 中同 slug 的 summary 与要求文档。
- 说明验收标准与测试证据。
- 说明迁移、部署和回滚影响（若适用）。
- 通过受保护 `main` 要求的 `CI / test (pull_request)`。

PR 合并是唯一交付硬闸门。Analyzer、Loop、provider wrapper 和 CI 都不得合并 PR。
manual PR 只由人合并；routine-auto 只能由独立 exact-repository merger 经 broker operation 合并。

提交前 handoff 固定包含 Issue、branch、`manual|routine-auto`、真实验证、判级读回和未执行项。
manual 确认允许合同内 CI 修复，required CI 全绿后停在 `READY_FOR_REVIEW`；不得出现自动合并 marker。
routine 确认必须明确“当前合同内 CI 修复可继续，最终 head 的 required CI 全绿且全部硬门通过后，
允许受控自动合并”。两者都不授权部署。确认绑定 Issue/branch/policy，不绑定当时 SHA；最终 merge
仍必须 pin exact SHA。分类标签不新增 merge-policy 维度。Gitea 1.26.4 没有 merge-only ACL；routine
merger 是 exact-repo Write identity，但 credential 由 broker 独占，且该 identity 不在 main push/force
allowlist。普通 Git 禁令由 typed operation、manifest/final-head gates 与 zero fallback 共同保证。

## 8. 升级给人的条件

Loop 只有在合同冲突、必须扩范围、破坏性迁移、安全/权限决策、缺凭据或外部服务、同一根因连续失败三次、验证不可靠或达到预算上限时才停止并请求人决定。普通编译、测试、构建和范围内 review 失败由 Loop 自主处理。

## 9. 当前实施状态

- Issue #57/#60 已把文档 resolver、writer、Matt triage projector、frontier ticket、Agent commit 后置校验、固定 upstream snapshot 与根级路由合并进 source；Issue #75 又统一了 readable branch/directory/worktree/PR 绑定。
- platform canonical taxonomy 为 20 个（Issue #108 把 `type/*` 扩为 10 个），Matt 另加 7 个 namespaced `triage/*`，source manifest 共 27 个；准确集合以 `codex/config/gitea-labels.json` 的 `canonical` 为准。外部状态可能漂移，部署到每个仓库前必须用 broker `gitea.labels.provision` 同步并读回。
- 旧 Issue 与历史文档不重命名；新 writer 只产生语义 basename，并从 Issue #75 起要求目录、branch、worktree 与同一 slug 一致。
- Provider 默认仍为 `IMPLEMENT_PROVIDER=none`；每个项目必须在独立 profile 完成真实验收后才能启用。
- Issue #208 governance source 定义 `AWAITING_PR_CONFIRMATION`、manual `READY_FOR_REVIEW` 和 routine
  `AUTO_MERGED` 合同；runtime/config/credential/protection/live apply 尚未由本步骤执行。#208 自身固定
  manual，本次治理变更不部署。
## 10. 依赖 Issue

source runtime 的 summary 可用可选字段 `depends_on` 声明本仓 Issue 编号或下述仓库限定引用；缺省或 `[]`
表示没有结构化依赖。裸数字没有外仓身份，不得把外仓编号填作本仓依赖，也不得从标题或正文猜仓库。
依赖同时是 routine hard gate 与 manual PR 就绪门，不改变分支或 CI：
当前 PR 的 CI 通过后，全部依赖 Issue 必须同时为 closed 且带有 `completed` 或
`deployed` 生命周期终态，manual 才能进入 `READY_FOR_REVIEW`，routine 才能 merge。否则保存
`awaiting_dependencies`，后续轮询只重查 CI 与依赖，不再次调用 provider、
不创建第二个 PR，也不自动合并。

### #286 依赖合同（source/local 已验证，installed/live 尚未验收）

本节的 source 实现已按 [映射 spec](docs/changes/286-dependency-references/spec-dependency-references-261002.md)
完成本地双闸门 fixture 验证；不是 installed/live 跨仓功能已生效的证明：

- 旧整数及已支持的数字 scalar 保持只表示本仓；新增严格 `owner/repo#N` scalar，
  仅支持同一 manifest-fixed Gitea host。URL、object、任意 host/owner/repo 与路径输入不支持。
- 目标必须精确命中 canonical manifest 与 source 项目的 `dependency_read_targets`，
  缺省只允许本仓；唯一新增跨仓边为 `sfm-digital-board → aisoft-platform`。
  新 typed dependency read 只接受 reference，通过该映射后才构造 request；既有
  `gitea.issue.read(number)` 不扩参数。source executable manifest 已声明此新字段；installed manifest 仍须独立验收。
- 外仓 GET 在 broker 内使用 manager-audit 只读路由，project-agent/routine merger
  credential 不得用于外仓；无 admin、mutation-token 或 direct-client fallback，不扩 ACL。
- canonical identity 为 repository identity 与 Issue number。本仓整数/限定形式重合须报重复，
  自依赖按完整身份判定；外仓同号不是自依赖。本仓同号终态不能满足外仓前置。
- Controller 与 routine merger 共用受控读取与终态规则，返回仅包含目标身份、编号、state、
  labels 和 reference；核身份并拒绝 PR。越界/schema 错误停 `NEEDS_HUMAN_DECISION`；
  已授权但网络、ACL、404 或响应不可验证停 `BLOCKED_EXTERNAL`，routine 零 merge POST。
- 依赖引用在 Issue 正文、summary、state 与 PR 展示中保留仓库身份；只在全部依赖真实终态时
  才通过既有就绪/merge 门。轮询不重新调用 provider、不创建第二个 PR。

旧 installed runtime 面对 qualified 输入应拒绝，不能降成数字或删依赖求绿。G01 已独立应用
治理合同并停止，fresh run 已完成 source 实现；安装/凭据/ACL/live apply/部署始终独立授权。

## 11. 合批关闭与交付终态

合批 PR 可在 merge message body 中逐行列出多个 `Closes #N`。部署成功后的确定性
工具必须处理全部编号并去重，不能只从 subject 猜一个 Issue。更新标签时必须保留
type、complexity 和非生命周期标签。最终 PR 已合并、且没有一次必然到来的部署会认领它时
使用 `completed`；确定性部署与验证成功后使用 `deployed`，它比 `completed` 强，会覆盖
`completed`（反向降级是人的决定，见下）。两者互斥，都不授权合并；Gitea `Closed` 本身
也不证明部署成功。

### 谁推进 `completed`

`deployed` 由应用部署链路在健康检查成功后回写（02 §9）。manual 路径由会话在人确认 merge 后
执行终态 plan/apply；routine-auto 成功后由同一 issue session 立即执行确定性 plan/apply。两条路径
都必须验证 exact merge，再用 pinned Issue 编号调用 `codex/tools/mark-completed-issues.sh`（#115）：

```bash
codex/tools/mark-completed-issues.sh --range 'origin/main~5..origin/main'   # 读计划
codex/tools/mark-completed-issues.sh --apply 167 168                        # 用计划回给的 pinned 编号写入
# 在别的项目仓上运行时目标由 checkout 判定（#184），判定不出才需要显式 --project：
codex/tools/mark-completed-issues.sh --repo ~/Projects/LocalWMS --range '...'  
```

默认只输出逐 Issue 的判定计划、不做任何写入；确定性验证计划瞄准 exact merge 后加 `--apply` 才经
broker `gitea.issue.labels.set` 写入。已经是 `deployed` 的 Issue 不会被降级为
`completed`。终态、文档、cleanup 与会话归档在 merge 后按确定性流程完成，不再增加人工确认点。

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

下表只适用于已经通过文档声明与实际文件校验的合同。#289 要求工具通过 §3 的共享 resolver 取得规范化 required_docs；缺失的 verification 不能作为“含 verification”的有效合同进入此表，不能改读原文或依据部署属性放行。该约束与工具接入已随 #289 完成 source/local 验证并合并；不由此推导现场安装或部署完成。

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
不是仓库名。governance manifest 按**仓库名**（`LocalWMS`）索引，两者只在六个项目里的三个上
同名（#275 重新接入 SFMDigitalBoard 前是五个里的三个，#252 退出五个项目前是十个里的四个），所以仓库名由 project id 反查得到、不由调用方提供（#172）——host-access manifest 已经
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
所有 remote 的 fetch 与 push URL 都参与匹配——`newemaint` 的 Gitea remote
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
