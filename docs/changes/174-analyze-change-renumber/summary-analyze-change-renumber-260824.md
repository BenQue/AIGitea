---
issue: 174
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/174
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
reason: 修改 codex/skills/gitea-analyze-change/SKILL.md 这一 Agent 行为文件，命中 AGENTS.md「Agent 或平台治理变更一律按 complex」的强制规则；条目语义不变只使 contract_effect 落在 small 候选，强制规则优先级更高
risk_flags:
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-analyze-change-renumber-260824.md
  spec: spec-analyze-change-renumber-260824.md
  plan: plan-analyze-change-renumber-260824.md
  verification: verification-analyze-change-renumber-260824.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/174-analyze-change-renumber
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/181
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

`codex/skills/gitea-analyze-change/SKILL.md` 的顶层有序列表里，第 50、51 行都写 `11.`，
第 52 行写 `12.`。Markdown 渲染器按**位置**重新编号，只有列表首项的数字参与定序，
因此实际渲染成 `11`、`12`、`13`。

结果是源文件里的数字与渲染结果不一致：「第 12 条」在源文件里指最后一项、
在渲染结果里指 `document_slug` 那一项。仓库里存在按序号引用 SKILL 条目的既有做法
（`docs/changes/139-push-lease-doc-sync/plan-push-lease-doc-sync-260822.md:67`
写「同文件第 12 条」），所以这个歧义会真实咬人，不只是排版瑕疵。

由 #168 的实现过程发现，#168 已在其 spec §6 把它显式列为非目标。

## 影响范围

- `codex/skills/gitea-analyze-change/SKILL.md`：两个数字。第 51 行 `11.` → `12.`，
  第 52 行 `12.` → `13.`。条目文本、顺序、数量一字不改。
- **渲染结果不变**：修改前后都渲染成 `1`…`13`。这把既有引用的失效面压到最小。
- 既有按序号引用：`grep -rn "第 1[0-9] 条\|item 1[0-9]"` 命中 6 处（tracked 文件），
  逐条归属判定后 **0 处需要修改**，判定过程记入映射的 verification。

## 初步方案与建议

把源文件编号对齐到**已经正确的**渲染编号，而不是反过来。两处纯数字替换即可。

关键判断：既然渲染编号前后都是 `1`…`13`，任何**按渲染结果**写下的引用都不会失效；
只有**按源文件数字**写下的、且指向第 51/52 行那两项的引用才会位移。仓库里不存在
这样的引用，因此 AC-2 的正确结果是「逐条判定、零处改动」，而不是「找不到就跳过」。

## 风险

低，且风险方向与直觉相反：真正的风险不是「改坏了引用」，而是**漏判**——
把某条指向别处的引用误改，或把该判定的引用当成不相关而不记录。
因此 AC-2 要求逐条写明归属判定，AC-3 要求 `git diff` 里除编号数字与引用数字外
无其它文本变化，两条互为约束。

回滚：`git revert` 单个 commit 即可，无数据、无部署、无外部契约。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
reason: 修改 codex/skills/gitea-analyze-change/SKILL.md 这一 Agent 行为文件，命中 AGENTS.md「Agent 或平台治理变更一律按 complex」的强制规则；条目语义不变只使 contract_effect 落在 small 候选，强制规则优先级更高
risk_flags:
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

- **强制 complex 的条件**：`AGENTS.md`「新增功能、功能性更改、…，以及 Agent 或平台
  治理变更一律按 complex 处理」。本次修改的 `codex/skills/gitea-analyze-change/SKILL.md`
  是 analyzer 的 Agent 行为文件，直接命中该条。`risk_flags: agent-governance`
  按 SKILL 第 10 条要求，直接指名这一个被命中的强制条件。
- **优先级**：SKILL 第 8 条规定按「forced-complex risk → explicit complex →
  validated explicit small → AI assessment」取值。`contract_effect: unchanged`
  使本次成为 small 候选，但强制规则先行，故 `effective_complexity: complex`。
- **`contract_effect: unchanged` 的依据**：AC-3 禁止改动任何条目语义；渲染结果
  修改前后同为 `1`…`13`，analyzer 读到的行为合同逐字不变。既不是 `restore`
  （没有被破坏的产品合同需要恢复），也不是 `add`/`change`。
- **声明 `verification` 的依据**：`03` §3「何时声明 `verification`」的判据是
  **验收证据的来源**。AC-2 的证据是一次 `grep -rn` **跨仓扫描**及其逐条归属判定，
  required CI（`.gitea/workflows/ci.yml` 只跑 `bash codex/tests/smoke.sh`）不跑它；
  而且未改动的 5 处引用在 diff 里根本不出现，reviewer 无法从 diff 确认它们被核对过。
  这正是该表第二行点名的「required CI 不跑的确定性命令（跨仓扫描）」。
  声明它表示本次**欠一份验证记录**，不表示本次要部署。
- **AGENTS.md 授权链**：AGENTS.md 规定「只有 complex 变更映射的 `spec` 明确授权时，
  才能修改 …Agent 行为…」。映射的 spec §「接口、数据与兼容性影响」显式授权本次对
  `codex/skills/gitea-analyze-change/SKILL.md` 的编号修改。本次不修改 `AGENTS.md` 本身。

### 缺失的 acceptance criteria 或决策

- 无。Issue #174 正文的 AC-1..AC-4 均可观察、可验证，直接采纳为映射 spec 的 acceptance criteria。
