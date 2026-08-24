---
issue: 168
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/168
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on: []
status: pr-open
branch: change/168-decouple-verification-authoring
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/169
created: 2026-08-24
updated: 2026-08-24
reason: 改写 analyzer 指引、analyzer runtime prompt、Loop 合同校验与平台文档合同里「何时声明 verification」的作者规则，属 Agent 与平台治理变更，强制 complex
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-decouple-verification-authoring-260824.md
  spec: spec-decouple-verification-authoring-260824.md
  plan: plan-decouple-verification-authoring-260824.md
  verification: verification-decouple-verification-authoring-260824.md
---

## 问题/需求总结

#163 把「合并后的终态」与「要不要部署」解耦：`03` §11 现在是一张合取表，
`deployment_lifecycle: none` 的仓库声明了 `verification` 也能到 `completed`。
机器侧已经跟上——`classification.py:189` 的 `route()` 注释明确写着「这里只剩
「欠不欠验证记录」，change_control 不改变它」。

**作者侧没跟上**。决定 `required_docs` 的人（和模型）读到的仍然是解耦之前的句子，
于是「声明 verification」在作者眼里仍然等于「这次要部署」：

- `templates/docs/changes/_template/verification.md` 整体是部署形状——`## 环境与版本`
  （Artifact/Environment）、`## 重复部署`、`## 故意失败与回滚`。不部署的变更照它写，
  三段只能填「无」。
- 没有任何一条规则说「不部署时什么才算合格的验证记录」。

后果就是 Issue 正文举的那组证据：#138、#146、#148 声明了 `verification`，
#152、#158、#160、#163 不声明，两种做法并存而没有依据。

## 影响范围

耦合措辞不止 Issue 点名的两处。全仓扫描 `部署或迁移 / deployment or migration /
deploy/migration` 后，**作者与 Agent 面向**的出处共 6 个：

| 出处 | 现状 | 为什么必须改 |
|---|---|---|
| `03` §3:64 | `# deploy/migration 必须，其他推荐` | 文档合同的 canonical 出处，其它 5 处都是它的复述 |
| `templates/docs/changes/_template/summary.md` | 「部署或迁移再追加 `verification`」 | Issue 点名；作者填 `required_docs` 时看的就是它 |
| `templates/docs/changes/_template/verification.md` | 三段部署专用结构 | Issue 点名；AC-2 的直接对象 |
| `codex/skills/gitea-analyze-change/SKILL.md:49` | `include verification for deployment or migration work` | Issue 点名；analyzer 判级合同 |
| `codex/agent/codex-analyzer.sh:45`、`claude-analyzer.sh:43` | 同一句英文 | **真正喂给模型的 prompt**。只改 SKILL.md 而不改这两行，规则对生成 `required_docs` 的组件就不生效 |
| `codex/skills/gitea-development-loop/SKILL.md:12` | `require mapped verification work for deployment or migration scope` | 消费端。它按「是不是部署范围」而不是按 `required_docs` 判断，声明了 verification 的平台变更在 Loop 里不会被校验 |

**不改**（在新规则下依然成立，都是「部署 ⇒ verification」这个仍然为真的单向蕴含）：
`gitea-spec-plan/SKILL.md:16`、`gitea-platform-ops/SKILL.md:30`、`plan.md` 模板的
`## 部署与回滚`。**不改**（历史规划记录，仍用已退役的 `00-summary.md` 命名，
已被 `03` §3/§7 取代）：`09` §295。

代码零改动：`classification.py`、`contract.py`、`analysis.py`、`documents.py` 均不动，
`DOCUMENT_ROLES`、`ALLOWED_DOCS`、`resolve-documents`、`check-change-documents` 保持原样。

## 初步方案与建议

### 先回答「一个角色还是两个」：一个

拆成两个角色（部署验收 vs 变更验证记录）应当**否决**，理由按重要性排列：

1. **原则**：两个角色要区分的正是「这次要不要部署」。而「走不走应用部署链路」是
   **仓库属性**，#163 已经用 governance manifest 的 `deployment_lifecycle` 回答过一次
   （`03` §11「哪些仓库有部署链路」）。把同一个问题再编码成单次变更的文档角色，
   等于把 #163 刚拆掉的那层耦合按原样重建在另一个维度上。
