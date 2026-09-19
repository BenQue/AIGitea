---
issue: 312
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/312
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把 NewEMaint 的治理边界声明与真实分支保护重新对齐，并把 routine live pilot 的单 context 上限改成多 context 精确声明；改的是 routine merge 硬门读取的治理合同与共享 runtime，按强制规则判为 complex。
risk_flags:
  - platform-governance
  - shared-core
  - ci-integration
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-governance-context-sync-260919.md
  spec: spec-governance-context-sync-260919.md
  plan: plan-governance-context-sync-260919.md
  verification: verification-governance-context-sync-260919.md
confidence: high
override_reason: ''
depends_on: []
status: approved
branch: change/312-governance-context-sync
pr_url:
created: 2026-09-19
updated: 2026-09-19
---

## 问题/需求总结

NewEMaint #158（PR #166，merge `6f5c9b7`）给 required CI 增加了 `mobile-verify` job，负责人随后在
Gitea 分支保护把 `CI / mobile-verify (pull_request)` 加进 `status_check_contexts`。平台侧的治理
合同 `codex/config/gitea-governance.json` 没有同步，于是 broker `host.access.audit --project
newemaint` 一律返回 `BLOCKED_EXTERNAL / PROTECTION_MISMATCH`。

这是**治理边界落后于已授权的真实变更**，不是 Gitea 被篡改：分支保护现在比 manifest 声明的更严
（多一条 required context），而 audit 用的是集合相等，严也算 drift。

## 影响范围

`host.access.audit` 是若干流程的前置：routine merger 的最终 head 硬门、`aisoft-project-check.sh`
的对齐检查、project-align。这些一律 fail closed。typed 写操作（`git.push.change`、
`gitea.pull.create`）不读 audit，2026-09-19 #183 合并当日实测仍正常。

2026-09-19 本会话读回的四个受管项目 audit 现状：

| 项目 | audit | 说明 |
|---|---|---|
| `newemaint` | **BLOCKED_EXTERNAL / PROTECTION_MISMATCH** | 本 Issue 的目标 |
| `localwms` | PASS | contexts 与 manifest 一致 |
| `sfm-digital-board` | PASS | contexts 与 manifest 一致 |
| `aisoft-platform` | PASS | contexts 与 manifest 一致 |

（`myapp` 与 `smoke-test` 是 manifest 里的占位项目，无凭据绑定，返回 `CREDENTIAL_UNAVAILABLE`，
与本 Issue 无关。）

## 初步方案与建议

Issue 正文要求先只读核对 merger 硬门比较 contexts 的语义。核对结果（`codex/runtime/
aisoft_host_access/broker.py` routine merge 路径）：

- 第 6 步 live protection 比对用**集合相等**：`sorted(protection["status_check_contexts"]) !=
  sorted(repository_contract.status_check_contexts)` 即 `ROUTINE_PROTECTION_DRIFT`。
- 第 7 步最终 head 的 CI 硬门**已经要求全部 context 成功**：
  `any(by_context.get(context) != "success" for context in contexts)` 即 `ROUTINE_CI_NOT_GREEN`，
  这里的 `contexts` 就是 `repository_contract.status_check_contexts` 全表。
- `routine_live_pilot.required_context` **不被 merge 路径读取**；grep 全仓，它只出现在
  `aisoft_gitea_governance/contract.py` 的 manifest 校验里。

所以只要把 `mobile-verify` 写进 `status_check_contexts`，「两个 context 都绿才合并」就是既有行为，
mobile-verify 不会在 routine 路径下失守。**不需要**改 merger 的硬门代码。

但只加这一行会引出第二个、更严重的问题。本会话实测（scratch 副本 + `load_contract`）：

```text
ContractError routine_live_pilot requires one exact status context: NewEMaint
```

`contract.py` 在 pilot 存在时钉死 `len(status_check_contexts) == 1`，并要求
`required_context == contexts[0]`。合同加载失败不是只让 newemaint 的 audit 变红，而是让**每个项目
的每一次 broker 调用**当场炸掉。因此最小改动比原缺陷危险，必须同时改 pilot 的声明形状。

方案：把 `routine_live_pilot.required_context`（单值字符串）改成 `required_contexts`（列表），
要求与该仓的 `status_check_contexts` **逐项有序相等**，并去掉 `len(contexts) == 1`。这保留了 pilot
块「双份记账、不一致就拒绝加载」的设计意图，把 pin 从 1 条升到 N 条：以后再加第三条 required
context，也必须同时改动 pilot 声明，不能悄悄溜进去。

被否定的替代方案：直接删掉 pilot 的 `required_context`，只靠 `status_check_contexts`。它更 DRY，
但删掉的是一条 live routine-merge pilot 的审计声明，等于放宽 #213 批准过的边界，不在本 Issue 授权内。

## 风险

- **治理合同加载是全局单点**。manifest 与 `contract.py` 的这次改动必须同一个 PR，先后装反或只装一边，
  所有项目的 broker 立即 fail closed。缓解：两侧改动在同一 commit，安装后立刻对四个项目重跑 audit。
- **安装的是尚未合并的合同**。AC-1 要在合并前达成，就必须从 change worktree 安装到 Mac。回滚是从
  `origin/main` 重装（installer 幂等），证据是重装后 audit 回到 `PROTECTION_MISMATCH`。
- **踩坑编号并发撞号**。06 踩坑表当前最大号 31，本次用 32；并行会话可能同时取 32，由合并者改号。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 把 NewEMaint 的治理边界声明与真实分支保护重新对齐，并把 routine live pilot 的单 context 上限改成多 context 精确声明；改的是 routine merge 硬门读取的治理合同与共享 runtime，按强制规则判为 complex。
risk_flags:
  - platform-governance
  - shared-core
  - ci-integration
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `contract_effect=change`：`status_check_contexts` 是治理边界的对外声明，routine merger 与 audit
  都读它；pilot 的键名与形状也是 manifest schema 的一部分。两者都不是「恢复既有合同」。
- 强制 complex 规则命中三条：平台/Agent 治理（`gitea-governance.json` 与 `aisoft_gitea_governance`）、
  共享核心（合同加载被全部 broker 操作依赖）、CI 契约（required context 集合）。
- `required_docs` 含 `verification`：AC-1 的证据是真实 Gitea 上的 broker audit 读回与安装后状态，
  diff review 加 required CI 复现不了，按 `03` §3 的判据欠一份验证记录。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文已给出 AC-1～AC-4；pilot 声明形状的选择在「初步方案」里定案并写明了被否定项。
