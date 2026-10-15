---
issue: 360
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/360
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - cross-module
  - agent-governance
depends_on: []
status: approved
branch: change/360-canonical-template-scope
created: 2026-10-15
updated: 2026-10-15
git_scope:
  - docs/changes/360-canonical-template-scope/summary-canonical-template-scope-261015.md
  - docs/changes/360-canonical-template-scope/spec-canonical-template-scope-261015.md
  - docs/changes/360-canonical-template-scope/plan-canonical-template-scope-261015.md
  - docs/changes/360-canonical-template-scope/verification-canonical-template-scope-261015.md
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - skill-for-codex/references/project-align.md
  - codex/runtime/aisoft_main_integration.py
  - codex/runtime/aisoft_loop/controller.py
  - codex/runtime/aisoft_loop/cli.py
  - codex/runtime/aisoft_host_access/broker.py
  - codex/runtime/tests/test_main_integration.py
  - codex/runtime/tests/test_controller.py
  - codex/runtime/tests/test_host_access.py
---

## 目标与原因

让已批准的 canonical vendored 模板更新具有可验证的精确 scope，同时持续拒绝另一 Issue
的文档及任何未批准路径。本票仅交付共享平台能力；下游采用、安装、业务与数据仍在各自项目。

本spec为用户在本会话直接批准的合同，批准锚为`ed03008a6cfbbfbf1826501ec6a482929f2d557e`。
`git_scope`的13项是获批整包最大范围，当前T02只可修改03、project-align及本票四文档；
runtime/测试源码须在T02完成并STOP后，由后续fresh run重读再推进。
未填写 `git_history_head/git_history_paths`：新票没有需要 grandfather 的已发表历史。

## 当前源码事实（2026-10-15 fresh main）

所有行号基于 `afd76bf2830ecc7ddc81dc07071ae4bbd8251fc8`，只读分析，没有运行产品函数。

| 路径与入口 | 已有判据 | 缺口/本票意义 |
|---|---|---|
| `codex/runtime/aisoft_main_integration.py:235–291` `GitRepository.scope` | 从 exact commit 读取同票 summary/spec；校验 issue/branch/status、mapped spec、列表数量/重复及 exact path | 285–286 行无差别拒绝非本票 `docs/changes/`；未读取 holder 或 canonical manifest；声明是 contract data，不是批准证明 |
| 同文件 `valid_path:47–52` | 拒绝 absolute、空段、`.`、`..`、`.git`、反斜杠、控制字符及 glob | 必须保留；新增大小写、编码与别名负例，不做路径归一化后放行 |
| 同文件 `verify_history:195–233` / `delta_paths:157–167` | 所有 relevant commit；祖先/objects/第一父链；线性提交 delta；合法 `[Issue tip,main]` merge tree；changed symlink/submodule 拒绝 | add/revert 中间 delta 不能消失；`git_history_paths` 不能变宽门 |
| `codex/runtime/aisoft_loop/controller.py:1063–1119` `LocalGit.integrate_main` | typed fresh main/change、clean exact owner、R0/R、scope、history、独立 merge-tree、HEAD 复核后整合 | 调用 shared scope；Controller 需要可信 template policy context；不赋予 provider merge 权 |
| `codex/runtime/aisoft_host_access/broker.py:3650–3777` | owner/branch/clean、manifest remote/identity、fresh main、scope/history、复读、ordinary push、真实 readback | 同一 reader；no-op 也重验；没有独立 canonical scope 实现可替代 |
| `codex/runtime/aisoft_main_integration.py:370–451` | ordinary single-ref push / 固定 guard；`qualified_broker_environment` 比对 wrapper 与七个 runtime 文件 | 复用现有模块一致性门，例外补足既有access/governance输入绑定；不新增template policy manifest，不能调用旧/mixed installed写入口 |
| `codex/runtime/aisoft_loop/cli.py:365–405` | load access/governance 与 project tuple；构造 `LocalGit(repo,branch)` | `LocalGit` 尚未获得已验证的 holder/project 上下文；需要有限接线，禁止另造caller authority |
| `codex/runtime/aisoft_gitea_governance/contract.py:603–619` | `vendors_change_templates` 必须 bool；缺省沿用既有 true | 可复用已解析 `RepositoryContract`，无需新增 identity、ACL 或 manifest 字段 |
| `codex/config/change-template-sync.json` / `codex/tools/change-template-sync.sh:135–151,195–206` | 四名、source root、template digest、holder defaults、`downstream_required_check=forbidden` | 只读对照四资源合同；digest继续由既有模板同步工具使用，A不新增其runtime依赖 |
| `codex/install-host-access-broker.sh:71–86` / `codex/install-vm.sh:49–68` | 已复制 shared Git/Controller/broker模块和 access/governance manifests | 足够分发A的现有文件变化；不复制sync manifest不是A的缺口，无需改installer |
| `codex/tools/check-installed-drift.py:382–397` | 已映射上述包、shared模块、access/governance manifests | 无新增受管文件，不需新mapping或installer pin变化；使用既有fixture验证 |

