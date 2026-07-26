---
issue: 19
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/19
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
depends_on: []
status: implemented
branch: change/19
pr_url:
created: 2026-07-26
updated: 2026-07-26
---

# Implementation plan

## 任务分解

1. 先扩展 manifest 和 mock sync 断言，锁定 17 个规范标签与幂等 provision。
2. 更新 runtime lifecycle 集合、dependency readiness 与 Gitea adapter 回归，覆盖
   `completed`/`deployed` 互斥及 open/closed 边界。
3. 把 `completed` 加入 deployed 回写的 lifecycle 替换集合，并补回归证明升级为
   `deployed` 后不残留 `completed`。
4. 更新当前权威文档、global AGENTS 和 onboarding skill；为历史 16-label 计划增加
   后续扩展说明，不重写其当时证据。
5. 运行 shell、Python、manifest 和全量 smoke 验证，填写 `03-verification.md`。
6. 提交并推送 `change/19`，创建带 `Closes #19` 的最终 PR，停止在人工合并闸门。
7. PR 合并后保存当前 10 个 Issue 的原标签快照，运行 label sync，再逐项替换为
   `type/platform`、`complexity/complex`、`completed` 并读回；失败则按快照恢复。

## 涉及文件

- `docs/changes/19/{00-summary,01-spec,02-plan,03-verification}.md`
- `codex/config/gitea-labels.json`
- `codex/runtime/aisoft_loop/{contract,controller}.py`
- `codex/runtime/tests/{test_controller,test_gitea}.py`
- `codex/tools/mark-deployed-issues.sh`
- `codex/tests/{smoke,test-sync-gitea-labels,test-mark-deployed-issues}.sh`
- `README.md`、`01-基础设施-VM-Gitea-Runner.md`
- `03-Issue-Spec-Plan与单闸门开发流程.md`
- `04-Agent编排与定时任务.md`
- `09-v3平台简化与Loop-Engineering文档改造规划.md`
- `10-AI-Issue判级与标签实施计划.md`
- `codex/global-AGENTS.md`
- `skill-for-codex/SKILL.md`
- `skill-for-codex/references/onboarding-runbook.md`

## 数据库迁移

无数据库迁移。Gitea label catalog 和 10 个 Issue 的标签集合属于外部 metadata 迁移，
只在 PR 合并后执行，并按迁移前快照提供逐 Issue 回滚。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `jq` manifest smoke 锁定 17 个唯一名称、颜色和描述 |
| AC-2 | `python3 -m unittest codex.runtime.tests.test_contract codex.runtime.tests.test_gitea -v` |
| AC-3 | `python3 -m unittest codex.runtime.tests.test_controller -v` |
| AC-4 | `bash codex/tests/test-mark-deployed-issues.sh` |
| AC-5 | `rg` 审查当前文档的 seven/16/closed+deployed 旧表述，并人工核对历史说明 |
| AC-6 | `bash -n ...`、`shellcheck ...`、`bash codex/tests/smoke.sh` |
| AC-7 | PR 合并后运行 `sync-gitea-labels.sh`，GET label catalog 与 10 个 Issue |
| AC-8 | live migration 前后快照 diff；故意对无效 Issue number dry-run，确认 fail closed |

## 部署与回滚

无应用部署。PR 合并前只运行本地/mock 验证，不修改真实标签目录或历史 Issue。合并后
metadata 迁移执行两次 label sync 验证幂等，并对全部目标 Issue GET 读回。回滚按
迁移前快照恢复标签；不得删除 Issue、修改 state、合并 PR 或写入 `main`。
