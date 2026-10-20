---
issue: 397
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/397
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 391
status: pending
branch: change/397-ops-closure
created: 2026-10-20
updated: 2026-10-20
---

# #397 verification：运维闭环第二步（R16）

## 基线与范围

- 基线：`origin/main` = `08be6f44a67ddb755d840611ae249128b574b8b3`（R10a 合并）
- 环境：Mac（darwin，平台主检出与 worktree `/private/tmp/issue-397-ops-closure`）；VM `gitea-ci`（经 `/usr/local/bin/orb -m gitea-ci`，默认用户）
- 本记录负责证明 AC1–AC12；合并后的两台重装与读回（AC12）在收尾第 5 步补记。

## 改动前观测（合并后无法重放）

| Command / check | Result | Evidence |
|---|---|---|
| Mac `bash codex/tools/check-installed-drift.sh` | GAP | `install-skills` PASS（8/8）、`install-host-role` GAP（唯一一条 `symlink-parent`：`/etc/aisoft/host-profile.example.json`，capabilities 20/20）、`install-host-access-broker` PASS（34/34）、`architecture/install` GAP（全部 missing）、`sync/install` GAP（missing 与 `/etc` 的 symlink-parent）、`skill-for-claude/install` PASS |
| VM `orb -m gitea-ci bash /mnt/mac/.../check-installed-drift.sh` | GAP | `install-host-role` PASS、`install-host-access-broker` PASS（34/34）；`install-skills` 0/8、`skill-for-claude/install` 0/2（`/home/benque` 无技能）、`architecture/install`、`sync/install` 全部 missing |
| `git worktree list`（主检出） | 8 prunable | #308×2、#333、#342、#343、#344、#349、#358；另有 3 个 `.claude/worktrees/*` 分离头（最新 10-08）与在用的 #395、#396 |
| `git branch --list 'claude/*'` | 11 | 全部是 `origin/main` 祖先，最新提交 10-08 |
| `git branch -r` 中 `origin/change/*` | 61（59 已并入） | 本地 remote-tracking 引用，`git.fetch.main` 不 prune，可能陈旧 |
| `aigitea-cleanup-merged.sh` 默认 remote | `gitea` | 平台仓 remote 名为 `origin`，默认调用报 `missing gitea/main` |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC1–AC12 | 待填写 | 待填写 |
