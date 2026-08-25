---
issue: 196
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/196
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改 broker runtime（aisoft_host_access/broker.py）的 host.onboarding.check 断言顺序与错误码，触发平台治理强制 complex；四个 mac_checkout 为 null 的项目的可观测错误码由 CREDENTIAL_UNAVAILABLE 变为 TARGET_UNAVAILABLE，属外部契约变更
risk_flags:
  - platform-governance
  - external-contract
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-null-checkout-error-code-260825.md
  spec: spec-null-checkout-error-code-260825.md
  plan: plan-null-checkout-error-code-260825.md
  verification: verification-null-checkout-error-code-260825.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/196-null-checkout-error-code
pr_url:
created: 2026-08-25
updated: 2026-08-25
---

## 问题/需求总结

同一个前置条件 `project.mac_checkout is None` 在 broker 的两条路径上被放在不同位置、
抛不同的错误码：

| 路径 | 位置 | 错误码 | 与凭据解析的先后 |
|---|---|---|---|
| `_git`（typed git 操作） | broker.py:1309-1311 | `TARGET_UNAVAILABLE: project has no approved Mac checkout` | 判定在前，凭据在后 |
| `_onboarding_check` | broker.py:1567-1569（改动前） | `ONBOARDING_MISMATCH: canonical checkout is not configured` | 凭据在前，判定在后 |

`ONBOARDING_MISMATCH` 的语义是「配置与主机实况不符，需要修」。而 `mac_checkout: null`
是**声明完整且正确**的终态——该项目没有 Mac 侧交付路径，没有任何东西需要修。用前者
表达后者，会把一个正常声明读成待修缺陷。这正是 #191 里选项 C 讨论踩到的坑：Issue 正文
按 `_git` 的行为预期 `TARGET_UNAVAILABLE`，实测 `host.onboarding.check` 并不会。

顺序分歧还有第二个后果：manifest 里 `mac_checkout: null` 的四个项目（`myapp`、
`sap-table-migrate`、`smoke-test`、`wmpda`）在 Mac 上也没有凭据目录，`_access_audit`
先失败，返回 `CREDENTIAL_UNAVAILABLE: approved credential binding is unavailable`。
该错误码会把运维引向「去装一份凭据」——而这四个项目本就不该有 Mac 凭据。因此
`ONBOARDING_MISMATCH` 这条分支在现网**从来没被观测到过**，缺陷一直隐着。

## 影响范围

- `codex/runtime/aisoft_host_access/broker.py`：`_onboarding_check` 一处，5 行内。
- `codex/runtime/tests/test_host_access.py`：新增两个测试。
- 可观测输出：10 个 manifest 项目中 4 个的 `host.onboarding.check` 错误码改变
  （`CREDENTIAL_UNAVAILABLE` → `TARGET_UNAVAILABLE`）；6 个 `mac_checkout` 非 null
  的项目断言顺序与结果完全不变。
- 所有 `BrokerError` 都被 `cli.py:155` 统一映射到 `status: BLOCKED_EXTERNAL`，
  退出码 20。本变更只改 `code` 与 `message`，不改 `status` 与退出码。

## 初步方案与建议

把 `mac_checkout is None` 的判定移到 `_access_audit` 之前，并改抛
`TARGET_UNAVAILABLE: project has no approved Mac checkout`——与 `_git` 路径逐字一致。
两条路径此后同构：先问「本项目有没有 Mac 交付路径」，再问「凭据/绑定对不对」。

人在 2026-08-25 就 Issue 正文 §待确定的两条分别决策：错误码改抛 `TARGET_UNAVAILABLE`；
断言顺序改为 null 判定先跑（因此触发 AC-4 的 10 项目复跑）。

## 风险

- **对外可观测输出变化**：4 个项目的错误码改变。缓解——本变更用 10 项目改动前后
  对照表（映射的 `verification`）逐个记录，且 `status`/退出码不变，脚本按 `status`
  或退出码判定的调用方不受影响。
- **断言被绕过的风险**：不存在。新增的短路只对 `mac_checkout is None` 生效，这些
  项目本来就在后续第一条断言（`_access_audit`）上 fail-closed；`mac_checkout` 非 null
  时执行路径逐行未变，既有断言一条不减（AC-3）。
- **权限边界**：`mac_checkout` 来自本地 manifest，短路不泄露凭据、不接触主机与网络；
  新测试断言此时 transport 与 credential resolver 都不会被调用。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 改 broker runtime（aisoft_host_access/broker.py）的 host.onboarding.check 断言顺序与错误码，触发平台治理强制 complex；四个 mac_checkout 为 null 的项目的可观测错误码由 CREDENTIAL_UNAVAILABLE 变为 TARGET_UNAVAILABLE，属外部契约变更
risk_flags:
  - platform-governance
  - external-contract
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 改动对象是 host-access broker runtime，属 AGENTS.md「Agent 或平台治理变更一律按
  complex」；`change_type: platform` 本身也在 `FORCED_COMPLEX_TYPES` 内
  （`classification.py:54`）。
- `contract_effect: change`：broker 的错误码是调用方可观测的对外契约，本次让 4 个
  项目的 `code` 改变，不是 restore 也不是 unchanged。
- `risk_flags` 三项均在 `FORCED_COMPLEX_RISKS` 内：`platform-governance`（broker
  runtime）、`external-contract`（错误码面）、`shared-core`（broker 为全项目共享组件）。
- 声明 `verification`：本次的关键证据是「改动前才观测得到」的 10 项目基线与前后对照，
  以及候选 runtime 的实调；diff review 与 required CI 都无法复现，合并后无法重放。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文 §待确定的两条决策已由人在 2026-08-25 明确（见「初步方案与建议」），
  两条都选择了变更侧，AC-1..AC-4 全部可测。
