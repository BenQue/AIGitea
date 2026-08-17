---
issue: 126
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/126
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - cross-module
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on:
  - 120
  - 124
status: pr-open
branch: change/126-gitea-parallel-replacement
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/127
created: 2026-08-17
updated: 2026-08-17
---

# Verification：greenfield systemd Gitea 并行替换

## 环境与版本

- Baseline：`fbc17787bc0f3cafa4113349d6190b936311ebc3`（protected `origin/main`）。
- Approved contract：`9af72f626bb1f3c58669dc4b6a376407429c7045`；最终实现树中的 mapped spec/plan
  与该提交逐字一致。
- Implementation candidate：`c0ec15db16f9fada87b52ed52cf22462c7758ac5`，验证时 worktree clean。
- Operator source version：`1.1.0`。
- PR：`#127`，创建后 readback 为 open、mergeable、unmerged；body 恰有一行 `Closes #126` 且只链接 mapped
  summary 一次。最终 head 在本 projection commit push 后由 typed broker 回读并记录到 Issue 评论，避免形成
  自引用 SHA 循环。
- Environment：Mac isolated worktree + fake runner/HTTP/port/path/release fixtures only。
- 公司 `scm-ci`、`appserver-prod` 与所有 live Gitea/PostgreSQL/service/network/repository：`NOT RUN`。

## Ticket 执行记录

| Ticket | Result | Atomic commit / evidence |
|---|---|---|
| T01 | PASS | inventory v2、transition v1 contracts/schema/templates；RED 后 GREEN；`2e91a14a46d0ae8d5becd04d4f445670553a6562` |
| T02 | PASS | fixed Docker/loopback/collision/resource probes；RED 后 GREEN；`a35443e5d497708e255cc8e45da309d89c4acbf9` |
| T03 | PASS | transition/handoff/package/inventory binding、legacy pre/post equality 与 CLI；RED 后 GREEN；`507ea65bd02a7e1c36bcfbb5701db399bd1cf4b3` |
| T04 | PASS | compatibility、Stage 10–50 runbook、authority docs 与 operator `1.1.0`；RED 后 GREEN；`f3ae92a7377eeb386254ac7a703af04a9e197e8f` |
| T05 | PARTIAL（final-head readback 待执行） | 审阅回归 `a553e7e61111d526d75039f0ffdd5eced66e7b76`；package-manifest 完整性与治理收口 `c0ec15db16f9fada87b52ed52cf22462c7758ac5`；唯一 PR #127 已创建 |

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| focused company-delivery tests | PASS | final `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery`：74 tests OK；contract/collector focused：39 tests OK |
| full runtime unittest discovery | PASS | exact clean `c0ec15d...`：435 tests OK |
| platform smoke | PASS | `bash codex/tests/smoke.sh` exit 0；结尾 `Codex platform static smoke checks passed`，内含 435 tests OK |
| JSON / bash / ShellCheck / diff gates | PASS | 全部 `company-delivery/**/*.json` 通过 parser；wrapper `bash -n` 与 `/opt/homebrew/bin/shellcheck` PASS；`git diff --check origin/main...HEAD` PASS |
| mapped document resolver | PASS | `resolve-documents 126` 精确返回本 Change 的 summary/spec/plan/verification 四个 basename |
| deterministic 1.1.0 fake bundle x2 | PASS（local fake only） | clean `c0ec15d...` 两次 archive bytes 相同；archive `aisoft-company-delivery-1.1.0-c0ec15db16f9fada87b52ed52cf22462c7758ac5.tar.gz`；SHA-256 `87592b51ee8b3688ea89b868e351f32cf4a1a625d2ff2243564903506bf42c2c` |
| handoff / payload readback | PASS（local fake only） | 两个原目录与一次解包后验证均 `ok=true`、`docker_calls=0`、`target_facts=NOT_READ`；transition schema/template 均在 payload 中 |
| tamper/no-secret/security negatives | PASS | builder 的结构化 no-secret scan 与静态 scan PASS；修改第二份 `operator/VERSION` 后 verifier exit 2，固定 `CHECKSUM_MISMATCH`，无输入回显 |
| package manifest fail-closed | PASS | RED 为 1 test 的 4 个 subtest failures；GREEN 拒绝 empty、malformed、duplicate、unsorted、`../`，并绑定 mode `0600` protected file digest |
| approved contract immutability | PASS | mapped spec/plan 与 approval commit `9af72f6...` 执行 `git diff --exit-code` 无差异 |
| Standards review | PASS | 第三轮 exact `c0ec15d...`：0 hard violations、0 judgement calls |
| Spec review | PASS | 第三轮 exact `c0ec15d...`：0 findings；前三项 package/handoff/schema findings 全部关闭 |
| protected main / PR / exact head / CI readback | PARTIAL | PR #127 初次 readback：head `0737f25d7d95601cdd6e9a4fa668b15d4976d911`、base `fbc17787bc0f3cafa4113349d6190b936311ebc3`、open/mergeable/unmerged；最终 projection head、protection、required CI 与 Actions 待 push 后回读 |

