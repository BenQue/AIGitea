---
issue: 142
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/142
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/142-loop-pr-url-backfill
created: 2026-08-22
updated: 2026-08-22
---

# Spec：`pr_url` 回填与 front matter 契约闸门

## 1. 目标与原因

change 文档的 front matter 契约目前只有约定、没有闸门，表现为两个缺陷：

- **A**：`pr_url` 从来没有写入方，回填是纯手工步骤，漏做静默；
- **B**：`resolve-documents` 所依赖的 front matter 没有任何检查，坏掉的变更能合并进 `main`。

本变更把 A 变成一条确定性命令，把 B 变成一个确定性检查，并让后者成为前者的验收手段。

### 1.1 为什么 A 与 B 合在同一个变更里

Issue 正文授权把 B 拆成独立 Issue。此处**裁决为不拆**，理由是二者不只是同根因，而是同一处代码面上互为验收的两半：

- 两者都读同一个入口（`contract._document_context` → summary front matter），B 的检查若不复用 A 的解析路径就会是第二套实现；
- Issue 的验收标准「`pr_url` 空、且 PR 已存在时，检查/回填能指出它」**只能由 B 的检查满足**——A 单独交付没有任何东西能证明它没被漏做；
- 拆开会产生两个 PR 改同一个 `cli.py` 与同一份 `aisoft-project-check.sh`，制造一次不必要的冲突面。

代价：本变更的 diff 比拆开时大。接受这个代价。

## 2. 裁决一：`pr_url` 只写在 summary

Issue §3 与其后的评论列出 `admin/LocalWMS` 九个 change 目录的三种形状，要求给出唯一答案。**裁决：`pr_url` 只出现在 summary 的 front matter；spec / plan / verification 不带该键。**

### 2.1 决定性论据：非 summary 文档里的 `pr_url` 没有消费者

这不是风格偏好，是可以从代码读出来的事实。平台代码从非 summary 的 change 文档里只读四个键：

| 读取点 | 读的键 |
|---|---|
| `contract.py:474` `_validate_complex_document_front_matter` | `issue`、`branch`、`effective_complexity` |
| `contract.py:407-420` `_resolve_documents` | `created` |
| `documents.py:_publish` | `issue`、`branch`、`created` |

`pr_url` 不在其中任何一处。spec/plan/verification 里的那一行是纯复制品：写它要写四遍，改它要改四遍，四份之间可以不一致，而没有任何代码或人会因为它一致而得到好处。

### 2.2 与另一条书面事实一致

`documents` 角色映射本身就只存在于 summary。「关于这个变更整体的事实住在 summary，各角色文档只描述自己」已经是既有形状，`pr_url` 属于前者。

### 2.3 一处反向证据，以及为什么裁决不变

取证时发现 `admin/LocalWMS` 已经合并 PR #21（`0699eee`），标题是「统一 change 文档 front matter 的 `pr_url`——**四份都带**」。方向与本裁决相反，必须摆在这里而不是略过。

它不改变裁决，理由有三：

1. 它是目标仓在**平台裁决尚不存在时**做的本地统一，而 Issue #142 正文与评论明确把这个选择留给平台裁决；
2. §2.1 的论据是可从代码读出的事实——非 summary 文档的 `pr_url` 没有消费者。这个事实不因某个仓选了哪种形状而改变；
3. 采纳「只有 summary 带」**不会**让 LocalWMS 转红：§5.2 裁决检查不报告非 summary 文档里残留的 `pr_url`，#21 的成果保持全绿。

冲突只存在于「今后新写的文档按哪种形状」与「模板长什么样」，由合并本 PR 的人一次性决定。

### 2.4 与实践证据一致

Issue 评论记录：`admin/LocalWMS` 最近四个变更（11、12、16、18）由三个互不相干的会话产出，全部收敛到「只有 summary 带 `pr_url`」。三次独立收敛到同一形状是关于「哪种形状在实际使用中站得住」的证据。

### 2.5 被否决的选项

