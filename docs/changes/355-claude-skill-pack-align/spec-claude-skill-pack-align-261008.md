---
issue: 355
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/355
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
depends_on: []
status: approved
branch: change/355-claude-skill-pack-align
created: 2026-10-08
updated: 2026-10-08
---

# Spec · Claude 侧外部技能包对齐

## 目标与原因

让 Claude 侧对两个外部技能包（Matt Pocock skills、superpowers）的平台合同与 Codex 侧等价，
且这份等价可以被离线检查，而不是靠两边各自的印象：

- Matt 插件的来源由平台仓决定，钉在与 Codex vendor 快照相同的 commit。
- v1.3.1 的四条边界规则在 Claude 侧始终在场，不依赖 Claude 侧并不存在的技能。
- superpowers 的默认落点与收尾菜单有明确的平台映射。

本票是 source 层：只交付仓库内的条目、规则文本、检查与测试。不安装、不升级任何插件。

## 设计决定

### D1 marketplace 条目放在仓库根

文件为 `.claude-plugin/marketplace.json`，marketplace 名为 `aisoft-platform`，只含一个条目：

| 字段 | 值 |
|---|---|
| `name` | `mattpocock-skills` |
| `source.source` | `url` |
| `source.url` | `https://github.com/mattpocock/skills.git` |
| `source.ref` | `v1.3.1` |
| `source.sha` | `24fe0ef7737efae15c87225755e9f6f5965e4888` |

- 条目不写 `version`：上游该 commit 的 `plugin.json` 已是 `1.3.1`，两处都写时 `plugin.json` 生效且
  `claude plugin validate` 告警。
- 放在根的原因：`claude plugin marketplace add` 只认 marketplace 根下的
  `.claude-plugin/marketplace.json`。放在根，按目录注册与按 git URL 注册（跟踪受保护 `main`）都
  可用；放在子目录则 git URL 注册必须另写 `extraKnownMarketplaces` 的 `path`。
- 本票不把该 marketplace 写进任何 `.claude/settings.json`，不注册、不安装。
- superpowers 不入此 marketplace，版本跟随官方来源。

### D2 pin 检查是独立工具

`skill-for-claude/check-plugin-pin.sh`（薄封装）调用 `skill-for-claude/check-plugin-pin.py`，
只读，不写缓存、临时文件或报告。

**source 模式**（`--source-only`）做三方相等：

1. marketplace 条目的 `source.ref` 等于 `codex/install-skills.sh` 的 `matt_version`；
2. `codex/vendor/mattpocock/<ref>/manifest.json` 存在且其 `tag` 等于 `ref`；
3. 条目的 `source.sha` 与该 manifest 的 `commit` 逐字相同，`source.url` 与 manifest `source`
   指向同一仓库。

全部成立输出 `PIN_SOURCE_OK` 并以 0 退出；任一不成立输出 `PIN_SOURCE_MISMATCH: <原因>` 并以 1 退出。
条目缺失、重复、JSON 不合法、`matt_version` 不是恰好一处，都按不成立处理。

**installed 模式**（`[target-home]`，缺省 `$HOME`）先跑 source 检查，失败则以 2 退出、不读安装面；
随后只读 `<target-home>/.claude/plugins/installed_plugins.json`：

| 情形 | 首行结论 | 退出码 |
|---|---|---|
| 文件不存在，或其中没有任何 `mattpocock-skills@*` 记录 | `PIN_NOT_INSTALLED` | 0 |
| 仅有 `mattpocock-skills@aisoft-platform` 记录，且每条 `gitCommitSha` 等于 pin | `PIN_CLEAN` | 0 |
| 存在来自其它 marketplace 的 `mattpocock-skills` 记录 | `PIN_DRIFT` | 1 |
| pin 来源的记录 `gitCommitSha` 缺失或不等于 pin | `PIN_DRIFT` | 1 |
| 文件不是可识别的 schema（顶层 `version` 非 2、`plugins` 结构不符、JSON 不合法） | `PIN_UNREADABLE` | 2 |