平台原件是 `templates/docs/changes/_template/{summary,spec,plan,verification}.md`。
消费者副本是 `docs/changes/_template/{summary,spec,plan,verification}.md`。
platform 的 holder=false；HSDB 未显式声明该 key，按现有解析规则为 true。
这里只读平台 source manifest，不将此推成 HSDB installed/adoption。

Issue #360 正文记载 HSDB #15 在真实 Controller 入口收到
`SCOPE_DENIED: scope crosses another Issue`。其历史整合 I 为
`2a69e773b9845f369e41d9eee538d3de1606838c`，parents 为
`[1913484cfd185147957b3c7ec3dc0812df1744c9,5f18c4ff99b1589b571084ba7022ce7e1ce8bc08]`。
这些是本轮 fresh 读回的 **Issue 报告**，本轮未重放、未读/改原 #15 WT；
原失败完整 candidate SHA 未独立核验，保持 GAP，不补猜。

## D-SCOPE360-1 · 最小流程修复整包审阅卡

**状态：整包已批准，当前只执行T02治理步骤并停止。** 用户直接批准本卡的
`ed03008a6cfbbfbf1826501ec6a482929f2d557e`版本及exact branch；T03–T05留待fresh run重读后继续。
批准不含push/PR、merge、真实安装或项目部署。
本卡是唯一审批入口；front matter的13条exact scope、下列资源/接线/验收/停止边界共同组成整包。
全历史模板内容锁已延期，六个非必要installer/drift源码修改继续排除，不再提出扩大方案选项。

### 必要性、最小实施包与延期项（本次复核）

**有必要实施共享流程修复；没有必要承接项目部署。** 当前同一平台既要求消费者维护四份
canonical vendored 模板，又把这些获批路径当成另一 Issue 拒绝；缺陷发生在平台通用的
scope 判据，修正受益于所有合法模板 holder，不是为 HSDB 增加特例。
只改消费者部署方案、只补平台说明或只删真实scope都无法修复这个判定。

| 项目 | 是否必要 | 最小处置与边界 |
|---|---|---|
| shared reader精确分类与history检查 | 必要 | 在既有Git模块区分own docs、四个canonical资源、otherIssue docs；复用approved scope和逐commit检查，不写第二套授权引擎 |
| `vendors_change_templates` | 必要且已有 | 直接复用`RepositoryContract`字段及既有缺省规则，不改manifest schema或新增逐项目白名单 |
| Controller/CLI接线 | 必要 | CLI已解析project/governance但未传LocalGit；只传足以核对repo/holder的有限上下文并调用shared reader，不新增调度状态机或provider权限 |
| broker接线 | 必要 | 用broker自己的canonical contract传入同一判据；否则Controller通过后broker仍会拒绝或两端边界不一致；不增加operation/参数/身份 |
| 来源/漂移约束 | 必要的局部约束 | 复用现有source/installed模块一致性门及canonical access/governance来源；例外拒绝候选manifest/任意override。只对本次判据所依赖的既有输入作绑定，不新建root/signature/observer框架 |
| 新policy manifest及分发协议 | 不必要 | 四资源身份固定在shared reader，holder已存在；不增加配置服务、动态白名单或sync manifest runtime依赖 |
| installer源码与drift mapping变更 | 不必要，移出scope | 两个现有installer与checker已覆盖全部拟改模块和既有manifests；只验证现有复制/版本检测，不新增安装目标或改六个无关installer |
| 平台工具的真实安装 | 后续独立授权 | 合并后按实际Mac/VM入口证明新模块已分发；这是共享工具版本交付，不是HSDB应用部署。本轮和source实施批准都不自动授权安装 |
| 全历史模板内容锁 | 已延期，不属于审阅包 | 不新增版本pin/历史快照catalog/模板制品留存，不作为本修复启动或交付前置，也不再次要求用户选项确认 |
| 项目PM2/库/服务/环境/UAT | 不属于本票 | 留在HSDB及其原owner的独立合同；不扩大到项目实际部署，也不把全部HSDB业务开发设成全局等待 |

