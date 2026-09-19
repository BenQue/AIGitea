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
status: verified
branch: change/313-newemaint-merger-credential
created: 2026-09-19
updated: 2026-09-19
---

# Verification

## 基线与范围

- Commit SHA: `fdff484a38bde8b85ac79f0572a344672b763295`（PR 315 的 head）
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
| 判级投影 `apply-classification-labels.sh --verify 313` | PASS | `"result":"projected"`，`change_type` 为 `security`，`complexity` 为 `complex` |
| 生命周期标签 `gitea.issue.labels.set --number 313 --lifecycle approved` | PASS | `before` 为 `["complexity/complex", "needs-analysis", "type/security"]`，`after` 为 `["approved", "complexity/complex", "type/security"]` |
| **T01 假 transport 先红**（改 fixture、未改 manifest） | **FAIL，如预期** | `python3 -m unittest tests.test_host_access tests.test_routine_merge` → `Ran 207 tests` / `FAILED (failures=21, errors=4)`；42 处断言差异全是 `HTTP_403`，例如 `AssertionError: 'HTTP_403' != 'ROUTINE_HEAD_DRIFT'`、`'HTTP_403' != 'ROUTINE_CANARY_ONLY'`；audit 用例 `test_newemaint_routine_audit_covers_account_scope_write_cross_project_and_allowlist` 直接 ERROR。这就是 live 行为第一次在测试里显形 |
| T02 scope 合同与 governance 校验 | PASS | 补 `read:user` 并同步 `contract.py` 后，`python3 -m unittest tests.test_host_access tests.test_routine_merge tests.test_gitea_governance` → `Ran 258 tests` / `OK` |
| T03 bootstrap 闸门与 shell 测试 | PASS | `bash -n` OK；`bash codex/tests/test-bootstrap-gitea-service-account.sh` → `bootstrap Gitea service account tests passed` |
| T04 `06` 条目与全量 smoke | 见下方 smoke 行 | 踩坑 33 与凭据清单新增 routine merger 行 |
| T05 负责人重发 token 与两台重装后的只读复验 | NOT RUN | 依赖负责人动作，见「未完成项」 |
| `git.push.change --branch change/313-newemaint-merger-credential` | PASS | 第一次 `pushed_head` 为 `1b49c4114ff96037558706ba1a8b2bcc44d9992b`、`previous_head` 为 `null`；回填后为 `fdff484a38bde8b85ac79f0572a344672b763295`。返回体带 `pushed_head` 即说明 #298 的单写者归属闸门已生效 |
| `gitea.pull.create --issue 313` | PASS | PR `315`，`mergeable: true`，base `3ff697202623651992526df025f016eaf101eaa1`，head `fdff484a…`，`changed_files: 11` |
| required CI（最终 head） | PASS | `gitea.commit.status.read --sha fdff484a…` → `state: success`；`CI / verify (pull_request)` success，run 1580 job 1639 |

### 反向证明（AC-4）

| 回退的那一处 | 结果 | 证据 |
|---|---|---|
| 只回退 manifest（`contract.py` 保持新值） | 整份合同拒绝加载 | `ContractError: routine_merge_agent_policy.token_scopes must equal ['write:repository', 'read:user']` |
| 只回退 `contract.py`（manifest 保持新值） | 整份合同拒绝加载 | `ContractError: routine_merge_agent_policy.token_scopes must equal ['write:repository']` |
| 只回退 bootstrap 闸门条件 | 正向用例被拒，测试未通过 | `BLOCKED_EXTERNAL: routine PAT scope must equal the manifest set including read:user`；恢复后该套件重新打印 `bootstrap Gitea service account tests passed` |
| 假 transport 退回无条件 200 | 见 T01 行 | T01 的 21 failures / 4 errors 正是「假 transport 不再无条件放行」之后才出现的 |

三处钉子任意一处单独回退都 fail closed，不存在只装半边还能加载的状态。

命令与输出照实抄。改动前才观测得到的证据只有写在这里才留得下来。

## 负责人执行步骤（AC-1 的授权闸门）

会话不生成、不粘贴、不读取任何 token 值；以下全部由负责人执行。顺序不能反。

1. **人工合并本 PR**（manual，`type/security` 不走 routine）。
2. **两台重装 broker**：Mac 与 gitea-ci 分别 `sudo bash codex/install-host-access-broker.sh`。
   合同进入 source 不等于生效；不重装，已安装 runtime 仍按旧的单条 scope 集合校验。