- `PIN_DRIFT` 之后逐条输出 `DRIFT: <plugin id> scope=<scope> version=<v> commit=<sha|missing> expected=<pin>`。
- 判定主键是 commit。版本号只作旁证输出：本机实测存在「同为 1.2.3、commit 不同」的记录。
- 与同目录 `check-drift.sh` 的退出码语义一致：未安装为 0，漂移为 1。
- 不读取 `settings.json`、任何凭据文件或环境变量中的凭据；是否启用不参与判定，已安装即计入。
  输出不含 `installPath`、`projectPath`。

不并入 `check-drift.sh` 的原因：后者回答「仓库装出去的技能字节是否一致」，装完隔离 HOME 必须读回
`CLEAN`（AC-3）；插件由 Claude Code 自己安装，两者的属主与生命周期不同。同理不进入
`codex/tools/check-installed-drift.*` 的八安装面。

### D3 规则内联进 `aisoft-platform` 技能

在 `skill-for-claude/aisoft-platform/SKILL.md` 新增一节「外部技能包边界」，包含：

- `$name` 记法在 Claude 侧对应插件技能 `mattpocock-skills:<name>`；期望 pin 与检查命令。
- **pr**：只产出候选正文，结构为 Summary / Evidence / Merge Danger，每条观察写明 SHA、命令或制品及其
  所在层；正文服从 broker `gitea.pull.create` 的正文合同；未执行项记 `NOT RUN`；不授予 push、PR、
  merge 或部署权限。
- **implement-spec**：随插件存在，但其写入编排在平台项目内禁用；保持 Controller 的单写者 frontier，
  不得据此 reset、合并子代理产物、并行写入、提前开 PR 或投影 ticket 状态。
- **retro**：仅在人明确要求 Matt 的 retro 时加载；同名技能先确认来源；只输出供人审查的改进候选，
  不自动修改治理文件、不扩大权限、不启动自主回顾循环。
- **domain 文档**：读 `docs/agents/domain.md`；新项目用 `GLOSSARY.md` 与 `docs/adr/`；既有
  `CONTEXT.md` / `CONTEXT-MAP.md` 与新文件并读，定义冲突时停止，不自动改名或丢弃规则。
- **superpowers 映射**：设计与计划写入 `docs/changes/N-short-description/` 的映射角色文档，不写
  `docs/superpowers/`；`finishing-a-development-branch` 的本地 merge、`git push`、建 PR 选项在平台
  项目内不可用，本地验证完成后停在 `AWAITING_PR_CONFIRMATION`，远端只走 broker；并行子代理不得
  向同一 change worktree 并发写入，也不得写别的会话的 worktree；`.superpowers/` 是本地工作目录，
  不入库；版本跟随官方 marketplace。

同时把「经 `$aisoft-matt-workflow` 适配」改为指向本节，并写明 Codex 侧 adapter 的仓库内路径
`codex/skills/aisoft-matt-workflow/SKILL.md` 仅作对照来源，Claude 侧不作为技能加载。

`skill-for-claude/issue-session-flow/SKILL.md` 只加指向性的短句（Red Flags 与 Common Mistakes 各一条），
不复制规则正文。

不新装 adapter 技能的原因：新增 Claude 技能须改 `AGENTS.md` 的目录描述，超出本票边界；独立技能
要靠模型主动加载，`pr` 被自动触发时不保证在上下文里。

### D4 等价性由 smoke 守卫钉住

`codex/tests/smoke.sh` 新增三组守卫：

