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
updated: 2026-10-25
git_scope:
  - docs/changes/430-greenfield-planning/summary-greenfield-planning-261024.md
  - docs/changes/430-greenfield-planning/spec-greenfield-planning-261024.md
  - docs/changes/430-greenfield-planning/plan-greenfield-planning-261024.md
  - docs/changes/430-greenfield-planning/verification-greenfield-planning-261024.md
  - skills/aisoft-platform/references/greenfield-planning.md
  - skills/aisoft-platform/SKILL.md
  - skills/issue-session-flow/SKILL.md
  - skills/aisoft-platform/references/getting-started.md
  - usage/USER-GUIDE.md
  - usage/CONTRACT.md
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - usage/bundle.json
  - docs/governance/review-evidence-index.md
---

# Spec：全新项目需求发现与滚动阶段规划

## 1. 目标与授权

AISoftPlatform 已覆盖新用户 onboarding、已有项目导入、单 Issue 开发及自动化部署。全新项目在“有想法”与“出现可批准的开发 Issue”之间，还需要统一的问题发现、阶段路线图与逐步细化方法。

本票补齐这段通用方法，保留 Matt 和 `issue-session-flow` 的既有路线图基线。核心尺度是：**当前阶段详细，下一阶段有轮廓，远期保留方向**。先暴露影响近期工作的全局约束，避免把未知远期需求写成已确定的详细设计。

2026-10-25 负责人要求按 Claude 两轮评估意见修订本合同，owner 审阅并补跑 grill-me 后，负责人明确确认修订合同。获准由 Codex 固定修订、同步 Issue 并读回，设为 approved 后启动 T01；治理文件提交后停止，由 fresh run 继续。确认点 2 前不 push、不建 PR。以下为已确认的交付合同，实施结果另记 verification。

## 2. 入口与适用边界

| 输入情形 | 本方法输出与转接 |
|---|---|
| 只有想法、尚未登记仓库 | 本方法不在登记与使用发布包采用之前启动。想法阶段只写用户自己的本地笔记，只用当时本机实际可用、不依赖 tracker 的能力（Claude 已装 Matt 插件时可用 grill-me；Codex、Cursor 在采用前没有 Matt 与平台技能，用普通对话整理）；不配置 Local-markdown/.scratch tracker，不运行 to-spec、to-tickets、triage 或 wayfinder。按 getting-started 完成登记和采用（可以先是空仓）后，由首张规划 Issue 把笔记整理进项目规划入口 |
| 已有需求文档或方案，但无可维护实现 | 提取已有结论及证据，标记冲突与未知，补当前阶段缺口；不重复全量访谈，也不把旧方案自动当成已批准合同 |
| 小型、单阶段新项目 | 可把简报、路线图和阶段记录放在一个文件的三个短节；只有一个 Issue 时直接走 Issue 会话，不强制调度会话 |
| 多领域、多个阶段的新项目 | 简报与必要全局边界相对稳定；仅展开当前阶段，复用现有多 Issue 调度路线图 |
| 已有代码或已交付项目的增量需求 | 转现有项目导入/对齐或 Issue 流程；不以“新项目”名义重置已有合同和证据 |

`change_control` 由负责人在登记时按 manifest 选择，本方法不推荐也不修改它。接入验收顺序按 onboarding-runbook，不由本方法改变；需要应用代码才能完成的验收项，在路线图中作为首阶段的退出证据引用。技术栈、交付形态等不可逆选择落到 `usage/CONTRACT.md` §4 的扩展点（项目 `AGENTS.md`「项目事实」、`.aisoft/architecture.json`），规划资料只放指针。

平台仓只保存通用规则与模板。具体业务研究、用户资料、领域模型、项目路线图和阶段内容留在对应项目仓。不得把业务材料写入平台技能或全局记忆来充当项目事实源。

## 3. 分层与权威来源

采用“项目 → 阶段 → Issue → Txx”。本文的“阶段”指规划阶段，与 `issue-session-flow` 中的“阶段”同义，不是 03 中 `change_control: development` 的“交付阶段”。阶段编号用于引用和恢复，不取代 Issue 主键，不成为新的授权对象。

