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
branch: change/434-decouple-adoption-from-registry
created: 2026-10-27
updated: 2026-10-27
---

# Plan：通用流程采用与中央项目登记解耦

## 全局约束与接口

- 依据：spec 的 D1、D2 是负责人已裁决的事项；D3–D10 经确认点 1 确认后，成为本计划的约束。
- 站点登记来源（引擎）：manifest schema、操作表与全部校验保持不变，回归必须全量通过。哪张票要改站点来源的行为，就停下来升级。
- 站点登记来源（manifest 与凭据）：已登记项目的 manifest 条目不改；不改 live 标签与保护规则；不新建凭据；不安装、不重装。
- 测试只用合成样例：本地 bare 仓库，加上 `127.0.0.1` 随机端口上的进程内 Gitea API 桩，以及 `codex/tests/fixtures/manifests` 下的合成夹具 manifest。不连 live Gitea，不借用真实项目。
- 无平台环境的测试：在临时 HOME 中运行，PATH 里没有平台检出，没有 `/usr/local` broker，也没有 `.agent.env`。断言全程未读这些路径。
- 发布包：凡是改动发布包成员的票，都在同一票内用 `usage-bundle.sh --release` 发一个递增的新版本，让该票的全量 smoke 能通过。现有工具拒绝不大于最新的版本号，所以不重发同号，整批允许出现多个版本。
- 治理步骤：T01 是独立的治理步骤，commit 后 STOP；fresh run 重读合同、治理 diff 与当前规则后，再做 T02。
- 每张票完成后运行 `bash codex/tests/smoke.sh`；改过的 shell 跑 `bash -n` 与 ShellCheck；改 runtime 前先 rg 测试目录，查看被钉住的活文档短语。
- 执行入口：Claude 使用 superpowers `executing-plans`，Txx 是唯一任务身份。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理先行：ADR 0003 与全部活文档、技能、使用合同、项目模板改为三层职责 | - | done |
| T02 | 引擎项目来源：单项目加载与映射表、项目入口 `aisoft-access`、remote 与同一凭据绑定、身份读回、操作闭集，合成回归，同票发版 | T01 | done |
| T03 | 会话工具接线与发版：全部入口改为经来源选择调用引擎，引擎与模板进入发布包 | T02 | done |
| T04 | 端到端回归与收口：无平台环境走完流程、兼容夹具、反向证明、verification | T03 | pending |

## T01：治理先行

- **交付/范围**：
  - 新增 `docs/adr/0003-adoption-access-decoupling.md`，写明三层职责与 D3–D9，并列出取代的旧条款。
  - 按 ADR 修改以下文件：
    - `skills/aisoft-platform/SKILL.md`
    - 该技能的 references：`execution-adapter.md`、`getting-started.md`、`onboarding-runbook.md`（拆成两部分，新增「接入既有项目」）、`project-align.md`
    - `skills/issue-session-flow/SKILL.md`
    - `usage/CONTRACT.md`、`usage/USER-GUIDE.md`
    - `templates/project/AGENTS.md`（在项目事实中写明访问来源与保护证据位置）
  - 本票不改代码。
- **blocked_by**：无。
- **AC**：AC-1、AC-6。
- **接口/约束**：
  - ADR 正文不得出现代码围栏、HTML 注释或原始 HTML 块（D3 守卫）。
  - 不写任何项目名。
  - 不手写 README 的日期与版本。
  - 技能与使用合同属于发布包成员，本票按全局约束发版。
- **验证**：
  - 运行全量 smoke 与 D3 泄漏守卫。
  - 用 rg 逐项列出所有包含「登记」「注册」「broker」「manifest」的活文档行，人工判定每一行属于以下三类之一：已改为三层职责、仅限站点加固访问、历史证据保持原样。判定结果写进 verification。
- **Expected**：守卫为绿；每一处残留表述都有判定。本票不覆盖代码行为。
- **停止条件**：治理文件 commit 后 STOP，fresh run。

