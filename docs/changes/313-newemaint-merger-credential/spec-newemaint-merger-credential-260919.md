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
status: contract-drafting
branch: change/313-newemaint-merger-credential
created: 2026-09-19
updated: 2026-09-19
---

# routine merger 凭据 403 的根因与合同修复

## 目标与原因

### 取证结论：不是凭据坏了，是合同自相矛盾

broker 在使用任何 routine 凭据之前，都会调 `_verify_identity`，它固定请求
`GET /api/v1/user`，再比对 `login` 与 `is_admin`
（`codex/runtime/aisoft_host_access/broker.py:2798`）。audit 的 routine 段在
`broker.py:3727` 调用它，真正的 merge 路径在 `broker.py:1293` 也调用它，且带
`require_non_admin_exact=True`。

同一份 manifest 把 routine merger 的 token scope 集合钉成**恰好一个**
`write:repository`（`codex/config/gitea-governance.json` 的
`routine_merge_agent_policy.token_scopes`）。Gitea 的 `GET /api/v1/user` 属于 user 作用域，
需要 `read:user`；缺少它时 Gitea 返回 HTTP 403，而不是 401。

于是：**按合同签发的 routine token，必然过不了合同自己的身份闸门。** 重新签发一份同样 scope
的 token 会一字不差地复现同一个 403。

### 三条互相独立的证据

1. **请求序列**（`312` 的 verification，已安装 runtime 实测）：
   `200 GET /api/v1/users/newemaint-routine-merger`（账号存在、非 site admin）紧接着
   `403 GET /api/v1/user`（用 routine merger 自己的 token）。403 的位置被精确定位在
   routine token 上，同时排除了「账号不存在」这一假设。
2. **对照组**：manifest 里另外三个身份策略全部显式带 `read:user` ——
   `platform_manager.audit_token_scopes`、`platform_manager.mutation_token_scopes`、
   `project_agent_policy.token_scopes`。这三个身份都走同一个 `_verify_identity`，都通过。
   唯一不带 `read:user` 的身份，正是唯一 403 的那个。
3. **Gitea 确实用 403 表达 scope 不足**：平台自己的 `_probe_token_scopes`
   （`broker.py:3858`）就是靠「请求 `/api/v1/notifications`，**断言必须是 403**，再从
   错误消息里解析 `token scope=`」来读回 scope 的。403 表示 scope 拒绝，是平台既有依赖的行为。

### 为什么测试是绿的

`codex/runtime/tests/test_host_access.py:3054` 的假 transport 对 `/api/v1/user` 无条件返回
200，而同一个 fixture 在 `/api/v1/notifications` 分支里又声明 `token-routine` 的 scope 只有
`write:repository`。假 transport 没有模拟 Gitea 的 scope 闸门，于是这份自相矛盾的合同在单元测试里
永远看不出来。这是缺陷能一直活到 live 的直接原因，必须一并修掉。

### 为什么只有 NewEMaint 触发

audit 的 routine 段包在 `if repository_contract.routine_auto_merge_enabled:` 里。manifest 六个
仓库中只有 NewEMaint 为 true，所以其余三个被治理的项目 audit 正常返回 PASS。LocalWMS 虽然配了
`localwms-routine-merger`，但 `routine_auto_merge_enabled` 为 false，同样不进入该分支。

### 修复必须两侧同时动

`_verify_identity` 跑在 `_probe_token_scopes` 之前，而 scope 比对是**精确相等**：

- 只给 token 补 `read:user`、不改 manifest：`_verify_identity` 通过，随后 scope 比对得到
  两个元素与期望的一个元素不等，audit 变成 `TOKEN_SCOPE_MISMATCH`，merge 路径变成
  `ROUTINE_TOKEN_SCOPE_MISMATCH`。这条已经被 `test_routine_merge.py:311` 当作负向用例钉住。
- 只改 manifest、不重发 token：token 仍缺 `read:user`，仍然停在同一个 403。

所以合同与凭据必须一起改，顺序是先合并合同、两台重装，再由负责人重发 token。

## Acceptance criteria

- [ ] **AC-1**（承接 Issue AC-1）合同修复合并、两台重装且负责人按新 scope 重发 token 之后，
  `host-access-broker --project newemaint --operation host.access.audit` 返回非 BLOCKED，
  且 `routine_merge.actual_token_scopes` 读回为 `read:user` 与 `write:repository` 两项。
- [ ] **AC-2**（承接 Issue AC-2）诊断结论写入 verification：403 的精确位置、账号状态、scope 状态、
  以及「重新签发同 scope 的 token 无法修复」这一结论，全文不含任何 token 值。
- [ ] **AC-3** `routine_merge_agent_policy.token_scopes` 增加 `read:user`，且下列三处逐字钉子
  同步到同一集合：`aisoft_gitea_governance/contract.py` 的校验、
  `codex/tools/bootstrap-gitea-service-account.sh` 的 routine PAT 读回闸门、
  `codex/tests/test-bootstrap-gitea-service-account.sh` 的 mock 与断言。
