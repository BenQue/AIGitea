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
  - agent-governance
  - platform-governance
  - external-contract
depends_on: []
branch: change/434-decouple-adoption-from-registry
created: 2026-10-27
updated: 2026-10-27
---

# Plan：通用流程采用与中央项目登记解耦

## 全局约束与接口

- spec 的 D1–D8 是已批准决定，执行中不再重议。
- 不改 broker：manifest、操作表、`codex/runtime/aisoft_host_access` 与 installer 的字节一律不动。哪张票发现必须改 broker，就停下升级。
- 不改已登记项目的 manifest 条目，不改 live 标签与保护规则，不新建凭据，不安装。
- 测试只用合成样例：
  - 本地 bare 仓库，加一个进程内 Gitea API 桩，地址是 `127.0.0.1` 上的随机端口；
  - 合成夹具 manifest 放在 `codex/tests/fixtures/manifests`。
  
  不连 live Gitea，不借真实项目。
- token 卫生：凡是测试 direct 传输的用例，都断言哨兵 token 不出现在 stdout、stderr、子进程 argv 和环境变量里。
- 治理文件（技能、ADR、`templates/project/AGENTS.md`）放在 T04，单独 commit 后 STOP；fresh run 重读后再做 T05。
- 每张票完成后跑 `bash codex/tests/smoke.sh`，改过的 shell 跑 `bash -n` 与 ShellCheck。
- 执行入口：Claude 用 superpowers `executing-plans`，Txx 是唯一任务身份。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 传输层：共用前置校验 + direct 传输实现 13 个 typed 操作，合成样例回归 | - | pending |
| T02 | 会话工具接入传输选择：`access.json` 解析、open-pr/classify/complete/labels-provision、兼容路径 | T01 | pending |
| T03 | `project-check` 的 `access` 检查与使用发布包发版 | T02 | pending |
| T04 | 治理文档：ADR 0003、技能、上手指南、onboarding「接入既有项目」、项目 AGENTS 模板 | T03 | pending |
| T05 | 端到端回归与入口清单：无平台记录的样例走完流程，兼容夹具不变，verification 收口 | T04 | pending |

## T01：传输层

- **交付/范围**：
  - 在 `codex/runtime/` 新增一个传输模块：一份前置校验，以及 broker 与 direct 两个实现。
  - broker 实现只是转调已安装的 broker，参数与回执形状保持原样。
  - direct 实现用 `git` 与 Gitea REST，并按 D5 取凭据。
  - 不包含工具接线。
- **blocked_by**：无。
- **AC**：AC-3（传输部分）、AC-4（闭集拒绝）。
- **接口/约束**：
  - D4 闭集与 D5 凭据边界。
  - 回执形状与 broker 同一操作的 JSON 一致，上层工具不区分传输。
  - 新共享 runtime 模块按「共享 runtime 模块 6 处清单」同步两个 installer 与相关测试。如果这么做要改 broker installer，就先停下。
- **验证**：新增 `codex/runtime/tests/test_access_transport.py`，用合成 bare 仓库与 API 桩逐个操作覆盖成功与拒绝；跑全量 smoke。
- **Expected**：
  - 13 个操作在 direct 下成功。
  - 推 `main`、推非当前分支、脏工作树、闭集外操作都被拒绝。
  - 哨兵 token 零命中。
  - 不覆盖真实 Gitea 的版本差异。
- **停止条件**：需要改 broker 或 installer；Gitea REST 无法在不传 token 参数的前提下完成某个操作。

## T02：会话工具接入传输选择

- **交付/范围**：
  - 新增 `.aisoft/access.json` 的 schema 与解析（D3）。
  - `codex/tools/aisoft` 的 `open-pr`，`apply-classification-labels.sh`，`mark-completed-issues.sh` 改为经传输模块调用。
  - 新增 `aisoft labels-provision`。
  - `aisoft-project-target.sh` 只在 broker 模式下使用。
- **blocked_by**：T01。
- **AC**：AC-2（工具入口）、AC-5。
- **接口/约束**：
  - 子命令参数不变。
  - 没有 `access.json` 时走兼容路径，manifest 解析失败报错，不降级成 direct。
  - 非法 `access.json` 一律拒绝。
- **验证**：扩展现有 open-pr、classify、complete 的测试，三种情形各跑一遍：direct、显式 broker、缺省兼容；合成夹具 manifest 承担兼容情形。
- **Expected**：
  - 缺省兼容情形的输出与本批前逐字节一致，对照现有测试的期望值。
  - direct 情形走 API 桩。
  - 不覆盖已安装 broker 的 live 行为。
- **停止条件**：兼容情形出现任何行为差异；需要改 broker 参数。

## T03：`access` 检查与发版

- **交付/范围**：
  - `aisoft project-check` 新增 `access` 检查：读回保护规则、直推/强推、合并 allowlist、required CI context，经传输层 `gitea.protection.read` 取得。
  - 使用发布包加入 `access.json` 模板与 canonical 标签集合，按 `usage-bundle.sh --release` 升版本。
- **blocked_by**：T02。
- **AC**：AC-4（GAP 报告）、AC-7。
- **接口/约束**：
  - 遵守「project-check 新增检查项清单」：计数字符串与 mock 变量都要同步。
  - 发布包成员改动必须升版本。