## T02：引擎项目自声明来源

- **交付/范围**：在 `codex/runtime/aisoft_host_access` 中实现以下各项：
  - `project.json` 的精确 schema，以及按 spec「项目上下文映射」构造单项目上下文的加载函数（D4、D5）。
  - 项目入口 `.aisoft/bin/aisoft-access`；站点 wrapper 保持固定使用站点来源（D5）。
  - remote 校验；同一份内存凭据同时供 API 与 Git 写入使用，Git 写入经引擎注入的凭据助手；token 卫生；按完整 origin 判定重定向（D6）。
  - 项目来源专属的身份读回、spec 闭集表与模板持有路径拒绝。
  - 运行依赖闭包进入发布包，同票发版（AC-7）。
  
  站点登记来源的代码路径保持原样，不改。
- **blocked_by**：T01。
- **AC**：AC-4、AC-5（引擎部分）。
- **接口/约束**：
  - 回执 JSON 形状与站点来源同一操作保持一致，上层工具不区分来源。
  - 不新增调用方参数，不接受 URL、token 或路径输入。
- **验证**：
  - 新增 `codex/runtime/tests/test_project_declared_source.py`，用合成 bare 仓库与 API 桩，覆盖 AC-4 列出的全部反例，并逐行覆盖 spec 闭集表中所有操作的成功路径，同时加入哨兵 token 断言。
  - 用导出的项目工具包，在无平台环境中运行 `aisoft-access` 的一个读操作，确认依赖闭包齐全。
  - 运行站点来源的现有 runtime 测试全集与全量 smoke。
- **Expected**：反例逐个被拒绝，成功路径通过，哨兵零命中，站点来源回归无差异。本票不覆盖真实 Gitea 的响应形状。
- **停止条件**：
  - 必须改变站点来源的行为；
  - 某个操作无法在不传 token 参数的前提下完成；
  - Write 级身份无法读到 `/user` 或仓库 permissions。

## T03：会话工具接线与发版

- **交付/范围**：以下入口改为经来源选择调用引擎：
  - `codex/tools/aisoft` 的 `open-pr`；
  - `apply-classification-labels.sh`；
  - `mark-completed-issues.sh`，其中 `deployment_lifecycle` 改为从当前来源读取；
  - `ticket_execution.read_issue`；
  - `aisoft project-check --remote`：站点来源保持现有行为，包括 `.agent.env`；项目来源改走 `aisoft-access` 的读操作，按 spec D7 输出身份检查、`MANUAL` 与 GAP。
  - 路由上下文：`route_policy` 与 `change_control` 在项目来源下从 `project.json` 读取 `change_control`。
  
  `aisoft-project-target.sh` 只在站点来源下使用。新增子命令只有 `aisoft labels-provision`。引擎、schema 与 `project.json` 模板进入 `usage/bundle.json`，同票发版。
- **blocked_by**：T02。
- **AC**：AC-2（工具入口）、AC-5、AC-7。
- **接口/约束**：
  - 子命令参数不变。
  - 没有 `project.json` 时，行为与本批之前逐字节一致。
  - 新增 `project-check` 检查项时，按项目已记录的「新增检查项清单」同步计数字符串与 mock 变量。
- **验证**：
  - 扩展现有 open-pr、classify、complete、prepare-ticket、review-candidate、project-check 的测试，每个入口覆盖三种情形：项目自声明、站点来源、两者冲突。
  - 路由测试覆盖项目来源声明 `development`。
  - `project-check` 覆盖 `MANUAL` 计数与缺失证据时的 GAP。
  - 发版后运行 `aisoft version`，确认 `tool-provenance` 读回新版本。
  - 运行全量 smoke。
- **Expected**：
  - 站点来源的期望输出不变；
  - 项目自声明来源走 API 桩；
  - 冲突时停止；
  - 版本读回一致。
