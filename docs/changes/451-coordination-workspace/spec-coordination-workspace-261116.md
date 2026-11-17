---
issue: 451
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/451
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
  - docs/changes/451-coordination-workspace/summary-coordination-workspace-261116.md
  - docs/changes/451-coordination-workspace/spec-coordination-workspace-261116.md
  - docs/changes/451-coordination-workspace/plan-coordination-workspace-261116.md
  - docs/changes/451-coordination-workspace/verification-coordination-workspace-261116.md
  - docs/changes/451-coordination-workspace/proposals/coordination-workspace.patch
  - docs/changes/451-coordination-workspace/proposals/home-repo-proposal-v2.1.md
  - skills/issue-session-flow/SKILL.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/greenfield-planning.md
  - skills/aisoft-matt-workflow/SKILL.md
  - codex/runtime/tests/test_session_contract.py
  - usage/bundle.json
  - docs/governance/review-evidence-index.md
branch: change/451-coordination-workspace
created: 2026-11-16
updated: 2026-11-16
---

# Spec：跨项目协调工作区成为可选的合法协调位置

## 目标与原因

负责人要建立一个独立的 Home 仓库作为日常入口和跨项目协调位置，同时保持平台独立、项目自治和各项目版本 pin。现行合同有三处挡在前面：

1. `issue-session-flow` 规定调度会话只能开在「这批 Issue 的相关项目」里，没有给跨项目协调留合法位置，也没有说明这种位置的角色边界与权限来源。
2. `greenfield-planning` 第一句写「已登记、已采用」，与 ADR 0003「采用不需要平台登记」不一致。
3. `aisoft-matt-workflow` 的仓库初始化第 1 步要求「exact manifest project」与 project Agent 权限闸门，把站点加固访问写成了所有项目的前置，同样与 ADR 0003 不一致。

本票只做平台侧的最小适配：让「跨项目协调工作区」成为可选的合法协调位置并写明中性边界，顺带对齐上述两处表述。组织专属内容不进平台，Home 仓库自身的建立、采用和试点由它自己的 Issue 承载。

### 授权与基线

- 2026-11-16 负责人在来源会话确认方案选择，原话：「D1–D6 都按推荐方案，Home 暂定为本地 Gitea admin/AISoftHome，由我维护，首轮仅我使用，使用 Claude Code。请把这些决定写入方案和交接文字，仍不实施，我会转到 Claude Code 继续开发。」这些选择是本合同的输入，不等于 `approved`。
- 同日负责人在本票线程要求接手会话「依据已确认的方案决定准备正式合同，并在获得对应实施授权后推进开发」。本轮只完成合同准备，实施等确认点 1。
- 2026-11-16 23:26（北京时间）经 broker `gitea.issue.read` 读回：#451 为 open，标签只有 `needs-analysis`，评论 0 条，`updated_at` 仍是 2026-11-15T17:45:15+08:00，正文未变。
- broker `git.fetch.main` 后 `origin/main` 为 `c14a86d4ad0d1fd5938ab31343f8d72acd486a71`，作为 change_base。接手时没有任何 #451 的既有分支、worktree 或 owner。
- exact branch `change/451-coordination-workspace`，worktree `/private/tmp/issue-451-coordination-workspace`，写者为 Claude Code 会话 `0a9bf32d-69b7-4d4e-a676-2bc1eb8df9ed`（claim 结果 `created`）。
- 实施 provider 为 claude。最终 actual-head 交叉审查由未参与实现的 Codex 承担。此前 Claude 对方案的 R1/R2 审核审的是上一版方案，不能代替本票实现的交叉审查。
- 无硬前置。#450 只是关联讨论，本票不依赖它，也不修改它的合同或 worktree。

### 已确认的决定（合同输入，不再询问）