## Acceptance criteria 结果

| AC | Result | Evidence |
|---|---|---|
| AC-1 Inventory v2 | PASS | v1 historical reader + v2 role/mode/scm runtime/schema parity；Docker-only legacy 不再投影为 absent |
| AC-2 Probe safety | PASS | fixed argv、loopback-only、bounded/no-echo negatives；无 `docker inspect`、env/config/log/raw output surface |
| AC-3 Transition state machine | PASS | two inventory、1.1.0 handoff/source、package manifest、exact stage map 与 tamper/role/collision negatives |
| AC-4 Fixed target identity | PASS | runtime/compatibility/schema/docs 锁定 Gitea/PostgreSQL version/checksum、namespace、paths、units 与 loopback ports |
| AC-5 Legacy invariant | PASS | pre/post presence/health/version/canonical baseline equality 与 drift negatives |
| AC-6 Initial isolation | PASS | SSH、Runner、timer、Actions auto deploy、production gate disabled；DNS/TLS/proxy/import 为 `NOT RUN` |
| AC-7 Portable operator | PASS（local fake） | `1.1.0` 双构建逐字一致、三次 handoff verify、payload/tamper/no-secret PASS；不是 company Stage 00 |
| AC-8 Runbook | PASS | Stage 10–50 greenfield/controlled-upgrade fork、stop point、evidence 与 rollback allowlist 静态/人工复核通过 |
| AC-9 Validation | PASS | focused 74、full 435、smoke、JSON、bash、ShellCheck、diff 与双轴 review 全部 PASS |
| AC-10 Governed delivery | PARTIAL | 唯一 PR #127 与 exact body 已读回；最终 projection head/protection/CI 将在 push 后写入 Issue audit comment；merge 始终不授权 |
| AC-11 Execution boundary | PASS | 公司 1.1.0 Stage 00、Stage 10/20/30/40/50 与全部 live mutation 均保持 `NOT RUN` |

## 重复部署

- Local fake deterministic bundle 第一次：`PASS`（制品验证，不是部署）。
- Local fake deterministic bundle 第二次：`PASS`（bytes/checksum 相同，不是部署）。
- 公司新 Gitea 第一次安装：`NOT RUN`。
- 公司同版本重复安装/验收：`NOT RUN`。

## 故意失败与回滚

- Local fake malformed Docker ID、multiple IDs、unhealthy legacy、candidate collision、inventory/transition tamper、
  skipped-stage fake PASS、baseline drift、invalid package manifest 和 Secret sentinel：`PASS`（均 fail closed）。
- handoff source/version/package drift 与 bundle payload tamper：`PASS`（固定错误 code、no-echo）。
- 公司新实例失败与只隔离新 namespace 的回滚：`NOT RUN`。
- legacy Docker Gitea rollback/mutation：不在本 Change 授权范围，固定 `NOT RUN`。
- database restore/delete、DNS/TLS/repo migration/phase-out：`NOT RUN`。

## Company/live 状态矩阵

| Scope / Stage | Result | 边界 |
|---|---|---|
| 历史 operator `1.0.1` Stage 00 | historical evidence only | 不投影为 `1.1.0` PASS |
| operator `1.1.0` company Stage 00 | NOT RUN | local fake bundle 不生成 Stage evidence |
| Stage 10 `scm-ci` / `appserver-prod` inventory | NOT RUN | 未连接公司内网或读取 host facts |
| Stage 20 cross-host transition decision | NOT RUN | 无真实 package manifest、public-name fingerprint 或 reviewer receipt |
| Stage 30 backup | NOT RUN | greenfield 必须继续 NOT RUN；controlled upgrade 未获批 |
| Stage 40 isolated restore | NOT RUN | greenfield 必须继续 NOT RUN；controlled upgrade 未获批 |
| Stage 50 install/health/legacy equality | NOT RUN | 未安装 Gitea/PostgreSQL，未操作 service/database/network/repository |
| merge / deploy / DNS/TLS / migration / retirement | NOT RUN | AI 无授权，最终 PR 为人工合并硬闸门 |

## 遗留风险与未完成项

- 公司 Stage 10 尚未运行，真实 OS/package manifest、legacy loopback port、capacity/collision 与 public-name
  fingerprint 尚无 evidence；在此之前 Stage 20/50 不能获批。
- PR #127 已建立；final-head/protected-main/required-CI/Actions readback 尚待本 projection commit push 后由 typed
  broker 完成并写入 Issue audit comment；AI 不合并。
- 本文只记录本地 source/test/bundle 与 PR evidence；不得把它改写为公司安装、升级或切流量成功。