上一分析commit `87fa88a8fde98155ae2b7eccbb27d93632883b04` 曾将sync manifest新分发列入候选；
本次依据既有复制/mapping源码确认可复用，撤回该非必要候选范围。
这是实施批准前的分析收缩，不是已实施后删测试或改验收制造PASS。

### 已收敛语义与批准边界

本卡只采用精确资源授权：canonical表示四个精确资源身份；复用holder与同票committed approved scope，
保留人工合同/PR内容审查及项目对齐的逐字节检查，不增加全历史内容锁。
用户已批准本卡完整scope内的平台source实施及所列本地验证，但明确先执行T02并STOP。
本轮不进入runtime实施/产品测试，不重复询问已确认边界，不增加业务、部署或新安全框架的决定。

### 精确合同

1. **资源集合 C 固定四项**：
   `docs/changes/_template/summary.md`、`docs/changes/_template/spec.md`、
   `docs/changes/_template/plan.md`、`docs/changes/_template/verification.md`。
   C 的四个完整路径在现有shared reader内集中定义并经fixture与既有四件套合同对照；
   不新建dynamic policy/manifest schema，也不运行时依赖sync manifest。
   不能通过改候选manifest或传任意列表把第五个文件加进C。上游 `templates/...` 路径不是此例外。
2. **同票批准投影**：继续从 exact H 的 committed mapped summary/spec 读取。
   issue/branch/slug/status、唯一 summary 与 mapped spec 必须合法。
   summary 只接受 `approved` 或有效同仓 `pr-open`，spec 必须 `approved`。
   只有逐项出现在 `git_scope`（或受限历史列表）中的 C 元素才有范围资格；
   不以 holder=true、Issue 标签或目录存在代替 scope。不为用户“补上”未批准模板。
3. **可信项目/holder**：broker 使用自己的已解析 access/governance 绑定；Controller
   使用相同 manifest-fixed project/repository 规则，将现有已验证contract的有限上下文传给shared reader。
   known repository 且 `RepositoryContract.vendors_change_templates=true` 才可使用 C；
   absent key 按既有 parser true，而 unknown repo/malformed key/unreadable manifest 均拒绝。
   holder=false 不影响该仓普通 own-doc/source scope，只拒绝其 vendored 例外。
4. **上下文与 source provenance**：在现有 shared Git 模块内接收不可变、有限的内部上下文；
   scope reader 不依赖 `aisoft_loop` 包，从而继续可由两个 installer 分发。
   `scope(head,branch)` 无 context 时保持旧的跨票拒绝；只接受内部 validated context 才允许 C。
   生产入口不能增加 caller URL/path、任意名单、skip/legacy/force 开关。
   repo/holder上下文只能来自 canonical 安装入口的既有access/governance绑定，
   source 模式需与其版本一致；现有 env-selected manifest 即使可 parse，也不能独自赋予 C 例外。
   Controller与broker复用同一核对函数和现有parser，校核目标repo与固定remote，不信候选checkout的manifest。
   复用`qualified_broker_environment`既有模块版本一致性门；仅对例外依赖的既有access/governance
   输入补足来源/bytes一致性绑定，不新增policy文件、快照catalog或独立批准服务。
   缺失、旧或 mixed surface 返回 `BROKER_SURFACE_GAP`，不临时安装或降级旧入口。
   source 单元/fixture 可显式构造封闭测试 context；不得暴露为生产 CLI 的通用 override。
5. **路径与类型**：按 Git tree 中大小写敏感的原始 repo-relative 字符串判断；
   own Issue 目录规则继续存在，C 外的 `docs/changes/` 路径继续拒绝。
   C 必须是 100644 普通 blob，不能 executable、symlink、gitlink、目录或别名。
   在 committed tree 和工作树入口分别核对，包含 parent 目录 symlink；不跟随 symlink 做白名单匹配。
   rename 用 `--no-renames` 的旧/新两个路径验证；删 canonical 模板不属于“更新副本”例外，应拒绝。
