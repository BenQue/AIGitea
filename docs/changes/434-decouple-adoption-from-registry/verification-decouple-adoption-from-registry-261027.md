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
status: pending
branch: change/434-decouple-adoption-from-registry
created: 2026-10-27
updated: 2026-10-27
---

# Verification：通用流程采用与中央项目登记解耦

## 基线与范围

- Commit SHA：逐票记录在下表
- 基线：`origin/main` = `74dc5808`
- 环境：Mac 交互会话（Claude），平台源码 runtime；不连 live Gitea，不重装 broker
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-8

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T01 `bash codex/tests/smoke.sh`（发版 1.18.0 后） | PASS | 尾行 `Codex platform static smoke checks passed.`。首轮依次红在发布包成员不一致、导出技能在非维护层节点名平台路径、站点值渗入守卫（`gitea-ci`），逐项修正后转绿 |
| T02 `python3 -m unittest tests.test_project_declared_source`（`codex/runtime`） | PASS | 22 tests OK：声明 schema 12 种拒绝、remote 7 种拒绝（userinfo、SSH、他仓、子路径、分离 push URL、多 URL、insteadOf）、身份 7 种拒绝、闭集外操作在取凭据前拒绝、闭集 21 个操作全部成功、推送闸门（无分支、`main`、他 Issue、脏树、越界 scope、会话不符）、哨兵 token 不进 argv 与 env、注入助手文件 600/目录 700 且调用后删除、重定向一律不跟随、站点 broker 无视 `project.json`、入口拒绝 `--project` |
| T02 站点来源回归 `python3 -m unittest tests.test_host_access tests.test_host_access_complete_reads tests.test_main_integration` | PASS | 抽出两个钩子方法后 240 tests OK |
| T02 `bash codex/tests/smoke.sh`（发版 1.19.0 后） | PASS | runtime 全集 768 tests OK，新测试在其中；尾行 `Codex platform static smoke checks passed.` |
| T02 导出工具包依赖闭包：按 `usage/bundle.json` 只复制 `.aisoft/` 成员到空检出，`env -i` 运行 `.aisoft/bin/aisoft-access --operation gitea.issue.read --number 1` | PASS | 导入链完整，停在凭据阶段 `CREDENTIAL_UNAVAILABLE`、exit 20；未访问平台检出或 `/usr/local` |
| T02 `shellcheck` 与 `bash -n codex/tools/aisoft-access` | PASS | 无输出 |
| T03 `python3 -m unittest tests.test_project_source_tools`（真实 HTTP：FakeGitea REST 加 `git http-backend`，只认项目凭据） | PASS | 8 tests OK：`labels-provision` 空仓对齐且幂等；`classify --apply/--verify` 投影并读回 projected；`open-pr` 首推、建 PR、回填 `pr_url`/`pr-open`、再推，Git 端 Basic 认证全部来自注入助手（无 other）；`prepare-ticket` 的 `read_issue` 走项目入口；`resolve-route` 读项目声明的 `change_control`（声明 development 后旧卡被判冲突，声明他仓被拒）；`project-check --remote` 输出 `PASS: access-identity`、两条 `MANUAL` 与 `manual=2`，管理员身份时 `GAP: access-identity`；声明检出上 `--project` 被拒；两种来源指向不同仓库时停止 |
| T03 `python3 -m unittest tests.test_project_declared_source tests.test_route_policy tests.test_change_control tests.test_ticket_execution` | PASS | 67 tests OK |
| T03 `bash codex/tests/smoke.sh`（发版 1.20.0 后） | PASS | runtime 全集 776 tests OK；站点来源的 open-pr、classify、complete、project-check 既有回归全部通过，`result:` 行在无 MANUAL 时与本批前同形 |
| T04 `python3 -m unittest tests.test_project_source_e2e` | PASS | 3 tests OK。真实 `usage-bundle.sh --adopt --tools claude` 导出工具包，项目只有 `.aisoft/project.json`；平台 manifest 环境变量指向不存在的路径，无 `.agent.env`；每次调用都套 `sandbox-exec`，拒读平台检出与 `/usr/local/{libexec,share,lib,etc}` 下的 aisoft 安装面。依次走通：`labels-provision`；`aisoft-access` 建 Issue、读 Issue；`classify --apply/--verify`；生命周期 `approved`；`prepare-ticket`；ticket commit 后 `review-candidate`；`open-pr`（首推、建 PR、回填、再推）；`gitea.pull.read`；`gitea.commit.status.read`；PR 置为已合并后 `complete --apply` 写 `completed`，重跑 `no-op`。`application-deploy` 加 verification 分支为 `requires-deployment`，不写 completed；声明 `development` 后路由按声明重算。Git 端 Basic 认证全部来自注入助手 |
| T04 反向证明（逐项临时改源码，跑对应测试后 `git checkout --` 复原） | PASS | 删去 site-admin 拒绝：`IdentityTest` 2 failures；删去 repo-admin 拒绝：2 failures；在 Git 环境里注入 token：`test_git_credential_reaches_git_only_through_the_injected_helper` 1 failure；让 `change_branch` 接受 `main`：`test_push_refusals_still_apply` 1 failure；同时删去入口闭集检查并把声明合同扩成全部操作：`ClosedSetTest` 7 failures、4 errors。只删入口检查时仍 OK，因为声明合同本身只含闭集，这是第二道闸门 |
| T04 `bash codex/tests/smoke.sh` | PASS | runtime 全集 779 tests OK（含 11 条新 E2E/工具测试）；尾行 `Codex platform static smoke checks passed.` |
| T01 残留表述 rg（`登记与采用|先.{0,6}登记|必须先登记|新项目登记|登记新项目|已注册项目|登记进平台`，排除 `docs/changes`、`archive`、`codex/vendor`、`usage/releases`） | 已判定 | 见下表 |

