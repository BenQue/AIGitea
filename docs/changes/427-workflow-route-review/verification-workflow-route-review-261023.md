---
issue: 427
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/427
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - agent-governance
  - platform-governance
  - cross-module
depends_on: []
branch: change/427-workflow-route-review
created: 2026-10-23
updated: 2026-10-23
status: pending
---

# Verification：合同准备与后续实施证据

## 基线与范围

- Issue：`admin/aisoft-platform#427`。
- source base / change_base：`dc1da41c6e6a51f85b1ec0464a97640a3ddb570e`。
- 当前阶段：合同/计划准备。未执行 T01–T05，下面准备检查不是实现验收。
- 环境：Mac Codex；唯一 writer/worktree 见 summary；当前源码 Matt v1.3.1 / SP v7.0.0。
- 本记录承接 AC-1–AC-8 的实现证据，另保存无法靠最终 diff/CI 重放的原始调用来源、治理交接和审查范围。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker gitea.issue.list --state open | PASS | 查重时只有 #417，凭据轮换；未操作该票 |
| broker git.fetch.main + git rev-parse HEAD origin/main | PASS | 二者均为上述 base；主仓 git status --short 空 |
| broker gitea.issue.create + gitea.issue.read 427 | PASS | exact admin/aisoft-platform#427，open，needs-analysis 入口；project-agent 身份 |
| aisoft change-name / claim-worktree | PASS | exact tuple、唯一 session 已核对 |
| Matt manifest 三个目录 hash | PASS | triage、to-spec、to-tickets 按现 _directory_hash 算法匹配；单文件 hash 不能拿来比较目录摘要 |
| 语义 triage | PASS | bug / ready-for-agent；问题已由源码核实，无需重复采访 |
| triage category/state 标签投影 | GAP | 当前 typed broker 仅 lifecycle/classify/extension，无 triage mutation；没有尝试越权、直连 API 或冒用标签 |
| check-change-documents --porcelain / resolve-documents 427 | PASS | change-documents、change-pr-url 均 PASS；四个映射 basename 正确 |
| type/platform + complexity/complex 投影与独立读回 | PASS | classify plan→--apply→--verify，result=projected；wrapper 的 merged summary 固定措辞不表示本地草稿已合并 |
| broker lifecycle set spec-review | PASS | after=[complexity/complex,spec-review,type/platform]；未设 approved |
| AC/Txx/精确范围预检 | PASS | 8 AC、5 pending tickets、线性依赖、37 个唯一 git_scope；exact Issue/branch、四文档映射与两确认点一致 |
| T01–T05 实现测试 / 完整 smoke | NOT RUN | 本轮未实施 |
| required CI / installed / live / provider fresh session | NOT RUN | 未 push、安装或现场执行 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | T02 待实施 |
| AC-2 | NOT RUN | T03 待实施 |
| AC-3 | NOT RUN | T03 待实施 |
| AC-4 | NOT RUN | T04 待实施 |
| AC-5 | NOT RUN | T04/T05 待实施 |
| AC-6 | NOT RUN | T01/T03/T04/T05 待实施 |
| AC-7 | NOT RUN | T01/T05 待实施 |
| AC-8 | NOT RUN | T05 待实施 |

## 每票执行与范围证据

本节是现有 verification 的增量，不另建状态权威。每票执行时记录：
Issue/Txx、provider/实际入口及 pin、branch/owner、plan 摘要、ticket_base、起始 staged/unstaged/untracked、授权范围；
实际命令/Expected/结果、commit 清单、candidate_head、净 diff、遗漏处置；
Standards/Spec 的共同 BASE/HEAD、实际模型/强度/上下文和 findings 的 fixed/residual/new。
缓存仅辅助恢复，不能凭 complete 文本宣告验收。整批审查另用 change_base。

T01 治理提交与 STOP：NOT RUN。fresh run 重读与 session/head：NOT RUN。

## 合同准备只读预检

本次两个 Codex 只读调查者审阅四文件；这不是 Claude 实现终审，也未运行实施测试。

| Finding | 结论 | 处置 |
|---|---|---|
| C1：原版 SP 还会写 sdd scratch，不能声称只写 aisoft 缓存 | fixed / 复核闭合 | spec D2 / plan T03 区分两目录，绑定身份、路径与清理归属，不改 vendor |
| C2：计划全文 hash 会因合法状态更新失效 | fixed / 复核闭合 | 原始审计摘要与语义恢复摘要分开，规定排除范围；正常补证可恢复/语义改变拒绝均有用例 |
| F6/治理/证据边界预检 | PASS | AC-4/5、N5–N8、STOP/fresh run、small/SP 与 installed 非目标均无阻断缺陷 |

未来若实施变化，不能把本节合同预检当作实现 PASS。

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 实施终审 | Codex | Claude Code Fable 5 / high（实际调用待记录） | 待实施候选 | NOT RUN | 研究方案 SUPPORT 不替代本票实现终审 |

## 遗留风险与未完成项

- 本轮只交付合同候选，未证明任何新 runtime 行为或安装采用。
- triage 标签 mutation 缺少现有 typed 入口，语义结论与未投影事实均已保留。不得以 needs-analysis/spec-review/approved 冒充 triage 状态；该既有工具缺口不夹带为本票 broker 扩权。
- fixture 可以证明固定源码调用链，不能证明当前 Codex 6.4.2 插件与平台 7.0.0 等价；实际来源必须分层。
- 本轮不部署，故无部署验收章节；后续未运行的实现/CI/真实会话项保持 NOT RUN。