6. **完整 delta/history**：允许集合只加已批准的 C 元素，数量/重复/空/解析/上限硬门保留。
   对 `git_scope` 和 `git_history_paths` 共用相同资源分类。
   历史锚是 exact 可达 ancestor；历史列表不授权锚后修改，也不授权另一 Issue。
   C 的内容不在 A 中另加逐字节全历史锁，但每个改动仍必须经过真实 per-commit 路径和类型检查；
   不得只看净 diff，不允许 add→revert 掩盖越界，不能缩 scope 省略实际 delta。
7. **操作/漂移**：R0、R、M 都保持原祖先要求；只有受控 `[Issue tip,M]` tree 整合；
   provider 只写线性本票 commit；ordinary single-ref FF、固定 guard、exact advertised old-id、
   no-op 重验、真实 remote=H 和 required CI 保留。
   在 policy 读取前后记录并比较其 manifest hashes 与 project binding；同次操作 policy/owner/H/R/M
   移动则停止，不能换新锚静默续跑。hash snapshot 是 cooperative drift 检测，不宣称同 UID 安全隔离。
8. **批准真实性边界**：`status: approved` 和 owner marker 都是合同投影，不证明人类批准不可伪造。
   仍须完整合同批准与最终 PR 第二确认。本票不交付 root authority、签名批准、OS 观察器或完整解释器闭包。

### 保留的失败响应及副作用语义

以下保留已有错误码，不创造“今天已返回”的新证据。新增情形归到相应现有码，诊断应区分具体原因。

| 阶段 | 错误码与行为 |
|---|---|
| summary/spec/status/mapping 或 scope 结构缺失/歧义 | `SCOPE_UNKNOWN`；不把草稿或标签直接当批准 |
| 另一 Issue docs、非 C 子路径、未批准模板、非法 path/type/holder、越界 delta | `SCOPE_DENIED`；fixture 断言零 push，远端不变 |
| 例外所需canonical上下文/source-installed bytes旧、混合、缺失或操作中漂移 | `BROKER_SURFACE_GAP`；固定入口前停止；不补装 |
| owned WT/branch/session 不一致或 dirty | 既有 `WORKTREE_UNCLAIMED`、`WORKTREE_CLAIM_INVALID`、`WORKTREE_OWNER_MISMATCH`、`WORKTREE_DIRTY` |
| history/objects/tree 不合法 | `NON_FAST_FORWARD`、`DAG_DENIED`、`FOREIGN_MERGE_DENIED`、`MERGE_TREE_DENIED`、`MERGE_BASE_DENIED`、`MERGE_CONFLICT` 及既有 Git capability/config/object 拒绝 |
| H/R/M 及 first-ref/删除重建漂移 | `HEAD_MOVED`、`REMOTE_BRANCH_MOVED`、`BASE_BRANCH_STALE`；保持 exact 前态，停止 |
| guard/transport/readback | 保留 `GUARD_*`、`PUSH_STATUS_INVALID`、`PUSH_READBACK_UNKNOWN`、`BASE_ADVANCED_AFTER_PUSH`；若可能已写入，保留 actual/possible H，不能称零写或盲重推 |

本票不要求所有 scope 错误都在 credential resolution 前发生：现 broker 会先读取身份并 fetch。
要求拒绝发生在远端写入前，零 scope 绕过；fixture 使用假 credential provider，绝不访问真实身份。

### 完整 source / 文档 / 测试范围

精确 future `git_scope` 位于本 spec front matter。普通修改不得触及其他路径。

