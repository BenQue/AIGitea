---
issue: 164
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/164
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写 governance manifest 中 localwms 的 analysis_provider 声明，决定哪个 AI 运行时代表该项目执行判级，属 Agent 与平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-localwms-analysis-provider-260824.md
  spec: spec-localwms-analysis-provider-260824.md
  plan: plan-localwms-analysis-provider-260824.md
  verification: verification-localwms-analysis-provider-260824.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/164-localwms-analysis-provider
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/177
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

`codex/config/host-access-broker.json` 里 `localwms` 的 `vm_profile.analysis_provider`
声明 `claude`，但 `gitea-ci` VM 上没有可用的 Claude 运行时——这条链**从未执行过一次**。

这个取值不是从证据来的。#152 的 summary 把理由写得很清楚：

> `analysis_provider` = `claude`。平台既有惯例：三个 internal-application
> （NewEMaint / SFMDigitalBoard / rsdesign-new）全是 `claude`，只有平台仓
> aisoft-platform 是 `codex`。LocalWMS 是 internal-application

也就是说，它是**按同类项目类推**选出来的，而那三条同类声明同样没有被验证过。
LocalWMS #66 的 analyzer canary 第一次把这条链真的接上，才发现它接不通：
`claude-analyzer.sh:13` 是 `command -v claude || exit 2`，而 `claude` 二进制在
`~/.npm-global/bin` 且不在 `coder` 的 PATH 上，也未认证。同一台 VM 上
`codex` 在 PATH 内、`auth.json` 有效，并且是唯一有产出物可查的分析链
（`docs/changes/120-company-delivery-pilot/` 由它在 2026-08-16 产出）。

canary 用 codex 链对 LocalWMS 三个真实 Issue 做了只读试跑，均正常产出五节 summary
与九字段判级。完整证据在 Issue #164 正文。

## 影响范围

**代码零改动。** `analysis_provider` 的取值集合在 `contract.py:430` 是封闭的
`{claude, codex, none}`，`codex` 本来就合法；schema、CLI、profile 生成逻辑一律不动。

| 文件 | 改动 |
|---|---|
| `codex/config/host-access-broker.json` | `localwms.vm_profile.analysis_provider`：`claude` → `codex`（1 行） |
| `codex/runtime/tests/test_host_access.py` | `test_localwms_profile_is_analyzer_only_without_a_timer` 的两处断言取值，并把新理由写进注释 |

该测试是这次改动的关键约束面：manifest 不只是数据，取值被一条**写明了理由**的测试钉住，
所以这个字段不可能被静默改掉——改值必须同时改断言，改断言就必须重新陈述依据。
#152 之所以留下一个没有证据的取值，恰恰是因为当时注释记的是「惯例」而不是「证据」。

**不改**：`implement_provider`（仍 `none`）、`timer_unit`（仍 `null`）、
`codex/config/gitea-governance.json`、其余九个项目条目、任何 agent 脚本或 runtime。

## 初步方案与建议

### 范围裁定：本次只改 `localwms`

Issue 把「另外三条同病的 profile 是否一并处理」交给平台会话裁定。结论是**不一并处理**，
另开 #178。四条理由按重要性排列：

1. **两条 profile 是活的。** `sfm`（`aisoft-agent@sfm.timer`）与 `emaintenance`
   （`aisoft-agent@emaintenance.timer`）每 15 分钟真在跑。今天每一跳都走到
   `analyze-claude.sh` 然后在第一行硬失败——这是一个 **fail-closed 的空转**。
   把它们改成 `codex`，等于在两个应用仓上**把一条死分支变成活的、有写权限的
   analyzer**：下一个被打上 `needs-analysis` 的 Issue 就会真的被判级、被写标签、
   被写 summary。这是「启用」，不是「订正配置」。
   `localwms` 与 `rsdesign` 的 `timer_unit` 是 `null`，没有任何东西会自动触发它们——
   风险档次根本不同，不该用同一个 PR 一起翻。
2. **证据只覆盖 localwms。** 只有 LocalWMS 跑过 canary。平台合同写死了
   provider 启用是**每项目独立验收门**，不是一次舰队级扫平。给另外三条改值而没有
   各自的产出物证据，等于把 #152 的错误——按类推选 provider——原样再犯一次，
   只是这次类推的方向反过来。
3. **各自需要独立的验收标准。** 按平台自己的一句话判据（`它需要写验收标准吗？
   需要就是新 Issue`），三条 profile 各需要自己的 canary 与 read-back 证据。
   #164 的 AC 全部只谈 `localwms`；扩大 diff 而不扩大 AC，产出的就是一个
   「多出来的改动没有任何东西验证它」的 PR。
4. **已知的反面理由，并已安排。** 让三条 profile 继续声明一个跑不起来的运行时，
   本身就是一条已知的假声明，而假声明正是 #164 的成因。但它 fail-closed，
   不产生错误产出；处置方式是紧接着开的独立 Issue，不是无限期搁置。

### 本变更声明 `verification`

