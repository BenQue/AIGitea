# 09 · v3 平台简化与 Loop Engineering 文档改造规划

> 状态：**通用 Codex runtime、synthetic、每项目 profile、VM 临时安装和一个真实 complex pilot 已完成；平台仓库不走应用部署，下一阶段为 Claude Code adapter parity**
> 日期：2026-07-16
> 适用范围：AISoftPlatform 平台文档、平台 skills 与 agent 编排说明
> 当前约束：v3 文档契约和通用 Codex candidate 已生效；VM 只保留禁用式 pilot 安装，新的 project-profile template 仅完成一次性 HOME smoke，未 enable 任何项目 timer，不得把 candidate 写成无人值守上线。

## 0. 实施状态

- [x] Phase D1：`AGENTS.md` 与 `README.md` 权威契约。
- [x] Phase D2：Issue/spec/plan 与 Development Loop 分册。
- [x] Phase D3：部署、运维、通知和内网边界已统一为首次非生产部署可由 AI 协作、生产 script-only、Loop 终态和单 PR 合并闸门。
- [x] Phase D4：Codex skills、复合 skill、VM 全局指导、onboarding 与 canonical templates。
- [x] Phase D5 文档/skill 部分：front matter、metadata、shell smoke、关键词检查和两项只读 forward test。
- [x] AI 判级增补：权威合同、canonical templates、Codex skills、初始 16 个 Gitea 标签与 `rsdesign-new` Issue #8 complex 试点合同；Issue #19 后续扩展为 17 个。
- [x] Loop runtime source：analyzer 单分支、classification/contract、state/lock、Codex adapter、verifier、Gitea adapter、controller 与安装入口。
- [x] Synthetic matrix：72 项 Python tests、ShellCheck、安装幂等、token 防泄漏、scope escalation、CI feedback 和终态回归。
- [x] VM candidate 临时/正式安装、回滚备份与 provider/timer 禁用边界验证。
- [x] 真实 complex Issue #8：one-shot Loop、deterministic verifier、PR #9 和 CI success 到 `READY_FOR_REVIEW`。
- [x] 通用化修正：项目 profile、namespaced state/worktrees、禁用式 systemd template；rsdesign-new 明确降级为 pilot evidence。
- [x] Claude adapter 前的中央 profile 安装 smoke：35 files / 7 scripts、两次 manifest、无 profile/凭据、systemd template verify。
- [x] Claude Code adapter 与 parity 验证（Issue #1，PR #2 已合并）：provider 选择由 `IMPLEMENT_PROVIDER` 驱动、fail-closed；17 项 parity 测试；adapter 输出规整（`extract-json`）；默认仍 `IMPLEMENT_PROVIDER=none`。真实 VM pilot 未做。

前序分类合同证据见 `10`。2026-07-16 中央分支 `codex/v3-loop-runtime` 已实现 runtime candidate；`bash codex/tests/smoke.sh` 运行 72 项 Python tests、ShellCheck、label sync mock、安装幂等和 token 防泄漏回归并通过。VM 临时 HOME 安装和带回滚备份的正式安装通过，timer 保持 inactive、implementation none。rsdesign-new Issue #8 作为 real complex pilot 暴露并验证了 worktree stdout 修复、deterministic verifier、PR/CI 和人工合并闸门；PR #9 后由人合并，测试环境健康。用户随后明确 AISoftPlatform 是通用平台文档/runtime source，不应继续把 rsDesign 当作承载仓库；误建的 rsdesign-new Issue #10 在仅生成 analysis summary 后已取消关闭，未实现、未建 PR、未部署。中央 source 因此增加每项目 profile 与 namespaced state/worktrees，部署验收改为每个有部署范围的应用接入门禁，而不是 AISoftPlatform 或 Claude adapter 的项目专用前置条件。

## 1. 规划目标

把现有“Issue → AI 分析 → 三道人工闸门 → 实现 → PR → 自动部署”收敛为：

