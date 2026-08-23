---
issue: 160
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/160
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: contract-drafting
branch: change/160-analysis-label-projection
created: 2026-08-23
updated: 2026-08-23
---

# Spec · 判级标签的交互会话投影路径（#160）

## 目标与原因

给交互会话补上唯一缺失的那一段：把一次 AI 判级的 `change_type` 与 `effective_complexity`
确定性地投影成 Gitea 上的 `type/*` 与 `complexity/*` 标签。

分工不新设，沿用 `mark-completed-issues.sh` 头部已经写死的原则：**判断在工具里，
broker 只做一次受约束的写**。因此本变更是「一个 typed 写操作 + 一个执行者工具」，
而不是把文档解析塞进 broker。

## Acceptance criteria

- [ ] **AC-1** broker 新增 typed 操作 `gitea.issue.labels.classify`，
      参数 `("number", "change_type", "complexity")`，`project-agent` 路由，`mutating: true`；
      它替换 Issue 的 `type/` 与 `complexity/` 两个维度，并保留生命周期标签、`triage/*`
      与 project extension 标签。
- [ ] **AC-2** 两个维度的取值逐维校验自**已安装的 label manifest**
      （canonical 里带 `type/`、`complexity/` 前缀的名字），不是脚本里的字面量；
      `complexity/standard`（retired）不可写入。
- [ ] **AC-3** 两个参数都必填：只给一个时 broker 以 `ARGUMENT_MISMATCH` 拒绝，
      不存在「只投影一半判级」的调用。
- [ ] **AC-4** 目标标签在仓库中未定义时 fail-closed 返回 `TARGET_MISMATCH` 并指向
      `gitea.labels.provision`，绝不顺手创建标签（与 `_set_issue_lifecycle` 同规则）。
- [ ] **AC-5** 两个维度都已经正确时不发出 PUT，返回 `result: "no-op"`。
- [ ] **AC-6** 新增 `codex/tools/apply-classification-labels.sh`：判定取自映射 summary 的
      `change_type` 与 `effective_complexity`，**不接受调用方传入标签**；
      默认只输出逐 Issue 判定计划、零写入，加 `--apply` 才经 broker 写。
- [ ] **AC-7** 该工具对已关闭 Issue 跳过并给出理由（`issue-closed`），不提供 override 开关；
      对无映射文档、无 summary、summary 缺 `effective_complexity`（`needs-human-decision`）
      的情况分别给出可区分的跳过理由，不臆造标签。
- [ ] **AC-8** `bash codex/tests/smoke.sh` 全绿；新写入路径在
      `codex/runtime/tests/test_host_access.py` 与新增
      `codex/tests/test-apply-classification-labels.sh` 中有测试覆盖，
      且 `codex/tests/test-host-access-broker.sh` 的 `operation_count` 断言更新为 30。
- [ ] **AC-9** `03` §11 与 `skill-for-claude/aisoft-platform/SKILL.md` 记录这条路径由谁、
      在什么时候运行，以及 closed Issue 不补写的结论。

## 接口、数据与兼容性影响

### 新 typed 操作

```
host-access-broker --project <id> --operation gitea.issue.labels.classify \
  --number <N> --change-type <value> --complexity <value>
```

`--change-type`/`--complexity` 传的是 front matter 里的**裸值**（`platform`、`complex`），
broker 拼成 `type/<value>` 与 `complexity/<value>` 后再对 manifest 校验。这样工具是
front matter 的直通管道，不需要在两侧各拼一次前缀。

返回体与 `gitea.issue.labels.set` 同形：`{issue, before, after, result, status}`，
`result` ∈ `{"no-op", "updated"}`。

为什么是新操作而不是给 `set` 加可选参数：`set` 的语义是「替换一个维度」，
其 `contract.py` 注释明确把 `type/`/`complexity/` 排除在外。新开一个操作让
`host.access.audit` 里判级写入与生命周期写入分开可见，也让「两个维度必须同时给」
能由 typed `arguments` 元组直接强制——挂在 `set` 上就只能是可选参数，强制不了。

