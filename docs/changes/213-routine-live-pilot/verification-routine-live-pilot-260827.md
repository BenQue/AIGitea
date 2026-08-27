---
issue: 213
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/213
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - security
  - shared-core
  - ci
  - rollback
  - agent-governance
  - platform-governance
depends_on:
  - 35
  - 208
status: pending
branch: change/213-routine-live-pilot
created: 2026-08-27
updated: 2026-08-27
---

# 单仓 routine auto-merge live pilot 验证记录

## 基线与范围

- Commit SHA: `8d109b14b6e0936be30f6f287ff6050e48632e0b`（实施前 exact source baseline）
- 基线：fresh fetch 后 `origin/main` = `8d109b14b6e0936be30f6f287ff6050e48632e0b`，即 #208/PR #212 merge
- Issue #35 baseline: `69251fd4d07665385eb6d9142038848c2b9392d7`
- 环境: macOS Codex isolated linked worktree；source/installed/read-only live probes；implementation tests 使用 fake transport/temp roots
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-14

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `git fetch origin --prune` + ancestry/readback | PASS | `origin/main=8d109b14...`；#208 exact merge 是当前 main；Issue #35 merge 为其祖先 |
| source/installed broker manifest `cmp` + operation count | PASS | 两份 host-access 与 governance manifests `cmp=0`；source/installed operations 均 31，routine operation 均 1 |
| 改动前 `host.access.audit` | GAP | protected main/required CI/manager/project-agent PASS，但 routine metadata 整段缺失；已确认是 #208 source gap，不是 installed drift |
| protected main baseline | PASS | direct push=false、force push=false、required context exact、merge allowlist=`[admin]` |
| Issue #213 creation/classification | PASS | broker 创建；labels=`type/platform + complexity/complex + spec-drafting`；branch=`change/213-routine-live-pilot` |
| implementation/tests | NOT RUN | 待 T02-T05 完成后填写 |
| Mac/VM install | NOT RUN | source 未合并；本任务禁止安装 live bytes |
| account/PAT bootstrap | NOT RUN | 本任务禁止 live credential/account mutation |
| collaborator/protection apply | NOT RUN | 本任务禁止 live governance mutation |
| NewEMaint Issue #74 canary | NOT RUN | 仅能在 merged source + 独立 live 授权后执行一次 |
| PAT revoke/account retain-delete rollback | NOT RUN | source path 将用 fake tests 验证；live rollback 未授权 |
| deployment | NOT RUN | pilot 与 routine merge 均不传递部署授权 |
| push/create PR/merge | NOT RUN | 停在最终 PR 前确认闸门 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待验证 | T02 manifest/diff tests |
| AC-2 | 待验证 | T02 provenance tests |
| AC-3 | 待验证 | T02 governance account-state tests |
| AC-4 | 待验证 | T04 bootstrap tests |
| AC-5 | 待验证 | T03/T04 exact-scope tests |
| AC-6 | 待验证 | T03 host audit tests |
| AC-7 | 待验证 | T02 apply/readback tests |
| AC-8 | 待验证 | T03 canary/zero-POST tests |
| AC-9 | 待验证 | T04 revoke tests |
| AC-10 | 待验证 | T04 retain/delete tests |
| AC-11 | 待验证 | T05 layered receipt review |
| AC-12 | 待验证 | T04 installer byte parity tests |
| AC-13 | 待验证 | manifest/protection/manual/deploy boundary tests |
| AC-14 | 待验证 | T05 full validation and controller preflight |

## 遗留风险与未完成项

- 当前 live routine account/PAT/collaborator/protection/canary 全部不存在或未读回，不能从 source 计划推定 PASS。
- 当前 `host.access.audit` 的 routine metadata 缺失是已复现 source GAP，修复前不能作为 pilot acceptance。
- 本任务只把 deterministic path 写入 source；所有 live mutation 必须等待 source merged 后的独立授权。
