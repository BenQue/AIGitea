---
issue: 190
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/190
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 为 change 文档模板的 vendored 副本补上原先缺失的两条声明——gitea-governance.json 的 vendors_change_templates（谁持有副本）与 change-template-sync.json 的 template_digest（模板是哪一版），并新增 codex/tools/change-template-sync.sh 与平台自身 required CI 的 digest 闸门，使「改模板必须广播下游」成为可重复执行的机制；这是新增平台合同面与新增 CI 闸门，contract_effect 为 add，且同时命中 platform-governance 与 ci-change 两项强制 complex 规则
risk_flags:
  - platform-governance
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-template-sync-broadcast-260824.md
  spec: spec-template-sync-broadcast-260824.md
  plan: plan-template-sync-broadcast-260824.md
  verification: verification-template-sync-broadcast-260824.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/190-template-sync-broadcast
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/197
created: 2026-08-24
updated: 2026-08-24
---

## 问题/需求总结

`templates/docs/changes/_template/` 是合同源，但每个接入项目在 `docs/changes/_template/`
里持有一份**逐字节相同的副本**，`aisoft-project-check.sh` 的 `change-templates` 查的正是
这个相等关系。副本与合同源之间**没有任何版本号或依赖声明**，下游因此无从知道自己何时
过期：平台一改模板，所有持有副本的项目同时静默过期，直到某人恰好跑了一次检查器。

LocalWMS Issue #78 / PR #81（合并于 `f33c69d`）刚刚兑现了这个代价一次——平台 PR #168
改写了 `summary.md` 与 `verification.md`，LocalWMS 的 `change-templates` 随之从 `PASS`
退回 `GAP`，而该仓库当时没有任何提交。发现它靠的是运气。

在那八条对齐检查里，`change-templates` 是**唯一一条判据横跨两个仓库**的，因此也是唯一
一条会因上游前进而自发变红、并且会周期性复发的检查。

## 影响范围

只改平台仓库，**不改任何下游项目**：

| 文件 | 动作 |
|---|---|
| `codex/config/change-template-sync.json` | 新增：模板集合 + `template_digest` + `downstream_required_check: forbidden` |
| `codex/config/gitea-governance.json` | 新增 `vendors_change_templates: false`（仅平台仓库自身；它是合同源，不持有副本） |
| `codex/runtime/aisoft_gitea_governance/contract.py` | 读入并校验新键；未声明时缺省 `True` |
| `codex/tools/change-template-sync.sh` | 新增：广播工具（plan / `--verify-digest` / `--refresh-digest`） |
| `codex/tests/test-change-template-sync.sh` | 新增：17 个行为用例 |
| `codex/runtime/tests/test_vendored_change_templates.py` | 新增：5 个 schema 用例 |
| `codex/tests/smoke.sh` | 接入 `bash -n` / shellcheck / 行为测试 / **digest 闸门** |
| `03-Issue-Spec-Plan与单闸门开发流程.md` | §3 新增「模板是 vendored 副本：改动必须由上游广播」 |
| `skill-for-codex/references/project-align.md`、`onboarding-runbook.md` | 指向新机制 |

**没有**修改 `AGENTS.md`：本次运行正在遵循它，平台合同禁止在同一次 implementation run
里改写它。新增的工具与 manifest 不需要它授权即可被发现——smoke 闸门失败时的输出直接
给出补救命令。

## 初步方案与建议

Issue 正文给了三个方向，本次**裁决为方向 1（上游广播）**，并把它从「产出一份清单」
加强为「不广播就过不了平台自己的 CI」。理由与另外两个方向的取舍见下方「### 方向裁决」。

机制由三件东西构成：

1. **谁持有副本** → `gitea-governance.json` 每仓库的 `vendors_change_templates`。
   未声明取 `true`：读不到声明只会让广播多列一个仓库，而漏列一个持有过期副本的仓库
   正是本 Issue 要修的失败模式。目前只有平台仓库自身显式声明 `false`。
2. **模板是哪一版** → `change-template-sync.json` 的 `template_digest`（覆盖文件名与
   内容两者，改名或增删一份模板同样必须刷新）。
3. **谁负责广播** → 平台自己的 required CI。smoke 跑 `--verify-digest`；改了模板却不
   刷新 digest，平台这次 PR 就是红的，作者被迫在同一次变更里跑 `--refresh-digest`，
   而那条命令会打印按声明枚举的完整 holder 清单。

关键性质：**广播清单不依赖比对下游内容**。平台一改模板，所有声明持有副本的项目按定义
全部过期，本机有没有那个项目的 checkout 不影响这个结论——本机读不到的 4 个仓库同样
被完整列出。逐项 `current`/`stale`/`missing` 只是附加信息，用来区分「已经同步过」与
「还没同步」。

### 方向裁决

