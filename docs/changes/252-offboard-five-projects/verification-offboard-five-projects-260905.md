---
issue: 252
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/252
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
depends_on: []
status: pending
branch: change/252-offboard-five-projects
created: 2026-09-05
updated: 2026-09-05
---

# Verification 统一退出五个项目

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = 071b6b0
- 环境：Mac 本地 checkout，broker 已安装为 2026-09-05 前的十项目版本
- 本记录负责证明的 acceptance criteria: AC-1 到 AC-13

## 改动前基线证据

改动合并后无法重放，先记录。

| 观测 | 取值 | 命令 |
|---|---|---|
| 治理项目数 | 待填写 | `validate` |
| non-target 摘要原值 | 待填写 | manifest 读取 |
| 已退出项目当前可寻址 | 待填写 | `--project sfm-digital-board --operation gitea.repo.read` |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 待执行 | NOT RUN | 待填写 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | 待填写 |

## 人工交接项

以下动作平台没有 typed 操作，或需要 sudo，必须由人执行。未执行一律 NOT RUN。

| 编号 | 动作 | 状态 |
|---|---|---|
| H-1 | 停用并禁用 `aisoft-agent@sfm.timer` | NOT RUN |
| H-2 | 清理三份 VM profile env 与 project-agent token | NOT RUN |
| H-3 | 两台重装 broker 与 host-role | NOT RUN |
| H-4 | 撤销八个 Gitea 身份的 token | NOT RUN |
| H-5 | 从五个仓库移除 collaborator | NOT RUN |
| H-6 | 停用八个 Gitea 账号（不删除） | NOT RUN |
| H-7 | 关闭 rsdesign-new #19、HSDB #18、SFMDigitalBoard #112 | NOT RUN |

## 遗留风险与未完成项

待填写。
