---
issue: 70
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/70
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 完成 purpose-built host broker 的治理写入与独立 worktree 闭环，使日常 Codex 会话只需固定 broker 授权并保留人工 merge
risk_flags:
  - authentication
  - authorization
  - security
  - external-contract
  - shared-core
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-governed-host-writes-260809.md
  spec: spec-governed-host-writes-260809.md
  plan: plan-governed-host-writes-260809.md
  verification: verification-governed-host-writes-260809.md
confidence: high
override_reason: ''
depends_on:
  - 35
  - 61
  - 67
status: approved
branch: change/70
pr_url: null
created: 2026-08-09
updated: 2026-08-09
---

## 问题/需求总结

Issue #61 建立了 fixed `host-access-broker/v1`、project-agent Keychain binding 和人工 merge 边界；
Issue #67 只修复 Git credential protocol 的合法 multi-valued attributes。当前 installed broker 与
protected-main source 字节一致，但 operation catalog 只覆盖 Gitea read、固定 canonical checkout 的 Git
fetch/change push、Mac binding 与 OrbStack/profile operations。

因此日常交互式 Codex 仍需退回 direct Git/Gitea/Keychain host path：Issue/PR mutation 没有 typed
operation，独立 worktree 不能通过 broker push，且一次治理流程会拆成多条 host execution approval。
三个 live candidate 进一步证明 Keychain item ACL metadata 与 Codex host approval 任一层单独通过都不能
宣告端到端零提示。用户因此明确批准 #70 用 repo-external project-scoped protected files 取代 Mac runtime
Keychain；这只 supersede #61 的 Mac credential-store 选择，不改变其 identity/target/merge 边界。

## 影响范围

- strict host-access manifest、broker runtime/CLI 与 fixed installed wrapper。
- project-agent scoped Issue create/read/update/comment、PR create/read/update 与聚合 access audit。
- 独立 worktree exact `change/N` Git fetch/push 和 controller/runner broker adapter。
- protected-file metadata、token identity/scope、repository permission 的脱敏 fail-closed 验证。
- installer、security negatives、fresh-session integration、full platform smoke 与 live canary runbook。

## 初步方案与建议

保留一个深、窄的 broker interface：调用方只能提供 manifest `project`、allowlisted `operation` 与该
operation 的 typed fields；method、Gitea path、owner/repository、Git refspec、credential service/account、
checkout discovery与 merge 禁止面全部由 broker 内部决定。文本字段是有长度/字符/语义约束的 schema
字段，不接受 raw URL、raw HTTP body、任意 JSON、shell、command、credential path 或 refspec。

独立 worktree 不由调用方任意传路径。broker 从当前进程 working directory 解析 Git common-dir，要求其
与 manifest canonical checkout 属于同一 repository，当前 branch 精确等于请求的 `change/N`，且 Issue
number 与 branch number 相等。push 固定构造同名 source/destination ref，并显式拒绝 detached/main/
other ref/force/delete/cross-project。

## 风险

- typed operation 若放宽为 raw URL/body/refspec 会成为通用高权限转发器；contract/schema 和负向测试必须
  在 credential resolution 与 transport 前拒绝。
- worktree identity 若只比较 remote string，可能把另一 checkout 或 project 误认为合法；必须同时验证
  common-dir、remote、branch、head ancestry 和 dirty/commit边界。
- mode/owner/type/link metadata 只能证明 credential-file 层；Codex exact-prefix approval 必须用 fresh task
  的 repeated broker calls 单独验收。
- 任何 token、credential path、Authorization header 或 credential protocol values 均不得进入
  argv、stdout/stderr、日志、repository、Issue/PR 或 fixture。

## AI 判级

```yaml
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 完成 purpose-built host broker 的治理写入与独立 worktree 闭环，使日常 Codex 会话只需固定 broker 授权并保留人工 merge
risk_flags:
  - authentication
  - authorization
  - security
  - external-contract
  - shared-core
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

- 新增 authentication/authorization/security external contract 与 shared controller/runner behavior。
- 修改 Gitea mutation、Git push、credential-store 和 host approval interface，命中强制 complex 规则。
- Issue #70 已实时读回 `approved` + `complexity/complex` + `type/platform`，验收与禁止项完整。

### 缺失的 acceptance criteria 或决策

无。用户已明确唯一持久授权入口、credential/ACL 下限、fresh-task canary、人工 merge 与禁止范围。