**「四份都带，由回填命令一次写四处」**：反对理由是它把一个没有读者的字段的维护成本自动化，而不是消除。回填命令确实能让四处保持一致，但一致的四份复制品仍然是四份复制品；而一旦有人手工编辑其中一份（历史上正是这样漂移的），命令的 fail-closed 检查就会在四个位置上各报一次同一个问题。保留复制只有一个真实好处——单独打开 `spec-*.md` 的读者能看到 PR 链接；这个好处由「同目录下就有 summary」抵消。

### 2.6 连带修改（本 spec 明确授权）

裁决为「只有 summary 带」就必须同步下列书面合同，否则新项目会继续按模板生成、继续漂移：

1. `templates/docs/changes/_template/{spec,plan,verification}.md` 删除 `pr_url:` 行（summary.md 保留）；
2. `03-Issue-Spec-Plan与单闸门开发流程.md:71` 的「所有 change 文档的共同 front matter」清单移出 `pr_url`，改为 summary 专属字段；
3. `skill-for-claude/SKILL.md` 与 `skill-for-codex/SKILL.md` 的会话标准动作第 4 步改为调用新命令。

**不追溯**：已合并仓库里带四份 `pr_url` 的历史文档保持原样。它们是惰性的，重写它们会制造与内容无关的巨大 diff。合同只约束新写入。

## 3. 裁决二：写在 `aisoft-loop` 子命令层

Issue §A.1 给出三个候选，逐条论证：

### 3.1 选中：新增 `aisoft-loop backfill-pr-url`

```
PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli \
  backfill-pr-url 142 --repo <checkout> --pr-url <url>
```

理由：

- **有先例且同构**：`publish-spec` / `publish-plan` 已经是「解析 `documents` 映射 → 原子写入 change 目录里的一份文档」，回填是同一件事的第三个实例，复用同一套路径逃逸与 symlink 防护；
- **不需要凭据**：写本地工作树的一行文本不需要任何 token，因此不该穿过凭据边界；
- **不需要重装**：broker 是 root-owned 的安装期快照（`/usr/local/lib/aisoft-host-access`），任何 broker 侧改动都要人输密码在两台机器上重装才生效。把一个不需要凭据的功能放进 broker，等于给它加上一个与其性质无关的部署闸门。

### 3.2 否决：在 broker 的 `gitea.pull.create` 里顺手改工作树

值最现成（`html_url` 就在响应体里），但：

- broker 目前**完全不写工作树**——它的写面只有 Gitea API 与 `git push`。让一个「建 PR」的操作留下未提交的文件改动，会让调用方在不知情的情况下持有脏工作树；
- 它把两件可以独立失败的事捆成一次调用：PR 建成功、文件写失败时没有可判读的中间态；
- 承接 3.1 第三条：附带重装闸门。

### 3.3 否决：新增 broker typed 操作 `git.change.pr_url.write`

比 3.2 显式，但仍然把一个无凭据的本地文件写入放进凭据边界内，且要付 6 处枚举点同步 + 两台重装的代价，换不到任何 3.1 给不了的东西。

### 3.4 裁决三：不连带 commit 与 push

新命令**只写文件**，commit 与 push 仍由调用方完成。理由：

- `publish-spec` / `publish-plan` 同样只写文件，保持一致；
- push 走 broker `git.push.change`，带 `BASE_BRANCH_STALE`、`--force-with-lease` 与 `REMOTE_BRANCH_MOVED` 三条既有语义。把它们藏进一个文档写入命令里，会让这些错误在一个读者预期只有文件 I/O 的地方冒出来；
- 一个只读写单个文件的命令可以被安全地重复执行，这正是幂等验收标准要求的性质。

### 3.5 诚实说明：额外那次 commit + push 消不掉

Issue 把「每个 complex 变更都要多付一次 commit + push」列为代价。**本变更不消除它，也不可能消除**：`pr_url` 的值来自 PR，而 PR 只有在分支推上去之后才能创建，因此第二次推送是结构性的。

本变更真正交付的是另外两件事：把那次编辑从手工变成确定性、幂等、冲突 fail-closed 的一条命令；并让漏做这一步从静默变成有检查会指出来。spec 在此明确这一点，以免 PR 被读成「省了一次推送」。

