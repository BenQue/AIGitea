---
issue: 268
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/268
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/268-delivery-loop-roadmap
created: 2026-09-06
updated: 2026-09-06
---

# 必要流程收口 → 公司 Gitea 与平台部署 → NewEMaint 闭环 → 流程沉淀

本文件是路线图事实源。方向确认来自用户 2026-09-06 的明确指令及其补充：公司内网 Gitea 和平台自身部署才是重要的第一环，然后才能是 NewEMaint 应用部署。具体实施须归各自 Issue。改名包括展示名称在内全部延期。本路线图不承诺未经确认的工期或现场窗口，按可验证的阶段出口推进。

## 1. 基线与现状

| 对象 | 2026-09-06 评估证据 | 使用边界 |
|---|---|---|
| 平台 | `main = 3fb6b605a59ce492ef4fb6ddcd3ebf64ca7f223a`；PR #267 head `9c49312b6901d333528b4e8c15812fa485739739`；CI run #1109 成功 | 必须在每个实施 Issue 开始前重新核对 |
| NewEMaint | `main = 0702bd34a41abb5e0f8df65aa2fd892cc6cb25a0`；PR #78 head `125180a8050c84393ae91843307f859138dcaad3`；CI run #1062 成功 | 最新 main 不等于公司已部署版本 |
| 历史 DockerLab release | `006d0c43cafebff058889e3338d1e8bdcc8b661c`；平台 pin `4e26ba063350579e7b2dfad633a2085e505243d0`，catalog `2026.08.3` | 历史 release 与最新主干需显式选择；固定 pin 下 lock 验证有效 |
| 本地与安装验证 | 699 个 Python tests 通过；122 个 change 文档门禁通过；`LC_ALL=C` 完整 smoke 通过；默认 Mac locale 的 registry 负向测试失败 | 不证明公司现场或真实 Docker lifecycle 通过 |
| 已完成维护 | Codex 安装 skills 后两侧 drift CLEAN；14 个旧平台 worktree 已安全清理 | 不重复清理；skills CLEAN 不等于 broker/VM 安装一致 |
| 公司内网 | 历史已有 Gitea 部分安装线索；正式 operator stage 尚未建立完整验收映射 | 现场当前状态 NOT RUN，先盘点接管，不能按空白主机重复安装 |
| 现有待办 | NewEMaint #18 MigrationBundle、#43 credential lifecycle、#74 vendored templates 仍 open | 先读 Issue 正文、评论、已有关联文档，再判定剩余工作，不重复立项 |

原评估及详细日志保存在本机：`/Users/benque/.codex/visualizations/2026/09/06/01a07591-511b-7d72-8471-391c85624938/platform-assessment/assessment.md`。本文件保留必要结论，不要求其他机器依赖该绝对路径才能理解路线图。原评估中“先改展示名”的建议已被用户最新指令覆盖，不再执行。

## 2. 阶段关系与完成定义

| 阶段 | 目的 | 进入条件 | 退出条件 |
|---|---|---|---|
| R0 路线图与调度 | 发布本路线图，建立调度任务 | 用户方向已确认 | 文档本地检查通过；新调度任务已接收；最终 PR/合并状态另列 |
| A 平台必要收口 | 公司 Gitea/平台先行交付及后续应用路径可执行 | R0 交接；对应 Issue 合同批准 | Gate A 全部满足 |
| B 公司平台首次落地 | 先完成公司内网 Gitea 与 AISoftPlatform 自身交付验收 | Gate A；平台现场交付合同和分阶段授权 | Gate B 全部满足 |
| C 应用首次闭环 | NewEMaint 在已验收的平台上完成实际交付 | Gate B；C1 的项目合同批准 | Gate C 全部满足 |
| D 实例驱动的流程化 | 用 B/C 的事实完善通用 onboarding/部署 | Gate C 和两轮复盘证据齐全 | Gate D 全部满足 |

