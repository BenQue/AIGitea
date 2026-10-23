---
name: aisoft-platform
description: AISoft 自托管交付平台（v3.6）的合同与操作入口。Use when 在已接入平台的项目上开发/修复/部署、接入新项目到平台、走 Issue→triage→spec/plan→实现→PR→部署流程、检查私有 Gitea 仓库/Issue/PR/Actions/分支保护、或排查平台 CI/部署/agent 问题。Also use to operate or onboard projects on the AISoft self-hosted Gitea delivery platform: Issue analysis, small-or-complex routing, spec/plan contracts, session implementation work, provider coexistence, CI/deployment incidents, first non-production deployments, rollback planning, production script boundaries. 触发词：AISoft、AIGitea、新用户上手、平台 VM、Gitea Issue、判级、small/complex、change 分支、host-access broker、architecture lock、部署失败、接入平台、project-align。
---

# AISoft 自托管交付平台（v3.6）

自托管的「Issue → AI 分析判级 →（small 直进 / production complex 先 spec/plan / development complex 用 Issue 验收合同）→ 提交确认 → 单 PR → 人工合并 → 独立部署授权」平台。核心原则：**Issue 定义工作，AI 会话把明确合同做到最终 PR；人确认提交，人合并；部署不由 merge 授权。** VM 上的 Development Loop 与 routine 自动合并已按 ADR 0002 退出（#391）。

本技能是唯一来源，由平台安装器生成各工具的落点。文中 `$名称` 表示“调用名为该名称的技能”，各工具按自己的方式调用。

文中 `aisoft <子命令>` 是随使用发布包分发的会话工具：项目内是 `.aisoft/bin/aisoft`，平台仓内是同一份源文件，不需要平台检出。`aisoft version` 自报 `bundle_version` 与源 SHA，`aisoft project-check` 的 `tool-provenance` 核对它与项目 lock 一致。子命令与合同见项目内 `.aisoft/platform-usage.md`「会话工具」。只有平台维护者在平台检出里做的步骤才写平台路径，放在标题含「维护层」的小节。

## 读合同

动手前先读 `README.md` 与对应分册。平台检出的权威根目录以 broker manifest `codex/config/host-access-broker.json` 的 `site` 段为准：Mac 上是 `site.platform_checkout_mac`，OrbStack VM 上是经 `/mnt/mac` 挂载的 `site.platform_checkout_vm`。检出**不能**放在 `~/Documents`、`~/Desktop`、`~/Downloads` 下：macOS TCC 挡住 `/mnt/mac` 访问这三个目录，`sudo` 也无效（见 `01` §1）。

- `03`：Issue、判级、文档、标签与最终 PR 闸门。
- `04`：Matt 编排、判级输出与自动化引擎迁出说明。
- `02` 与 `06`：部署与事故；`06` 另有 broker 与踩坑。
- `08`：双工具共存、两层验证矩阵与交叉审核。
- `architecture/` 等子合同目录以 README 目录为准。

## 现行合同（v3.6，#208 governance source）