- **验证**：`test-project-check.sh` 新增四种缺失各一例与一个全满足例；发版后跑 `aisoft version`，`tool-provenance` 读回新版本；跑全量 smoke。
- **Expected**：四种缺失各报 GAP，全满足例报 PASS，版本读回一致。
- **停止条件**：发版规则要求改已发布版本。

## T04：治理文档

- **交付/范围**：
  - 新增 `docs/adr/0003-adoption-access-decoupling.md`。
  - 改 `skills/aisoft-platform/SKILL.md` 的「现行合同」「目标项目与 governance manifest」「私有 Gitea 的确定性访问」「会话标准动作」。
  - getting-started：第 3 步改为可选的 broker 加固访问，新项目路径不改平台 manifest。
  - onboarding-runbook：拆成「采用（项目自主）」与「可选 broker 加固访问」两部分，新增「接入既有项目」。
  - `project-align.md`。
  - `issue-session-flow` 中涉及 broker 的步骤。
  - `templates/project/AGENTS.md`：在项目事实里写明访问方式。
  - 本 spec 授权改动这些治理文件。
- **blocked_by**：T03。
- **AC**：AC-1、AC-6。
- **接口/约束**：
  - 先用 rg 搜 `codex/runtime/tests` 与 smoke，找出被钉住的活文档短语，同步更新。
  - 不手写 README 日期版本。
  - ADR 正文不得出现代码围栏、HTML 注释或原始 HTML 块（D3 守卫）。
  - 不写任何项目名。
  - 技能改动牵动发布包时，并入 T03 的版本，或在本票再发一次版。
- **验证**：
  - 跑全量 smoke 与 D3 泄漏守卫。
  - 跑 `rg -n "先.*登记|登记.*前置|一切.*走 broker"`，人工逐条核对，确认没有残留的「登记是采用前置」表述。
- **Expected**：守卫绿，残留表述清单为空或逐条注明「仅 broker 模式」。
- **停止条件**：治理文件 commit 后 STOP，fresh run 重读合同、治理 diff 与当前规则后再继续 T05。

## T05：端到端回归与收口

- **交付/范围**：
  - 新增一条端到端测试：合成样例项目，平台夹具 manifest 里没有它的条目，声明 direct，然后依次走完 spec AC-3 的八步。
  - 同一条测试再证明兼容夹具项目仍走 broker 路径。
  - 在 verification 里写入口清单表（AC-2）、迁移说明（AC-5）与执行结果。
- **blocked_by**：T04。
- **AC**：AC-2、AC-3、AC-5。
- **接口/约束**：测试登记进 smoke，按「smoke 登记新工具的 5 处」清单走，最容易漏的是第 5 处「测试执行区」。
- **验证**：跑端到端测试、全量 smoke，对改过的 shell 跑 `bash -n` 与 ShellCheck；再对删掉关键闸门的情形做一次反向证明（`full+reverse-proof`）。
- **Expected**：
  - 端到端测试绿。
  - 反向证明分别让推 `main` 拦截与 token 卫生断言变红。
  - 不覆盖 live Gitea，也不覆盖已安装 broker，这两项在 verification 记为 NOT RUN 并说明原因。
- **停止条件**：同一根因连续三次失败。

## Expected touch points

- T01：`codex/runtime/` 新传输模块及其测试；两个 installer 的源文件清单（只加文件，不改 broker 安装字节；如果做不到就停下）。
- T02：`codex/tools/aisoft`、`apply-classification-labels.sh`、`mark-completed-issues.sh`、`codex/agent/aisoft-project-target.sh` 的调用方，以及相关测试。
- T03：`project-check` 实现与 `test-project-check.sh`、`usage-bundle.sh` 发布清单与新版本目录。
- T04：`docs/adr/0003-*`、`skills/aisoft-platform/**`、`skills/issue-session-flow/**`、`templates/project/AGENTS.md`，以及被钉住短语的测试。
- T05：端到端测试、`codex/tests/smoke.sh`、本目录的 verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | T04 文档 diff review，加 ADR 0003 与技能一致性核对 |
| AC-2 | T05 verification 入口清单表，加 T04 残留表述 rg |
| AC-3 | T01 `test_access_transport.py`，加 T05 端到端测试 |
| AC-4 | 现有 broker 回归、T03 `access` 检查四例、T01 闭集拒绝 |
| AC-5 | T02 三情形测试、T05 兼容夹具、verification 迁移说明 |
| AC-6 | T04 onboarding 与 getting-started diff review |
| AC-7 | T03 发版，加 `aisoft version` 与 `tool-provenance` 读回 |

## 执行证据

<!-- execution-evidence:start -->
尚未执行。实际记录 ticket_base、起始状态、provider/入口来源、验证结果、candidate_head、
审查范围与 findings；可引用本 Issue 映射 verification，不另建证据权威。
<!-- execution-evidence:end -->

语义摘要仅排除图中的 Status 单元、updated 与这段成对标识的执行证据；原始全文摘要另存审计。
标记不得嵌套、重复或包住任务图/正文/约束。正常状态推进、补证不改变任务语义；
AC/依赖/命令/Expected/约束变化必须报告，不能静默续跑。具体规则见平台 execution-adapter。

## 部署与回滚

无部署影响。回滚方式是 revert 本批 PR；已改用 direct 的项目删除 `.aisoft/access.json` 即回到兼容路径。
