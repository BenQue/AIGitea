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
updated: 2026-10-06
status: approved
git_history_head: 3052a8a0d47a8c7333f06e073ca5a4ecc1047a90
git_history_paths:
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 04-Agent编排与定时任务.md
  - 06-运维手册与踩坑集.md
  - 08-双工具共存与实施.md
  - AGENTS.md
  - README.md
  - codex/runtime/aisoft_host_access/dependencies.py
  - codex/runtime/aisoft_host_access/profiles.py
  - codex/skills/aisoft-matt-workflow/SKILL.md
  - codex/skills/issue-session-flow/SKILL.md
  - docs/agents/issue-tracker.md
  - docs/changes/327-broker-ff-integration/plan-broker-ff-integration-261002.md
  - docs/changes/327-broker-ff-integration/spec-broker-ff-integration-261002.md
  - docs/changes/327-broker-ff-integration/summary-broker-ff-integration-261002.md
  - docs/changes/327-broker-ff-integration/verification-broker-ff-integration-261002.md
  - skill-for-claude/aisoft-platform/SKILL.md
  - skill-for-claude/issue-session-flow/SKILL.md
  - skill-for-codex/SKILL.md
  - skill-for-codex/references/private-gitea-access.md
  - templates/docs/agents/issue-tracker.md
git_scope:
  - codex/runtime/aisoft_host_access/broker.py
  - codex/runtime/aisoft_main_integration.py
  - codex/runtime/aisoft_loop/controller.py
  - codex/runtime/aisoft_worktree_owner.py
  - codex/runtime/aisoft_loop/gitea.py
  - codex/runtime/aisoft_host_access/runner.py
  - codex/install-host-access-broker.sh
  - codex/install-vm.sh
  - codex/tools/check-installed-drift.py
  - codex/runtime/tests/test_host_access.py
  - codex/runtime/tests/test_controller.py
  - codex/runtime/tests/test_worktree_owner.py
  - codex/runtime/tests/test_main_integration.py
  - codex/tests/test-host-access-broker.sh
  - codex/tests/test-install-host-access-broker.sh
  - codex/tests/test-installer-source-guard.sh
  - codex/tests/test-agent-runtime.sh
  - codex/tests/test-installed-drift.sh
  - codex/tests/fixtures/installed-drift/test-installed-drift.py
  - codex/tests/smoke.sh
  - docs/changes/327-broker-ff-integration/summary-broker-ff-integration-261002.md
  - docs/changes/327-broker-ff-integration/spec-broker-ff-integration-261002.md
  - docs/changes/327-broker-ff-integration/plan-broker-ff-integration-261002.md
  - docs/changes/327-broker-ff-integration/verification-broker-ff-integration-261002.md
---

# #327 当前最小 Git 合同（2026-10-05）

## 授权与优先级

本人在根聊天读完 #327/#333/#336 诊断后明确要求“按你的建议通知各个会话按此执行”。本 owner 收到的一次定向续办明确接受下述收缩，不重放 T10 批准，也不再请求同一方向确认。本轮只治理应用/校验/本地原子 commit 后 STOP；后续 fresh run 重读才实施。Issue #327、`change/327-broker-ff-integration`、owner `01a0fcec-eb78-7790-a36a-daea917f43d2`、worktree `/private/tmp/issue-327-broker-ff-integration`、complex/manual 不变。

本合同取代 T04–T10 中把本票 source 整合/首次发表绑定到 R02 qualified program、root authority、protected grant、begin/verify、ES/kernel/signing、完整 OS/解释器闭包和 scratch/resource 隔离的前置。原实现与验收记录保留；延期是新的明确范围决定，绝不改成 PASS。原 UI-only 逐文件首发也被本票本人标准 Git 路径替代，避免重建另一套 human SHA/history。Agent 禁令与 main 保护保持。

## 当前事实与保全