- **可读命名元组**：新变更 = Issue `N` + 分支 `change/N-短描述` + 目录 `docs/changes/N-短描述/` + worktree `issue-N-短描述` + 唯一 PR（`Closes #N`）。编号仍是唯一主键；remote/history evidence 已存在的 `change/N`、`docs/changes/N/` 与 pre-#57 纯数字文档只作读取或维护兼容，新 writer、first push 和 first PR 不得创建。
- **语义文档**：新文档名 `<role>-<短描述>-<YYMMDD>.md`，summary front matter 的 `documents` 字段映射 summary/spec/plan/verification 到真实文件名。解析用 `aisoft resolve-documents N`，不要 glob 猜。
- **判级**：contract_effect 先行（restore/unchanged → small 候选；add/change → complex；unclear → 人工澄清）。功能新增/变更、schema/迁移、外部契约、安全、共享核心、跨模块、CI/制品/部署/回滚、Agent/治理一律强制 complex。small 还须范围局部、可简单 revert，并有可测验收标准。显式要求 complex 照办；要求 small 不能绕过 AI 校验与强制 complex 规则。
- **文档要求**：production complex 必须有映射的 spec 与 plan；development complex 从 Issue 读取可测验收标准并用合成 `T01`；已验证的 small 与 development complex 不写仪式性 spec/plan。验收证据不能由 diff review 与 required CI 重放时声明 `verification`；部署与迁移总要它，但 `verification` 不等于部署。
- **Matt 主路径**：开发方式以 [路由表](references/route-policy.md) 为准。每个 Issue 走 `$triage #N` → production complex `$to-spec #N` → `$to-tickets #N` → 按计划执行（Claude 与 Cursor 用 superpowers `executing-plans`，Codex 用 `$implement #N Txx`）（平台适配规则见下文「外部技能包边界」；small 与 development complex 在 triage+summary+判级+`approved` 复核后跳过 spec/plan，后者使用合成 `T01`）。`triage/ready-for-agent` ≠ `approved`；`approved` 只授权开始实现，不授权 merge 或部署。仓库初始化调用 `$setup-matt-pocock-skills`（tracker 选 `Other`），使用 `templates/docs/agents/` 的 tracker、triage、domain 三份文件；Codex 侧经 `aisoft-matt-workflow` 适配器串起这一步。
- **路由**：`$triage #N` 与平台判级之后，显式指定 provider，查 [route-policy](references/route-policy.md) 得到八键 `route:` 与 summary 顶层 `route_provider`，把执行/核验义务展开为具体技能再写入合同与判级评论。历史卡只读兼容，执行时重新解析，不猜 provider。确认点 1 展示具体路由；人覆盖某格写入 `override_reason`，不能把强制 complex 降为 small。默认分工不变，其余技能按 Issue 选择并记录；模型按 tier 选，型号映射见 `08` §7.3。
- **执行与审查适配**：按 [execution-adapter](references/execution-adapter.md) 处理 Txx→Task N、frontier/恢复、开始前 BASE、本地提交后的固定候选与实际新 HEAD 审查。small/SP 不增加 Matt 每票双轴义务。新 helper 的接口合同不是运行可用证明，缺能力如实报告 GAP。
- **27 标签四维正交**：10 `type/*`（bugfix/feature/docs/test/refactor/maintenance/platform/security/reliability/data，Issue 作者输入，AI 按证据核对或更正一个主类型）+ 2 `complexity/*`（AI 输出，不是作者覆盖）+ 8 生命周期（`completed` 与 `deployed` 互斥终态；`completed` 是合并且无需部署，`deployed` 要求确定性部署与验证）+ 7 `triage/*`（Matt 编排）。
- **单闸门**：最终 PR merge 是唯一交付硬闸门，只由人合并。会话与 project agent 不 merge、不直推受保护 `main`；部署需独立授权。
- **一切 Gitea/Git/OrbStack 访问走 broker**：`/usr/local/libexec/aisoft/host-access-broker --project <manifest项目> --operation <typed操作>`（gitea.issue.create/read/update、gitea.pull.create、git.push.change --branch、host.access.audit…）。不拼 raw token、不传 URL/refspec/shell；Git push 只允许当前 checkout 同名 readable 分支。
- **没有无人值守引擎**：自动化最多止于 PR 候选，重建条件见 ADR 0002「重开条件」。
- **部署边界**：流程不变量全平台一致——不可变制品、测试与生产同字节晋级、真实健康检查、可回滚、生产 script-only；AI 可参与开发/测试环境首次部署并固化为脚本（两次幂等 + 一次故意失败回滚），生产只跑已验证脚本。交付形态由项目自己的 profile 与 `AGENTS.md` 声明和实现，平台不规定。

## 共享工程原则

