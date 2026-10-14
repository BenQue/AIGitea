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
status: contract-drafting
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
  - codex/install-host-access-broker.sh
  - codex/install-vm.sh
  - codex/tools/check-installed-drift.py
  - codex/tests/test-install-host-access-broker.sh
  - codex/tests/test-installer-source-guard.sh
  - codex/tests/fixtures/installed-drift/test-installed-drift.py
---

## 目标与原因

让已批准的 canonical vendored 模板更新具有可验证的精确 scope，同时持续拒绝另一 Issue
的文档及任何未批准路径。本票仅交付共享平台能力；下游采用、安装、业务与数据仍在各自项目。

本 spec 是候选合同，`git_scope` 是待批准的 future 最大范围，**本轮不生效**。
status 必须维持 `contract-drafting`；本轮实际写入只有本票四份文档。
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
| `codex/runtime/aisoft_main_integration.py:370–451` | ordinary single-ref push / 固定 guard；`qualified_broker_environment` 比对 wrapper 与七个 runtime 文件 | 没有校核 template policy manifest；需要扩展版本一致性覆盖，不能调用旧/mixed installed 写入口 |
| `codex/runtime/aisoft_loop/cli.py:365–405` | load access/governance 与 project tuple；构造 `LocalGit(repo,branch)` | `LocalGit` 尚未获得 policy；禁止从候选项目文件或任意 caller path 取得放行 authority |
| `codex/runtime/aisoft_gitea_governance/contract.py:603–619` | `vendors_change_templates` 必须 bool；缺省沿用既有 true | 可复用已解析 `RepositoryContract`，无需新增 identity、ACL 或 manifest 字段 |
| `codex/config/change-template-sync.json` / `codex/tools/change-template-sync.sh:135–151,195–206` | 四名、source root、template digest、holder defaults、`downstream_required_check=forbidden` | 可作为可信 canonical 名单来源；digest 描述版本，不是目标候选的授权根 |
| `codex/install-host-access-broker.sh:71–86` / `codex/install-vm.sh:49–68` | 各自复制 shared Git 模块和 access/governance manifests | 当前不复制 sync manifest；source 局部修复不会自动进入 installed |

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

## D-SCOPE360-1 · 完整实施与验收卡

### 一次需要裁定的安全语义

| 选项 | 授权含义 | 影响与建议 |
|---|---|---|
| **A：精确资源授权（推荐）** | canonical 表示四个精确资源身份；holder + 同票 approved scope 逐项授权；保留人工合同/PR 内容审查与项目对齐的逐字节检查 | 修复原 gate 的资源误分类，不在 Git scope gate 新增全历史模板版本锁；下列完整实施范围、fixtures 与 AC 按 A 编排 |
| B：模板内容锁 | 在 A 上增加每个相关提交的模板 bytes 必须对应获批来源快照 | 需要版本 pin、历史范围到快照的映射、快照安装/留存与旧版本升级规则；本方案不把现有 template_digest 当作这些能力。选择 B 后先修订本票 spec/plan，不能直接执行 A |

区别会影响合法的历史模板版本与获批定制内容是否被拒绝，属于安全/架构决定。
本轮只提出建议；等待人一次裁定并批准实施。其余实现选择由下述合同固定，不逐命令请求确认。
没有新的业务规则、数据库或公司运行决定。

### A 的精确合同

1. **资源集合 C 固定四项**：
   `docs/changes/_template/summary.md`、`docs/changes/_template/spec.md`、
   `docs/changes/_template/plan.md`、`docs/changes/_template/verification.md`。
   trusted sync manifest 必须 version/root/documents 形状正确且等于既有四件套；
   不能通过改候选 manifest 把第五个文件加进 C。上游 `templates/...` 路径不是此例外。
2. **同票批准投影**：继续从 exact H 的 committed mapped summary/spec 读取。
   issue/branch/slug/status、唯一 summary 与 mapped spec 必须合法。
   summary 只接受 `approved` 或有效同仓 `pr-open`，spec 必须 `approved`。
   只有逐项出现在 `git_scope`（或受限历史列表）中的 C 元素才有范围资格；
   不以 holder=true、Issue 标签或目录存在代替 scope。不为用户“补上”未批准模板。
