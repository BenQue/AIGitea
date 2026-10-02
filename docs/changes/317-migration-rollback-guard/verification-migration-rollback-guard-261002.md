---
issue: 317
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/317
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - data-migration
  - external-contract
  - shared-core
  - rollback
  - security
  - platform-governance
depends_on: []
status: verified
branch: change/317-migration-rollback-guard
created: 2026-10-02
updated: 2026-10-03
---

## 当前本地结项（2026-10-03）

T01–T05 本地工作全部完成。最新组合 base `16beee09aefe89b5bc80a31544c59d456190ea32` / source `ed37445c9986fbff2aaac747ad41457da2a622ef`
在默认 `C.UTF-8`、native Bash 3.2 下执行 `bash codex/tests/smoke.sh`，真实 exit=0：
1057 runtime tests、197 release tests、23 installed-drift 临时 fixture，registry 步骤 PASS。
26 boundary regression 已包含在最新全量 runtime 中；Standards 0硬违反/0 heuristic，Spec 0 findings。

当前 AC-01–13 为 source/local PASS（AC-10 仅 consumer 文档）；验证回执
`evidence/t05-final-validation.json`、完整日志和 `evidence/review-final-main289.md` 保留 exact SHA。
上游 #288/#319/#289 已人工合并并整合，未应用本票的未批准 fixture 提案。旧 FAIL、
sandbox 路径阻塞和 C-only PASS 记录保持原结论；下方旧阶段的 pending/阻塞均是当时历史状态。

当前 local handoff 为 `PR_SUBMISSION_APPROVED`，不是 Controller 状态投影。唯一 branch
`change/317-migration-rollback-guard` 尚未首次发布；2026-10-03 用户直接“确认提交”，已取得 manual 最终提交授权，receipt 为 `evidence/pr-submission-confirmation.json`。
PR CI、真实 Docker/DB、installed/live 与 NewEMaint #229 消费验收仍 `NOT RUN`；#229 pin 未改。
最终 PR 草稿与确认边界见 `evidence/final-pr-candidate.md`。

# 当前验证与证据边界

## 基线与范围

- 本票起始 authoritative origin/main：`5c2cd726c9aeaee9d17541d8feb049e33881bbac`；2026-10-02 经 project=aisoft-platform broker fetch。
- Session：`01a0fc7b-9d82-75e2-975f-d407cd23e34a`；exact worktree `/private/tmp/issue-317-migration-rollback-guard` 已 claim。
- 当前合同已批准，T01 独立停止后 fresh run 已实施 T02/T03。下节保存批准前历史观测，不代表当前授权、实现或标签状态。

## 批准前基线执行结果（历史）

| Command / check | Result | Evidence |
|---|---|---|
| broker gitea.issue.read #317 + comments.read | PASS | open、needs-analysis；正文记录批准1,2；评论=[] |
| broker host.onboarding.check | PASS | exact project-agent write；main 不可 push/force；admin-only merge；required CI=CI / verify (pull_request)；routine disabled |
| branch/history/docs/PR 去重 | PASS | 无 #317 既有 branch/docs/history；broker pulls.read all 的 #317 filter=[] |
| worktree add / claim | PASS | fresh authoritative main；branch tuple；真实 session owner |
| `PYTHONPATH=codex/runtime python3 docs/changes/317-migration-rollback-guard/evidence/reproduce-baseline.py` | BUG CONFIRMED | baseline-reproduction.json；3/3入口无依据旧镜像 up=1 |
| semantic analyzer normalization / document check | PASS | validate-analysis 成功；resolve-documents 精确四角色；check-change-documents changes=145 pass=2 gap=0 |
| classification plan | PASS | 从映射 summary 得到 bugfix/complex，仅计划 |
| live classification --apply | BLOCKED | 自动审批拒绝，未执行写入；理由为合同启动确认尚未取得 |
| live classification --verify | GAP | 两维 projection-missing；不伪造 projected |
| runtime 修复/新回归测试/完整 smoke | NOT RUN | 合同未批准，未修改 runtime |
| PR CI | NOT RUN | 未 push/PR |
| installed/live Docker/DB/公司现场 | NOT RUN | 未获得此范围授权 |

`reproduce-baseline.py` 只调用 repository FakeDocker 和临时 fixture，无真实 Docker subprocess。
其中 database_restore_calls=0 表示本 baseline adapter 没有 restore 调用；不代表真实 DB 验收。
该脚本绑定上列 baseline，在修复后运行当前 source 预期结论改变，不能重写本 baseline evidence。

## Acceptance criteria 结果