| 路径 | 允许内容 |
|---|---|
| 本票四份 mapped docs | 合同、真实证据、后续唯一 PR summary 回填 |
| `03-Issue-Spec-Plan与单闸门开发流程.md`、`skill-for-codex/references/project-align.md` | 独立治理 T02：补资源边界/holder/批准/source层次，不改其他全局或 provider 规则；提交后 STOP，fresh run 再读 |
| `codex/runtime/aisoft_main_integration.py` | shared scope分类、有限repo/holder上下文、历史模板类型及既有来源绑定；保留standard-library固定guard，不建新框架 |
| `codex/runtime/aisoft_loop/{controller,cli}.py` | 从 canonical context 绑定 LocalGit，Controller 共用判断/漂移处置；不增加 agent merge 权 |
| `codex/runtime/aisoft_host_access/broker.py` | 传入自己 manifest-bound policy、复核快照，与 Controller 同判据 |
| `codex/runtime/tests/{test_main_integration,test_controller,test_host_access}.py` | 下表真实 Git 正负例、dispatch 与一致性回归 |

两个installer、`check-installed-drift.py`及其fixture源码仅只读复用，不在future修改allowlist。
既有分发验收仍需运行，且不能因没有新增安装文件而宣称真实安装已完成。

`codex/config/{gitea-governance,host-access-broker,change-template-sync}.json`、
`templates/docs/changes/_template/*.md` 是只读 policy/模板来源，不属于本票修改范围。
现有 holder 字段已足够，不新增注册仓、身份、operation 或 required context。
本票不修改 AGENTS.md、全局 skills、workflow、source guard，也不改 HSDB 任何文件。
若实际实现必须增加这里之外的文件/权限或策略，停在本票修订合同，不能沿目录扩大范围。

### 真实 Git fixture 与正负验收计划（本轮全部 NOT RUN）

fixtures 使用全新临时目录、真实 `/usr/bin/git` 对象/工作库/本地 bare remote；
project/manifest/identity 均为封闭 fixture。复制平台真实四模板内容作为合法样本，
不访问 `.orb.local`、真实凭据、用户 #15 repo/refs/claim 或数据库。

| 场景 | 必须观察的结果 |
|---|---|
| F01 合法 holder、同票 approved summary/spec、四模板逐项获批 | reader 返回 exact 路径；复制四模板的真实 commit 被 history 接受；未提交 spec 放宽无效 |
| F02 只批准四件套的严格子集 | 仅返回已列项；未批其余项的实际 delta 拒绝，证明 holder/C 不自动授权全部四个 |
| F03 main 在不同普通路径前进 | 从 C 执行真实 `LocalGit.integrate_main`，I.parents=[C,M]、I.tree=独立 merge-tree；裸 remote 首发、再次普通 FF、线性修复、PR summary-only 回填/no-op 均 exact readback |
| F04 另一票目录、任意子目录、第五模板、伪 Issue 命名/多 slug | `SCOPE_DENIED` 或既有 tuple 冲突拒绝；零 push、H/R 前态保留 |
| F05 holder=false/unknown repo/伪 candidate manifest/env替身/missing context | 禁止 canonical 例外；普通 own scope 仍按原规则工作；production caller 无通用 override |
| F06 summary analyzed、spec drafting、错 issue/branch/url、duplicate scope/mapping、空/超限 | `SCOPE_UNKNOWN`；pr-open 仅接受同仓有效 PR URL + approved spec；未提交修正不生效 |
| F07 `../`、`./`、absolute、glob、反斜杠、控制字符、大小写/URL编码/Unicode相似名/尾斜杠 | 非 C 或 invalid path；不得 canonicalize 成合法名单后放行 |
| F08 leaf/parent symlink、Git mode120000/gitlink160000、executable100755、删除/rename到别处 | canonical 模板更新拒绝；每个中间 tree 检查；symlink 后再还原也不放行 |
| F09 超范围 add→revert、历史另一票、历史未批模板、伪/不可达 history anchor、锚后扩大 | 保留 per-commit 拒绝；合法 history锚+明确精确历史 C 可通过；scope 不隐藏真实 delta |
| F10 非FF、reverse/octopus/foreign/extra-tree merge、replace/graft/shallow/缺对象/driver | 原 #327 负例保持；无 forced rewrite/guard bypass |
| F11 owner/H/R/M/policy 在读前后/guard窗口移动、first-ref抢占/删除重建 | 同因错误、零本次覆盖或如实 possible-write；保全证据，不静默重锚 |
| F12 三入口一致性及旧行为 | 相同 fixtures 输入 reader/Controller/broker 得相同允许/拒绝语义；无模板范围的现有消费者无需新字段，旧/mixed policy 无法获得例外 |
| F13 复用既有installer/drift fixture | 已有复制模式覆盖改动模块和access/governance，旧/缺/漂移模块继续被识别，原source guard仍有效；不新增sync manifest安装链，不在真实主机安装 |