| 编号 | 已确认选择 | 在本票的落点 |
|---|---|---|
| D1 | 团队可共享的私有 Home，首轮仅负责人本人使用 | 组织专属，不进平台文字；留给 Home 自己的 Issue |
| D2 | A：Home 对其他项目只读，产出任务书，由目标项目会话建票和评论 | 平台写成中性缺省：工作区对其他项目缺省只读；放宽须写进工作区仓库自己的已批准合同 |
| D3 | 平台先做合法协调位置、角色边界和自主采用入口两处一致性修正；模板先在 Home 试用；不开发新核验 CLI | 即本票的全部语义范围 |
| D4 | 试点为 LocalWMS 单项目交接、SFMDigitalBoard 旧 pin 对照、WMPDA-WMS 只读缺失检出演练 | 不在本票执行；留给 Home 的试点 |
| D5 | 会话自主只读核验来源；合同冲突或执行依赖不可证时停止受影响动作；合法旧 pin 不强制升级；未取得会话证据不写成通过 | 平台写成工作区「版本不一致」规则 |
| D6 | 首版不要求打通正式跨仓依赖；真实前置不可验证仍阻塞，不得改称关系说明 | 平台只加一句指回现有「依赖身份」规则，不改依赖门 |

Home 参数：暂定仓库为本地 Gitea `admin/AISoftHome`；维护者是负责人本人；首轮使用者与读者仅负责人本人；首轮 provider 为 Claude Code。「暂定」表示这是后续合同的选定目标，不表示仓库已创建或已获建仓授权。

完整方案 v2.1（职责与事实来源矩阵、分阶段路线、试点映射）按原字节保存在 [proposals/home-repo-proposal-v2.1.md](proposals/home-repo-proposal-v2.1.md)，SHA-256 `5f306c6a6a75c29e13845cde0d14f625509a6b9c894c5cf93e7e93c295ea8573`。它是方案记录与后续 Home Issue 的引用来源，不是生效治理；生效文字只有下面的冻结补丁。方案里指向本机路径的链接只对来源机器有效。

### 证据分层

| 层 | 本票能证明什么 | 当前状态 |
|---|---|---|
| 源码合同 | 四份技能文件的文字与冻结候选一致；合同钉子测试通过 | 候选已冻结，未应用 |
| 发布包 | bundle 追加一个版本，历史与成员集合不变；隔离导出的三端技能与源码同字节 | NOT RUN |
| required CI | 远端 `CI / verify (pull_request)` | NOT RUN，PR 之后才有 |
| 安装 | Mac 上 `~/.claude/skills` 与 `~/.agents/skills` 的实际字节 | 不在本票授权内，合并后由负责人重装再读回 |
| 实际会话 | 某个 provider 会话实际加载了新文字并按它行事 | 本票不取得；写「本次未取得证据」 |
| live | Home 仓库存在、已采用、从 Home 读取其他项目、试点交接 | 不在本票范围，全部未执行 |

静态源码、发布包、安装、实际会话与 live 分别报告，不互相推断。

## 范围与非范围

### 冻结候选

精确文字以 [proposals/coordination-workspace.patch](proposals/coordination-workspace.patch) 为准，补丁 SHA-256 `d2352ae89d3c4709c394f693ca821d7ba3c4d2b6de60d4edcbea9c3451b1a7c3`。它相对 change_base 生成，`git apply --check` 已通过；本阶段只保存候选，不应用。