- 原 HEAD `f8750441f3dce96f3b9a24a134f877ad1cf6aa35`；tree `8f6935ca1b59f13ea2c0f36b4530b18eee75c3a9`；T10 只完成治理，没有整合 main。
- fresh canonical broker main `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`，共同基线 `dc9aa468580f92a73dfa054c6f04ef5113f56694`；旧目标 `e2edb3e08194624a6647212571c6cc866298575b` 仅为历史选择。
- installed broker 已读到模块 SHA256 `c865bd757a6213673d55e39dc64be46dfb02022e9baf76065f95849cb9a78260`，仍有 BASE_BRANCH_STALE、blanket MERGE_COMMIT_DENIED 和 lease-force。38 项 installed operations 无 begin/verify；managed verification bootstrap 不存在。不能沿旧 push 返回 PASS 推定新政策可用。
- 现有 `aisoft-platform-agent` 的 exact repo 权限为 non-admin pull/push；origin 与已安装 credential helper 绑定已核。main 禁直推/force，merge allowlist 仅本人 `admin`，required context 是 `CI / verify (pull_request)`。只读 transport 已通过；真实发布/安装没有执行。
- `git.fetch.change` 返回 HOST_COMMAND_FAILED；R0/R 精确值仍 GAP，不推断远端 ref 不存在，也不拿 `last_push_head=null` 作证明。首次发表前必须取得 same exact ref 的成功读回。
- HEAD、33 文件 WIP、17 治理文件、raw index、全部 refs 对象与 5,721 个原证据条目已经保全。恢复 tar 的 bytes/mode/uid/gid、独立 bare 仓库的 HEAD/parents/tree/ref targets 及复制 index entries 已实际验证。证据位于本 owner 的 `issue-327-convergence-20261005/preservation.json`（完整绝对路径见 verification）。

## 当前交付：只修 Git

R0 是已核验的原 remote tip（未知则 GAP，不重置）；R 为本次 exact ref tip；M 为本次 fresh manifest main；C 为已核验 Issue 第一父链末端；I 的两 parent 精确 `[C,M]`；H 为最终验证候选。原/current remote tip 都须为 H 祖先。仅承接经读回的 main 历史，不靠 message、同名 branch、owner marker 或本地 PASS 声称物理创作来源/不可伪造批准。

1. 允许无冲突标准 main 整合，保留所有已有 Issue/remote 历史。Controller 仍负责常规编排；Agent/provider 只追加线性本地 commit。本票首次自举允许**负责人本人**在原 worktree 用标准 Git 构造同样的两 parent 整合；不要求未交付 #327 runtime 先执行它自己的整合。拒绝 octopus、反序、侧向 other-change merge、criss-cross/缺对象/replace/graft/shallow、非默认 driver、额外 merge 内容及超出批准范围的 delta。冲突停止，不自动解决；合并 tree 用真实 Git 三方结果独立核对。
2. `git.push.change(branch)` 的 typed 参数、manifest 固定 repo/remote/identity/credential、现有单 writer 和最终 PR 授权保持。去掉 blanket merge deny，改为核完整 relevant DAG、允许的 `[C,M]`、tree/范围、fresh M、R0/R 祖先与锁定 H。不新增 public begin/verify/merge/approve 或 authority。
3. 仅单 ref 普通 FF，源绑定 exact H；无 force、lease-force、`+refspec`、main、mirror/all/delete 或 fallback。固定 pre-push guard 必须核传输公告的 remote old-id=R（首次为全零）、local-id=H、唯一 exact branch，并证明本次 guard 实际执行；不用可编辑 repo hook、任意程序或 caller PASS。公告后的服务端 old-id 检查负责后一个竞态窗口。此 guard 是最小 Git 修复的直接代码，不建设 root/OS 服务。
4. 拒绝远端非 FF、首次 ref 抢占、R1 恰为 H 祖先、删除重建、本地 H 移动与 guard 缺失/漂移。预检 H≠R 却 transport up-to-date 不能报本次写入 PASS。no-op 必须重新读 exact ref/main 并重验；成功后真实 remote=H 才记录。marker/网络/readback 不明保留 actual/possible H，不盲重推或伪称零写。
5. main freshness 无跨两 ref 原子保证：push 前再读 M；push 后若 main 前进，记录实际已发表 H 与 BASE_ADVANCED_AFTER_PUSH，停止 PR ready，追加整合/重验，不回退或 force。
6. fixed guard 的程序/hash/argv 及相关 Git 配置必须可核；不能通过不受控 hook/config 绕过门。现有主机/凭据/权限门继续有效。当前较大同 UID 恶意 provider、root custody、kernel 执行/加载证明不在本票可证明范围，不能对外宣称隔离已经实现。