T01 残留表述判定：

| 位置 | 判定 |
|---|---|
| `AGENTS.md:8`「换成任意一个已注册项目还成立吗」 | 保留：平台维护层的准入问法，与 ADR 0001 D4 同源，不构成采用前置；本 spec 未授权改 `AGENTS.md` |
| `docs/adr/0001-platform-boundary.md:49`、`:81` | 历史决策原文保持；ADR 0003 补充而不撤销 |
| `docs/governance/remediation-roadmap.md:22` | 历史整改路线证据，保持原样 |
| `architecture/README.md:250` | 描述 reference profile 不对应任何项目，与登记前置无关 |
| `docs/adr/0003-*` 命中 | 本 ADR 引述被取代的旧条款 |
| `greenfield-planning.md:12`、`:18` | 已改为「采用」，去掉登记前置 |
| 技能、getting-started、onboarding-runbook、project-align、execution-adapter、issue-session-flow、使用合同、用户手册、项目 AGENTS 模板 | 已改为三层职责；保留的 broker 表述均限定为站点来源或「当前来源的 typed 操作入口」 |

命令与输出照实抄。改动前才观测得到的证据（基线状态、改动前后对比、先看着测试红）
只有写在这里才留得下来——改动合并后就无法重放。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | T01：ADR 0003 写明三层职责与 D3–D9，并列出取代的旧条款；技能、execution-adapter、getting-started、onboarding-runbook、project-align、issue-session-flow、使用合同、用户手册、项目模板已同步；残留表述逐条判定见上表 |
| AC-2 | PASS | 下文「入口清单」；T03/T04 测试覆盖每个工具入口 |
| AC-3 | PASS（合成环境） | T04 端到端测试 |
| AC-4 | PASS | T02 声明、remote、身份、闭集、推送拒绝与 token 卫生测试；站点回归在 T02、T03、T04 三次全量 smoke 中通过；T04 反向证明 |
| AC-5 | PASS | T03 冲突与 `--project` 拒绝测试；站点来源既有回归不变；下文「迁移与回滚」 |
| AC-6 | PASS | T01：onboarding-runbook §0、§0.1「接入既有项目」八步；getting-started 第 3 步改为可选 |
| AC-7 | PASS | 发布包 1.18.0（T01 文档）、1.19.0（T02 引擎闭包、入口、schema、模板、标签集合）、1.20.0（T03 工具接线）、1.21.0 与 1.21.1（交叉审查修复）；T04 用 `--adopt` 导出的包跑通即证明闭包齐全。`aisoft version` 在项目布局读 provenance，由既有 smoke 覆盖 |
| AC-8 | 已记录 | 下文「未验证边界」 |

### 入口清单（AC-2）

本批之前要求中央登记的入口，以及处置方式：

