---
issue: 327
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/327
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - cross-module
  - security
  - rollback
depends_on: []
branch: change/327-broker-ff-integration
created: 2026-10-02
updated: 2026-10-02
status: approved
---

# #327 最小治理与发布合同

## 目标与原因

保持 original remote tip 为每次新 head 祖先，允许严格来源限定的 fresh manifest main 整合，并经 ordinary FF push 发布；禁止 force、lease-force、任意 merge 与更宽身份 fallback。负责人已在本聊天确认合同和独立 T01。此轮授权只覆盖映射治理文本、四角色文档、验证及本地原子提交，完成后立即 STOP；不能据此同轮实施 runtime、发表 PR 或安装。

## 状态、来源与信任边界

| 符号 | 来源及含义 |
|---|---|
| R0 | 第一次接管时经 canonical broker 读回的 original remote tip；无远端则 null |
| R | 本次发布前同一 exact ref 的真实 tip；每次刷新，不把 last_push_head 当远端真值 |
| M | 本次 fresh fetch 的 manifest main，40 位 lowercase SHA |
| C | owner 已核验的本 Issue 线性本地提交末端，R 必须为其祖先 |
| I | Controller 构造的 main 整合 commit，parents 精确为 [C, M] |
| H | 本次验证并锁定的最终候选；允许 I 后继续追加本 Issue 线性 commit |

提交 message、author、同名 branch 和可编辑本地 receipt 都不足以证明来源。Controller 需记录每次 owner/issue/branch/base/commit/tree/scope 的验证证据；broker 独立读取 Git DAG、main 来源、批准合同与完整 delta，不把模型自述或 receipt 的 PASS 当授权。Git 对象本身没有所属分支字段，不能从 commit subject 推断 branch provenance。

R0 一经 pin 就不改写。正常演进保持 R0→R→H 的祖先链。若远端被人工修改、重写、删除或换 slug，停止；先解释、保全与重新核验，不能把异常 tip 静默采为新的 R0。已有人工 main 整合的 remote commit 只有通过同样 parent/tree/range 验证及 exact 人工事件读回后才能采用。

## 受控整合与兼容

1. owner 仅在自己的 exact worktree 追加本地原子 commit。provider 仍不得创建 merge commit、push、PR、merge main 或持有凭据。
2. 若 M 已为 C 祖先，无需整合；若 C 为 M 祖先，可在不丢弃 Issue 历史且合同 delta 仍满足时本地 FF；已被 main 完全吸收的 Issue 不通过空 PR 掩盖终态。
3. 若 C/M 分叉，只有外层 Controller 的受控本地步骤可构造 I=[C,M]。M 必须来自本次 broker fetch，C 属于已核验本 Issue 第一父链，R 为 C 祖先。只支持确定性、无冲突合并；独立重算 merge tree，并要求 I tree 完全相同。
4. 有冲突、criss-cross/多 merge base、不支持的 Git 行为、非默认 merge driver、replace/graft/shallow 或缺失对象均 fail closed。拒绝 `ours`、隐藏额外 blob、未经核验的冲突解决；若需要改变支持范围，升级合同，不静默处理。
5. 首次、重复整合与之后 CI repair 都验证完整 relevant DAG；历史合法整合第二 parent 必须仍在当前 manifest main 祖先链中，且 parent/tree/provenance 全部复核。不得“遇到一个合法 merge 就放行所有 merge”。
6. 拒绝其他 change branch 的侧向 merge、外仓来源、other-Issue 未批准 commit、parent 反序、octopus、第二 parent 仅与 main 有共同祖先但不是 main 历史、merge 中额外内容或范围越界。
7. M..H 的最终差异与整合前 Issue delta 均按批准 spec 的 exact 文件清单和内容目的校验；不能只校验文件名或 commit subject。main 自身引入的其他 Issue 变化作为基线继承，不要求改写其 message。

## Ordinary FF 发布与并发

