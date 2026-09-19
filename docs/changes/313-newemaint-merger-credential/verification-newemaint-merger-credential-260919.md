---
issue: 313
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/313
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - authorization
  - platform-governance
  - shared-core
depends_on:
  - 312
status: pending
branch: change/313-newemaint-merger-credential
created: 2026-09-19
updated: 2026-09-19
---

# Verification

## 基线与范围

- Commit SHA: 待填写
- 基线：`origin/main` = `3ff697202623651992526df025f016eaf101eaa1`
- 环境：Mac 交互会话，已安装 broker source commit `3ff6972`，36 typed operations；
  Mac 与 gitea-ci 两台已由负责人在 `312` 合并后重装
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-7

## 诊断（AC-2）

### 现场复现

| Command / check | Result | Evidence |
|---|---|---|
| `host-access-broker --project newemaint --operation host.access.audit` | BLOCKED | `{"code": "HTTP_403", "message": "Gitea returned HTTP 403", "status": "BLOCKED_EXTERNAL"}`，与 `312` 会话记录一致，非抖动 |
| `host-access-broker --project newemaint --operation gitea.protection.read` | PASS | `status_check_contexts` 两条与 manifest 一致；`merge_whitelist_usernames` 为 `["admin"]`，即合同允许的 pre-apply 状态；说明 manager audit 凭据本身可用 |
| `host-access-broker --project newemaint --operation host.onboarding.check` | BLOCKED | 同样 `HTTP_403`，与 audit 同源 |
| `host-access-broker --project {localwms, sfm-digital-board, aisoft-platform} --operation host.access.audit` | PASS（`312` 已记录） | 三仓正常；它们 `routine_auto_merge_enabled` 为 false，不进入 routine 分支 |

### 403 的精确位置

`312` 的 verification 记录了已安装 runtime 的完整请求序列，其中相邻两行定位了故障点：

```text
200 GET /api/v1/users/newemaint-routine-merger      账号存在、is_admin 为 false
403 GET /api/v1/user                                用 routine merger 自己的 token
```

前一行用 manager audit 凭据成功读到该账号，**排除了「账号不存在」这一假设**；后一行是
`_verify_identity`（`codex/runtime/aisoft_host_access/broker.py:2798`）用 routine 凭据发出的，
由 audit 的 routine 段在 `broker.py:3727` 调用。`312` 还用 pre-`312` 的已安装 runtime 与旧
manifest 单独解析同一凭据调用 `_verify_identity`，同样得到 `HTTP_403`，证明与 required context
集合无关。

### 根因：合同自相矛盾，不是凭据失效

| 观测 | 来源 | 结论 |
|---|---|---|
| `routine_merge_agent_policy.token_scopes` 恰为 `["write:repository"]` | `codex/config/gitea-governance.json` | 合规签发的 routine token 只有这一个 scope |
| `GET /api/v1/user` 属 Gitea 的 user scope 类别，需要 `read:user` | Gitea 上游文档 `development/oauth2-provider`，原文把该类别描述为覆盖 `/user/*` 与 `/users/*` 路由 | 只有 `write:repository` 的 token 调它必然被拒 |
| Gitea 用 HTTP 403 表达 scope 不足 | 平台自己的 `_probe_token_scopes`（`broker.py:3858`）断言 `/api/v1/notifications` **必须**返回 403，再从消息里解析 `token scope=` | 403 是 scope 拒绝，不是账号问题 |
| 另外三个身份策略全部显式带 `read:user` | 同一 manifest 的 `platform_manager.audit_token_scopes`、`platform_manager.mutation_token_scopes`、`project_agent_policy.token_scopes` | 走同一个 `_verify_identity` 且全部通过；唯一不带 `read:user` 的身份正是唯一 403 的那个 |
| `bootstrap-gitea-service-account.sh` 硬闸门要求 routine PAT 的读回 scope 恰等于 `write:repository` | `codex/tools/bootstrap-gitea-service-account.sh` 的 routine 分支 | 按现行 runbook 重新签发，会一字不差地复现同一个 403 |

**结论：Issue 正文假设的「过期 / 撤销 / 账号被禁」均不成立，处置「重新签发 token」无效。**
根因是 routine merger 的 scope 合同缺少 `read:user`，而 broker 的身份闸门必须调用需要该 scope
的端点。缺陷先于 `312` 存在，只是此前 `PROTECTION_MISMATCH` 在链条更前面中止，把它遮住了。

本节不含任何 token 值。会话未读取、未打印、未生成、未写入任何凭据内容。

### 为什么测试是绿的

`codex/runtime/tests/test_host_access.py` 的 newemaint audit 用例中，假 transport 对
`/api/v1/user` 无条件返回 200，同一份 fixture 却在 `/api/v1/notifications` 分支声明
`token-routine` 的 scope 只有 `write:repository`。假 transport 没有模拟 Gitea 的 scope 闸门，
这份自相矛盾的合同因此在单元测试里不可见。

### 未能读回的字段

broker 没有读取任意用户 `prohibit_login` 与 `restricted` 的 typed 操作，本会话无法读回这两个
字段。尝试用源码 runtime 解析 routine 凭据做隔离复验的动作被本机权限策略以
`Credential Exploration` 拒绝，**未执行、未绕过**。scope 缺失已足以充分解释 403；若按新合同重发
token 后 AC-1 仍不通过，下一步是由负责人在 Gitea 管理界面核对这两个字段。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 合同文档与判级 | 待填写 | 待填写 |
| T01 假 transport 先红 | NOT RUN | 待填写 |
| T02 scope 合同与 governance 校验 | NOT RUN | 待填写 |
| T03 bootstrap 闸门与 shell 测试 | NOT RUN | 待填写 |
| T04 `06` 条目与全量 smoke | NOT RUN | 待填写 |
| T05 负责人重发 token 与两台重装后的只读复验 | NOT RUN | 待填写 |

命令与输出照实抄。改动前才观测得到的证据只有写在这里才留得下来。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 依赖负责人重发 token 与两台重装 |
| AC-2 | 达成 | 见上面「诊断」整节 |
| AC-3 | NOT RUN | 待填写 |
| AC-4 | NOT RUN | 待填写 |
| AC-5 | NOT RUN | 待填写 |
| AC-6 | NOT RUN | 待填写 |
| AC-7 | NOT RUN | 待填写 |

## 遗留风险与未完成项

- 合同改完、token 未重发的窗口期内 audit 会从 `HTTP_403` 变成 `TOKEN_SCOPE_MISMATCH`；
  两者都是 BLOCKED，routine 路径全程不可用，不会出现半开状态。
- source 合并不等于 installed 生效；未经两台重装，任何 source PASS 都不得投影为 installed PASS。
- 本次不启用 routine 自动合并、不改分支保护、不执行 merge、不部署。
