---
issue: 192
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/192
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把「跳过等待部署」的判据从「这个仓库有没有部署链路」收紧成「这条链路会不会覆盖到本次 merge」，为此给 deployment_lifecycle 增加第三档 application-deploy-selective 并把它设为缺省，改写 mark-completed-issues.sh 的终态分支与 03 §11 的合取表；改的是终态记账合同本身，命中 platform-governance 与 agent-governance，change_type 为 platform 属 FORCED_COMPLEX_TYPES
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-selective-deploy-lifecycle-260824.md
  spec: spec-selective-deploy-lifecycle-260824.md
  plan: plan-selective-deploy-lifecycle-260824.md
  verification: verification-selective-deploy-lifecycle-260824.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/192-selective-deploy-lifecycle
pr_url:
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

`03` §11 的终态判定是一个合取。#163 把它拆成两个条件之后，第二行仍然把「欠一份验证记录」
与「必须等部署」绑在一起：

| `required_docs` 含 `verification` | 仓库 `deployment_lifecycle` | 终态 |
|---|---|---|
| 否 | 任意 | `completed` |
| 是 | `application-deploy`（缺省） | 跳过并给出 `requires-deployment` |
| 是 | `none` | `completed` |

目前只有 `aisoft-platform` 声明了 `none`。其余仓库按缺省取 `application-deploy`，于是一个
**不部署但确实欠一份验证记录**的变更如实声明 `verification` 之后：`completed` 因含
`verification` 被排除，`deployed` 因从未部署而永不写入，两个终态都没人写——正是 #163 要修的
失败模式换了一类仓库重新出现。

**这不是推演，LocalWMS 上已经发生了。** 15 个已合并且声明了 `verification` 的 Issue 里，
有 5 个（#13、#23、#29、#34、#35）closed 之后**一个标签都没有**；另外 10 个拿到了
`completed`，而当前工具对它们全部判 `skip requires-deployment`——也就是说那 10 个标签是绕过
这条判定写上去的。逐条读回见映射的 verification 文档。

## 影响范围

- `codex/runtime/aisoft_gitea_governance/contract.py`：`DEPLOYMENT_LIFECYCLES` 与缺省值。
- `codex/tools/mark-completed-issues.sh`：终态分支由二选一变成三选一，未知取值 fail closed。
- `03` §3 与 §11、`02` §9、`skill-for-claude/issue-session-flow/SKILL.md`：合同文字。
- `codex/runtime/tests/test_deployment_lifecycle.py`、`codex/tests/test-mark-completed-issues.sh`。
- 不改任何仓库的实际声明：`aisoft-platform` 保持 `none`，其余仓库仍未声明、只是缺省档换了一个。

## 初步方案与建议

`deployment_lifecycle` 增加第三档，并把**缺省**换成它：

| 取值 | 含义 | 声明了 `verification` 的变更 |
|---|---|---|
| `application-deploy` | 链路存在，且**每一次 merge 都会被它部署** | 跳过等待 `deployed`——等待有保证的终点 |
| `application-deploy-selective` | 链路存在，但只覆盖一部分 merge（**缺省**） | 写 `completed`，`reason: deployment-not-guaranteed` |
| `none` | 没有链路 | 写 `completed`，`reason: no-deployment-chain` |

判据仍然全部取自仓库证据：一个来自 summary front matter 的 `required_docs`，一个来自
governance manifest 的仓库声明。工具没有新增任何接受人工终态判断的入口（#163 约束不变）。

## 风险

- **早写的 `completed` 会不会盖掉一次真实部署？** 不会。broker 在 `_set_issue_lifecycle` 里
  拒绝把已经 `deployed` 的 Issue 降级为 `completed`（`REQUEST_DENIED`）。
- **缺省档换宽了会不会让在途部署被提前写成 `completed`？** 会有一个窗口，但它自愈：
  `mark-deployed-issues.sh` 剥掉整个生命周期维度再写 `deployed`。反方向（漏写）没有任何
  组件会回头补——`03` §11 自己写着「没有任何组件处在能观察到合并的位置上」。
- **声明 `application-deploy` 却并非合并即部署**，等待就又没有终点。这一档因此是需要主动
  声明的一档，缺省不会落到它上面。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把「跳过等待部署」的判据从「这个仓库有没有部署链路」收紧成「这条链路会不会覆盖到本次 merge」，为此给 deployment_lifecycle 增加第三档 application-deploy-selective 并把它设为缺省，改写 mark-completed-issues.sh 的终态分支与 03 §11 的合取表；改的是终态记账合同本身，命中 platform-governance 与 agent-governance
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

- `change_type: platform` 属 `classification.py` 的 `FORCED_COMPLEX_TYPES`，单这一项即强制 complex。
- `risk_flags` 的 `platform-governance` 与 `agent-governance` 都属 `FORCED_COMPLEX_RISKS`，各自独立强制。
- `contract_effect: change`：终态判定规则本身被改写，不是恢复既有合同。
- `required_docs` 含 `verification`：按 `03` §3 的证据来源判据，本次的决定性证据是**跨仓库扫描**
  （5 个仓库全部 verification 文档的标题结构、全部 summary 的 `risk_flags` 词表）与 **LocalWMS
  真实 checkout 上改动前的工具输出**——required CI 一条都不跑，且旧工具的输出在本次改动合并后
  无法重放。本仓库声明 `none`，按 §11 到 `completed`，声明 `verification` 不会让它卡住。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文列的三个方向已在映射 spec 的「为什么不选另外两条路」里逐条裁决。