## 4. `backfill-pr-url` 的行为契约

输入：Issue 号、checkout 路径、PR URL。

1. 经 `contract` 解析该 Issue 的唯一 change 目录与 active summary（复用既有的 `CHANGE_NAME_CONFLICT`、legacy 证据、`documents` 映射校验）；
2. **URL 自洽校验**：summary 必须声明 `gitea_url`，形如 `<prefix>/issues/<N>` 且 `<N>` 等于本 Issue 号；传入的 `--pr-url` 必须精确形如 `<prefix>/pulls/<正整数>`。这挡住把别的仓库、别的 Issue 或一个任意字符串写进 front matter，且不需要联网；
3. 定位 front matter 内的 `pr_url` 行（只在 `---` 与 `---` 之间找，正文里的同名字符串不算）：
   - 键缺失 → `ContractError`（summary 必须声明该键；缺失说明文档不是按模板生成的）；
   - 值为空 → 写入，返回 `changed`；
   - 值与传入值逐字相同 → **不写文件**，返回 `unchanged`（重复执行零 diff）；
   - 值不同且非空 → `ContractError` **fail-closed**。一个变更只有一个 PR，出现第二个值说明前提被破坏，静默覆盖会抹掉这个信号；
4. 写入方式与 `_publish` 一致：同目录 `mkstemp` + `fsync` + `os.replace`，`0o644`；除 `pr_url` 那一行外整个文件逐字节不变（不动 `updated`——见 4.1）。

### 4.1 连带推进 `status` 到 `pr-open`（实现期发现，必须裁决）

首次把巡检跑在平台仓自身上时暴露了一个顺序缺陷：历史会话（含 #138）在**首次推送**时就把 summary 写成 `status: pr-open`，而此时 PR 还不存在、`pr_url` 必然为空。若巡检只按 §5 的判据工作，**每个变更的第一次 CI 都会因为自己的文档而变红**——一个新闸门把正常流程判成违规，是闸门的错，不是流程的错。

根因是那句 `status: pr-open` 在写下的时刻是**假的**。裁决：

1. change 文档在首次推送时携带**真实的**前置状态（通常是 `approved`）；
2. `backfill-pr-url` 在写入 `pr_url` 的同时，把 `status` 推进到 `pr-open`——**当且仅当**当前状态还不属于 `{pr-open, completed, deployed}`。已经是 `completed` 或 `deployed` 的变更不会被降级回 `pr-open`。

这样「PR 存在」这一个事实的两处记录被同一条命令、在同一个时刻写下，巡检的判据在任何时间点都可满足，且不需要人再手工改一次 `status`。幂等性不受影响：两者都已正确时命令一个字节都不写。

### 4.2 为什么不顺手更新 `updated`

`updated` 会让「值已正确时不产生 diff」这条验收标准在跨日重跑时失效。回填是把一个已经确定的事实补进文档，不是内容修订。

## 5. `check-change-documents` 的行为契约

```
PYTHONPATH=codex/runtime python3 -m aisoft_loop.cli check-change-documents --repo <checkout>
```

只读，遍历 `<repo>/docs/changes/` 下每个目录（跳过 `_template`），输出稳定排序的 `PASS:` / `GAP:` 行，末尾 `result: pass=… gap=…`，有 GAP 时退出码 1。

判据两条：

1. **`change-documents`**：目录名必须能解析成 change 名元组，且 `resolve_documents(N)` 必须成功。GAP 行必须点名**是哪个变更、哪个文件、什么原因**——Issue 的负向验收标准明确要求这三样；
2. **`change-pr-url`**：当 summary 的 `status` 属于「PR 必然已存在」的生命周期（`pr-open`、`completed`、`deployed`）时，`pr_url` 不得为空。

### 5.1 为什么用 `status` 而不是查远端

Issue 的验收标准说「`pr_url` 空、且 PR 已存在时，检查能指出它」。判定「PR 已存在」有两条路：查 Gitea，或读仓库里已有的声明。选后者：

