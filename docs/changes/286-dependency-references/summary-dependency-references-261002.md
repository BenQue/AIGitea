---
issue: 286
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/286
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 限定跨仓依赖新增 schema 与只读权限边，涉及共享核心、Controller 和平台治理，强制 complex/manual
risk_flags:
  - shared-core
  - external-contract
  - authorization
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-dependency-references-261002.md
  spec: spec-dependency-references-261002.md
  plan: plan-dependency-references-261002.md
  verification: verification-dependency-references-261002.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/286-dependency-references
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/330
created: 2026-10-02
updated: 2026-10-03
---

## 问题/需求总结

#286 解决跨仓前置无法结构化表达、外仓裸编号被本仓同号误判的问题。旧数字继续只表示本仓；
新增 owner/repo#N 显式引用，broker 限定只读权限；Controller 与 routine merger 共用依赖规则。
裸数字没有仓库信息，不能识别作者误填的意图，禁止推断或替换目标仓。

## 合同确认与当前阶段

用户在本聊天 2026-10-02 对上一条裁决与启动请求回复“确认”。按该请求中的推荐 A 执行，
确认绑定 #286、change/286-dependency-references、A1–A7（spec 的 AC-1–AC-7）、候选 ticket graph、
唯一只读边 sfm-digital-board → aisoft-platform，以及覆盖旧 NewEMaint #80 调度前置。
这表示前置调度限制已被本次直接启动授权覆盖，不表示 #80 部署已经完成或验收 PASS。
草案曾把逻辑源项目写作 sfmdigitalboard；已按当前 manifest 的 project_id 更正为
  sfm-digital-board，仓库与 source→target 权限边不变。B/C 未选定，不再是执行路径。Policy=manual；无 PR/push、merge、安装、凭据、ACL 或部署授权。

G01（T01）已独立应用治理合同并停止；本 fresh run 已重读合同并完成 T02、T03 的 source
实现与本地测试。原候选 T01/T02/T03 顺延为 T02/T03/T04，切片与顺序不变，无需重复启动确认。
T04 已完成 #289 真实 merge 后的串行整合与组合验证：完整 smoke PASS，1042 runtime tests。
用户已确认提交，唯一最终 PR #330 已创建。历史失败保留于 verification 与 evidence。

## 集成顺序（非产品依赖）

2026-10-02 总调度安排 #286 在 #289 之后集成，优先级 5。#289 真实合并后，本会话
本人 fresh-fetch/rebase 并跑两条依赖闸门及文档/终态全套验证；不代写 #289。
这是集成顺序，不新增 depends_on，不改变已批准 A 合同，不重复启动确认。

## 影响范围与边界

- 源合同与 runtime 仅涉及 dependency schema/resolver、broker bounded read、
  Controller/routine 依赖闸门、展示与测试，详见映射 spec/plan。
- 初始基线 5c2cd726c9aeaee9d17541d8feb049e33881bbac；当前整合基线
  16beee09aefe89b5bc80a31544c59d456190ea32（#289 已合并并整合）；隔离 worktree
  /private/tmp/issue-286-dependency-references，本 session
  01a0fc7c-1670-75b2-a61b-f47e62fc856c 已 claim，last_push_head=null。
- #289 负责 required_docs/documents 与终态数据源，本票不改该算法，不写其 worktree；
  共享 contract.py 后续按各自 owner 串行整合。无 Issue 机器硬依赖。
- 不修改 AGENTS.md，不新增其它跨仓边，不顺带修其它 Issue，不安装 global skills。

## 验证状态

AC-1–AC-7 source/local 验收 PASS。#289 PR325 已真实合并，exact merge 在 origin/main，
本 owner 无冲突整合；最终完整 smoke PASS：1042 tests / 104.165s / exit 0。
依赖与 required_docs 组合 targeted 34 tests PASS；双轴增量复核均 0 项发现。
151 changes 文档 gap=0；4-role required_docs/documents、7 AC、approved loader、
classification projected 与终态工具 dry-run PASS。未修改 #289 算法，未 apply 终态。

历史 C.UTF-8/Bash 3.2 registry 失败及提前 65268ee5 基线的 #308 fixture 失败保留。
当前主线包含上游隔离 fixture 修复，完整 smoke 已验证；没有在本票弱化或绕过检查。
PR CI、manual merge、真实 installed/live dependency GET 与部署 NOT RUN。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 限定跨仓依赖新增 schema 与只读权限边，涉及共享核心、Controller 和平台治理，强制 complex/manual
risk_flags:
  - shared-core
  - external-contract
  - authorization
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

qualified dependency 扩展数据格式、broker 权限合同、Controller 与 routine 行为；即使局部代码
很小也强制 complex。verification 保存只能改动前观测的误判证据，不意味着本票部署。

### 缺失的 acceptance criteria 或决策

无。用户已选推荐 A 并确认启动。G01→fresh-run 边界已满足，T04 本地硬门与最终集成已通过。
不是再次需要选择 A/B 或批准合同；真实 classification --verify 已 projected，仅待最终 PR 提交确认。

## 当前交接

#289 PR325 最新 typed readback：closed、merged=true，exact merge
16beee09aefe89b5bc80a31544c59d456190ea32；broker fresh-fetch 与 ancestor proof PASS。
本 owner 在未发布、干净分支无冲突整合；7 个本票 patch range-diff 全部 =。
完整 smoke 的 tested source head 为 36609fa975301518c4bc7daf564b1892b1ba5eb6。
源代码与测试 tree digest、前后 SHA、完整压缩日志、分类与终态 dry-run 见
[evidence/t04-post289-integration-receipt.json](evidence/t04-post289-integration-receipt.json)。

T04 completed；用户直接回复“确认提交”，绑定 #286/change/286-dependency-references/manual。
唯一最终 PR #330 已真实创建；首发 pushed_head 精确等于已确认候选
5f5b5f101183f5cdb19c039ddc8bcd8cdfa2acdb，previous_head=null，owner/session 相同。
当前 PR_OPEN/awaiting_ci，文档回填与收据按原确认继续 fast-forward 发布；每次逐字核对
新鲜验证的 exact pushed_head。required CI 全绿后停 READY_FOR_REVIEW，由人合并。
未 merge、安装、扩 ACL、部署、写 completed 或归档。

先前“按你的建议继续”只覆盖提前本地 rebase；本次“确认提交”另行满足最终 PR 确认。历史拒绝与失败收据
保留；#327 未新增为 hard 前置，未代改 broker 或其它 owner worktree。
