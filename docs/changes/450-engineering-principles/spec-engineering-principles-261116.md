---
issue: 450
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/450
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
git_scope:
  - docs/changes/450-engineering-principles/summary-engineering-principles-261116.md
  - docs/changes/450-engineering-principles/spec-engineering-principles-261116.md
  - docs/changes/450-engineering-principles/plan-engineering-principles-261116.md
  - docs/changes/450-engineering-principles/verification-engineering-principles-261116.md
  - docs/changes/450-engineering-principles/proposals/engineering-principles.patch
  - skills/aisoft-platform/references/engineering-principles.md
  - usage/bundle.json
  - docs/governance/review-evidence-index.md
branch: change/450-engineering-principles
created: 2026-11-16
updated: 2026-11-16
---

# Spec：以结果和结构改进共享工程原则

## 目标与原因

在已有 Matt / superpowers 分工、路由和验证合同内，帮助方案、实现与审查更清楚地说明验证对象、证据来源和重复问题的处理方法。只细化共享工程原则，不另建工作流、技能或验证框架。

原方案拟改 spec 模板、execution-adapter 和共享原则三处。Herdr 中 Claude Opus 5.5 / high 独立审核后建议缩到共享原则一处；主会话逐项核对原文并澄清初审过度推断，收敛稿复核无阻断项。先前的方案审核不是对本次实际补丁的最终交叉审查。

### 授权与基线

- 2026-11-16 负责人明确：“同意，按收敛后的方案继续推进 #450，先补齐 spec 和 plan，语义改动只落在共享工程原则中。”本轮先完成合同；不因补文档自动应用治理 patch。
- 合同完整、文档预检 OK 后沿用上述同意推进本 Issue，不重复询问已确定的范围。最终 PR 仍按 confirm: 2，merge、安装、项目采用与部署不在此授权内。
- fresh broker fetch 后 `origin/main` 与本地主干均为 `c14a86d4ad0d1fd5938ab31343f8d72acd486a71`，作为 change_base。基线工作区干净。
- exact branch：`change/450-engineering-principles`；worktree：`/private/tmp/issue-450-engineering-principles`；唯一写者：Codex 会话 `01a1deda-7dba-7d80-8ce7-703794ceee24`。
- 无硬前置；#451 只是关联讨论，不依赖 Home Repo，也不修改其合同。

## 范围与非范围

### 唯一语义落点与冻结候选

仅修改 `skills/aisoft-platform/references/engineering-principles.md`：

1. 验收结果说明相关入口、前置条件及判断依据。
2. 按本次目标选择 Bug / 功能 / 重构 / 性能的验证关注点，不要求每项任务执行四类验证。
3. 区分审查者独立运行、实现方提供的结果与静态推导，保留未验证说明和证据层次边界。
4. 保留“实现 / 上下文 / 判断方法”的归因、按合同逐步改进及人的成本判断；先评估统一事实来源、边界或类型结构能否消除成因，再考虑确定性检查与文字约定，并考虑会被继续复制的错误范例。
5. 保留既有来源，在来源段补充已经阅读的 pstack 固定版本；不移植其执行指令。

精确文字以 [冻结 patch](proposals/engineering-principles.patch) 为准，零上下文格式，检查或应用使用 `--unidiff-zero`。本阶段只保存候选，不应用：

- 基线原则文件 SHA-256：`07c78311875b6c99a68a131d8b1adaf5894d8faf1cb02902e9335bd19983f456`。
- 应用后全文 SHA-256：`3dda609655418d22edffcd2cfb00468d4988416d24c0a5173fa99d2a1d9d1811`。
- patch SHA-256：`81d827200e282b69df16393b840439382d0b15ed737f04cbf2774cb611fc4efe`。

### 必要配套范围

- 本目录四份映射文档和冻结 patch 是本 Issue 合同与证据。
- 原则属于现有使用包成员。T01 使用现有 release 工具只在 `usage/bundle.json` 追加版本；不改 members 集合或已发布历史。当前从 1.24.1 追加 **1.24.2 / patch**：只是既有原则的澄清，无新增强制义务或接口变化。若 fresh main 占用了版本，只顺延到下一可用 patch，并同步本票证据，不改历史。
- `docs/governance/review-evidence-index.md` 仅追加本票实际最终交叉审查行。#450 没有路线图批次或 E2E / 项目采用事件，不改对应表。
- “一个语义文件”不等于最终只有一个 diff 文件；以上八个 exact 路径是全部 git_scope。

### 不纳入

不改 AGENTS.md、CLAUDE.md、技能入口、route-policy、execution-adapter、03 / 04 / 08、模板及其 digest、usage/CONTRACT、runtime、测试、CI、broker、安装器或部署脚本。不得补写这些文件来解决范围外问题。

不安装 pstack 或其他技能，不升级 vendor，不新增确认点、字段、状态、固定审查轮次、多模型竞赛、必用工具、功能地图文档、通用验证框架、项目试点或自动化引擎。不自动合并、不并行写同一 worktree、不重写已发表历史，不对真实 HOME 或下游项目安装 / adopt。

### 来源、覆盖与取舍

