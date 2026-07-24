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
status: verified-local
branch: change/12
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Verification

## 环境与版本

- Commit SHA: 本分支最终实现提交（PR 创建前回填）
- Artifact: 不适用；平台 source 仓库不构建应用制品
- Environment: macOS 本地临时 Git 仓库 + mock Gitea API

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/test-mark-deployed-issues.sh` | PASS | 多 `Closes`、去重、fallback、标签保留、重复调用、API failure best-effort 与 token argv/output 扫描通过 |
| `bash codex/tests/test-sync-gitea-repository-settings.sh` | PASS | enable/read-back/disable/read-back 与 token argv 扫描通过 |
| `bash codex/tests/test-cleanup-merged.sh` | PASS | 临时 Git 仓库中 dry-run 保留、空 REMOVE + apply + branches 安全删除 merged local branch |
| `bash -n codex/tools/*.sh codex/tests/test-*.sh` | PASS | 新增脚本与测试均通过语法检查 |
| `shellcheck ...` | PASS | 当前环境已安装 ShellCheck；新增六个 shell 文件无诊断 |
| `bash codex/tests/smoke.sh` | PASS | 98 个 Python runtime 测试与全部 shell/static smoke 通过 |

## Acceptance criteria 结果

- AC-1/AC-2/AC-3：`test-mark-deployed-issues.sh` 通过。
- AC-4：`test-sync-gitea-repository-settings.sh` 通过。
- AC-5：`test-cleanup-merged.sh` 与破坏性命令静态扫描通过。
- AC-6：完整 smoke 通过。
- AC-7：onboarding、02、03、06 已更新；应用真实采用仍须独立 PR。

## 重复部署

- 第一次：PASS；mock 合批 message 生成 #12/#13 两个 label PUT。
- 第二次：PASS；相同输入再次生成相同请求集合，无重复编号或标签漂移。

## 故意失败与回滚

- 失败场景：PASS；mock Gitea label PUT 返回失败。
- 停止/回滚结果：PASS；工具返回 success、输出脱敏告警，不把部署判失败。
- 数据恢复验证：不适用；无数据迁移。repository setting 已用 `--disable` 读回 false。

## 遗留风险与未完成项

- 各应用仓库的真实 workflow 采用、健康检查后回写和 Gitea 设置读回必须通过各自 Issue/PR 完成；本平台 PR 不越权修改应用。
