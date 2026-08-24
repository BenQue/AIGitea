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
status: approved
branch: change/174-analyze-change-renumber
created: 2026-08-24
updated: 2026-08-24
---

# Spec · 消除 gitea-analyze-change 条目编号的源/渲染歧义

## 1. 目标与原因

`codex/skills/gitea-analyze-change/SKILL.md` 顶层有序列表的源文件编号是
`…10. / 11. / 11. / 12.`，渲染结果是 `…10 / 11 / 12 / 13`。

Markdown 的有序列表只用**首项**数字定序，其余标记按位置重编号，所以两套编号
从第二个 `11.` 开始分叉。目标是让源文件编号与渲染结果一致，从而使「第 N 条」
这种引用在两种读法下指向同一条目。

之所以值得单独做：仓库里**存在**按序号引用 SKILL 条目的既有做法，歧义会真实咬人。
#168 在其 spec §6 已把它列为非目标，理由是「改动号码会使既有引用位移，
需要独立验收标准」——本 Issue 就是那份独立验收标准。

## 2. Acceptance criteria

采纳 Issue #174 正文的 AC-1..AC-4，正文为准。

- [ ] **AC-1** `codex/skills/gitea-analyze-change/SKILL.md` 的有序列表编号连续、无重复，
      与渲染结果一致。判定：`grep -n '^[0-9]\+\.'` 取出的数字序列等于 `1..13`，
      严格递增且无重复。
- [ ] **AC-2** 因重编号而位移的条目，其在仓库里的既有按序号引用同步更新。逐条核对
      `grep -rn "第 1[0-9] 条\|item 1[0-9]"` 的结果：指向本文件的更新，指向其它文件的
      不动，并在映射的 verification 文档里写明**每条**的归属判定（命中位置、
      「本文件 / 其它文件」、以及改或不改的理由）。
- [ ] **AC-3** 条目**内容**一字不改。`git diff` 里除编号数字与引用数字外无其它文本变化。
      判定：对 `SKILL.md` 的 diff 做 hunk 级核对，每个 `-`/`+` 行配对后仅行首序号不同。
- [ ] **AC-4** `bash codex/tests/smoke.sh` 全绿。

## 3. 接口、数据与兼容性影响

**Agent 行为文件修改授权（AGENTS.md 要求的显式授权）**：本 spec 授权本次变更修改
`codex/skills/gitea-analyze-change/SKILL.md`，且**仅限**其顶层有序列表的行首序号数字。
不授权修改该文件的任何条目文本、条目顺序、条目数量，也不授权修改任何其它治理文件。
本次不修改 `AGENTS.md`、controller、CI/部署脚本。

- **对 analyzer 行为的影响：无。** 渲染结果修改前后同为 `1`…`13`，条目文本逐字不变，
  模型与人读到的行为合同不变。
- **对既有引用的兼容性：无位移。** 只有按**源文件数字**写下、且指向第 51/52 行那两项的
  引用会位移；仓库里不存在这样的引用（逐条判定见 verification）。按渲染结果写下的
  引用一律继续成立。
- **数据/schema/外部契约/认证授权：不涉及。**
- **CI：** 无新增或修改的 workflow；`.gitea/workflows/ci.yml` 的 required context 不变。

## 4. 风险与回滚约束

| 风险 | 处置 |
|---|---|
| 误改指向**其它** SKILL 文件的序号引用 | AC-2 要求逐条写明归属判定；`139/plan:67` 的「同文件」由其上文第 64 行绑定，必须读上下文而不是只看命中行 |
| 顺手改动条目语义 | AC-3 把 `git diff` 限死在数字上，hunk 级核对 |
| 把「零处需要改」当成「没查」 | AC-2 要求 6 处命中**全部**留下判定记录，含不改的理由 |

回滚：单个 commit，`git revert` 即可。无数据迁移、无部署、无外部契约、无状态。

## 5. 非目标

- 不改其它 SKILL 文件的编号（如 `gitea-implement-change/SKILL.md`）。如有同类问题各自开 Issue。
- 不改任何条目的语义、顺序，不增删条目。
- 不改 `docs/changes/` 下历史变更文档中与本歧义无关的内容。
- 不改 `docs/changes/168-decouple-verification-authoring/spec-*.md:113-114` 的非目标声明：
  那是 #168 当时决策的**历史记录**，不是对某条目的活引用；改写它会篡改已合并变更的
  记录，且违反 AC-3。
- 不引入 Markdown lint 或编号检查的自动化工具——那是新增能力，需要独立验收标准。

## 6. 未决问题

无。
