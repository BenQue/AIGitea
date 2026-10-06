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
status: pr-open
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
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/346
---

# #327 保留历史的最小 Git 修复

2026-10-06 当前进度：本人首次 main 整合已核实完成，H0 `3052a8a0d47a8c7333f06e073ca5a4ecc1047a90` 的 parents 精确 `[1078e4aead52020b49a91cc97b118245f7d972f1,96ba8a17baad8e9854d4e8d0397d4162b8067b09]`。fresh T02 复用原 stash 的直接 Git 9 WIP，23 延期源码完整保全。来源计数一行补充已由本人确认落实；固定最终源码的原样默认 smoke PASS，包含 full runtime 1146 tests；Python3.9 核心 98 tests、7 shell 的 bash-n/ShellCheck 与源受管映射 PASS。增量 Spec/Standards hard=0/0；本地单 parent source commit 与最终 fixed-head review 的 exact SHA/结果在本 owner 外部候选回执记录，避免文档自引用 SHA。

T02 原 source/local 候选已完成；T03 in-progress。本人已批准 exact Issue/branch/manual 与首次 H=`f97d0d88a99373711a22c44b72d46976cd290638`，完成单 ref 普通 FF；冻结 guard 实际执行 PASS，R0 已知不存在且未重 pin，remote 与 owner.last_push 均读回 H，当时 main=`96ba8a17baad8e9854d4e8d0397d4162b8067b09`。唯一 [PR #346](http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/346) 已通过 typed broker 创建；首次 required `CI / verify (pull_request)` 随后 success（run1801/job2007）。fresh typed read 已发现 main/base 推进到 `000a3f73cd7069f4aef0a202b1a19555014fd887`；旧 head 的成功 CI 不覆盖新候选和新 base，未到 READY_FOR_REVIEW。

PR 回填后 summary 正确进入 `pr-open`，最小 Git scope 原只接受 `approved`，实际回填提交的预检因而失败。本次仅修复原批准模块和测试：summary 允许 `approved|pr-open`，开放 PR 必须有唯一 exact Issue URL 与同仓正数 PR URL；spec 仍唯一 `approved`，空/错误/畸形重复字段全部拒绝。实际回填器→scope/history→bare ordinary FF 正向与16负向 cases 包含在 Python3.9 核心20项 PASS、Homebrew full runtime1148项 PASS，源码 hash 稳定，两轴 hard=0。完整 smoke 在 source guard 的 behind10 门 FAIL，未到 runtime；错误使用系统 Python3.9 的全仓1011项 FAIL也保留。只读三方 tree 预演无冲突，人工本地整合入口6个真实Git fixture PASS；下一步本人整合固定新 main 并 STOP，随后重跑默认 smoke，再更新同一 PR。实际后续整合/发表、final head/base CI、manual merge、安装/live仍 NOT RUN；旧失败和延期能力保留。

## 2026-10-05 收缩治理时的摘要（历史）

本人 2026-10-05 在根聊天接受诊断收缩并授权一次定向续办；这不是旧 T10 的批准重放。本轮只完成具体收缩治理、验证/本地原子 commit 后 STOP，下一 fresh run 续 T02。exact owner/branch/worktree/manual 保持，最终唯一 PR 第二确认与本人 merge 独立保留。

- [spec](spec-broker-ff-integration-261002.md)：只修 main 整合、ordinary FF、非法/并发漂移拒绝、required CI 与恢复；当前条款明确取代旧 R02/authority/OS 自举前置。
- [plan](plan-broker-ff-integration-261002.md)：保留原 Ticket IDs/历史状态；T02 in-progress、T03 pending，不新增合同卡链/Issue。
- [verification](verification-broker-ff-integration-261002.md)：原 FAIL/GAP/NOT RUN 保留；完整恢复与现有能力读回；32 源码 WIP 不动、原 verification WIP 正文随本次治理保存。

原 HEAD `f8750441f3dce96f3b9a24a134f877ad1cf6aa35`；fresh main `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853` 尚未整合。33 WIP/index/refs/原证据已完整保全并独立恢复核对。existing installed broker 仍 lease-force/blanket merge deny，begin/verify 不可用；不能当新 FF 能力使用。project-agent non-admin pull/push 已核，main 禁直推/force，required `CI / verify (pull_request)`；远端 #327 exact ref 仍 GAP，fetch 错误不表示 absent。

root authority/protected grant、ES/kernel/signing、完整 OS/解释器闭包与 scratch/resource 隔离及 I01/I02/AC-9～11 **明确延期，未交付**；AC-7 installed 仍 GAP/NOT RUN。不再要求将来运行程序先整合其自身源码，也不再用逐文件 UI 重建本地 history。Agent/provider 仍不 merge；首次本地整合由本人按标准 Git 临时 park/保存 stash/bundle 后做 `[治理 G,fresh M]`，只本地，不发表。具体复制操作在本 owner 外部 `human-first-main-integration.md`，实际 G 由本次 receipt 绑定。

最短后续：本人一次标准 Git main 整合 → fresh T02 按保全清单复用直接相关 WIP、完成最小修复与真实全门 → T03 exact final candidate/guard/恢复 → 唯一最终 PR 第二确认 → 本人普通 FF 首次发表与 required CI → 本人 manual merge/当前范围的可恢复收尾。首次发表的 guard/FF 未验收就如实 GAP，不能先安装 unmerged broker 或 Agent 改用 direct Git。延期项不作当前 source PR/收尾硬依赖，source/local/CI 不代表 installed/live。

live Issue 仍 open、只有 `triage/needs-triage`；本轮不写标签/远端。`depends_on: []` 保持，不把 #333/#336 或 #339 设为本票产品 hard dependency。routine disabled、main 保护、现有 credentials/required contexts/双 provider 配置均保持。
