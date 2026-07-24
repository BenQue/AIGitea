---
issue: 12
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/12
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-deployment
  - repository-settings
  - destructive-operations
depends_on: []
status: contract-ready
branch: change/12
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Implementation plan

## 任务分解

1. 先用 shell mock 写 deployed 多 Issue、标签保留、fallback、失败不泄密的回归，再实现 `mark-deployed-issues.sh`。
2. 写显式目标和 enable/disable/read-back 回归，再实现 `sync-gitea-repository-settings.sh`。
3. 把现有 cleanup 脚本收编到 `codex/tools/`，写临时 Git 仓库 regression 复现空数组路径并加入最小 guard。
4. 把三个脚本纳入 `bash -n`、ShellCheck（若可用）和 `codex/tests/smoke.sh`。
5. 更新 02/03/06 分册和 onboarding runbook，记录采用、回滚和各应用独立 PR 边界。
6. 在 `03-verification.md` 记录两次相同 mock 调用、一次故意 API 失败及 cleanup 破坏性负向检查。

## 涉及文件

- `codex/tools/mark-deployed-issues.sh`
- `codex/tools/sync-gitea-repository-settings.sh`
- `codex/tools/aigitea-cleanup-merged.sh`
- `codex/tests/test-mark-deployed-issues.sh`
- `codex/tests/test-sync-gitea-repository-settings.sh`
- `codex/tests/test-cleanup-merged.sh`
- `codex/tests/smoke.sh`
- `skill-for-codex/references/onboarding-runbook.md`
- `02-CI与自动部署流水线.md`
- `03-Issue-Spec-Plan与单闸门开发流程.md`
- `06-运维手册与踩坑集.md`
- `docs/changes/12/`

## 数据库迁移

无。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1 | `bash codex/tests/test-mark-deployed-issues.sh` 验证 3 个 Closes、去重和 fallback |
| AC-2 | 同一 mock 断言 PUT label IDs 保留 type/complexity/非生命周期并替换 lifecycle |
| AC-3 | mock 失败与 sentinel token 检查 argv/stdout/stderr，脚本返回 best-effort success |
| AC-4 | `bash codex/tests/test-sync-gitea-repository-settings.sh` 验证 enable、read-back、disable |
| AC-5 | `bash codex/tests/test-cleanup-merged.sh` 在临时仓库运行 dry-run 和 apply+branches |
| AC-6 | `bash codex/tests/smoke.sh` |
| AC-7 | 人工复核 onboarding、02、03、06 的采用与回滚说明 |

## 部署与回滚

本 PR 不部署应用。`03-verification.md` 对部署后记账工具执行两次相同输入并故意制造一次 API 失败；应用采用后还需在目标仓库自己的 PR/verification 中验证真实健康检查后调用。仓库设置用 `--disable` 回滚，cleanup 工具通过 revert 恢复。
