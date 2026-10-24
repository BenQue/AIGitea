---
issue: 430
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/430
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
branch: change/430-greenfield-planning
created: 2026-10-24
updated: 2026-10-24
git_scope:
  - docs/changes/430-greenfield-planning/summary-greenfield-planning-261024.md
  - docs/changes/430-greenfield-planning/spec-greenfield-planning-261024.md
  - docs/changes/430-greenfield-planning/plan-greenfield-planning-261024.md
  - docs/changes/430-greenfield-planning/verification-greenfield-planning-261024.md
  - skills/aisoft-platform/references/greenfield-planning.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-matt-workflow/SKILL.md
  - skills/issue-session-flow/SKILL.md
  - skills/aisoft-platform/references/getting-started.md
  - usage/USER-GUIDE.md
  - usage/CONTRACT.md
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 04-Agent编排与定时任务.md
  - usage/bundle.json
  - docs/governance/review-evidence-index.md
---

# Spec：全新项目需求发现与滚动阶段规划

## 1. 目标与授权

AISoftPlatform 已覆盖新用户 onboarding、已有项目导入、单 Issue 开发及自动化部署。全新项目在“有想法”与“出现可批准的开发 Issue”之间，还需要统一的问题发现、阶段路线图与逐步细化方法。

本票补齐这段通用方法，保留 Matt 和 `issue-session-flow` 的既有路线图基线。核心尺度是：**当前阶段详细，下一阶段有轮廓，远期保留方向**。先暴露影响近期工作的全局约束，避免把未知远期需求写成已确定的详细设计。

当前仅获准创建 Issue 与准备本 spec/plan。以下内容是拟批准后的交付合同，尚未开始实施。用户将自行组织 Claude 结合平台内部材料评估；本票不自动调用模型或向另一会话发送材料。

## 2. 入口与适用边界

| 输入情形 | 本方法输出与转接 |
|---|---|
| 只有想法、尚未登记仓库 | 可先形成可迁移的需求草案；不视为已接入平台。进入受管仓库写入、Issue 实施前完成现有 onboarding 和权限核对 |
| 已有需求文档或方案，但无可维护实现 | 提取已有结论及证据，标记冲突与未知，补当前阶段缺口；不重复全量访谈，也不把旧方案自动当成已批准合同 |
| 小型、单阶段新项目 | 可把简报、路线图和阶段记录放在一个文件的三个短节；只有一个 Issue 时直接走 Issue 会话，不强制里程碑或调度会话 |
| 多领域、多个阶段的新项目 | 简报与必要全局边界相对稳定；仅展开当前阶段，复用现有多 Issue 调度路线图 |
| 已有代码或已交付项目的增量需求 | 转现有项目导入/对齐或 Issue 流程；不以“新项目”名义重置已有合同和证据 |

平台仓只保存通用规则与模板。具体业务研究、用户资料、领域模型、项目路线图和阶段内容留在对应项目仓；未建仓草案在接入时迁入项目的明确位置。不得把业务材料写入平台技能或全局记忆来充当项目事实源。

## 3. 分层与权威来源

采用“项目 → 可选里程碑 → 阶段 → Issue → Txx”。里程碑只在确有对外结果或多阶段目标时使用。阶段编号用于引用和恢复，不取代 Issue 主键，不成为新的授权对象。

项目规划只有一个明确入口，指向简报、路线图和当前阶段记录。可复用项目现有文档，不强制新目录；首次建立时记录实际路径，后续会话依该指针读取。模板内的路径是建议，不引入机器 schema、新 resolver role 或必填 summary 字段。