项目规划只有一个入口文件，指向简报、路线图和当前阶段记录。入口路径登记在项目 `AGENTS.md`「项目事实」的「项目规则」条目（建议默认 `docs/planning/README.md`），采用发布包时填写项目事实即一并填写。已采用的项目由首张规划 Issue 补写：`AGENTS.md` 是约束本次运行的治理文件，该 Issue 按 `usage/CONTRACT.md` §2 判 complex，并按 onboarding-runbook §6 只生成 proposal，由独立受控治理步骤应用。跨会话恢复只从项目 `AGENTS.md` 出发找到入口。规划资料不放在 `docs/changes/` 下。不引入机器 schema、新 resolver role 或必填 summary 字段。

| 资料 | 最小内容 | 权威边界 |
|---|---|---|
| 项目简报 | 谁遇到什么问题；证据来源及日期；预期价值与可观察指标；范围/非目标；约束；关键假设和待验证事项 | 描述项目方向与事实，不批准任何 Issue 实施 |
| 项目路线图 | 稳定阶段 ID、名称、结果目标、范围轮廓、依赖、关键未知、退出证据、阶段状态、关联 Issue 链接与证据指针 | 阶段视图；每张 Issue 的状态只以该 Issue 为准，阶段行只链接、不复述 Issue 状态 |
| 当前阶段记录 | 阶段目标、输入事实、范围/非目标、设计决定指针、尚未验证的假设、验证方式、Issue 切分与依赖、阶段结果和调整理由 | 记录跨 Issue 的阶段决策与假设；术语、架构决定与业务规则按下文落点链接，不存副本 |
| 各 Issue 合同 | small 与 development complex 以 Issue 正文 AC 为合同（development complex 用合成 T01，没有 plan 文件）；production complex 以映射 spec/plan 为合同；verification 按现行义务产生 | 不复制为阶段级任务表；Txx 只存在于所属 Issue 的 canonical plan |

已接受的决定按项目 `docs/agents/domain.md` 的落点保存：术语写 `GLOSSARY.md`，架构决定写 `docs/adr/`，业务规则写相关产品或变更合同（通常是 Issue 合同）。简报与阶段记录只链接它们。出现冲突以 Issue 合同和实际证据为准。

**写入路径。** 规划资料只经普通项目 Issue 写入。首张规划 Issue 创建简报、路线图和阶段记录；阶段内调整与阶段结果由专门的规划或收口 Issue 写入，并列进其 git_scope。多 Issue 阶段中的实现 Issue 不改规划资料，只在自己的合同里链接阶段记录。只有一张 Issue 的小型项目或阶段，由该 Issue 兼作规划 Issue：规划文件列进其 git_scope，简报、路线图、阶段记录与阶段结果随同一 PR 写入。调度会话只起草文字，并把确认后的起草稿写进承载它的那张规划 Issue 的正文，不只留在会话里；阶段记录合并之前，同阶段的其它 Issue 把那张规划 Issue 列为依赖。`GLOSSARY.md` 与 `docs/adr/` 的写入同样只发生在拥有它的 Issue 的 change worktree 内。

## 4. 需求发现与滚动规划方法

### 4.1 从问题开始

从现有材料和用户已确认方向开始，用 Matt `grill-me` 补影响决策的缺口：实际使用者、当前工作方式、主要困难、期望结果、成功指标、不能做什么、必须遵守的约束。区分“有来源的事实”“负责人决定”“尚未验证的假设”。用户已经回答的问题直接引用，不强制重新走固定问卷。

访谈深度按 §4.2 收口：当前阶段问到底；下一阶段只问到「需要明确」一列；远期分支不再追问，写成 §4.2 的假设行。访谈确认后，按 reference 模板写出简报、路线图和阶段记录（经 §3 写入路径），这一步才算持久化。

证据不足时记录最小调查或可行性验证及其结果判据，安排到当前或后续阶段。原型、调研或技术验证一旦涉及受管仓库实施，也遵循现有 Issue 合同；“探索”不是绕过授权的名称。

### 4.2 三种规划深度

| 时间范围 | 需要明确 | 可以保留未知 |
|---|---|---|
| 当前阶段 | 可观察目标；范围与非目标；关键设计及跨模块接口；当前依赖/风险；退出证据；Issue 切分（每张 Issue 可测的 AC 草案与依赖，完整合同在各 Issue 会话按其路由产出） | 不影响本阶段边界的后续细节 |
| 下一阶段 | 只展开紧接的一个阶段：目标、主要能力、对当前阶段的依赖、关键未知、进入前要补的证据；转为当前阶段之前不为它的交付范围建 Issue，进入前要补的证据作为当前阶段的发现/验证 Issue 安排 | 详细设计、任务拆解、具体工期和完整 Issue 清单 |
| 远期 | 方向、业务结果、关键约束或可能依赖 | 顺序、完整需求、方案、任务、日期承诺 |