- **停止条件**：站点来源出现任何行为差异；发版规则要求改动已发布的版本。

## T04：端到端回归与收口

- **交付/范围**：
  - 新增端到端测试：用导出的项目工具包，在无平台环境中按 spec AC-3 的九步走完流程；同一测试中再证明已登记夹具项目仍走站点来源。
  - 在 verification 中写入：入口清单表（AC-2）、迁移与回滚说明（AC-5）、未验证边界（AC-8），以及执行结果。
- **blocked_by**：T03。
- **AC**：AC-2、AC-3、AC-5、AC-8。
- **接口/约束**：把测试登记进 smoke，按项目已记录的「smoke 登记新工具的 5 处」清单逐处同步，最容易漏的是测试执行区。
- **验证**：
  - 运行端到端测试与全量 smoke；
  - 做反向证明：分别删掉 admin 身份拒绝、推 `main` 拦截与 token 卫生断言，确认对应测试变红后再恢复。
- **Expected**：
  - 端到端测试为绿；
  - 三个反向证明各自变红；
  - 以下三项在 verification 中记为 NOT RUN 并写明原因：真实 Gitea 兼容、broker 重装、live 读回。
- **停止条件**：同一根因连续三次失败。

## Expected touch points

- T01：`docs/adr/0003-*`、`skills/aisoft-platform/**`、`skills/issue-session-flow/**`、`usage/CONTRACT.md`、`usage/USER-GUIDE.md`、`templates/project/AGENTS.md`、`usage/bundle.json` 与发布记录、被钉住短语的测试。
- T02：`codex/runtime/aisoft_host_access/*`、`.aisoft/bin/aisoft-access` 的源文件、新测试文件、合成夹具、`usage/bundle.json` 与发布记录。
- T03：
  - 工具：`codex/tools/aisoft`、`apply-classification-labels.sh`、`mark-completed-issues.sh`、`aisoft-project-check.sh` 与 `test-project-check.sh`、`codex/agent/aisoft-project-target.sh`
  - runtime：`codex/runtime/aisoft_loop/ticket_execution.py`、`route_policy.py`、`change_control.py`
  - 发布：`usage/bundle.json` 与发布记录、`project.json` 模板与 schema
- T04：端到端测试、`codex/tests/smoke.sh`、本目录的 verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | T01 文档 diff review、残留表述判定表 |
| AC-2 | T04 verification 入口清单表、T03 入口测试 |
| AC-3 | T04 端到端测试 |
| AC-4 | T02 `test_project_declared_source.py`、站点来源现有回归、T04 反向证明 |
| AC-5 | T03 三情形测试、T04 兼容夹具、verification 迁移与回滚说明 |
| AC-6 | T01 onboarding 与 getting-started 的 diff review |
| AC-7 | T03 发版，以及 `aisoft version` 与 `tool-provenance` 读回 |
| AC-8 | T04 verification 未验证边界一节 |

## 执行证据

<!-- execution-evidence:start -->
尚未执行。实际记录 ticket_base、起始状态、provider/入口来源、验证结果、candidate_head、
审查范围与 findings；可引用本 Issue 映射 verification，不另建证据权威。
<!-- execution-evidence:end -->

语义摘要仅排除图中的 Status 单元、updated 与这段成对标识的执行证据；原始全文摘要另存审计。
标记不得嵌套、重复或包住任务图/正文/约束。正常状态推进、补证不改变任务语义；
AC/依赖/命令/Expected/约束变化必须报告，不能静默续跑。具体规则见平台 execution-adapter。

## 部署与回滚

本批不涉及应用部署。

- 合并后，需要由维护者在两台机器上重装 broker，使已安装引擎与源码一致。本批不执行重装，记为 NOT RUN。
- 回滚：revert 本批 PR，并由维护者按 revert 后的字节重装 broker。项目侧按 spec AC-5 处理。