| 资料 | 最小内容 | 权威边界 |
|---|---|---|
| 项目简报 | 谁遇到什么问题；证据来源及日期；预期价值与可观察指标；范围/非目标；约束；关键假设和待验证事项 | 描述项目方向与事实，不批准任何 Issue 实施 |
| 项目路线图 | 稳定阶段 ID、名称、结果目标、范围轮廓、依赖、关键未知、退出证据、关联 Issue、进度和证据指针 | 是现有调度路线图的阶段视图；不另建第二份执行状态数据库 |
| 当前阶段记录 | 阶段目标、输入事实、范围/非目标、必要设计决策、验证方式、Issue 切分与依赖、技能选择依据、阶段结果和调整理由 | 记录跨 Issue 的阶段决策；各 Issue spec/plan/verification 仍是其合同与完成证据来源 |
| 既有 Issue 四件套 | summary/spec/plan/verification，按现行项目 change_control 和判级义务产生 | 不复制为另一份阶段级详细任务表；Txx 只存在于所属 Issue 的 canonical plan |

现有 `domain.md`、ADR、数据/接口说明有对应内容时直接引用，不生成平行副本。路线图展示的 Issue 状态须注明核对时间并链接原 Issue；出现冲突以 Issue 合同和实际证据为准。

## 4. 需求发现与滚动规划方法

### 4.1 从问题开始

从现有材料和用户已确认方向开始，用 Matt `grill-me` 补影响决策的缺口：实际使用者、当前工作方式、主要困难、期望结果、成功指标、不能做什么、必须遵守的约束。区分“有来源的事实”“负责人决定”“尚未验证的假设”。用户已经回答的问题直接引用，不强制重新走固定问卷。

证据不足时记录最小调查或可行性验证及其结果判据，安排到当前或后续阶段。原型、调研或技术验证一旦涉及受管仓库实施，也遵循现有 Issue 合同；“探索”不是绕过授权的名称。

### 4.2 三种规划深度

| 时间范围 | 需要明确 | 可以保留未知 |
|---|---|---|
| 当前阶段 | 可观察目标；范围与非目标；关键设计及跨模块接口；当前依赖/风险；退出证据；可批准的 Issue 切分和各自必要合同 | 不影响本阶段边界的后续细节 |
| 下一阶段 | 目标、主要能力、对当前阶段的依赖、关键未知、进入前要补的证据 | 详细设计、任务拆解、具体工期和完整 Issue 清单 |
| 远期 | 方向、业务结果、关键约束或可能依赖 | 顺序、完整需求、方案、任务、日期承诺 |

初始跨阶段设计只处理当前必须知道的系统边界、核心领域语言、数据所有权、权限/隔离边界、外部接口及不可逆选择；记录决定理由、适用前提和复核触发条件。其余采用可修订假设，不提前设计所有服务或全部数据库。

每个关键未知记录“假设—影响—验证所在阶段—证据/结果—失效时受影响范围”。当前阶段无法在未知下安全界定时，先安排有退出判据的发现/验证工作；远期未知本身不阻止独立的当前工作。

### 4.3 当前阶段展开到交付

先对整个阶段澄清需求，再按可验证结果拆 Issue。跨多个 Issue 时由 `issue-session-flow` 调度，沿用当前路线图表形和推荐顺序，不在调度会话实现任何 Issue。单 Issue 直接进入其会话。

每条 Issue 独立判级与查路由。production complex 按 Matt `to-spec → to-tickets` 形成可确认合同，再选择该 provider 的执行入口；small 与 development complex 保持现行简化规则，包括 development 的 Issue AC 与合成 T01，不因有项目路线图而强制补完整 spec/plan。当前阶段记录只链接这些合同，不另写一份 Txx。

项目 brief、路线图、阶段草案不授予自动建仓、批量建 Issue、派发新会话、实施或部署权限。实际动作按已有工具能力、用户指令和平台合同执行。下一阶段正式进入当前范围时，才补足其缺口并准备待批准的 Issue；没有新增“阶段批准”闸门。

### 4.4 阶段结果与调整

阶段结果同时核对：各 Issue 的真实状态与证据、跨 Issue 的接口/集成结果、阶段目标所需的业务或技术观察、仍未消除的假设。PR 合并、测试通过和部署可达分别记录，不能互相代替，也不能单凭 Issue 全关闭就声称阶段业务目标完成。

