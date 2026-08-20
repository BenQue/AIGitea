---
issue: 132
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/132
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: spec-drafting
branch: change/132-localwms-manifest-onboarding
pr_url: ''''
created: 2026-08-20
updated: 2026-08-20
---

# Spec · LocalWMS manifest 登记（#132）

## 目标

使 `admin/LocalWMS` 成为 governance 与 host-access 两份 manifest 的显式受管对象，且不改变任何既有项目的行为。

## 精确变更

### 1. `codex/config/gitea-governance.json` → `repositories[]`

按现有 case-insensitive 字母序插入 `HSDB` 与 `myapp` 之间：

```json
{
  "name": "LocalWMS",
  "classification": "internal-application",
  "visibility": "private",
  "project_agent": "localwms-agent",
  "status_check_contexts": [
    "CI / test (pull_request)"
  ],
  "required_approvals": 0
}
```

字段依据：

| 字段 | 依据 |
|---|---|
| `name` | owner 为顶层 `admin`，exact repository 即 `admin/LocalWMS`；大小写沿用项目自身名称，与 `HSDB`/`NewEMaint`/`SFMDigitalBoard` 风格一致 |
| `classification` | 业务应用，非平台仓、非测试仓 |
| `visibility` | 不在 `repository_policy.public_allowlist`，取 `default_visibility: private` |
| `project_agent` | 沿用 `<项目>-agent` 小写命名；权限由 `project_agent_policy` 固定为 Write 且 `merge_allowed: false` |
| `status_check_contexts` | 与 LocalWMS 仓库 `.gitea/workflows/ci.yml` 的 `name: CI` + job key `test` 精确匹配 |
| `required_approvals` | 与全部既有仓库一致；唯一硬闸门是人工合并 |

### 2. `codex/config/host-access-broker.json` → `projects[]`

按现有字母序插入 `hsdb` 与 `myapp` 之间：

```json
{
  "project_id": "localwms",
  "repository": "LocalWMS",
  "project_agent": "localwms-agent",
  "mac_checkout": "/Users/benque/Projects/LocalWMS",
  "vm_profile": null
}
```

字段依据：

| 字段 | 依据 |
|---|---|
| `project_id` | broker `--project` 实参，沿用小写命名 |
| `mac_checkout` | canonical checkout，`mac.git.bind` 只在此写 repo-local scoped helper |
| `git_remote_name` | **刻意不声明**。Issue #73 规定未声明即为 `origin`；LocalWMS 为新建仓库，remote 即 `origin`，无需如 NewEmaint 固定 `gitea` |
| `vm_profile` | `null` —— analyzer/Loop 属 LocalWMS 路线图 M3；与 `myapp`/`wmpda`/`sap-table-migrate` 同形 |

### 3. 同步既有契约测试的受管对象期望值

平台契约测试刻意钉死受管对象的精确数量与集合，以防止 manifest 被静默扩张。新增一个受管仓库必须同步以下三处，且**只改数量/集合，不放松断言强度**：

| 文件 | 改动 |
|---|---|
| `codex/tests/test-host-access-broker.sh` | jq 断言 `.project_count == 9` → `== 10`；`operation_count == 26` 与 `merge_operation_count == 0` **保持不变** |
| `codex/runtime/tests/test_host_access.py` | `assertEqual(len(self.contract.projects), 9)` → `10` |
| `codex/runtime/tests/test_gitea_governance.py` | `assertEqual(len(self.contract.repositories), 9)` → `10`；private 精确集合加入 `"LocalWMS"` |

不需要改动的相关断言（已验证 LocalWMS 天然满足）：

- `test_host_access.py` 的 `profiles` 映射只收录 `vm_profile is not None` 的项目，LocalWMS 为 `null`，不入表；
- `test_manifest_fixed_remote_defaults_and_rejects_unsafe_names` 断言「未列入 gitea 远端集合的项目必须默认 `origin` 且不得声明 `git_remote_name`」—— LocalWMS 正因未声明该字段而满足；
- `public_allowlist` 断言不变，LocalWMS 为 private。

## 明确不在范围

创建 `localwms-agent` 账号与 PAT、`bootstrap-manager`、`governance apply`、分支保护施加、CI 首跑、任何部署。以上均在本 PR 合并后按 runbook §1.1 顺序单独执行。

## 回滚

`git revert` 本 PR 的合并提交即可。本变更不产生 Gitea 侧副作用（未建账号、未改权限、未动保护），故回滚无残留。