1. Issue 始终作为需求、缺陷或平台变更的发起与追踪主键。
2. 保留 `needs-analysis` 驱动的 AI 自动分析和八个流程状态标签，并增加变更类型和复杂度标签。
3. AI 根据 Issue 声明、仓库证据和风险规则判定有效复杂度；只在信息不足、内容冲突或边界风险无法确定时升级给人。
4. Bug 修复、纯文档、纯测试和不改变外部行为的维护性修改可以按小变更直接进入开发 Loop。
5. 新增功能或改变现有功能合同的变更必须先形成与 Issue 绑定的 spec 和 plan。
6. `approved` 从“Gate B 后的实现许可”改为“合同已明确，可启动开发 Loop”的控制信号。
7. 开发 Loop 在既定合同内自主完成实现、测试、失败分析、修复、再验证和 CI 反馈处理。
8. 最终 PR 合并是唯一交付硬闸门。
9. AI 可以参与非生产环境的部署流程设计、首次部署、调试和验收。
10. 生产环境只运行已版本化、已验证、可回滚的确定性部署脚本。
11. 生产部署故障发生后，AI 可以分析脱敏证据，并在开发/测试环境复现和修复；AI 不直接执行生产部署。

## 2. 非目标

本轮文档规划不包含：

- 修改任何 shell 脚本、workflow、systemd timer 或 VM 配置。
- 启用无人值守实现 Loop。
- 删除现有标签、agent、Claude/Codex 配置或凭据。
- 修改试点应用 `admin/rsdesign-new`。
- 建设 prod-sim 或执行生产部署彩排。
- 改变受保护的 `main`、现有 CI context 或测试硬门。
- 把 AI 插入合并后的正常生产部署执行链路。

## 3. 目标平台边界

### 3.1 人负责

- 创建 Issue，说明目标、背景和验收结果。
- 可以在 Issue 上选择一个主要 `type/*` 标签，并可显式要求 `complexity/small` 或 `complexity/complex`。
- 对 AI 无法判定、判级冲突或合同不完整的结果进行澄清。
- 必要时提高复杂度等级；降低 AI 判定的复杂度必须留下可审计理由，且不得绕过强制复杂规则。
- 对需求范围、架构、安全、破坏性迁移等升级事项作出决策。
- 审核并合并最终 PR。
- 触发或授权生产部署脚本。

### 3.2 AI 自动分析负责

- 消费带 `needs-analysis` 标签的 Issue。
- 读取仓库和项目规范，生成 `00-summary.md`。
- 识别或校验 `type/*` 标签，判断变更是在恢复、保持、新增还是改变产品合同。
- 输出影响范围、初步方案、风险、请求复杂度、评估复杂度和最终有效复杂度。
- 根据有效复杂度自动路由：小变更进入开发准备，复杂变更进入 spec/plan，不确定项进入人工澄清。
- 把分析结果与 Issue、分支和文档目录关联。
- 更新 Issue 评论和流程标签。

### 3.3 开发 Loop 负责

- 严格读取 Issue、summary、spec/plan 和 `AGENTS.md`。
- 按 plan 逐项实现最小改动。
- 运行确定性测试和构建命令。
- 分析普通失败，在原范围内修复并重新验证。
- 对改动进行自审；复杂变更可增加独立 reviewer。
- 本地验证通过后推送分支并创建 PR。
- 消费 PR CI 失败和范围内 review feedback，继续迭代。
- 只在达到完成或升级条件时退出。

### 3.4 确定性平台负责

- Gitea 保存 Issue、代码、文档、PR 和审计记录。
- 分支保护阻止直接推送 `main`。
- PR CI 独立运行测试、迁移验证和构建。
- 合并后构建不可变制品并部署测试环境。
- 生产 promote 使用与测试环境验证过的同一制品。
- 部署脚本执行备份、迁移、切换、启动、健康检查和回滚。

## 4. 两类变更路径

### 4.1 小变更

小变更必须有 Issue，但不强制 `01-spec.md` 和 `02-plan.md`。

小变更的本质是恢复或保持已经存在的产品合同，而不是代码行数少。典型范围包括：

- 修复偏离既有明确预期的 Bug。
- 纯文档修正。
- 只补充或修正测试，且不借测试改变产品行为。
- 不改变外部可观察行为的局部重构或维护性修改。

