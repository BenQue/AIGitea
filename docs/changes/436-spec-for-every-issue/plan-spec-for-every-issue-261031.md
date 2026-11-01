---
issue: 436
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/436
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - external-contract
depends_on: []
branch: change/436-spec-for-every-issue
created: 2026-10-31
updated: 2026-10-31
---

# 实施计划

## 全局约束与接口

- 推送守卫 `scope()`、`_pull_body`、`open-pr` 守卫逻辑不改；只补测试。
- 文档义务的唯一来源是 route-policy「文档义务」节；其余文档引用它，不复述整表。
- 治理文件（`AGENTS.md`、技能、路由表）在 T01 单独 commit 后 STOP，fresh run 重读合同再做 T02 起的 runtime。
- 停止条件：需要改 `scope()` 语义、扩大 `git_scope`、或 D2 结论与实现冲突时停下升级。

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 治理与合同文本：route-policy「文档义务」节、`AGENTS.md`、`03`/`04`/`08`/GLOSSARY/README、技能、`usage/CONTRACT.md`、`templates/project/AGENTS.md` | - | pending |
| T02 | 模板：简版/完整版 spec、短索引 summary、analyzer 输出节；刷新模板 digest | T01 | pending |
| T03 | runtime：`classification.route()` 最低文档、`contract` spec 分级、`route_policy` 文档义务与预检、`ticket_execution` 合成 T01 取 spec、`aisoft classify` 打印预检 | T02 | pending |
| T04 | 测试：正向/负向/预检/production 不回退，fixture 改为简版 spec 形状；全量 smoke | T03 | pending |
| T05 | 发布包新版本与迁移说明；review-evidence 行；Codex 交叉审查 | T04 | pending |

## T01: 治理与合同文本

- **blocked_by**: none
- **scope**: spec `git_scope` 中的 `*.md` 治理/技能/合同文件
- **AC**: AC-1
- **validation**: `rg` 旧说法清零（来历表、change 目录除外）；`bash codex/tests/smoke.sh` 的文档钉子段
- **Expected**: 所有入口指向同一张文档义务表
- **constraints**: commit 后 STOP，fresh run 再继续

## T02: 模板

- **blocked_by**: T01
- **scope**: `templates/docs/changes/_template/{spec,summary}.md`、`skills/gitea-analyze-change/SKILL.md`、`codex/config/change-template-sync.json`、smoke 钉子
- **AC**: AC-1、AC-5（digest）
- **validation**: `bash codex/tools/change-template-sync.sh --verify-digest`；`test_vendored_change_templates`
- **Expected**: 新模板产出的简版 spec 能被 `scope()` 与合同校验接受
- **constraints**: 不改 plan/verification 模板

## T03: runtime

- **blocked_by**: T02
- **scope**: `classification.py`、`contract.py`、`route_policy.py`、`ticket_execution.py`、`codex/tools/aisoft`
- **AC**: AC-2、AC-3、AC-6
- **validation**: 相关单测；`aisoft classify 436` 在本 worktree 打印预检 OK
- **Expected**: 预检与合同按 D1/D2 判定；`scope()` 未改
- **constraints**: fail closed；存量 change 文档检查不追溯

## T04: 测试

- **blocked_by**: T03
- **scope**: spec 中列出的测试文件与 fixture
- **AC**: AC-2、AC-3、AC-4、AC-6
- **validation**: `python3 -m unittest discover -s codex/runtime/tests`；`bash codex/tests/smoke.sh`
- **Expected**: 全绿；新增用例在去掉实现后变红（反向证明）
- **constraints**: 未运行的不写通过

## T05: 发布与审查

- **blocked_by**: T04
- **scope**: `usage/bundle.json`、`usage/USER-GUIDE.md`、`docs/governance/review-evidence-index.md`、verification
- **AC**: AC-5
- **validation**: `bash codex/tools/usage-bundle.sh --release …` 后 smoke 绿；Codex 只读审查 PASS
- **Expected**: 下一可用版本发布，notes 写迁移
- **constraints**: 不推 GitHub 镜像

## AC 映射

| AC | Ticket | 验证 |
|---|---|---|
| AC-1 | T01、T02 | `rg` 清零 + 审查 |
| AC-2 | T03、T04 | 单测 + e2e fixture |
| AC-3 | T04 | 负向单测 |
| AC-4 | T04 | 全量单测 + smoke |
| AC-5 | T02、T05 | digest 校验 + 发布包 + notes |
| AC-6 | T03、T04 | 预检单测 |
