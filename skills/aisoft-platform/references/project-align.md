# 项目对齐 · aisoft-project-align

> 初始化新项目与更新已接入项目是同一操作：**把项目对齐到平台当前合同**。本入口是
> 幂等的：已对齐仓库重跑为 no-op；未接入仓库首跑等价于 onboarding；漂移仓库首跑
> 产出精确缺口清单。事实源永远是 [onboarding-runbook.md](onboarding-runbook.md) 与平台
> `templates/`——本 checklist 只指向，不复制合同正文；两处表述冲突时以 runbook 为准。
>
> 对齐的对象是**一个版本的平台使用发布包**（#377）：平台 `usage/bundle.json` 声明成员与只追加的
> 版本历史，项目复制 `usage/CONTRACT.md` 为 `.aisoft/platform-usage.md`，并在
> `.aisoft/platform-usage.lock.json` pin `bundle_version` 与 `bundle_digest`。项目一旦 pin，
> 平台前进不再改变它的对齐结论；升级版本是项目自己的 Issue。

## 操作循环

1. 在目标仓 checkout 里运行确定性检查器盘点现状（只读，不改任何状态）：

   ```bash
   aisoft project-check [--kind software|docs] [--remote]
   ```

   尚未采用发布包的仓库还没有 `aisoft`，由平台维护者在平台检出里对它运行同一检查器（见下文「维护层」节）。

2. 需要复制平台文件时（首次接入、升级版本或补齐缺失副本），由平台维护者在平台检出里生成采用改动
   （下文「维护层：导出与采用」），在目标仓的 change worktree 里提交。

3. 逐条 `GAP:` 在**目标仓**建独立 Issue，由 AI 按合同影响和强制风险判级后用单一 PR
   修复（回补程序见 runbook §2；不批量脚本改写多仓）。纯合同保持型局部回补可为 small，
   CI、部署、权限、Agent/治理或共享核心变化仍强制 complex。
4. 修复合并后复检，直到无 `GAP:`。全 PASS 即对齐完成。

新仓库首次接入时，先完成 runbook §0.1「接入既有项目」的采用步骤（项目自主，不需要平台登记）。选用站点加固访问的项目，还要先通过 §1.1 的 governance manifest 与 project-agent gate。两者都不能被本 checklist 替代或跳过，本入口从 §2 起接管逐项对齐。

## 维护层：导出与采用

首次采用时，项目里还没有 `.aisoft/bin/aisoft-access`。这时在项目 change worktree 内运行平台检出里同一份 `codex/tools/aisoft-access`，它按该 worktree 的 `.aisoft/project.json` 走项目自声明来源，完成首推与建 PR（ADR 0003）。

以下命令只在平台检出里运行，由平台维护者执行：

```bash
codex/tools/aisoft-project-check.sh --repo <目标仓checkout> [--kind software|docs] [--remote]
codex/tools/usage-bundle.sh --adopt <目标仓 change worktree> [--tools claude,codex,cursor]
codex/tools/usage-bundle.sh --build <空目录>
```

`--adopt` 要求目标是干净的 git 工作树，把最新版本的采用改动直接写进去：lock、使用合同副本、`CLAUDE.md`、
change 模板四件套、`AGENTS.md` 常驻指针两节（就地替换，「项目事实」不动）、`--tools` 所列工具的技能与
Matt/superpowers 项目级落点（缺省 `claude,codex`；用 Cursor 的项目加 `cursor`）、会话工具 `.aisoft/bin/aisoft` 与 `.aisoft/lib/`；`docs/agents/` 三件套与
`.cursor/rules/aisoft-platform.mdc` 只在缺失时写；CI 种子不写，只打印 NOTE（改 CI 不是 small）。结束时
打印写入清单与改动路径数，并跑一次 `--project-status`。legacy 模板（`00-summary.md` 等）不删、只打印 NOTE：
broker 的范围闸门不允许在别的 Issue 名下删除 `docs/changes/` 里的非 canonical 文件。broker 推送要求映射 spec 的
`git_scope` 逐项列出改动路径（small 也一样，最多 256 项），采用 Issue 因此带一份只写 `git_scope` 的 spec。`--build` 只导出不写目标仓：
`<空目录>/project/` 下的文件按项目落点排好，含生成的 `.aisoft/platform-usage.lock.json`；
`AGENTS.md` 是完整模板，存量仓库只同步其常驻指针两节，「项目事实」保持项目自己的内容；
`docs/agents/` 与 CI 示例是种子，已有的项目版本不覆盖。技能从同一份源导出到三种项目级落点：
`.claude/skills/`、`.agents/skills/`（Codex）与 `.cursor/skills/`，`--adopt` 按 `--tools` 写落点；
Cursor 另有种子 `.cursor/rules/aisoft-platform.mdc`，它只指向使用合同、lock 与 `AGENTS.md`，不复述规则。

## 对齐 checklist