```text
Issue + needs-analysis
  → AI 生成 00-summary.md
  → AI 判定 effective_complexity=small
  → 合同完整则 approved；信息不足则 awaiting-triage
  → Loop：实现 → 测试 → 修复 → 再验证
  → PR + CI
  → pr-open
  → 人工合并
  → 自动部署
  → deployed
```

小变更应同时满足：

- 目标和验收结果明确。
- 修改范围局部，回滚可以通过 revert 完成。
- 不涉及 schema、历史数据迁移或外部接口契约。
- 不涉及认证、授权、安全边界或共享核心组件。
- 不修改 CI、制品、部署、健康检查或回滚脚本。
- 不新增功能，不改变既有功能、业务规则、用户交互或外部可观察行为。

### 4.2 复杂变更

出现以下任一情况即按复杂变更处理：

- 新增任何产品功能。
- 改变既有功能行为、业务规则、用户交互或产品合同；即使代码改动很少也不例外。
- 需求存在多个合理方案或关键取舍。
- 涉及数据库 schema、数据迁移或兼容窗口。
- 改变 API、数据格式、权限、安全或外部系统契约。
- 跨模块、跨服务或影响核心业务流程。
- 修改 CI、制品、部署、健康检查、备份或回滚机制。
- 修改 `AGENTS.md`、Agent 行为、自动化控制器或平台治理规则。
- 失败后无法简单 revert，或存在较高数据/运行风险。

```text
Issue + needs-analysis
  → AI 生成 00-summary.md
  → AI 判定 effective_complexity=complex
  → spec-drafting
  → 01-spec.md + 02-plan.md
  → spec-review（可选协作状态，不是硬闸门）
  → approved（启动开发 Loop）
  → Loop：实现 → 测试 → 修复 → 再验证
  → PR + CI
  → pr-open
  → 人工合并
  → 自动部署
  → deployed
```

### 4.3 AI 判级与优先级

AI 判级首先判断变更对产品合同的作用：

```text
restore / unchanged  → small 候选
add / change         → complex
unclear              → awaiting-triage，等待人澄清
```

有效复杂度按以下优先级确定：

```text
强制复杂风险规则
  > Issue 明确要求 complexity/complex
  > Issue 要求 complexity/small 且通过 AI 校验
  > AI 根据 Issue 与仓库证据自动判级
```

- Issue 作者可以显式选择复杂度，但只能主动提高等级，不能用 `complexity/small` 绕过功能变更或风险规则。
- `complexity/complex` 一经 Issue 明确要求，AI 不得自动降级。
- 标签和 Issue 内容冲突时，AI 以仓库证据、产品合同影响和强制风险规则为准，更正标签并在 Issue 评论及 summary 中记录原因。
- AI 只有在合同明确且置信度足够时才可自动路由；信息不足、需求矛盾或风险边界无法确定时保留 `awaiting-triage`，不得按小变更继续。
- Development Loop 发现实际范围扩大或产品合同发生变化时，必须停止并从 `small` 单向升级为 `complex`；补齐 spec/plan 并重新启动后才能继续。
- 系统不得在运行中的 Development Loop 内自动把 `complex` 降级为 `small`。

分析结果必须记录至少以下字段：

```yaml
requested_complexity: auto # auto | small | complex
assessed_complexity: small # small | complex | needs-human-decision
effective_complexity: small # small | complex
contract_effect: restore # restore | unchanged | add | change | unclear
reason: 恢复已经明确的既有行为
risk_flags: []
required_docs:
  - 00-summary.md
confidence: high # high | medium | low
override_reason:
```

`assessed_complexity: needs-human-decision` 时不得写入 `effective_complexity`，Issue 保持 `awaiting-triage`。

## 5. Issue、分支与文档合同

### 5.1 Issue 是唯一主键

继续使用 Gitea Issue 号 `N` 绑定：

```text
Issue #N
  ↔ change/N
  ↔ docs/changes/N/
  ↔ PR（Closes #N）
  ↔ commit / CI / deployment SHA
```

### 5.2 单分支模型

v3 建议从分析开始只使用一个变更分支：

```text
change/<issue-number>
```

