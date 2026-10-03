---
issue: 288
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/288
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 容器源码文件新增强制核验入口改变共享架构校验合同并迁移声明输入
risk_flags:
  - shared-core
  - schema-change
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-dockerfile-digest-261002.md
  spec: spec-dockerfile-digest-261002.md
  plan: plan-dockerfile-digest-261002.md
  verification: verification-dockerfile-digest-261002.md
depends_on: []
status: pr-open
branch: change/288-dockerfile-digest
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/328
created: 2026-10-02
updated: 2026-10-02
---

## 问题/需求总结

现有 architecture validate/lock 完全不读取 Dockerfile。基线探针修改 digest、退回 tag 或删除文件后仍 valid true 且 lock hash 相同。#288 选择 validator 共用入口核验源码 FROM。

## 影响范围

仅 AISoftPlatform architecture declaration schema、README、runtime、相关 tests 与 fixtures/reference；complex/manual，不修改应用、catalog/profile pin、release reader、Agent 或 CI/部署脚本。

## 初步方案与建议

映射 spec 固定 dockerfiles 路径数组、repo root、全部外部 FROM 的 digest 集合双向检查及保守变量/语法边界；独立 T01 治理合同 commit 后停止，fresh run 再做 T02/T03。

## 风险

- 已有容器声明缺 Dockerfile 输入将 fail closed，需要应用自身 Change 迁移，不能用旧兼容跳过。
- 静态核验仅证明声明源码输入；不能证明实际 builder 参数或制品 provenance。
- 与 #287 文件邻近，独立 worktree/PR；只由本 owner 自行整合 fresh main。

## AI 判级