| 方向 | 裁决 | 理由 |
|---|---|---|
| 1 上游广播 | **采用** | 唯一在**产生过期的那一刻**动作的方向；代价只是平台侧一条 digest 闸门，且能覆盖本机没有 checkout 的项目 |
| 2 下游不再持有副本 | 不采用 | 要改 `change-templates` 这条检查本身的语义，并逐个迁移 6+ 个下游仓（每仓一条 Issue/PR）——正是本 Issue 想避免的分摊成本；副本还承担「起草起点在本仓库内可见」这个作用，去掉它等于用一个更大的迁移换一个更小的对齐面。Issue 正文点名的离线/无网行为也仍未决 |
| 3 非阻塞定期核对 | 暂不实现，但已铺好路 | 它只把「靠运气发现」换成「靠定时器发现」，不解决副本没有依赖声明这个根因，且必然滞后于漂移的产生。方向 1 落地后它退化为可选的补网：不带参数运行本工具即是只读现状核对，退出码 0/3 可直接被定时任务消费。要不要挂定时器、GAP 是否自动开 Issue，需要独立验收标准，属另一条 Issue |

### 明确不做的事

**不在任何下游项目引入阻塞式 required check。** 下游 CI 要跑这条比对，就得让每个 PR
去 clone 平台仓——等于把上游演进变成下游全部在途 PR 的阻塞，包括与模板毫不相干的那些；
而这条 GAP 的修复代价只是一次复制覆盖。这个约束不只写在文档里：
`change-template-sync.json` 的 `downstream_required_check` 必须是 `forbidden`，否则工具
直接停机（退出 1），smoke 另有一条 `jq -e` 断言与一条文档断言钉住它。

## 风险

1. **广播只在平台 PR 时触发，不覆盖历史欠账。** 本次首跑就暴露了 5 个既存缺口
   （见「### 首跑暴露的既存缺口」），它们早于本机制存在，本 Issue 不修——每个下游仓
   一条独立 Issue 是平台合同要求的路径。
2. **逐项状态取自本机 checkout 的工作树，不是该仓库 `main` 的状态。** checkout 落后或
   停在别的分支时，`stale`/`missing` 可能是 checkout 的状态而不是仓库的状态。工具因此
   对非 `main` 分支的 checkout 一律在行尾标注，`unverified` 也明确写着「不等于已同步」。
3. **回滚是纯删除**：撤掉本次变更即回到「只有一条 GAP 提示、无广播」的现状，不留残留
   状态——`vendors_change_templates` 未声明时的缺省与删除后的行为一致。

### 首跑暴露的既存缺口

机制第一次运行就给出了完整画像（真实输出见 verification 文档）：

| 项目 | 状态 | 说明 |
|---|---|---|
| LocalWMS | `current` | #78 刚同步过 |
| HSDB | `stale`（四份全部） | 仍持有 pre-#57 的 `00-summary.md` 一代命名，从未迁到语义四件套 |
| NewEMaint | `stale`（四份全部） | 上次回补停在 #67 |
| rsdesign-new | `missing` | checkout 停在 `codex-rsdesign-new-phase0` 分支，需在 `main` 上复核后再定性 |
| SFMDigitalBoard | `missing` | checkout 在 `main`，确实没有 `docs/changes/_template/` |
| myapp / SapTableMigrate / smoke-test / WMPDA | `unverified` | 本机 `mac_checkout` 为 `null` |

这些**不在本 Issue 范围内**，作为衍生 Issue 上报给人。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增平台合同面（vendors_change_templates 声明与 template_digest）与新增平台侧 required CI 闸门，把「改模板必须广播下游」落地为可重复机制
risk_flags:
  - platform-governance
  - ci-change
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- `change_type: platform` 属 `classification.py` 的 `FORCED_COMPLEX_TYPES`，单这一项即
  强制 complex。
- `risk_flags` 的 `platform-governance` 与 `ci-change` 都属 `FORCED_COMPLEX_RISKS`，各自
  独立地再次强制 complex：本次新增治理 manifest 键并改写 `codex/tests/smoke.sh`。
- `contract_effect: add`：新增了一条此前不存在的合同义务（改模板必须刷新 digest 并广播），
  不是恢复既有行为，因此不是 `restore`。
- `required_docs` 含 `verification`：aisoft-platform 未声明 `change_control`，取缺省
  `production`，complex 因此需要 `spec` 与 `plan`；`verification` 的取舍单独判定——本次
  验收标准四要求「用一次真实的模板改动验证机制生效」，其证据是**跨 6 个真实下游 checkout
  的扫描**与**改动前后对比**，required CI 两者都不跑（CI 里没有任何下游 checkout）。
  按 `03` §3 的表，这落在第二行。平台仓库 `deployment_lifecycle: none`，声明它不影响
  终态仍是 `completed`。

### 缺失的 acceptance criteria 或决策

- 无。Issue 正文的四条验收标准全部可测，方向裁决在本文档「### 方向裁决」给出。