保留 `git.push.change` 的 typed argument 精确集合 `branch`，project/repository/remote/credential 仍来自 canonical manifests，不接受调用方 URL、refspec、checkout、merge、force 或 hook 参数。无新公开 merge typed operation；本地构造与 broker 的远端独立验证分开。

- 发布前验证 clean HEAD、exact branch/ref、single-writer、40 位 SHA、权限、唯一 active branch/docs/PR、R0/R/H 来源、R→H、fresh M→H、范围及本次核验 H。拒绝时零远端写。
- 使用普通单 ref push；禁止 `--force`、`--force-with-lease`、`+refspec`、`--mirror`、`--all`、delete、main 更新、push-option/fallback；传输源绑定 exact H，避免分支在核验后移动。
- 仅“先 ls-remote 再裸 push”不足以实现 strict R pin：并发的 R1 若恰好是 H 祖先，Git 仍可能允许 FF。拟采用 broker 控制的固定 pre-push guard，读取本次传输公告的 remote object id，要求 exact R（新 ref 为全零），local object id=H、唯一 exact target；不符合即拒绝。
- guard 必须由受控 runtime 生成/执行，固定 hook path、固定程序与参数、隔离环境和权限；不得执行仓库自带或调用方注入 hook，不允许 `--no-verify`、可替换 guard、symlink 或缺失 guard。新增受管代码必须纳入 installer 和漂移核对。
- 传输公告后 ref 再变由服务端 old-id ref update 检查拒绝；需实际 bare-remote race fixture 证明。首创竞争、远端删除重建、R1 位于 R→H 之间、公告后变化均覆盖。拒绝表示本次零覆盖；外部 writer 自身产生的变化如实保留。
- no-op H=R 时不依赖 hook 被调用：重新读回 exact ref 与 main 并全门验证，返回 truthful no-op；若有漂移则拒绝。 对预检H≠R却传输报告up-to-date（并发writer已把ref推进至H），不能伪称本次发表PASS；必须标为REMOTE_BRANCH_MOVED/本次零写。检查固定guard执行回执与实际更新行，预期有更新却guard未执行或无exact ref行均fail closed。首创并发者恰好创建H也同样拒绝，不误报本次创建。
- Git 单 ref push 不能把“不更新 main 的 freshness read”和 change 更新变成双 ref 原子事务。M 绑定最后一次明确读取的快照，push 前再次检查；若发现 main 前进则停止。push 后 main 发生推进，记录已发表 H、latest main、`BASE_ADVANCED_AFTER_PUSH`，停止 PR ready/merge，不 force 退回 H；重新受控整合。不得宣称整个并发窗口 main 从未改变。
- 成功后再读真实 remote SHA，必须等于 H 才报 PASS、记录 last_push_head；`previous_head=R`、`pushed_head=H` 保留原字段，新增 M/R0/verification receipt 可以向后兼容追加。网络失败或读回不明时报告“写入可能已落地”，不盲重试、不误称零写。

