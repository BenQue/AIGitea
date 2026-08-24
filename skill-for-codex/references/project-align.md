# 项目对齐 · aisoft-project-align

> 初始化新项目与更新已接入项目是同一操作：**把项目对齐到平台当前合同**。本入口是
> 幂等的：已对齐仓库重跑为 no-op；未接入仓库首跑等价于 onboarding；漂移仓库首跑
> 产出精确缺口清单。事实源永远是 [onboarding-runbook.md](onboarding-runbook.md) 与平台
> `templates/`——本 checklist 只指向，不复制合同正文；两处表述冲突时以 runbook 为准。

## 操作循环

1. 运行确定性检查器盘点现状（只读，不改任何状态）：

   ```bash
   codex/tools/aisoft-project-check.sh --repo <目标仓checkout> [--kind software|docs] [--remote]
   ```

2. 逐条 `GAP:` 在**目标仓**建独立 Issue + 小 PR 修复（回补程序见 runbook §2；
   不批量脚本改写多仓）。
3. 修复合并后复检，直到无 `GAP:`。全 PASS 即对齐完成。

新仓库首次接入时，runbook §1/§1.1 的 governance manifest 与 project-agent gate 是
一切的前置，不能被本 checklist 替代或跳过；本入口从 §2 起接管逐项对齐。

## 对齐 checklist

| # | 查什么 | 事实源 | 机器检查 |
|---|---|---|---|
| 1 | AGENTS.md 常驻指针前两节 + CLAUDE.md 一行指针 | `templates/project/`；runbook §2 | `pointer-sections` |
| 2 | 语义 change 模板四件套在位 | `templates/docs/changes/_template/`；runbook §2 | `change-templates`（唯一会因上游前进而自发变红的一行，见下方「模板同步」） |
| 3 | Matt 编排三件套已初始化 | `templates/docs/agents/`；runbook §2 | 人工核对 |
| 4 | canonical 标签读回一致；受管命名空间无冲突取值、无仍在用的 retired 取值；其余标签须落在 manifest 声明的扩展前缀内 | `codex/config/gitea-labels.json`（`schema_version: 2`）；runbook §5 | `labels-readback`（`--remote`） |
| 5 | required CI context 与治理清单一致 | `codex/config/gitea-governance.json`；runbook §5/§8 | `ci-context`（`--remote`） |
| 6 | `.aisoft/architecture.json` 声明 + lock 有效 | runbook §9（Architecture declaration onboarding）；`architecture/bin/aisoft-architecture` | `architecture-lock` |
| 7 | 交付形态（delivery profile）已显式声明 | runbook §4；目标仓 AGENTS.md 项目事实 | `delivery-profile` |
| 8 | host access / onboarding 聚合核对 | runbook §1.1；broker `host.onboarding.check` | 既有工具，非本检查器 |

## 模板同步（第 2 行专属）

第 2 行的模板是 vendored 副本，平台一改模板它就在每个持有副本的项目里同时变红，
与目标仓是否有提交无关。触发同步的是**上游广播**，不是下游轮询：平台侧改模板的变更
必须在同一次变更里跑 `bash codex/tools/change-template-sync.sh --refresh-digest`，
否则平台自己的 required CI 变红；该命令打印按 `gitea-governance.json` 的
`vendors_change_templates` 枚举出的完整 holder 清单。

不带参数运行即只读现状核对，可随时重跑。**不在任何下游项目引入阻塞式 required check**
——那会把上游演进变成下游全部在途 PR 的阻塞。合同与理由见 `03` §3「模板是 vendored 副本」。

## 边界与工具分工

- 检查器只读、确定性；缺口修复始终走目标仓 Issue/小 PR，停在人工合并——本入口
  不授权合并、部署或批量改写。
- 例外只有标签一项：第 4 行的缺失/漂移由 broker `gitea.labels.provision` 幂等对齐
  （runbook §5），因为它是把仓库收敛到已合并 manifest，不产生新合同。**修改 manifest
  本身**——canonical 取值、`project_extensions.allowed_prefixes`、`retired`——仍须走
  平台 Issue/PR；受管命名空间冲突与退役取值在用同样不由本入口处置，provision 只报告，
  删除标签不在任何 typed 操作内。
- `aisoft-project-check` 查仓库内容对齐；`gitea-governance.sh check` 查权限/保护
  校准；broker `host.onboarding.check` 查 host 接入——三者各管一段，不互相替代。
- 纯文档/规范仓库用 `--kind docs`（architecture 与 delivery 两项按声明 SKIP），
  不虚构部署合同（runbook §1）。
