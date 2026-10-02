---
issue: 317
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/317
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 在共享发布状态机加入迁移后旧镜像兼容控制及可信依据，涉及数据、外部合同与回滚强制风险。
risk_flags:
  - data-migration
  - external-contract
  - shared-core
  - rollback
  - security
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-migration-rollback-guard-261002.md
  spec: spec-migration-rollback-guard-261002.md
  plan: plan-migration-rollback-guard-261002.md
  verification: verification-migration-rollback-guard-261002.md
status: approved
branch: change/317-migration-rollback-guard
pr_url:
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

当前 local handoff 为 `AWAITING_PR_CONFIRMATION`，不是 Controller 状态投影。唯一 branch
`change/317-migration-rollback-guard` 未 push/未创建 PR，manual 最终提交确认尚未取得。
PR CI、真实 Docker/DB、installed/live 与 NewEMaint #229 消费验收仍 `NOT RUN`；#229 pin 未改。
最终 PR 草稿与确认边界见 `evidence/final-pr-candidate.md`。

## 问题/需求总结

activate、legacy deploy、显式 rollback 在数据库完成不同 migration identity 后仍可无兼容依据启动旧镜像，阻塞 NewEMaint #229。

## 影响范围

只修改 AISoftPlatform release 合同及 runtime/test/schema；不修改 NewEMaint、应用 pin、现场配置或凭据。

## 初步方案与建议

统一所有旧镜像启动与恢复入口的 fail-closed gate，记录数据库迁移位置；只允许可证明相同位置或 exact、未过期且 operator 管理的兼容依据。

## 风险

- 容器 current_release 不等于当前数据库位置；迁移成功而激活失败后两者会分离。
- 合法旧 state 不包含迁移顺序，读兼容不能变成安全事实默认值。
- 兼容依据自身是权限边界，必须与不可变制品及目标、数据库状态绑定；不得以 producer boolean 代替。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 在共享发布状态机加入迁移后旧镜像兼容控制及可信依据，涉及数据、外部合同与回滚强制风险。
risk_flags:
  - data-migration
  - external-contract
  - shared-core
  - rollback
  - security
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 批准前判级证据（历史）

- authoritative origin/main=5c2cd726c9aeaee9d17541d8feb049e33881bbac；共享 main clean。
- #317 正文记录 2026-09-21 批准1,2 的平台先行方向，评论线程为空，无已映射 spec/plan、branch/history/PR。
- FakeDocker public ReleaseRuntime seam 在 activate、legacy v1 deploy、explicit rollback 均复现：不同迁移已完成、兼容依据不存在、旧 SHA 启动 1 次。
- host.onboarding.check=PASS；main 禁止 push/force，唯一 merge identity=admin，required CI=CI / verify (pull_request)，routine disabled。

### 缺失的 acceptance criteria 或决策

- 无；2026-10-02 用户直接批准完整 spec/plan。

## 授权与会话

- 本会话：`01a0fc7b-9d82-75e2-975f-d407cd23e34a`；worktree 已 claim。
- Branch/worktree：`change/317-migration-rollback-guard` / `/private/tmp/issue-317-migration-rollback-guard`。
- 既有授权：平台先补控制，人工合并后由 NewEMaint #229 更新 pin；不重复确认此方向。
- 2026-10-02 用户在本会话直接回复“批准”，当前完整 spec/plan 已获合同启动授权；receipt 见 evidence/contract-start-approval.json。
- `depends_on: []`：#317 无前置；NewEMaint #229 依赖本票，应用层不在本分支修改。
- Delivery policy：`manual`。合同启动确认不授权 push、PR、merge、安装、部署或 Secret。
- 三阶段：合同审阅 → 独立治理合同步骤并停止 → fresh run 重新读取后实施 runtime → 最终 PR 提交确认。
- 所有文档只存在本地；未 push，不提供不存在的远端文档链接。

## 当前投影边界

判级为 bugfix/complex。首次自动审批在完整合同批准前拒绝 live classification --apply，未写入标签；2026-10-02 用户直接批准后允许按 spec 执行本票投影，并独立 --verify 读回。历史拒绝不再是当前缺授权 blocker；不存在的 triage typed surface 仍不绕过。


