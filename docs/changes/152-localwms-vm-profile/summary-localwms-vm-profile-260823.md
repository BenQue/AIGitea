---
issue: 152
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/152
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: pr-open
branch: change/152-localwms-vm-profile
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/156
created: 2026-08-23
updated: 2026-08-23
reason: 改动 host-access broker 的 governance manifest 与共享合同校验（新增一个项目的 VM profile 声明），属 Agent/平台治理类别，强制 complex
required_docs:
  - summary
  - spec
  - plan
  - verification
override_reason: ''
documents:
  summary: summary-localwms-vm-profile-260823.md
  spec: spec-localwms-vm-profile-260823.md
  plan: plan-localwms-vm-profile-260823.md
  verification: verification-localwms-vm-profile-260823.md
---

## 问题/需求总结

LocalWMS 路线图 M3 的退出门之一是 **analyzer 低风险 canary**。它现在做不了，因为
`codex/config/host-access-broker.json` 里 `localwms` 的 `vm_profile` 是 `null`：

```
$ /usr/local/libexec/aisoft/project-profile-migration --project localwms --action plan
{"code": "TARGET_DENIED", "message": "project has no approved VM profile migration", "status": "BLOCKED_EXTERNAL"}
```

本变更只解开 manifest 这一道锁：给 `localwms` 声明一份 analyzer-only 的 `vm_profile`。
真正的 canary 执行是一次运维动作，需独立授权，不在本变更范围内。

## 影响范围

锁其实有两处，都必须一起动，否则 manifest 加载会 fail closed：

1. `codex/config/host-access-broker.json` —— `localwms.vm_profile` 从 `null` 变成具体声明。
2. `codex/runtime/aisoft_host_access/contract.py` —— 校验里有一条**双向相等**断言
   `profile_repositories == {五个仓}`。它不是「子集」检查，所以只填 JSON 会让整份
   manifest 校验失败。允许集必须同步扩到六个（新增 `LocalWMS`）。

这是治理写路径故意设的两处摩擦：改 JSON 是**声明**，改 contract 是**批准**。

连带需要同步的断言（同一事实的三份镜像）：

- `codex/runtime/tests/test_host_access.py` —— profile 映射表、`path_prepend` 声明表、
  以及新增的 LocalWMS profile 形状测试。
- `codex/tests/test-host-access-broker.sh` —— jq 的 `vm_profile != null` 仓库列表。

不改动的：`codex/config/gitea-governance.json`（LocalWMS 已在 #148 声明
`change_control: development`，`vm_identity_policy` 与本变更无关）、任何其它项目的 profile、
任何 timer 的启用状态。

## 初步方案与建议

`localwms` 的 `vm_profile` 取值与三个既有业务项目对齐：

| 字段 | 取值 | 依据 |
|---|---|---|
| `name` | `localwms` | profile 名在 manifest 内全局唯一，取 project_id |
| `repo_dir` | `work/LocalWMS` | 与仓库名一致，同 `work/NewEMaint`、`work/SFMDigitalBoard` |
| `analysis_provider` | `claude` | 平台既有惯例：三个 internal-application（NewEMaint / SFMDigitalBoard / rsdesign-new）全是 `claude`，只有平台仓 aisoft-platform 是 `codex`。LocalWMS 是 internal-application |
| `implement_provider` | `none` | 平台默认；contract 里还有一条 `implementation == "none"` 的硬断言 |
| `timer_unit` | `null` | Development Loop 不在范围内；contract 的 timer 白名单也只有 emaintenance / sfm 两个既有单元 |
| `path_prepend` | 不声明 | 只有 SFMDigitalBoard 需要（Node 22 路径），LocalWMS 无此需求 |

## 风险

- **合并 ≠ 生效**：broker 读的是 `/usr/local/share/aisoft/host-access-broker.json`，
  合并后还须 sudo 重装才会被 broker 看到。已核实本次改动前 installed 与仓库副本 `diff` 为空，
  说明上一次 manifest 变更的重装有人做过，但它不是自动的。详见 verification 的交接项。
- **扩大的是声明面，不是执行面**：`implement_provider=none` + `timer_unit=null` 意味着
  这份 profile 只能被 analyzer 消费，不会被 Loop 或 timer 拉起。
- **`localwms-agent` 的 VM 侧凭据尚未验证**：`vm.profile.plan` 会去读
  `/home/benque/.config/aisoft/credentials/localwms-agent-project-agent.token`。
  这一步只有在 manifest 重装后、在 VM 内才能验证，属 canary 的前置运维项。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 改动 host-access broker 的 governance manifest 与共享合同校验（新增一个项目的 VM profile 声明），属 Agent/平台治理类别，强制 complex
risk_flags:
  - platform-governance
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

- AGENTS.md：「Agent 或平台治理变更一律按 complex 处理」。本变更写的是
  `codex/config/host-access-broker.json`（governance manifest）与
  `codex/runtime/aisoft_host_access/contract.py`（broker 合同校验）。
- `contract_effect: add`：LocalWMS 此前没有任何 VM profile 声明，本变更为它新增了一个
  可被 analyzer 消费的治理面，不是恢复或维持既有产品合同，因此不满足 small 的候选条件。
- `shared-core`：`contract.py` 的允许集断言对全部十个项目的 manifest 加载生效，改错会让
  broker 对所有项目 fail closed。

### 缺失的 acceptance criteria 或决策

- 无。Issue 已给出可测验收标准；`analysis_provider` 的取舍由平台既有惯例裁定（见上表）。