一个阶段对应一个可由退出证据验证的可观察结果，通常就是一张调度路线图。阶段边界由 AI 提议、负责人确认，记为“负责人决定”，不是审批状态。

初始跨阶段设计只处理当前必须知道的系统边界、核心领域语言、数据所有权、权限/隔离边界、外部接口及不可逆选择；已接受的结论按 §3 落点保存，并记录理由、适用前提和复核触发条件。其余采用可修订假设，不提前设计所有服务或全部数据库。

每个关键未知记录一行假设：“假设—影响—验证所在阶段—证据/结果—失效时受影响范围”。当前阶段无法在未知下安全界定时，先安排有退出判据的发现/验证工作；远期未知本身不阻止独立的当前工作。

### 4.3 当前阶段展开到交付

先对整个阶段澄清需求，再按可验证结果拆 Issue。拆分是调度会话按 `issue-session-flow` 提出的路线图建议；每张 Issue 按 `issue-session-flow` 经 broker `gitea.issue.create`（带入口标签）逐张创建，正文写 AC、依赖和规划入口/阶段记录链接。单 Issue 直接进入其会话。

每条 Issue 独立判级与查路由。production complex 按 Matt `to-spec → to-tickets` 形成可确认合同，再选择该 provider 的执行入口；small 与 development complex 保持现行简化规则，包括 development 的 Issue AC 与合成 T01，不因有项目路线图而强制补完整 spec/plan。子 Issue 的路由卡以 `aisoft resolve-route` 的输出为准（该工具目前不读取 G1 的第三个条件）；G1 的语义以 route-policy 为准，本方法不另作解释，需要澄清时另立 Issue。Issue 会话先读阶段记录，再按路由做 grill-me 与 to-spec。

项目 brief、路线图、阶段草案不授予自动建仓、批量建 Issue、派发新会话、实施或部署权限。实际动作按已有工具能力、用户指令和平台合同执行。下一阶段何时转为当前阶段由负责人决定；§4.2 的进入证据与 §4.4 的结果是决定依据，不是闸门，转换可以与仍在收尾的独立 Issue 重叠。转为当前后按 `issue-session-flow`「何时开调度会话」的第一种情形处理；没有新增“阶段批准”闸门。

### 4.4 阶段结果与调整

阶段结果同时核对：各 Issue 的真实状态与证据、跨 Issue 的接口/集成结果、阶段目标所需的业务或技术观察、仍未消除的假设。PR 合并、测试通过和部署可达分别记录，不能互相代替，也不能单凭 Issue 全关闭就声称阶段业务目标完成。

用结果更新路线图：保留阶段 ID、调整原因、证据和受影响依赖。未批准的未来范围可以逐步细化；已经批准的 Issue 若受到范围、AC、架构/安全边界变化影响，经 broker `gitea.issue.comment` 在该 Issue 上评论记录，不改其正文，由该 Issue 自己的会话停止受影响部分，按既有合同冲突/范围变更机制处理；调度会话不改它的合同或 worktree。无关的独立 Issue 可继续，不借一次调整重新批准全部项目，也不静默改已批准合同。

跨会话恢复按 §3 从项目 `AGENTS.md` 找到入口，再读当前阶段、其 Issue 原始合同、最新证据与未决项。会话聊天和技能包内部缓存不能成为唯一依据。

## 5. 技能选择与既有流程衔接

本方法的规划与编排只使用下表列出的技能。本机或项目里可见的其它规划、编排技能包，尤其会自建项目、阶段或计划状态的，不是本方法的工具；要用须另立适配 Issue。每张 Issue 内部的技能选择照 route-policy，不在阶段记录另记。

| 职责 | 本票采用的衔接 |
|---|---|
| 问题发现、阶段需求澄清 | Matt `grill-me`，按 §4.1 深度收口；需要第三方回答的事实用 `to-questionnaire`，一手资料核查用 `research`，产物与阶段记录放在一起并由其链接 |
| Issue 内的方案、规格和任务图 | 照 route-policy「默认入口」与该 Issue 的路由，本方法不复制；`to-tickets` 只在一张已存在的 Issue 内运行，不对简报、路线图或阶段记录运行 |
| 多 Issue 协调与恢复 | `issue-session-flow` 现有路线图、依赖、会话和单写者规则 |
| 执行、完成核验与审查 | route-policy 的 provider 映射；平台 complex 的最终独立审查规则保持 |
| Matt `wayfinder` | 不是本方法的入口，虽然 Matt `ask-matt` 把全新项目指向它；其地图与 child Issue 仍按项目 `docs/agents/issue-tracker.md`「Wayfinding and multi-Issue mode」；接入前不得用它的 .scratch 地图替代项目规划入口 |