| 调用入口 | 操作 | 来源处置 |
|---|---|---|
| `aisoft open-pr` | `git.push.change`、`gitea.pull.create` | 两种来源通用（`resolve_access` → `aisoft_access_invoke`） |
| `aisoft classify`（`apply-classification-labels.sh`） | `gitea.issue.read`、`gitea.issue.labels.read`、`gitea.issue.labels.classify` | 两种来源通用 |
| `aisoft complete`（`mark-completed-issues.sh`） | `gitea.issue.labels.set` | 两种来源通用；项目来源从 `project.json` 读取 `deployment_lifecycle` |
| `aisoft project-check --remote` | 项目来源：`gitea.labels.read`、`gitea.issue.list`、`gitea.repo.read`；站点来源：`.agent.env` 直读，不变 | 分支处理；保护相关检查在项目来源下输出 `MANUAL` |
| `prepare-ticket` / `review-candidate`（`ticket_execution.read_issue`） | `gitea.issue.read` | 两种来源通用 |
| 路由（`route_policy.repository_context`、`change_control`） | 无远端 | 项目来源读取 `project.json` 的 `change_control` |
| `aisoft-project-target.sh` | 无远端 | 先看 `project.json`；站点解析原样保留，只用于冲突判定 |
| 新增 `aisoft labels-provision` | `gitea.labels.provision` | 两种来源通用 |
| 技能直接调用（`gitea.issue.create/list/comment/comments.read/update`、`git.fetch.main/change`、`gitea.pull.read`、`gitea.commit.status.read`、`gitea.actions.*`） | 同左 | 项目来源经 `.aisoft/bin/aisoft-access`，站点来源经 broker |
| getting-started 第 3 步、runbook §1.1、技能「一切访问走 broker」 | — | T01 改写；§1.1 只适用于站点加固访问 |
| `host.*`、`orbstack.*`、`mac.git.bind`、`gitea.credential.rotate`、`gitea.protection.read`、`gitea.dependency.read`、`gitea.labels.extension.define`、`gitea.issue.labels.extension.set`、`gitea.issue.state.set`、`gitea.pull.update` | — | 仅站点来源。按源码核对，技能、模板、使用合同与会话工具里没有调用后四个项目级写操作；`gitea.protection.read` 只出现在维护层盘点里 |

源码核对与 spec D6 表的差异：`aisoft open-pr` 的编号取自 `gitea.pull.create` 的回执（第 3 轮评审 MINOR 已删去 `pulls.read`）；`aisoft complete` 只调用 `gitea.issue.labels.set`；`project-check` 在项目来源下另需 `gitea.issue.list`，用于 Issue 引用清单，该操作已在闭集内。

### 迁移与回滚（AC-5）

- **已登记项目**：不需要任何动作。没有 `project.json` 时，所有工具的行为与本批之前相同（站点回归全量通过）。合并后由维护者在 Mac 与 OrbStack VM 两台重装 broker，已登记项目才会用上新引擎字节；重装之前，漂移检查报差异属于预期。
- **已登记项目改用项目来源（可选）**：先按 runbook §0.1 第 2、3 步准备非管理员项目身份与保护证据，再写 `project.json`。回退方法是删除该文件，自动回到站点来源。
- **未登记项目**：采用 1.20.0 及以后的发布包并写 `project.json`。回退方法是用 `--adopt` 恢复上一版兼容工具包；恢复不了就停止远端写入。已经正常创建的 Issue 与 PR 不撤销。
- **平台回滚**：revert 本批 PR，由维护者按 revert 后的字节重装两台 broker。

### 未验证边界（AC-8）

- 真实 Gitea 1.26.4 下 `/user` 与 `GET /repos/{owner}/{name}` 的 `permissions` 响应形状：NOT RUN。只有源码依据（第 2 轮评审引用的官方路由与 convert），没有 live 读回。
- 已安装 broker 的两台重装：NOT RUN。需要 sudo，由维护者执行。
- 真实项目上的 live 采用与 canary：NOT RUN，不在本票范围。
- 合成 Gitea 桩与 `git http-backend` 通过，只证明本平台代码路径成立，不证明真实 Gitea 上可用。

## 交叉审查