- 检查因此是纯离线、纯确定性的，可以在任何 checkout 上跑，包括 CI 与没有凭据的环境；
- `status` 本身就是平台的生命周期事实源，`pr-open` 的字面含义就是「PR 已开」。一个 `status: pr-open` 却 `pr_url:` 为空的 summary 是自相矛盾的，这个矛盾不需要联网就能判定；
- 远端查询会让一个只读检查需要凭据，并把它的结果绑到网络可达性上。

代价：状态还停在 `approved` 而 PR 其实已开的窗口期漏报。接受——那个窗口正是「还没走到回填这一步」的正常状态。

### 5.2 刻意不检查的事

**不**报告 spec/plan/verification 里残留的 `pr_url` 键。§2.6 裁决不追溯，检查若报告它们，等于用另一种方式强制追溯，会让每个已接入仓一上来就是一片红。

## 6. 模板改动的连带影响（已知、有意、有处置）

`aisoft-project-check.sh` 用 `cmp -s` 逐字节比对目标仓的 `docs/changes/_template/` 与平台模板。改模板会让**所有已接入仓的 `change-templates` 检查转 GAP**，直到各仓自行同步。

这不是回归，是漂移检测器正常工作：它就是为「平台模板变了而项目没跟」设计的。处置路径是既有的——每个目标仓开自己的小 Issue/小 PR 同步三份模板文件。本变更不代任何目标仓提交（与「不追溯」同一条理由：那是各仓自己的变更）。

verification 需记录本次会让哪些仓转红，以便人决定同步节奏。

## 7. Acceptance criteria

- [ ] `pr_url` 的写入位置唯一，且 spec §3 逐条论证了为何不选 broker 内联与新 broker typed 操作两个候选；
- [ ] 「哪些角色的文档带 `pr_url`」有唯一答案（只有 summary），`templates/docs/changes/_template/` 三份非 summary 模板同步去键；
- [ ] 对已有正确值的 summary 重复执行 `backfill-pr-url` 不产生任何 diff（`git diff` 为空）；
- [ ] 对已有不同非空值的 summary 执行 `backfill-pr-url` fail-closed 报错并且不写文件；
- [ ] `--pr-url` 与 summary 的 `gitea_url` 不自洽（不同主机/owner/repo，或不是 `/pulls/<正整数>`）时报错；
- [ ] `check-change-documents` 对仓库里每个 change 目录断言 `resolve-documents` 成功；
- [ ] 负向验证：删掉任意一份 spec/plan/verification 的 front matter，检查变红并指明是哪个变更、哪个文件；
- [ ] 负向验证：`status: pr-open` 且 `pr_url` 为空时，检查变红并点名该变更；
- [ ] 该检查已接进 `aisoft-project-check.sh`（目标仓）与 `codex/tests/smoke.sh`（平台仓自身），且在 `admin/LocalWMS` 当前 `main` 上的运行结果如实记录，不为了变绿而调整判据；
- [ ] `bash codex/tests/smoke.sh` 全过，Python 单测全绿。

## 7.1 一处必须先修的存量缺陷：`docs/changes/58/00-summary.md`

巡检在平台仓自身上报出的**唯一**文档缺陷：变更 58 是 pre-#57 的 legacy 目录（`00-summary.md` 等），但它的 summary 声明了 `documents:` 映射，而 `contract.py:370` 明确禁止 legacy summary 携带该映射。因此 `resolve-documents 58` 今天在 `main` 上就是失败的——正是本变更要拦的那一类缺陷，恰好存在于平台仓自己。

处置：删除该 summary 的 `documents:` 五行。它声明的映射与 `LEGACY_DOCUMENTS` 推断出的完全相同，删除不丢任何信息。

这不违反「不追溯修补历史文档」——那条约束针对的是**目标仓**（LocalWMS 侧）。平台仓要把闸门接进自己的 `smoke.sh`，就必须先让自己通过；留着它等于交付一个一上来就红的闸门。

## 8. 明确不做

- 不改语义命名合同（`<role>-<短描述>-<YYMMDD>.md` 与 `documents` 映射）；
- 不追溯修补任何已合并仓库里的历史文档；
- 不代目标仓同步模板；
- 不引入新的运行时依赖；
- 不新增或修改任何 broker typed 操作。
