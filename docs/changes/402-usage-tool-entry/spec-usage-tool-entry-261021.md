---
issue: 402
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/402
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
  - artifact
depends_on:
  - 391
  - 392
  - 395
status: approved
branch: change/402-usage-tool-entry
created: 2026-10-21
updated: 2026-10-21
git_scope:
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 06-运维手册与踩坑集.md
  - codex/runtime/tests/test_session_contract.py
  - codex/tests/smoke.sh
  - codex/tests/test-aisoft-entry.sh
  - codex/tests/test-project-check.sh
  - codex/tests/test-usage-bundle.sh
  - codex/tools/aisoft
  - codex/tools/aisoft-project-check.sh
  - codex/tools/usage-bundle.py
  - docs/changes/402-usage-tool-entry/plan-usage-tool-entry-261021.md
  - docs/changes/402-usage-tool-entry/spec-usage-tool-entry-261021.md
  - docs/changes/402-usage-tool-entry/summary-usage-tool-entry-261021.md
  - docs/changes/402-usage-tool-entry/verification-usage-tool-entry-261021.md
  - docs/governance/platform-e2e-acceptance.md
  - docs/governance/remediation-roadmap.md
  - skills/aisoft-matt-workflow/SKILL.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/onboarding-runbook.md
  - skills/aisoft-platform/references/private-gitea-access.md
  - skills/aisoft-platform/references/project-align.md
  - skills/issue-session-flow/SKILL.md
  - templates/project/AGENTS.md
  - usage/CONTRACT.md
  - usage/bundle.json
---

# R11 使用层可独立消费：aisoft 工具入口、技能去平台检出依赖、采用批处理与发布说明

## 目标与原因

ADR 0001 D7 让项目按版本 pin 发布包，但发布包今天只锁文本：技能正文 26 行仍要求会话跑
`PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli …` 与 `codex/tools/*.sh`，项目会话离开平台检出就做不了
判级投影、文档检查与收尾。HSDB、LocalWMS、SFM 三个项目还没有 pin（NewEMaint 已 pin 1.2.0）。本票让项目会话
只用项目内随发布包分发的 `aisoft` 完成全部会话动作，并用脚本批量生成三个项目的采用改动（裁决 D4 a）。

## 设计

### 1. aisoft 工具包与落点

- 唯一源文件 `codex/tools/aisoft`（bash）。平台仓内直接运行；项目内落在 `.aisoft/bin/aisoft`。它按自身位置找根：
  `../lib` 下有 `codex/` 时以 `.aisoft/lib` 为根，否则以平台仓根为根。
- 工具包是被包装工具的**闭包子集**，在项目内落在 `.aisoft/lib/<平台相对路径>`，保持平台目录结构，所以被包装的
  脚本按原有相对路径找依赖，不改它们的查找逻辑：`codex/tools/` 的三个脚本与 `usage-bundle.{sh,py}`、
  `codex/agent/` 的四个 shell 库、`codex/runtime/` 中 `aisoft_loop`、`aisoft_change_name`、
  `aisoft_worktree_owner`、`aisoft_host_access` 的 `__init__`/`contract`/`dependencies`、`aisoft_gitea_governance`
  的 `__init__`/`contract`、`aisoft_architecture`，以及 `architecture/` 的 `bin`、`catalog.json`、`profiles/`、
  `schemas/`。清单在 `usage/bundle.json` 逐文件声明为 `exact` 成员，归入新核对项 `tool-provenance`。
- **manifest 不进项目仓**：governance、labels 与 broker manifest 读本机 broker 安装副本
  `/usr/local/share/aisoft/`（`aisoft-project-target.sh` 与 `mark-completed-issues.sh` 已有这条回退；
  `aisoft-project-check.sh` 补同样的回退）。governance manifest 列着全部项目仓，进项目仓会违反 ADR 0001 D3。
  broker 本身仍是本机安装的 `/usr/local/libexec/aisoft/host-access-broker`，与平台检出无关。
- `--build` 与 `--adopt` 另写两份生成文件（不是成员）：`.aisoft/lib/usage/bundle.json`（截至该版本的发布历史，
  供离线 `bundle status`）与 `.aisoft/lib/provenance.json`（`bundle_version`、`bundle_digest`、`source_sha`）。
- 运行时设 `PYTHONDONTWRITEBYTECODE=1`，不在项目仓留下 `__pycache__`。

### 2. 子命令

| 子命令 | 实现 |
|---|---|
| `change-name N slug`、`resolve-documents N`、`check-change-documents`、`backfill-pr-url N --pr-url U`、`claim-worktree`、`scan-worktrees` | 转给 `aisoft_loop.cli`，`--repo` 缺省为当前 git 顶层 |
| `classify N`、`classify --apply N`、`classify --verify N` | 包装 `apply-classification-labels.sh`；计划模式先打印 summary `route:` 的「路由」行（R10b 的确认点 1 格式），缺 `route:` 时提示按 `route-policy.md` 补写 |
| `complete --project ID --range R`、`complete --project ID --apply N…` | 包装 `mark-completed-issues.sh`，参数原样传递 |
| `project-check [--kind …] [--remote]` | 包装 `aisoft-project-check.sh` |
| `bundle status` | 包装 `usage-bundle.sh --project-status`（项目内用自带发布历史） |
| `version` | 打印 `bundle_version`、`bundle_digest`、`source_sha`；平台仓内打印 `source-tree` 与当前 HEAD |