阶段 B/C 的只读盘点、材料搜集和合同草案可与 A 并行。B 的现场执行不得越过 Gate A；NewEMaint 的部署执行（含路线图安排的非生产验收）必须等 Gate B，不能先以应用部署替代平台自身部署。D 的想法可记录，通用实现留到两个真实实例闭环之后。

### Gate A：先行平台交付所需流程闭合

- SCM/平台 bootstrap、平台自身部署、应用部署有独立入口和证据，不要求先取得 NewEMaint 镜像包才能开始公司 Gitea/平台部署；如当前 builder 不支持，必须先形成受控的独立交付合同。
- Stage 40/90 的恢复证据归属明确，不再要求不适用阶段填写虚假 PASS。
- 首次安装、升级、失败停止、回退基线均有可达的流程分支和停止条件。
- source SHA、release identity/digest、公司审批记录之间关系已选择并验证；保留原字节和可追溯性。
- 公司已有实例接管与空白安装明确分流；准入先识别现场资产与兼容版本。
- 与首发有关的 operator 版本、required CI、安装来源等文字一致；所选 transport 的必需依赖明确，裁剪须先改合同。
- 默认 macOS Bash/locale 回归通过；受影响的安装组件有 source/installed 版本及差异结论，必要升级经对应授权并读回。
- 平台自身 manual 开发/交付必需能力通过；可选 routine 能力明确禁用或阻塞，不能扩大权限消红。NewEMaint `HTTP_403` 先定位影响；仅应用特有的修复归 C1，不阻塞公司平台独立部署。
- 所需平台 Change 已人工合并、required CI 通过；下游选定稳定 pin/安装版本并验收。平台文档不是项目现场命令的事实源。

### Gate B：公司 Gitea 与 AISoftPlatform 自身已落地

- 公司实际实例和主机角色已经脱敏盘点；明确已有 Gitea 的采用/整改范围、访问入口、版本、数据与回退基线，不重复运行空白安装器。
- 公司 Gitea 可经批准的内网入口访问，选定认证/权限、备份及隔离恢复演练、健康和运维接手均有实际证据。已有 legacy 读取/改动受其独立 Change 约束。
- 平台项目本身的公司仓库已导入或接管：记录 repository identity、source refs/SHA、初始化信任来源、公司审批权威、受保护 main 和 required CI；bootstrap 安装与安装后的正常受保护 PR 流程边界明确。
- 有一份按 host role 的平台组件安装清单：开发侧 skills/AI 工具与公司确定性组件明确分开，公司只安装所需 guard、治理配置/profile、确定性 runtime/CLI、Runner 与所选 transport 支撑；broker 是否需安装及允许能力由现场合同逐项确定。注明安装位置/用途、source/installed provenance、验收或有依据的不适用；不等于全量安装八个 installer。
- 保留 `07` 的持续双权威模型：AI/Claude/Codex 和开发 Issue 留开发侧，公司内网只作部署权威且不安装或调用 AI；appserver-prod 不装通用 Runner 或源码构建器，只配置批准的角色/固定目标能力。未启用 provider/routine 合并的状态单列。
- 平台自身的可审计 canary 闭环完成：本地受控 Issue/变更 → 平台结果入站 → 公司 sync/审批 PR → required CI/verification → 人工合并 → provenance/readback；同时验证禁止 direct/force push 和最小权限边界。公司不复制本地 Issue/账号/PAT，不变成第二个开发权威。canary 使用平台部署合同内的真实安全变更，不靠 NewEMaint 应用部署证明。
- 所选安装步骤在隔离验证环境两次复跑、故意失败/停止/恢复验证通过，现场安装/采用有前后读回、回退记录与运行观察。部署批准是 exact 公司环境/版本/脚本/范围，不继承本路线图批准。
- 本 Gate 的事实记录归平台自身的部署 Change；NewEMaint 只引用已通过的平台基线。Gate B 未通过时，应用部署状态保持 BLOCKED。

### Gate C：NewEMaint 公司内网真实闭环