AI 自动分析先在该分支写入 `00-summary.md`。后续 spec、plan、代码、测试和 verification 都在同一分支演进，最终只创建一个交付 PR。

迁移期间可以继续识别旧 `spec/N` 分支，但新 Issue 不再要求先合并独立 docs-only spec PR。

### 5.3 文档目录

```text
docs/changes/<issue-number>/
├── 00-summary.md       # 所有变更必须有
├── 01-spec.md          # 复杂变更必须有
├── 02-plan.md          # 复杂变更必须有
└── 03-verification.md  # 部署/迁移变更必须有；其他变更推荐
```

建议统一 front matter：

```yaml
---
issue: 123
gitea_url: http://gitea.example/owner/repo/issues/123
change_type: bugfix # bugfix | feature | docs | test | refactor | maintenance | platform
requested_complexity: auto # auto | small | complex
assessed_complexity: small # small | complex | needs-human-decision
effective_complexity: small # small | complex；needs-human-decision 时省略
contract_effect: restore # restore | unchanged | add | change | unclear
confidence: high # high | medium | low
risk_flags: []
status: implementing
branch: change/123
pr_url:
created: 2026-07-14
updated: 2026-07-14
---
```

### 5.4 最终 PR

PR 正文至少包含：

```markdown
Closes #123

Change documents:
- docs/changes/123/00-summary.md
- docs/changes/123/01-spec.md
- docs/changes/123/02-plan.md
- docs/changes/123/03-verification.md
```

小变更只要求链接 `00-summary.md`；复杂变更链接 summary/spec/plan；部署与迁移变更还必须链接 verification。

## 6. 标签模型

标签分为三个正交维度：

```text
type/*                Issue 是什么变更
complexity/*          AI 判定需要什么流程
八个状态标签           Issue 当前处于什么阶段
```

### 6.1 变更类型标签

每个 Issue 最多保留一个主要 `type/*` 标签。Issue 作者可以选择；未选择时由 AI 补充；标签与实际内容冲突时由 AI 更正并说明。

| 标签 | 含义 | 默认判级 |
|---|---|---|
| `type/bugfix` | 恢复已经明确的既有行为 | `small` 候选 |
| `type/feature` | 新增功能或改变功能行为 | 强制 `complex` |
| `type/docs` | 纯文档修正 | `small` 候选 |
| `type/test` | 只补充或修正测试 | `small` 候选 |
| `type/refactor` | 不改变外部行为的内部重构 | `small` 候选 |
| `type/maintenance` | 依赖、配置或日常维护 | 由 AI 按实际影响判定 |
| `type/platform` | 改变 CI、部署、Agent 或平台治理行为 | 强制 `complex` |

纯平台文档勘误使用 `type/docs`；`type/platform` 专用于改变平台行为或治理合同的变更。

### 6.2 复杂度标签

| 标签 | 含义 |
|---|---|
| `complexity/small` | 有效复杂度为小变更，可在合同明确后直接进入 Loop |
| `complexity/complex` | 有效复杂度为复杂变更，必须先有 spec/plan |

- 两个复杂度标签互斥。
- 缺少复杂度标签表示尚未判级，不另设 `complexity/auto`。
- AI 判级完成后必须只保留一个最终有效复杂度标签；无法判定时不添加复杂度标签，并保持 `awaiting-triage`。

### 6.3 八个流程状态标签

| 标签 | v3 语义 | 是否阻塞 |
|---|---|---|
| `needs-analysis` | 触发 AI 自动分析 | 是，分析触发条件 |
| `awaiting-triage` | AI 无法安全判级、内容冲突或合同不完整，等待人工澄清 | 是，阻止自动路由 |
| `spec-drafting` | 复杂变更正在编写 spec/plan | 否 |
| `spec-review` | 可选的方案讨论或协作 review 状态 | 否 |
| `approved` | 合同已明确，启动开发 Loop | 是，Loop 启动条件 |
| `pr-open` | 最终交付 PR 已创建 | 否 |
| `completed` | 最终 PR 已合并且该变更明确无需部署 | 否 |
| `deployed` | 已部署并完成规定验证 | 否 |

