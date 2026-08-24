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

# Verification · 把「何时声明 verification」的判据从题材换成证据来源

本记录本身就是 **AC-2 的交付物**：它照 T02 重构后的模板写成，`## 部署验收` 整节
按 `TEMPLATE_CONDITIONAL` 的指示删除，全文没有一个只能填「无」的部署专用段落。

## 基线与范围

- 基线：`origin/main` = `208b2bf`（#166 合并 #163 之后的第一个变更）
- 分支：`change/168-decouple-verification-authoring`，worktree `issue-168-decouple-verification-authoring`
- 环境：macOS 26.5.2 (arm64) · Python 3.14.4 · GNU bash 3.2.57
- 日期：2026-08-24
- 本记录负责证明的 acceptance criteria：AC-1 … AC-5（全部）

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `grep -rn "for deployment or migration\|部署或迁移再追加\|deploy/migration 必须" 03-*.md templates/docs/changes/_template/ codex/skills/ codex/agent/` | PASS（exit 1，零命中） | §「AC-3」 |
| `bash -n codex/agent/codex-analyzer.sh` | PASS | `codex-analyzer.sh OK` |
| `bash -n codex/agent/claude-analyzer.sh` | PASS | `claude-analyzer.sh OK` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .`（改动前，平台 checkout） | PASS | `result: changes=75 pass=2 gap=0` |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .`（改动后，本 worktree） | PASS | `result: changes=76 pass=2 gap=0` |
| `git status --porcelain docs/changes/` | PASS | 只有 `?? docs/changes/168-decouple-verification-authoring/` |
| `bash codex/tests/smoke.sh` | PASS（exit 0） | `Ran 520 tests in 26.838s` / `OK` / `Codex platform static smoke checks passed.` |

命令与输出照实抄。`grep` 的 exit 1 是「零命中」而不是失败，判据写在该行结果里。

### 改动前才观测得到的证据

`check-change-documents` 的 `changes=75`（改动前）与 `changes=76`（改动后）只有并排
才能证明「历史目录一个没少、只多出本 change 一个」。改动合并后 `75` 不可重放。

同样只在改动前成立的取证结论：耦合措辞的**真实分布**是 6 处而不是 Issue 点名的 2 处。
改动前的全仓扫描输出：

```
03-Issue-Spec-Plan与单闸门开发流程.md:64:└── verification-<slug>-YYMMDD.md  # deploy/migration 必须，其他推荐
codex/skills/gitea-analyze-change/SKILL.md:49:... include `verification` for deployment or migration work.
codex/agent/codex-analyzer.sh:45:... add verification for deployment or migration. ...
codex/agent/claude-analyzer.sh:43:... add verification for deployment or migration. ...
codex/skills/gitea-development-loop/SKILL.md:12:   - require mapped `verification` work for deployment or migration scope;
```

（第 6 处 `templates/docs/changes/_template/summary.md` 用的是中文「部署或迁移再追加」，
不在同一条英文 grep 的输出里。）

`codex/agent/*-analyzer.sh` 这两处是**真正喂给模型的 prompt**：只改
`gitea-analyze-change/SKILL.md` 而不改它们，新规则对实际生成 `required_docs`
的那个组件不生效。这条事实决定了本变更的范围，也是它没有停在 Issue 点名的两处的原因。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `03` §3 新增 `### 何时声明 verification`（`03:77`），含二行判定表与「声明 `verification` **不隐含要部署**，也不改变终态判定」一句，并显式指回 §11 的合取表。`git diff -U0 03-*.md` 的两个 hunk 头为 `@@ -64 +64 @@` 与 `@@ -76,0 +77,25 @@`，都落在 §3 内（§4 原起于第 77 行），§11 一个字未动 |
| AC-2 | PASS | 模板的部署内容由三个 `##` 段收敛为一节 `## 部署验收` + 三个 `###` 子项，并由 `TEMPLATE_CONDITIONAL` 注释指示「不部署的变更**整节删除**」；模板另补「不部署时的合格标准」一段。实例即本文档：`grep -nE '^#{2,3} (部署验收\|重复部署\|故意失败)' docs/changes/168-*/verification-*.md` 零命中 |
| AC-3 | PASS | 6 处措辞全部改写并与 AC-1 一致；退役措辞零命中（见执行结果第 1 行）。逐处：`03:64` 目录树注释改为「按下方「何时声明 `verification`」判定」；`summary.md` 末段改为「验收证据不能由 diff review 与 required CI 复现时再追加」；`gitea-analyze-change` 第 10 条改为 `append verification when the acceptance evidence cannot be reproduced by diff review and required CI`；两个 `*-analyzer.sh` 的 prompt 同义改写；`gitea-development-loop` 第 2 条第 3 项改为按映射 summary 的 `required_docs` 判定而不是重新推导部署范围 |
| AC-4 | PASS | `git status --porcelain docs/changes/` 只有本 change 的新目录，无一个历史文件被修改或重命名；`check-change-documents` 改动前 `changes=75 pass=2 gap=0`、改动后 `changes=76 pass=2 gap=0`，其中 `change-documents` 这一项对每个目录断言 `resolve-documents` 成功 |
| AC-5 | PASS | `bash codex/tests/smoke.sh` exit 0，`Ran 520 tests` / `OK`；两个改动的 shell 脚本 `bash -n` 通过。`smoke.sh:623-637` 对四个模板 front matter 的 7 字段断言随之通过——`verification.md` 重构时 front matter 原样保留 |