按 `03` §3 的新判据（#168）——判据是**验收证据的来源**，不是变更的题材：

| AC | 证据来源 | 能否由 diff + required CI 复现 |
|---|---|---|
| AC-1 manifest 取值 | 仓库 diff | 能 |
| AC-4 `implement_provider` / `timer_unit` 不变 | 仓库 diff | 能 |
| AC-2 VM 上 `localwms.env` 的 `ANALYSIS_PROVIDER` 与文件模式 | 重装 + provision 后的主机侧状态 | **不能** |
| AC-3 `--action read-back` 返回 PASS | 同上 | **不能** |

AC-2/AC-3 正落在 §3 表格第二行点名的形态上——「部署、迁移、**安装与主机侧生效**」。
另外，改动前的基线（`vm.profile.plan` 当前返回 `no-op`）**只有现在观测得到**，
合并后无法重放。两条都要求声明 `verification`。

`aisoft-platform` 的 `deployment_lifecycle` 是 `none`，按 `03` §11 的合取表，
声明了 `verification` 仍然到 `completed`，不会卡在无人写终态的状态里（#163）。

## 风险

- **与 VM 上陈旧 runtime 的相互作用（本变更不修，但比 Issue 描述的更早触发）。**
  Issue #164 记录 VM 上 `~/.local/lib/aisoft-loop` 是 2026-08-14 的副本，早于
  `change_control`（实际引入于 2026-08-21 的 `3141620` / #134，日期吻合），
  其 `route()` 只有 production 一档。Issue 说这要「Development Loop 一旦启用」才生效，
  **范围被低估了**：`3141620` 同时给 `_render_analysis`（`cli.py:378`）和
  `_apply_analysis`（`cli.py:409`）加上了 `change_control=`，而
  `analyze-codex.sh:29` 在每一次 analyzer 调用里都会跑 `render-analysis`，
  远在任何 Loop 之前。因此陈旧 runtime 的 over-claim 会在 **LocalWMS 第一次端到端
  analyzer 运行**时就写出来，不必等 Loop。
  canary 之所以没撞上，是因为它直接调 `codex-analyzer.sh`（`:53` 只到
  `validate-analysis`，不碰 `route()`），没走 `analyze-codex.sh` 这层外壳。

  LocalWMS 是**唯一**声明 `change_control: development` 的仓库，另外三个
  internal-application 都取 production 缺省——也就是说陈旧 runtime 的错误答案
  恰好只在 LocalWMS 上和正确答案不一致（production `('summary','spec','plan','verification')`
  vs development `('summary','verification')`）。

  **不阻塞本变更**：`localwms` 的 `timer_unit` 是 `null`、`implement_provider` 是 `none`，
  没有任何东西会自动触发 `analyze-codex.sh`。但交接项因此比 Issue 写的更紧：
  刷新 VM runtime 应当排在 LocalWMS **第一次端到端 analyzer 运行之前**，
  而不只是排在启用 Loop 之前。已开 #179 跟踪。

- **合并不等于生效。** broker 运行时读的是安装态副本
  `/usr/local/share/aisoft/host-access-broker.json`。合并后必须由人重装两台并跑
  profile 迁移，否则 VM 上仍是 `ANALYSIS_PROVIDER=claude`。见 verification 的交接项。
- **回滚** = revert 本 PR；若彼时已重装，revert 后需再重装一次并重跑
  `--action apply` 才能让 VM 回到旧声明。无 schema、无迁移、无数据。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写 governance manifest 中 localwms 的 analysis_provider 声明，决定哪个 AI 运行时代表该项目执行判级，属 Agent 与平台治理变更，强制 complex
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：「Agent 或平台治理变更一律按 complex 处理」。本变更改的是
  `codex/config/host-access-broker.json`——canonical governance manifest——中
  决定「哪个 AI 运行时代表 LocalWMS 执行判级」的字段，两个条件都命中。
- `classification.py:55` `FORCED_COMPLEX_TYPES` 含 `platform`；`FORCED_COMPLEX_RISKS`
  含 `platform-governance` 与 `agent-governance`；`route()` 另按
  `contract_effect in {add, change}` 强制 complex。三条独立路径都指向 complex。
- `contract_effect: change` 而不是 `restore`：`restore` 是「恢复曾经成立、后来退化的
  产品合同」。claude 链在 LocalWMS 上**从未成立过**，没有东西退化。#152 的 summary
  把 `claude` 记为一次有依据的选择，本变更推翻的是那次被记录在案的决定——
  平台声明的合同确实变了。
- 复杂度不因「只改一个字段」下调：`03` §4 明确 `type/platform` 在改变平台行为或
  治理合同时强制 complex，而这一个字段决定的正是哪个 agent 有权代表该项目产出判级。

### 缺失的 acceptance criteria 或决策

- 无。AC-1..AC-4 在 Issue 正文中已可测。唯一的开放决策——「另外三条 profile
  是否一并处理」——由上文「范围裁定」一节基于仓库证据与风险档次判定为「不一并处理」，
  并在 spec §6 列为非目标，已开 #178 跟踪。