用结果更新路线图：保留阶段 ID、调整原因、证据和受影响依赖。未批准的未来范围可以逐步细化；已经批准的 Issue 若受到范围、AC、架构/安全边界变化影响，停止受影响部分，按既有合同冲突/范围变更机制处理。无关的独立 Issue 可继续，不借一次调整重新批准全部项目，也不静默改已批准合同。

跨会话恢复只需定位项目规划入口、当前阶段、其 Issue 原始合同、最新证据与未决项。会话聊天和技能包内部缓存不能成为唯一依据。

## 5. 技能选择与既有流程衔接

默认保留 Matt 的需求、方案和计划能力。先判断能力缺口，再在平台已允许、当前项目实际可用的技能中选择；记录用途、输入、输出落在哪个 canonical 文档及使用理由。不要求每个项目选一套新框架。

| 职责 | 本票采用的衔接 |
|---|---|
| 问题发现、阶段需求澄清 | Matt `grill-me`；吸收已有材料与已确认决定 |
| 必要技术方案 | Matt `to-spec` 方案节；how 未收敛或可行性存疑时才按现行默认选择已有辅助技能 |
| Issue 规格和任务图 | Matt `to-spec`、`to-tickets`，服从项目 change_control/路由 |
| 多 Issue 协调与恢复 | `issue-session-flow` 现有路线图、依赖、会话和单写者规则 |
| 执行与完成核验 | 读取 route-policy 的 provider 映射，不在新方法里另复制算法 |
| 质量和阶段结果核对 | 复用 Issue 验证证据及阶段目标所需观察；平台 complex 的最终独立审查规则保持 |

Spec Kit、GSD、gstack 的定位只记录为未来候选与评估问题，不在本票进行安装、调用、版本 pin、vendor 引入、命令适配、导入其状态目录或试点。即使本机已可见这些技能，也不代表本票获准使用。未来需要时另建能力缺口清晰、输出可回归到现有文档和交付流程的适配 Issue。

## 6. 拟交付物与精确改动边界

1. 新增 `skills/aisoft-platform/references/greenfield-planning.md` 作为方法唯一来源，包含入口分流、上述规则和三份最小资料的内嵌模板；模板可以组合为单文件。
2. 在 `aisoft-platform`、`aisoft-matt-workflow`、`issue-session-flow` 技能入口及 getting-started 增加必要指针与职责说明，不复制整套方法、不改外部技能原文。
3. `usage/USER-GUIDE.md` 展示用户从新项目想法进入规划的入口；`usage/CONTRACT.md`、03、04 仅解释项目规划与 Issue 层的关系并链接 canonical reference，不新增状态或执行引擎。
4. 将新 reference 加入 `usage/bundle.json` 的技能成员，并按现行工具追加一个向后兼容 minor 版本，记录实际字节；现有 `aisoft-platform` 已覆盖 Codex/Claude/Cursor 分发，无须修改 skills.manifest 或安装器。版本号取实施时 fresh main 最新版本的下一 minor，不能改已发布历史或抢占其他 Issue 的版本。
5. 本票四份文档及最终独立审查证据索引记录真实结果。旧整改路线图和平台 E2E 表没有本票对应运行事件时，不新增虚构“已部署/已采用”行。

front matter 的 `git_scope` 是最大允许文件集合，未需要的文件不改。本轮合同准备实际只写本票四份文档。未来实现发现需要范围之外文件，先记录真实原因并按既有合同变更处理。

## 7. Acceptance criteria