每个失败 fixture 都需断言拒绝阶段、实际 Git transport 调用数、remote ref 与 owned HEAD/index/marker 的
可解释结果。不能用 mock reader success 代替真实 delta/history/transport；mock 仅限身份/network桥接与竞态注入。

### Acceptance criteria

- [ ] AC-1：canonical C 与 another-Issue docs 被准确区分；精确批准子集可用，无目录级 fallback（F01/F02/F04）。
- [ ] AC-2：同票 issue/branch/status/mapping、trusted project/holder/source-policy绑定、输入边界与所有别名/类型负例成立（F05–F08）。
- [ ] AC-3：历史锚、逐提交完整 scope 与类型不被净 diff 或历史例外绕过，R0/R/M/H 祖先/objects/tree 原门保留（F09/F10）。
- [ ] AC-4：真实 Controller `[C,M]` 整合与 ordinary FF、回填/修复/no-op成功，失败/并发/可能写入报告真实（F03/F11）。
- [ ] AC-5：reader/Controller/broker一致且fail closed；旧无模板消费者不回归，既有分发/drift fixture证明覆盖同一组模块与输入，不新建分发机制（F12/F13）。
- [ ] AC-6：全 runtime/default smoke、适用 shell 检查、文档门和未来 exact-head required CI 均有真实记录；旧 FAIL/GAP 保留。
- [ ] AC-7：单票/单 writer/唯一 manual PR；source merge、Mac/VM installed 与 HSDB adoption 明确分门，无未合并安装或越权消费者操作。

### 必要本地资源、停止与保全

| 资源或情况 | 整包批准后的允许用途 / 停止边界 |
|---|---|
| 已claim的`/private/tmp/issue-360-canonical-template-scope` | 继续同branch/同writer线性本地commit；不创建第二writer或借用HSDB WT |
| 现有`python3`、`/usr/bin/git`、Bash及默认smoke所需既有工具 | 只用已有环境；Git须支持现有`merge-tree --write-tree`及对象检查。缺工具/不支持/依赖缺失即GAP/BLOCKED_EXTERNAL，不自行安装 |
| 新建的本票临时fixture目录及本地bare remote | 仅在`/private/tmp/`新建本票独占临时root，放合成数据/假manifest/假身份；可重复重建自己的fixture，不能清理历史WT、用户库或他票资源；需要网络或真实凭据的验证不属于本地fixture授权 |
| 本会话artifact证据目录 | 记录命令/exit、前后H/R/M/tree、失败及恢复结果；不把源码/fixture通过投成installed/UAT |
| exact owner/branch/HEAD、scope/manifest来源或R/M并发漂移；冲突/历史非法/重复同因失败 | 立即停止并保全前态、实际/可能写入状态与日志；不重锚、覆盖、force、扩大scope或关闭guard |
| 必须新增scope外文件、机制或真实目标动作 | 记录具体GAP，返回本票审阅；不得把整包批准解释成无限扩展或安装授权 |

当前没有分配/创建上述产品fixture资源、没有执行产品测试。source实施后，若实际installed入口旧/缺失，
记录具体入口和pin的后续平台工具安装需求，source合并后另获授权；不为此扩建本轮installer框架。

### 实施、source merge、installed 与 HSDB 采用的边界

1. **本轮T02**：03、project-align及四份mapped docs，文档检查、本地线性提交后STOP。
2. **后续fresh run**：重读已应用治理合同与原整包批准，复核owner/HEAD/来源后继续T03–T05本票source/tests；
   不触发安装或真实身份/业务目标访问。源码门完成后提出唯一最终 PR 第二确认。
3. **source 交付**：第二确认绑定 exact #360/branch/manual 后才受控 FF 与唯一最终 PR；
   required `CI / verify (pull_request)` 必须 final exact head/base/merge-preview 全绿，再等待本人 manual merge。
   source 完成不等待 HSDB #15 完成，也不宣称 installed 已完成。