`completed` 与 `deployed` 是互斥的交付终态：前者用于无需部署的已合并变更，后者必须有确定性部署和验证证据。`approved` 是运行控制信号，不代表独立 spec 审批，也不授权合并或部署。受控 analyzer/controller 在完成合同完整性校验后可以自动写入该标签：小变更要求 Issue、summary 和可测验收标准完整；复杂变更还要求 spec/plan 完整且没有未解决决策。人工也可以添加或移除标签，但 controller 启动前必须重新验证合同，不能只信任标签本身。

标签组合示例：

```text
type/bugfix + complexity/small + approved
type/feature + complexity/complex + spec-drafting
type/platform + complexity/complex + approved
type/platform + complexity/complex + completed
```

## 7. Development Loop 合同

### 7.1 Loop 输入

所有变更：

- Issue 正文和评论中的有效决定。
- `00-summary.md`。
- 可验证的 acceptance criteria。
- 明确的非目标和禁止修改范围。
- 仓库 `AGENTS.md`。
- 隔离的 `change/N` 分支。

复杂变更额外读取：

- `01-spec.md`。
- `02-plan.md`。
- 数据、接口、安全、部署和回滚约束。

### 7.2 每轮执行

```text
读取合同与状态
  → 选择下一个未完成任务
  → 实现最小改动
  → 运行确定性验证
  → 分析失败
  → 在合同范围内修复
  → 记录进度
  → 判断继续、完成或升级
```

验证层级按项目实际能力配置：

1. format、lint、类型检查。
2. 受影响模块单元测试。
3. 相关集成测试。
4. 数据迁移和兼容性验证。
5. 完整测试集。
6. 构建。
7. 浏览器/API acceptance。
8. AI diff 自审和可选独立 reviewer。
9. PR CI。

### 7.3 Loop 不应打断人的问题

- 编译、类型、lint 和格式错误。
- AI 自己引入的单元或集成测试失败。
- 普通 import、依赖和构建问题。
- 可复现的本地/CI 差异。
- 范围内 reviewer 意见。
- 可以通过现有代码、文档和日志判断的实现问题。

### 7.4 Loop 必须升级给人的情况

- Issue、spec、plan 或验收标准相互冲突。
- 必须改变合同或扩大范围才能完成。
- 涉及不可逆数据删除或未批准的破坏性迁移。
- 需要新凭据、权限或外部团队协调。
- 需要直接修改生产环境。
- 出现新的安全、认证、授权或架构决策。
- 同一根因连续三次尝试仍无法解决。
- 测试不稳定，无法可靠判断实现正确性。
- 达到配置的时间、token 或迭代次数上限。

### 7.5 Loop 终态

| 状态 | 含义 |
|---|---|
| `READY_FOR_REVIEW` | 合同满足，本地验证和 PR CI 通过，等待人审核合并 |
| `NEEDS_HUMAN_DECISION` | 需要需求、架构、安全或范围决策 |
| `BLOCKED_EXTERNAL` | 缺少凭据、服务、网络或外部协调 |
| `FAILED_LIMIT` | 达到循环次数、时间或成本上限 |

Loop 不得以“基本完成”“应该通过”或未运行的测试作为完成结论。

### 7.6 第一版编排原则

第一版使用：

```text
一个实现 agent
  + 一个独立的确定性 verifier
  + 复杂变更可选一个 review agent
```

暂不引入多 agent 并行实现、自动模型互评集群或跨 Issue 调度，避免重新制造平台编排复杂度。

## 8. 部署生命周期中的 AI 边界

### 8.1 建设期和首次部署

AI 可以与人一起在开发/测试环境：

- 分析应用、数据库、运行时和网络依赖。
- 设计 build、pack、deploy、health-check 和 rollback。
- 执行真实安装、构建、迁移、启动和验证命令。
- 查看日志，修改 workflow 和部署脚本。
- 验证脚本重复执行的安全性。
- 故意制造迁移、启动和健康检查失败。
- 验证数据库备份、应用回滚和错误报告。
- 把所有有效临时操作固化为版本化脚本。

首次人工协作部署成功不等于验收完成。必须证明清理环境后只运行脚本也能完成部署。