`grill-me`、`to-questionnaire`、`to-spec`、`to-tickets` 只能显式调用。USER-GUIDE 写明用户在三种工具里如何启动规划访谈。

Spec Kit、GSD、gstack 只作为本票文档记录的未来候选：本票不安装、调用、pin、vendor、适配或试点，这份候选清单也不写进下发的 reference。即使本机已可见（例如 Codex 落点里的 gsd-* 技能），也不代表获准使用。

本方法引用 `engineering-principles.md` 的通用原则（事实、假设与决定分开，不为假想的未来设计，证据分层），只补阶段专属规则，不复述。

## 6. 拟交付物与精确改动边界

1. 新增 `skills/aisoft-platform/references/greenfield-planning.md` 作为方法唯一来源，包含入口分流、上述规则和三份最小资料的内嵌模板（只用占位值）；模板可以组合为单文件。本 reference 只写阶段规划专属做法，不新增 Matt 通用用法约束。
2. `aisoft-platform/SKILL.md` 在「接入新项目 / 项目对齐 / 私有访问」加一行指针，在「外部技能包边界」加一句指向本 reference 的指针（不是新的成对规则，`aisoft-matt-workflow` 不变），并在 description 追加“全新项目、新项目规划、阶段路线图”触发词（不改 `agents/openai.yaml`）。`issue-session-flow/SKILL.md` 在「何时开调度会话」加一句指针，并删去指向维护层 `docs/governance/remediation-roadmap.md` 的路径，保留行内列名。getting-started 在登记与采用之后加规划入口，以及在 AGENTS「项目规则」登记入口的一句。
3. `usage/USER-GUIDE.md` 在「第一张 Issue 怎么走」之前加“新项目先规划”入口，写明三种工具如何显式启动 grill-me。`usage/CONTRACT.md` 在末尾追加 §8 两行指针（按 #423 的先例，不重编号既有小节，不进 §2 不变量）。03 在 §2.2「大需求链」可选加一句回链。不新增状态或执行引擎。
4. `--release` 之前先在 `usage/bundle.json` 的 members 登记新 reference（mode 为 skill），再按现行工具追加一个向后兼容 minor 版本，记录实际字节；现有 `aisoft-platform` 已覆盖 Codex/Claude/Cursor 分发，无须修改 skills.manifest 或安装器。版本号在 `prepare-ticket 430 T01` 之前按 fresh main 最新版本的下一 minor 确定，不能改已发布历史或抢占其他 Issue 的版本。之后若任一成员改动，删除本分支上尚未合并的本批 release 条目，以同一版本号重新 `--release` 并 `--verify`。
5. 本票四份文档及最终独立审查证据索引记录真实结果。旧整改路线图和平台 E2E 表没有本票对应运行事件时，不新增虚构“已部署/已采用”行。README §8 按 #420、#423 纯指导类变更的先例不新增行；本方法只有 source 级证据，真实项目的首次采用由该项目自己的规划 Issue 承载并验收。

front matter 的 `git_scope` 是最大允许集合（13 个文件），未需要的文件不改；不改 04、`aisoft-matt-workflow`、route-policy、AGENTS、模板。

编写时避开现有 smoke 守卫：
- 模板与示例只用占位值，不写项目名、站点值或交付形态名；占位不用 myapp、smoke-test，示例不含平台主机名或负责人账号子串（大小写不敏感）；SKILL.md 与 CONTRACT 不出现 compose、pm2、iis 子串（含 decompose 这类词）。
- 活文档禁用短语（如“开发与设计”“维护与部署”）一律不用。
- SKILL.md 不写 provider 专有工具名；Claude 落点 SKILL.md 中的 `$名称` 只能是 Matt 技能名。
- 不改 03 标题与「现行合同」行。
- 跑完整 smoke 之前先 `git add` 新 reference，因为项目泄漏检查只扫已跟踪文件。

本轮合同准备实际只写本票四份文档。未来实现发现需要范围之外文件，先记录真实原因并按既有合同变更处理。

## Acceptance criteria

