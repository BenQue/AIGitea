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
| Issue #213 creation/classification/lifecycle | PASS | broker 创建；PR 创建后的受控 dry-run/apply/readback 将 lifecycle 从 `approved` 精确投影为 `pr-open`，保留 `type/platform + complexity/complex`；label mutation count=1 |
| targeted Python tests | PASS | governance/host-access/routine/controller + canonical-digest compatibility suites：230 tests PASS；新增 reconcile account `is_admin` exact-bool 与 cross-project permission exact-schema 变体均在任何 apply mutation 前 fail closed，API mutation count=0 |
| bootstrap/rollback/installer shell tests | PASS | bootstrap、rollback、host-access installer、5 installers × 3 source states 均 PASS；existing-account unsafe identity 矩阵保持 Gitea mutation=0；new-account 同矩阵均 PAT=0、credential/marker tree byte/mode-identical、create=1/delete=1、fresh 404，delete failure 与非 404 confirm 分别 fail closed 并给人工恢复指引；rollback immediate-pre-delete 同矩阵 delete=0 |
| modified shell `bash -n` + ShellCheck | PASS | bootstrap tool/test 在 CI repair head `9964165` 上均无语法或 ShellCheck finding |
| Linux runner-compatible bootstrap regression | PASS | `node:22-bookworm-slim` Linux 容器只读挂载 exact source；补齐 CI 已具备的 git/jq/python3/shasum 后，修复前 trace 在旧 config-preflight count 断言失败，修复后 exact bootstrap test PASS；未授权请求的 Gitea/PAT/curl/config-preflight 与 credential tree 均保持 0/byte-identical |
| `bash codex/tests/smoke.sh` | PASS | CI repair 提交 `9964165` 后从头重跑 595 tests PASS；`Codex platform static smoke checks passed.` |
| local atomic commits | PASS | T01=`00f94c8`；T02-T03=`324a053`；T04=`db3ecc3`；T05 docs=`cfbb52d`；live authorization repair=`5484856`；repair verification=`46cd080`；review gates=`551dfce`；canonical fixture=`363bb7f`；first-review evidence=`5728dd0`；second-review variants=`f095032`；second-review evidence=`f07e250`；third-review identity gates=`86d029a`；third-review evidence=`c7d30d5`；fourth-review compensation/TOCTOU=`c0558f0`；PR lifecycle/URL backfill=`e37d941`；CI authorization-order repair=`9964165` |
| Controller contract/readback | PASS | fresh broker readback：Issue #213 open、labels exact `pr-open + complexity/complex + type/platform`；PR #214 唯一、open/unmerged、head branch/base/manual markers exact；summary `status=pr-open` 且 `pr_url` 指向 PR #214；routine ineligible，merge POST=0 |
| PR CI evidence | FAIL / repair pending review | run #758/job #758 在 head `cb9141e...` 的 `Platform smoke suite` 于 repository-settings PASS 后、bootstrap PASS 前退出 1；Linux trace 定位旧 authorization ordering 触发 config-preflight count 漂移。summary 回填 head `e37d941...` 的 run #759/job #759 在下载 `actions/checkout@v4` 时 `EOF`，两步均 cancelled，属于外部 runner/network failure。修复 head `9964165...` 尚未 push，等待独立增量复审 |
| Mac/VM install | NOT RUN | source 未合并；本任务禁止安装 live bytes |
| account/PAT bootstrap | NOT RUN | 本任务禁止 live credential/account mutation |
| collaborator/protection apply | NOT RUN | 本任务禁止 live governance mutation |
| NewEMaint Issue #74 canary | NOT RUN | 仅能在 merged source + 独立 live 授权后执行一次 |
| PAT revoke/account retain-delete rollback | PASS (source) / NOT RUN (live) | deterministic source + fake Gitea/curl/sudo tests PASS；live rollback 未授权 |
| deployment | NOT RUN | pilot 与 routine merge 均不传递部署授权 |
| push/create PR/merge | PASS / PASS / NOT RUN | 唯一 PR #214 已创建；初始 branch push=1、Controller summary 回填 push=1，未创建第二 PR；CI repair head 尚未 push；complex/manual merge POST=0 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS (source) | exact only-NewEMaint enabled list；loader 按 canonical serialization 实时重算 non-target declarations SHA-256 并 exact compare，wrong-but-well-formed digest 被拒绝 |
| AC-2 | PASS (source) | #35/#208 ancestor calls、#213 exact Issue 与 current manifest-byte gate tests |
| AC-3 | PASS (source) | governance `routine_accounts` 三态 tests |
| AC-4 | PASS (source) / NOT RUN (live) | exact #213 binding、marker byte/mode 与幂等矩阵通过；existing-account unsafe identity 保持 mutation=0；404 后刚创建账户的 unsafe readback 不能预先为零 mutation，现由 exact username 补偿事务如实执行 create=1/delete=1 并 fresh 确认 404，net-state unchanged；补偿失败停止并给人工恢复指引 |
| AC-5 | PASS (source) | bootstrap 在任何 PAT/credential/marker mutation 前用 `jq -e` 要求 identity root object、exact login、`is_admin` boolean 且 false；unsafe 新账户矩阵 PAT=0、credential/marker tree byte-identical，但明确记录补偿 create/delete，不再伪称 Gitea mutation=0；routine merge/reconcile 仍保持零 POST/apply mutation |
| AC-6 | PASS (source) / GAP (live baseline) | enabled audit 完整 PASS/GAP fixtures；cross-project permission 使用共享 strict parser，响应只能是 exact `{permission: string}` schema；explicit read 安全，write/admin/owner 阻塞，missing/unknown/non-string/extra fields fail closed，apply mutation=0 |
| AC-7 | PASS (source) / NOT RUN (live) | pre/post snapshot、post-plan empty、operation/API mutation counts；apply 在读取 mutation credential 前要求 exact action-specific live mode |
| AC-8 | PASS (source) / NOT RUN (canary) | only Issue #74 fixture；其它 Issue stable refusal、merge POST=0 |
| AC-9 | PASS (source) / NOT RUN (live) | fixed `/api/v1/token` 204、自撤销后 401、revoke count=1 |
| AC-10 | PASS (source) / NOT RUN (live) | rollback preflight unsafe identity 仍在 repository rollback 前零 mutation；delete 路径在 safe preflight → repository rollback=1 → PAT revoke=1 后，对新的临时文件执行 fresh GET + strict identity，再紧邻 fixed delete；immediate unsafe 矩阵 account delete=0 且如实保留已发生 rollback/revoke 计数。Gitea 无 conditional delete，GET-delete 之间仍有不可消除但已最小化的残余竞态 |
| AC-11 | PASS (source receipt) / NOT RUN (live layers) | source/fake mutation counts 完整；所有未授权 live layers 明确 NOT RUN |
| AC-12 | PASS (installer contract) / NOT RUN (final Mac/VM) | temp install root 两次安装、bootstrap/revoke/runtime/config source-byte cmp；最终 merged SHA 安装待后续 |
| AC-13 | PASS | complex/manual、protected main、exact context、zero deploy/zero fallback assertions |
| AC-14 | PASS (local) / FAIL (remote CI) | bash -n、ShellCheck、230 targeted、595 smoke、Linux bootstrap regression、semantic audit `changes=96 pass=2 gap=0`、diff-check、Controller/broker fresh readback 均 PASS；远端 required context 尚未 green，修复 head 等待独立增量复审后才能 push |

## 遗留风险与未完成项

- 当前 live routine account/PAT/collaborator/protection/canary 未创建或未执行，不能从 source tests 推定 live PASS。
- 本 branch 的 source 已补齐 routine audit metadata；installed broker 仍是合并前字节，只有 #213 合并并按独立授权安装后才能重新验收。
- 本任务只把 deterministic path 写入 source；所有 live mutation 必须等待 source merged 后的独立授权。
- 前四轮 findings 已关闭。PR CI 暴露的 authorization ordering 回归已在 `9964165` 最小修复并通过 macOS/Linux 本地门禁；该修复改变安全检查顺序（把 Gitea config preflight 恢复到 exact mode gate 之后），因此按合同停在独立增量复审，未经结论不 push repair head。
