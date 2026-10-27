---
issue: 434
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/434
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把通用流程采用与中央项目登记解耦，登记降为可选的 broker 加固访问，涉及访问控制规则与 Agent 治理入口
risk_flags:
  - authorization
  - agent-governance
  - platform-governance
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-decouple-adoption-from-registry-261027.md
  spec: spec-decouple-adoption-from-registry-261027.md
  plan: plan-decouple-adoption-from-registry-261027.md
  verification: verification-decouple-adoption-from-registry-261027.md
route_provider: claude
route:
  process: complex-production
  tier: frontier
  effort: max
  skills: to-spec, to-tickets, executing-plans, verification-before-completion
  method: spec-plan
  verify: full+reverse-proof
  review: cross-provider+security
  confirm: 2
confidence: high
override_reason: ''
depends_on: []
status: analyzed
branch: change/434-decouple-adoption-from-registry
pr_url:
created: 2026-10-27
updated: 2026-10-27
---

# Summary：通用流程采用与中央项目登记解耦

## 问题/需求总结

Issue #434 要求平台只提供方法、流程、模板与通用工具，项目自主导入，采用通用流程不需要向平台仓新增具体项目记录。

现状相反：

- 会话工具 `aisoft open-pr`、`aisoft classify`（`apply-classification-labels.sh`）与 `aisoft complete`
  （`mark-completed-issues.sh`）的远端步骤只有 broker 一条路径。
- broker 只服务登记在平台两份 manifest 里的项目，项目解析脚本 `codex/agent/aisoft-project-target.sh` 也只从 manifest 解析。
- 技能 `aisoft-platform`、上手指南第 3 步与 onboarding runbook §1.1 都把「先在平台仓走 Issue/PR 登记」写成采用前置。

一次真实的既有项目接入因此出现三类问题：

- 项目内容被立成平台仓 Issue。
- 登记前没有 broker 路由，约 16 次 admin 例外审批。
- 私有仓迁移、历史导入、首个 CI、runner 依赖都是临场处理。

负责人在设计讨论中依次裁决：

- 注册表留在平台仓，不搬到站点本地，也不让项目自注册（方案 A）。
- 登记从「采用前置」降为「可选的 broker 加固访问」，项目可用自己的 Git 凭据跑完整流程（A+ 解耦，2026-10-27）。

## 影响范围

- 会话工具：`codex/tools/aisoft` 及其包装的 `apply-classification-labels.sh`、`mark-completed-issues.sh`、`codex/agent/aisoft-project-target.sh`。
- 新增一条 direct 传输：复用项目检出的 Git remote 与本机 Git 凭据助手，不经平台 manifest。
- 使用发布包：增加项目侧访问声明模板与标签集合，按发布规则升版本。
- 合同文档：
  - 新增 ADR 0003。
  - `aisoft-platform` 技能及其 getting-started、onboarding-runbook、project-align 参考。
  - `issue-session-flow` 技能。
  - `templates/project/AGENTS.md`。
- 已登记项目：不改 manifest，不删除登记，缺省继续走 broker。

## 初步方案与建议

见映射 spec 与 plan。

要点是把远端操作收成一组 typed 操作，broker 与 direct 两种传输实现同一组操作，且执行同一套本地前置校验。传输由项目侧声明选择；没有声明时按现有行为解析 manifest，以保持兼容。

## 风险

- direct 传输下，Git 凭据由项目自管，平台失去「会话拿不到凭据」这一层隔离。直推 `main`、强推与合并的拦截只能落在仓库服务端保护上。缓解方式是：工具里没有 merge 操作；`aisoft project-check` 读回保护规则，缺失时报 GAP；技能要求使用非管理员的项目身份。这是一项需要负责人在确认点 1 认可的安全取舍。
- 两条传输的行为可能漂移。缓解方式是共用一份前置校验实现，并用同一组回归用例跑两条传输。
- 改动牵涉多份活文档，runtime 单测钉了活文档短语，需要逐票跑全量 smoke。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把通用流程采用与中央项目登记解耦，登记降为可选的 broker 加固访问，涉及访问控制规则与 Agent 治理入口
risk_flags:
  - authorization
  - agent-governance
  - platform-governance
  - external-contract
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 改变「一切 Gitea/Git 访问走 broker」的访问控制规则，属于 authorization 与安全决策，强制 complex。
- 改技能、ADR 与项目 `AGENTS.md` 模板，属于 Agent 与平台治理。
- 使用发布包与会话工具的行为变化是项目侧外部契约。
- direct 传输的端到端证据要求真实或合成仓库上的读回，不能只靠 diff review 与 required CI 重放，所以声明 `verification`。
- 路由按 route-policy 取 R3，再应用 S1（平台仓、安全类）。`contract_effect: change` 不触发 G1。需求已在本线程经两轮讨论收敛，不另跑 grill-me。

### 缺失的 acceptance criteria 或决策

- 无。注册表归属（方案 A）与解耦（A+）已由负责人裁决。direct 传输的安全取舍写在 spec，由确认点 1 一并认可。