方案、实现与审查参考 [共享工程原则](references/engineering-principles.md)。首次使用时阅读，本会话已读且内容未变时不重复加载。

## 目标项目与 governance manifest

任何 Gitea 或 Git 写操作之前先显式选定目标项目。broker manifest 的 `projects[]` 把一个项目 id 绑定到 exact 仓库、project agent 与 Mac checkout。不要从别的项目或示例推断目标仓库，也不要让两个项目共用 worktree。

每个本地 Gitea 软件仓库必须先登记在严格的 `codex/config/gitea-governance.json`（Issue #35 governance 合同已生效）：校验 manifest，为一个 exact 仓库引导非 site-admin 的平台 manager，只读跑 governance `check`，再用 manifest 声明的 project agent apply 这一个仓库。未知仓库只报告；不从发现结果推断可见性、归属或权限。

每次变更都要求 exact 仓库、Issue #35、字节一致的已合并平台 SHA、manager 变更凭据与新的证据目录；工具必须读回 private/public 可见性、manager=Admin、project-agent=Write、无跨项目 Write/Admin、合并后删分支与受保护 `main`。直推与 force push 关闭，所有仓库只有人能合并。

routine 自动合并已退出（#391）：broker 没有合并操作，manifest 的 routine 字段已随 #397 删除，合同拒绝再声明。源码声明、安装字节、凭据下发、保护规则 apply 与 live 读回是各自独立的证据，不能互相推断。

共享 `ci-bot` collaborator 闸门已退役：`ensure-gitea-collaborator.sh` 只作历史兼容与回归测试证据，不得用于接入、修复任何项目，也不得作为 broker 的回退路径；见 `06` §「旧 `ci-bot` gate（已退役）」。

不要把变更路径当检查捷径。优先用 broker 的 exact 项目路由；跨项目的设置与保护盘点用 manager audit PAT 与 `gitea-governance.sh check`。

## 私有 Gitea 的确定性访问

检查私有仓库、Issue、PR、Actions run、分支保护或仓库设置之前，先读 [references/private-gitea-access.md](references/private-gitea-access.md)。

- 先解析并核实 exact Gitea remote 或 broker manifest 项目。
- 不要从匿名 API 请求开始。private-repository `404` 或 Git `Repository not found` 不能证明对象不存在。
- 优先用 broker 的 exact 项目路由与最小权限身份；读 Git ref 时复用已配置的 Git credential helper。
- 跨项目只读盘点设置与保护用独立的平台 manager audit PAT，不用变更 PAT 或普通 Git 代替。
- 没有 broker route/manager 或 ACL 挡住 exact 目标时，VM 本地管理员凭据只能用于经授权、脱敏的只读 helper 调用；不要把凭据复制到 Mac，也不要扩大 bot 权限。
- helper 不可用或需要界面证据时，已登录的浏览器会话可作只读后备。
- 网络、凭据可用性、仓库 ACL 与对象是否存在，分别作为独立事实报告。

## approved 之后默认自主推进

人在确认点 1 确认合同后，以下动作不再逐项询问：证据收集与判级、合同文档补齐、合同内实现与本地原子 commit、测试与普通修复、必需的更宽闸门（smoke、required CI）、判级投影，以及确认点 2 之后的 push、唯一最终 PR 与 PR CI 修复。不要把每张 ticket、每条测试命令、每次 commit 或 CI 重试变成确认点；合同里已定下的选择不再重问。两个确认点的格式由 `issue-session-flow` 负责。

治理变更按获批 complex 合同独立受控应用、commit 后 STOP；fresh run 重读合同、治理 diff、当前规则与
worktree/owner/HEAD 后继续。原批准持续有效，不重复启动确认；具体交接遵循 execution-adapter。

会话自己处理普通的编译、lint、类型、测试、构建、浏览器与 CI 失败。受治理的状态只有 `AWAITING_PR_CONFIRMATION`、`READY_FOR_REVIEW`、`NEEDS_HUMAN_DECISION`、`BLOCKED_EXTERNAL`、`FAILED_LIMIT`。未运行的检查永远不能写成通过。