### 8.2 测试环境常规部署

部署流程验收后，常规测试环境部署由 CI/CD 脚本自动执行。发生失败时，人再启动 AI 排障会话。

### 8.3 生产环境

生产环境只允许：

- 接收已验证的不可变制品。
- 运行固定版本的部署、迁移、健康检查和回滚脚本。
- 使用本地环境配置和凭据。
- 输出可脱敏、可审计的确定性日志。

生产环境不依赖模型、AI API、provider 认证或动态生成的命令。

### 8.4 生产故障修复

```text
生产脚本失败
  → 停止并按既定策略回滚
  → 收集脱敏证据
  → AI 在开发/测试环境分析和复现
  → 修复版本化脚本
  → 重新完成测试部署和回滚验收
  → 修复 PR 人工合并
  → 人重新触发生产部署脚本
```

## 9. 文档影响矩阵

| 文件 | 规划修改 | 保留内容 |
|---|---|---|
| `AGENTS.md` | 把“三道闸门”改为“合同明确后 Loop + 最终 PR 合并硬闸门”；写清非生产首次部署和生产部署边界 | 凭据保护、测试硬门、Claude/Codex 独立、运维验证要求 |
| `README.md` | 升级 v3 总纲、目标架构、双路径流程和角色边界 | Gitea/runner/制品/部署总体导航 |
| `01-基础设施-VM-Gitea-Runner.md` | 调整 `coder`、ci-bot、timer 的职责；标注 Loop 所需状态目录和权限边界 | Gitea、runner、Verdaccio、Mailpit、端口、账号隔离 |
| `02-CI与自动部署流水线.md` | 增加首次部署验收条件、部署变更 verification、生产 script-only 原则 | CI context、制品、SQLite、PM2、健康检查、回滚 |
| `03-Issue-Spec-Plan与单闸门开发流程.md` | small/complex 双路径、单分支和唯一最终 PR | Issue 主键、docs/changes 目录、可追溯关联 |
| `04-Agent编排与定时任务.md` | 重写为 Analysis + Development Loop 编排；定义重试、状态、终态和升级条件 | 专用用户、最小权限、provider 可插拔、独立测试硬门 |
| `05-通知与多人协作.md` | 通知从三闸门就绪转向 analysis 完成、Loop 升级、PR ready、CI/部署失败和回滚结果 | Gitea mailer、Mailpit/SMTP、多用户协作 |
| `06-运维手册与踩坑集.md` | 增加 AI 排障入口、标准故障证据包、生产故障修复路径 | 现有真实命令、14 条踩坑、凭据位置、部署排障树 |
| `07-内网与生产平移路线.md` | 移除生产服务器 AI 依赖；办公客户端负责 AI；更新 prod-sim 验收优先级 | 三层拓扑、离线生产、制品传输、备份与回滚 |
| `08-Codex双工具共存与实施.md` | 从“一次性 provider 调用”升级为 provider-neutral Loop；Mac 交互与 VM headless 分工重新定义 | Claude/Codex 配置独立、共享 AGENTS、sandbox 和最小权限 |
| `skill-for-codex/SKILL.md` | 更新总流程、标签语义、small/complex 路由、Loop 和部署边界 | 平台诊断入口、关键事实、凭据保护 |
| `skill-for-codex/references/onboarding-runbook.md` | 新项目接入改为双路径、Loop 验收、首次部署 AI 协作与生产 script-only | 参数化接入、端口、CI、环境、分支保护 |
| `codex/global-AGENTS.md` | 更新唯一闸门、Loop 终态和部署生命周期规则 | VM 全局路径、凭据禁令、生产安全边界 |
| `codex/skills/gitea-*` | 调整分析输出、spec 条件、Loop 实现和平台排障说明 | 阶段型 skill、sandbox 和最小权限原则 |
| `archive/` | 不修改 | 历史设计依据和迁移审计记录 |

## 10. 后续文档实施顺序

### Phase D1 · 权威契约

1. 修改 `AGENTS.md`。
2. 修改 `README.md`。
3. 明确版本、日期、当前实施状态和兼容期。