4. **Mac/VM installed**：source merge 后另获确切目标/身份/文件/回滚授权，先只读盘点实际执行入口。
   Mac broker wrapper `/usr/local/libexec/aisoft/host-access-broker`、库 `/usr/local/lib/aisoft-host-access/`、
   policy `/usr/local/share/aisoft/`；VM broker 同类 system 路径，Controller 实际 runtime 按执行账号盘点
   `$HOME/.local/lib/aisoft-loop/`、`$HOME/.local/share/aisoft/` 与实际启动解释器/import路径。
   核对 merged source pin、shared module/dispatch/context输入 bytes、版本与模式、wrapper、source guard receipt、
   既有access/governance绑定、两次可重复安装/no-op和一次故意缺失/漂移拒绝及snapshot恢复；不增加sync manifest安装目标。
   先完整保存前态再写；不以 install exit0 或 source fixture 证明现场成功；不复制/读取用户凭据。
   这些真实动作本次均 NOT RUN，不能为测试启动 provider/timer/服务。
5. **HSDB 采用**：由 `admin/HSDB#15` 原 owner 在自己的授权下 fresh 核对原保留基线/资源、批准 scope、
   所需 Mac/VM 实际入口与本票 installed 能力，再使用正式 reader/Controller/broker 验证完整模板 delta/history。
   保留原 refs/claim/固定 H，不缩实际 scope；原 spec 如需变更安全语义，由其 owner 获批后维护。
   不使用 #360 WT PYTHONPATH 或未合并 runtime 临时绕 gate。
   HSDB 自己的 PR/merge/本机运行/部署/UAT 继续独立授权；#358 架构 gate 独立处理。

### 已收到的整包批准及历史审阅措辞

用户在本会话直接批准#360按本卡`ed03008a6cfbbfbf1826501ec6a482929f2d557e`版本实施及所列本地验证，
绑定`change/360-canonical-template-scope`；先T02并停止，fresh run重读后继续；
不含push/PR、merge、真实安装或项目部署。下方保留原整包审阅措辞以供核对，不能改变用户实际授权。

> 批准admin/aisoft-platform#360按D-SCOPE360-1最小流程修复整包卡实施，绑定
> change/360-canonical-template-scope及卡内13条exact scope；允许先完成T02独立治理步骤并停止，
> fresh run重读后继续T03–T05范围内source、所列本地合成fixture/回归、普通修复和线性本地提交。
> 全历史模板内容锁及六个installer/drift源码修改不纳入；push/唯一最终PR仍待第二确认，
> manual merge、Mac/VM真实安装、HSDB采用及任何项目部署/UAT不在本次批准内。

上方批准锚保留为原被审阅HEAD，不能替换成本轮新HEAD以扩大批准内容；后续普通实现commit遵循既定scope。

## 接口、数据与兼容性影响

不改外部 typed operation 参数、remote/identity、业务 API 或数据库。内部 shared policy 参数只供可信调用方；
缺省保持旧拒绝行为，不让旧消费者意外放行。所需既有canonical manifest不可用时例外fail closed。
`git_scope` 与 `git_history_paths` 仍是 exact 路径列表，A 不新增消费者 front matter key；
因此原已批准四模板列表无需伪造路径或迁移格式。

## 风险与回滚约束

scope reader 的 fail-open 是主要风险；本方案将 policy 与路径集合放在 shared reader，三入口同判据。
policy版本漂移会让 vendored 例外暂停，必须如实报告具体缺口；不得通过关闭 guard 修复。
source 回滚使用后续受控 revert/修复 PR，不 reset 或 force 旧 refs。
installed 回滚先保存 exact bytes/mode/owner/policy pin、在独立授权窗口恢复成套 snapshot并读回；
混合新旧模块不可作为恢复成功。允许停止而拒绝新模板发表，不以扩大范围保服务。
本轮没有任何 runtime/安装修改可回滚，四文档本地 commit 可审阅并保留。

## 非目标与后续门槛

不改 AGENTS、操作权限、Secret/identity、全局 skill、source guard、CI contexts、remote refs保护、
业务库、公司环境；不实现 #358，不代修 HSDB #15，不重做 R2，不恢复旧调度/monitor。
不交付 #327 已延期的 authority/OS/解释器/资源隔离，不制造授权闭包。

整包启动批准已收到，没有待裁定的A/B选择；产品AC仍全部未验收。
本轮T02完成后STOP，后续fresh run重读与正式入口复核后才进入T03–T05；PR/merge/install/deploy授权未授予。