### 为什么这不是「绕过产出管线」

`contract.py:203-206` 原始论证排除的是**任意标签写入**。本操作的调用方只有
`apply-classification-labels.sh`，而它的取值来源是判级产物本身；broker 侧再叠一道
manifest 枚举校验。人工能影响结果的唯一方式是改 summary front matter，
那正是判级产物的所在地。

### 工具接口

```
codex/tools/apply-classification-labels.sh \
  [--repo <checkout>] [--project <id>] [--range <git range>] [--apply] [N ...]
```

参数面、每 Issue 一行 JSON 的输出形状、`--range` 的 `Closes #N` 抽取、
默认 dry-run 与 `--apply` 的关系，全部与 `mark-completed-issues.sh` 一致——
运维在两者之间不需要学第二套用法。

`action` 取 `set-classification`；dry-run 行额外带 `change_type` 与 `complexity`，
让人在写入前看见将要投影的值。

### 兼容性

- 既有 29 个操作、`gitea.issue.labels.set` 的 lifecycle 语义、Loop 的 `apply-analysis`
  与 `mark-completed-issues.sh` 的行为一字不改。
- 新参数 `--change-type` / `--complexity` 是 CLI 上新增的可选 flag，
  旧调用形式不受影响（`supplied != set(operation.arguments)` 保证旧操作传新参数会被拒）。
- **manifest 改动必须重装 broker 才生效**，Mac 与 gitea-ci 两台都要装。
  重装前调用新操作返回 `REQUEST_DENIED / not allowlisted`（`06` 踩坑 20）。
  重装是合并后的人工前置步骤，不在本 PR 的交付物内。

## 风险与回滚约束

- 回滚 = revert 本 PR 后重装 broker。操作是纯新增，没有数据迁移，没有状态残留；
  已经写进 Gitea 的 `type/*`/`complexity/*` 标签是合同要求的正确状态，不需要回滚。
- 写入范围的硬边界在 broker 侧：`final` 集合由「当前标签里不属于这两个维度的 id」
  并上两个目标 id 构成，没有任何调用方能让它丢掉 lifecycle 或 `triage/*`。
- 工具不会被任何定时器或 CI 调用，只在人显式运行时写入。

## 非目标

- 不改判级判据（`classification.py`）。
- 不改 `mark-completed-issues.sh` / `mark-deployed-issues.sh` 的终态判定逻辑。
- 不改 `apply-analysis` 与 Development Loop 的投影路径。
- 不补写已关闭 Issue 的标签（#138/#146/#148/#152/#158），依据见 summary。
- 不给 `triage/*` 维度加 typed 写入口——那是 Matt 编排的输出，不在本 Issue 范围。
- 不在本 PR 内重装 broker。

## 治理文件修改授权

依 `AGENTS.md`「只有 complex 变更映射的 `spec` 明确授权时，才能修改 …… 治理文件」，
本 spec 授权本次变更修改下列文件，且仅限下列文件：

- `codex/runtime/aisoft_host_access/{contract,broker,cli,runner}.py`
- `codex/config/host-access-broker.json`（仅 `operations` 数组新增一条）
- `codex/tools/apply-classification-labels.sh`（新增）
- `codex/tests/{smoke.sh,test-host-access-broker.sh}`、
  `codex/tests/test-apply-classification-labels.sh`（新增）、
  `codex/runtime/tests/test_host_access.py`
- `03-Issue-Spec-Plan与单闸门开发流程.md`（§11 新增小节）
- `skill-for-claude/aisoft-platform/SKILL.md`（会话标准动作新增一步）

不授权修改 `AGENTS.md`、`codex/global-AGENTS.md`、controller、CI 工作流与部署脚本。

## 未决问题

无。