| 文件 | 改动 | 基线 SHA-256 | 应用后 SHA-256 |
|---|---|---|---|
| `skills/issue-session-flow/SKILL.md` | 「何时开调度会话」补一句跨项目协调可放在协调工作区；「两种会话」表「开在」一格同步；新增一节「跨项目协调工作区（可选）」 | `a9e2637e8639f7294cabdcc5db826935537d216fd6448513451b68bf2aed9fd8` | `b883faf61a196c5e93690da50355b4c1dbd31e9699b5a228f839364eb48dbc54` |
| `skills/aisoft-platform/SKILL.md` | 「目标项目与 governance manifest」补一句：协调工作区只作导航与交接，它的项目目录不是第三种访问来源 | `97dee173e7d16752ec482c05352dbd13c54958b3ab630270444f5ba07630aa47` | `6c73263c76e1203325bee239897779fb14f7c43878ed56d3f8aed3a29f10bc7d` |
| `skills/aisoft-platform/references/greenfield-planning.md` | 第一句去掉「已登记」，注明采用不需要平台登记 | `0e38f63249d42bd0e3a49fb8a4c6e2ef4dfca503f265cf2260ee1a2141c5061b` | `b63333a0a74d5e8d000e4d7fec5e46aceeeaad907c08f75892d87deaec461457` |
| `skills/aisoft-matt-workflow/SKILL.md` | 仓库初始化第 1 步改为按访问来源取证，project Agent 权限闸门只适用于站点加固访问 | `4a9c49d467fbb3ced1502db8863c73d9fb7aa469e1fe816350793c1c6df6cec9` | `b008bbaf40dfd0e3bbf5bbf085805bec45f10c6563c584a0056767c1c3d2b92c` |

新增小节的九条规则：不授权不覆盖、角色、读取、远端写入、任务书、版本不一致、依赖、不继承的职责、缺席与恢复。平台文字只用「跨项目协调工作区」这个中性名称，不出现 Home 的仓库名或任何项目名。

### 方案与决策

- **落点选在 `issue-session-flow` 而不是新 reference。** 调度会话的位置与职责本来就定义在这里；新增一个 reference 要改 bundle 成员集合、安装器与多处计数钉子，收益不抵成本。
- **D2 在平台写成缺省，而不是禁令。** 现行合同允许项目调度会话评论通知和建票，worktree 单写者规则也不直接禁止远端评论。所以平台只规定协调工作区对其他项目缺省只读，放宽要写进工作区仓库自己的已批准合同并服从目标项目规则。Home 的合同选 A，与缺省一致。理由是经站点 broker 的写入使用目标项目自己的 agent 身份，在 Gitea 上分辨不出是哪个会话发起的。
- **不改依赖门、不新增 CLI、不新增模板。** 交接任务书的模板先在 Home 试用；技能来源的自动核对工具确有需求时另立通用 Issue。
- **加一组合同钉子测试作为反向证明的载体。** smoke 的 `grep -Fq` 钉子是只减不增的棘轮，所以钉子加在已有的 `codex/runtime/tests/test_session_contract.py`：新小节存在且保留「不授权」「缺省只读」「待建票」三条关键规则，另两份文件不再出现旧表述。先看它红，应用补丁后变绿；删掉对应短语它必须再红。

### 必要配套范围

- 本目录四份映射文档、冻结补丁与方案副本是本票的合同与证据。
- 四份技能文件都是使用发布包成员。T01 用现有 release 工具在 `usage/bundle.json` 追加一个版本，不改成员集合与已发布历史。拟定 **1.25.0 / minor**：新增一个可选能力，对已采用项目没有新增义务。实施时以当时 fresh `origin/main` 的最新版本为准；被占用就顺延到下一个可用版本并同步本票证据。#450 的分支已登记 1.24.2，两票谁后合并谁在集成 `main` 后重发自己的版本。
- `docs/governance/review-evidence-index.md` 只追加本票最终交叉审查一行。本票没有路线图批次，也没有 E2E 或项目采用事件，不改对应表。
- 以上十三个 exact 路径是全部 git_scope。

### 不纳入