## 精确实施范围（仅下一 fresh T02）

2026-10-06 fresh T02 将下表已有批准范围投影到 front matter 的 `git_scope`，供 committed mapped summary/spec 的逐 commit exact 路径检查使用。`git_history_head=3052a8a0d47a8c7333f06e073ca5a4ecc1047a90` 固定已由本人完成的两 parent 整合；`git_history_paths` 仅承接既有 18 治理文档和历史 T07 已提交的 `dependencies.py`/`profiles.py` 四行兼容修正，共 20 路径。它们不是新的修改范围、批准根或创作证明；missing/duplicate/wildcard/跨 Issue 映射均 fail closed。原 fresh `git_scope` 为 23 路径；本人随后直接“确认”新增下述一行测试数量映射，现为 24 个允许路径，实际修改仍须为其子集。

| exact 文件 | 当前允许目的 |
|---|---|
| `codex/runtime/aisoft_host_access/broker.py` | 恢复实际 Git push 路由，FF、完整 DAG/tree/范围、strict R guard、readback；不依赖 authority |
| `codex/runtime/aisoft_main_integration.py` | 复用既有 WIP 的纯 Git DAG/tree/guard 代码，移出本票当前流程对 root grant/closure 的耦合；无新服务/网络/凭据接口 |
| `codex/runtime/aisoft_loop/controller.py` | 常规本地整合与 broker 接线，保留 provider merge deny/单 writer/每次 H 验证 |
| `codex/runtime/aisoft_worktree_owner.py` | R0/last_push 的必要审计保全；不把 marker 升成授权根、不重 pin R0 |
| `codex/runtime/aisoft_loop/gitea.py`、`codex/runtime/aisoft_host_access/runner.py` | 仅必要的既有 typed fetch/push 接线；若无需修改则保持 |
| `codex/install-host-access-broker.sh`、`codex/install-vm.sh`、`codex/tools/check-installed-drift.py` | 仅最小 Git 模块/guard 的受管安装与漂移映射，不执行安装/启用、不改 source guard |
| `codex/runtime/tests/test_host_access.py`、`test_controller.py`、`test_worktree_owner.py`、`test_main_integration.py` | FF/DAG/竞态/owner/Controller 的真实 bare remote 与必要回归 |
| `codex/tests/test-host-access-broker.sh`、`test-install-host-access-broker.sh`、`test-agent-runtime.sh`、`test-installed-drift.sh`、`codex/tests/fixtures/installed-drift/test-installed-drift.py`、`codex/tests/smoke.sh` | 必要 fixture/受管文件映射与新增 Git 用例，不删除、skip 或弱化既有 required 门 |
| `codex/tests/test-installer-source-guard.sh` | 本人 2026-10-06 补充确认：仅来源数量预期 `+2`→`+3`，纳入新受管模块；来源闸门实现保持 |
| 本 Issue 四份 mapped docs | 真实证据与唯一 PR 回填，不把声明当验收 |

以上测试文件中不带完整前缀的 basename 均相对前一个相同目录，不能泛配目录。已保全 32 个源码 WIP 中与此表直接相关者复用；其余 authority/config/bootstrap/ES/toolchain/scratch 代码和测试明确延期，仍 UNDELIVERED。可在完整 bytes/mode/uid/gid 与补丁映射保全后按清单临时 park，不能 rm/reset 丢弃或 skip 原 required tests 制造 clean/PASS。更改范围外的 runtime 或新增机制必须先说明真实必要性，不能从旧宽合同继续扩张。

