---
issue: 210
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/210
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci-integration
  - rollback
  - platform-governance
depends_on: []
status: approved
branch: change/210-required-context-migration
created: 2026-08-26
updated: 2026-08-26
---

# Evidence-approved required-context migration 规格

## 目标与原因

在不放宽普通 protection drift 检查的前提下，为 manifest 已钉住、真实成功 PR status 已证明的
required context 提供一次窄作用域 migration 能力。该能力必须把 exact repository、canonical
context、evidence、snapshot、read-back 与 rollback 绑定为同一个可审计事务边界。

## Acceptance criteria

- [ ] AC-1：manifest 以 strict schema 为 exact repository 声明可选 required-context migration
  evidence；未声明时现有行为逐字保持。CLI 只接受 manifest repository 名或等价固定 selector，
  不接受 URL、owner/repo、context、force/bypass/legacy 参数。
- [ ] AC-2：evidence 至少绑定 exact repository、exact canonical context、Gitea pull request 编号、
  full head SHA、`pull_request` event 与 `success` state；字段缺失、额外字段、错误 repo/context、
  非成功状态、非 PR event、非 full SHA 均在 mutation 前 fail closed。
- [ ] AC-3：migration 只允许 live 起点为 status check disabled 且 contexts 空；除
  `enable_status_check` 与 `status_check_contexts` 外，所有受管 protection 字段必须与 manifest
  精确一致。任何其它 drift、live 非空/未知 context 或 manifest 多 context 都继续产生 blocker。
- [ ] AC-4：plan 必须显式区分普通 `status-check-context-drift` 与 evidence-approved migration action；
  普通 `apply` 不选择 migration 时仍按现有错误 fail closed。
- [ ] AC-5：apply 在任何 PATCH 前原子持久化完整、可解析且 exact-repository-bound 的 protection
  snapshot；snapshot 失败时不得调用 PATCH。
- [ ] AC-6：PATCH 后完整 read-back，并用与 plan 相同的严格比较验证 direct/force push 禁止、
  merge allowlist 仅 `admin`、required approvals、所有其它受管字段不变且唯一 context 为
  `CI / verify (pull_request)`；PATCH 或 read-back 失败返回失败，不宣称迁移成功。
- [ ] AC-7：rollback 只接受该 exact repository 的已持久化 snapshot，恢复后完整 read-back；
  snapshot repo/branch/schema 不匹配时 fail closed。
- [ ] AC-8：测试覆盖合法 migration，以及错误/额外 context、错误 repository、非成功/非 PR
  evidence、其它 protection drift、snapshot 写失败、PATCH/read-back 失败和 rollback 正反例；
  相关 Python tests、`python3 -m compileall`、`bash codex/tests/smoke.sh` 与适用 shell 静态检查通过。
- [ ] AC-9：本 Change 只准备唯一最终 PR；live apply、runtime/skill 安装、部署与 merge 均为
  `NOT RUN`，创建/提交 PR 前等待人工确认。

## 接口、数据与兼容性影响

- `codex/config/gitea-governance.json` 可为 exact repository 增加一个 strict migration evidence
  对象；它只描述 source-approved evidence，不表示 live apply 已授权或执行。
- governance contract/parser 拒绝未知键、宽泛 selector、非 full SHA、重复或多 context。
- planner/apply 增加显式 migration selector；缺省路径与现有任意 drift fail-closed 行为兼容。
- snapshot schema 若需扩展，必须版本化并继续验证 repository/branch；rollback 不猜测 target。
- 不改变 Gitea API target、credential route、manager/project-agent ACL 或 merge surface。

本规格授权修改以下范围；不授权修改 `AGENTS.md`：

- `codex/config/gitea-governance.json`
- `codex/runtime/aisoft_gitea_governance/contract.py`
- `codex/runtime/aisoft_gitea_governance/reconcile.py`
- `codex/runtime/aisoft_gitea_governance/cli.py`
- `codex/runtime/tests/test_gitea_governance.py`
- `codex/tools/gitea-governance.sh`（仅在 CLI wrapper 需要透传固定 selector 时）
- `codex/tests/smoke.sh`（仅在新增独立测试入口需要接入时）
- `06-运维手册与踩坑集.md`（只记录该能力的使用边界与 rollback）
- 本 Issue 映射的 summary/spec/plan/verification。

## 风险与回滚约束

- 不能从 caller 输入或 live discovery 推导目标 context；唯一事实源是 merged manifest。
- evidence 只能批准 manifest 与 live 空起点之间的一次收敛，不能批准 context-to-context 替换。
- snapshot 必须先于 PATCH；read-back 必须比较所有受管 protection 字段。
- source 可整体 revert 唯一 PR。未来 live migration 只能在独立授权下执行，失败时使用同次
  apply 之前的 exact snapshot rollback 并再次完整读回。

## 非目标

- 通用 protection bypass、force、legacy 或 arbitrary drift acceptance。
- 任意 URL/repository/context 输入或跨仓批量 apply。
- 修改 visibility、权限、merge allowlist、direct/force push、approval 数量或 agent merge 能力。
- live apply、安装、部署、PR merge 或 #208 routine auto-merge。

## 未决问题

无。
