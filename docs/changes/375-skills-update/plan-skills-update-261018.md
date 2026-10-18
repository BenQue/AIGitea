---
issue: 375
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/375
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: contract-drafting
branch: change/375-skills-update
created: 2026-10-18
updated: 2026-10-18
---

# #375 计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 四份映射文档，本地 commit 后等确认点 1 | - | in-progress |
| T02 | 适配结论落地：`08` §5 示例与映射行、两侧平台技能规则、smoke 锚点 | T01 | pending |
| T03 | 版本核对脚本、适配记录、回归测试与 smoke 五处登记；`08` §5 用途说明 | T01 | pending |
| T04 | 路线文档、泄漏检查、全量 smoke、本机矩阵与 verification；Codex 独立审查 | T02, T03 | pending |
| T05 | 判级投影与 PR 候选，等确认点 2 | T04 | pending |

## Expected touch points

见 spec 的 `git_scope`。

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC1 | smoke 的适配清单锚点与两侧成对短语 |
| AC2 | verification 记录的本机命令输出 |
| AC3 | `bash codex/tests/test-external-skill-versions.sh`；本机 `bash codex/tools/check-external-skill-versions.sh` 实跑输出 |
| AC4 | 合并后负责人重装，`bash codex/tools/check-installed-drift.sh` 读回 |
| AC5 | 全量 smoke 输出与 verification 的分层记录 |
| AC6 | diff review |
| AC7 | `bash codex/tests/smoke.sh`；`python3 -B codex/tests/check-project-leak.py` |

## 部署与回滚

无应用部署。合并后负责人重装两侧平台技能（不需要 sudo）。回滚：revert 本 PR 后重装。
