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
status: approved
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

# 实施 Ticket graph

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 发布并可读回独立 release 兼容治理合同，完成后停止等待 fresh run | - | completed |
| T02 | public phased lifecycle 实现 v3 DB position 与 exact compatibility gate，从状态记录到 activate/rollback/错误输出可验收 | T01 + fresh run | completed |
| T03 | legacy deploy 与所有恢复路径统一 gate，consumer 说明、边界回归与最终候选 | T02, T05 | completed |
| T04 | 应用已批准的精确 source-evidence 治理修订，记录授权并停止 | T02 | completed |
| T05 | fresh run 实施 bounded checker/addition pins 与相应拒绝回归，完整验收及审查 | T04 + fresh run | completed |

不新建子 Issue；所有 ticket 保持 #317。T01 合同批准前不应用。T01 完成后停止当前运行；后续 fresh run 沿用该批准，不增加第三个产品确认点。

## Expected touch points 与明确 allowlist

- T01：`docker-release/README.md`、`docker-release/contracts/migration-rollback-v1.md`、本 Issue 映射文档。只应用治理合同，不触 runtime/schema/test。
- T02：`codex/runtime/aisoft_release/runner.py`、`state.py`、`contract.py`、`errors.py`；同目录新增受限 compatibility 模块；`docker-release/schema/state-v3.schema.json`、target profile v1 schema 的 optional field、compatibility evidence v1 schema；release phase/state/CLI/safety tests 及现有 fixture support；`cli.py` 仅若安全结构化错误需要调整，既有 CLI 参数不扩展。
- T03：同一 runner public deploy/restoration path；相应 runner/phases/contract/safety/CLI/evidence tests；consumer contract 说明、脱敏 example 与本 Issue verification。原 v1/v2 state schema 原字节保持。
- T04：仅映射 spec/plan/summary/verification、versioned migration rollback contract 与本票 evidence。合同步骤完成后停止，不修改 checker/tests/runtime。
- T05：新授权只包括 `codex/tests/check-release-evidence-boundary.py`、`codex/runtime/tests/test_release_evidence_boundary.py`；exact allowed/addition paths、固定 hash/mode、历史不变约束全部以 spec 修订节为准。
- 禁止 AGENTS.md、CLAUDE.md、controller/provider、broker、CI workflow、smoke.sh、任何 installer、host permission/grant、应用仓文件改动。

## 测试与验收映射

| Ticket / AC | Verification command or review |
|---|---|
| T01 | docs diff review；`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .`；确认仅合同文档，并记录停止点 |
| T02 / AC-01,03,04,05,06,07 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_phases tests.test_release_rollback_compatibility tests.test_release_contract tests.test_release_safety` |
| T02 / AC-08,09 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_cli tests.test_release_gate`；包括安全字段及 argv 出口 |
| T03 / AC-02,04,06,08 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_runner tests.test_release_phases tests.test_release_rollback_compatibility` |
| T03 / AC-01–09 | `PYTHONPATH=codex/runtime python3 -m unittest discover -s codex/runtime/tests -p 'test_release*.py'`；`bash codex/tests/smoke.sh` |
| T03 / AC-10 | consumer 文档人工 diff review，说明仅使用最终人工 merged SHA，未提供不存在的 pin；scope diff 检查 |
| T04 | semantic document loader/check、纯合同 scope/hash 检查、本地提交后停止 |
| T05 / AC-11–13 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_evidence_boundary`；`python3 -B codex/tests/check-release-evidence-boundary.py`；完整 release suite / `bash codex/tests/smoke.sh`；两轴审查 |
| 最终候选 | classification --apply → 独立 --verify #317 两维 projected；local commit clean；唯一 Issue/branch/worktree/docs tuple |

新增测试文件已在 fresh run 实施并运行；具体完整验证及审查结果见映射 verification。

## 逐项 AC 验收索引

本索引将已批准的分组验证展开为 Controller 可读的独立 AC 行；不改变验收范围。