```yaml
change_type: bugfix
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 容器源码文件新增强制核验入口改变共享架构校验合同并迁移声明输入
risk_flags:
  - shared-core
  - schema-change
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 2026-10-02 broker read #288 open、needs-analysis、无 approved 合同，唯一评论为旧调度延后说明；本轮明确派单重新准备。
- broker onboarding PASS；main 禁 direct/force push，required CI / verify (pull_request)，routine disabled。
- fresh origin/main 5c2cd726c9aeaee9d17541d8feb049e33881bbac；本 worktree 已 claim 到 session 01a0fc7b-f327-7a93-a48c-a254937cb08d。
- 共用 build_lock 与 CLI _build 不消费 Dockerfile；4 场景基线假绿已记入 verification。
- 现有 architecture 57 tests PASS，未覆盖真实 FROM 核验；未发现冗余实现。
- .out-of-scope 与 CONTEXT.md 未发现本 Change 相关既有拒绝或词汇合同；ADR-0001/0004/0006 已读取。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。

## 合同与实施边界

- Policy: manual；用户于 2026-10-02 明确回复“确认”，批准本映射 spec/plan 启动。PR 提交尚未授权。
- 完整合同见 [spec](spec-dockerfile-digest-261002.md)，ticket graph 见 [plan](plan-dockerfile-digest-261002.md)，基线结果见 [verification](verification-dockerfile-digest-261002.md)。
- Matt triage 已验证 bug，推荐 ready-for-agent；当前 broker 没有 triage 双维度 projector，live 投影为 GAP，不绕行直接 API，不在 #288 修改 broker。
- T01/T04/T02/T05/T06/T03 完成本地交付；T06 后 fresh-run 完整 runtime/smoke 均 PASS，最终候选等待唯一 PR 提交确认（manual）。PR CI、installed/live/现场验收为 NOT RUN。无硬依赖。

## 启动授权与治理步骤

授权记录见 [receipt](evidence/contract-start-authorization.json)，冻结批准时 spec/plan SHA256。
T01 只应用 schema 与 README 合同；运行时文件核验仍为 NOT RUN。治理独立 commit 后停止，fresh run 重读本合同继续 T02/T03，无需重复启动确认。

## 最小范围补充授权

用户于 2026-10-02 再次回复“确认”，仅批准两处 shell 测试的显式 root 参数与 synthetic 模板迁移；receipt 与完整 patch 在 evidence。T04 独立应用后停止，原合同批准持续有效，runtime/最终 PR/安装部署仍未执行。

## T02 初轮实现进度（历史快照）

T02 已完成：容器所有声明文件的 FROM digest 双向检查，root/路径/语法 fail closed，
三 CLI 入口、库调用与现有 checker 共用硬门。非容器四合同 canonical bytes 与 baseline 完全一致。
平台 smoke 真实 FAIL：release evidence checker 仍冻结旧 reference lock bytes。
未修改该治理文件；T03/最终 PR 待补充授权与 #287 fresh main 组合验证。

## T05 治理补充应用

用户确认完整两文件补充，已冻结授权 receipt。checker 只新增当前 synthetic reference lock
的 exact SHA256 pin；防篡改单测覆盖该 lock 的 disk/index 漂移。20 项 boundary tests 与
真实静态 source identity PASS，historical evidence 与原 runtime pins 保持原 bytes。
本步独立治理 commit 后停止，完整 smoke/runtime 与 #287 fresh-main 组合待下一轮；
没有 push、PR、merge、install 或 deploy 授权。

## 第一轮最终候选进度（main 14bfe6 的历史快照）

已由本 owner 整合 #287 已合并的 main `14bfe6edea6a78e994daac88b3615c009ae37fea`，
组合 runtime commit `aa585dd5b5b7a27e8ed6cdbebb9f8746a7a27128`。
完整 runtime 1008 项 PASS；受控 host 完整 smoke PASS（含第二次 1008 项 runtime）；
四种非容器合同在 V1/V2 的八组 canonical bytes 与 fresh main 相同。
T05 synthetic V1 lock exact pin 未漂移；原历史 evidence、release reader、lock schema 未改。
批准合同真实读回 PASS / 8 AC；分类为 bugfix / complex，两维度 projected，Policy manual。
当时拟准备 AWAITING_PR_CONFIRMATION 候选，尚未持久化该状态；后续最终 main 刷新发现新的阻塞。
本轮只证明 source/local 验收；唯一 PR/required CI、全局安装、现场、制品构建与部署均 NOT RUN。

## main 65268ee smoke 阻塞（T06 批准前历史快照）

已整合 #308 合并 main `65268ee5f1e622c486fd9e354dd35e20a2900f91`，组合 head
`aaa9e8dc2b6875c4658f7a9c8f59f7c91907a983`。新 smoke 在 installed-drift fixture
23 tests / 16 failures，八个临时安装面 bytes PASS，但真实 cached-main source GAP
令默认 fixture 预期不成立。完整 smoke 当前 FAIL；后续完整 runtime 未执行。
此前 1008 项结果保持绑定前轮 head；不得用旧结果覆盖新 gate。
T03 pending，当前 NEEDS_HUMAN_DECISION。未批准 T06 草案仅修正单个 fixture 的默认本地
源码基线，保留真实 checker fail closed，临时副本 23 tests PASS，未应用。
完整 patch/范围/回滚与证据见 `evidence/installed-fixture-amendment-proposal.json`。
原 spec 保持批准范围；先取此精确补充确认，不能请求或提交最终 PR。

## T06 已批准应用与治理停止（本次 fresh run 前的历史快照）

用户回复“确认”，批准 exact patch
`af73fbd48c2459b0792cc88493e08af9d7c89ae74a17026b5845271fcadecf22`。
映射 spec/plan 已同步该唯一 fixture 路径的授权。实际工作树官方 wrapper 23 tests / 44.895s
PASS，after hash/compile/reverse patch 与真实 approved 合同读回 PASS。
真实 installed checker、runtime、installer、smoke 硬门、actual origin/main 与历史 evidence 未改。
授权和应用 receipt 分别保留；原 proposal 仍是批准前快照，不将提案测试冒充实际应用验证。
T06 done，独立本地 commit 后停止；T03 pending，fresh run 重读新合同后继续完整 smoke/runtime，
不重复启动或 T06 补充确认。该停止不表示全部验收完成或最终 PR 提交已获准。
本轮 full smoke/runtime、PR/required CI、global installed、现场与部署均 NOT RUN；
旧 smoke FAIL 和旧 head 的 1008 项结果保持各自原有边界。

## T03 完成、最终 PR 待确认（提交授权前历史快照）

T06 独立提交停止后，本 fresh run 重读批准合同，真实 owner/branch/clean tree/patch hashes
与 main readback 通过。验证 source head `1507e358319ebfc2206fe0402ce1520f3392a246`，
pinned main `65268ee5f1e622c486fd9e354dd35e20a2900f91`。
完整 runtime 1008 tests / 101.684s PASS；完整 host smoke PASS，含新 fixture 23 tests / 44.320s
与第二次 runtime 1008 tests / 101.989s。八组非容器 V1/V2 输出与 pinned main bytes 相同。
真实分类读回 bugfix / complex / projected，Policy manual；approved/onboarding/protection/唯一 PR PASS。
当前所有 ticket 完成本地验收，准备 AWAITING_PR_CONFIRMATION；最终候选 exact SHA 由本地状态
文件固定。PR 草稿为 `evidence/final-pr-body.md`，只有一行 Closes #288。
本轮只证明 source/local；没有 push/PR/merge，required CI/global installed/应用迁移/
builder provenance/现场/部署 NOT RUN。历史失败、提案和治理停止 receipt 均保留原样。

## 提交已批准、线性候选通过（首次发表前快照）

用户明确回复“确认提交”，授权 exact #288 / change/288-dockerfile-digest / manual
的唯一最终 PR 与合同内 CI 修复，绑定记录见 `evidence/pr-submission-authorization.json`。
首次 broker push 在发表前拒绝本地 merge commits；保留原候选本地 tag 后，将未发表
历史线性整理。新 code head `69d5ad511dd9620f2f3865e6439773b2c1744d1f` 的完整 tree
与批准候选相同，main 以上无 merge commit。完整 host smoke 重新 PASS，含 1008 tests
/ 109.408s 与 fixture 23 tests / 47.297s，证据见 `evidence/pr-linear-history-validation.json`。
本次只新增提交授权、线性验证证据及 PR 草稿格式修正；已测试技术字节保持相同。
现继续首次成功 push/唯一 PR/required CI；全绿停 READY_FOR_REVIEW，人工合并。
当前 PR/required CI、global installed、应用迁移、builder provenance、现场与部署 NOT RUN。

## 当前状态：唯一 PR #328 已提交，required CI 待核对

[PR #328](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/328) 为本 Issue 唯一最终 PR，
Policy manual。首次成功发表 head `1215d1c2c86dbeb81288ebbcc1a35cc05ac79d20`，
broker pushed_head 与本地候选相同；publication receipt 见 `evidence/pr-publication.json`。
本次回填 summary 的 pr_url/status，并记录 PR 元数据；技术字节未改。后续普通 push
保留已发表 tip 为祖先，最终 required context `CI / verify (pull_request)` 必须绑定最新 head。
当前 PR open、未 merge；required CI PENDING，不沿用本地 PASS 代替 CI。
全绿停 READY_FOR_REVIEW 等人审核合并；global installed/应用迁移/builder provenance/现场/deploy NOT RUN。
