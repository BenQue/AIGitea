---
issue: 139
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/139
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
depends_on:
  - 136
status: pr-open
branch: change/139-push-lease-doc-sync
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/140
created: 2026-08-22
updated: 2026-08-22
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `skill-for-claude/SKILL.md` 第 5/6 条按新推送语义重写（AC-1、AC-2） | - | done |
| T02 | `06-运维手册与踩坑集.md` broker 段落新增四段（AC-3） | - | done |
| T03 | `codex/skills/` 与 `skill-for-codex/` 只读核对与结论记录（AC-4） | - | done |
| T04 | grep 断言、smoke、diff 范围核对（AC-5、AC-6、AC-7） | T01, T02, T03 | done |

四个 ticket 互不阻塞（T04 汇总），单次 pass 内完成。

## Expected touch points

- T01：`skill-for-claude/SKILL.md`「会话标准动作」第 5 条，拆为第 5、6 条。
- T02：`06-运维手册与踩坑集.md`，Issue #73 段之后、adoption 闸门段之前。
- T03：只读，无文件改动。
- T04：只读断言，无文件改动。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `sed -n '/^5\. push 报/,/^6\. push 报/p' skill-for-claude/SKILL.md`——确认含 `git.fetch.main`、`git rebase origin/main`、`git.push.change` 三步与「remote 访问始终只走 broker」 |
| AC-2 | `grep -n "REMOTE_BRANCH_MOVED" skill-for-claude/SKILL.md`——确认含「推送已被拒绝，远端没有被覆盖」与「不要试图用更强的 force 绕过去」 |
| AC-3 | `sed -n '/^Issue #136 解开/,/^新项目或已有项目 adoption/p' 06-运维手册与踩坑集.md`——逐项核对 (a)(b)(c)(d) 四点 |
| AC-4 | 见下「codex 侧核对结论」 |
| AC-5 | `grep -c "REMOTE_BRANCH_MOVED" skill-for-claude/SKILL.md 06-运维手册与踩坑集.md` 均 ≥1；`grep -n "不直接 fetch/rebase/push" skill-for-claude/SKILL.md` 无命中 |
| AC-6 | `bash codex/tests/smoke.sh`；`git diff --stat origin/main` |
| AC-7 | 见下「部署与回滚」 |

### codex 侧核对结论（AC-4）

对 `codex/skills/`（6 份 SKILL.md）与 `skill-for-codex/`（SKILL.md + 3 份 references）grep
`git.push.change` / `git.fetch.main` / `BASE_BRANCH_STALE` / `rebase` / `force-with-lease` /
`non-fast-forward` / `REMOTE_BRANCH_MOVED`，仅一处命中：

- `codex/skills/gitea-implement-change/SKILL.md:18`
  —— "do not amend published history, create merge commits, rebase or change branches"。
  **结论：不改。** 该 skill 治理的是 Controller/worker 分工中的 **implement worker** 角色，
  同文件第 12 条明确「Do not push… The deterministic Controller owns remote mutation」。
  worker 从不执行 push，所以这里的禁止 rebase 是**角色边界**，与 #136 修掉的互锁无关：
  worker 若 rebase，会重写 Controller 正要据以对账的历史。#136 改变的是**推送时**的语义，
  而 worker 不推送。反之 `skill-for-claude/SKILL.md` 描述的 Mac 交互流程里 Claude Code 同时
  承担 worker 与 Controller，rebase→重推正是该流程的恢复路径，故只在该文件放开。

- `skill-for-codex/SKILL.md` 及其 references
  —— **结论：不改。** 属合同层表述，从不描述推送失败的具体错误码与恢复步骤
  （`BASE_BRANCH_STALE` 零命中），因此不存在需要纠正的过期表述；新增一节错误码处置属于
  Issue #139 范围之外的内容扩张。

- 其余 5 份 codex skills —— 零命中，无需改动。

## 部署与回滚

**本变更无部署动作。** 回滚为人工 revert PR，两份文档回到 #99/#73 表述，无主机操作、无残留副作用。

以下两项部署动作**本次明确不做**（AC-7）：

1. **不重装 Mac 与 gitea-ci VM 的 installed broker。**
   已核实 `/usr/local/lib/aisoft-host-access/aisoft_host_access/broker.py`（2026-08-15）不含
   `LEASE_REJECTION_MARKERS` 与 `force-with-lease`——#136 的 source 已并入 `main`，但实机仍跑旧
   字节，互锁在实机上依然存在。重装是部署动作，需独立授权，且按根 `AGENTS.md` 不能与治理文档
   变更同一 run 交付。该生效边界已写入 `06`。

2. **不重装或改写全局 `~/.claude/skills/aisoft-platform/`。**
   已核实其 `SKILL.md`（2026-08-11）落后于仓库源，仍是 Issue #99 之前的版本——第 5 条写的是
   「`git fetch && git rebase origin/main` 后重推」，与仓库源共 5 处差异（核心原则表述、legacy
   命名兼容措辞、small 判级补充条件、第 5 条、以及仓库源多出的「项目对齐」章节）。
   一致性策略：**仓库 `skill-for-claude/SKILL.md` 是唯一事实源，`~/.claude/skills/` 是部署产物**；
   本变更只改事实源，安装是独立步骤，届时需一次补齐 #99 与本变更两个版本的差异。在此静默改写
   全局 skill 会绕过该独立步骤，且会在 PR 之外产生不可审的本地状态变更。