| AC | 当前结果 | 可复核证据 |
|---|---|---|
| AC-01 | PASS | phased activation 不同 migration 时 ROLLBACK_BLOCKED，旧 up=0，保留数据库位置 |
| AC-02 | PASS | legacy v1/v2 deploy 失败均拒绝无依据自动回退 |
| AC-03 | PASS | operator 文件 strict shape、双 manifest hash、target binding、UTC expiry、权限/路径、限量、open/fstat 与替换中读取测试 |
| AC-04 | PASS | known same identity proof；不同/null/untracked 需 exact evidence；uncertain/started/failed 固定拒绝 |
| AC-05 | PASS | #305 同 identity completed no-op 和审计 receipt.release_id 保持 |
| AC-06 | PASS | A/B 共用 A 而 C 已迁移时拒绝回退；noop 不伪造 DB cursor |
| AC-07 | PASS | v1/v2 合法读升级 untracked、不写原 bytes；v3 非法 generation/identity/fields 拒绝；旧 schema 未改 |
| AC-08 | PASS | 四类入口、固定 evidence gate 与最新默认 UTF-8 完整 smoke 1057 tests；t05-final-validation.json |
| AC-09 | PASS | CLI failed exit=2、稳定安全 code/message；没有 override/bypass 参数、无路径/fixture secret/Docker error 回显 |
| AC-10 | PASS (local docs) | README、versioned contract、过期合成 example 和 merged-pin 边界；应用采用/现场验收 NOT RUN |
| AC-11 | PASS | exact 8 existing pins / 5 additions；历史 baseline/constants/evidence 保持；最新 checker receipt |
| AC-12 | PASS | 26 boundary tests；disk/index bytes/mode/unknown/missing/rename/symlink/staged-only 拒绝 |
| AC-13 | PASS (source/local) | latest checker 197 release、完整 UTF-8 smoke、两轴0 findings；CI/real-E2E/installed/live NOT RUN |

190-test为T02历史source/fixture验收；当前T05为197-test，完整smoke与未完成项以下方最新回执为准。


## 授权、遗留风险与未完成项

2026-09-21 平台先行方向保留；本票首次具体的 profile/evidence/state/security 合同已获2026-10-02 用户直接批准；授权证据见 evidence/contract-start-approval.json。
依赖：#317 depends_on=[]；NewEMaint #229 被本票阻塞。
runtime/schema/test 和本地 consumer 文档已实施。完整 smoke/审查已本地通过；最终候选仍须最终 PR 提交确认与人工 merge；不能提供新的 merged SHA 或宣称解除 #229 前置。

## T01 独立治理合同步骤（2026-10-02）

- 用户本会话直接回复“批准”；绑定原 reviewed head `abc1adfffe6fcdc3b6053695050a5a83fd3e4830` 的 spec/plan 和 manual policy；无最终 PR、merge、install、deploy 权限。
- Fresh authoritative main 仍为 `5c2cd726c9aeaee9d17541d8feb049e33881bbac`；工作区 ownership/clean 读回正确，未修改共享 main。
- 已应用 Docker release README 与 versioned `docker-release/contracts/migration-rollback-v1.md`；README 明确当前 runtime 仍为基线，不虚报 guard 已生效。
- spec AC 表转换为现有 loader 可读的 checklist、plan 逐项 AC 映射展开，内容和验收范围保持。
- 本阶段只运行文档/纯合同检查；未启动 Controller，未实施 runtime/schema/test，也未运行 Docker/DB。

| Check | Result | Evidence |
|---|---|---|
| 合同启动授权 | PASS | direct user “批准”；contract-start-approval.json |
| 仅 #317 classification --apply | PASS | bugfix/complex updated |
| 独立 classification --verify | PASS | 两维 result=projected |
| approved lifecycle 投影 | PASS | before needs-analysis → after approved；保留 type/complexity |
| pure load_contract + frontier | PASS | CONTRACT_VALID；criteria_count=10；frontier=T01 |
| 文档与 pr_url 检查 | PASS | changes=145 pass=2 gap=0 |
| Matt triage/category 状态投影 | GAP | 当前 broker 无 triage typed write；extension 明确禁止 managed prefix，未绕过 |
| T01 Standards / Spec 独立 review | PASS | 两轴发现1+2项文档问题；95ff8f3修复，原reviewer复核均通过；evidence/review-t01.md |
| runtime、release suite、smoke、CI、installed/live | NOT RUN | T01 文档步骤，本阶段不宣称功能通过 |

T01 完成后停止。下一条 fresh run 重读当前 AGENTS/README、已批准 spec/plan、新治理合同和 claim，再沿用已有批准实施 T02/T03；不额外申请合同启动批准。

### T01 完成证据

