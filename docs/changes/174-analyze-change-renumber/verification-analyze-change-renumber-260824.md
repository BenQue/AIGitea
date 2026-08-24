---
issue: 174
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/174
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - agent-governance
depends_on: []
status: passed
branch: change/174-analyze-change-renumber
created: 2026-08-24
updated: 2026-08-24
---

# Verification · 消除 gitea-analyze-change 条目编号的源/渲染歧义

## 基线与范围

- 基线：`origin/main` = `5faffa7`（#169 合并 #168 之后的第一个变更）
- 分支：`change/174-analyze-change-renumber`，worktree `issue-174-analyze-change-renumber`
- 环境：macOS 26.5.2 (arm64) · Python 3.14.4 · GNU bash 3.2.57 · ripgrep `/opt/homebrew/bin/rg`
- 日期：2026-08-24
- 本记录负责证明的 acceptance criteria：AC-1 … AC-4（全部）

声明 `verification` 的原因是 AC-2 的证据来自 **required CI 不跑的跨仓扫描**及其逐条
归属判定，且未改动的引用在 diff 里根本不出现、reviewer 无法从 diff 确认它们被核对过
（判据见 `03` §3「何时声明 `verification`」）。本次**不部署、不迁移**，故无 `## 部署验收` 一节。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `grep -n '^[0-9]\+\.' codex/skills/gitea-analyze-change/SKILL.md`（改动前） | 基线已记录 | 序号序列 `1..10, 11, 11, 12`——第 50、51 行并列 `11.`，第 52 行 `12.` 实为第 13 项 |
| `grep -n '^[[:space:]]\+[0-9]\+\.' codex/skills/gitea-analyze-change/SKILL.md` | PASS（exit 1，零命中） | 全文件只有一个顶层有序列表，无嵌套有序列表，重编号范围因此封闭 |
| `grep -n '^[0-9]\+\.' codex/skills/gitea-analyze-change/SKILL.md`（改动后）+ Python 断言 | PASS | `AC-1 sequence: [1,…,13]` / `AC-1 == 1..13 : True` / `strictly increasing, no dup: True` |
| `diff <(git show HEAD:…/SKILL.md \| sed 's/^[0-9]\{1,\}\./N./') <(sed 's/^[0-9]\{1,\}\./N./' …/SKILL.md)` | PASS（空输出） | 行首序号归一化后两版逐字节相同 ⇒ 除序号外零文本变化 |
| `git grep -n "第 1[0-9] 条\|item 1[0-9]" origin/main -- .` | PASS（6 命中） | **AC-2「既有」引用的全集**，锚定基线 `5faffa7`，天然不含本 change 自身文档；逐条判定见下表 A |
| `grep -rn "第 1[0-9] 条\|item 1[0-9]" .`（排除 `.git/`，本 worktree） | PASS（16 命中） | 6 处既有 + 10 处由本 change 自身文档产生（summary 3、verification 7）；见下表 B |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli resolve-documents 174 --repo .` | PASS | 四个语义角色全部解析到真实 basename |
| `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .` | PASS | `result: changes=78 pass=2 gap=0` |
| `bash codex/tests/smoke.sh`（最终树，含全部新增文档） | PASS（exit 0） | `Ran 520 tests in 29.590s` / `OK` / `Codex platform static smoke checks passed.`（实现落地后先跑过一次 `Ran 520 tests in 30.318s` / `OK`，文档补齐后重跑以覆盖最终树） |
| `bash codex/tools/apply-classification-labels.sh --repo . --verify 174`（`--apply` 前） | 基线已记录 | `reason: projection-missing` / `Observed: type=<none> complexity=<none>` |
| `bash codex/tools/apply-classification-labels.sh --repo . --apply 174` | PASS | `applied:true, result:"updated", change_type:"platform", complexity:"complex"` |
| `bash codex/tools/apply-classification-labels.sh --repo . --verify 174`（`--apply` 后） | PASS（exit 0） | `result:"projected"` / `Issue #174 carries the classification its merged summary declares` |

命令与输出照实抄。`grep` 的 exit 1 是「零命中」而不是失败，判据写在该行结果里。

## AC-2 逐条归属判定

**判定方法**：本次只改**源文件**编号（第 51 行 `11.`→`12.`，第 52 行 `12.`→`13.`）。
Markdown 有序列表只用首项数字定序，其余按位置重编号，因此**渲染编号修改前后同为
`1`…`13`，一个都没动**。由此得到唯一的判定规则：

> 只有「指向本文件」**且**「按源文件数字写下」**且**「指向第 51/52 行那两项」的引用才会位移。
> 三个条件缺一即不位移。

对每一处命中，先读其**上下文**确定指代绑定到哪个文件（`139/plan:67` 的「同文件」
就必须回看其上第 64 行），再套用上述规则。

### A. 既有引用（6 处，锚定基线 `origin/main` = `5faffa7`）

