---
issue: ISSUE_NUMBER
gitea_url: ISSUE_URL
change_type: CHANGE_TYPE
requested_complexity: auto
assessed_complexity: ASSESSED_COMPLEXITY
effective_complexity: complex
contract_effect: CONTRACT_EFFECT
confidence: CONFIDENCE
risk_flags: []
depends_on: []
status: pending
branch: change/ISSUE_NUMBER-SHORT-SLUG
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Verification template

<!-- TEMPLATE_CONDITIONAL:
`## 部署验收` 一节只适用于实际部署或迁移的变更。不部署的变更**整节删除**，
不要保留标题再填「无」。声明 `verification` 的含义是「这次变更欠一份验证记录」，
不是「这次变更要部署」：判据见 `03` §3「何时声明 `verification`」，合并后的终态
见 `03` §11 的合取表——`deployment_lifecycle: none` 的仓库照样到 `completed`。
-->

## 基线与范围

- Commit SHA:
- 基线：`origin/main` =
- 环境:
- 本记录负责证明的 acceptance criteria:

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

命令与输出照实抄。改动前才观测得到的证据（基线状态、改动前后对比、先看着测试红）
只有写在这里才留得下来——改动合并后就无法重放。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | 待填写 |

## 部署验收

仅当本次变更实际部署或迁移时保留本节；否则整节删除。

### 制品与环境

- Artifact:
- Environment:

### 重复部署

- 第一次：NOT RUN
- 第二次：NOT RUN

### 故意失败与回滚

- 失败场景：NOT RUN
- 停止/回滚结果：NOT RUN
- 数据恢复验证：NOT RUN

## 遗留风险与未完成项

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
