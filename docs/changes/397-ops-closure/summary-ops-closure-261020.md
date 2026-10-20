---
issue: 397
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/397
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 漂移检查适用面与棘轮、告警投影闸门、清扫与 PAT 周期、部署通知模板、平台仓 CI 触发与 routine manifest 字段删除，属于 schema、共享核心、跨模块、CI 与平台治理变更
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-ops-closure-261020.md
  spec: spec-ops-closure-261020.md
  plan: plan-ops-closure-261020.md
  verification: verification-ops-closure-261020.md
confidence: high
override_reason: ''
depends_on:
  - 391
status: approved
branch: change/397-ops-closure
pr_url:
created: 2026-10-20
updated: 2026-10-20
---

## 问题/需求总结

整改路线 R16：给平台自己的安装面、凭据与仓库卫生补上节奏、闸门与通知，并收掉 R10a 留下的 routine manifest 字段与 `aisoft-loop` 死路径。合同与验收见 spec。

## 影响范围

`codex/tools/check-installed-drift.py` 与新基线 JSON、`aisoft-alert-poll.sh`、`aigitea-cleanup-merged.sh`、`aisoft-platform-readiness.sh`、`templates/project/ci/` 新模板、`.gitea/workflows/ci.yml`、`skills/issue-session-flow`、两份真实与夹具 manifest、`aisoft_host_access` 与 `aisoft_gitea_governance` 的合同与 routine 读者、轮换与 bootstrap 工具、`aisoft_main_integration.py`、相关测试、`05`、`06`、README、路线图与使用层发布包。

## 初步方案与建议

不新增 broker 操作；适用面写在检查器里、由基线 JSON 再钉一次；routine 字段删除排在最后，等 R13 合并后开工；治理文件单独 commit 后停下重读。

## 风险

SKIP 掩盖真缺失、与 R13/R10b 撞文件、本机清理不可 revert；缓解见 spec。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 漂移检查适用面与棘轮、告警投影闸门、清扫与 PAT 周期、部署通知模板、平台仓 CI 触发与 routine manifest 字段删除，属于 schema、共享核心、跨模块、CI 与平台治理变更
risk_flags:
  - shared-core
  - schema-change
  - cross-module
  - rollback
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- manifest schema 收窄（删 routine 字段）、CI workflow 触发变更、技能收尾流程变更，按 `AGENTS.md` 判级规则一律 complex。
- 合并后需两台重装与读回，验收证据不能由 diff review 与 CI 复现，声明 `verification`。

### 缺失的 acceptance criteria 或决策

- 无；默认值见 spec「决定」。
