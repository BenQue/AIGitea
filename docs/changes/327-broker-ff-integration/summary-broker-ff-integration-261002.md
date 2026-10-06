---
issue: 327
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/327
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - cross-module
  - security
  - rollback
depends_on: []
branch: change/327-broker-ff-integration
created: 2026-10-02
updated: 2026-10-06
status: approved
reason: 改变受控发布与主线整合行为并覆盖历史治理合同，涉及共享 broker、Controller、安全与回滚
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-broker-ff-integration-261002.md
  spec: spec-broker-ff-integration-261002.md
  plan: plan-broker-ff-integration-261002.md
  verification: verification-broker-ff-integration-261002.md
override_reason: ''
pr_url: ''
---

# #327 保留历史的最小 Git 修复

2026-10-06 当前进度：本人首次 main 整合已核实完成，H0 `3052a8a0d47a8c7333f06e073ca5a4ecc1047a90` 的 parents 精确 `[1078e4aead52020b49a91cc97b118245f7d972f1,96ba8a17baad8e9854d4e8d0397d4162b8067b09]`。fresh T02 复用原 stash 的直接 Git 9 WIP，23 延期源码完整保全。来源计数一行补充已由本人确认落实；固定最终源码的原样默认 smoke PASS，包含 full runtime 1146 tests；Python3.9 核心 98 tests、7 shell 的 bash-n/ShellCheck 与源受管映射 PASS。增量 Spec/Standards hard=0/0；本地单 parent source commit 与最终 fixed-head review 的 exact SHA/结果在本 owner 外部候选回执记录，避免文档自引用 SHA。

T02 当前 source/local 范围完成；T03 in-progress，已准备只读精确 ref 操作。真实 R0/R 仍 GAP，下一人操作仅为成功 exact ref/main 读回；不重复已完成人工 main 整合。成功读回后才绑定 exact R/H 的首次普通 FF 命令与唯一最终 PR 第二确认。真实发表/PR/新 head CI/manual merge、实际新 broker 安装仍 NOT RUN；旧失败与明确延期能力继续保留。完整分层证据见 verification 最新节。

## 2026-10-05 收缩治理时的摘要（历史）

本人 2026-10-05 在根聊天接受诊断收缩并授权一次定向续办；这不是旧 T10 的批准重放。本轮只完成具体收缩治理、验证/本地原子 commit 后 STOP，下一 fresh run 续 T02。exact owner/branch/worktree/manual 保持，最终唯一 PR 第二确认与本人 merge 独立保留。

- [spec](spec-broker-ff-integration-261002.md)：只修 main 整合、ordinary FF、非法/并发漂移拒绝、required CI 与恢复；当前条款明确取代旧 R02/authority/OS 自举前置。
- [plan](plan-broker-ff-integration-261002.md)：保留原 Ticket IDs/历史状态；T02 in-progress、T03 pending，不新增合同卡链/Issue。
- [verification](verification-broker-ff-integration-261002.md)：原 FAIL/GAP/NOT RUN 保留；完整恢复与现有能力读回；32 源码 WIP 不动、原 verification WIP 正文随本次治理保存。

原 HEAD `f8750441f3dce96f3b9a24a134f877ad1cf6aa35`；fresh main `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853` 尚未整合。33 WIP/index/refs/原证据已完整保全并独立恢复核对。existing installed broker 仍 lease-force/blanket merge deny，begin/verify 不可用；不能当新 FF 能力使用。project-agent non-admin pull/push 已核，main 禁直推/force，required `CI / verify (pull_request)`；远端 #327 exact ref 仍 GAP，fetch 错误不表示 absent。

root authority/protected grant、ES/kernel/signing、完整 OS/解释器闭包与 scratch/resource 隔离及 I01/I02/AC-9～11 **明确延期，未交付**；AC-7 installed 仍 GAP/NOT RUN。不再要求将来运行程序先整合其自身源码，也不再用逐文件 UI 重建本地 history。Agent/provider 仍不 merge；首次本地整合由本人按标准 Git 临时 park/保存 stash/bundle 后做 `[治理 G,fresh M]`，只本地，不发表。具体复制操作在本 owner 外部 `human-first-main-integration.md`，实际 G 由本次 receipt 绑定。

最短后续：本人一次标准 Git main 整合 → fresh T02 按保全清单复用直接相关 WIP、完成最小修复与真实全门 → T03 exact final candidate/guard/恢复 → 唯一最终 PR 第二确认 → 本人普通 FF 首次发表与 required CI → 本人 manual merge/当前范围的可恢复收尾。首次发表的 guard/FF 未验收就如实 GAP，不能先安装 unmerged broker 或 Agent 改用 direct Git。延期项不作当前 source PR/收尾硬依赖，source/local/CI 不代表 installed/live。

live Issue 仍 open、只有 `triage/needs-triage`；本轮不写标签/远端。`depends_on: []` 保持，不把 #333/#336 或 #339 设为本票产品 hard dependency。routine disabled、main 保护、现有 credentials/required contexts/双 provider 配置均保持。