## 只在这些情况暂停

合同冲突；范围扩张；破坏性迁移；新的安全/权限/架构决策；任何直接生产动作；外部依赖缺失（凭据、服务、权限）；验证不可靠（环境不可达、结果不可复现）；同一根因连续三次失败；达到配置的上限。宿主要求的 sandbox/网络授权是执行许可，不是新的产品决策。暂停时报告真实 blocker 并等人，不自行决定。

## PR URL 回填

确认点 2 之后用一条命令开 PR：`aisoft open-pr N --title <标题> --body-file <正文文件>`（#408）。它先在本地校验正文
（恰好一行 `Closes #N`，映射 summary 路径恰好出现一次，不合格时不发任何 broker 请求），再依次经 broker 首推 change 分支、
`gitea.pull.create`、回填 summary 并只提交这一份、运行 `check-change-documents`、经 broker 再推同一分支。任何一步失败就停下报告；
重跑安全：同一 change 已有开放 PR 时 broker 返回原 PR，回填已是同值时不再提交。

手工修复时，会话用 broker `gitea.pull.create` 建 PR 后必须运行
`aisoft backfill-pr-url N --pr-url <实际 PR URL>`，
把 PR 的 URL 写进映射 summary 的 `pr_url` 并把 `status` 推进到 `pr-open`，只提交这一份文档，并经 broker 推送同一个 change 分支（#142/#146）。`pr_url` 只写在 summary 里，spec、plan 与 verification 不带它；PR 存在之前留空、保持真实的 PR 前状态。summary 没有声明 `pr_url` 或已经声明了另一个值时，工具拒绝并要求人决定——一个 change 只有一个 PR。回填后对更新过的 checkout 运行 `check-change-documents`。

summary-only 回填会产生一个合法的新 head。在后续 push 之前，审查只含映射 summary 的实际 URL/status diff，运行文档检查，核对归属、exact branch 与干净的工作树，记录本次 fresh 验证的 exact head 并把 `pushed_head` 与它比较。范围内 CI 修复走同样的 fresh 验证与读回规则。首次 push 仍与确认点 2 已验证的候选比较。授权绑定 exact Issue/branch，合法 commit 不逐个确认；范围扩大、他人改写或任何不匹配立即停止。完整比较合同见 `issue-session-flow`。检查任何 checkout 用 `aisoft check-change-documents --repo <checkout>`（缺省当前仓库）。

## 会话标准动作（Mac 交互开发，最常见）

> **会话本身的编排**（一 Issue 一会话、合同/启动确认、提交 PR 确认、人工合并、merge 后确定性收尾与归档）见 `issue-session-flow` 技能；本段只覆盖单个会话内部到 PR candidate 为止的动作。