`7de1cc2` 应用独立治理合同；`95ff8f3` 修复 review 表达缺口。原 Standards/Spec reviewer 复核均通过。
当前 T01=completed，T02/T03=pending；本运行到此停止，未调用 runtime/Controller/Docker/DB。
远端合同批准评论已由 broker 发布：`http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/317#issuecomment-12027`。
Matt triage typed 写缺口保持 GAP，本票允许范围不含broker修复；核心contract loader不依赖该维度。

## T02/T03 fresh run（2026-10-02）

- 用户继续指令沿用完整批准；fresh run 重读合同/单写者 claim 后实施，未改共享 main。
- 先添加 public-interface 回归并观察失败：缺 database_revision；不同 migration 健康失败时返回旧代码并启动旧镜像；中断后其它 migration 可运行；legacy/恢复路径仍无 guard。分别实现后转绿。
- Evidence reader 固定 256 KiB/128 records，directory FD + O_NOFOLLOW/open/fstat 验证同一 inode；安全消息不拼接路径或 untrusted 内容。Operator immediate parent 必须非 group/world writable 且 owner 为 profile owner/root；root-owned sticky system-temp 仅作为祖先 traversal anchor，不能作为 operator parent。
- 同 identity lane 使用 actual DB cursor + completed ledger，不以 receipt.release_id 作限制；显式 evidence fingerprint 不含 current/previous/last_result/env。
- README 的教学 example 已过期且为合成 hash，未 provision live profile、依据或 grant。
- `evidence/release-suite.json`：完整 release suite 190 tests PASS。
- `evidence/platform-smoke.json`：FAIL，exit=1；`check-release-evidence-boundary.py` 报 current file set differs from the fixed baseline。不能写成 PASS。
- classification --verify 已经 broker host 路径读回真实 projected（bugfix/complex）；初次 sandbox state-unreadable 是执行路径失败，未据此改判级或绕过 broker。
- 两轴审查及 P1 修复复核完成；详见 `evidence/review-t02-t03.md`，无未解决 source finding。
- PR CI、installed/live Docker/DB、NewEMaint #229 消费验收、安装、部署：NOT RUN。

## 新发现的合同范围冲突

完整 smoke 的固定检查器保留 #65/#290 历史 baseline，当前 source 仅允许 runner/transport/matrix
三项 exact pin amendment。本票新增 module/schema/contract 和 state/parser/errors，因文件集合及
固定 bytes 同时不匹配而被 fail closed。批准 allowlist 不含该检查器，故未修改，也未把它跳过。
AGENTS 要求合同冲突/范围扩张升级给人。当时的精确修订提案另存 `evidence/governance-amendment-proposal.md`；
该阶段未改批准spec或伪造批准。随后用户批准的T04应用见下节。最终 PR 候选尚不满足完整 hard gate。

## Review 修复与 fresh remote 读回

Standards 轴发现1项 P1：evidence reader 重新 stat profile pathname 取得 owner，可能把验证后
被替换 profile 的新 owner 作为可信 operator。替换回归在旧实现实际失败（无 ReleaseError），
修复后通过：protected profile 使用同 FD open/fstat/限量读取，捕获 verified owner UID；
后续 evidence 只使用此 UID，不能从 pathname 重选身份。另覆盖 protection check/open 间替换。
190-test 全 release suite 用 worktree 外独立 bytecode cache 执行，PASS；source hashes 记录在回执。
首轮完整 smoke 仍为 FAIL；review 修复后未重跑完整 smoke（NOT RUN），既知固定集合阻塞未解除。

2026-10-02 再次 broker fetch：authoritative main 已前进到
`11c0410d3878d5449fa61796f174ba3d2dd5e59c`（#320/#322 文档治理合并）；本票起始 base 仍为
`5c2cd726c9aeaee9d17541d8feb049e33881bbac`。上游未改 release runtime/checker 或 AGENTS；未
rebase/重写本地审阅历史。合同修订获批后 fresh run 需重新读取 #320 合同并整合最新 main，再
做 final validation/PR candidate。本票此刻不是可提交 PR 的终态。
`legacy-schema-preservation.json` 读回：历史 v1 schema 原本不存在，保持缺席；v2 原 bytes 不变。

批准前历史 local handoff 为 NEEDS_HUMAN_DECISION（非 Controller 投影），精确 blocker 与下一步见 `evidence/handoff-needs-human-decision.json`；最终 PR 提交确认尚未请求。

## T04 独立治理合同应用（2026-10-02）

本会话用户再次直接回复“批准”，绑定 reviewed head
`32b0ee524ef5ae46f986498f6c617e8e5ce8cadf` 与送审proposal真实SHA256。授权仅为精确两文件
scope修订、T04合同应用并停止、后续fresh-run T05；不授权push/PR/merge/安装/部署。
Receipt为 `evidence/governance-amendment-approval.json`；原送审草案保持原bytes，作历史读回。