3. **重发 routine PAT**。`bootstrap-gitea-service-account.sh` 只有创建路径，没有轮换路径：
   凭据文件已存在时它返回 `no-op`，凭据缺失而 marker 还在时它直接 `BLOCKED_EXTERNAL:
   token marker exists but credential is missing; rotate explicitly`。因此顺序是
   先用 `codex/tools/rollback-gitea-routine-pilot.sh --account-policy retain` 撤销旧 PAT，
   再移除该项目的凭据文件与 token marker，最后在 gitea-ci 上重跑
   `bootstrap-gitea-service-account.sh --token-kind routine-merge-agent --project-id newemaint`
   （需要 `AISOFT_ACCOUNT_BOOTSTRAP_MODE=approved-issue-213`、`--merged-sha` 为 `213` 的 merge SHA、
   `--credential-output` 为 `projects/newemaint/routine-merge-agent.token`）。
   新 PAT 的 scope 由 manifest 派生，脚本会自己读回校验。
   **本节由源码阅读得出，会话未执行也未验证这条轮换序列**；平台目前没有一条被测试覆盖的
   routine PAT 轮换脚本，这是本次发现的衍生问题，已回报调度会话，未自立 Issue。
4. **只读复验**：`host-access-broker --project newemaint --operation host.access.audit`
   期望返回非 BLOCKED，且 `routine_merge.actual_token_scopes` 为 `["read:user", "write:repository"]`。

窗口期说明：第 2 步做完、第 3 步没做时，audit 会从 `HTTP_403` 变成 `TOKEN_SCOPE_MISMATCH`。
两者都是 BLOCKED，routine 路径全程不可用，不存在半开状态。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | **NOT RUN** | 依赖负责人合并、两台重装与重发 token，见「负责人执行步骤」。本会话没有 sudo，也不经手凭据 |
| AC-2 | 达成 | 见上面「诊断」整节；全文不含任何 token 值 |
| AC-3 | 达成 | manifest、`contract.py` 的 `_exact_string_list`、bootstrap 的 PAT 读回闸门、其 shell 测试的 mock 与断言四处同集合；后两处改为从 manifest 派生，不再手抄字符串 |
| AC-4 | 达成 | 见「反向证明」表，三处逐一回退各自 fail closed |
| AC-5 | 达成 | T01 红（21 failures / 4 errors，全部 `HTTP_403`）→ T02 绿（258 tests OK）；两次结果都在「执行结果」表里 |
| AC-6 | 达成 | `06` 踩坑 33；另在同文件凭据清单补 routine merger 一行与轮换要点一句 |
| AC-7 | 达成 | `bash codex/tests/smoke.sh` → `Ran 967 tests` / `OK` / `Codex platform static smoke checks passed.`；`python3 -m unittest tests.test_host_access tests.test_routine_merge tests.test_gitea_governance` → `Ran 258 tests` / `OK`；`check-change-documents` → `changes=143 pass=2 gap=0`；`apply-classification-labels.sh --verify 313` → `projected` |

## 遗留风险与未完成项

- 合同改完、token 未重发的窗口期内 audit 会从 `HTTP_403` 变成 `TOKEN_SCOPE_MISMATCH`；
  两者都是 BLOCKED，routine 路径全程不可用，不会出现半开状态。
- source 合并不等于 installed 生效；未经两台重装，任何 source PASS 都不得投影为 installed PASS。
- 本次不启用 routine 自动合并、不改分支保护、不执行 merge、不部署。
- **AC-1 未达成，且不可能在本会话内达成**：它需要人工合并、两台 `sudo` 重装与凭据重发，
  三件都是负责人动作。
- **衍生问题（只回报，未自立 Issue）**：平台没有一条被测试覆盖的 routine PAT 轮换路径。
  `bootstrap-gitea-service-account.sh` 只有创建路径，凭据已存在时返回 `no-op`，
  凭据缺失而 marker 还在时直接拒绝并要求「显式轮换」，而这个显式轮换没有对应工具。
- **取证受限**：会话尝试用源码 runtime 解析 routine 凭据做隔离复验，被本机权限策略以
  `Credential Exploration` 拒绝，未执行也未绕过；`prohibit_login` 与 `restricted` 两个字段
  因此没有读回，broker 也没有读任意用户账号状态的 typed 操作。