2026-10-06 默认 smoke 实跑在既有 `codex/tests/test-installer-source-guard.sh` 的来源数量断言停止：新增受管 `aisoft_main_integration.py` 后实际数量 34，旧测试预期仍为 33。仅将测试预期加数 `+2` 改为 `+3` 的一行补丁已在外部准备；该文件尚不在上表/`git_scope`，已向本人请求补充这一 exact 文件，未应用。`codex/lib/install-source-guard.sh` 的来源、staleness 和写入前闸门保持；当前结果仍是 FAIL，不删除/skip 或改变输出来制造 PASS。

上述为补充前停止记录，原失败保留。本 owner 会话随后对该一行补丁直接收到本人“确认”，已只应用 `+2`→`+3` 及受管模块说明，后续重跑默认 smoke；不继承旧 FAIL 为 PASS、不新增 push/PR/安装授权。

## 首次人工 main 整合与发布

本轮治理 commit 后 STOP。本人执行一次**仅本地**的标准 Git main 整合：先绑定实际治理 G/fresh M/owner、确认只有已保全 32 源码 WIP；用 `git stash push --include-untracked` 临时 park，保存不可变 stash SHA 与 bundle，禁止 pop/drop/clear；再 `git merge --no-ff --no-commit -s ort M`，无冲突且 index 只含 main 基线变化、parent/head 正确后由本人 commit `[G,M]`。失败 `git merge --abort`，保留 stash/恢复包/实际 HEAD；不 reset。实际成功后 fresh owner 按该 stash SHA 恢复/复用 WIP，必要的已知 main 变更只在独立源码步骤处理，不能把 clean checkpoint 当修复或测试 PASS。

精确可复制步骤放在本 owner 外部 `human-first-main-integration.md`，仅使用标准 Git 与已安装 broker 的只读 fetch，不安装或伪装 Controller/R02；实际 G 由本次治理 commit receipt 绑定，不在合同自引用。该步骤**不推送、不创建 PR**，R0/R 的当前 GAP 不被本地保全/整合伪造闭合。

fresh T02 完成最小修复并跑门 → T03 给出 exact C/M/R/H、tree/blob/mode、固定 guard hash/argv、完整恢复证据与唯一 PR 候选 → **唯一第二确认** → 本人经现有 manifest 绑定 helper 用普通 Git、exact H 单 ref 和已验证固定 guard 首次发表 → remote readback/唯一 PR/新 head+base required CI → 本人 manual merge。Agent 不 direct Git/API，也不沿旧 broker lease-force 或未合并安装自举。已有 helper 与 project push ACL 证明入口存在，不能冒称真实 FF/strict-R 已验收；T03 必须在实际最小代码上形成可执行的一条命令，缺证据保持具体 GAP，禁止扩建另一层系统。

## 验收与明确延期