3. **可信项目/holder**：broker 使用自己的已解析 access/governance 绑定；Controller
   使用相同 manifest-fixed project/repository 规则与 shared policy factory。
   known repository 且 `RepositoryContract.vendors_change_templates=true` 才可使用 C；
   absent key 按既有 parser true，而 unknown repo/malformed key/unreadable manifest 均拒绝。
   holder=false 不影响该仓普通 own-doc/source scope，只拒绝其 vendored 例外。
4. **policy 与 source provenance**：在现有 shared Git 模块内增加不可变、有限的内部 policy context；
   scope reader 不依赖 `aisoft_loop` 包，从而继续可由两个 installer 分发。
   `scope(head,branch)` 无 context 时保持旧的跨票拒绝；只接受内部 validated context 才允许 C。
   生产入口不能增加 caller URL/path、任意名单、skip/legacy/force 开关。
   trusted policy 只能来自 canonical 安装入口的 access/governance/sync 文件，
   source 模式需与其版本一致；现有 env-selected manifest 即使可 parse，也不能独自赋予 C 例外。
   Controller 与 broker 重用同一 factory，校核目标 repo 与固定 remote，不信候选 checkout 的 manifest。
   `qualified_broker_environment` 扩展到 policy 输入的 exact bytes/版本一致性；
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
| policy provenance/installed bytes 旧、混合、缺失或操作中漂移 | `BROKER_SURFACE_GAP`；固定入口前停止；不补装 |
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
| `codex/runtime/aisoft_main_integration.py` | shared bounded policy、scope 分类、历史模板类型检查与 policy 版本一致性；保留 standard-library 固定 guard |
| `codex/runtime/aisoft_loop/{controller,cli}.py` | 从 canonical context 绑定 LocalGit，Controller 共用判断/漂移处置；不增加 agent merge 权 |
| `codex/runtime/aisoft_host_access/broker.py` | 传入自己 manifest-bound policy、复核快照，与 Controller 同判据 |
| `codex/runtime/tests/{test_main_integration,test_controller,test_host_access}.py` | 下表真实 Git 正负例、dispatch 与一致性回归 |
| `codex/install-host-access-broker.sh`、`codex/install-vm.sh` | 仅受管复制 `codex/config/change-template-sync.json` 到各自 share root，保留 source guard、no-op、previous/恢复规则；写脚本不是执行安装 |
| `codex/tools/check-installed-drift.py` | 两个 installer mapping 增加该 manifest，维护实际受影响的 installer pin，其他六面行为不改 |
| `codex/tests/test-install-host-access-broker.sh`、`codex/tests/test-installer-source-guard.sh`、`codex/tests/fixtures/installed-drift/test-installed-drift.py` | isolated install-root/home fixture 的精确新增文件、缺失/漂移、无凭据/服务访问、原 guard 回归 |

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
| F13 两类 installer 与 drift fixture | 受管 manifest 正确复制、重复 no-op、旧/缺/伪 manifest 失败、previous 可恢复；source guard 写前拒绝仍有效；不在真实主机安装 |

每个失败 fixture 都需断言拒绝阶段、实际 Git transport 调用数、remote ref 与 owned HEAD/index/marker 的
可解释结果。不能用 mock reader success 代替真实 delta/history/transport；mock 仅限身份/network桥接与竞态注入。

### Acceptance criteria

- [ ] AC-1：canonical C 与 another-Issue docs 被准确区分；精确批准子集可用，无目录级 fallback（F01/F02/F04）。
- [ ] AC-2：同票 issue/branch/status/mapping、trusted project/holder/source-policy绑定、输入边界与所有别名/类型负例成立（F05–F08）。
- [ ] AC-3：历史锚、逐提交完整 scope 与类型不被净 diff 或历史例外绕过，R0/R/M/H 祖先/objects/tree 原门保留（F09/F10）。
- [ ] AC-4：真实 Controller `[C,M]` 整合与 ordinary FF、回填/修复/no-op成功，失败/并发/可能写入报告真实（F03/F11）。
- [ ] AC-5：reader/Controller/broker 一致且 fail closed；旧无模板消费者不回归，分发与 drift fixture 覆盖 policy 输入（F12/F13）。
- [ ] AC-6：全 runtime/default smoke、适用 shell 检查、文档门和未来 exact-head required CI 均有真实记录；旧 FAIL/GAP 保留。
- [ ] AC-7：单票/单 writer/唯一 manual PR；source merge、Mac/VM installed 与 HSDB adoption 明确分门，无未合并安装或越权消费者操作。

