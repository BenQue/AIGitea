---
issue: 416
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/416
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/416-round2-partial-closeout
created: 2026-10-22
updated: 2026-10-22
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | D3：清除项改写、ADR 例外表、守卫核对例外表与反向测试、基线收紧 | - | pending |
| T02 | readiness 非 macOS 拒绝与测试，`06`、`issue-session-flow` 收尾节主机口径 | - | pending |
| T03 | smoke 整句钉子改结构检查，下调钉子基线 | - | pending |
| T04 | 路线图更正、审查索引补行、D6/D9 例外与退出条件收口、本批行；发 1.12.0；smoke；verification 与交叉审查 | T01, T02, T03 | pending |

每张 ticket 完成后提交一次本地 commit；T01–T03 各做一轮 Codex 只读交叉审查（`gpt-6-astra`，effort high），T04 后对完整候选再审一轮。

## Expected touch points

- T01：`docs/adr/0001-platform-boundary.md`、`codex/tests/check-project-leak.py`、`codex/config/project-leak-baseline.json`、01/07/12–15 分册、
  `codex/tools/{bootstrap-gitea-service-account.sh,gitea-readonly.sh,gitea-pat-helper/README.md,rotate-gitea-service-account.md}` 与两个对应测试。
- T02：`codex/tools/aisoft-platform-readiness.sh`、`codex/tests/test-platform-readiness.sh`、`06-运维手册与踩坑集.md`、`skills/issue-session-flow/SKILL.md`。
- T03：`codex/tests/smoke.sh`、`codex/tests/smoke-pin-baseline.json`。
- T04：`docs/governance/*`、`usage/bundle.json`、本目录 verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `rg` 读回路线图；审查索引逐行对照来源文档 |
| AC-2 | `python3 -B codex/tests/check-project-leak.py`；夹具根上加一个未登记文件的反向用例 |
| AC-3 | `test-platform-readiness.sh` 用 PATH 里的 `uname` 替身覆盖两种主机；Mac 实跑；`orb -m <machine>` 在 VM 内实跑 |
| AC-4 | smoke 自带的钉子计数；`bash codex/tests/smoke.sh` |
| AC-5 | 读回路线图退出条件节 |
| AC-6 | 新测试先在未改源码上运行记录失败，再在修复后记录通过 |
| AC-7 | `usage-bundle.sh --release` 与 `--verify` |

## 部署与回滚

无部署。合并后负责人两台重装 broker（`bootstrap-gitea-service-account.sh` 随它安装），Mac 重装技能；读回两台 drift 与 Mac readiness。