| AC | 当前要求 / 历史处置 |
|---|---|
| AC-1 | exact 四文档/判级/授权/单 writer；本轮独立治理检查/commit/STOP，fresh 重读；live labels 未投影仍 GAP |
| AC-2 | bare remote 的创建/FF、合法两 parent 整合/重复整合、回填/CI repair/no-op；真实 R0/R/M/H/DAG/tree/范围 |
| AC-3 | 真实非 FF、R1 祖先/首创抢占/删除重建/公告后 race/本地 H 移动，零本次覆盖或如实 possible-write |
| AC-4 | 非法 DAG/parent/tree/范围/driver/缺对象/project/owner/branch/dirty/provider merge 均拒绝；物理程序来源/root-record 证明延期 |
| AC-5 | actual remote H、truthful no-op/失败回执/marker/main 推进；全 runtime discover、默认 smoke、shell bash-n/ShellCheck 与文档门真实运行 |
| AC-6 | 本人首次标准 Git 保留 history/模式/树与唯一 PR；exact final H/base required CI、manual merge、可恢复收尾；旧 UI-only 方式撤销 |
| AC-7 | 原两机 installed/authority/resource 验收仍 NOT RUN/GAP，明确延期；source PR 不等待 installed，不主动安装、不宣称已解锁其他 Agent 发表 |
| AC-8 | main 保护、required contexts、身份与单 writer、唯一 manual PR 不变；不代写其他 Issue/建立机械跨票 hard dependency |
| AC-9 | root authority/peer/custody/隔离/grant/record/replay/I02 延期，原 NOT RUN/GAP 不转 PASS |
| AC-10 | 完整 OS/解释器/loader/alias/cache closure、native pre-import/bootstrap、ES/kernel/signing 延期，原 FAIL/GAP/NOT RUN 保留 |
| AC-11 | scratch/rootGit/resource/own-lease/mount/capacity/crash/cleanup 隔离延期，原 FAIL/GAP/NOT RUN 保留 |

原全部合同/AC/FAIL 日志保存在原 Git 历史、33 WIP/17 治理恢复包及完整 original-evidence archive；当前未实现的条目不勾选通过。旧 1254 tests/7 FAIL/9 ERROR 保留，最新 smoke 是在 source staleness guard 前停止（runtime NOT REACHED）；不能拿 targeted/mock/unsigned 结果覆盖它们。延期项不作为当前 source PR/收尾硬依赖；本票按当前 source/Git/CI/人工发表与恢复范围验收，installed/live/安全能力继续单独标记 GAP/NOT RUN。

## 本轮 exact 治理范围与回退

独立修改原 14 个 #327 活治理消费者及四 mapped docs，共 18 个文档：`AGENTS.md`、`03-Issue-Spec-Plan与单闸门开发流程.md`、`04-Agent编排与定时任务.md`、`06-运维手册与踩坑集.md`、`08-双工具共存与实施.md`、`README.md`、`codex/skills/issue-session-flow/SKILL.md`、`skill-for-claude/issue-session-flow/SKILL.md`、`codex/skills/aisoft-matt-workflow/SKILL.md`、`skill-for-claude/aisoft-platform/SKILL.md`、`skill-for-codex/SKILL.md`、`skill-for-codex/references/private-gitea-access.md`、`docs/agents/issue-tracker.md`、`templates/docs/agents/issue-tracker.md`，以及本目录 summary/spec/plan/verification 的 exact 映射 basename。

只替换当前 #327 活合同与重复前置，保留无关条款、历史 #136 和原失败证据。verification 原 WIP 的历史证据正文保留并纳入本次文档提交，32 源码 WIP 原 bytes/mode/uid/gid 不动；不实现 runtime、不改 config/CI/installer、不更新全局 skills/标签、root/Secret/账号权限/服务/部署，不 push/PR/merge。治理失败只撤回本次已知文档增量及本次 index 项，留 HEAD 历史与所有恢复包；不 reset/force/覆盖他人 ref。成功实际提交后立即 STOP，原 T02 仍 in-progress、T03 pending，不新增 Ticket/Issue/系统。

## 2026-10-06 最小 Git source 实施证据

既有精确范围内完成相关 installed dispatch/FF 模块的只读版本绑定：固定 wrapper SHA 和本发行相关模块 bytes 比对在写调用前拒绝旧/mixed surface；这只证明 cooperative version 一致，不扩张成 root/OS/加载闭包。净化环境仅保留经格式校验的 owner session。启动后无有效回执、partial/坏JSON/坏编码/timeout 都保留有限非秘密候选 H 与 possible_write/UNKNOWN，成功 exact readback 前禁止盲重推。默认 smoke 原门保留；tracker相对链接先核相同真实目标、其余bytes仍严格一致。全门及历史FAIL按 verification 分层记录；真实首次发表仍须成功R读回与唯一最终第二确认。
