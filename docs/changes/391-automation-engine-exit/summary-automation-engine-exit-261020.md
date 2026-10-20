---
issue: 391
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/391
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 按 ADR 0002 删除 VM Development Loop、routine 合并与 VM profile 的代码、broker 操作、安装面与 manifest schema，并改治理文件与使用层发布包，属于共享核心、schema、跨模块、Agent 与平台治理变更
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
  summary: summary-automation-engine-exit-261020.md
  spec: spec-automation-engine-exit-261020.md
  plan: plan-automation-engine-exit-261020.md
  verification: verification-automation-engine-exit-261020.md
confidence: high
override_reason: ''
depends_on:
  - 389
status: approved
branch: change/391-automation-engine-exit
pr_url:
created: 2026-10-20
updated: 2026-10-20
---

## 问题/需求总结

整改路线 R10a：ADR 0002 D2 裁定 VM 执行引擎退出平台 `main`。本批删除 Development Loop、routine 自动合并与 VM profile 的代码、broker 操作（39 → 34）与 `install-vm` 安装面（7 → 6），收窄 manifest，改写治理文件与相关文档，并给出 VM 旧单元与 LocalWMS routine merger 的清理命令。合同与验收见 spec。

## 影响范围

`codex/runtime/aisoft_loop/` 的 Loop 模块与 CLI、`codex/agent/` 的 Loop 脚本、`codex/systemd/`、`codex/install-vm.sh`、`templates/agent/`；`aisoft_host_access` 与 `aisoft_gitea_governance` 的 routine 与 profile 部分；两份真实 manifest 与两份夹具；smoke、漂移检查、source guard 与相关测试；`AGENTS.md`、`codex/global-AGENTS.md`、README、`03`、`04`、`06`、`08`、`GLOSSARY.md`、技能、模板与使用层发布包。

## 初步方案与建议

按 R8 的迁出做法一次删完，`archive/` 只留迁出说明。routine 两个字段保留并冻结为 `false`/`null`，避免碰 K1 凭据工具；`vm_profile_policy` 收窄为 `vm_runtime.runtime_user` 供 `orbstack.vm.units.read` 使用。治理文件单独 commit 后停下重读。

## 风险

删错会话工具依赖、两侧 manifest 不一致、文档钉子测试跟着变红。缓解见 spec。VM 单元与 merger 账号删除不可由 revert 恢复，排在合并、重装与读回之后。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 按 ADR 0002 删除 VM Development Loop、routine 合并与 VM profile 的代码、broker 操作、安装面与 manifest schema，并改治理文件与使用层发布包，属于共享核心、schema、跨模块、Agent 与平台治理变更
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

- 删除 broker 操作与 runtime 模块、改 manifest schema、installer 与漂移检查，属强制 complex 的共享核心、schema、跨模块与回滚类别。
- 改 `AGENTS.md`、`codex/global-AGENTS.md`、技能与使用层发布包成员，属 Agent 与平台治理，需受控步骤与发布包升版。
- 验收含合并后两台重装、VM 单元清理、账号删除与 audit 读回，不能只靠 diff review 与 CI 重放，故声明 verification。

### 缺失的 acceptance criteria 或决策

- 无。任务书的 6 条验收已展开为 spec AC1–AC10；spec「决定」一节列出确认点 1 的默认值。
