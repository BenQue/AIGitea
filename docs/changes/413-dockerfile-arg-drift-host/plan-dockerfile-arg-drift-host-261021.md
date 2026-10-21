---
issue: 413
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/413
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - artifact
  - platform-governance
depends_on: []
branch: change/413-dockerfile-arg-drift-host
created: 2026-10-21
updated: 2026-10-21
---

# Implementation plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | Dockerfile 全局 ARG 默认值展开加 stage 守卫，测试与 README 合同段 | - | pending |
| T02 | 漂移检查在 macOS 真实根拒绝 `--host vm`，测试与 06 一句话 | - | pending |
| T03 | 使用发布包发版、smoke、verification 与交叉审查 | T01, T02 | pending |

## Expected touch points

- T01：`codex/runtime/aisoft_architecture/dockerfile.py`、`codex/runtime/tests/test_architecture_dockerfile.py`、`architecture/README.md`。
- T02：`codex/tools/check-installed-drift.py`、`codex/tests/fixtures/installed-drift/test-installed-drift.py`、`06-运维手册与踩坑集.md`。
- T03：`usage/bundle.json`、本目录 verification。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1、AC-2、AC-3 | `python3 -m unittest` 跑 `test_architecture_dockerfile`（新增守卫通过与拒绝子用例） |
| AC-4、AC-5 | `test-installed-drift.py` 新增用例：patch `sys.platform` 为 darwin 的真实根拒绝、合成根照旧 |
| AC-6 | 新测试先在未改源码上运行并记录失败，再在修复后运行记录通过 |
| AC-7 | `usage-bundle.sh --release` 读回；`bash codex/tests/smoke.sh` |

## 部署与回滚

无部署。合并后负责人按常规两台重装并读回漂移（`--host vm` 在 VM 里跑）。
