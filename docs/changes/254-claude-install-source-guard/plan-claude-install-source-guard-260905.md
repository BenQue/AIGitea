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
status: approved
branch: change/254-claude-install-source-guard
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan: skill-for-claude/install.sh 接入共用 source guard

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | installer 接入 guard，测试矩阵与连带测试同批绿 | - | pending |
| T02 | 06 踩坑 20 清单更新与真机验证记录 | T01 | pending |

单一垂直切片加一个文档/证据切片。T01 自身端到端可验证：改完直接跑
`test-installer-source-guard.sh` 与 `test-install-claude-skills.sh`。

## Expected touch points

- T01
  - `skill-for-claude/install.sh`：在 `[[ -d "$refs_source" ]]` 检查之后、manifest
    解析之前 source 共用库并调用一次 guard，`repo_root` 用第 11 行已算好的 `$root`，
    installer 名字用 `skill-for-claude/install`。
  - `codex/tests/test-installer-source-guard.sh`：`INSTALLERS` 加
    `skill-for-claude/install`；新增 `expected_claude_skills` 与
    `expected_claude_references`（用 `find` 重算，不复用 installer 的 glob）；
    `make_source_tree` 的目录清单加 `skill-for-claude`；`run_installer`、
    `installed_marker`、`assert_provenance` 各加一个 case。
  - `codex/tests/test-install-claude-skills.sh`：`undeclared_root` 追加复制
    `codex/lib`，使接入后的 source 调用在该临时树里可解析。
- T02
  - `06-运维手册与踩坑集.md` 踩坑 20：症状栏补本 installer 的显形方式；处置栏把
    「补齐第七个」延伸为第八个，删除「仍未接入的只剩 skill-for-claude/install.sh…
    尚未立 Issue」整段，并在逐 installer 可读量清单末尾加本条。
  - `docs/changes/254-claude-install-source-guard/verification-…md`：真机证据。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-installer-source-guard.sh`（level 与 no-remote 两段的 `assert_provenance`） |
| AC-2 | 同上 behind 段：`ERROR: skill-for-claude/install: source checkout is 1 commit(s) behind origin/main`、`merge --ff-only origin/main`、`[[ ! -e "$root" ]]` |
| AC-3 | 同上 no-remote 段：`WARNING: skill-for-claude/install: branch main has no upstream` 后仍产出 installed marker |
| AC-4 | diff review 加 `grep -c 'rev-list --count' skill-for-claude/install.sh` 为 0 |
| AC-5 | `test-installer-source-guard.sh` 末行输出 `8 installers x 3 source states` |
| AC-6 | `bash codex/tests/test-install-claude-skills.sh` |
| AC-7 | diff review 加 `grep` 反证：踩坑 20 内不再出现「仍未接入」 |
| AC-8 | `bash codex/tests/smoke.sh` |
| AC-9 | 真机 `bash skill-for-claude/install.sh`；落后 clone 复跑；前后对 `~/.claude/skills` 取文件清单与 `shasum` 比对 |

`shellcheck skill-for-claude/install.sh` 在 T01 后手工执行一次并记入 verification
（smoke 现状只对该文件跑 `bash -n`，本次不改这份清单，见 spec 非目标）。

## 部署与回滚

无部署。回滚方式为 revert 单一 PR；guard 是纯新增调用，无状态、无迁移、无持久化配置。

AC-9 的真机安装写的是本机 `~/.claude/skills/`，不是任何服务器环境，也不构成部署；
落后 clone 那一次的预期结果是「什么都没写」，正是要观测的东西。