只修改mapped spec/plan/summary/verification、versioned release contract及本票证据。
治理checker、tests、runtime/schema与历史evidence在T04不改；scope/hash检查和文档验证结果
记录在 `evidence/t04-governance-validation.json`。T04不会重跑runtime功能测试或smoke；
190-test PASS是上轮 source回执，完整smoke仍保留原FAIL，T05 implementation/新增验收均NOT RUN。

- AC-11：NOT RUN；T05 exact source/addition gate实现和targeted回归尚未执行。
- AC-12：NOT RUN；T05 addition/tamper/permissions/index negative cases尚未执行。
- AC-13：NOT RUN；T05 checker/full release/full smoke及两轴review尚未执行。
- #317 live readback：open，labels exact `approved`、`type/bugfix`、`complexity/complex`。
- T04当前动作：本地合同提交后STOPPED_AFTER_GOVERNANCE_APPLY；需下一fresh run重新读合同，
  然后沿用本次批准实施T05。此停止是已批准步骤，并非再次请求同一范围批准。
- PR、push、CI、installed/live、NewEMaint #229集成/pin：NOT RUN。

T04合同应用commit：`c183a4d0acba74f14af8124661b252f43d1b33a1`。
Standards/Spec原reviewer并行只读复核，均0项发现、PASS，详见 `evidence/review-t04.md`。
Scope、proposal/prior-spec/source snapshot hashes实算保持；T04结束后停止，不实施T05。

## T05 fresh run 当前验证（2026-10-02）

Owner/session/Issue open+approved/classification projected真实读回；整合最新main
`65268ee5f1e622c486fd9e354dd35e20a2900f91`，仅在本人未发布branch做无冲突本地rebase。
旧recorded commit IDs仍是历史事实，未重写approval/handoff原bytes；映射见t05-fresh-read.json。
固定实现head `31e4f8592e178583c3b3be771e8d5c2f03173bd6`。新增当前回执t05-validation.json，
不覆盖旧platform-smoke.json/release-suite.json。

| Check / AC | Result | Evidence |
|---|---|---|
| AC-11 exact pins/constants/additions | PASS | fixed checker和两轴实算；historical constants/evidence/transport/matrix保持 |
| AC-12 boundary rejection regression | PASS | 26 tests；t05-targeted.log.gz；每个addition disk/index bytes/mode及非法pin等拒绝 |
| 完整checker + historical fake harness | PASS | t05-checker-receipt.json；历史绑定/source identity/cache；no override |
| 完整current release suite | PASS | 197 tests；t05-checker.log.gz；public runtime/state/CLI安全回归 |
| Standards / Spec source review | PASS | 0/0 findings；review-t05.md |
| AC-13完整smoke | GAP / FAIL | t05-smoke-failed.log.gz；exit=1，#308 fixture 23 tests/16 failures |
| 失败后续smoke步骤 | NOT RUN | fail-fast在test-installed-drift.sh，未跳过它继续宣称完整PASS |
| 未应用fixture提案试验 | PASS (draft only) | 独立candidate24 tests；真实fixture无diff；installed-drift-draft-test.log.gz |
| current real-E2E/installed/company_live/PR CI | NOT RUN | 没有现场/push/PR权限，不以临时fixture替代 |

新失败根因不是sandbox限制：8个临时安装surface row全PASS，但public checker按合同将
真实PR相对cachedmain的managed source差异报告source GAP/exit1；默认fixture正例仍要求0。
该测试文件不在已批准allowlist，本票没有修改；仅保存单文件patch/未批准修订提案。
AC-08完整smoke部分及AC-13仍未完成，T05/T03保持pending。按AGENTS范围扩张规则交接
local NEEDS_HUMAN_DECISION，未写Controller状态，未请求最终manual PR提交确认。

#327 broker已发布branch更新规则由独立owner治理；本票不改broker、不force、不发布branch。
未来提交前必须重新核验fresh main、claim、合法publication路径与exact验证head。

### 同根因上游去重与外部阻塞（历史）

调度提供#288正在独立治理同一fixture根因；已只读核对其patch真实SHA及边界，见
`evidence/t05-upstream-fixture-reference.json`。当前优先等待独立结果合并main，再由本票
fresh读取/整合并重验实际bytes，暂不重复请求扩范围；上文NEEDS_HUMAN_DECISION是发现
越界时的中间交接，目前local BLOCKED_EXTERNAL（不投影Controller）。
本票单文件提案保持未批准/未应用，不能继承#288批准/测试，不能把未产生PR加入hard
依赖。#317 depends_on=[]保持，T05/T03 pending、完整smoke FAIL、PR CI/installed/live NOT_RUN。