1. 需求/缺陷 → broker `gitea.issue.create`，必须带 `--entry-label`（`needs-analysis`，或 triage 入口 `triage/needs-triage`）；正文写可测验收标准，衍生 Issue 另写来源会话、目标项目与已知依赖（`03` §1）。
2. `aisoft change-name N <slug>` 校验命名 → `git worktree add /private/tmp/issue-N-<slug> -b change/N-<slug> origin/main` → `aisoft claim-worktree`（并行会话必须各自 worktree；commit 前 `git branch --show-current` 核对——`06` 踩坑 15）。
3. 按判级与 `change_control` 写映射文档（production complex 补 spec/plan；development complex 从 Issue 读取验收标准并用合成 `T01`），实现 + 测试全绿（改 shell 后跑 `bash codex/tests/smoke.sh`）。`verification` 由证据能否经 diff review + required CI 重放决定，不等同部署。summary 此时写**真实的**前置 `status`（通常 `approved`），`pr_url` 留空——PR 还不存在。
4. 判级投影：`aisoft classify N` 看计划与路由行 → `aisoft classify --apply N` → `aisoft classify --verify N` 读回两个维度都 `projected` 才算完成；窗口在合并时关闭，closed Issue 永不补写。读到 `broker-operation-missing` 见 `06` 踩坑 20，结论与 Gitea 事实不符见踩坑 21。
5. 平台仓的 complex 变更：进入确认点 2 之前，由未参与实现的另一方提供者对候选 head 做一次只读交叉审查，结论记入 verification（`03` §「交叉审核」）。
6. 本地验证完成后进入 `AWAITING_PR_CONFIRMATION`（候选格式见 `issue-session-flow`）；确认后 `aisoft open-pr N --title <标题> --body-file <正文文件>` 一步完成首推、建 PR、回填与再推（见上文「PR URL 回填」），**到开 PR 为止**；`pr_url` 合同见 `03` §3。
7. push 报 `BASE_BRANCH_STALE`：broker `git.fetch.main` → 把 `origin/main` 集成进本分支（已推送过的分支用 merge commit；从未推送的分支也可以本地 rebase）→ broker 重推（remote 只走 broker，集成是本地操作）；lease 语义见 `06` §1.0。
8. push 报 `REMOTE_BRANCH_MOVED`：推送已被拒、远端未被覆盖，先 broker `git.fetch.change --branch change/N-<slug>` 看清远端再决定，不用更强的 force 压过去；见 `06` §1.0。

## 部署边界

已接入且有部署范围的应用：协助设计并执行第一次真实的开发/测试环境部署，把手工步骤转成版本化脚本，从可重复的状态连跑两次，并演练一次故意失败与回滚。AISoftPlatform 这类纯文档平台仓不需要应用部署流水线。

生产环境只运行已验证的制品与脚本。出现故障时停止或回滚、收集脱敏证据，在非生产复现、修复、验证并准备 PR。永远不要生成或执行临时的生产命令。

## 保护平台

- 会话、project agent、manager 与共享 bot 都不得 merge PR。永远不直推受保护 `main`。
- 保住 `CI / test (pull_request)`、不可变制品、环境隔离、真实健康检查与回滚。
- 不打印 token、密码、`.env`、认证文件或 Git 凭据。
- 不为方便只读检查而新增凭据或协作者权限；账号与仓库变更只属于已合并的 governance manifest 与 exact-repository 工具。
- Gitea manager/project PAT、OrbStack 宿主控制、VM 运维账号与各项目部署身份彼此分离。Gitea 凭据不授权 SSH、sudo、VM 生命周期、数据库或生产访问。
- 各工具的配置互相独立，共用同一平台合同与会话验证流程。

## 工具分工

Claude 与 Codex 在平台维护层共用同一平台合同，能力等价、可互换、不分主辅；两个模型互相取长补短、目标一致，都不各自发明判级、文档或交付流程。complex 平台变更由未参与实现的一方做交叉审核。项目使用层可按项目 `AGENTS.md` 选用 Claude、Codex 或 Cursor，合同入口是项目内 `.aisoft/platform-usage.md`。

本技能需要的能力按能力名描述：**并行代理**（没有时串行执行，只读调查才可并行）、**技能调用**（没有时直接读对应 SKILL.md 照做）、**向人提问**（没有时在回复里列出选项并停下等答复）。

`gitea-analyze-change`、`gitea-spec-plan`、`gitea-development-loop`、`gitea-implement-change` 只是兼容 adapter，不是第二套开发方法，仅用于 Gitea 标签投影、语义文档解析/发布与旧调用方；`gitea-platform-ops` 独立负责平台证据、首次非生产部署、事故与回滚。这五个 adapter 与 `aisoft-matt-workflow` 只装在 Codex 落点。

## 外部技能包边界（Matt / superpowers）

