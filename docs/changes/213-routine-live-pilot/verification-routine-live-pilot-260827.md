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
status: verified
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
| fresh installed broker `cmp` + operation count | PASS | 本轮重新读回：installed host-access/governance 均与 merged `8d109b14...` bytes 相等；branch host-access 仍 `cmp=0`，branch governance 因 #213 source 改动按预期不同；source/installed operations 均 31，routine operation 均 1 |
| 改动前 `host.access.audit` | GAP | protected main/required CI/manager/project-agent PASS，但 routine metadata 整段缺失；已确认是 #208 source gap，不是 installed drift |
| protected main baseline | PASS | direct push=false、force push=false、required context exact、merge allowlist=`[admin]` |
| Issue #213 creation/classification | PASS | broker 创建；最终 readback labels=`type/platform + complexity/complex + approved`；branch=`change/213-routine-live-pilot` |
| targeted Python tests | PASS | governance/host-access/routine/controller + canonical-digest compatibility suites：229 tests PASS；新增 reconcile account `is_admin` exact-bool 与 cross-project permission exact-schema 变体均在任何 apply mutation 前 fail closed，API mutation count=0 |
| bootstrap/rollback/installer shell tests | PASS | bootstrap、rollback、host-access installer、5 installers × 3 source states 均 PASS；bootstrap marker 使用含尾换行的 byte-exact `cmp`，额外换行、NUL、prefix/suffix 均 mutation count=0；rollback delete 的 unsafe password-policy marker 使 account delete/rollback call=0 |
| modified shell `bash -n` + ShellCheck | PASS | bootstrap、rollback、installer、对应 tests 与 `codex/tests/smoke.sh` 均无语法或 ShellCheck finding |
| `bash codex/tests/smoke.sh` | PASS | 第二轮修复提交后从头重跑 595 tests PASS；`Codex platform static smoke checks passed.` |
| local atomic commits | PASS | T01=`00f94c8`；T02-T03=`324a053`；T04=`db3ecc3`；T05 docs=`cfbb52d`；live authorization repair=`5484856`；repair verification=`46cd080`；review gates=`551dfce`；canonical fixture=`363bb7f`；first-review evidence=`5728dd0`；second-review variants=`f095032` |
| Controller contract preflight | PASS | fresh installed broker Issue/PR readback + local Controller resolver：Issue=213 open、labels exact、branch exact、complex、frontier=T05、policy=manual、routine ineligible、唯一 Closes/authorization marker；open matching PR=0；未写 state、未 push/create PR |
| Mac/VM install | NOT RUN | source 未合并；本任务禁止安装 live bytes |
| account/PAT bootstrap | NOT RUN | 本任务禁止 live credential/account mutation |
| collaborator/protection apply | NOT RUN | 本任务禁止 live governance mutation |
| NewEMaint Issue #74 canary | NOT RUN | 仅能在 merged source + 独立 live 授权后执行一次 |
| PAT revoke/account retain-delete rollback | PASS (source) / NOT RUN (live) | deterministic source + fake Gitea/curl/sudo tests PASS；live rollback 未授权 |
| deployment | NOT RUN | pilot 与 routine merge 均不传递部署授权 |
| push/create PR/merge | NOT RUN | 停在独立复审闸门；本轮不请求最终 PR 确认 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS (source) | exact only-NewEMaint enabled list；loader 按 canonical serialization 实时重算 non-target declarations SHA-256 并 exact compare，wrong-but-well-formed digest 被拒绝 |
| AC-2 | PASS (source) | #35/#208 ancestor calls、#213 exact Issue 与 current manifest-byte gate tests |
| AC-3 | PASS (source) | governance `routine_accounts` 三态 tests |
| AC-4 | PASS (source) / NOT RUN (live) | exact #213 binding、mutation counts、idempotent second run；所有 ownership marker 在 adopt/no-op 或 mutation 前验证 regular/non-symlink、mode 400/600、含尾换行的 exact Issue/username/token-kind bytes；额外换行、NUL、prefix/suffix 全部 fail closed 且 mutation=0 |
| AC-5 | PASS (source) | bootstrap 与每次 routine merge 前 exact `write:repository`；reconcile/account audit 的 routine identity `is_admin` 必须 `type(...) is bool` 且 exact false，missing/true/0/string/list 全部拒绝且 merge/apply mutation=0 |
| AC-6 | PASS (source) / GAP (live baseline) | enabled audit 完整 PASS/GAP fixtures；cross-project permission 使用共享 strict parser，响应只能是 exact `{permission: string}` schema；explicit read 安全，write/admin/owner 阻塞，missing/unknown/non-string/extra fields fail closed，apply mutation=0 |
| AC-7 | PASS (source) / NOT RUN (live) | pre/post snapshot、post-plan empty、operation/API mutation counts；apply 在读取 mutation credential 前要求 exact action-specific live mode |
| AC-8 | PASS (source) / NOT RUN (canary) | only Issue #74 fixture；其它 Issue stable refusal、merge POST=0 |
| AC-9 | PASS (source) / NOT RUN (live) | fixed `/api/v1/token` 204、自撤销后 401、revoke count=1 |
| AC-10 | PASS (source) / NOT RUN (live) | 底层 rollback CLI 在 credential read/client/rollback call 前要求 source disabled；delete policy 还要求 password-policy marker regular/non-symlink、mode 400/600、byte-exact；unsafe mode/content 时 account delete/rollback call=0；retain/delete fake paths完整读回 |
| AC-11 | PASS (source receipt) / NOT RUN (live layers) | source/fake mutation counts 完整；所有未授权 live layers 明确 NOT RUN |
| AC-12 | PASS (installer contract) / NOT RUN (final Mac/VM) | temp install root 两次安装、bootstrap/revoke/runtime/config source-byte cmp；最终 merged SHA 安装待后续 |
| AC-13 | PASS | complex/manual、protected main、exact context、zero deploy/zero fallback assertions |
| AC-14 | PASS | bash -n、ShellCheck、229 targeted、595 smoke、semantic audit `changes=96 pass=2 gap=0`、diff-check、Controller fresh preflight |

## 遗留风险与未完成项

- 当前 live routine account/PAT/collaborator/protection/canary 未创建或未执行，不能从 source tests 推定 live PASS。
- 本 branch 的 source 已补齐 routine audit metadata；installed broker 仍是合并前字节，只有 #213 合并并按独立授权安装后才能重新验收。
- 本任务只把 deterministic path 写入 source；所有 live mutation 必须等待 source merged 后的独立授权。
- 第一轮 2×P1/3×P2 已关闭；第二轮发现的 2×P1/2×P2 变体已在 `f095032` 修复并通过本地门禁。当前停在第三轮独立复审闸门，未经复审结论不进入用户最终 PR 确认。
