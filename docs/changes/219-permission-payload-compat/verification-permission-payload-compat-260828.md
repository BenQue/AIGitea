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
status: pending
branch: change/219-permission-payload-compat
created: 2026-08-28
updated: 2026-08-28
---

# Gitea collaborator permission payload 兼容验证记录

## 基线与范围

- Baseline SHA: `9f4595c6d997032e1b36cef47999a820fd2c9a46`（fresh main exact；#217/PR #218 merge 后基线）
- 当前 branch: `change/219-permission-payload-compat`
- 环境: macOS Codex managed worktree；installed/source byte readback；canonical broker 与 installed governance
  read-only GET；官方 Gitea v1.26.4 source；本阶段只写 docs
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-9
- Merge policy: manual

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 完整合同读取 | PASS | `aisoft-platform`、`issue-session-flow`、`context7-mcp`、private-access、AGENTS/README/03/04/06/08/09、#213/#215/#217 四份 docs、相关 governance/host-access runtime/tests 已读 |
| fresh baseline | PASS | worktree 初始 detached HEAD exact `9f4595c6d997032e1b36cef47999a820fd2c9a46`，clean；未用旧 #217 branch 代替 main |
| source/installed bytes | PASS | `aisoft_gitea_governance/reconcile.py` 与 installed runtime `cmp=0`；canonical 与 installed `gitea-governance.json` `cmp=0` |
| canonical `host.access.audit` | GAP (expected) | sandbox transport 受限后在同一 typed operation 的 host context 重试；account/credential/target permission missing，9 个 cross-project absent/null，protection 保持 push/force denied、required context exact；read-only，mutation=0 |
| installed governance `check --repository NewEMaint` | PASS (defect reproduced) | rc=2；`BLOCKED_EXTERNAL: collaborator permission response is invalid`；只执行 GET，无 planned actions/readiness结论 |
| sanitized live permission schema | PASS (observed) | root fields exact `permission:str + role_name:str + user:object`；sample repo permission/role 均为 `admin` 且相等；nested `login`/`username` exact 匹配 requested identity并彼此相等；`is_admin` type=boolean、value=false；只保留字段名/类型/匹配布尔，无 token/credential/个人值 |
| official Gitea v1.26.4 source | PASS | `RepoCollaboratorPermission` exact 三字段；`ToUserAndPermission` 同时以 `accessMode.ToString()` 填 permission/role_name；`User` schema 与 live known fields/types一致并增加 `username` compatibility field |
| current parser review | PASS (cause identified) | governance `_strict_collaborator_permission` 要求 root key set exact `{"permission"}`；#217 tests 把 extra field 固定为 invalid；host-access routine/cross-project surface也存在同形 exact-one-key parser，future account-present 会受影响 |
| Issue #219 create | PASS | canonical broker 创建 exact title；number=219；无 runtime、push、PR、install、live apply、merge 或 deploy mutation |
| semantic mapping/check | PASS | `resolve-documents 219` 返回 exact summary/spec/plan/verification mapping；`check-change-documents` 为 `changes=99 pass=2 gap=0`；`git diff --check` PASS |
| T01 docs commit | PASS (prepared) | 本四文件集是唯一 T01 docs commit；exact commit SHA 在会话 handoff 中读回，提交不包含 runtime/tests |
| runtime/tests implementation | NOT RUN | 必须等待用户明确合同/启动确认 |
| install/live check/apply/#74/merge/deploy | NOT RUN | 本 Issue 当前阶段禁止 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | CONTRACT READY / implementation NOT RUN | legacy 与 extended 两个 exact root variant 已固定；未知 top-level fail closed |
| AC-2 | CONTRACT READY / implementation NOT RUN | permission/role exact string allowlist 与 equality 已固定 |
| AC-3 | CONTRACT READY / implementation NOT RUN | Gitea 1.26.4 known nested allowlist、required subset与逐字段类型已固定 |
| AC-4 | CONTRACT READY / implementation NOT RUN | login/username/requested identity exact binding与 is_admin exact false 已固定 |
| AC-5 | CONTRACT READY / implementation NOT RUN | governance/host-access 全 permission surfaces 与 manifest-derived caller identity 已纳入 |
| AC-6 | CONTRACT READY / implementation NOT RUN | #217 target missing 404 唯一兼容路径及其它错误隔离已固定 |
| AC-7 | CONTRACT READY / implementation NOT RUN | check/audit GET-only、apply/account/PAT/scope/protection/order门禁不放宽 |
| AC-8 | CONTRACT READY / implementation NOT RUN | actual+legacy正向与完整 malformed/security/ordering matrix 已定义 |
| AC-9 | CONTRACT READY / implementation NOT RUN | source/installed/live/CI/install/apply/merge/deploy 分层与 manual policy 已定义 |

## 遗留风险与未完成项

- 当前 installed governance 仍是 blocker；本阶段只完成合同，不能把 docs 或 live schema观察写成 runtime 修复。
- `host.access.audit` 当前可读是因为 routine account missing 走 #215 inventory；account present 后同形 extended payload
  仍需 T02-T04 覆盖，不能从当前 GAP 推定未来 PASS。
- remote PR/required CI、runtime tests、install 与 live readback均未运行；用户确认合同前不得开始。
- live rollout 即使未来 parser 可读，仍应输出 account/PAT/apply 未完成的可信 GAP/planned actions，不得自动 apply。