参考：[Git FF 定义与普通 push](https://git-scm.com/docs/git-push)、[pre-push 的 remote object id 与非零退出拒绝](https://git-scm.com/docs/githooks#_pre_push)。上述 guard/CAS 组合为本合同设计推论，实际实现与竞态验证 NOT RUN。

## 治理映射与独立停止点

T01 只在独立受控治理应用步骤，按已确认本 spec 精确修改以下文本，不混入 Python/runtime/install/CI 实现；commit 后立即停止。合同准备阶段没有修改 AGENTS.md；当前独立 T01 仅依据负责人随后直接确认应用该映射治理，不能混入 runtime。后续 fresh run 必须重新读取本 worktree 的治理、Issue、有效评论、spec/plan 和 installed 能力，不继承旧上下文替代读取。

| exact 文件 | 允许的最小治理变动 |
|---|---|
| `AGENTS.md` | 保留 Agent 无 merge 与 Controller FF；增补只有受控 Controller 可构造 [Issue first-parent, fresh main] 确定性整合；所有已发表历史不可重写；声明 source/installed 与自举边界 |
| `03-Issue-Spec-Plan与单闸门开发流程.md` | 覆盖 rebase/重推活语句，补 provenance、FF、per-push SHA 和已发表/未发表分界 |
| `04-Agent编排与定时任务.md` | Controller 专属整合步骤，不将 main merge 当 provider commit；失配与冲突停止 |
| `06-运维手册与踩坑集.md` | 标注 #136 lease 解法为历史、被 #327 取代；旧安装只读，不执行旧 leased write；写 incident/rollback 与两机验收边界 |
| `08-双工具共存与实施.md` | 两 provider 共用整合/发表边界；不新增启用权限 |
| `codex/skills/issue-session-flow/SKILL.md` | 源技能表达已发表分支追加整合和 SHA 核对；保留单 writer、两个确认点 |
| `skill-for-claude/issue-session-flow/SKILL.md` | 同一共享合同的 Claude 对等说明 |
| `codex/skills/aisoft-matt-workflow/SKILL.md` | provider 无 merge，Controller 执行限定整合；不编辑 vendored 上游 |
| `skill-for-claude/aisoft-platform/SKILL.md` | 与Codex对应的共享发布能力与installed/live边界说明 |
| `skill-for-codex/SKILL.md` | 限定 FF 能力、人工自举、source/installed 与验收前不完成 |
| `skill-for-codex/references/private-gitea-access.md` | 保留 broker-only；区分人本人 UI 自举与 Agent 禁令 |
| `docs/agents/issue-tracker.md` | Controller 整合归属与本 Issue 人工 UI 发表卡；禁止代操作 |
| `templates/docs/agents/issue-tracker.md` | 同步平台 tracker 合同；不新增另一套模板 |
| `README.md` | 仅增加 #327 source/installed 状态及导航，不改无关内容 |

建议治理核心措辞：Agent/provider 只追加本 Issue 线性 commit；外层 Controller 仅在批准合同内以 exact remote 原历史为祖先、fresh manifest main 为第二 parent，构造可复算无冲突整合；broker 全门验证后仅普通 FF 发布。此许可不包括 arbitrary merge、历史重写、force、凭据、保护调整、UI 代提交或部署。

历史 #298 spec AC-6（rebase-重推）及 AC-5 中 A 推送 B 改写 HEAD 的“推送发生”预期，以及 #136/06 的 leased rewrite，是历史验收口径。#327 生效后已发表分支重写必须拒绝；#298 的 owner、拒绝错误与逐 push SHA 回执继续保留。通过本 spec 与当前活文档明确覆盖，不改写、删除已闭合历史文档。未发表本地 rebase仅限自身 worktree、未核验/未发表历史；不传递已发表重写权限。

## Runtime 精确映射（fresh run 后）

| exact 文件 | 允许职责 |
|---|---|
| `codex/runtime/aisoft_host_access/broker.py` | 用 FF/DAG/provenance/guard/readback 替代 blanket merge deny 与 leased push |
| `codex/runtime/aisoft_loop/controller.py` | Controller 专属本地整合与验证记录；原 provider 线性提交校验保持 |
| `codex/runtime/aisoft_loop/gitea.py` | 必要的 broker fetch/push 调用接线，禁绕行 |
| `codex/runtime/aisoft_host_access/runner.py` | 同一 typed bridge 的可读 exact branch 接线（只在整合需要时）；不得恢复纯编号新 writer |
| `codex/runtime/aisoft_main_integration.py`（可新增） | 两侧共用纯本地 DAG/tree verifier 与固定 guard 支撑；无网络、凭据或宽命令入口 |
| `codex/runtime/aisoft_worktree_owner.py` | 必要的向后兼容 R0/last_push 证据扩展，不把标记当授权凭据 |
| `codex/install-host-access-broker.sh`、`codex/install-vm.sh` | 仅新增 helper 的受管安装映射；不执行真实安装，不改 provenance guard |
| `codex/tools/check-installed-drift.py` | helper 的受管文件映射；不加入自动修复 |
| `codex/runtime/tests/test_host_access.py`、`test_controller.py`、`test_worktree_owner.py`、`test_main_integration.py`（可新增） | 参数、DAG、scope、单 writer、真实临时 bare remote 与组合回归 |
| `codex/tests/test-host-access-broker.sh`、`codex/tests/test-install-host-access-broker.sh`、`codex/tests/test-agent-runtime.sh`、`codex/tests/test-installed-drift.sh`、`codex/tests/fixtures/installed-drift/test-installed-drift.py` | 固定guard、两侧安装与漂移fixture更新 |
| `codex/tests/smoke.sh` | 只接入本 Issue 必要用例/受管 helper 检查，不删改现有硬门 |
| `docs/changes/327-broker-ff-integration/` 的四份映射文档 | 同步批准状态、真实验收和 handoff |

不改 broker 公共 operation 表与参数，不改治理 manifest 身份/权限/main/context/routine 值，不扩大 runtime scope。若 fresh 核对显示需要其他文件，先记录冲突再由人批准，不能泛用目录授权。

## 本 Issue first-PR 自举（负责人本人 UI）

旧 installed broker 的任意首推仍携带 lease-force。本 Issue 不调用它发表，也不先安装 unmerged runtime、不用 source wrapper/direct Git/API fallback。完全自动 Agent 自举目前不具备合规路径。

只读 Chrome 已看到 Gitea 1.26.4 的 Add File → New File/Upload File；New File 的“Commit directly to main”被保护禁用，“Create a new branch for this commit and start a pull request”可选，branch name 可填写。只证明入口，不证明写入与 tree/mode 等价。

1. T01/T02/T03 全在本地 exact branch完成；保存候选 L、base M、完整 binary patch/bundle、tree id、每文件 blob/mode 与文档映射。零 remote write。
2. 最终提交确认绑定 #327 / `change/327-broker-ff-integration` / manual，并明确采用负责人本人 UI publisher，AI 不代点击。发表前 fresh 查重 remote branch与唯一 PR；若能力缺失，停止 GAP，不能推断 ref absent。
3. 负责人本人使用 New File 的 new-branch 方式创建 exact branch，并在 PR 提交页面只创建一个最终 PR。若 UI 自动创建 PR，那就是唯一 PR；不再 broker create第二个。全部候选文件只写 change branch，绝不写 main。逐文件编辑/上传追加提交，保留已有 executable mode；新文件限普通文本 100644。不能保留 mode、不可精确写树或 UI 不支持时停止，不能改用 direct Git。
4. UI 创建的是 human-authored commit H，并非本地 L。owner 只通过 typed fetch 读取对象，验证 base/parent/全部文件 blob+mode、scope 和最终 tree等价；main变化则重新计算并验证组合结果。远端 H 必须重新跑全部本地必要验证和 exact head required CI，不能引用 L 的旧绿灯。
5. mapped summary 的唯一 pr_url、status=pr-open 由 owner 准备准确文件，再由负责人同一 UI追加；不调用旧 broker 回填 push。每次新 H 都重新 scope/tree/CI。CI repair由 owner本地准备并验证文件，仍由本人UI追加到同一 branch/PR；人也可 Update branch by merge，并由 owner验 exact old tip与fresh main祖先/DAG。
6. 本地 L不应 reset/rebase为human H；保留可恢复bundle与原owner worktree，本地与远端 SHA 两层分别记录。必要测试在只读 fetch 对象导出的隔离验证目录执行，不创建第二 active writer。单 writer 约束保留。
7. fresh final H、main保护/祖先、requiredCI、唯一PR、分类全满足后 READY_FOR_REVIEW。负责人本人普通人工 merge；AI 不点击 merge/Update branch，不自动排程 merge。

本路线是本 Issue 源码发表所需的人工执行卡方案；后续真实 UI tree/mode验证仍为 AC，失败就保留阻塞。它不授予 Agent ordinary Git 或 admin credential，不把 #327 设为 #289/#319 人工更新的机械前置。

## Acceptance criteria

- [ ] AC-1：四角色 exact 映射、platform/complex/manual、来源/授权、单 writer与triage/分类读回可复核；准备期零 live mutation。T01治理只改映射合同并停止；fresh run记录重读后才能runtime。
- [ ] AC-2：R0/R/H、M、commit/tree/scope 全门有效；首次创建、普通FF、无冲突限定整合、重复整合、summary backfill/CI repair及no-op可完成；每次 old tip 为 new tip祖先。
- [ ] AC-3：真实 bare remote的非FF、首创抢占、R1处于R→H之间、公告后竞态、异常删除/重建与本地HEAD移动均被拒绝或如实报告落地不明；失败不能覆盖他人历史，无force/fallback。
- [ ] AC-4：foreign/other-Issue/反序/octopus/stale-main/tampered-tree/范围越界/driver/缺对象/不支持历史、错误project/owner/branch/dirty树均在 mutation前拒绝；原单writer与provider merge deny不弱化；历史 #298 AC-5/6覆盖有测试。
- [ ] AC-5：逐push H/R和actual remote readback一致；不明网络失败、mark写入失败、main推进分别记录真实状态，不把已经写入写成零写；全部broker/Controller组合、完整smoke、语法/ShellCheck与文档门真实执行。
- [ ] AC-6：本Issue人工UI首PR唯一且exact branch，local L与human H分层、tree/blob/mode等价、fresh main与CI实证；无未合并安装或directGit绕行，最终manual merge证据明确。
- [ ] AC-7：源码merge后，Mac及gitea-ci各获exact版本安装批准，读回完整受管组件前后SHA256/mode/owner、真实FF正反向/竞态路径、重复no-op和一次受控失败rollback；旧字节仅rollback停写，不再被用于leased publish。source/local/CI不能代替installed/live。
- [ ] AC-8：main保护/context/身份/单writer/唯一manualPR保持；不改业务项目、不代写#289/#319或重复建PR。安装AC完成及原owner真实采用前，不声称已解锁其Agent发表；人工更新不要求等待#327。

## 风险、回滚与完成边界

整合来源假冒、tree污染、hook/config注入、竞态、freshness窗口和installed差异是核心风险；对应AC-2～5/7均要求负向真实验证。source失败通过追加修复或独立revert PR，不force改历史。

两机安装以合并且稳定pin的source为唯一输入；安装card明确所有变化文件及缺失前态（含新增helper）、精确owner/mode、保存的旧文件集合与hash。不能仅恢复broker.py或信任`.previous`自动完整。rollback恢复完整前态，删除仅本版本新引入的受管文件并核验列表，保留证据；回滚后禁用本新发布路径，旧lease路径不重新获得合规许可。不得为验收创建新身份/PAT、扩大保护、服务/timer或部署。

安装AC只能在源码merge后闭合，故`Closes #327`的Gitea自动closed不等于本Issue真实完成。若源码合并自动关闭而AC-7尚缺，owner据已确认合同通过现有typed `gitea.issue.state.set`保持/恢复open并记录“source merged / installed acceptance pending”；不写completed、不触发runtime、不清理/归档。已有终态工具的自动source-only计划不能覆盖本合同AC。本项是该Issue的确定性验收保留，不新增通用终态机制。

AC实证全部满足后才terminal reconcile、文档check、精确cleanup/归档。本地L若不是merge祖先先保留可恢复bundle并验证human H等价，不能冒称已合并本地对象并强删；清理仍要对exact目标保全读回。

## 非目标

不在合同准备阶段修改治理，独立 T01 只按映射治理表应用；不恢复#319 remote、不更新#289 PR、不修其业务/UTF-8范围、不操作他人worktree。不开放任意merge、冲突解决、force、new operation参数、身份/PAT/保护/context/routine变更、应用部署或provider启用。不批量重命名/删除历史Change或上游skills。

## 未决问题

无；以上完整最小合同已由负责人直接确认。本轮只完成独立 T01 后 STOP，T02/T03 需后续 fresh run。真实UI发表/字节mode等价和guard竞态实证属于待执行AC，失败不得以替代路径伪造闭合。
