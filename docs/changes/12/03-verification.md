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
status: pending
branch: change/12
pr_url:
created: 2026-07-24
updated: 2026-07-24
---

# Verification

## 环境与版本

- Commit SHA: 待实现提交
- Artifact: 不适用；平台 source 仓库不构建应用制品
- Environment: macOS 本地临时 Git 仓库 + mock Gitea API

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `bash codex/tests/test-mark-deployed-issues.sh` | NOT RUN | 待实现后填写 |
| `bash codex/tests/test-sync-gitea-repository-settings.sh` | NOT RUN | 待实现后填写 |
| `bash codex/tests/test-cleanup-merged.sh` | NOT RUN | 待实现后填写 |
| `bash codex/tests/smoke.sh` | NOT RUN | 待实现后填写 |

## Acceptance criteria 结果

实现后逐项映射 AC-1 至 AC-7，不以文档代替真实命令。

## 重复部署

- 第一次：NOT RUN；使用同一 merge message 执行 deployed mock。
- 第二次：NOT RUN；重复相同输入，验证标签结果和请求集合幂等。

## 故意失败与回滚

- 失败场景：NOT RUN；mock Gitea label PUT 返回失败。
- 停止/回滚结果：NOT RUN；预期记录脱敏告警且不把部署判失败。
- 数据恢复验证：不适用；无数据迁移。repository setting 用 `--disable` 读回 false。

## 遗留风险与未完成项

- 各应用仓库的真实 workflow 采用、健康检查后回写和 Gitea 设置读回必须通过各自 Issue/PR 完成；本平台 PR 不越权修改应用。