### 实施、source merge、installed 与 HSDB 采用的边界

1. **本轮**：四份文档、检查、本地线性提交。停在安全语义与实施批准前。
2. **实施批准后**：T02 治理单独应用/检查/commit 后停止，fresh run 重读，继而 T03–T05 本票 source/tests；
   不触发安装或真实身份/业务目标访问。源码门完成后提出唯一最终 PR 第二确认。
3. **source 交付**：第二确认绑定 exact #360/branch/manual 后才受控 FF 与唯一最终 PR；
   required `CI / verify (pull_request)` 必须 final exact head/base/merge-preview 全绿，再等待本人 manual merge。
   source 完成不等待 HSDB #15 完成，也不宣称 installed 已完成。
4. **Mac/VM installed**：source merge 后另获确切目标/身份/文件/回滚授权，先只读盘点实际执行入口。
   Mac broker wrapper `/usr/local/libexec/aisoft/host-access-broker`、库 `/usr/local/lib/aisoft-host-access/`、
   policy `/usr/local/share/aisoft/`；VM broker 同类 system 路径，Controller 实际 runtime 按执行账号盘点
   `$HOME/.local/lib/aisoft-loop/`、`$HOME/.local/share/aisoft/` 与实际启动解释器/import路径。
   核对 merged source pin、shared module/dispatch/context输入 bytes、版本与模式、wrapper、source guard receipt、
   new sync manifest 与 policy hash、两次可重复安装/no-op和一次故意缺失/漂移拒绝及 snapshot 恢复。
   先完整保存前态再写；不以 install exit0 或 source fixture 证明现场成功；不复制/读取用户凭据。
   这些真实动作本次均 NOT RUN，不能为测试启动 provider/timer/服务。
5. **HSDB 采用**：由 `admin/HSDB#15` 原 owner 在自己的授权下 fresh 核对原保留基线/资源、批准 scope、
   所需 Mac/VM 实际入口与本票 installed 能力，再使用正式 reader/Controller/broker 验证完整模板 delta/history。
   保留原 refs/claim/固定 H，不缩实际 scope；原 spec 如需变更安全语义，由其 owner 获批后维护。
   不使用 #360 WT PYTHONPATH 或未合并 runtime 临时绕 gate。
   HSDB 自己的 PR/merge/本机运行/部署/UAT 继续独立授权；#358 架构 gate 独立处理。

## 接口、数据与兼容性影响

不改外部 typed operation 参数、remote/identity、业务 API 或数据库。内部 shared policy 参数只供可信调用方；
缺省保持旧拒绝行为，不让旧消费者意外放行。新安装 manifest缺失时例外 fail closed。
`git_scope` 与 `git_history_paths` 仍是 exact 路径列表，A 不新增消费者 front matter key；
因此原已批准四模板列表无需伪造路径或迁移格式。

## 风险与回滚约束

scope reader 的 fail-open 是主要风险；本方案将 policy 与路径集合放在 shared reader，三入口同判据。
policy版本漂移会让 vendored 例外暂停，必须如实报告具体缺口；不得通过关闭 guard 修复。
source 回滚使用后续受控 revert/修复 PR，不 reset 或 force 旧 refs。
installed 回滚先保存 exact bytes/mode/owner/policy pin、在独立授权窗口恢复成套 snapshot并读回；
混合新旧模块不可作为恢复成功。允许停止而拒绝新模板发表，不以扩大范围保服务。
本轮没有任何 runtime/安装修改可回滚，四文档本地 commit 可审阅并保留。

## 非目标与未决问题

不改 AGENTS、操作权限、Secret/identity、全局 skill、source guard、CI contexts、remote refs保护、
业务库、公司环境；不实现 #358，不代修 HSDB #15，不重做 R2，不恢复旧调度/monitor。
不交付 #327 已延期的 authority/OS/解释器/资源隔离，不制造授权闭包。

唯一未决方向：D-SCOPE360-1 A/B 安全语义及是否批准 A 的完整实施范围。
批准前本 spec 保持草稿，所有产品 AC 未验收，不启动 Development Loop。