### 规则与 §11 的逐句比对（AC-1 的非冲突性）

| §11 的陈述 | §3 新小节的陈述 | 是否冲突 |
|---|---|---|
| 「`required_docs` 说的是这次变更欠不欠一份验证记录」 | 判据按「验收证据的来源」而不是题材 | 否，后者是前者的可执行化 |
| 「`deployment_lifecycle` 说的是这个仓库有没有那条会写 `deployed` 的链路」 | 未重复回答该问题；只声明「不隐含要部署」 | 否 |
| 表格第三行：含 `verification` + `none` → `completed` | 「`deployment_lifecycle: none` 的仓库声明了 `verification` 照样到 `completed`」 | 否，同一句 |
| 「不改变 `required_docs` 该不该含 `verification`」（#163 的自我限定） | 本变更正是补上那条被 #163 显式留白的规则 | 否，接续而非覆盖 |

### 本变更为什么自己声明了 `verification`

按新规则自判：AC-4/AC-5 的证据由 `smoke.sh` 复现（`smoke.sh:199` 已经跑
`check-change-documents --repo $ROOT`，而 CI 只跑 `smoke.sh`），落在判定表第一行；
但 **AC-2 的证据是一份「照新模板写出来的文档」**，实例无法从 diff 中读出，落在第二行。
合取取严，所以声明。这既是新规则的第一次自我应用，也是 #163 那张合取表
（`required_docs` 含 `verification` + `deployment_lifecycle: none` → `completed`）的第一次正向使用。

## 遗留风险与未完成项

- **未执行**：`resolve-documents` 未逐个目录手工重跑——它由 `check-change-documents`
  对全部 76 个目录代跑并断言（`smoke.sh:195-199` 的注释即此意）。单独重跑 76 次不会
  增加信息。
- **未执行**：CI 上的 `smoke.sh` 尚未跑（PR 未建）。本地 exit 0 是同一条命令、同一份
  仓库内容，但 runner 环境与本地不同（本地 `rg` 为 Homebrew 二进制），以 PR 的 CI 结论为准。
- **合并后待办，不是本 PR 交付物**：需重装 Claude/Codex skills 才能消除 `check-drift`
  漂移（`codex/skills/` 的三个文件已改）。与 #163 同形态，不阻塞终态判定。
- **判级投影**：`codex/tools/apply-classification-labels.sh 168 --apply` 必须在人合并
  **之前**跑完——工具对已关闭 Issue 永久跳过，#163 就是这样丢掉自己的 `type/*` 与
  `complexity/*` 标签的。**已完成**：`apply-classification-labels.sh --repo . --apply 168`
  返回 `{"issue":168,"action":"set-classification","applied":true,"result":"updated",
  "change_type":"platform","complexity":"complex"}`；`gitea.issue.labels.read --number 168`
  读回 `complexity/complex` 与 `type/platform` 两个标签。
- 本变更不部署、不迁移，因此没有制品、重复执行与故意失败回滚可记录——模板的对应
  整节按其 `TEMPLATE_CONDITIONAL` 指示删除，而不是保留标题填「无」。