验收：根契约不再要求独立 spec PR 或三道硬闸门，同时没有弱化最终 PR、CI、制品、回滚和凭据规则。

### Phase D2 · 日常开发流程

1. 重写 `03`。
2. 重写 `04`。
3. 更新 `08`。
4. 更新 Issue 文档模板和 front matter 说明。

验收：AI 能根据类型、产品合同影响和强制风险规则稳定判级；小变更与复杂变更均能从 Issue 走到 `READY_FOR_REVIEW`，且没有相互冲突的分支、标签或文档要求。

### Phase D3 · 部署与运维

1. 更新 `02` 的部署生命周期边界。
2. 更新 `06` 的 AI 故障诊断和证据包。
3. 更新 `07` 的内网/生产拓扑。
4. 更新 `05` 的通知事件。

验收：文档明确区分“AI 参与首次非生产部署”和“生产 script-only”，并保留真实验证和回滚要求。

### Phase D4 · Skills 与接入说明

1. 更新复合 skill 和 onboarding runbook。
2. 更新 VM 全局指导。
3. 更新四个阶段型 Codex skills 的职责描述。
4. 只规划 agent 脚本变化，不在文档阶段实施。

验收：skill 不再把旧三闸门或独立 spec PR 当成不可妥协项，也不会授权 AI 合并或直接部署生产。

### Phase D5 · 一致性检查

检查关键词和交叉链接：

```bash
rg -n '三道闸门|闸门 A|闸门 B|spec/N|docs-only spec PR|IMPLEMENT_PROVIDER|部署链路无 AI' \
  README.md AGENTS.md 0*.md codex skill-for-codex

rg -n 'READY_FOR_REVIEW|NEEDS_HUMAN_DECISION|effective_complexity:|type/feature|complexity/complex|change/<issue-number>|生产.*script' \
  README.md AGENTS.md 0*.md codex skill-for-codex
```

旧术语可以出现在迁移说明或 archive 引用中，但不能继续作为 v3 当前规则。

## 11. 文档实施验收标准

- `README.md` 能在一页内说明 v3 目标流程和 AI/人/平台边界。
- 所有需求和缺陷仍以 Issue 为主键。
- 所有 Issue 都有 `00-summary.md`；复杂变更必须有 spec/plan。
- AI 以产品合同影响为核心判级，并在明确时自动路由；无法安全判定时停止在 `awaiting-triage`。
- 新增功能和功能性修改始终为复杂变更；Bug、文档、测试和内部维护只有在不改变产品合同时才可为小变更。
- `type/*`、`complexity/*` 和八个流程状态标签的职责及组合在所有文档中一致。
- Issue 明确要求 `complexity/complex` 时不得自动降级，`complexity/small` 不得绕过强制复杂规则。
- 部署和迁移变更必须有 verification、真实命令和回滚说明。
- `approved` 只表示 Loop 启动，不表示合并或部署授权。
- 所有文档只保留最终 PR 合并这一道交付硬闸门。
- Development Loop 有明确输入、验证、重试、升级和终态。
- 正常生产部署没有模型依赖。
- AI 可以参与开发/测试环境首次部署及生产故障的非生产复现修复。
- Claude 与 Codex 配置继续独立，provider 可以替换但平台合同不变。
- 当前 CI context、不可变制品、健康检查和回滚约束没有被弱化。
- 文档链接有效，历史 archive 不被重写。

## 12. 迁移与回滚原则

### 12.1 文档迁移

- 文档实施使用独立分支和 PR。
- 每个 Phase 单独检查，不与 agent 脚本改造混在同一提交。
- v3 文档未全部一致前，明确标注兼容期和实际运行状态。
- 不把尚未启用的 Loop 描述成已经上线。

### 12.2 运行迁移

后续脚本实施前必须记录：

- 当前 systemd timer/service 状态。
- 当前 `ANALYSIS_PROVIDER` 和 `IMPLEMENT_PROVIDER`。
- 当前 agent 脚本版本和安装路径。
- 当前类型、复杂度、八个流程状态标签与分支规则。
- 当前试点仓库的工作树、开放 Issue 和 PR。