| 输入 | 已有覆盖 | 本票增量 / 不修改项 | 收益与成本 |
|---|---|---|---|
| pstack 的结果导向验证 | AC / Expected、可靠复现、风险相称验证和 NOT RUN 已存在 | 在原则中集中给出四类目标提示；不改模板，不让 spec 反向引用 Txx | 更易选对验证对象；增加少量阅读成本 |
| 证据与审查 | 原则与 verification 已要求证据对应结论 | 仅补“独立运行 / 实现方结果 / 静态推导”的来源区分 | 避免把转述当独立复核，不新增证据库 |
| 结构优先与 Code is memory | 已有简单设计、根因、范围聚焦和学习条目 | 保留归因维度，细化改进顺序，考虑错误范例的复制 | 减少重复叮嘱；结构调整须有实际依据，范围外另行处理 |
| 功能地图思想 | AC、Txx、Expected 已能承载用户结果 | 只补入口、条件和失败结果，不建地图文档 | 复用现有载体，避免同步成本 |
| 团队工具、统计与自动化 | 现有工具分工、人工合并及证据边界 | 不引入 Dune 策略、TLA+ / Lean、token 配额或自动合并 | 保持平台独立；不声称来源案例效果已在本平台复现 |

输入为 pstack `cursor/plugins` commit `bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7`（0.15.42）及用户提供的 [Lauren Tan 视频总结](https://app.notion.com/p/Agent-Lauren-Tan-41a55a8cd92e81a1a2dbed1d511b244d?source=copy_link)。主会话读完 Notion 九节，Claude 只读主会话归纳；未独立观看原视频或核验统计。文章转述链路保留在本票证据，不把私有阅读记录写成视频原始证据。0.47% 是 commits reverted，不是缺陷率；约 70% 验证 token 不是本平台预算要求。

## Acceptance criteria

- [ ] AC-1：实际原则全文与冻结候选 SHA-256 一致；引言“不增加确认点、流程状态或验证硬门”及原有非目标条目保留；来源如实。
- [ ] AC-2：场景与反例审议能说明四类提示只服务于本次目标，不新增验证文档、测试、轮次或工具义务；Matt / superpowers 分工和现行 route 不变。
- [ ] AC-3：证据表述区分独立运行、引用结果、静态推导与未执行；可靠静态发现不会仅因没运行被丢弃，必要验收没证据时不能宣布通过。
- [ ] AC-4：学习条目保留归因与成本维度，结构优先是评估顺序，不授权清理无关代码、任意抽象或自动修改治理规则；缺数据不声称效果提升。
- [ ] AC-5：bundle 只追加新 patch release，既有历史及 members 集合不变；隔离导出的 Codex / Claude / Cursor reference 与源码字节一致；真实安装与项目采用保持未执行。
- [ ] AC-6：exact scope、文档预检、既有完整 smoke、反向验证和实际候选的跨提供者独立审核通过；治理步骤独立 commit 后 STOP，fresh run 重读后继续，最终停在 PR 确认前。

## 场景与反例

| 场景 | 沿用现有流程与拟议提示 | 必须排除的误读 |
|---|---|---|
| 页面清空筛选后没有恢复结果 | 先确认既有合同与触发路径，按实际风险判级；在固定数据、入口和前置条件下检查结果。回归检查区分原错误与正确行为，required CI 可重放的证据沿用原记录方式 | 不是每个 Bug 都新增 verification，也不要求每项任务都做四类验证 |
| 两个调用方抽取共同排序逻辑 | 跨模块按 complex，用 Txx 覆盖两个调用方的输入、相等项、边界与副作用；只测新函数不能证明两端行为均保持 | 不把“测试全绿”等同用户目标已证明；逐票 Matt 审查不扩成 SP 的每票义务 |
| 审查者无法运行页面 | 分别写出实现方测试结果、审查者静态依据和页面 NOT RUN；充分静态发现可保留，必要页面验收仍缺证据 | 既不把转述当独立运行，也不因没复现抹掉可靠风险 |
| 旧计时器补丁被反复复制 | 在当前范围内分析共同成因，评估结构、检查或约定的成本；无关旧代码另记 | 不引入计时器 / useEffect 全局禁令，不因重复固定次数自动改规则 |

上述是文本合同审议，不是新增项目试点或实际模型实验。Bug 的交付按项目当前 route 的 confirm 值和 typed 入口执行；项目来源使用 aisoft-access，站点来源使用 broker。规划期风险放在已有 spec 风险段；执行后依当前合同的执行证据或遗留风险位置记录，不为补记录回改影响执行身份的已批准合同。

## 风险与回滚约束

- 主要风险是把指导读成统一硬门、扩大结构改造或误报证据独立性；由冻结文字、反例审议和实际新 HEAD 审核核对。
- verification 判据继续用 03 §3：diff review + required CI 可复现的证据不额外制造记录义务，真实环境或一次性观察按原规则处理。此解释只属于本 spec，不复制进原则正文。
- 一处 reference 仍是治理类 complex。R3 成本包括完整 spec / plan、full+reverse-proof、cross-provider 以及治理 STOP / fresh run；不能以改动行数少跳过。
- 本机生效和项目采用需要各自授权及验证；源码或隔离导出通过不能写成 installed / live PASS。
- 未发布候选可通过本分支追加 revert 提交回退。合并后用新 Issue / PR 恢复原则增量并追加修正版 bundle；不删除或改写已发布历史，不自动改变项目 pin。
- 效果仅在自然发生的后续审查中观察遗漏、误报、返工和人工纠偏；已有时间数据可参考，不新增计时表、固定 N 张 Issue 或观察门，也不把“文字已交付”当成缺陷率下降。

## 接口、数据与兼容性影响

无 API、schema、运行时接口、依赖或数据迁移。使用包格式和成员集合不变；项目继续 pin 原版本，只有获授权采用新版本才获得新文字。未修改模板，因此不刷新 change-template-sync digest 或其夹具。

## 未决问题

无需要重新裁决的范围问题。负责人已同意收敛方向与本轮合同补齐；具体候选见冻结 patch。后续发现实质范围变化、授权冲突或新的可靠反证时按既有合同升级。
