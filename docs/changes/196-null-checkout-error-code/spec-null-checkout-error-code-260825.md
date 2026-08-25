---
issue: 196
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/196
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - external-contract
  - shared-core
depends_on: []
status: approved
branch: change/196-null-checkout-error-code
created: 2026-08-25
updated: 2026-08-25
---

# Spec：`mac_checkout: null` 在 `host.onboarding.check` 上的错误码与判定顺序

## 目标与原因

让 `host.onboarding.check` 对「本项目没有 Mac 侧交付路径」这一**正确的终态声明**
给出字面含义正确的答案，并与 typed git 路径 `_git` 对同一条件的处理保持结构一致。

改动前 `_onboarding_check`（broker.py:1566-1570）：

```python
access_operation = self.contract.operation("host.access.audit")
access = self._access_audit(project, access_operation)
if project.mac_checkout is None:
    raise BrokerError("ONBOARDING_MISMATCH", "canonical checkout is not configured")
```

`_git`（broker.py:1309-1311）对同一条件：

```python
canonical = project.mac_checkout
if canonical is None:
    raise BrokerError("TARGET_UNAVAILABLE", "project has no approved Mac checkout")
```

两处分歧有两层：错误码语义，以及该判定相对于凭据解析的先后。本 spec 两层都改，
使 `_onboarding_check` 与 `_git` 对齐。

## 本 spec 授权的治理改动

按 AGENTS.md「只有 complex 变更映射的 `spec` 明确授权时，才能修改 …… 治理文件」，
本 spec 显式授权且**仅**授权下列改动：

- `codex/runtime/aisoft_host_access/broker.py` 中 `_onboarding_check` 的开头五行：
  把 `mac_checkout is None` 的判定上移到 `_access_audit` 调用之前，并把错误码与
  message 改成与 `_git` 逐字一致的 `TARGET_UNAVAILABLE` /
  `project has no approved Mac checkout`。
- `codex/runtime/tests/test_host_access.py` 新增覆盖该分支的测试。

不授权：改动 `_access_audit` 自身、`_git`、任何 manifest 声明、任何其它 broker
操作，也不授权修改 `AGENTS.md` 或任何 CI/部署脚本。

## Acceptance criteria

- [ ] **AC-1** `mac_checkout` 为 `null` 的项目在 `host.onboarding.check` 上得到的
      错误码，其字面含义与该项目的真实声明状态一致，且与同条件下 `_git` 路径的
      错误码不矛盾——具体即两条路径都返回
      `TARGET_UNAVAILABLE: project has no approved Mac checkout`。
- [ ] **AC-2** 覆盖该分支的单元测试存在：构造「有凭据 + `mac_checkout: null`」的
      组合并断言错误码。该组合现网不存在，必须由测试补上。
- [ ] **AC-3** 不放宽 `_onboarding_check` 的任何既有断言（沿用 #191 AC-4）：
      `mac_checkout` 非 `null` 时的执行路径与断言集合逐条不变，既有测试全绿。
- [ ] **AC-4** 因本 spec 改动了断言顺序，须对全部 10 个 manifest 项目复跑
      `host.onboarding.check`，记录改动前后对比，并说明每个变化项目的新结果
      为什么更贴近事实。

## 接口、数据与兼容性影响

- **改变的可观测输出**：`myapp`、`sap-table-migrate`、`smoke-test`、`wmpda` 四个项目
  的 `host.onboarding.check` 由
  `{"code":"CREDENTIAL_UNAVAILABLE","message":"approved credential binding is unavailable"}`
  变为
  `{"code":"TARGET_UNAVAILABLE","message":"project has no approved Mac checkout"}`。
- **不变的**：`status` 仍是 `BLOCKED_EXTERNAL`，CLI 退出码仍是 20——所有 `BrokerError`
  在 `cli.py:155` 走同一个映射。按 `status` 或退出码判定的调用方行为不变。
- `mac_checkout` 非 `null` 的 6 个项目：PASS 载荷、断言顺序、错误码全部不变。
- 无 schema、无数据、无迁移、无部署影响。

## 风险与回滚约束

- 回滚方式：`git revert` 该 commit；改动集中在一个函数的五行内，无状态、无迁移，
  revert 后行为立即回到改动前。
- 新增的短路只对 `mac_checkout is None` 生效。这些项目在改动前也一定失败（凭据
  与 checkout 两条断言都不满足），所以短路不会让任何原本失败的输入变成通过——
  这是 AC-3 的核心论据。
- `mac_checkout` 来自本地 manifest，短路发生在任何凭据解析、主机命令和网络访问
  之前，不构成新的信息泄露面。

## 非目标

- 不改 `_access_audit` 的任何断言、顺序或错误码。
- 不改 `_git` 路径——本次是让 `_onboarding_check` 向它对齐，不是双向改动。
- 不改任何项目的 `mac_checkout` 声明；四个 `null` 项目保持 `null`。
- 不给这四个项目补 Mac 凭据目录——它们没有 Mac 交付路径，本就不该有。
- 不重装本机已安装的 broker（`sudo bash codex/install-host-access-broker.sh`）；
  验收用候选 runtime 直调，重装是合并后的独立运维动作。

## 未决问题

无。Issue 正文 §待确定的两条决策已由人在 2026-08-25 明确：
(1) 错误码改抛 `TARGET_UNAVAILABLE`；(2) 断言顺序改为 null 判定先跑。
