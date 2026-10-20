---
issue: 392
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/392
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on:
  - 389
status: approved
branch: change/392-superpowers-vendor-pin
created: 2026-10-20
updated: 2026-10-20
---

# #392 plan

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理文件：`08` §5、`aisoft-platform` 技能、`README.md` 改为平台 pin 作基准三端核对（单独 commit 后停止重读） | - | pending |
| T02 | superpowers 7.0.0 vendor 快照与带技能包参数的快照校验 | T01 | pending |
| T03 | 发布包 `vendor` 成员、`--build` 两包落点、发 1.3.0 | T02 | pending |
| T04 | `check-external-skill-versions` 三端 PIN 状态与 `--repo` | T02, T03 | pending |
| T05 | 三端适配实测与 verification（Claude/Codex 读回、Cursor fresh 会话） | T04 | pending |

## Expected touch points

- T01：`08-双工具共存与实施.md`、`skills/aisoft-platform/SKILL.md`、`README.md`
- T02：`codex/vendor/superpowers/v7.0.0/**`、`codex/runtime/aisoft_loop/matt_snapshot.py`、`codex/runtime/tests/test_matt_snapshot.py`、`codex/tools/check-installed-drift.py`（仅当它钉的 `matt_snapshot.py` 哈希需要同步）
- T03：`codex/tools/usage-bundle.py`、`usage/bundle.json`、`codex/tests/test-usage-bundle.sh`
- T04：`codex/tools/check-external-skill-versions.py`、`codex/tools/check-external-skill-versions.sh`、`codex/config/external-skill-adaptation.json`、`codex/tests/test-external-skill-versions.sh`
- T05：本目录 `verification-*`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `PYTHONPATH=codex/runtime python3 -m aisoft_loop.matt_snapshot verify --pack superpowers codex/vendor/superpowers/v7.0.0 codex/vendor/superpowers/v7.0.0/manifest.json`；`diff -r` 对插件缓存 `skills/`；`test_matt_snapshot.py`、`test_matt_install.py` 不变仍过 |
| AC-2 | `bash codex/tools/usage-bundle.sh --verify --baseline-ref origin/main`；`--build <tmp>` 后 `find`；`test-usage-bundle.sh` |
| AC-3 | `test-external-skill-versions.sh` 夹具 |
| AC-4 | `check-external-skill-versions.sh --repo <落地检出>` |
| AC-5 | `cursor-agent` 与 `codex exec -s read-only` 在落地检出 fresh 运行；记录 exact 输出 |
| AC-6 | `bash codex/tests/smoke.sh`；`codex exec -s read-only -C <worktree>` 审查 |

## 部署与回滚

无应用部署，无 installed 层改动（`aisoft-platform` 技能文本变了，合并后照常重装两侧技能并读回漂移）。回滚为 revert。