- 项目合同确定目标环境、业务范围、版本、责任人、数据边界、验收指标和发布窗口；范围内阻断项有证据闭合。
- NewEMaint `HTTP_403` 已定位到确切 operation/端点；应用 manual 开发/发布必需能力通过，可选 routine 明确状态。
- 测试过的不可变制品经已批准的身份映射进入公司流程，digest 读回一致，审批/required CI/部署证据指向明确版本。
- 非生产完成两次可重复部署、一次故意失败的停止/回退、A→B→A 应用版本切换，以及独立的数据库与 uploads 恢复/核对。备份存在不能代替恢复通过。
- 数据迁移/旧文件搬迁在所选发布范围内完成彩排、对账和撤回验证；若不涉及则在合同中给出依据。
- 引用 Gate B 已验收的公司平台基线，应用仓库/权限/CI/transport/固定目标另行通过项目验收，正式 stage 记录与现场资产一致。
- 生产执行前取得 exact 制品、环境、脚本版本、窗口和回滚基线授权；生产只执行已验证的确定性脚本。
- 目标环境有真实健康、浏览器（实际 Origin）、核心业务验收、观察期和运维接手证据；监控、备份、RPO/RTO 达到已批准目标。
- 全链路证据齐全后才标记闭环 PASS。前置 CI、历史 DockerLab、生产计划或部分安装均不能替代此结论。

### Gate D：通用流程经过实例验证

- 新/存量项目与首装/升级等入口明确；每一步有输入、责任方、产物、检查、失败出口和证据位置。
- 通用规则收敛在既有 onboarding/runbook/templates/checker，不生成平行事实源；各技术栈和环境细节仍归项目。
- NewEMaint 按新流程复核不产生无依据改写；至少一个不同项目/交付形态完成受控演练，未获批准的外部操作保持 NOT RUN。
- 仓库准入配置、检查器适用范围及已采用 pin/最新版本诊断按批准合同完善，并覆盖越权拒绝和无操作复跑。

## 3. 实施工作包与依赖

下表是后续立项入口，编号 A1–D3 不冒充真实 Issue。调度者必须在派发前补齐实际 Issue 与 exact branch；没有必要为每一行拆出新 Issue，可合并同一可验收合同内的相关项。