| # | 命中位置 | 原文 | 归属判定 | 结论 |
|---|---|---|---|---|
| 1 | `docs/changes/139-push-lease-doc-sync/plan-push-lease-doc-sync-260822.md:67` | 「同文件第 12 条明确「Do not push… The deterministic Controller owns remote mutation」」 | **指向其它文件**。「同文件」由同一 bullet 的第 64 行 `codex/skills/gitea-implement-change/SKILL.md:18` 绑定，指的是 **gitea-implement-change**，不是本文件。核对该文件第 20 行确为 `12. Do not push, change labels, open/merge PRs, or deploy. The deterministic Controller owns remote mutation…`，引文逐字吻合。本文件第 12 条（改动后）是 `For needs-human-decision…`，与引文无关 | **不动**（AC-2「指向其它文件的不动」；亦属 spec §5 非目标） |
| 2 | `docs/changes/168-decouple-verification-authoring/plan-decouple-verification-authoring-260824.md:28` | 「`gitea-analyze-change` 第 10 条」 | **指向本文件**，但指的是第 10 项（第 49 行，源号 `10.`，渲染 10）。重编号起点在第 51 行，第 10 项源号与渲染号均未变 | **不动**（指向本文件但未位移） |
| 3 | `docs/changes/168-…/spec-decouple-verification-authoring-260824.md:53` | 「`codex/skills/gitea-analyze-change/SKILL.md` 第 10 条、」 | 同 #2：**指向本文件**第 10 项，未位移 | **不动** |
| 4 | `docs/changes/168-…/spec-decouple-verification-authoring-260824.md:91` | 「`codex/skills/gitea-analyze-change/SKILL.md`：仅改第 10 条句子。」 | 同 #2：**指向本文件**第 10 项，未位移 | **不动** |
| 5 | `docs/changes/168-…/spec-decouple-verification-authoring-260824.md:114` | 「不修复 `gitea-analyze-change/SKILL.md` 里两个并列的 `11.` 编号：改动号码会使 Issue 与历史文档里「第 10 条 / 第 12 条」的引用失效，需要独立验收标准，另开 Issue。」 | **指向本文件**，但它不是对某条目的**活引用**，而是 #168 §6 记录「当时为何不做」的**历史决策**。其中「第 10 条」对应本表 #2–#4（未位移），「第 12 条」对应本表 #1（指向 gitea-implement-change）——即该行当时担心的失效在事实上没有发生 | **不动**。改写已合并变更的非目标声明会篡改历史记录；且违反 AC-3「除编号数字与引用数字外无其它文本变化」；亦属 spec §5 显式非目标 |
| 6 | `docs/changes/168-…/verification-decouple-verification-authoring-260824.md:76` | 「`gitea-analyze-change` 第 10 条改为 `append verification when…`」 | 同 #2：**指向本文件**第 10 项，未位移。且这是已合并变更的验证记录，本身不得回填 | **不动** |

**既有引用需要修改的处数：0。** 这是逐条判定的**结论**，不是「没查到就跳过」——
6 处全部读过上下文并留下判定理由：1 处指向其它文件，5 处指向本文件但都锚定在未位移的第 10 项
（或为历史决策记录）。

### B. 本 change 自身文档产生的自指命中（10 处，不属 AC-2 的「既有」范围）

写下 A 表本身就要**引述**那些引用，所以本 change 的文档必然命中同一 pattern。
这是自指产物，不是需要同步更新的引用。为免被误读成遗漏，逐文件记录：

| 文件 | 命中数 | 性质 |
|---|---|---|
| 本 change `summary-…-260824.md` | 3 | `:38`「「第 12 条」在源文件里指最后一项…」= 问题陈述，描述**修复前**的歧义本身；`:41`「写「同文件第 12 条」」= 引述 A#1 原文以说明歧义会咬人；`:95`「按 SKILL 第 10 条要求」= 指向本文件第 10 项（`Use stable risk_flags names…`），未位移，按修复后编号写下即正确 |
| 本 change `verification-…-260824.md`（本文件） | 7 | 全部出现在 A 表的「原文」列与判定理由里，即**被判定对象的引文**，不含任何新的按序号引用 |

`git grep … origin/main` 之所以是 AC-2 的正确锚点：它取**基线树**，天然排除本 change
自身的自指命中，且任何 reviewer 都能逐字复现，不受本 change 文档字数增减影响。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 改动后 `grep -n '^[0-9]\+\.'` 序号序列为 `[1,2,…,13]`，Python 断言 `== 1..13`、严格递增、无重复均为 `True`；渲染结果同为 `1`…`13`，源/渲染一致。另确认全文件无嵌套有序列表（`^[[:space:]]\+[0-9]\+\.` 零命中），不存在第二处需要重编号的列表 |
| AC-2 | PASS | 「既有」全集锚定基线（`git grep … origin/main` = **6 处**），**逐条**归属判定见上节 A：#1 指向 `gitea-implement-change`（其它文件）→ 不动；#2–#4、#6 指向本文件第 10 项但未位移 → 不动；#5 指向本文件但为 #168 的历史决策记录 → 不动。需要修改的既有引用 **0 处**。工作树另有 10 处自指命中（本 change 的 summary 与 verification 引述被判定对象所致），见上节 B |
| AC-3 | PASS | 行首序号归一化后 `diff` **空输出**，证明除序号数字外零文本变化；`git diff` 仅一个 hunk、两对 `-`/`+` 行，配对后仅行首 `11.`→`12.`、`12.`→`13.` 不同。引用数字实际改动 0 处（AC-2 判定结果），故 diff 中除 `SKILL.md` 两个数字外只有本 change 的新增文档 |
| AC-4 | PASS | 最终树 `bash codex/tests/smoke.sh` exit 0：`Ran 520 tests in 29.590s` / `OK` / `Codex platform static smoke checks passed.` |

## 遗留风险与未完成项

- **无未执行项**，无不可达环境。所有 AC 均由本机真实执行的命令支撑。
- 已知同类问题（范围外，未处理）：本次只核对了 `gitea-analyze-change/SKILL.md`。
  其它 SKILL 文件若存在同类源/渲染编号不一致，按 Issue #174「范围外」各自开 Issue。
  顺带确认：`gitea-implement-change/SKILL.md` 的顶层序号为 `1..12` 连续无重复，不存在同类问题。
- 判级投影已在合并前完成并读回 `projected`（见执行结果末三行），窗口未遗漏。