平台不改写两个技能包的原文，只在这里约束它们在平台项目内的用法。Matt 的同一组约束在 Codex 侧由 `aisoft-matt-workflow` 技能承载（源文件 `skills/aisoft-matt-workflow/SKILL.md`），与本节逐条对照。

两个技能包任一发生大版本更新、或含技能增删的更新时，安装或升级之前先按 `08-双工具共存与实施.md` §5
「外部技能包升级后的适配检查」人工逐项核对（技能增删、调用方式、文件与目录约定、Git / PR / 并行写入
副作用），结论写进承载该次升级的 Issue。这是人工清单，不据此设定时任务、自动检查或安装。

**Matt（`mattpocock-skills`）**：钉在 v1.3.1（`24fe0ef7737efae15c87225755e9f6f5965e4888`）。Claude 侧是插件技能
`mattpocock-skills:<技能名>`，期望来源是仓库根 `.claude-plugin/marketplace.json` 的
`mattpocock-skills@aisoft-platform`，`bash skill-for-claude/check-plugin-pin.sh` 读回 `PIN_CLEAN`
才说明已装插件就是这个 commit；Codex 侧由平台安装器装同一 commit 的 vendor 快照。读到 `PIN_DRIFT` 或 `PIN_NOT_INSTALLED` 时不要声称已是
v1.3.1，也不要自行注册 marketplace、安装或升级插件——那是需要单独授权的 installed 层动作。各工具的版本核对是维护层动作：平台维护者在平台检出里运行只读的 `check-external-skill-versions.sh`。

- **`pr`**：只生成候选正文，结构为 Summary / Evidence / Merge Danger。每条观察写明 SHA、命令或
  制品，以及它属于 source / local / CI / installed / live 哪一层；缺少 Before 证据要明说，未执行项
  记 `NOT RUN`。正文服从 broker `gitea.pull.create` 的正文合同（恰好一行 `Closes #N`，映射的
  summary 路径恰好出现一次）。这个技能不授予 push、PR、merge 或部署权限，这些仍在确认点 2 之后
  经 broker 进行。
- **`implement-spec`**：随技能包存在，但它的写入编排在平台项目内禁用。保持 change worktree 的单写者
  frontier：不 reset、不合并子代理产物、不并行写入、不提前开 PR、不投影 ticket 状态。要换编排方式，
  先为它开一份自己的 complex 合同。
- **`retro`**：仅在人明确要求 Matt 的 retro 时加载；人可以指定会话，否则只看当前会话。别的技能包
  也提供同名技能时，先确认要的是哪一个，不覆盖、不改名上游技能。只输出有证据的改进候选供人审查；
  不自动修改治理文件、不扩大权限、不启动自主回顾循环。
- **domain 文档**：读 `docs/agents/domain.md`。新项目用 `GLOSSARY.md` 记术语、`docs/adr/` 记决策；
  既有 `CONTEXT.md` / `CONTEXT-MAP.md` 与新文件并读，直到其中的术语、业务规则、决策和入链都有着落。
  定义冲突时停止，不自动改名文件或丢弃规则。

**superpowers**：Claude 与 Codex 跟随各自的官方 marketplace 同步，平台不安装；平台 pin 在 7.0.0
（`bb92a77741419a4ab5f06e711a283343f1ada0c3`，vendor 快照 `codex/vendor/superpowers/v7.0.0/`），作为三端核对基准，并由发布包导出到
项目级 `.cursor/skills/`。`check-external-skill-versions.sh` 读到某端 `PIN_DRIFT` 时先过适配清单，不要声称该端已是 7.0.0。
它的流程技能三端照常使用，落点与收尾服从平台合同：

