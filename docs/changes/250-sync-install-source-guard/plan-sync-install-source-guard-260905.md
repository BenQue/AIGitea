---
issue: 250
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/250
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - deployment
depends_on: []
status: approved
branch: change/250-sync-install-source-guard
created: 2026-09-05
updated: 2026-09-05
---

# Implementation plan: sync/install.sh 接入共用 source guard

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | `sync/install.sh` 接入 guard，测试数组加入 `sync/install`，三态全绿 | - | done |
| T02 | 踩坑 20 逐 installer 清单补 `sync/install` 并更新覆盖范围表述 | T01 | done |

T01 是完整的垂直切片：脚本改动与覆盖它的测试同批交付，任一单独提交都不可验证。
T02 只改文档，依赖 T01 定下的实际标签名。

## Expected touch points

- T01：`sync/install.sh`、`codex/tests/test-installer-source-guard.sh`
- T02：`06-运维手册与踩坑集.md`

这是范围提示，不授权扩大 spec。`codex/lib/install-source-guard.sh` 不在触点内。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-installer-source-guard.sh` 的 level 分支，`assert_provenance` 断言 checkout、commit 与两个可读量 |
| AC-2 | 同上 behind 分支，断言非零退出、带 installer 名的 ERROR 行与 `[[ ! -e "$root" ]]` |
| AC-3 | 同上 no-remote 分支，断言 `WARNING: sync/install: branch main has no upstream` 后仍安装 |
| AC-4 | diff review：`sync/install.sh` 只 source 共用库，`grep -rn aisoft_install_source_guard sync/` 只有一处调用 |
| AC-5 | 上述测试末行输出 `7 installers x 3 source states` |
| AC-6 | diff review 踩坑 20 那一行 |
| AC-7 | `bash codex/tests/smoke.sh`、`bash -n sync/install.sh`、`shellcheck sync/install.sh` |

测试文件需要同步改动的位置：`INSTALLERS`、`make_source_tree` 的目录列表要加 `sync`
（否则临时 checkout 里没有 sync/ 源）、`run_installer` 的 case、`installed_marker`、
`expected_*` 计数与 `assert_provenance` 的 case。

## 部署与回滚

无部署影响。本次不在任何主机上执行 `sync/install.sh`，不改变已安装产物。

回滚为单次 revert，见 spec 的回滚约束。
