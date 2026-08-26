---
issue: 208
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/208
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更默认人工确认语义、Controller 状态机、独立合并身份、broker 权限面与 protected-main 合并治理，触发 Agent、权限、安全、共享核心和平台治理强制 complex。
risk_flags:
  - agent-governance
  - security
  - shared-core
  - ci
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-routine-pr-auto-merge-260826.md
  spec: spec-routine-pr-auto-merge-260826.md
  plan: plan-routine-pr-auto-merge-260826.md
  verification: verification-routine-pr-auto-merge-260826.md
confidence: high
override_reason: ''
depends_on:
  - 207
status: approved
branch: change/208-routine-pr-auto-merge
pr_url:
created: 2026-08-26
updated: 2026-08-26
---

## 问题/需求总结

日常 Issue 会话仍把“开最终 PR”“人工合并”“终态标签 apply”“归档”等动作拆成多个确认点，
同时平台没有可用于 routine small PR 的受控合并身份或 broker hard gate。目标是把默认人工确认
收敛为：提交最终 PR，以及完成后归档；两者之间的 CI 修复、routine 合并、终态核对和清理按
已确认合同自动推进。

## 影响范围

- 根 `AGENTS.md`、README、03/04/08/09 与 Codex/Claude 会话及平台 skills。
- `aisoft_loop` 的 PR 提交确认、状态持久化、manual/routine 分流和 merge receipt。
- Gitea governance manifest、独立 per-project routine merger、protected-main allowlist 与 read-back。
- host-access broker 的固定身份绑定和唯一 routine merge typed operation。
- Controller、broker、governance、双工具 drift、安装与 shell smoke 回归。

## 初步方案与建议

先用独立 governance-only 提交改变当前人机合同并停止；fresh run 重读后再实现 runtime。
提交 PR 的确认绑定 exact Issue、readable branch 与 routine policy，并明确“required CI 全绿后允许
受控自动合并”。merge 时 broker 使用独立 per-project merger，在最终 head SHA 上重新读取全部
硬门；任何失败只返回一个稳定升级原因，不 force、不绕过、不自动部署。

## 风险

- 错把 small 标签当充分条件，会让 major、阶段完结或强制风险变更绕过人工合并。
- 复用 admin、manager 或 project agent 会扩大凭据与权限边界。
- 只看 aggregate CI、旧 head 或 Controller 缓存会产生 TOCTOU 合并。
- 把 merge 视为部署许可会跨越独立的 production/deployment gate。
- source 合并不代表 broker/runtime 已安装或 live protection 已应用。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更默认人工确认语义、Controller 状态机、独立合并身份、broker 权限面与 protected-main 合并治理，触发 Agent、权限、安全、共享核心和平台治理强制 complex。
risk_flags:
  - agent-governance
  - security
  - shared-core
  - ci
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 当前 `AGENTS.md`、governance contract 和 broker tests 明确禁止任何非人工 merge。
- 当前 broker identity bindings 只有 manager/project-agent，operation catalog 的 merge surface 为 0。
- 当前 Controller 本地验证后直接创建 PR，无法表达“提交最终 PR”的第一次人工确认。
- 本变更依赖一次性的改动前 live protection/source/installed 对照，必须保留 verification。

### 缺失的 acceptance criteria 或决策

- 无。
