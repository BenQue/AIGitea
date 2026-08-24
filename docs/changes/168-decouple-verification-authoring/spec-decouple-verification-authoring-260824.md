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
status: approved
branch: change/168-decouple-verification-authoring
created: 2026-08-24
updated: 2026-08-24
---

# Spec · 把「何时声明 verification」的判据从题材换成证据来源

- Issue：[#168](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/168)

## 1. 目标与原因

#163 只解耦了**读**的一半（合并后终态怎么判），**写**的一半没动：作者与 analyzer
读到的规则仍然是「部署或迁移再追加 `verification`」。本 spec 把写的一半也解耦，
使「声明 `verification`」的含义收敛到 `03` §11 已经写下的那句话——
「`required_docs` 说的是这次变更欠不欠一份验证记录」——并给出可执行的判据与可用的模板。

判据换轴，不是放宽：

| | 旧 | 新 |
|---|---|---|
| 问的是 | 变更的**题材**是不是部署/迁移 | 验收**证据的来源**能不能由 diff review + required CI 复现 |
| 部署/迁移 | 必须声明 | 必然落在「不能复现」侧，仍然必须声明 |
| 不部署但需要真实观测 | 无规则，两种做法并存 | 必须声明 |
| 不部署且证据可复现 | 「其他推荐」，含糊 | 明确不声明 |

旧规则是新规则的真子集：没有任何既有判断被推翻。

## 2. Acceptance criteria

- [ ] **AC-1** `03` §3 新增小节「何时声明 `verification`」，用一张二行判定表给出
      判据，并显式声明「声明 `verification` 不隐含要部署，终态由 §11 的合取表决定」。
      表述与 §11 不冲突。
- [ ] **AC-2** `templates/docs/changes/_template/verification.md` 的部署专用内容
      收敛为**一节** `## 部署验收`，并由 `TEMPLATE_CONDITIONAL` 注释指示「不部署时
      整节删除」；模板补上不部署时的合格标准。照该模板写出的文档不含只能填「无」
      的部署专用段落——本 change 映射的 `verification` 文档即为该实例。
- [ ] **AC-3** 以下 5 处措辞与 AC-1 的规则一致，且都不再把 `verification` 等同于部署：
      `03` §3:64 的目录树注释、`templates/docs/changes/_template/summary.md`、
      `codex/skills/gitea-analyze-change/SKILL.md` 第 10 条、
      `codex/agent/codex-analyzer.sh` 与 `codex/agent/claude-analyzer.sh` 的
      `required_docs` prompt、`codex/skills/gitea-development-loop/SKILL.md` 第 2 条第 3 项。
- [ ] **AC-4** 既有 change 文档不迁移、不重命名、不回填；`resolve-documents` 与
      `check-change-documents` 对全部历史目录仍然通过（改动前后同为 75 个目录、
      `pass=2 gap=0`）。
- [ ] **AC-5** `bash codex/tests/smoke.sh` 全绿；改动的两个 shell 脚本 `bash -n` 通过。

## 3. 接口、数据与兼容性影响

- **代码零改动**。`DOCUMENT_ROLES`、`ALLOWED_DOCS`、`LEGACY_DOCUMENTS`、
  `Classification.route()`、`resolve-documents`、`check-change-documents` 一行不动。
  `required_docs` 的取值集合、顺序约束与 legacy 兼容行为完全不变。
- **只增一个角色的判据，不增角色**。见 §6 非目标。
- `smoke.sh:623-637` 对四个模板 front matter 的 7 个字段断言必须继续通过：
  `verification.md` 重构时 front matter **原样保留**。
- `codex/agent/*-analyzer.sh` 只改一个单引号字符串字面量的内容，不改参数结构、
  不改引号形式、不引入 `'` 字符。

## 4. 风险与回滚约束

- 回滚 = revert 本 PR。纯文档、模板与 prompt 文本；无 schema、无迁移、无外部状态、
  无已写出的 Gitea 状态需要撤销。
- 本变更**不部署、不迁移、不改 CI 配置**，但 `required_docs` **含** `verification`：
  AC-2 的证据只能是一份照新模板写出来的实例，而实例不可能从 diff 中读出。
  这正是本 spec 要建立的规则的第一次自我应用。
- 合并后需重装 Claude/Codex skills 才能消除 `check-drift` 漂移（与 #163 同形态）。
  不是本 PR 交付物，也不阻塞终态判定。

## 5. 治理文件修改授权

按 `AGENTS.md`「只有 complex 变更映射的 spec 明确授权时，才能修改 `AGENTS.md`、
Agent 行为、controller、CI/部署脚本或其他治理文件」，本 spec 授权且**仅**授权：

- `03-Issue-Spec-Plan与单闸门开发流程.md`：仅改 §3 目录树第 64 行的注释，并在 §3
  末尾新增「何时声明 `verification`」小节。不动 §11 一个字。
- `templates/docs/changes/_template/verification.md`：仅重构正文段落结构，front matter 原样保留。
- `templates/docs/changes/_template/summary.md`：仅改末尾说明 `required_docs` 的那一段。
- `codex/skills/gitea-analyze-change/SKILL.md`：仅改第 10 条句子。
- `codex/skills/gitea-development-loop/SKILL.md`：仅改第 2 条的第 3 个子项，
  使校验依据从「是不是部署范围」改为「映射 summary 的 `required_docs` 含不含该角色」。
- `codex/agent/codex-analyzer.sh`、`codex/agent/claude-analyzer.sh`：仅改
  `required_docs` 那一句 prompt 字符串的内容。

不授权修改 `AGENTS.md`、`classification.py`、`contract.py`、`analysis.py`、controller、
CI 配置、broker 操作表、标签 manifest、判级复杂度判据，以及任何 `docs/changes/` 下的历史文档。

## 6. 非目标

- **不拆第二个 verification 角色**。理由见映射 summary 的「先回答「一个角色还是两个」」：
  两个角色要区分的「要不要部署」是仓库属性，#163 已用 `deployment_lifecycle` 回答；
  再编码成单次变更的文档角色即重建被拆掉的耦合。`ALLOWED_DOCS`/`DOCUMENT_ROLES`、
  `documents` 映射与 `resolve-documents` 因此完全不动。
- 不改 `mark-completed-issues.sh` 的终态判定与 `deployment_lifecycle` 声明（#163 交付物）。
- 不改判级复杂度判据本身，不改 `required_docs` 的取值集合与顺序约束。
- 不迁移、不重命名、不回填任何历史 change 文档或分支。
- 不改 `gitea-spec-plan/SKILL.md:16`、`gitea-platform-ops/SKILL.md:30`、
  `plan.md` 模板的 `## 部署与回滚`：它们陈述的是「部署 ⇒ verification 且需要
  两次重复与一次故意失败」，这个单向蕴含在新规则下依然成立。
- 不改 `09` §295：历史规划记录，仍用已退役的 `00-summary.md` 命名，已被 `03` §3/§7 取代。
- 不修复 `gitea-analyze-change/SKILL.md` 里两个并列的 `11.` 编号：改动号码会使
  Issue 与历史文档里「第 10 条 / 第 12 条」的引用失效，需要独立验收标准，另开 Issue。

## 7. 未决问题

无。