仅平台仓 complex 变更保留本节（`03` §7「交叉审核」）；项目仓整节删除。每轮一行，`exact head` 写 40 位 SHA，
实现方与审查方不能是同一提供者。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 合同 1 | claude | codex（gpt-6-astra，high，只读） | f2f24f022ebd670224583c20ababe2270a64a1fd | REJECT | 3 BLOCKER（direct 写入前无身份硬门；无登记后项目策略无机读来源；installer 约束自相矛盾）、10 MAJOR、1 MINOR，共 14 条。处置：放弃另写 direct 传输，改为同一 broker 引擎加项目自声明来源（spec D3–D7），治理先行（plan T01），补全入口清单、反例、回滚与未验证边界，修复本文件模板残片 |
| 合同 2 | claude | codex（gpt-6-astra，high，只读） | fcd5eacfbe0bd63260f5e8a2216837416ae74a63 | REJECT | 第 1 轮 14 条：6 RESOLVED、8 PARTIAL。新发现 1 BLOCKER（单项目来源最小合同与站点入口边界未定）、6 MAJOR（路由 change_control 与模板 git_scope 消费者；身份检查只在项目来源且绑定同一凭据；project-check 站点不变与项目分支冲突；发布包依赖闭包与入口表；complete 只 dry-run；不存在的同号重发）、2 MINOR（D7 证据格式；轮 1 计数笔误）。处置：spec 新增项目上下文映射表与入口操作闭集表，站点 wrapper 固定站点来源、新增项目入口 aisoft-access；身份检查限项目来源、同一内存凭据经注入助手供 Git 写入、按完整 origin 判重定向、写明 PAT scope；project-check 两来源分支与 MANUAL 结果值；路由读项目 change_control，模板持有路径在项目来源拒绝；AC-3 增 review-candidate、complete --apply 幂等与 development 路由；AC-7 列依赖闭包；发版改为逐票递增；D7 证据字段与 protection_evidence；更正计数 |
| 合同 3 | claude | codex（gpt-6-astra，high，只读） | dd50967aa5b12130e3019c123e8e7f48c8d9a372 | ACCEPT WITH CHANGES | 第 2 轮 9 条全部 RESOLVED；无 BLOCKER、无 MAJOR。3 条 MINOR 已处置：AC-3 第 9 步注明只证明路由消费、推送仍要求 spec；open-pr 编号沿用 pull.create 回执，删去 pulls.read；删去开放式薄包装预留，只保留 labels-provision |
| 实现 1 | claude | codex（gpt-6-astra，high，只读） | ed5d1f4853ee92df61af4904849373500ff3dde4 | REJECT | 2 BLOCKER、8 MAJOR、2 MINOR，逐条核实成立，一次修复，每条先有会红的测试：B1 Git 跟随重定向，凭据会发往新 origin：Git 环境加 `http.followRedirects=false`，注入助手只回应声明的 protocol/host/path（`test_git_redirect_never_carries_the_credential`、`test_injected_helper_refuses_any_other_target` 红→绿）；B2 助手路径 shell 注入：改为随包的 `project_git_helper.py`，参数全部 `shlex.quote`（`test_helper_path_with_shell_metacharacters_stays_inert` 红→绿，并对旧实现单独复红）；M3 参数缩写覆盖标签清单：`allow_abbrev=False`，并删去 `--label-manifest` 参数，路径固定在 runtime 旁（`test_entry_refuses_abbreviated_internal_options`）；M4 凭据未按仓库路径取：`git -c credential.useHttpPath=true credential fill`（`test_credential_fill_asks_for_the_exact_repository_path`）；M5 站点 `open-pr --repo` 丢了 cwd：恢复 `cd $repo`（`test_site_open_pr_runs_the_broker_inside_the_target_checkout`）；M6 冲突只比短名：改为比较完整目标 URL，并要求声明的 `owner/name` 与 remote 一致，`project-check` 也走共享解析（`test_same_short_name_under_another_owner_and_host_is_a_conflict`）；M7 闭集多开了 `gitea.pulls.read`：删除（`test_pulls_read_is_outside_the_closed_set`）；M8 残留登记前置表述：issue-session-flow 派单、使用合同 `change_control` 与 §8、route-policy 查表输入、project-align 第 9 行、onboarding §1.1 两句、CI 模板注释；M9 E2E 的 PR head 与 status 假绿：桩改为读 bare remote 的真实 tip，断言最终 HEAD、remote tip、PR head 三者一致，旧 SHA 的 status 为 `HTTP_404`；M10 development 缺成功路径：新增 `test_development_project_prepares_the_synthetic_ticket`，`resolve-route` 无差异且 `prepare-ticket` 得 `complex-development`；m11 全局 URL 改写：改用用户自己的全局与系统配置检查，只拒绝覆盖声明 URL 的改写（`test_global_rewrite_of_the_declared_remote_is_refused`）；m12 计数更正。修复后发布包 1.21.0，smoke 789 tests 全绿 |
| 实现 2 | claude | codex（gpt-6-astra，high，只读） | 2f8b9fa0ec9d54f80899fcbf53bdeaeae645006d | REJECT | 第 1 轮 12 条中 10 条 RESOLVED，2 条 PARTIAL。MAJOR：站点解析出现多个候选时失败被当成「未命中」，回落到项目来源继续写入。处置：站点解析器新增 `AISOFT_PROJECT_TARGET_MISS`，只有「没有 manifest」或「没有 remote 匹配」才算未命中，其余失败一律停止（`test_ambiguous_site_match_stops_instead_of_falling_back` 红→绿，断言零请求、零标签）。MINOR：本地 `http.<url>.followRedirects=true` 会覆盖注入值。处置：项目来源拒绝任何 URL 专属的 followRedirects 配置（`test_url_specific_redirect_override_is_refused` 红→绿）。修复后发布包 1.21.1，smoke 791 tests 全绿 |
| 实现 | 待填写 | 待填写 | 待填写 | NOT RUN | 待填写 |


