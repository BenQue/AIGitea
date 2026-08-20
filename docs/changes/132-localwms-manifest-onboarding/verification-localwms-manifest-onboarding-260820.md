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

# Verification · LocalWMS manifest 登记（#132）

执行日期：2026-08-20 · 分支 `change/132-localwms-manifest-onboarding` · 基线 `origin/main` = `15b9dc6`

## T01 / T02 · 纯新增 diff

```
$ git diff --numstat
10	0	codex/config/gitea-governance.json
7	0	codex/config/host-access-broker.json
```

两文件均为 `新增 / 删除 = N / 0`，无既有行改动。**PASS**

## T03-1 · manifest validate

```
$ gitea-governance.sh --manifest codex/config/gitea-governance.json validate
{ "contract_version": "gitea-governance/v1", "environment": "local-orbstack",
  "owner": "admin", "platform_manager": "aisoft-platform-manager", ... }
退出码 0
```

**PASS**

## T03-2 · account-spec 由阻塞转为可解析

变更前（origin/main）：

```
BLOCKED_EXTERNAL: service account is not declared by the manifest
```

变更后：

```json
{
  "scopes": ["write:issue", "write:repository", "read:user"],
  "site_admin": false,
  "token_kind": "project-agent",
  "user_type": "bot",
  "username": "localwms-agent"
}
```

scopes 与 `project_agent_policy.token_scopes` 一致，`site_admin: false`。**PASS**

## T03-3 · 既有条目未受影响

```
governance 既有 9 条逐字段全等 : True
broker     既有 9 条逐字段全等 : True
两文件其余顶层键全等           : True
新增                           : ['LocalWMS'] / ['localwms']
broker operations 长度         : 26（未变）
```

**PASS**

## T03 · 契约测试期望值同步

首次实现只改了两份 manifest，未同步测试期望值，被平台 smoke 套件 fail-closed 拦下——这是该套件的预期行为，记录如下：

| 断言位置 | 首次结果 | 修正后 |
|---|---|---|
| `test-host-access-broker.sh` jq `.project_count == 9` | 静默 exit 1（`set -e` + jq -e，无输出） | `== 10`，PASS |
| `test_gitea_governance.py:133` `len(repositories) == 9` | `AssertionError: 10 != 9` | `== 10` 且 private 集合含 `LocalWMS`，PASS |
| `test_host_access.py:52` `len(projects) == 9` | `AssertionError: 10 != 9` | `== 10`，PASS |

`operation_count == 26` 与 `merge_operation_count == 0` 全程未改动，仍为原值。

## T04 · 全量 smoke 与 baseline 对照

| 运行 | 退出码 | 输出行数 | 结果 |
|---|---|---|---|
| `origin/main`（baseline，独立 detached worktree） | 0 | 538 | `Ran 437 tests ... OK` |
| 本分支，首次实现（仅改 manifest） | 1 | 24 | 停在 broker 契约测试 |
| 本分支，最终 | **0** | **538** | `Ran 437 tests in 24.335s ... OK` |

最终行数与 baseline 逐数相等，证明既未引入新失败，也未跳过既有用例。

## 目标仓库侧的既有事实（本变更未改动，仅记录）

```
admin/LocalWMS  private: true   empty: false   default_branch: main
refs/heads/main = 253a3136855b4dc05723931dd013151e25206ecc（16 提交，与 canonical checkout 零差异）
collaborators   : 空（apply 尚未执行，符合预期）
```

## 合并前未验证 / 不属本 PR

以下均依赖本 PR 合并后才具备前提，不在本次证据范围：

- `check --repository admin/LocalWMS` 的 live 结果（需 manifest 已合并且 manager 已是该仓 Admin）；
- `localwms-agent` 账号与 PAT 的实际创建（需人工 site-admin）；
- `apply` 施加的 visibility / project-agent Write / `main` protection / required CI context；
- broker `--project localwms` 的 typed 操作（需上述凭据落位）；
- LocalWMS 仓库 `CI / test (pull_request)` 的首次真实变绿。