- [ ] **AC-1 入口分流**：从想法、已有方案、单阶段、多阶段、已有代码五种输入都能找到明确的规划或现行对齐路径；未 onboarding 不被当成已接入。
- [ ] **AC-2 滚动深度**：方法及模板清楚区分当前/下一/远期，下一与远期无强制详细任务或工期承诺；当前具有结果、范围、设计边界和退出证据。
- [ ] **AC-3 单一事实源**：最小三种资料可合并、可引用已有材料；项目入口唯一；Issue/Txx 仍唯一交付身份，路线图不复制授权、任务图或 resolver roles。
- [ ] **AC-4 必要全局边界**：覆盖跨阶段数据/权限/接口及不可逆选择；关键假设具有影响、验证阶段和证据，当前未知与远期未知的处理不同。
- [ ] **AC-5 现行路由兼容**：阶段澄清与拆 Issue 可追踪到 Matt 和 issue-session-flow；production/development、small/complex 与三 provider 的现有路由不改变，不新增确认点。
- [ ] **AC-6 阶段结果与变化**：有跨 Issue 结果核验、证据分层、调整原因和依赖影响；已批准 Issue 变化触发既有合同处理，合并不被当成业务验收。
- [ ] **AC-7 技能边界**：技能按能力缺口选择且记录文档归属；Matt 基线保持；没有新增技能包安装、调用、pin、vendor、自动运行或第二编排状态。
- [ ] **AC-8 跨会话恢复**：仅依据项目入口、阶段记录和关联 Issue 即能恢复当前/下一阶段、未知与证据，不依赖聊天历史或某个模型专有缓存。
- [ ] **AC-9 分发与兼容**：新 reference 进入三工具隔离导出，字节与源一致，受改技能按既有目标分发；release append-only，版本号依据实际基线确定；未修改真实用户技能目录或项目 pin。
- [ ] **AC-10 反向核验**：正反场景均有真实 source/local 检查记录；文档检查、路由解析、使用包验证和现有 smoke 通过或如实记录阻塞；检查没有新增状态/确认点/runtime/外部包接入。
- [ ] **AC-11 治理与评议**：T01 独立治理 commit 后 STOP，fresh run 重读后才继续；最终实际 diff 由未参与实现的另一方审查并记录 finding；用户的前置 Claude 合同评估不替代最终审查。

## 8. 风险、回滚和非目标

风险是把滚动规划写成另一套大而全流程、把阶段视图当新的授权或任务系统、或只更新维护层而遗漏项目可分发内容。通过最小模板、单一 reference、现行路由指针、场景反例与隔离导出检查控制。

若方法需回退，按新的受管修正/revert Issue 和使用发布包版本交付；不改写已发布历史，不自动回退下游项目 pin，不删除项目既有规划资料。下游采用或回退仍经项目自身 Issue/PR。

无数据库、业务 API、runtime、CLI、broker、CI/部署脚本、路由枚举、标签 schema、AGENTS.md 或外部包版本变更。无新技能包集成、真实业务项目 pilot、全局安装、下游自动采用、合并、部署或 UAT。本票不是特定业务项目的需求咨询交付。

## 9. Claude 内部评估材料与问题

按以下顺序阅读本票和主仓当前实际内容，必要时报告它们相对本票基线的差异：

1. 本 Issue 正文中的完整 spec/plan、summary 所列基线与当前授权。
2. `README.md`、`AGENTS.md`、`docs/adr/0001-platform-boundary.md`、`docs/adr/0002-deterministic-development-flow.md`。
3. `03-Issue-Spec-Plan与单闸门开发流程.md`、`04-Agent编排与定时任务.md`、`08-双工具共存与实施.md`。
4. `skills/aisoft-platform/references/route-policy.md`、`execution-adapter.md`；三个相关技能的 `SKILL.md`；getting-started、onboarding-runbook 与项目对齐参考。
5. `usage/CONTRACT.md`、`usage/USER-GUIDE.md`、`usage/bundle.json`、`skills/skills.manifest`；平台 pin 的 Matt manifest 与所选 `grill-me`/`to-spec`/`to-tickets` 原文。

重点判断：是否仍存在第二份状态/合同；三种规划深度是否足够具体；必要全局设计会否过度；development 与 provider 例外是否正确；阶段完成能否被证据支持；是否有隐式外部包接入；15 个允许文件是否必要且充分；隔离导出能否覆盖使用层。

评估输出建议为：结论、按严重度排序的 finding（引用本票条款与内部证据）、最小修订建议、未验证假设。只评估，不实施、不安装、不推送、不批量建 Issue，也不自行将状态设为 approved。评估结果由负责人带回本票。当前无必须预先再问用户的方向性未决项；新 finding 在批准前消解或明确收缩范围。
