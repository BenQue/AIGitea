---
issue: 448
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/448
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
depends_on: []
git_scope:
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - codex/runtime/aisoft_host_access/broker.py
  - codex/runtime/aisoft_host_access/contract.py
  - codex/runtime/tests/test_host_access.py
  - codex/runtime/tests/test_project_declared_source.py
  - docs/agents/triage-labels.md
  - docs/changes/448-terminal-clears-triage-state/plan-terminal-clears-triage-state-261114.md
  - docs/changes/448-terminal-clears-triage-state/spec-terminal-clears-triage-state-261114.md
  - docs/changes/448-terminal-clears-triage-state/summary-terminal-clears-triage-state-261114.md
  - docs/changes/448-terminal-clears-triage-state/verification-terminal-clears-triage-state-261114.md
  - docs/governance/review-evidence-index.md
  - templates/docs/agents/triage-labels.md
  - usage/CONTRACT.md
  - usage/bundle.json
branch: change/448-terminal-clears-triage-state
created: 2026-11-14
updated: 2026-11-14
---

# 终态写入清除 triage 状态标签 · spec

## 目标与原因

建票入口标签 `triage/needs-triage` 永远不会被摘掉：Issue 判级、合并、写完 `completed` 后仍声称「尚未完成分类与下一处理者判断」。`triage/ready-for-agent` 同样残留在已完成的 Issue 上（平台 #73、NewEMaint #61）。

根因：broker 的三个标签写者都只替换自己点名的维度，`_replace_issue_label_dimensions` 把其余标签按 id 原样带过；`triage/*` 没有任何写者，入口标签只在 `gitea.issue.create --entry-label` 写入一次。另一个入口 `needs-analysis` 属于生命周期维，终态写入按互斥规则替换它，所以不残留。

目标：终态写入成为 triage 状态维的收口点，修住根因；对已经残留的存量做一次受控清理。

## 范围与非范围

范围：

- `gitea.issue.labels.set` 写 `completed` 或 `deployed` 时，在同一次 PUT 里移除 Issue 上的 triage 状态标签。站点 broker 与项目自声明 `aisoft-access` 共用这段实现，一处修复覆盖两种来源。
- 文档：`03` §4 标签维度段、`docs/agents/triage-labels.md` 与其模板写明终态收口规则；使用发布包同 PR 发版。
- 存量清理方案：修复装好后，对已关闭且已终态、仍挂 triage 状态标签的 Issue，逐条重写其现有终态，dry-run 后经人确认再 apply。

非范围：

- 不新增 broker 操作，不给 triage 维开通用写入口，不改任何操作的参数集合。
- `classify --apply` 不推进 Matt triage 状态。
- 非终态生命周期写入（`approved`、`pr-open` 等）行为不变。
- 已关闭但没有终态的 Issue（平台 9 条、NewEMaint #108、LocalWMS #356）与开放 Issue 不做批量改写；`triage/wontfix` 的 Issue 不动。
- 不改 `mark-completed-issues.sh` 的判定逻辑与输出格式。
- 项目仓升级发布包属于各项目自己的对齐动作，不在本 Issue。

## 方案与决策

负责人 2026-11-15 在确认点 1 批准下列方案，本节即为合同。

