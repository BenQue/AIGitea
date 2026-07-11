# Spec 驱动工作流 + Spec/Plan ↔ Issue 绑定方案

> 试点项目：**rsdesign-new**（机器人线束设计工具重构，企业级 B2B：项目/图号/装配组件明细 + SAP BOM(RFC) + PDF 图纸）。
>
> 本文回答你的三层问题，重点解决核心问题：**spec/plan 文档如何与 issue / change request 绑定**。方案与具体代码结构无关，可直接套用；若要针对 rsdesign-new 实际目录细化，把仓库放到可访问位置或在 VM 内让 Claude Code 分析后再补。
>
> **📌 可执行口径以《阶段 2.6》为准**：本文为概念设计，正文中的文件夹/分支/标签命名为示意。最终落地约定——文件夹 `docs/changes/<N>`（纯数字，脚本用）；分支 `spec/N`（独立 spec PR）+ `change/N`（代码 PR）；状态/标签用 2.6 的七个（`needs-analysis / awaiting-triage / spec-drafting / spec-review / approved / pr-open / deployed`，用 `approved`，无 `spec-approved` / `merged`）。

---

## 0. 你的三个问题，先各一句话

1. **用真实项目 rsdesign-new 试** —— ✅ 合适。下面的绑定方案不依赖项目内部结构，接入即用。
2. **用 Codex 还是 Claude Code？怎么在 Codex 里描述想法？** —— 关键洞见：**你不该在 Codex 的对话框里临时描述意图，而是把意图写成 spec.md / plan.md，再指给 agent 执行。** spec/plan 就是"意图接口"，agent 可插拔（Codex / Claude Code 都行）。因本地 Gitea 是 `.orb.local`，只能用**本地 CLI** 版（云端够不到）。详见 [第 4 节](#4-codex-vs-claude-codespecplan-就是意图接口)。
3. **spec/plan 怎么绑定 issue/CR？** —— 核心答案：**同一个 ID 贯穿 + 文档进仓库 + 双向链接 + 标签状态机**。详见 [第 2 节](#2-绑定方案核心答案)。

---

## 1. 核心思想：让一切挂在同一根线上

绑定的本质是**可追溯性（traceability）**：从任何一个产物都能跳到其它产物。三条主线撑起整个方案：

- **唯一 ID = Gitea issue 号 `N`**。一个 CR/bug = 一个 issue = 一个号 N。N 贯穿 branch、commit、PR、spec、plan、部署记录。
- **文档进仓库**（不进 wiki / 网盘 / 聊天记录）。spec/plan 和代码放在同一个 repo、同一次 PR 里，一起版本化、一起 review。这是**最强的绑定**——意图和实现在同一处、同一时刻被审查，且永久留在 git 历史里。
- **双向链接**。issue↔doc↔branch↔commit↔PR↔deploy 每个方向都要能跳过去，不能只有单向。

---

## 2. 绑定方案（核心答案）

### 2.1 唯一 ID = Gitea issue 号

任何需求/问题先落成一个 Gitea issue，拿到号 `N`。之后所有产物都带上 `N`。不要用外部编号或文档标题当主键——issue 号是天然唯一、天然可点击的。

### 2.2 文档在仓库里的位置与命名

每个 issue 一个文件夹，放在仓库的 `docs/changes/` 下：

```
docs/changes/
  └─ 42-drawing-number-multiseg/        # <N>-<slug>
       ├─ 00-summary.md    # 问题/需求总结 + 初步评估与建议（分析阶段产出）
       ├─ 01-spec.md       # 规格：做什么、为什么、验收标准、接口/数据模型影响
       ├─ 02-plan.md       # 实施计划：任务分解、涉及文件、迁移、测试计划
       └─ notes.md         # 可选：brainstorm 记录 / 决策留痕
```

命名规则：`<issue号>-<短横线小写 slug>`。文件用 `00/01/02` 前缀固定阅读顺序。**文件夹名里带 N**，这样在文件树里就能一眼对应到 issue。

### 2.3 结构化 front-matter（让绑定可机读）

每个文档顶部放 YAML front-matter，既是给人看的元数据，也让索引/校验脚本能自动解析：

```yaml
---
issue: 42
gitea_url: http://gitea-ci.orb.local:3000/<owner>/rsdesign-new/issues/42
type: change-request          # bug | feature | change-request
title: 图号生成规则支持多段式编码
status: approved              # analyzed | awaiting-triage | spec-review | approved | in-progress | pr-open | deployed
branch: spec/42               # spec 阶段在 spec/42；进入执行后代码在 change/42
pr: null                      # 合并后填 PR URL
owner: ci-bot
created: 2026-07-09
updated: 2026-07-10
---
```

`status` 字段与下面的标签状态机保持一致——文档里的 status 是"事实记录"，Gitea 标签是"驱动流程的开关"，两者由脚本同步。

### 2.4 双向链接矩阵（每个方向都要通）

| 从 → 到 | 绑定方式 |
|---------|----------|
| **issue → docs** | agent 在 issue 里贴一条"控制台"评论，链接 spec/plan 文件的 Gitea Raw URL，并随状态更新 |
| **docs → issue** | front-matter 的 `issue:` + `gitea_url:` |
| **branch → issue** | 分支名 `change/<N>-<slug>` 带 N |
| **commit → issue** | 提交信息含 `(#N)`，正文可引用 `docs/changes/<N>/…` |
| **PR → issue** | PR 正文写 `Closes #N`（Gitea 合并时自动关闭并双向关联），且 PR 里**包含** `docs/changes/<N>/` 全部文件 |
| **deploy → issue** | 部署流水线成功后回帖到 issue：「已部署到 test/prod @ <sha>」，并把 status 改 `deployed` |

关键在 **PR 同时包含 spec + plan + 代码**：审查者一眼能看到"要做什么（spec）→ 怎么做（plan）→ 实际改了什么（diff）"，三者对齐才合并。

### 2.5 标签状态机（生命周期开关）

Gitea 标签驱动 agent 与人工闸门，状态单向推进：

```
needs-analysis
   └─(agent 出总结)→ awaiting-triage
        └─(人批准方向/闸门A)→ spec-drafting
             └─(agent/你出 spec+plan)→ spec-review
                  └─(人批准 spec/plan/闸门B)→ approved
                       └─(agent 执行开 PR)→ pr-open
                            └─(人 review+合并/闸门C)→ merged
                                 └─(部署回帖)→ deployed
```

每次 agent 动作结束都换标签，避免被下一轮重复处理（沿用[阶段 2.5](#) 的 `poll.sh` 机制）。

---

## 3. Spec 驱动生命周期（含三道人工闸门）

把你描述的"审核 issue → 写总结/初步方案 → 本地 brainstorm→spec→plan→执行 → PR → 合并部署"落成四个阶段：

**阶段 1 · 分析与总结（agent 只读）**
- 触发：issue 打 `needs-analysis`。
- agent 读 issue + 仓库相关文档 + 领域上下文 → 产出 `00-summary.md`：问题/需求总结、影响范围、初步方案与建议、风险、是否需要完整 spec。
- 贴到 issue 评论 + 提交到 `change/<N>` 分支。标签 → `awaiting-triage`。
- **【闸门 A】** 你判断 go / no-go / 调整方向。go → 打 `spec-drafting`。

**阶段 2 · Brainstorm → Spec → Plan（在本地克隆，用 superpowers）**
- 在本地克隆的仓库里，用 superpowers 做 brainstorm → 写 `01-spec.md`（做什么、为什么、验收标准、接口/数据模型/ SAP RFC / PDF 影响）→ 写 `02-plan.md`（任务分解、涉及文件、Prisma 迁移、测试计划）。
- 提交到 `change/<N>` 分支并推送；可开一个 **docs-only 的"spec 草案 PR"** 让 spec/plan 先在 Gitea 里被 review。标签 → `spec-review`。
- **【闸门 B】** 你审 spec/plan——**这是最关键的一道**，改意图比改代码便宜得多。批准 → 打 `approved`。

**阶段 3 · 执行 → PR（Codex 或 Claude Code）**
- agent 读 `01-spec.md` + `02-plan.md`（它们**就是**详细意图）→ 在同一 `change/<N>` 分支实现 → 跑测试 → 推送 → 开 PR（正文 `Closes #N`，包含 docs + 代码）。标签 → `pr-open`。
- CI 自动跑。
- **【闸门 C】** 你 review PR（spec+plan+代码一起看）→ 合并。

**阶段 4 · 合并 → 部署 → 回写**
- 合并触发部署流水线 → 部署成功回帖 issue → status/标签 → `deployed`；`Closes #N` 自动关闭 issue。

---

## 4. Codex vs Claude Code：spec/plan 就是"意图接口"

### 核心洞见

你问"如何在 Codex 里详细描述我的想法"——**答案是：不要在 Codex 的对话框里临时口述。** 临时口述的意图不可追溯、不可复用、每次都不一样。正确做法是把想法沉淀成 `01-spec.md` / `02-plan.md`，然后让 agent 读这两个文件去执行。这样：

- 意图被**版本化**、绑定到 issue、可被 review；
- 换 agent（Codex ↔ Claude Code）不影响，因为它们读的是同一份 spec/plan；
- 执行阶段的 prompt 极简，就一句"按 docs/changes/<N>/ 的 spec 和 plan 实现，遵循仓库规范"。

### 两个 agent 的"规范文件"

| | Claude Code | Codex |
|---|---|---|
| 自动读取的规范文件 | `CLAUDE.md`（仓库根，自动加载）| `AGENTS.md`（仓库根，会话首轮自动注入；从 git root 向下查找）|
| 任务输入 | `claude -p "按 docs/changes/42 的 spec/plan 实现…"` | `codex "按 docs/changes/42 的 spec/plan 实现…"`（或 TUI / stdin）|
| brainstorm→spec 工作流 | superpowers 等技能原生适配 | 用自身能力，无 superpowers |

**单一来源做法**（避免两份规范打架）：以 `AGENTS.md` 为准（它是被 Codex、以及越来越多工具采用的开放约定），让 `CLAUDE.md` 只写一行导入 `@AGENTS.md`。这样规范只维护一处，两个 agent 都读得到。

`AGENTS.md` 该写什么（新人第一天需要知道的）：

```markdown
# AGENTS.md · rsdesign-new

## 命令
- 安装: npm ci（前后端各自目录）
- 后端测试: cd backend && npm test
- 前端构建: cd frontend && npm run build
- 生成迁移: cd backend && npx prisma migrate dev --name <名>

## 硬性规范
- 改动必须带/更新测试；提交前测试必须通过
- schema 变更必须走 Prisma 迁移，向后兼容
- 每个改动对应一个 issue：在 docs/changes/<N>/ 下有 spec+plan
- 只做与当前 issue 相关的最小改动；不碰 .gitea/workflows、scripts、部署文件
- 前端遵循企业级 B2B 风格（表格可读性优先、信息密度适中、少动画）
- SAP BOM 走 RFC 接口；PDF 图纸按 SAP 号规则从文件服务器取

## 分支/提交
- 分支: change/<N>-<slug>；提交: feat: <简述> (#N)
```

### 连通性约束（和之前一样的坑）

Codex 云端、以及任何 SaaS 版 agent，**够不到你 `.orb.local` 的自托管 Gitea**（将来放内网也一样，外部服务进不了内网）。所以无论选谁，都以**本地 CLI** 形态运行——在能解析 Gitea 地址的机器上（gitea-ci VM 或你的 Mac），操作本地克隆，`git push` 走本机到 Gitea。这与[阶段 2.5](#) 选"VM 内 Claude Code"是同一个道理。

### 推荐

- **spec/plan 阶段**：用 **Claude Code + superpowers**（你要的 brainstorm→spec→plan 工作流就是这套技能，天然契合）。这一步在本地克隆做，人深度参与。
- **执行阶段**：Codex 或 Claude Code 都行——因为读的是同一份 spec/plan。想试 Codex 就在这步用 Codex CLI，规范放 `AGENTS.md` 即可。
- 建议先统一用一个把闭环跑通，再考虑混用。

---

## 5. 可追溯：索引 + 一致性校验（可选但推荐）

**变更索引 `docs/changes/INDEX.md`**：一个脚本扫所有 front-matter，生成总表（N / 标题 / 类型 / status / spec / plan / PR）。你一眼看到每个需求走到哪一步。

```bash
# scripts/build-index.sh 思路：grep front-matter 字段，拼成 markdown 表格
# 由 CI 在合并时自动重建并提交，或本地手动跑
```

**CI 一致性校验**（加进阶段 1 的 `ci.yml`）：PR 若改了 `backend/` 或 `frontend/` 代码，就检查是否存在对应 `docs/changes/<N>/spec.md` 且 front-matter 的 `issue` 有效——**强制"无 spec 不改码"**，从流程上保证绑定不断链。

**可选看板**：用一个 Cowork live artifact，读 Gitea issues + 仓库 front-matter，渲染成"需求 → spec → plan → PR → 部署"的实时状态墙，你每天打开就能看全貌。需要时我可以帮你搭。

---

## 6. 落到 rsdesign-new：接入 + 一个真实 CR 走查

**接入步骤**（一次性）：
1. 在 Gitea 建 `rsdesign-new` 仓库，把重构后的代码推上去（沿用阶段 1–2 的 CI/部署）。
2. 仓库根放 `AGENTS.md`（+ 一行 `@AGENTS.md` 的 `CLAUDE.md`）。
3. 建 `docs/changes/` 目录 + 一份 `docs/changes/_template/`（空的 00/01/02 模板，agent 照着填）。
4. 建标签：`needs-analysis / awaiting-triage / spec-drafting / spec-review / approved / pr-open / deployed`。
5. 扩展阶段 2.5 的 `poll.sh`：把 `spec-drafting`、`approved` 两个标签接到对应脚本。

**一个真实 CR 走查**（以项目里的"图号生成"为例）：

```
① 你提 issue #42「图号生成规则支持多段式编码」→ 打 needs-analysis
② agent 出 docs/changes/42-…/00-summary.md：
   现状规则 / 期望的多段式 / 影响到装配组件明细与搜索 / 是否动 schema / 风险
   → 贴评论，标签 awaiting-triage
③ 【闸门A】你确认方向 → spec-drafting
④ 本地 Claude Code + superpowers：brainstorm → 01-spec.md（编码格式、校验、迁移旧数据的策略、验收标准）
   → 02-plan.md（改哪些文件、Prisma 迁移、单测用例）→ 推分支，标签 spec-review
⑤ 【闸门B】你审 spec/plan（这里定生死）→ approved
⑥ agent 按 spec/plan 实现 → npm test → 开 PR（含 docs+代码，Closes #42）→ pr-open
⑦ CI 绿 → 【闸门C】你合并
⑧ 部署到测试环境 → 回帖 issue → deployed；验证后 promote 上生产
```

---

## 7. 与阶段 2.5 的衔接

本方案是阶段 2.5 的自然升级——把原来的"analyze → implement"两段，细化成"**analyze(总结) → spec/plan → implement**"三段，多了一道 spec 闸门和一批可追溯文档。脚本层面：
- `analyze.sh` 产出 `00-summary.md` 并提交（而不只是评论）。
- 新增 `spec.sh`（本地跑，带 superpowers）产出 `01/02`，走 `spec-review`。
- `implement.sh` 改成读 `docs/changes/<N>/` 的 spec/plan 来实现。
- `poll.sh` 多扫一个 `approved` 之外的 `spec-drafting` 状态。

---

## 8. 小结 + 待你定的两点

**绑定的答案浓缩成一句**：让 **issue 号 N** 当主键，spec/plan 以 `docs/changes/<N>/` 进仓库、带 front-matter，与 issue 双向链接，随 PR 一起 review，标签驱动生命周期。这样任何一处都能追溯到其余全部，且 spec/plan 天然成为喂给任何 agent 的"意图接口"。

**需要你拍板两点：**
1. **执行 agent**：先统一用 Claude Code（配 superpowers，闭环最顺），还是执行阶段试 Codex CLI（我就把 `AGENTS.md` 和执行脚本按 Codex 写）？
2. **spec 是否走独立"草案 PR"**：spec/plan 先单独开 docs-only PR 评审（更正式、闸门更清晰），还是直接和代码放同一个 PR 一起审（更快）？

你定了这两点，我就把 `AGENTS.md`、`docs/changes/_template/`、`spec.sh` 和改造后的 `implement.sh`/`poll.sh` 整理成可执行清单，接着阶段 2.5 往下接。
