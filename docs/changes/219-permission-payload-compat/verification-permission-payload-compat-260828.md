---
issue: 219
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/219
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - shared-core
  - platform-governance
depends_on:
  - 217
status: verified
branch: change/219-permission-payload-compat
created: 2026-08-28
updated: 2026-08-28
---

# Gitea collaborator permission payload 兼容验证记录

## 基线与范围

- Baseline SHA: `9f4595c6d997032e1b36cef47999a820fd2c9a46`（fresh main exact；#217/PR #218 merge 后基线）
- 当前 branch: `change/219-permission-payload-compat`
- 环境: macOS Codex managed worktree；source/runtime mock tests；T01 installed/source byte baseline；canonical broker
  read-only Issue/main readback；官方 Gitea v1.26.4 source；无 post-change install/live readback
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-9
- Merge policy: manual

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 完整合同读取 | PASS | `aisoft-platform`、`issue-session-flow`、`context7-mcp`、private-access、AGENTS/README/03/04/06/08/09、#213/#215/#217 四份 docs、相关 governance/host-access runtime/tests 已读 |
| fresh baseline | PASS | worktree 初始 detached HEAD exact `9f4595c6d997032e1b36cef47999a820fd2c9a46`，clean；未用旧 #217 branch 代替 main |
| source/installed bytes | PASS (baseline) / NOT RUN (post-change installed) | T01 前 `aisoft_gitea_governance/reconcile.py` 与 installed runtime、canonical 与 installed manifest 均 `cmp=0`；本实现只修改 source，未 install，未把 source PASS 推定为 installed PASS |
| canonical `host.access.audit` | GAP (expected) | sandbox transport 受限后在同一 typed operation 的 host context 重试；account/credential/target permission missing，9 个 cross-project absent/null，protection 保持 push/force denied、required context exact；read-only，mutation=0 |
| installed governance `check --repository NewEMaint` | PASS (defect reproduced) | rc=2；`BLOCKED_EXTERNAL: collaborator permission response is invalid`；只执行 GET，无 planned actions/readiness结论 |
| sanitized live permission schema | PASS (observed) | root fields exact `permission:str + role_name:str + user:object`；sample repo permission/role 均为 `admin` 且相等；nested `login`/`username` exact 匹配 requested identity并彼此相等；`is_admin` type=boolean、value=false；只保留字段名/类型/匹配布尔，无 token/credential/个人值 |
| official Gitea v1.26.4 source | PASS | `RepoCollaboratorPermission` exact 三字段；`ToUserAndPermission` 同时以 `accessMode.ToString()` 填 permission/role_name；`User` schema 与 live known fields/types一致并增加 `username` compatibility field |
| pre-fix parser review | PASS (cause identified) | governance parser要求 root exact `{"permission"}`；host-access routine/cross-project要求同形 exact-one-key，manager/project只看 `.get("permission")` 而可忽略任意 extra；两种行为均不满足有界 extended 合同 |
| Issue #219 create | PASS | canonical broker 创建 exact title；number=219；无 runtime、push、PR、install、live apply、merge 或 deploy mutation |
| lifecycle readback | PASS | 用户确认合同后 canonical broker 精确推进并读回 `approved + type/platform + complexity/complex`；fresh resume 再次读回无漂移 |
| governance TDD | FAIL before fix / PASS after fix | actual extended fixture在旧 parser稳定报 `collaborator permission response is invalid`；最小实现后 focused 2/2 与 governance full 49 tests PASS；完整 malformed/root/role/user/type/identity/site-admin矩阵 fail closed |
| host-access TDD | FAIL before fix / PASS after fix | retained 3 个公共 seam tests在旧实现产生 3 failures + 1 error；共享 bounded validator 后 manager/project/routine/cross-project 与 routine merge zero-POST focused 4/4 PASS |
| security Python suites | PASS | governance + host-access + routine-merge 共 208 tests PASS；legacy 与 actual extended variants、#217/#215 404/inventory、auth/server/transport、GET-only、apply/merge zero-mutation/zero-POST ordering均覆盖 |
| broker/bootstrap/rollback/installer shell suites | PASS | `test-host-access-broker.sh`、`test-bootstrap-gitea-service-account.sh`、`test-rollback-gitea-routine-pilot.sh`、`test-install-host-access-broker.sh` 全部 PASS |
| shell syntax/static | PASS | 上述四个相关 shell tests 的 `bash -n` 与 ShellCheck 均 rc=0、无诊断；source shell 未修改 |
| `bash codex/tests/smoke.sh` | PASS | 640 tests PASS；末行 `Codex platform static smoke checks passed.`；installer/idempotence名称均为临时 mock fixtures，不是 installed/live rollout |
| semantic mapping/check | PASS | `resolve-documents 219` 返回 exact summary/spec/plan/verification mapping；`check-change-documents` 为 `changes=99 pass=2 gap=0`；`git diff --check` PASS |
| Controller preflight | PASS | canonical readback确认 Issue open/exact labels；classification `--verify 219` 返回 `projected`；本地 `load_contract` 重算 platform/complex/restore、security/shared-core/platform-governance、branch、depends_on #217 与四份 required docs；canonical manual title/body成功渲染；`origin/main` 为 HEAD 祖先 |
| local atomic commits | PASS | T01 docs=`e64961bd37e80807659f06a692e794fed36e87ce`；approval=`1c78ed3`；governance TDD=`40a6ee2`；host-access TDD=`ea2a283`；最终 verification 另作 docs-only commit |
| push/create PR/remote CI | NOT RUN | 等待最终 PR 提交确认；未创建 remote branch、PR 或 CI run |
| install/live check/apply/#74/merge/deploy | NOT RUN | 本 Issue 明确禁止；post-change installed bytes 与 live routine state 未验证 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS (source/local) | 两个 exact root variants均接受；legacy extra、extended missing/extra与未知 top-level全部稳定 schema error |
| AC-2 | PASS (source/local) | permission/role只接受 exact string allowlist且必须相等；unknown/type/conflict矩阵 fail closed |
| AC-3 | PASS (source/local) | actual full-known-metadata fixture通过；required subset、known field allowlist及 string/integer(non-bool)/boolean exact types逐项验证 |
| AC-4 | PASS (source/local) | manifest-derived requested identity exact绑定 login/username；case-only/另一个 identity/conflict 与 is_admin true/string false均拒绝 |
| AC-5 | PASS (source/local) | governance target/cross-project与 host-access manager/project/routine/cross-project、routine merge hard gate统一执行等价合同；输出仍只持久化 permission |
| AC-6 | PASS | #217 configured routine account-missing target 404继续是唯一 governance compatibility；project/shared/unknown/cross-project/present/admin/auth/server/transport隔离与 #215 inventory路径全套回归通过 |
| AC-7 | PASS | check/audit call inventory仍为GET；schema/security失败在 evidence/PUT/PATCH/POST/DELETE 前停止；apply account/PAT/scope/non-admin/protection/order与 routine zero-POST门未放宽 |
| AC-8 | PASS | legacy、actual extended完整 metadata正向 fixtures与 malformed/root/role/user/metadata/identity/security负例覆盖；governance 49、security 208、full smoke 640全部通过 |
| AC-9 | PASS (source/local) / NOT RUN (remote/installed/live) | shell、syntax/static、full smoke、semantic/Controller preflight PASS；policy manual；push/PR/CI/install/live/apply/merge/deploy均未运行 |

## 遗留风险与未完成项

- installed governance 仍是 T01 观察到的 blocker；source 修复未 push、合并或安装，不能从本地 PASS 推定
  post-change installed/live PASS。
- remote PR/required CI尚不存在；本记录只证明 source/local gates，不能把未来 CI 写成通过。
- install、live check/apply、#74、merge 与 deploy均未运行；未来 rollout 必须钉住 exact merged SHA 并另行授权。
- 安装后真实 check 的目标仍是输出可信 `GAP/DRIFT/planned actions`，不是自动 apply 或 readiness PASS。