- 不创建 `admin/AISoftHome`，不为它建身份、凭据、保护规则或 CI，不运行 `usage-bundle.sh --adopt`，不执行任何试点交接。
- 不改 `AGENTS.md`、`CLAUDE.md`、ADR、`route-policy`、`execution-adapter`、`onboarding-runbook`、`project-align`、`usage/CONTRACT.md`、模板及其 digest、`03`/`04`/`08` 分册、runtime、broker、manifest、安装器、CI 与部署脚本。
- 不处理 `templates/docs/agents/issue-tracker.md` 里同类的「exact manifest project」旧句，也不处理 #419 范围 B 留下的四处 `$implement` 主路径旧句。D3 只授权两处一致性修正，这些留给下一个本来就要动它们的批次。
- 不打通正式跨仓依赖的 installed/live 验收，不扩大任何身份的权限，不引入新的技能体系、状态看板、自动同步、批量升级或无人值守引擎。
- 不在真实 HOME 安装技能，不让任何项目采用新版本。

### 后续阶段归属（不在本票实施）

| 阶段 | 归属 | 启动条件 |
|---|---|---|
| 最小 Home：建仓、采用、保护、CI、导航、本机映射约定、canary | Home 仓库自己的采用 Issue | 本票合并且新版本已发布；建仓、身份与凭据等动作各自取得授权 |
| 少量交接试点（D4 的三项） | Home 的交接记录；各项目自己的任务与证据 | Home 采用完成；只用已有授权任务或只读演练 |
| 按需求扩展 | 组织工具归 Home，业务能力归项目，通用能力回平台另立 Issue | 有真实重复成本与明确拥有者 |

Home 首建顺序沿用方案第 8 部分与校准附录的校准 4：先由有权人员建私有仓并提供可检出的最小 `main`，再在 Home 仓开采用 Issue，然后处理身份、保护、required CI、采用与 canary。`usage-bundle.sh --adopt` 在平台检出执行、目标指向 Home 的 change worktree；首次 push 与建 PR 的工作目录是 Home 的 change worktree，调用平台检出路径下的 `codex/tools/aisoft-access`；合并后改用 Home 自己的 `.aisoft/bin/aisoft-access`。`admin/AISoftHome` 当前是否已存在没有读回：它没有 typed 路由，匿名 404 不构成证据，留给建仓前由有权人员核对。

## Acceptance criteria

- [ ] AC-1：四份技能文件应用后的全文 SHA-256 与上表一致；补丁可反向匹配；改动以外的既有条文不变。
- [ ] AC-2：`issue-session-flow` 里跨项目协调工作区是可选的合法协调位置；文字明确它不授予访问权，不覆盖目标项目的规则、pin、路由、确认点与在途授权，不实现、不进入任何项目的 worktree，对其他项目缺省只读，不继承其他项目的清扫职责，项目没有它仍可独立工作。
- [ ] AC-3：任务书规则允许「待建票」交接且不编造编号；版本不一致按 D5 处理；真实跨仓前置按现有依赖身份规则保持阻塞。确认点数量、路由、单写者、人工合并与部署边界没有任何变化。
- [ ] AC-4：`greenfield-planning` 与 `aisoft-matt-workflow` 不再把平台登记或站点加固访问写成采用前置，表述与 ADR 0003 一致；`aisoft-platform` 写明协调工作区的项目目录不是访问来源。
- [ ] AC-5：平台新增文字不含任何组织或项目专属名称，泄漏守卫基线不增。
- [ ] AC-6：合同钉子测试在应用补丁前失败、应用后通过；删掉任一被钉短语时重新失败。
- [ ] AC-7：bundle 只追加一个新版本，既有历史与成员集合不变；隔离导出的 Codex、Claude、Cursor 三端对应技能文件与源码字节一致；真实安装与项目采用保持未执行。
- [ ] AC-8：exact scope、文档预检、完整 smoke、判级投影读回 `projected` 与实际候选的跨提供者独立审查通过；治理步骤独立 commit 后 STOP，fresh run 重读后继续，最终停在确认点 2 之前。

Issue 正文的方案阶段 AC-1 至 AC-6 由方案 v2.1 覆盖，对应关系见方案第 11 部分；那是方案覆盖说明，不是本票实施验收。

## 场景与反例