| 工作包 | 责任仓库 / 对应事项 | 前置 | 主要产物与完成依据 | 默认模型 |
|---|---|---|---|---|
| A1 首发流程合同 | 平台，新 Issue 待去重；F1/F2/F3/F4/F9/F10 | R0；对应合同确认 | 优先定义独立 SCM/平台交付入口、bootstrap 信任链与组件清单；阶段依赖、first-install/upgrade/adopt、release/approval 身份、版本/CI/来源说明一致；回归和 PR 通过 | Sol high |
| A2 Mac 回归修复 | 平台，新 Issue 待去重；F8 | R0；局部修复合同 | registry 错误路径正确非零退出；Bash 3.2 默认 locale 与 C locale 均通过；相应模板 digest 及下游同步影响可追踪 | Sol high 负责 Issue；Terra high 可做已定的机械修复子任务 |
| A3 安装与准入核对 | 平台负责 broker/profile 合同，项目负责自身准入记录；F6 | 可与 A1/A2 并行只读诊断；实际安装依赖稳定版本与授权 | Mac/VM 安装差异表、403 确切原因、manual 必需能力通过、optional routine 明确状态；必要安装有前后读回及回退记录 | Sol high；只读清单整理可 Terra high |
| B1 公司资产与平台交付合同 | 平台自身部署 Change，去重后立项 | 只读盘点可先做；执行依赖 Gate A/对应批准 | 既有 Gitea 采用或整改决策、公司角色与依赖、平台 exact SHA/安装清单、bootstrap/正常审批分界、逐阶段验收及回退计划 | Sol high；脱敏清单可 Terra high |
| B2 公司 Gitea 采用/部署 | 平台部署 Change | B1；exact 现场步骤授权 | 现有实例安全采用或必要安装、内网访问/认证/权限、备份和隔离恢复、运行接手的现场证据 | Sol high |
| B3 平台自身安装与接入 | 平台部署 Change；必要独立安全/治理 Change | B2；对应合同与阶段授权 | 平台仓导入、保护/required CI、公司所需确定性组件/Runner/guard/profile 安装及读回；开发侧 skills 独立对齐，内网不装 AI | Sol high |
| B4 平台自身闭环验收 | 平台部署 Change | B3 | 本地 Issue→结果入站→公司审批 PR→CI/verification→人工合并 canary、安装复跑/失败停止/恢复、source/installed/live 对账、运维接手；逐项判断 Gate B | Sol high |
| C1 项目候选基线 | NewEMaint；优先复用 #18/#43/#74，独立发布合同另行去重立项 | 可先调研；部署依赖 Gate B/所属合同 | 发布范围与候选 SHA/digest/pin、Issue 剩余 AC、业务/数据/安全/运行保障准入矩阵 | Sol high；#74 合同内机械同步可 Terra high |
| C2 非生产闭环 | NewEMaint，归项目部署 Change | C1 合同；Gate B | 两次部署、故意失败、A→B→A、DB/uploads 恢复、迁移彩排、浏览器与业务验收的真实记录 | Sol high |
| C3 应用仓与目标接入 | NewEMaint；引用 B 的平台基线 | Gate B；C1；所选现场操作授权 | 在已验收 Gitea/平台上接入应用仓、项目身份/权限/required CI、制品运输及 AppServer 固定目标；不重复承担 Gitea/平台安装 | Sol high |
| C4 正式发布与运行验收 | NewEMaint，确定性项目脚本 | C2/C3 PASS；#18/#43 及范围内阻断项闭合；生产授权 | exact 制品部署、健康与业务验收、观察期、备份/恢复安排、运维接手与实际 readback | Sol high 调度与核对；执行按生产合同 |
| C5 闭环复盘 | NewEMaint 事实记录，平台接收共性问题 | C4 验收完成 | 每次阻塞、手工决策、重复操作、实际回滚与偏差都有来源；Gate C 逐项结论 | Sol high；证据索引可 Terra high |
| D1 从实例提炼合同 | 平台，复盘后立项 | Gate B/C 实证 | 哪些规则通用、哪些留项目的决策清单；流程输入/责任/产物/失败出口 | Sol high |
| D2 流程与工具完善 | 平台；F5/F7 和 B/C 的新证据 | D1 合同 | onboarding 与部署流程、manifest 准入、pin/latest 诊断、适用性和模板/skills 检查；保持拒绝越权与兼容性 | Sol high；有限文档同步可 Terra high |
| D3 第二实例验证 | 选定项目（届时确认），平台汇总 | D2 已发布稳定版本 | 新接入与重复对齐演练；至少一种不同交付形态的步骤归属可验证；差异有明确去向 | Sol high；只读整理可 Terra high |

F7 的“已采纳 pin 下有效”立即用于人工判读，避免误改制品；全面 checker 改造仍留 D2。若新证据表明某个 D 类问题确实阻断首发，调度者提交具体阻塞和最小修复范围，更新所属合同后才前移。

## 4. 发现登记与去向