- [ ] **AC-4** 反向证明：任一钉子单独回退到旧值，合同加载或对应测试必须失败；证据写入 verification。
- [ ] **AC-5** `test_host_access.py` 的假 transport 改为按 token 的声明 scope 决定
  `/api/v1/user` 返回 200 还是 403。在**未**修 manifest 的情况下跑该用例必须失败，
  修好后必须通过；两次结果都写入 verification。
- [ ] **AC-6** `06-运维手册与踩坑集.md` 新增条目，记录「前一个闸门修好之后才暴露出下一个缺陷」
  这一形态与 merger 403 的诊断路径。
- [ ] **AC-7** `bash codex/tests/smoke.sh` 与 `python3 -m unittest tests.test_host_access
  tests.test_routine_merge tests.test_gitea_governance` 全绿；`check-change-documents` PASS；
  `apply-classification-labels.sh --verify 313` 读回 `projected`。

## 接口、数据与兼容性影响

- **安全边界**：routine merger 增加 `read:user`。该 scope 只读用户资料，不含任何写能力，
  不放大合并权限。`merge_allowed`、`repository_permission`、`ordinary_git_allowed`、
  `cross_project_write_allowed`、`allowed_operation` 一律不动。`213` 的最小权限意图保持不变：
  新集合仍是「让 broker 自己的身份闸门能跑」所需的最小集合。
- **为什么不改成不验身份**：`_verify_identity` 对 routine 凭据带 `require_non_admin_exact=True`，
  是防止 routine 身份被换成 site admin 的闸门。删掉它等于拆一道安全门，方向错误。
- **为什么不换端点**：要确认「我是谁」只有 `GET /api/v1/user`。scope 探针的 403 消息只含 scope，
  不含身份；collaborator permission 端点需要先知道用户名，是循环论证。
- **既有凭据**：旧 token 在新合同下会被 scope 闸门判为不符，必须重发。这是预期行为，不是回归。
- **数据与迁移**：无。

## 风险与回滚约束

- 合同改完、token 未重发的窗口期内，audit 会从 `HTTP_403` 变成 `TOKEN_SCOPE_MISMATCH`。
  两者都是 BLOCKED，routine 路径在整个窗口期保持不可用，不会出现「半开」状态。
- 回滚方式：revert 本 PR 的 merge commit 并两台重装，合同回到旧集合；此时 audit 回到
  `HTTP_403`，即当前已知状态。不产生新的破坏。
- 本次不动分支保护、不把 routine merger 加入 merge allowlist、不执行任何 merge、不部署。
- 凭据签发与写入全部由负责人执行。会话不读、不打印、不生成、不粘贴任何 token 值。

## 非目标

- 不启用、不演练 NewEMaint 的 routine 自动合并；AC-1 只验证 audit 读回，不验证 merge。
- 不把 `newemaint-routine-merger` 加入 `merge_whitelist_usernames`（当前 `["admin"]` 是
  合同允许的 pre-apply 状态）。
- 不改其它三个身份的 scope，不改 `212`/`208` 的 merge 硬门顺序。
- 不新增 broker typed 操作（例如读任意用户账号状态）。
- 不改 `AGENTS.md`、CI workflow 或部署脚本。

## 与 Issue 验收标准的映射

调度会话 2026-09-19 19:30 依本会话诊断改写了 Issue 标题与正文，加入「根因更正与裁决」一节，
取方案 B 并声明原范围第 2 条「重新签发同一 token」作废。本 spec 的合同与该裁决逐条一致；
本 spec 的 AC 是 Issue AC 的细分，映射如下：

| Issue AC | 本 spec |
|---|---|
| AC-1 audit 返回非 BLOCKED | AC-1 |
| AC-2 诊断入 verification 且不含 token 值；假 transport 先红后绿；三处 scope 钉子一致；smoke 全绿 | AC-2、AC-3、AC-5、AC-7 |
| AC-3 `06` 新条目；`check-change-documents` PASS；判级读回 `projected` | AC-6、AC-7 |

Issue 末尾「判级预期」那行写的 `contract_effect=unchanged` 早于裁决，本次按 `change` 判：
routine merger 的 token scope 是安全边界合同，本变更改了它。判级维度本身仍是
`type/security` 与 `complexity/complex`，与 Issue 预期一致。

## 未决问题

无。原先的范围裁决已由负责人在确认点 1 取方案 B，调度会话同步改写了 Issue 正文。

`prohibit_login` 与 `restricted` 仍未读回（broker 没有读任意用户账号状态的 typed 操作，
隔离复验被本机权限策略拒绝），按裁决如实记 `NOT RUN`：scope 缺失已足以解释 403，
若重签 token 后仍 403，再核这两个字段。这不改变实现方向。

本会话实现过程中只读发现的「服务账号 PAT 没有被测试覆盖的显式轮换路径」已由调度会话立为
**#316**，阻塞于本 Issue 合并与两台重装，不在本次范围内。
