---
issue: 406
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/406
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on:
  - 397
status: approved
branch: change/406-drift-source-ancestor
created: 2026-10-21
updated: 2026-10-21
---

# 实施计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 夹具先红：只改文档的提交、改轮换文件的提交、非祖先 source_sha、helper 凭证三态；检查器改为祖先判定后转绿 | - | done |
| T02 | 反向证明、全量 smoke、Codex 交叉审查、verification | T01 | done |

## Expected touch points

- T01：`codex/tools/check-installed-drift.py`、`codex/tests/fixtures/installed-drift/test-installed-drift.py`
- T02：本目录 verification 与 summary

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1–AC-4 | `python3 codex/tests/fixtures/installed-drift/test-installed-drift.py` 新用例 |
| AC-5 | 临时还原判定后重跑新用例，记录红 |
| AC-6 | `bash codex/tests/smoke.sh`；`codex exec -s read-only` 审查 |
| AC-7 | 合并后两台重装 + `check-installed-drift` 读回 |

## 部署与回滚

无应用部署。合并后由用户两台重装 broker；回滚为 revert 后重装。