| 发现 | 核验结论摘要 / 代码或文档指针 | 去向 |
|---|---|---|
| F1 | `company-delivery/runbook.md` Stage 40 固定 NOT RUN，Stage 90 却要求它 PASS | A1 修复证据依赖 |
| F2 | Stage 100 要求 previous release，历史 NewEMaint 首装为 null | A1 首装回退基线；C2/C4 实验与采用 |
| F3 | 原制品身份与公司普通 PR merge 新 SHA 的关系未定义完整 | A1 比较并确认策略；C3 实证。禁止重构建冒充原字节 |
| F4 | 空白主机检查与公司已有 Gitea 线索不匹配 | A1 接管入口；B1/B2 平台现场采用/整改 |
| F5 | `aisoft_host_access/contract.py` 固定三仓 profile 集合 | D2 受控参数化；非首发必改 |
| F6 | Mac broker 21 个映射中 2 DRIFT；NewEMaint onboarding HTTP 403；routine source/live 不一致 | A3 查明范围，走 manual，不凭空扩 ACL |
| F7 | NewEMaint checker 4 PASS/4 GAP/3 SKIP；catalog 最新版与固定 pin 误混；平台 source 自检适用性问题 | C1 正确解释 pin；#74 既定模板；D2 工具完善 |
| F8 | Bash 3.2 默认 locale 下 `$REGISTRY（` 解析错误，registry 负向测试失败 | A2 修复引用并做真实目标环境回归 |
| F9 | operator 1.2/1.3、CI test/verify、installer guard 来源描述不一致 | A1 校正现状；不顺便扩大 installer 安全合同 |
| F10 | 补充盘点：`company-delivery/README.md` 的 builder 要求 exact 应用 release 与项目 compatibility matrix，现有打包入口不能作为不依赖应用制品的公司平台 bootstrap 路径 | A1 定义独立 SCM/平台交付合同与证据归属；B 单独验收。不能先搬 NewEMaint 包来掩盖依赖 |

本评估不是完整业务代码安全审计。NewEMaint `docs/OPEN-ISSUES.md` 所列 uploads/PDA/TLS/日志/签名事项仅是待复核线索；只针对所选发布范围判定真实阻断，不把旧列表当成全部现存漏洞已证实。

## 5. 后续必须作出的决策

| 决策 | 最晚决策点 | 调度者应先准备的可审阅材料 |
|---|---|---|
| 公司平台部署版本、逐角色组件范围、bootstrap 运输与信任起点 | B1 执行合同批准前 | 已有资产、平台 source SHA、独立交付包、开发侧/公司侧组件矩阵、所需身份、可复跑安装与回退证据 |
| 首次发布包含 Web/API/PDA 哪些部分，是否含旧数据/文件 | C1 合同批准前 | 当前功能、风险和业务需求证据；推荐最小可用范围及被排除项影响 |
| 选择历史已测 release 还是新候选，采用哪个平台/operator pin | C1/C2 执行前 | SHA、差异、制品 digest、支持/兼容性和必要重验清单 |
| 公司审批如何绑定本地已测制品 | A1 合同批准前 | 保留 source SHA 与显式审批映射等候选的真实可行性、约束和验证设计 |
| 公司现有实例采用、整改还是替换 | B1/B2 写入前 | 只读 inventory、版本、角色、冲突、备份/回退基线；不能假定为空白主机 |
| Registry 或离线 transport 及必需基础设施 | A1/B1（平台）及 C1（应用）合同批准前 | 项目实际通路与 operator 当前 Stage 70 约束；裁剪的正式合同变更 |
| 生产窗口、责任人、观察期、RPO/RTO 与业务验收 | C4 授权前 | 非生产完整证据、exact 环境/脚本/制品、操作与撤回方案 |
| 第二个验证项目/交付形态 | D3 准备时 | B/C 复盘发现与最有价值的差异场景；不提前批量接入其他项目 |

只有需要用户判断的具体候选准备完成才提问。已确认的方向与模型选择不重复询问。

## 6. 调度协议与持久化台账

1. 每次恢复先读本 plan、目标仓 `AGENTS.md`/README/相关分册、`aisoft-matt-workflow`、`issue-session-flow`；核对工作区、分支和 SHA。
2. 对两仓执行 broker 开放 Issue sweep，完整分页、排除 PR。输出六列：编号、标题、仓库、duplicate-of、判定、下一步。判定用 `dispatch` / `duplicate` / `blocked by #M` / `needs human decision`。读取已有 Issue 的正文/评论后再判定可复用合同。
3. 用实际 Issue/branch/PR/SHA 建台账；派发后再次 sweep。派生事项有来源、依赖、AC、明确所有者；同一 Issue 不同时开两个实施者。
4. 仅派发依赖已满足的工作；复杂使用 Sol high、简单使用 Terra high。调度者不实施，实施任务限定自己的 exact worktree/文件。不得回退其他任务的改动。
5. 子任务回报：已完成什么、exact SHA/PR、哪些验证在何环境运行、剩余阻塞、人工闸门和下一步。状态变更以读回证据为准，不能只接受一句“完成”。
6. 最终 PR、人工 merge、现场生产授权保留现有闸门。未经现场证据核验不将 stage 或 Issue 标为完成。重复失败三次按平台合同升级，不循环尝试更宽权限。
7. 每批派发、关键状态改变或交接时，更新调度任务状态，并在对应 Issue 留存必要的追踪记录；路线图合同变化走独立平台 Change。不依赖聊天记忆作为唯一状态源。