`get-issue`、`list-issues`、`apply-analysis` 不进 `aisoft`：三者要 raw `GITEA_TOKEN`，与「Gitea 访问一律走 broker」
冲突，且当前无调用方。`aisoft_loop.cli` 本票不删它们；删除连同 `gitea-analyze-change` 技能与 `03` 的引用一起，作为后续遗留项写进本票交接，由负责人另行排期。

### 3. 发布包合同

- `usage-bundle.py` 新增核对项 `tool-provenance`：项目内工具包的每个文件与所 pin 版本记录的 sha256 一致，
  且 `.aisoft/lib/usage/bundle.json` 的历史是平台历史的前缀。pin 的版本早于工具包（≤ 1.6.0）时报 NOTE。
  核对项覆盖要求只对 `members` 与引入工具包之后的版本生效，已发布版本不变。
- `releases[]` 新增可选键 `notes`（一句话）与 `compatibility`（`patch|minor|major`）；从本票的版本起
  `--release` 必须给出 `--compatibility` 与 `--notes`，已发布版本不补写（历史只追加）。
- `--project-status`：pin 落后最新版本时，落后区间内有 `major` 记 GAP，否则 NOTE（写明区间内最高的
  `compatibility`，旧版本无此键记 unknown）。
- 新增 `--adopt <项目检出>`：要求目标是干净的 git 工作树；写入 lock、`.aisoft/platform-usage.md`、`CLAUDE.md`、
  change 模板四件套、`AGENTS.md` 常驻指针两节（就地替换或插入，项目事实不动）、`--tools` 所列工具（缺省
  `claude,codex`，用 Cursor 的项目加 `cursor`）的平台技能与 Matt/superpowers 项目级落点、`docs/agents/` 三份（仅缺失时）、`.cursor/rules/aisoft-platform.mdc`（仅缺失时）与 `.aisoft/` 工具包；
  legacy 模板（`00-summary.md` 等四件套）不删，只打印 NOTE（见下「实现中的合同更正」）。CI 种子
  （`ci.yml`、`merge-preview.sh`、`registry-preflight.sh`）不写，改为 NOTE：改 CI 不是 small。
  结束时打印写入清单，并对结果跑一次 `--project-status`。

### 4. 技能与文档

- 技能正文（`aisoft-platform/SKILL.md`、`issue-session-flow/SKILL.md`、`references/onboarding-runbook.md`、
  `project-align.md`、`private-gitea-access.md`）把会话动作改写为 `aisoft <子命令>`，并在 `aisoft-platform` 开头说明
  `aisoft` 是项目内 `.aisoft/bin/aisoft`（平台仓内为 `codex/tools/aisoft`）。只有平台维护者在平台检出里做的步骤
  （governance apply、仓库设置同步、模板 digest 刷新、只读 helper、外部技能版本核对）保留原命令，放进标题含
  「维护层」的小节；守卫按小节豁免。
- `usage/CONTRACT.md` 加一节「会话工具」：入口、子命令与 `tool-provenance`。
- `templates/project/AGENTS.md`「项目事实」改为固定条目（原八项加「选用工具与 required CI」「项目规则」两项）、≤ 2 KB，其余项目规则链接到项目文档；
  `aisoft-project-check.sh` 新增 `agents-budget`：项目 `AGENTS.md` 的「项目事实」节超过 2 KB 时 NOTE（不计 GAP）。
- `03` 与 `06` 只补一句指向 `aisoft` 的说明，维护层命令原样保留。
- `docs/governance/platform-e2e-acceptance.md` 新增「采用记录」表（项目、版本、Issue、PR、`--project-status`），
  不改写已有行；路线图 R11 行更新状态。

### 5. 三个项目的采用

HSDB、LocalWMS、SFM 各在自己的仓库开一个 Issue（`needs-analysis`，正文写 `--adopt` 的来源版本与验收标准）、
一个 change worktree 与唯一 PR，判 small（`contract_effect: restore`，路由 R5 `small-direct`），change 目录只有
summary。每个 PR 推送前单独请负责人确认。采用会话本身就是验收 1 的那次 small Issue：在临时 HOME、
`PATH` 不含平台检出的环境里只用 `.aisoft/bin/aisoft` 完成 change-name → 文档检查 → `classify --verify` →
`complete` dry-run。