## T01 进度（历史停止点）

2026-10-02 合同已获用户直接批准。Fresh base 不变；已独立应用 release 治理文档。
classification --verify 两维真实 projected，远端 lifecycle=approved。
完整合同 loader 读到10条 AC、frontier=T01。runtime/schema/test、PR CI、installed/live 均 NOT RUN。
Matt triage typed 写缺口记录为 GAP，本票不改 broker 或通过其他身份绕过。


T01 治理合同应用及两轴文档 review 已完成；3项发现已修复复核，无未解决review finding。
本运行按已批准合同停止。T02/T03必须由下一fresh run重读后实施，沿用当前批准，不追加合同确认。
批准记录已发布至Issue评论12027；无remote branch/PR，尚无可供应用采用的新merged SHA。

## T02/T03 进度（历史）

用户后续“下一步，继续”构成 fresh run，已重读 AGENTS、README、批准的治理合同/spec/plan 和
单写者 claim，在同一 worktree 实施。State v3 与数据库位置持久化、四类旧镜像启动/恢复路径
的统一兼容 gate、strict operator evidence、schema、CLI 与 consumer 本地实现已完成。
本地 release suite 190 tests PASS；首次完整 smoke FAIL，当时固定证据检查器的治理 amendment 尚未授权。
两轴审查结果见 verification，T03 最终验收 pending；尚未请求最终 PR 提交确认。
远端 classification --verify 实际读回 bugfix/complex projected；manual policy 固定。
PR、PR CI、installed/live 均 NOT RUN，NewEMaint #229 pin 未改，本票尚未解除该消费前置。

## T04 进度（历史停止点）

用户已批准精确两文件治理修订，receipt见 `evidence/governance-amendment-approval.json`。
映射spec新增固定source evidence合同与AC-11–13，plan新增T04/T05并让T03结项依赖T05。
T04只应用合同/记录并停止；checker/tests/pins尚未实施，原smoke FAIL未被改写为PASS。
下一fresh run沿用此次批准从T05继续，不重复请求此范围批准；最终manual PR确认仍保留。
原 `governance-amendment-proposal.md` 和 `handoff-needs-human-decision.json` 保留为批准前历史。
本次current交接为 `evidence/handoff-t04-fresh-run.json`，不投影自动Controller状态。

## T05 历史进度与新阻塞

Fresh run整合main `65268ee5f1e622c486fd9e354dd35e20a2900f91`，本会话owner-only对未发布
branch做无冲突本地rebase，旧approval/evidence原bytes保留，commit映射见t05-fresh-read.json。
T05精确checker/test实现head `31e4f8592e178583c3b3be771e8d5c2f03173bd6`；26 boundary tests、
完整checker的197 release tests与historical regression PASS，Standards/Spec 0/0 findings。
完整smoke FAIL：新#308 fixture八个临时安装row虽全PASS，但使用真实pending PR源码作
正例baseline，source GAP产生23 tests/16 failures。后续smoke步骤NOT_RUN。

本票T05/T03仍pending，AC-13/GAP；原190-test与首轮smoke FAIL保留为历史，未改旧回执。
新单test文件最小提案 `evidence/installed-drift-fixture-amendment-proposal.md` 未批准/未应用；
独立candidate局部24-test PASS不替代full smoke。本次local NEEDS_HUMAN_DECISION是交接记录，
不是Controller状态投影。未push/PR/安装/部署，NewEMaint #229仍无可采用的新merged SHA。

### 同根因上游去重与外部阻塞（历史）

调度提供#288正在独立治理同一fixture根因；已只读核对其patch真实SHA及边界，见
`evidence/t05-upstream-fixture-reference.json`。当前优先等待独立结果合并main，再由本票
fresh读取/整合并重验实际bytes，暂不重复请求扩范围；上文NEEDS_HUMAN_DECISION是发现
越界时的中间交接，目前local BLOCKED_EXTERNAL（不投影Controller）。
本票单文件提案保持未批准/未应用，不能继承#288批准/测试，不能把未产生PR加入hard
依赖。#317 depends_on=[]保持，T05/T03 pending、完整smoke FAIL、PR CI/installed/live NOT_RUN。