建议执行台账字段：`工作包 | repo/Issue | exact branch/head | owner/task ID | model/effort | dependencies | state | evidence URI | blocker | next action`。工作流状态采用所属仓现有 lifecycle；证据结论统一 `PASS / GAP / BLOCKED / NOT RUN`，不自创并写入 live 标签。

当前台账初值：R0 文档本地核验和任务启动见 verification；A1/A2 待立项；A3 待只读定位；B1–B4 为第一轮公司 Gitea/平台交付，待合同/Gate A；C1 引用 NewEMaint #18/#43/#74；C2–C5 等待 Gate B 与项目合同；D1–D3 等待 Gate C；改名延期。

## 7. 未来通用流程的整理框架（D 阶段候选）

此表用于真实实例复盘时归类，不是已实施的新合同，也不增加第二套流程入口。

| 流程 | 顺序 | 每一步必须保留的结果 |
|---|---|---|
| Onboarding | 申请/盘点 → 项目归属与范围 → 已有仓库/环境采用 → 治理与工具接入 → 项目开发/交付合同 → 能力验收 → 接手 | 项目身份、owner、exact repo、架构/profile/pin、权限边界、required CI、项目脚本入口、准入结论 |
| 持续开发中的部署 | 发起发布 → 选定不可变候选 → 准入与变更影响 → 非生产验证 → 目标环境审批/准备 → 确定性执行 → 业务验收/观察/关闭 | source/制品/审批映射、依赖/数据影响、恢复证据、窗口与停止条件、运行证据、运维归属 |

平台负责阶段、责任、证据和禁止条件。项目负责部署到哪里、使用什么技术、具体执行与迁移/回滚命令。首装/升级、空白/已有环境、新/存量项目均在入口分类，不强迫所有项目采用同一 Docker 或 VM 方案。

## Ticket graph

以下 Txx 只用于本 Issue 的路线图交付，不是 A/B/C/D 的实施授权。

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 固定用户方向、基线与范围，完成映射合同及路线图 | - | complete |
| T02 | 文档语义/判级/diff 验证，准备本地可审阅提交 | T01 | complete |
| T03 | 创建 Sol high 调度任务，记录交接回执与最终 PR 待确认状态 | T02 | queued：创建受理，启动回执待客户端 |

## Expected touch points

- T01/T02：仅本目录 summary/spec/plan/verification 四文件。
- T03：Codex 调度任务、verification 交接记录；不修改任何运行时/业务代码。

## 数据库迁移

无。本 Issue 不执行任何数据操作。

## 测试与验收映射

| Acceptance criterion | Verification command or review |
|---|---|
| AC-1/AC-2 | 对照用户最新指令和前一轮 assessment，核查 F1–F10、阶段出口及已有 Issue |
| AC-3 | 审阅 spec 多 Issue 授权、模型、所有权与 plan 调度协议/决策表 |
| AC-4 | Codex create_thread 回执与一次有界状态读回 |
| AC-5 | `PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo .`、resolver 判级校验、`git diff --check` |

## 部署与回滚

无实际部署影响。本次文档可普通 revert；停止新派发即可暂停调度，保留 Issue 和证据。后续部署 Change 必须自行提供两次执行、故意失败与回滚/恢复的计划及实际验收。