| superpowers 默认 | 平台项目内 |
|---|---|
| 设计写 `docs/superpowers/specs/`，计划写 `docs/superpowers/plans/` | 写进 `docs/changes/N-short-description/` 里映射的 `spec` / `plan` 角色文档；small 只有 summary，不另建设计文档 |
| `.superpowers/` 下的工作目录 | 本地状态，已在 `.gitignore` 里，不入库、不当验收证据 |
| `finishing-a-development-branch` 提供本地 merge、`git push`、建 PR | 三项都不可用。本地验证完成后停在 `AWAITING_PR_CONFIRMATION`；确认后远端只走 broker |
| 并行子代理各自实现 | 一个 change worktree 同一时刻只有一个写者：子代理不得并发写入它，也不得写别的会话的 worktree；只读调查可以并行 |
| `dispatching-parallel-agents` 并行派出子代理 | 只用于只读调查 |
| `subagent-driven-development` 每个任务派一个实现子代理 | 只许顺序派发，一次一个写者，只写本 change worktree |
| `brainstorming` 自己定级：快速任务直接做、小改动在聊天里确认后就做 | 它的定级与聊天内确认不替代平台判级与 `approved`；写文件前仍要有 Issue、判级与确认点 1 |
| `executing-plans` / task-start 按 Task N 读取计划 | canonical Txx 保持唯一合同，通过 execution-adapter 生成派生视图；不直接把 Txx 文件当兼容 Task N |
| task-done、一次修复裁决、清理 scratch | 依 execution-adapter 校验 AC/提交/真实结果并保全证据；局部 complete 不替代平台最终另一 provider 新 HEAD 审查 |

## 接入新项目 / 项目对齐 / 私有访问

- 新用户上手：用户要按自己所用的 AI 工具配好本机并开始第一个项目时，按 [references/getting-started.md](references/getting-started.md) 一步一步带用户走。
- 新项目接入：改基础设施之前先读 [references/onboarding-runbook.md](references/onboarding-runbook.md)——governance manifest + project-agent gate、host-role gate、architecture 声明、CI/部署与验收顺序都有既定约定，不得跳步。
- 项目对齐（初始化=更新，幂等）：入口 [references/project-align.md](references/project-align.md)——checklist 盘点缺口、逐项走目标仓独立 Issue/AI 判级的单一 PR，不假设每个对齐缺口都是 small；确定性核对用 `aisoft project-check`（PASS/GAP，只读）。项目按版本化使用发布包对齐：合同入口是项目内 `.aisoft/platform-usage.md`，版本以 `.aisoft/platform-usage.lock.json` 为准；导出与生成采用改动是维护层动作（`project-align.md`「维护层」节）。
- 私有 Gitea 检查：先读 [references/private-gitea-access.md](references/private-gitea-access.md)；**匿名 404 不构成不存在证据**，按 authenticated ladder 走。

## Common Mistakes

- 用数字命名新建分支/文档（`change/N`、`00-summary.md`）——新写入会被 fail-closed 拒绝；readable 元组才是现行合同。
- 绕过 broker 直接 `git push`/裸 token `curl`——治理写路径只认 broker typed 操作。
- 把 `triage/ready-for-agent`、green CI 或 Issue `approved` 当成合并或部署授权——合并只由人做，部署仍需独立授权。
- 让会话或 project agent 自己 merge——必须 fail closed；source merged 也不等于 credential/protection/live 已 apply。
- 把 merge 当成部署授权或 `deployed` 证据——merge 不调用 deploy，也不传递生产授权。
- 把判级投影留到收尾再补——窗口在合并时关闭，closed Issue 永久拒绝补写；进入待合并前必须用 `aisoft classify --verify N` 读回 `projected`（#167）。
- 把 broker 的 `REQUEST_DENIED / not allowlisted` 当权限问题查——那是安装期操作表陈旧，两台重装即可（`06` 踩坑 20）。
- 在共享 checkout 并行开会话不建 worktree——HEAD 是全局可变状态，B 的 commit 会落进 A 的分支（`06` 踩坑 15）。
- 从任何示例项目推断目标仓库/端口/部署合同——一切以显式 manifest 为准。
- 把平台 candidate/参照实现写成业务已部署——一个项目在某个环境的证据不等于其它项目或生产完成。
