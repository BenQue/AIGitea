---
issue: 158
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/158
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/158-issue-session-flow
created: 2026-08-23
updated: 2026-08-23
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `skill-for-claude/` 迁到多技能布局，install/check-drift 遍历技能目录，现有 aisoft-platform 安装行为不变 | - | done |
| T02 | 新增 `skill-for-claude/issue-session-flow/SKILL.md`，并在 aisoft-platform SKILL.md 加交叉引用 | T01 | done |

T01 先行是因为 T02 的技能一旦落盘，旧版单技能 `install.sh` 会把它当作陌生文件 prune 掉。

**实际交付时两个 ticket 落在同一个 commit 里**：`skills.manifest` 把布局与技能集合绑成了
一个事实——声明了 `issue-session-flow` 而源不存在会让 `install.sh` fail closed，
`test-install-claude-skills.sh` 也同时断言两个技能。拆成两个 commit 会留下一个测试红的中间态，
那不是原子提交。合并方向仍是收敛的（两个 ticket 都在 plan frontier 内，没有扩大范围）。

## Expected touch points

T01：
- `skill-for-claude/SKILL.md` → `skill-for-claude/aisoft-platform/SKILL.md`（`git mv`，保留历史）
- `skill-for-claude/install.sh`
- `skill-for-claude/check-drift.sh`
- 引用上述路径的仓库内文档（以 grep 结果为准，不预设清单）

T02：
- `skill-for-claude/issue-session-flow/SKILL.md`（新增）
- `skill-for-claude/aisoft-platform/SKILL.md`（新增一行交叉引用）

范围提示，不授权扩大 spec。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `python3 -c` 解析 `skill-for-claude/issue-session-flow/SKILL.md` 的 front matter，断言 `name` 与 description 含六类触发词 |
| AC-2 | `git show HEAD~:skill-for-claude/SKILL.md \| diff - skill-for-claude/aisoft-platform/SKILL.md`，差异仅为交叉引用行 |
| AC-3 | `t=$(mktemp -d); bash skill-for-claude/install.sh "$t"` 两次；`diff -r` 两次快照；`bash skill-for-claude/check-drift.sh "$t"; echo $?` |
| AC-4 | 空 HOME 上 `check-drift.sh` 断言输出 `NOT_INSTALLED` 且 `$? -eq 0`；改一个已安装文件后断言输出含 `DRIFT` 且 `$? -eq 1` |
| AC-5 | 在受管技能目录内 `touch stray.md` 后重装，断言文件消失；在 `$t/.claude/skills/` 下放一个本仓库未声明的技能目录，断言重装后它**仍在** |
| AC-6 | `bash codex/tests/smoke.sh`（会话内 `rg` 是 shim，须先造 PATH shim，见风险） |
| AC-7 | `grep` 断言 SKILL.md 含 7 步收尾清单与两个陷阱关键词 |

AC-3/AC-4/AC-5 合并写成一个一次性验证脚本执行，输出留在 PR 描述里作为证据。

## 部署与回滚

无部署。本变更只增删仓库内文件；回滚为 `git revert` 该 PR。

合并后的**交接项**（不属于本 PR 范围，由人执行或在收尾会话中执行）：

```bash
bash skill-for-claude/install.sh
```

装完后**必须新开会话**技能才可见——技能列表在会话启动时加载。