| 场景 | 按新文字应当发生什么 | 必须排除的误读 |
|---|---|---|
| 工作区会话收到一个只涉及单个项目的需求，该项目已有调度会话 | 核对 exact 仓库后把需求交回该项目调度，回收原 Issue 与 PR 链接 | 工作区不替项目拆票、派单或维护第二份状态 |
| 目标项目没有调度也没有 Issue | 产出任务书，Issue 写「待建票」；人在目标项目开会话，在该项目授权内建票 | 不为凑字段编造编号；不由工作区会话代建，除非工作区自己的合同已放宽 |
| 两个项目的 pin 不同 | 各按自己的 pin 执行；接收会话可做只读的来源观察并记录 | 不为交接升级旧 pin；不把「旧版没有某条规则」写成整个项目没有能力 |
| 目标检出在本机找不到 | 停下核实，如实报告 | 不猜路径、不自动 clone、不改投别的仓库 |
| 交付确实依赖另一仓库的 Issue，当前配置验证不了 | 保留 exact `owner/repo#N`，受影响交付阻塞，独立部分可继续 | 不改称关系说明，不换成裸编号或空依赖 |
| 工作区仓库不可用 | 项目从自己的合同与 tracker 继续；恢复后回源重读 | 旧快照不补写成当前事实 |
| 工作区目录里列了某个项目 | 只是导航 | 不因此获得凭据、读写、合并或部署权限 |

以上是文本合同审议，不是项目试点或模型行为实验。

## 风险与回滚约束

- 主要风险是把协调工作区读成新的权限来源、第二个调度权威或必经入口。由冻结文字、场景审议、合同钉子与实际新 HEAD 的交叉审查核对。
- 四份技能文件属于治理文件。T01 独立受控应用、commit 后 STOP；fresh run 重读批准合同、治理 diff、当前规则与 worktree/owner/HEAD 后继续，原批准持续有效。
- 路由 effort 为 max。实际会话强度由负责人在客户端设定，会话如实记录读到的实际值；与路由不一致时由负责人裁决并写入 `override_reason`，不由会话自行认定已满足。
- `usage/bundle.json` 与 #450 的分支会在同一位置追加版本，后合并的一方集成 `main` 时会冲突。处理办法是把该文件退回 `main` 原文后重发自己的版本，不手工拼接别人的 release 条目。
- 源码或隔离导出通过不能写成 installed 或 live 通过。本机生效需要负责人重装技能；项目要采用新版本各自走自己的升级 Issue。
- 未发布的候选通过本分支追加 revert 提交回退。合并后回退要开新 Issue 与 PR 恢复原文并追加修正版 bundle，不删除或改写已发布历史，也不自动改变任何项目的 pin。平台回退不会自动回退 Home；Home 要经自己的 Issue 回到已验证的版本。
- 停止条件：需要新引擎、新 CLI、扩大权限或修改不纳入清单里的文件时停止并升级；冻结补丁不能干净应用时停止分析，不模糊套用；smoke 暴露本票范围外必须同步的钉子时按范围扩张处理。

## 接口、数据与兼容性影响

没有 API、schema、运行时接口、依赖或数据迁移。broker 操作表、manifest 与访问来源规则不变。使用包格式和成员集合不变，只追加一个 minor 版本；已采用项目继续 pin 原版本，行为不变，只有自行采用新版本才得到新文字。旧 pin 的项目没有这一节，也能作为交接的接收方，因为接收方只按自己的合同执行。模板未修改，不刷新 change-template-sync digest。

合并后的维护层动作不在本票授权内：负责人在 Mac 重装技能（`skills/` 被改动），会话读回 `check-installed-drift.sh` 与 `aisoft-platform-readiness.sh` 并把结论写成 Issue 评论。VM 不装技能，不需要重装。

## 未决问题

无。D1–D6 与 Home 参数已由负责人确认，冻结文字见补丁。实施中出现实质范围变化、授权冲突或可靠反证时，按既有合同升级。