- [ ] **AC-1 入口分流**：从想法、已有方案、单阶段、多阶段、已有代码五种输入都能找到明确的规划或现行对齐路径；想法阶段在登记与采用之前只产出用户本地笔记并转接 onboarding，未接入不被当成已接入。
- [ ] **AC-2 滚动深度**：方法及模板清楚区分当前/下一/远期，下一与远期无强制详细任务或工期承诺；当前具有结果、范围、设计边界和退出证据；访谈深度按 §4.1 收口。
- [ ] **AC-3 单一事实源**：最小三种资料可合并、可引用已有材料；项目入口唯一，并可从项目 AGENTS.md「项目规则」发现；规划资料只经 Issue 写入，多 Issue 阶段中的实现 Issue 不改它；Issue/Txx 仍唯一交付身份，路线图不复制授权、任务图、Issue 状态或 resolver roles。
- [ ] **AC-4 必要全局边界**：覆盖跨阶段数据/权限/接口及不可逆选择，已接受的决定落在 GLOSSARY.md、docs/adr/ 或 Issue 合同；关键假设具有影响、验证阶段和证据，当前未知与远期未知的处理不同。
- [ ] **AC-5 现行路由兼容**：阶段澄清与拆 Issue 可追踪到 Matt 和 issue-session-flow；production/development、small/complex 与三 provider 的现有路由不改变，子 Issue 路由以 resolve-route 输出为准，不新增确认点。
- [ ] **AC-6 阶段结果与变化**：有跨 Issue 结果核验、证据分层、调整原因和依赖影响；已批准 Issue 的变化以评论记到该 Issue 并由其会话按既有合同处理，合并不被当成业务验收。
- [ ] **AC-7 技能边界**：规划与编排只用 §5 表列出的技能，wayfinder 的位置明确，Matt 基线保持；没有新增技能包安装、调用、pin、vendor、自动运行或第二编排状态。
- [ ] **AC-8 跨会话恢复**：只从项目 AGENTS.md 出发，依据项目入口、阶段记录和关联 Issue 即能恢复当前/下一阶段、未知与证据，不依赖聊天历史或某个模型专有缓存。
- [ ] **AC-9 分发与兼容**：新 reference 进入三工具隔离导出，字节与源一致，受改技能按既有目标分发；release append-only，版本号依据实际基线确定；未修改真实用户技能目录或项目 pin。
- [ ] **AC-10 反向核验**：正反场景均有真实 source/local 检查记录；文档检查、路由解析、使用包验证和现有 smoke 通过或如实记录阻塞；检查没有新增状态/确认点/runtime/外部包接入。
- [ ] **AC-11 治理受控应用**：T01 治理 commit 前的本地检查（含完整 smoke）通过；commit 后 STOP，fresh run 重读后才继续。
- [ ] **AC-12 最终独立审查**：最终实际 diff 由未参与实现的另一方只读审查并记录 finding；用户的前置 Claude 合同评估不替代最终审查。

## 8. 风险、回滚和非目标

风险是把滚动规划写成另一套大而全流程、把阶段视图当新的授权或任务系统、或只更新维护层而遗漏项目可分发内容。通过最小模板、单一 reference、现行路由指针、场景反例与隔离导出检查控制。

若方法需回退，按新的受管修正/revert Issue 和使用发布包版本交付；不改写已发布历史，不自动回退下游项目 pin，不删除项目既有规划资料。下游采用或回退仍经项目自身 Issue/PR。

本票会话不运行安装器；合并后由负责人按 `issue-session-flow`「平台仓重装读回（维护层）」重装，会话读回漂移与 readiness，未运行写 NOT RUN。

无数据库、业务 API、runtime、CLI、broker、CI/部署脚本、路由枚举、标签 schema、AGENTS.md 或外部包版本变更。无新技能包集成、真实业务项目 pilot、全局安装、下游自动采用、合并、部署或 UAT。本票不是特定业务项目的需求咨询交付。

## 9. 合同评估记录

Claude 已于 2026-10-24 完成内部材料评估，并于 2026-10-25 做反证复核（7 个只读核对）与修订稿复核（4 个只读核对），本版已吸收其结论；修订映射见 verification「合同修订」行。前置评估不是实施授权，也不替代 AC-12 的最终实现审查。

## 未决问题

- 负责人于 2026-10-25 明确选择补跑 `grill-me`，已有结论直接沿用。owner 会话已完成一次决策树核对，新增待决问题为 0；记录见 verification「grill-me 补跑记录」。负责人随后明确确认完整修订合同，保留原 route.skills 与空 override_reason。当前无影响实施方向的未决项；批准与启动证据见 summary/verification。