| Acceptance criterion | Verification command or review |
|---|---|
| AC-01 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_phases tests.test_release_rollback_compatibility` |
| AC-02 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_runner tests.test_release_rollback_compatibility` |
| AC-03 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_rollback_compatibility tests.test_release_contract tests.test_release_safety` |
| AC-04 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_rollback_compatibility tests.test_release_runner` |
| AC-05 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_phases tests.test_release_runner` |
| AC-06 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_rollback_compatibility tests.test_release_phases` |
| AC-07 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_contract tests.test_release_phases tests.test_release_rollback_compatibility` |
| AC-08 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_gate tests.test_release_phases tests.test_release_runner`；完整 release suite / smoke |
| AC-09 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_cli tests.test_release_safety tests.test_release_rollback_compatibility` |
| AC-10 | consumer diff review、确认未更新应用 pin、最终人工 merged SHA 由消费会话采用 |
| AC-11 | fixed checker exact allowed paths/additions/pins diff review；targeted evidence-boundary regression |
| AC-12 | `PYTHONPATH=codex/runtime python3 -m unittest tests.test_release_evidence_boundary` 新增对象正/负例 |
| AC-13 | `python3 -B codex/tests/check-release-evidence-boundary.py`；完整 release suite；`bash codex/tests/smoke.sh`；source/evidence边界回读 |

## 数据库迁移

无真实数据库迁移。本票仅改变本地 deployment state 的受限读升级和写版本；FakeDocker 不操作真实 DB。未知旧 state 不自动生成可信位置，兼容依据独立 operator 管理。

## 部署与回滚

不部署、不安装。两次重复、一次故意健康失败及失败回退阻止在临时 fixture 执行，报告 source/local 事实；真实 Docker/公司现场验收 NOT RUN，属于消费项目独立授权。

本票代码出现问题用 forward fix 或保留 guard 的源码 revert，state v3 不强行降级。不能恢复旧 state/数据库绕过新的保护。

## 最终确认与交付

只有本地 AC 验证、完整 smoke、diff review 和真实 classification --verify projected 后才请求 exact #317 / change/317-migration-rollback-guard / manual 的最终 PR 提交确认。随后 broker push、pushed_head 与候选 SHA 比对、唯一 Closes #317 PR、回填实际 pr_url、required CI。停 READY_FOR_REVIEW，由人合并。merge 后证明 exact SHA 在 origin/main、确定性终态检查/清理/归档；NewEMaint #229 在其会话继续更新 pin。

## T01 完成与停止交接

2026-10-02 独立治理合同已应用，本地源码 commit `7de1cc2516d38c2b86d667e31d92f5f4a60dfa7e`；文档 review 修复 commit `95ff8f30f679a1baf978774ed32b855ae4ebe70a`。
Standards 和 Spec 两轴发现3项文档表达问题，均修复后由原 reviewer 只读复核通过，详见 `evidence/review-t01.md`。
纯合同和文档检查通过；type/complexity/lifecycle 实际读回正确。运行在这里停止，不实施 T02/T03。
下一 fresh run 沿用当前完整批准，重读治理合同和 claim 后从 T02 开始；不得把本次批准作为最终PR提交或merge/deploy许可。

## Fresh run 实施结果（历史）

T02 先通过 public ReleaseRuntime + FakeDocker 验证 v3 position/no-op、phased gate 与 strict evidence；
T03 本地实现已统一 legacy deploy 和显式回退失败恢复，但完整 smoke 的固定 source 闸门阻塞最终验收；保留 #305、host/action、artifact/image、transport、
health 与 CLI 既有闸门。只使用合成 fixture，无真实 Docker/数据库调用。完整验收与最终候选
以 verification 的实际命令回执为准；最终 manual PR 提交确认仍未取得。

首次完整 smoke 拒绝新增文件集合，结果 FAIL；当时 checker 不在批准 allowlist。
用户第二次直接批准精确修订后，T04 已应用合同并停止；T05 尚未实施，T03 仍 pending，
不能把范围获批等同 hard gate 已通过，也不能提前请求最终 PR。


## T04 完成与停止交接

第二次直接用户批准绑定 reviewed head `32b0ee524ef5ae46f986498f6c617e8e5ce8cadf` 与
`evidence/governance-amendment-proposal.md` 的真实 SHA256；具体 receipt 为
`evidence/governance-amendment-approval.json`。只应用治理合同/本票记录，source checker、tests、
runtime/schema、历史 evidence 原 bytes 保持；验证回执与停止点见 verification。
下一 fresh run 沿用该批准，先重新读共享 #320/main 合同和 owner claim，再从 T05 开始。
T03 只有在 T05 完整 hard gates 实际通过后才能 completed；唯一最终 PR 仍需 exact manual确认。

## T05 历史实施与停止交接

已实施精确checker/test两文件并提交本地31e4f8592e178583c3b3be771e8d5c2f03173bd6；
26 targeted tests、完整checker的197 release tests、historical regression与两轴review PASS。
完整smoke在新#308 fixture失败（23 tests/16 failures），不在当前额外两文件allowlist内。
T05/T03保持pending；单fixture文件提案未批准、未应用，草案24-test PASS仅为局部试验。
下一步取决于精确范围修订或独立上游修复，不重复已有两文件启动批准、不提前请求最终PR。

### 同根因上游去重与外部阻塞（历史）

调度提供#288正在独立治理同一fixture根因；已只读核对其patch真实SHA及边界，见
`evidence/t05-upstream-fixture-reference.json`。当前优先等待独立结果合并main，再由本票
fresh读取/整合并重验实际bytes，暂不重复请求扩范围；上文NEEDS_HUMAN_DECISION是发现
越界时的中间交接，目前local BLOCKED_EXTERNAL（不投影Controller）。
本票单文件提案保持未批准/未应用，不能继承#288批准/测试，不能把未产生PR加入hard
依赖。#317 depends_on=[]保持，T05/T03 pending、完整smoke FAIL、PR CI/installed/live NOT_RUN。