2. **代价**：`DOCUMENT_ROLES` 硬编码在 `classification.py:27`、`contract.py:16`、
   `contract.py:26`（legacy 映射）、`contract.py:29`（文件名正则）、`analysis.py:131,192`
   共 5 处；新角色没有对应的 legacy 文件名，`LEGACY_DOCUMENTS` 会变成非对称的
   3 对 4；75 个历史 change 目录一个也不用新角色。
3. **收益**：为零。两个角色要区分的东西是记录里的**一节**，不是记录的**身份**——
   条件段落用零 schema 改动达成同一效果，并让 AC-4 自动成立。

### 一个角色下要补的两样东西

- **判据换轴**：从「变更的题材是不是部署/迁移」换成「验收证据的来源能不能由
  diff review 与 required CI 复现」。部署与迁移必然落在「不能」那一侧，所以旧规则
  是新规则的真子集——没有任何既有判断被推翻，只是覆盖了原先无人回答的那一半。
- **模板条件化**：部署三段合并为一节 `## 部署验收`，并用 `TEMPLATE_CONDITIONAL`
  注释明确「不部署时整节删除，不要留标题填「无」」；同时补上不部署时的合格标准
  （每条 AC 一条真实执行过的命令或一次真实观测、输出照抄、不可达项显式写明）。

### 本变更自身声明 `verification`

按新规则判：AC-4/AC-5 的证据由 `smoke.sh` 复现（`smoke.sh:199` 已经跑
`check-change-documents --repo $ROOT`，CI 只跑 smoke），落在「否」那一侧；但 **AC-2
只能由一份「照新模板写出来的文档」作证**，而那份实例不可能从 diff 里读出来。
本 change 的 verification 文档**就是**那份实例——它自身不含任何只能填「无」的部署段落。

这同时是对 #163 那张合取表的第一次正向使用：`required_docs` 含 `verification`
且 `deployment_lifecycle: none` → `completed`。

## 风险

- **规则更宽 → 有人滥用**。缓解：判据以「证据来源」为轴且给出否定形态（能由 diff +
  required CI 复现就不声明），而不是留一句「推荐」；声明后是否到达终态由 §11
  的合取表兜底，不会因为多声明而卡死在无人写终态的状态里——那正是 #163 修掉的。
- **改的是 Agent 行为文件**（analyzer prompt、Loop 合同）。缓解：spec §5 逐文件授权，
  改动限于措辞，`classification.py` 与 `route()` 一行不动；行为不变由 `smoke.sh`
  与 `check-change-documents` 对 75 个历史目录的全量通过作证。
- **回滚** = revert 本 PR。纯文档与 prompt 文本，无 schema、无迁移、无外部状态。
- **合并后**需重装 Claude/Codex skills 才能消除 `check-drift` 漂移（与 #163 同形态，
  不是本 PR 交付物，也不阻塞任何判定）。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改写 analyzer 指引、analyzer runtime prompt、Loop 合同校验与平台文档合同里「何时声明 verification」的作者规则，属 Agent 与平台治理变更，强制 complex
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

- `AGENTS.md`：「Agent 或平台治理变更一律按 complex 处理」。本变更修改
  `codex/skills/gitea-analyze-change/SKILL.md`、`codex/skills/gitea-development-loop/SKILL.md`
  与 `codex/agent/{codex,claude}-analyzer.sh`，全部是 Agent 行为文件。
- `classification.py:55` `FORCED_COMPLEX_TYPES` 含 `platform`；`route()` 另按
  `contract_effect in {add, change}` 强制 complex，本变更两条都命中。
- `contract_effect: change`：`required_docs` 的**填写规则**是作者面向的合同，
  本变更改变它的判据轴。机器侧行为不变，但作者侧合同确实变了，不是 `restore`。
- 复杂度不因「只是文档」下调：`03` §4 明确 `type/platform` 在改变平台行为或治理合同时强制 complex。

### 缺失的 acceptance criteria 或决策

- 无。AC-1..AC-5 在 Issue 正文中可测；「一个还是两个角色」这个唯一的开放决策由
  上文「先回答」段基于仓库证据判定为「一个」，并在 spec §6 列为非目标。
