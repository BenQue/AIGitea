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
status: approved
branch: change/286-dependency-references
pr_url:
created: 2026-10-02
updated: 2026-10-02
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
T04 的完整 smoke 已在 LC_ALL=C 下通过；#289 后集成门仍未完成，没有最终 PR 提交确认。

## 集成顺序（非产品依赖）

2026-10-02 总调度安排 #286 在 #289 之后集成，优先级 5。#289 真实合并后，本会话
本人 fresh-fetch/rebase 并跑两条依赖闸门及文档/终态全套验证；不代写 #289。
这是集成顺序，不新增 depends_on，不改变已批准 A 合同，不重复启动确认。

## 影响范围与边界

- 源合同与 runtime 仅涉及 dependency schema/resolver、broker bounded read、
  Controller/routine 依赖闸门、展示与测试，详见映射 spec/plan。
- 初始基线 5c2cd726c9aeaee9d17541d8feb049e33881bbac；当前整合基线
  11c0410d3878d5449fa61796f174ba3d2dd5e59c（#320 已合并）；隔离 worktree
  /private/tmp/issue-286-dependency-references，本 session
  01a0fc7c-1670-75b2-a61b-f47e62fc856c 已 claim，last_push_head=null。
- #289 负责 required_docs/documents 与终态数据源，本票不改该算法，不写其 worktree；
  共享 contract.py 后续按各自 owner 串行整合。无 Issue 机器硬依赖。
- 不修改 AGENTS.md，不新增其它跨仓边，不顺带修其它 Issue，不安装 global skills。

## 验证状态

改动前合成复现 PASS；contract/Controller 基线 67 tests PASS；初稿文档检查 145 changes、gap=0。
完整命令与阶段结果在 verification。G01 的文档/真实 approved 合同 loader 与分类读回 PASS；
完整 smoke FAIL（未修改的 registry-preflight 停服负向断言两次失败），独立全量 runtime 基线 978 tests PASS。
本 fresh run 的 AC-1–AC-6 source/local fixture 已通过，最终全量 runtime 998 tests PASS。
双轴审查发现的 3 项缺口已修复并复核；文档、digest、分类读回、broker shell 与 ShellCheck PASS。
本轮完整 smoke 在 LC_ALL=C 下 PASS，含 998 runtime tests；原 C.UTF-8/Bash 3.2 失败保留。
AC-7 最终整合仍 PARTIAL：#289 后整合尚未完成。PR CI、installed/live 与部署 NOT RUN。

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

无。用户已选推荐 A 并确认启动。G01→fresh-run 边界已满足，后续仅剩 T04 硬门与集成验收，
不是再次需要选择 A/B 或批准合同。最终 PR 前须真实 classification --verify 与独立提交确认。

## 当前交接

已无冲突整合 origin/main 的 #320；当前 base 为
11c0410d3878d5449fa61796f174ba3d2dd5e59c，完整 smoke 测试 source head 为
12dd967eb60253d7033c2c8ccb0c382b499bf1c6。本地 rebase 的前后 commit 映射与环境诊断收据
见 evidence/t04-resume-receipt.json。未 push，last_push_head=null。

完整 smoke PASS（LC_ALL=C，998 tests，97.111s）。原 registry 失败为 C.UTF-8 locale 下
Bash 3.2 把变量后的中文标点误读为变量名；只设置单次测试命令的环境，未修改或绕过任何
registry 断言，也未改用户全局 locale 或真实服务。前次失败保留，不改写历史收据。

当前唯一前置是 #289：PR #325 最新 exact readback 为 open、merged=false，head
15b963a4f4dab52e4a161de0d8bab29ebc7d53c5。T04 保持 pending；待真实 merge 后，本 owner
fresh-fetch/rebase，再验证两依赖闸门及文档/终态。不进入 AWAITING_PR_CONFIRMATION，未取得
最终 PR 提交确认；不 push、不建 PR、不合并、不安装、不扩 ACL、不部署、不归档。
