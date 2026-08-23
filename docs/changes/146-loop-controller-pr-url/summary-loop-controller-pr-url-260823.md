---
issue: 146
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/146
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/146-loop-controller-pr-url
pr_url:
created: 2026-08-23
updated: 2026-08-23
reason: 改动 controller.py 与 Agent 在 change 分支上的提交行为，属 Agent/平台治理类别，强制 complex
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-loop-controller-pr-url-260823.md
  spec: spec-loop-controller-pr-url-260823.md
  plan: plan-loop-controller-pr-url-260823.md
  verification: verification-loop-controller-pr-url-260823.md
---

## 问题/需求总结

Issue #142 把 `pr_url` 回填变成确定性命令并加了闸门，但只覆盖人/Claude 交互路径。Loop/Controller 路径上这件事完全没落地，而那恰恰是**唯一一处 PR 号自动可得的地方**：

`controller.py:356-366` 拿到 `pr["number"]`、把 Gitea 标签推进到 `pr-open`，却不碰 summary 的 `pr_url` 与 `status`。#142 交付的 `backfill_pr_url()` 就在 `documents.py` 里，没有调用方。

后果是 Loop 产出的变更会**安静地永远缺 `pr_url`**——正是 #142 要消灭的静默漏做，换到了自动化路径上，而且 #142 的闸门恰好照不到它（summary 的 `status` 停在 `approved`，检查只在 `pr-open`/`completed`/`deployed` 时才要求 `pr_url` 非空）。

同时存在一处记录分裂：Gitea 标签说 `pr-open`，summary front matter 说 `approved`，同一个事实两处记录只更新了一处。

## 影响范围

- `codex/runtime/aisoft_loop/controller.py`：`create_pr` 之后回填并提交、推送；`LocalGit` 新增一个受限的提交方法；
- `codex/runtime/aisoft_loop/documents.py`：新增按 PR 号回填的入口；
- `codex/runtime/tests/test_controller.py`、`test_documents.py`：正向、幂等、失败升级与「只提交声明路径」的负向覆盖；
- `skill-for-codex/` 与 `codex/skills/`：说明该步骤已自动完成，不是新增人工步骤。

不改 #142 已裁决的「`pr_url` 只写 summary」，不改 `backfill_pr_url()` 的幂等与 fail-closed 语义。

## 初步方案与建议

在 `create_pr` 与 CI 轮询之间插入回填：写 summary → 只提交那一个文件 → push → 用新的 `head_sha` 继续轮询 CI。附带收益是 CI 证据从此对应分支真实 HEAD。

## 风险

- **Controller 首次产生自己的 commit**。此前 change 分支上的所有 commit 都来自 provider 并受 `validate_provider_commit` 校验。提交路径必须窄到只能提交那一个文件，且有负向测试钉住。
- **失败处置**。summary 缺 `pr_url` 键或已有不同值时 `backfill_pr_url` 会 fail-closed；Controller 必须把它变成可判读的升级，而不是崩溃。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
```

强制规则命中：改动 controller 与 Agent 提交行为（Agent/平台治理维度）。→ 需 summary + spec + plan + verification。

## 证据

- `controller.py:356-366`：建 PR、取号、推进标签，无 summary 写入；
- `controller.py:185`：`provider_base_sha = self.git.head_sha()` 在**每轮开头**取值——这一条推翻了 Issue 正文对两条约束的判断，见 spec §2；
- `controller.py:596-640`：`LocalGit` 只有 `push`/`head_sha`/`validate_provider_commit`，没有提交方法；
- `_revalidate` 经 `load_contract` 从 **Gitea 标签**读生命周期，不读 summary 的 `status`——因此写 `status` 不与之打架。

## 缺失验收标准

- 无；Issue 正文验收标准逐条可测，spec §8 给出映射。