- **D1 清什么**：终态写入时把 triage 状态标签视为与生命周期同一次替换的维度。清除集合是 Issue 上所有 `triage/*` 标签减去两个 category（`triage/bug`、`triage/enhancement`），按命名空间判定而不是按清单，与 `complexity/standard` 的处理同一规则。category 是 Issue 的类别事实，终态后仍然成立，保留。终态之后没有「下一处理者」，所以不写入任何新的 triage 状态。
- **D2 遇到 `triage/wontfix`**：终态写入 fail closed，返回 `REQUEST_DENIED`，不发 PUT。标签合同写明 wontfix「不得映射为 completed 或 deployed」，一个 Issue 同时声明「不实施」和「已交付」是需要人判断的矛盾。`aisoft complete --apply` 遇到时如实报 `broker-refused`，由人决定。
- **D3 `classify --apply`**：不顺带推进 `needs-triage` → `ready-for-agent`。判级投影的是 analyzer 的两个维度；Matt 的下一处理者判断（agent 还是 human）不是判级结果的一部分，混进去会让 classify 替 Matt 做决定。开放 Issue 上的入口标签在终态写入时由 D1 收口。
- **D4 不新增 broker 操作**：triage 维的写入只发生在已有的终态写入里，不开放任意 triage 写入（#115 排除任意标签写的理由仍然成立）。参数集合不变，manifest 不变；但 installed broker 的行为改变，必须两台重装。
- **D5 存量清理**：修复装好后，对每个已登记且有凭据的项目，用 typed `gitea.issue.list --state closed` 读出「已关闭、恰有一个终态标签、挂 triage 状态标签、不挂 `triage/wontfix`」的 Issue 作 dry-run 计划；人确认后逐条调用 `gitea.issue.labels.set --number N --lifecycle <它现有的终态>`，再用同一读取复核。重写的是 Issue 已有的终态，所以生命周期维不变，只有 triage 状态被收口；不经 raw token，不拼 URL。

## Acceptance criteria

- [ ] AC-1：对挂 `triage/needs-triage`（或 `needs-info`、`ready-for-agent`、`ready-for-human`）的 Issue 写 `completed` 或 `deployed`，读回不含任何 triage 状态标签；`triage/bug`、`triage/enhancement`、`type/*`、`complexity/*` 与 `area/`、`priority/` 扩展标签原样保留。
- [ ] AC-2：已是终态但仍挂 triage 状态标签的 Issue，重写同一终态结果为 `updated` 且只移除状态标签；已经正确的 Issue 重写仍为 `no-op`、不发 PUT。
- [ ] AC-3：挂 `triage/wontfix` 的 Issue 写 `completed` 或 `deployed` 返回 `REQUEST_DENIED`，不发 PUT，标签不变。
- [ ] AC-4：非终态生命周期写入不触碰任何 `triage/*` 标签；`deployed` → `completed` 降级仍被拒绝。
- [ ] AC-5：AC-1–AC-3 在站点 broker 与项目来源（`ProjectSourceBroker`）两条路径上都有单测；新增用例在修复前的代码上变红（反向证明），修复后 `python3 -m unittest discover codex/runtime/tests` 与 `bash codex/tests/smoke.sh` 全绿。
- [ ] AC-6：`03`、`docs/agents/triage-labels.md` 与模板写明终态收口规则；使用发布包发新版本，`usage-bundle.sh` 校验通过。
- [ ] AC-7：给负责人的两台重装命令与读回步骤写入 verification；重装后的读回与 D5 存量清理（dry-run 计划、apply 结果、复核）写成 Issue 评论。合并前这一条只要求命令与步骤就绪，执行结果属于合并后收尾。

## 风险与回滚约束

- 风险：清除集合按命名空间判定，将来 Matt 新增的 category 会被当成状态清掉。缓解：category 集合写成带注释的字面量，新增 category 是标签合同变更，与 03 同步修改；单测钉住两个现有 category 保留。
- 风险：D2 会让某些 `aisoft complete --apply` 从成功变为 `broker-refused`。当前清点没有同时挂 wontfix 与终态候选的 Issue；拒绝即是期望的人工闸门。
- 回滚：revert 本 PR 并按同一命令两台重装 broker，行为回到只替换生命周期维。存量清理移除的是错误陈述的状态标签，不需要回滚；如确需恢复，typed 操作里没有 triage 写入口，只能由人在 Gitea 界面加回。

## 接口、数据与兼容性影响

- 接口：`gitea.issue.labels.set` 参数集合不变（`number`、`lifecycle`），返回体形状不变（`before`/`after`/`result`/`status`）；终态写入时 `after` 少了 triage 状态标签，新增一种 `REQUEST_DENIED` 原因。
- 数据：只改 Gitea Issue 的标签附着，不改标签定义，不删标签。
- 兼容：旧 broker 与旧发布包的项目继续按旧行为工作（不清除），不会出错；项目升到新发布包、站点两台重装后才生效。`mark-completed-issues.sh` 不需要改动。

## 未决问题

- 无。负责人 2026-11-15 在确认点 1 按推荐方案批准 D1–D5。