| # | 查什么 | 事实源 | 机器检查 |
|---|---|---|---|
| 0 | 平台使用发布包已 pin：`.aisoft/platform-usage.lock.json` 的版本在平台历史中、摘要一致 | `usage/bundle.json`；`usage-bundle.sh --adopt` | `platform-pin`（落后最新版本时仍 PASS，另打印 `NOTE:`；落后区间含 `major` 时 GAP） |
| 0a | 会话工具 `.aisoft/bin/aisoft` 与 `.aisoft/lib/` 的字节等于所 pin 版本的发布记录 | `usage/bundle.json` 的 `tool-provenance` 成员；`aisoft version` | `tool-provenance`（pin 早于工具包的版本记 NOTE） |
| 1 | AGENTS.md 常驻指针前两节 + CLAUDE.md 一行指针 | `templates/project/`；runbook §2 | `pointer-sections`（按 pin 版本的摘要核对；无 lock 时对照最新版本） |
| 2 | 语义 change 模板四件套在位 | `templates/docs/changes/_template/`；runbook §2 | `change-templates`（同上；未 pin 的项目仍会因上游前进而自发变红，见下方「模板同步」） |
| 3 | Matt 编排三件套已初始化 | `templates/docs/agents/`；runbook §2 | 人工核对 |
| 4 | canonical 标签读回一致；受管命名空间无冲突取值、无仍在用的 retired 取值；其余标签须落在 manifest 声明的扩展前缀内 | `codex/config/gitea-labels.json`（`schema_version: 2`）；runbook §5 | `labels-readback`（`--remote`） |
| 5 | required CI context 与治理清单一致 | `codex/config/gitea-governance.json`；runbook §5/§8 | `ci-context`（`--remote`） |
| 6 | `.aisoft/architecture.json` 声明 + lock 有效 | runbook §9（Architecture declaration onboarding，含 `delivery_contract` 如实选取）；`architecture/bin/aisoft-architecture` | `architecture-lock` |
| 7 | 交付形态（delivery profile）已显式声明，部署方案位置指向项目自己的 docs/脚本目录 | runbook §4（环境级原则，非部署步骤）；目标仓 AGENTS.md 项目事实与项目自己的部署文档 | `delivery-profile` |
| 8 | host access / onboarding 聚合核对 | runbook §1.1；broker `host.onboarding.check` | 既有工具，非本检查器 |
| 9 | merge allowlist 只有人、无 routine merger 声明（#391）与 protection read-back | governance manifest；runbook §1.1/§5；项目来源为采用 Issue 中的人工保护证据（ADR 0003） | runtime checker/read-back；项目来源下 `project-check` 记 `MANUAL`；source contract 只人工核对 |

## 模板同步（第 2 行专属，维护层）

第 2 行的模板是 vendored 副本。项目 pin 了发布包版本后按该版本核对，不再因平台前进变红；
未 pin 的项目对照最新版本，平台一改模板它就在每个持有副本的项目里同时变红，
与目标仓是否有提交无关。改模板的平台变更还必须发布新的发布包版本（`usage-bundle.sh --release`）。触发同步的是**上游广播**，不是下游轮询：平台侧改模板的变更
必须在同一次变更里跑 `bash codex/tools/change-template-sync.sh --refresh-digest`，
否则平台自己的 required CI 变红；该命令打印按 `gitea-governance.json` 的
`vendors_change_templates` 枚举出的完整 holder 清单。

不带参数运行即只读现状核对，可随时重跑。**不在任何下游项目引入阻塞式 required check**
——那会把上游演进变成下游全部在途 PR 的阻塞。合同与理由见 `03` §3「模板是 vendored 副本」。

### 模板更新的 Git scope 边界（#360）

第 2 行的四份 `docs/changes/_template/{summary,spec,plan,verification}.md` 是 canonical
共享资源，不是另一 Issue 的合同目录。其范围授权仍须复用现有 holder 与 exact committed
approved scope，逐项授权、完整历史检查；不允许放开整个 `docs/changes/`、省略真实 delta
或伪造 Issue 路径。唯一规则见 [03 §3「Canonical 模板的精确 Git scope 合同」](../../../03-Issue-Spec-Plan与单闸门开发流程.md#canonical-模板的精确-git-scope-合同360)，
实现和验收范围见 [#360 spec](../../../docs/changes/360-canonical-template-scope/spec-canonical-template-scope-261015.md)。

模板例外由 broker 推送闸门的 canonical 模板上下文实现：scope 列出四份模板时，闸门核对目标仓是
holder、summary 的 Issue URL 属于该仓，再逐份核对模板路径是普通文件（不是链接、目录或可执行文件）；
模板内容是否等于所 pin 版本由 `aisoft project-check` 的 `change-templates` 核对。遇 `SCOPE_DENIED` 保留具体失败与批准 scope，
不关闭 guard；本入口不增加 installer/policy 框架，也不接管项目部署。

## 边界与工具分工

- 检查器只读、确定性；缺口修复始终走目标仓 Issue/单一判级 PR。发现 credential 或 protection GAP 必须走目标仓或平台治理 Issue。source
  candidate、installed bytes 与 live protection 分开记录。本入口不授权合并、部署或批量改写。
- 例外只有标签一项：第 4 行的缺失/漂移由 broker `gitea.labels.provision` 幂等对齐
  （runbook §5），因为它是把仓库收敛到已合并 manifest，不产生新合同。**修改 manifest
  本身**——canonical 取值、`project_extensions.allowed_prefixes`、`retired`——仍须走
  平台 Issue/PR；受管命名空间冲突与退役取值在用同样不由本入口处置，provision 只报告，
  删除标签不在任何 typed 操作内。
- `aisoft-project-check` 查仓库内容对齐；`gitea-governance.sh check` 查权限/保护
  校准；broker `host.onboarding.check` 查 host 接入——三者各管一段，不互相替代。
- 纯文档/规范仓库用 `--kind docs`（architecture 与 delivery 两项按声明 SKIP），
  不虚构部署合同（runbook §1）。
