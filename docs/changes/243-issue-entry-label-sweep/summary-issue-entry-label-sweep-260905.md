---
issue: 243
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/243
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变 broker typed 操作 gitea.issue.create 的参数合同并新增一次标签写入，同时改动 Agent 行为文件 issue-session-flow skill 与治理文档 03、issue-tracker.md；AGENTS.md 的强制规则把 Agent 与平台治理变更一律判为 complex。
risk_flags: []
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-issue-entry-label-sweep-260905.md
  spec: spec-issue-entry-label-sweep-260905.md
  plan: plan-issue-entry-label-sweep-260905.md
  verification: verification-issue-entry-label-sweep-260905.md
confidence: high
override_reason: ''
depends_on:
  - 222
status: pr-open
branch: change/243-issue-entry-label-sweep
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/249
created: 2026-09-05
updated: 2026-09-05
---

## 问题/需求总结

衍生 Issue 立案后落进一个没人看的收件箱。入口缺一环：`03` 定义 Issue 以 `needs-analysis`
进入分析，但 broker 的 `gitea.issue.create` 只接受 `title` 与 `body`，不写任何标签；平台仓
`vm_profile.timer_unit` 为 `null`，也没有任何自动化会领这些 Issue。结果是 2026-09-05 盘点
时全部开放 Issue 零标签、从未进过 triage，并出现两对相隔十几秒到十几分钟的重复立案。

本变更做三件事：让 `gitea.issue.create` 在同一次写入里带上流程入口标签；给
`issue-session-flow` skill 补一个「开放 Issue 清扫」节，把清扫的枚举、逐条判定与需裁决汇总
写成固定格式；在 `03` 与 `docs/agents/issue-tracker.md` 写明衍生 Issue 的正文要求与默认认领方。

## 影响范围

- broker typed 合同：`gitea.issue.create` 的 `arguments` 从两项变为三项，新增 `entry_label`。
  身份路由、`mutating` 标记与操作总数都不变，不新增任何操作，不给 `coder` 新增写权限。
- 同步点按 `06` 踩坑 20 的清单：`contract.py`、`broker.py`、`runner.py`、`cli.py`、
  `codex/config/host-access-broker.json`、`codex/runtime/tests/test_host_access.py`（含逐字钉死
  `execute()` kwargs 的那条测试）、`codex/tests/test-host-access-broker.sh`。
- 治理文件：`skill-for-claude/issue-session-flow/SKILL.md`、
  `codex/skills/issue-session-flow/SKILL.md`、`skill-for-claude/aisoft-platform/SKILL.md`、
  `03-Issue-Spec-Plan与单闸门开发流程.md`、`docs/agents/issue-tracker.md`。
- 不改 `AGENTS.md`；不改任何 identity route、凭据托管或 main 保护配置。

## 初步方案与建议

入口标签在创建 Issue 的同一个 POST 里随 `labels` 一起写入，而不是创建后再补一次 PUT：
一次请求就没有「Issue 已存在但还没有标签」的中间态，也不会在补写失败时留下半成品。

`entry_label` 定为必填而不是带默认值的可选参数。broker 的参数闸门是精确集合相等，合同里
没有可选参数这个概念；要引入它就得改动 manifest 里全部 33 条操作的 schema。更重要的是，
本 Issue 的根因正是一个看不见的默认值（谁都没写标签），再用一个藏在 broker 里的默认值去
修它，调用点仍然看不出这条 Issue 走的是哪个入口。必填让漏写在解析凭据之前就以
`ARGUMENT_MISMATCH` 失败。

取值限定为两个已被 `03` 命名的流程入口：`needs-analysis` 与 `triage/needs-triage`。

## 风险

- 参数合同变化必须两台重装才在 wrapper 上生效；只装一台会出现 `REQUEST_DENIED` 形态的
  假权限问题（`06` 踩坑 20）。缓解：验收直接用候选 manifest 调 `aisoft_host_access.cli`
  取得真实证据，重装作为独立的运维步骤记录，未完成就如实写进未执行项。
- 治理文件与 runtime 混在同一个 commit 会违反 AGENTS.md 的受控步骤要求。缓解：plan 把治理
  合同单独放在 T01，实现前重新读取。
- 平台治理文件受 smoke 的项目名与交付形态守卫约束，清扫节不得出现任何具体项目名。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改变 broker typed 操作 gitea.issue.create 的参数合同并新增一次标签写入，同时改动 Agent 行为文件 issue-session-flow skill 与治理文档 03、issue-tracker.md；AGENTS.md 的强制规则把 Agent 与平台治理变更一律判为 complex。
risk_flags: []
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `AGENTS.md`：Agent 或平台治理变更一律按 complex 处理；本变更改 Agent 行为文件与治理文档。
- `codex/runtime/aisoft_host_access/contract.py:171` 与 `codex/config/host-access-broker.json`
  声明 `gitea.issue.create` 的 `arguments` 为 `title`、`body`；本变更改写这条外部契约，
  `contract_effect` 是 `change` 而不是 `restore`。
- `codex/config/gitea-governance.json` 未给 `aisoft-platform` 声明 `change_control`，按
  `03` §1 一律作 `production` 处理，因此 complex 必须有映射的 `spec` 与 `plan`。
- 声明 `verification` 的依据是证据来源而不是题材（`03` §3）：本变更的验收需要一次真实的
  Gitea 写入与读回、以及安装期生效的确认，required CI 与 diff review 都重放不了。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文的五条验收标准可测；实现位置由本次 spec 裁定。
