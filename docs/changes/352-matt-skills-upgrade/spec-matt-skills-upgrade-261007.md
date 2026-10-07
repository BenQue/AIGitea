---
issue: 352
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/352
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - rollback
  - external-contract
depends_on: []
status: approved
branch: change/352-matt-skills-upgrade
created: 2026-10-07
updated: 2026-10-07
---

# #352 Matt v1.3.1 受控升级合同

## 目标与原因

让平台采用已核验的完整 v1.3.1 技能快照，吸收新的 PR 证据、术语表约定和人工复盘，同时保持既有确定性 Controller、单写者与人工交付门。

用户 2026-10-07 在 session `01a11682-fafc-70c1-80f2-a5d0d470bca1` 的“批准你的建议”承接前一轮审查卡的明确范围。合同不扩大该批准。T01 只修改本 Change 的四角色文档和证据，校验、本地 commit 后 STOP；后续 fresh run 重读本合同继续既定 source 工作，无须重复批准同一范围。

## Acceptance criteria

- [ ] AC-1：完整 v1.3.1 vendor 固定 tag object、commit、license 和 37 个技能目录哈希；上游 SKILL.md 及辅助文件逐字节保持，旧 v1.2.2 保留可恢复。
- [ ] AC-2：隔离 HOME fixture 证明新安装、从 v1.2.2 升级、重复安装、故意失败不改变 current、N-1 回滚；只处理可证明归属的技能和元数据，不覆盖外部目录或插件，不产生悬空入口。
- [ ] AC-3：平台及模板明确 GLOSSARY/GLOSSARY-MAP 新约定；已有 CONTEXT 文件的术语、业务规则、ADR 与历史引用保全；本仓 glossary 只包含已有合同支持的术语。
- [ ] AC-4：生成的 PR 正文包含具体变化、真实 Before/After 或诚实的缺证说明、证据 SHA/层次、回滚方式和影响范围；唯一 Closes 行、summary 映射、authorization marker、policy 与后续回填保持兼容。
- [ ] AC-5：Codex 与 Claude 的技能发现和调用边界分别验收；Matt retro 的 exact 来源可确认，gstack retro 不被覆盖或误选，用户调用型技能不被隐式启用。无法验证的真实会话行为明确记录 GAP/NOT RUN。
- [ ] AC-6：Matt retro 只在用户指定的会话范围运行，按证据输出建议，不自动应用治理修复；implement-spec 不替代 Controller，不放开 reset、子代理 merge、并行写入、提前 PR 或 ticket 终态投影。
- [ ] AC-7：对应 focused tests、默认 smoke、变更 shell 的 bash-n/ShellCheck、文档 resolver 与必要 provider parity 检查真实通过；无删除测试、弱化断言或 skip 制造 PASS。
- [ ] AC-8：最终 handoff 明确 source/local/CI/installed/live 的结果；源 PR 只人工合并；实际全局/VM 安装仍须固定目标、备份、回滚、fresh session 读回的独立验收。

## 接口、数据与兼容性影响

### 固定来源及安装所有权

- Release：v1.3.1；commit：`24fe0ef7737efae15c87225755e9f6f5965e4888`；tag object：`0b6cee10f260a2e048279cf737bfd3e37b1fce0b`。
- Source snapshot：`codex/vendor/mattpocock/v1.3.1/`；保留 `v1.2.2/`。manifest 继续用现有 schema；平台差异写 adapter，不修改 upstream 原文或静默追踪 main。
- 保持既有 source provenance/staleness guard。安装前完成来源、目标归属和变更集预检，再写 stage，验证后才切 current，保留 previous。
- 对 resolving-merge-conflicts 的旧入口，只允许在链接确为上一受管 release 时退役；无关目录、外部 symlink、历史 standalone 技能保持原样并报告。
- 旧 skills.sh 锁文件不得继续被当作平台安装权威。仅在证明 ownership 后处理受本次升级影响的记录，并保全原内容；不得调用全局无界 update，也不得抹掉其他来源记录。
- 不修改 Claude-owned plugin。两个 provider 的平台 adapter/source conformance 与真实会话加载分开验收；Claude 插件的实际升级不随本票自动执行。

### 术语表与入口解析

新项目采用 GLOSSARY.md，多个上下文才采用 GLOSSARY-MAP.md。既有 CONTEXT 文件先审查内容和引用：术语可迁入 glossary，业务规则或架构决策保留在适当合同/ADR，必要时保留兼容指针。两个文件同时存在且含义冲突时停止迁移，不猜测权威来源。本票不执行下游项目批量迁移。