- **可解析性**：`skill-for-claude/*/SKILL.md` 中每个 `` `$<name> `` 记法的技能名，必须属于 vendor
  manifest 的技能集合；否则失败并指出该名字。
- **两侧对照**：pin commit 在两侧文本中都出现；四条规则各有一对锚定短语，Claude 侧中文、
  Codex 侧英文，任一侧缺失即失败。
- **落点**：仓库内不存在 `docs/superpowers/`；`.gitignore` 含 `.superpowers/`。

## Acceptance criteria

沿用 Issue #355 的 AC-1 至 AC-7，下列为可观察的判定方式。

- [ ] **AC-1** `.claude-plugin/marketplace.json` 存在且可解析；`check-plugin-pin.sh --source-only`
  在当前树输出 `PIN_SOURCE_OK`；把条目 `sha` 或 `ref` 改成别的值的 fixture 输出
  `PIN_SOURCE_MISMATCH` 并非零退出；该检查登记在 smoke 中执行。
- [ ] **AC-2** fixture 覆盖一致（`PIN_CLEAN`）、不一致（非 pin commit、非 pin marketplace 各一例，
  `PIN_DRIFT`）、插件缺失（`PIN_NOT_INSTALLED`）三种情形，另加 schema 不可识别（`PIN_UNREADABLE`）；
  fixture 中放置的凭据样式字符串不出现在任何输出里；工具源码不打开 `installed_plugins.json` 与仓库
  自有文件之外的路径。
- [ ] **AC-3** Claude 侧技能含 D3 的四条 Matt 规则；可解析性守卫通过，且对重新写入
  `$aisoft-matt-workflow` 的副本变红；`skill-for-claude/install.sh` 装到隔离 HOME 后
  `check-drift.sh` 读回 `CLEAN`。
- [ ] **AC-4** Claude 侧技能含 D3 的 superpowers 映射；`.gitignore` 覆盖 `.superpowers/`；
  `codex/vendor/**` 与两个上游插件的原文零 diff。
- [ ] **AC-5** 两侧对照守卫通过，并对删除任一侧锚定短语的副本变红；verification 另附四条规则的
  逐条对照表。
- [ ] **AC-6** `bash codex/tests/smoke.sh`、新增与改动 shell 的 `bash -n` 与 ShellCheck、
  `resolve-documents 355`、`check-change-documents` 真实通过；diff 中没有删除测试、弱化断言或 skip。
- [ ] **AC-7** verification 按 source / local / CI 与 installed / provider-session 分层；插件升级、
  marketplace 注册、两 provider fresh-session 行为明确指向 #354 并记 `NOT RUN`。

## 接口、数据与兼容性影响

- 新增对外接口：marketplace 名 `aisoft-platform`、插件 id `mattpocock-skills@aisoft-platform`、
  `check-plugin-pin.sh` 的四个首行结论与退出码。技能前缀由插件自身的名字决定，仍是
  `mattpocock-skills:`，不因 marketplace 改变。
- 升级 pin 的合同：今后升级 Matt 版本，须在同一变更内同时改 vendor 快照、`matt_version` 与
  marketplace 条目；三方相等检查保证不会只动其一。
- 对现有检查无影响：`check-drift.sh` 的三种结论、`check-installed-drift` 的八安装面、
  `skills.manifest` 的技能集合与各处计数都不变。
- 无数据、schema 或迁移影响。无部署影响。

## 风险与回滚约束

- `installed_plugins.json` 是未公开承诺的内部文件；Claude Code 改格式后检查读出
  `PIN_UNREADABLE`，需要一次小变更跟进。宁可读不出，不可误判 `PIN_CLEAN`。
- `PIN_CLEAN` 只证明已装记录的来源与 commit，不证明技能在 fresh session 中被发现或按规则执行；
  后者属于 #354。
- 规则是文本约束，不是硬门；确定性的硬门仍是 broker、Controller 与 required CI。
- 回滚：本 Issue 的线性 commit 整体 revert 即可。marketplace 条目删除后，Claude 侧回到官方
  marketplace 来源；本票不产生任何 installed 状态，无须现场回滚。

## 非目标

- 不执行 Claude 或 Codex 的插件安装、升级、marketplace 注册；不做全局或 VM 安装。
- 不修改 `AGENTS.md`；其目录描述与本票新增入口的同步留给之后的独立治理步骤。
- 不修改 Codex adapter、vendor 快照、Codex 安装器、Controller、broker、main protection、required CI。
- 不为 superpowers 自建 pin；不裁剪或改写任一上游原文。
- 不迁移下游项目的 CONTEXT 文档；不触碰 Secret、账号或权限。
- 不把 pin 检查接入八安装面检查或任何自动修复。

## 未决问题

无。
