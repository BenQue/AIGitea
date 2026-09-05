---
issue: 254
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/254
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - deployment
depends_on:
  - 250
status: verified
branch: change/254-claude-install-source-guard
created: 2026-09-05
updated: 2026-09-05
---

# Verification: skill-for-claude/install.sh 接入共用 source guard

## 基线与范围

- Commit SHA: dfad463（T01；本文件随 T02 提交）
- 基线：`origin/main` = 00f7d53481d5723fa63759a14d959ffbfb18bca2（PR 253，#250 合并）
- 环境：Mac 本机，worktree `/private/tmp/issue-254-claude-install-source-guard`，
  真实目标 `~/.claude/skills/`
- 本记录负责证明的 acceptance criteria：AC-9（只能在真实环境一次性观测到的证据）。
  AC-1 到 AC-8 由 required CI 与 diff review 复现，此处照抄本地执行结果。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/test-installer-source-guard.sh` | PASS | `installer source guard tests passed (8 installers x 3 source states)` |
| `bash codex/tests/test-install-claude-skills.sh`（改 fixture 前） | FAIL，预期内 | `FAIL: install must name the undeclared skill source`——`undeclared_root` 缺 `codex/lib`，installer 的新 source 行无法解析 |
| `bash codex/tests/test-install-claude-skills.sh`（改 fixture 后） | PASS | `claude skill install tests passed` |
| `bash codex/tests/smoke.sh` | PASS | `Ran 671 tests in 40.409s` / `OK` / `Codex platform static smoke checks passed.` |
| `shellcheck skill-for-claude/install.sh codex/tests/test-installer-source-guard.sh codex/tests/test-install-claude-skills.sh` | PASS | 无输出（shellcheck 0.11.0 可用；smoke 现状只对 `skill-for-claude/install.sh` 跑 `bash -n`，本次未改那份清单） |
| `grep -c 'rev-list --count' skill-for-claude/install.sh` | 0 | 没有第二份实现，判断全部来自共用库 |

### 真机安装（level 源）

```text
$ bash skill-for-claude/install.sh
source checkout:   /private/tmp/issue-254-claude-install-source-guard
source commit:     00f7d53 (level with origin/main)
source skills:     2
source references: 3
installed skill aisoft-platform in /Users/benque/.claude/skills/aisoft-platform
installed skill issue-session-flow in /Users/benque/.claude/skills/issue-session-flow
Claude skills installed from .../skill-for-claude/skills.manifest: aisoft-platform issue-session-flow
Shared references copied from skill-for-codex/references (single source).
Pruned 0 stale entries; each declared skill tree is exact.
Undeclared skills under .claude/skills were not read or modified.
No credentials, runtime, or provider state was installed.
exit=0
```

第二次执行（幂等路径）同样打印这四行 provenance，逐字节相同。

顺带观测到本 Issue 前提的一次实证：这次安装前后 `~/.claude/skills/` 的文件清单不变，
内容哈希由 `adbf57f7…` 变为 `07339ab0…`，即本机装的 Claude 侧 skills 原本落后于
`origin/main`——`769f619`（#243）动过 `skill-for-claude/`。换言之，如果这次重装站在一个
陈旧 checkout 上，被装回去的正是 #243 之前的 `issue-session-flow`。

### 陈旧源被拒（behind 1）

临时 clone `/private/tmp/issue-254-stale-clone`，把 HEAD 停在其 upstream 之前一个 commit：

```text
$ git status -sb | head -1
## change/254-claude-install-source-guard...upstream-main [behind 1]

$ bash skill-for-claude/install.sh
source checkout:   /private/tmp/issue-254-stale-clone
source commit:     4e8a697 (1 commit(s) BEHIND upstream-main)
source skills:     2
source references: 3
ERROR: skill-for-claude/install: source checkout is 1 commit(s) behind upstream-main
  Installing now would install this checkout's older contract and report success:
  the success output does not distinguish it from a correct install (#162).
  Fast-forward first, then re-run:
    git -C /private/tmp/issue-254-stale-clone merge --ff-only upstream-main
  On a change branch, rebase onto the upstream instead:
    git -C /private/tmp/issue-254-stale-clone rebase upstream-main
exit=1
```

真实 managed tree 零变化，观测窗口精确套在这一次尝试上（逐文件 `shasum -a 256`，
5 个文件）：

```text
$ diff <pre-stale per-file hashes> <post-stale per-file hashes>
（无输出）
```

`Pruned` 一行始终没有出现——拒绝发生在 prune 循环与 `install -d` 之前。测试矩阵里
`[[ ! -e "$root" ]]` 断言的是同一件事：behind 路径下连安装根目录都不会被创建。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | 真机两次执行均打印 `source checkout` / `source commit` / `skills` / `references`；测试矩阵 level 与 no-remote 两段的 `assert_provenance` 覆盖 |
| AC-2 | PASS | 陈旧 clone 以 `ERROR: skill-for-claude/install:` 退出 1，给出 `merge --ff-only`；真实 tree 逐文件哈希零变化，无 `Pruned` 输出 |
| AC-3 | PASS | 测试矩阵 no-remote 段：`WARNING: skill-for-claude/install: branch main has no upstream` 后仍产出 installed marker |
| AC-4 | PASS | `grep -c 'rev-list --count'` 为 0；实现只有一条 `source codex/lib/install-source-guard.sh` |
| AC-5 | PASS | `8 installers x 3 source states` |
| AC-6 | PASS | `claude skill install tests passed`（改 fixture 后） |
| AC-7 | PASS | 踩坑 20 含「补齐第八个」与本条可读量；`grep -c '仍未接入'` 与 `grep -c '尚未立 Issue'` 均为 0 |
| AC-8 | PASS | smoke 671 tests OK |
| AC-9 | PASS | 见上两节 |

## 遗留风险与未完成项

- `skill-for-claude/install.sh` 仍不在 smoke 的 shellcheck 清单里（现状只 `bash -n`）。
  本次按 spec 非目标不改那份清单，改为手工执行一次并记录在上表。这是一条可以单独
  处理的小缺口，不影响本 Issue 的任何 AC。
- 陈旧场景用的是临时 clone 加一个本地 `upstream-main` 分支，不是真实 remote：guard
  读的是已在磁盘上的 remote-tracking ref、从不 fetch，所以这与真实 `origin/main`
  落后是同一条代码路径。
- 未执行：任何服务器侧安装或部署——本 Issue 无部署影响。