## 执行裁决

- T02 Ruling：`project.json` 增加 `schema_version: 1` 必填键。映射表未列，但精确键集合没有版本键就无法演进。代价：多一个键。
- T02 Ruling：项目来源对每次调用都读回身份，读操作也读回。spec 只要求写前读回；这样更严，且同一份凭据只取一次。代价：每次调用多两次 GET。
- T02 Ruling：项目来源一律不跟随重定向，REST 与 Git 都如此（Git 一侧经交叉审查补上 `http.followRedirects=false`）。spec 只要求 origin 变化时拒绝；一律不跟随更严，也更简单。代价：Gitea 前置代理若对同源做 3xx 改写，会被拒绝。
- T02 Ruling：站点来源抽出 `_git_credential_environment` 与 `_template_context` 两个钩子，供项目来源覆盖，行为逐字节不变，由 240 条站点回归与全量 smoke 证明。代价：站点代码多两层间接调用。
- T02 Ruling：凭据交给 Git 的方式，是 mode 700 临时目录里一个 mode 600 文件，由随包的 `project_git_helper.py` 只在请求与声明目标完全一致时读出，调用结束即删除。spec 首选管道，允许落盘时用 600 并删除；Git 不向 helper 传递额外 fd。代价：进程被强杀时，文件可能残留到系统清理临时目录。
- T03 Ruling：来源选择放在共享库 `aisoft-project-target.sh` 的 `aisoft_resolve_project_target` 里，新增 `aisoft_access_invoke`；三个 shell 工具与 `read_issue` 都经它分派，不各自判断。代价：这个库多了一条项目分支。
- T03 Ruling：`project-check --remote` 在项目来源下用 `api_get_project` 把标签与 Issue 两类 REST 读取映射到 `gitea.labels.read`、`gitea.issue.list`，`check_remote_labels` 的判断逻辑原样复用；新增 `access-identity` 检查行，`MANUAL` 只在项目来源出现，`result:` 行只在 `manual>0` 时追加计数。代价：分页由一次全量读取模拟。
- T03 Ruling：`complete --apply` 的真实终态写入链放到 T04 端到端测试中验证（它需要合并后的主干状态）。T03 只覆盖 `--project` 拒绝与来源分派。
- T04 Ruling：新测试都在 `codex/runtime/tests` 下，由 smoke 的 `unittest discover` 自动执行（日志里能看到 11 条），不需要再在 smoke 里单独登记。
- T04 Ruling：端到端测试用真实 `--adopt` 导出（`--tools claude`），而不是手工复制 `.aisoft/` 成员。手工复制漏掉了技能里的 route-policy 落点，路由会失败，所以这次导出本身就是闭包证据。
- T04 Ruling：「未访问平台安装面」由 `sandbox-exec` 拒读来证明。没有 `sandbox-exec` 的平台只剩环境变量隔离，证据较弱。
- 收口 Ruling：spec front matter 补上 `git_scope`（取自 `git diff --name-only 74dc5808`；首版 35 个文件，交叉审查修复后为 38 个），这是推送闸门需要的范围投影，不改变任何决定或 AC。代价：如果交叉审查后的修复又碰到新文件，要同步扩充并在此记录。
- T02 Ruling：发布包另带 `project_cli.py` 与 `codex/config/project-declaration.schema.json`（schema 由测试钉成与加载器一致）。

## 遗留风险与未完成项

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