Matt retro 与 gstack retro 必须按来源、版本和真实路径消歧。仅在用户明确请求 Matt 复盘时加载已验证的 Matt 内容；裸名称存在歧义时不得任选一个。适配器只提供本 provider 已验证支持的显式入口/路径；若无法证明调用目标则停止并报告 GAP，不靠修改 upstream name 或覆盖 gstack 解决。

### PR 正文证据

在当前 Controller 的 PR 候选/正文路径中接入 Summary、Evidence 和 Merge Danger 信息，沿用已有 verification/report 作为证据来源。每项结果需指明检查对象、命令或证据引用、SHA 与 source/local/CI/installed/live 层次。

没有 Before 观察时写明没有基线证据；没有实际执行时写 NOT RUN。不得用源码阅读推导“运行通过”，也不为了补图表强行运行无关测试。回滚风险区分可直接 revert 的代码与存在外部状态影响的操作，并给出具体范围。

始终保留唯一 `Closes #352` 对应的一般化 Issue 规则、semantic summary 路径、authorization marker、依赖列表及 exact branch/policy。不得因采用 pr 技能而授予远端写权限、自动创建 PR 或改变合并条件。

### 复盘及实现纪律

retro 是人工触发的候选建议生成步骤。可机械检测的问题优先使用既有 lint/test/CI；判断性规则进入编码规范；治理或权限改动另经相应批准步骤。它不持续自调用，不自动应用修复，不扫描用户未指定的大范围会话。

继续由 Controller 选择 frontier Txx，Agent 只追加该 Issue 的线性本地 commit。测试接口和验收依据在合同中约定一次，执行时复用；遇到真正的新边界再升级。每 ticket review 对照其 AC；整个 spec 的完整性 review 放在所有 tickets 完成后。

完整快照仍包含 implement-spec，但安装存在不代表平台启用。受管项目保持默认禁用其写入编排；用户需要该模式时必须另行确认带有 claim、分支、整合、并发限额和发布边界的 complex 合同。

## 明确授权的 source 文件范围

- T01：本目录四角色文档及 `evidence/`，不修改当前 AGENTS.md 或其他 source。
- T02：新完整 vendor 与 manifest；`codex/install-skills.sh`；确有需要的 `codex/runtime/aisoft_loop/matt_snapshot.py`；对应 `test_matt_snapshot.py`、安装/失败/回滚 fixture；`codex/tests/smoke.sh`、`test-agent-runtime.sh`、installed-drift fixture 的受影响断言；Matt workflow adapter；docs/agents 与 templates/docs/agents 的 domain/tracker 合同；本仓 GLOSSARY.md；04、08、README 的对应说明。
- T03：`codex/runtime/aisoft_loop/controller.py` 的 PR 候选/正文及其已有证据通路；必要的 provider/verifier 接口适配与对应测试。优先复用既有数据结构；若需要新的持久 schema、外部 API 或跨模块扩权，则停止并补充合同。
- T04：上述范围内的测试修复、结果文档及唯一最终 PR 候选；不修改无关治理、应用代码或历史 Change。

这份映射 spec 明确授权上述 Agent 行为、Controller 和安装脚本 source 变更。T01 必须独立 commit 并 STOP，runtime 只能由后续 fresh run 实施；不以此授权修改本次正在遵循的 AGENTS.md。

## 测试决策

安装通过隔离 HOME 的入口行为验证，观察指针、所有权、文件字节与失败后原状；不接触真实 home。PR 通过既有 Controller/Gitea fixture 验证最终正文与 hard gate 字段，并使用独立已知期望值。技能通过完整 manifest、真实 provider 元数据与明确加载路径验证；static PASS 不冒充 provider session PASS。

## 风险与回滚约束

本票不做数据库迁移。source 可按本 Issue 线性 commit 回退；vendor 旧 release 保留。安装器须证明 previous 仍能恢复旧快照及旧入口集合；失败不得先切 current 或删除不可恢复目录。真实主机回滚须在安装卡中绑定 exact source/target/snapshot，当前 NOT RUN。

## 非目标

不替换 Controller，不启用并行写入，不修改当前 AGENTS.md，不增加确认仪式，不绕过人工 PR/merge，不改变 main protection/required CI，不更新独立 Claude 插件，不做全局安装、VM 变更、Secret/账号/权限/服务/timer/生产操作或下游项目迁移。

## 未决问题

无会改变本期方向的未决问题。运行实现细节在上述边界内决定；实际主机安装的目标与执行窗口尚未授权，不作为源码合同的未决项或已完成证据。
