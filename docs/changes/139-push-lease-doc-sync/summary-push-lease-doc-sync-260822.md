---
issue: 139
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/139
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 Claude skill 中 agent 的推送/失败恢复行为指导与平台运维合同文档，属 Agent 与平台治理变更
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
documents:
  summary: summary-push-lease-doc-sync-260822.md
  spec: spec-push-lease-doc-sync-260822.md
  plan: plan-push-lease-doc-sync-260822.md
confidence: high
override_reason: ''
depends_on:
  - 136
status: pr-open
branch: change/139-push-lease-doc-sync
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/140
created: 2026-08-22
updated: 2026-08-22
---

## 问题/需求总结

Issue #136 / PR #137（已由 `admin` 于 2026-08-22T11:13 合并，merge commit `760497e`）把
`git.push.change` 改为 `--force-with-lease=refs/heads/<branch>:<remote-sha>` 并新增错误码
`REMOTE_BRANCH_MOVED`。runtime 合同已变，两处治理文档仍描述旧语义：

| 位置 | 现状 | 问题 |
|---|---|---|
| `skill-for-claude/SKILL.md` 第 5 条 | Issue #99 AC-1 定下的保守表述：`BASE_BRANCH_STALE` → 停止当前实现 pass，由 Controller 重建候选，「Agent 不直接 fetch/rebase/push」 | 该表述的成因之一正是 #136 修掉的互锁；修复后「取新基线 → rebase → 重推」可行，旧指导会让 agent 在可自行恢复时无谓停机 |
| `06-运维手册与踩坑集.md` broker 段落 | 只有 Issue #73 的 remote 解析约束 | 既未记录新推送语义与新错误码 `REMOTE_BRANCH_MOVED`，也未记录「三条约束互锁」这个历史故障本身 |

全仓（排除 `archive/` 与 `docs/changes/136-*`）grep `REMOTE_BRANCH_MOVED` 与 `force-with-lease`
均为零命中，`BASE_BRANCH_STALE` 只出现在 `skill-for-claude/SKILL.md` 与 #99 的 spec 中。

## 影响范围

- `skill-for-claude/SKILL.md`：第 5 条重写，并拆出第 6 条描述 `REMOTE_BRANCH_MOVED`。
- `06-运维手册与踩坑集.md`：broker 段落（Issue #73 段之后）新增四段。
- 只读核对但不修改：`codex/skills/`、`skill-for-codex/`（结论见 plan 的「测试与验收映射」）。
- 无 runtime、CI、部署脚本、标签或分支保护影响。

## 初步方案与建议

`skill-for-claude/SKILL.md` 第 5 条改为完整恢复路径：broker `git.fetch.main` → 本地
`git rebase origin/main` → broker `git.push.change` 重推，并保留 #99 的真实治理边界
——**remote 访问只走 broker**。#99 把 rebase 与 fetch/push 并列禁止，但 rebase 是纯本地操作、
不触达 remote；它当初被连带禁止是因为 rebase 之后推不上去，而这一点已被 #136 修掉。
新增第 6 条说明 `REMOTE_BRANCH_MOVED`：远端在 lease 读取后被改动，推送**被拒绝而非覆盖**，
处置是重新 fetch 看清变化，而非提高 force 力度。

`06` 在 Issue #73 段之后新增四段：互锁故障复盘、新的 lease 推送语义、新错误码、生效边界。

## 风险

- **放宽过头**：本变更只把 rebase 从禁止改为允许，`BASE_BRANCH_STALE` 与 `MERGE_COMMIT_DENIED`
  两条检查在 runtime 侧未变，文档也明确写出这一点，不会被读成放宽基线新鲜或线性历史要求。
- **与 #99 的治理意图冲突**：#99 AC-1 的核心是「不直接 fetch/push」，属 remote 访问边界，
  本变更完整保留；只解除 rebase 这一项本地操作的连带禁止，并在文中给出理由。
- **文档描述未生效的行为**：installed broker 尚未重装，实机仍是旧语义。本变更在 `06` 中
  显式记录这一生效边界，而非默认读者已知。
- **全局 skill 漂移**：仓库源与已安装的 `~/.claude/skills/aisoft-platform/` 不同步（后者停在
  #99 之前）。本变更只改仓库源；安装是独立步骤，不在此静默改写。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 修改 Claude skill 中 agent 的推送/失败恢复行为指导与平台运维合同文档，属 Agent 与平台治理变更
risk_flags:
  - platform-governance
  - agent-governance
required_docs:
  - summary
  - spec
  - plan
confidence: high
override_reason: ''
```

### 判级证据

- `change_type: platform` 属 `codex/runtime/aisoft_loop/classification.py` 的
  `FORCED_COMPLEX_TYPES`（`feature`/`platform`/`security`/`data`），强制 complex，无 small 候选空间。
- `contract_effect: change` 独立触发强制 complex：新表述允许 agent 在 `BASE_BRANCH_STALE` 后
  本地 rebase 并重推，这不是恢复 #99 之前的行为（旧行为不经 broker），而是一份新的行为合同。
- `required_docs` 不含 `verification`：本变更纯文档、无部署动作。按 `classification.py` 中
  `route()` 的既有语义，`required_docs` 含 `verification` 同时表示「该变更要部署、终态是
  `deployed` 而非 `completed`」（见该处注释与 `mark-completed-issues.sh`）。先例为 Issue #99
  （skill/治理文档对齐，summary/spec/plan）；对照 #134/#136 因有部署影响而含 `verification`。
- `aisoft-platform` 在 `codex/config/gitea-governance.json` 未声明 `change_control`，按 Issue #134
  的默认按 `production` 处理，complex 的 `spec`/`plan` 不可省。
- 依赖已满足：PR #137 已由人合并进 `main`，`--force-with-lease` 与 `REMOTE_BRANCH_MOVED`
  已是 source 合同的一部分。

### 缺失的 acceptance criteria 或决策

- 无。Issue #139 正文已给出七条可测验收标准。