第一阶段只增加新 Loop 入口并保持旧实现可恢复；在真实低风险 Issue 完成验证前，不删除旧脚本或认证路径。

### 12.3 回滚

如果 v3 Loop 试点失败：

1. 把 `IMPLEMENT_PROVIDER` 恢复为 `none`。
2. 停止新的 Loop controller。
3. 保留 AI 自动分析，开发回到 Mac 人机交互模式。
4. 继续使用最终 PR、CI 和现有部署流程。
5. 不需要恢复无人值守实现，也不影响生产部署。

## 13. 实施参数

`09` 早期把以下八项列为"实施前仍需定稿"。runtime candidate 与 Claude adapter 落地后，其中七项已在实现中定稿，这里回填为决策；只有一项仍开放。当前值全部取自 `codex/runtime/aisoft_loop/`，接入新项目前应以这里为准，而不是从 env 默认值反推。

### 13.1 已定决策

| # | 决策 | 当前值 / 落点 | 理由 |
|---|---|---|---|
| 1 | 默认实现 provider 与切换策略 | 默认 `IMPLEMENT_PROVIDER=none`；`claude`/`codex` 显式选择；未知或禁用一律 fail-closed，**无自动回退** | 启用是每项目独立门禁；active Issue 上换 provider 必须先结束或迁移状态，避免状态不一致 |
| 2 | 每 Issue 预算 | `LOOP_MAX_ROUNDS=8`、`LOOP_MAX_SAME_ROOT=3`、`LOOP_PROVIDER_TIMEOUT=2700` 秒（provider 硬上限 7200）；均可按项目 env 覆盖 | 同根因三次即升级（`03 §8`）；总轮数上限兜底防止无界迭代；单值可为慢项目上调 |
| 3 | Loop 状态存储 | VM 本地 `~/.local/state/aisoft-loop/projects/<profile>/`（见 `04 §2`） | 状态不进 Issue 评论或仓库，避免污染审计记录与合同文档 |
| 4 | PR 创建时机 | 本地 verifier 全绿后才建，不用 Draft PR | PR 一旦出现即代表"本地已验证、等 CI 与人审"，语义单一 |
| 5 | CI 结果读取与反馈 | `get_commit_status` 映射 pending/success/failure；`success`→`READY_FOR_REVIEW`，`pending`→持久化 `stage=awaiting_ci` 返回 CONTINUE，`failure`→证据进下一轮，三次记入同根因上限 | 复用唯一交付闸门的 CI，不新造状态；失败反馈闭环但不无限重试 |
| 6 | Provider 输出规整 | adapter 用 `extract-json` 取输出中最后一个 JSON 对象，再交严格校验器；共享 `ProviderResult`/`AnalysisResult` 校验保持严格不放宽 | Claude 会先输出散文再给 JSON；把 CLI 差异关在 adapter 内，两个 provider 的结果契约保持一致 |
| 7 | 并发与隔离 | 每 profile 单 active Issue + `GlobalLock` + 独立 `change/N` worktree（见 `04 §3`） | 第一版不做跨 Issue 并行，避免重造编排复杂度；并行启用需另做 VM 容量验收 |

### 13.2 仍开放

- **Review agent 触发规则**：复杂变更是否引入独立 review agent，以及由复杂度还是风险规则触发。当前实现**未引入**（`§7.6` 记为可选）。现状即事实决策——verifier 已独立验证、controller 已校验 changed_files 与授权范围、人工合并是最终闸门，在此之前再加一个模型意见收益不明。启用前需单独设计与授权。
- **首次部署验收的故意失败与最低重复次数**：仅对有部署范围的应用 profile 适用，随该项目接入门禁定稿；AISoftPlatform 等文档/source 仓库 not applicable（见 `08 §7`）。

## 14. 本规划的批准边界

批准本文件只表示同意 v3 文档改造方向，不自动授权：

- 修改现有运行脚本。
- 启用 `IMPLEMENT_PROVIDER`。
- 启动 Development Loop。
- 修改 Gitea 标签或分支保护。
- 停止 VM 服务。
- 建设或部署生产环境。

进入文档实施、Loop 设计、脚本实施和真实 Issue 试点前，分别需要明确授权。