**合并顺序**：平台 PR 先合并（项目的 `--project-status` 要在平台 main 上找到所 pin 的版本），三个项目 PR 后合并。
平台 PR 合并前若版本号被别的批次占用，按协调约定以 merge commit 集成 main、改发下一版本，并对三个项目重跑
`--adopt` 更新它们的 PR。

### 6. 实现中的合同更正（2026-10-21，试采用发现）

对三个项目的 `origin/main` 试跑 `--adopt` 后，已安装 broker 的 `git.push.change` 范围闸门（#327）有三条约束与
原设计冲突，本票在不改 broker 的前提下这样处理：
- 闸门要求映射 spec 的 `git_scope` 逐项列出改动路径，small 也一样。采用 Issue 仍判 small，change 目录另带一份
  只写 front matter 与 `git_scope` 的 spec；「small 只有 summary」与闸门的冲突作为后续遗留项记进交接。
- `git_scope` 最多 256 项。三种落点全写约 355 个文件，所以 `--adopt` 增加 `--tools`，缺省 `claude,codex`
  （约 180 个文件），Cursor 落点按需加；三个项目目前都不用 Cursor。
- 闸门不允许在本 Issue 目录之外删除 `docs/changes/` 下的非 canonical 文件，所以 legacy 模板不删，只打印 NOTE。

## 验收标准

1. AC-1：临时 HOME 且 `PATH` 不含平台检出时，一个采用项目的 small Issue 用 `.aisoft/bin/aisoft` 完成
   change-name → `check-change-documents` → `classify --verify N`（读回 `projected`）→ `complete --range` dry-run，
   全程不读平台检出（`sandbox-exec` 配置拒绝读取平台检出目录，记录命令、退出码与 `PATH`/`HOME` 读回）。
2. AC-2：`rg 'PYTHONPATH=codex/runtime|codex/tools/' <导出目录>/project/.claude/skills` 在「维护层」小节之外零命中；
   smoke 守卫钉住，反向证明（在非维护层小节加一行）变红。
3. AC-3：`--adopt` 对 HSDB、LocalWMS、SFM 各运行一次，`--project-status` 全部 PASS（含 `tool-provenance`）；三个
   采用 Issue 与 PR 链接写进 E2E 表「采用记录」。
4. AC-4：工具包闭包测试：导出到空目录后，在只含导出物的环境里逐个运行子命令的帮助与一条真实调用，无缺文件；
   删掉清单中的任一 Python 模块反向证明变红。
5. AC-5：`tool-provenance` 改一个字节变 GAP；pin 1.2.0 的项目报 NOTE 不报 GAP。
6. AC-6：`--release` 缺 `--compatibility` 或 `--notes` 拒绝；落后区间含 `major` 时 `--project-status` 记 GAP，
   patch/minor 记 NOTE；`--verify --baseline-ref origin/main` 证明已发布版本未改。
7. AC-7：`agents-budget` 对超 2 KB 的「项目事实」报 NOTE；模板自身 ≤ 2 KB。
8. AC-8：`bash codex/tests/smoke.sh` 全绿，`usage-bundle.sh --verify` 通过，发布下一空闲版本（当前候选 1.8.0），
   `check-change-documents` gap=0，Codex 只读交叉审查 PASS。

## 风险与回滚约束

- 工具包把约 40 个平台文件复制进每个项目仓。它们由 `tool-provenance` 锁定为某个发布版本的字节，项目不得手改；
  升级只经 `--adopt`。
- 被工具包收录的平台文件（`aisoft_loop`、`aisoft_host_access` 的 contract 与 dependencies、governance contract、architecture 校验器与三个被包装工具）从此也是发布包成员：以后改它们的平台变更都要同 PR 发新版本。
- 被包装脚本改为在 `.aisoft/lib` 下运行，相对路径假设由闭包测试覆盖；平台仓内行为不变。
- `aisoft-project-check.sh` 的结果计数被测试逐字钉死（新增 `tool-provenance` 与 `agents-budget` 两行要同步改测试）。
- 不改 broker、installer 与 manifest，合并后不需要两台重装；技能需重装。
- 整 PR revert 即回滚平台侧；三个项目的采用 PR 各自独立 revert。治理文件（技能、模板、使用合同）先单独 commit
  并停止，fresh 重读后再改 runtime。

## 非目标

不改 broker 操作；不改 legacy change 文档判定（R12）；不把 `route:` 改为必填；不从 `route-policy.md` 生成机器读
JSON（`classify` 只显示 summary 已写的路由卡）；不删 `aisoft_loop.cli` 的三个旧子命令（后续遗留项）；不推 GitHub 镜像。

## 未决问题

以下实现选择在确认点 1 一并确认：工具包提交进项目仓而 manifest 读本机安装副本（设计 §1）；`compatibility`
落后含 `major` 记 GAP、其余 NOTE（§3）；`--adopt` 不写 CI 种子（§3）；平台 PR 先合并、项目 PR 后合并（§5）。
本票的 G1 `grill-me` 已在最终计划阶段由 D4 裁决完成，不另开一轮。
