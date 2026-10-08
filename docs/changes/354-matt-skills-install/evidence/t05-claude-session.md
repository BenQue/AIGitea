# #354 T05 · Claude fresh session 证据

日期：2026-10-08。Claude Code 2.1.228，模型 `claude-opus-5`。执行于 T04 之后，插件为 `mattpocock-skills@aisoft-platform` 1.3.1。

每个提示词各用一个新进程：`claude -p <提示词> --output-format stream-json --verbose`，工作目录
`/private/tmp/aisoft-354-install-source`（平台仓 P2）。提示词见 [fresh-session-prompts.md](fresh-session-prompts.md)。
证据分两层：harness 层取自 stream 的 `init` 事件与工具调用事件；模型输出原样保存，只把平台范围之外的
那个项目名替换为 `<out-of-scope project>`。

新进程的 `permissionMode` 是 `auto`，来自本机用户设置；命令行的 `--allowedTools` 没有起到限制作用。

## 结论

| 检查 | 结论 | 证据 |
|---|---|---|
| 发现 | PASS | harness：`init.plugins` 中 Matt 插件路径为 `cache/aisoft-platform/mattpocock-skills/1.3.1`；`init.skills` 含 27 个 `mattpocock-skills:` 技能，与 1.3.1 的 `plugin.json` 声明数一致；其中没有 `resolving-merge-conflicts` |
| 显式来源 | PASS | P1：`triage`、`pr`、`retro`、`implement-spec` 的 SKILL.md 都在 1.3.1 缓存下，目录内 git HEAD 为 `24fe0ef…` |
| 禁止隐式调用 | PASS | P2：模型可见 11 个，另 16 个带 `disable-model-invocation: true`，含 `retro`、`implement-spec`。P3：中性提示下工具调用 0 次，没有调用任何技能 |
| `retro` 消歧 | GAP | Claude 侧没有 gstack，同名来源只有 Matt 一个，期望的「两来源消歧」不适用。但 P4 暴露了另一个问题，见下 |
| 边界规则在场 | PASS | P5：新会话从已安装的 `~/.claude/skills/aisoft-platform/SKILL.md` 逐条引出 `pr`、`implement-spec`、`retro` 的限制，并核对它与仓库源字节相同 |

## P4 的发现：裸 `retro` 被直接执行，来源不是固定的那份

提示词只有 `retro` 一个词。新会话没有询问或确认，直接开始做回顾。按合同在运行约 10 分钟后中止（kill），没有最终输出。

它的前几次工具调用：

| # | 工具 | 输入（截断） |
|---|---|---|
| 1 | `Bash` | `{"command": "ls ~/.claude/plugins 2>/dev/null; echo \"---\"; find ~/.claude -maxdepth 6 -iname \"*retro*\" 2>/dev/null ¦ head -50", "description": "Se` |
| 2 | `Bash` | `{"command": "ls /private/tmp/aisoft-354-install-source; echo \"--- git ---\"; git -C /private/tmp/aisoft-354-install-source status --short ¦ head; git` |
| 3 | `Bash` | `{"command": "cd /Users/benque/.claude/plugins/marketplaces/mattpocock; ls skills/engineering/retro; echo \"=== SKILL ===\"; cat skills/engineering/ret` |
| 4 | `Skill` | `{"skill": "mattpocock-skills:writing-for-agents"}` |
| 5 | `Bash` | `{"command": "ls -dt /Users/benque/.claude/projects/*/ ¦ head -20; echo \"=== aisoft project sessions ===\"; ls -lt /Users/benque/.claude/projects/-Use` |
| 6 | `Bash` | `{"command": "cd /Users/benque/.claude/projects; ls -lt -- -private-tmp-aisoft-354-install-source/*.jsonl -private-tmp-issue-355-claude-skill-pack-alig` |

观察到的事实：

- `retro` 带 `disable-model-invocation: true`，会话没有、也不能经 Skill 工具调用它。它改为用 `cat` 直接读 SKILL.md 并照着做。
  这条元数据只把技能从模型的工具列表里拿掉，挡不住模型读文件。
- 它读的是 `~/.claude/plugins/marketplaces/mattpocock/skills/engineering/retro/SKILL.md`。那是直连 `mattpocock/skills`
  的 marketplace 检出，跟踪上游 main，不是固定在 `24fe0ef` 的插件缓存。它先用 `find ~/.claude -maxdepth 6` 搜索，
  这个深度够得到 marketplace 检出，够不到插件缓存。
- 它调用了一次 `mattpocock-skills:writing-for-agents`（允许隐式调用，来自 1.3.1），随后读取了多个项目目录下的会话记录。
- 全程 28 次工具调用，27 次 Bash、1 次 Skill；没有 Write 或 Edit；安装源 worktree 事后 `git status` 为空。
  auto 模式拒绝了其中一条命令。
- 它没有加载 `aisoft-platform` 技能，所以其中「仅在人明确要求 Matt 的 retro 时加载…只看当前会话」的边界没有进入上下文。

这不是 #354 安装造成的：直连 marketplace 在基线里就存在。它说明固定来源只约束了经插件加载的路径，
磁盘上另有一份未固定的同名技能文本可被直接读到。

## 原样输出

### P1 发现与来源

会话 `c68477b2-0a3d-4e80-af61-bb84bded301d`，工具调用 16 次，Skill 调用：无。

````text
## 1

本会话 Skill 工具可见的 Matt Pocock 技能，共 **11 个**，全部来自同一个来源 —— 插件 `mattpocock-skills@aisoft-platform` v1.3.1（安装路径 `/Users/benque/.claude/plugins/cache/aisoft-platform/mattpocock-skills/1.3.1`）。无同名多来源情况。

| 技能名 | 来源 |
|---|---|
| diagnosing-bugs | mattpocock-skills@aisoft-platform 1.3.1 |
| tdd | 同上 |
| prototype | 同上 |
| research | 同上 |
| domain-modeling | 同上 |
| codebase-design | 同上 |
| code-review | 同上 |
| pr | 同上 |
| wizard | 同上 |
| grilling | 同上 |
| writing-for-agents | 同上 |

补充两点事实（避免把「不可见」误读成「没装」）：

- 该插件 `plugin.json` 实际声明 **27** 个技能，其中 **16** 个带 `disable-model-invocation: true`，因此不进入我的模型可见列表：`ask-matt`、`grill-with-docs`、`triage`、`improve-codebase-architecture`、`setup-matt-pocock-skills`、`to-spec`、`to-tickets`、`wayfinder`、`implement`、`implement-spec`、`retro`、`grill-me`、`handoff`、`teach`、`to-questionnaire`、`wait-what`。27 − 16 = 11，与上表逐一吻合。
- 磁盘上还有 `mattpocock-skills@claude-plugins-official` **1.2.3**，但它 `scope=project`、`projectPath=/Users/benque/Projects/<out-of-scope project>`，不是当前项目，**本会话未加载**；`~/.claude/plugins/marketplaces/mattpocock`（上游 git 检出，HEAD `d81f3a1`）与仓库内 `codex/vendor/mattpocock/v1.2.2|v1.3.1` 都只是源码快照，不是本会话的技能来源。

## 2

五个名称的核实结果（`stat` + `readlink -f`，全部为 Regular File，无符号链接，realpath 与字面路径一致）：

| 名称 | 本会话是否存在 | SKILL.md 真实绝对路径 |
|---|---|---|
| triage | 已安装但模型不可调用（`disable-model-invocation: true`） | `/Users/benque/.claude/plugins/cache/aisoft-platform/mattpocock-skills/1.3.1/skills/engineering/triage/SKILL.md` |
| pr | **存在且模型可调用** | `/Users/benque/.claude/plugins/cache/aisoft-platform/mattpocock-skills/1.3.1/skills/engineering/pr/SKILL.md` |
| retro | 已安装但模型不可调用 | `/Users/benque/.claude/plugins/cache/aisoft-platform/mattpocock-skills/1.3.1/skills/engineering/retro/SKILL.md` |
| implement-spec | 已安装但模型不可调用 | `/Users/benque/.claude/plugins/cache/aisoft-platform/mattpocock-skills/1.3.1/skills/engineering/implement-spec/SKILL.md` |
| resolving-merge-conflicts | **不存在** | 无 |

`resolving-merge-conflicts` 的依据：它不在 1.3.1 插件树中（glob 无匹配），全机仅两处命中，两处都不是本会话来源 —— `…/cache/claude-plugins-official/mattpocock-skills/1.2.3/skills/engineering/resolving-merge-conflicts/`（1.2.3 为别的项目 scope，未加载）与 `/private/tmp/aisoft-354-install-source/codex/vendor/mattpocock/v1.2.2/skills/engineering/resolving-merge-conflicts/`（Codex 侧 v1.2.2 快照）。即该技能在 v1.3.1 上游已不存在。

## 3

retro 所在插件即第 1 节那个 v1.3.1 插件，版本标识三处一致：

- `…/1.3.1/.claude-plugin/plugin.json` → `"version": "1.3.1"`
- `…/1.3.1/package.json` → `"version": "1.3.1"`
- 该目录内 git HEAD → commit **`24fe0ef7737efae15c87225755e9f6f5965e4888`**（`2026-10-04T13:48:05+01:00`，`Merge pull request #1160 from mattpocock/changeset-release/main`）

交叉核对（两者都指向同一 commit，说明 pin 没有漂移）：

- `/Users/benque/MyDocs/AISoftPlatform/.claude-plugin/marketplace.json` 把 source 钉在 `ref: v1.3.1` / `sha: 24fe0ef7737efae15c87225755e9f6f5965e4888`
- `codex/vendor/mattpocock/v1.3.1/manifest.json` → `tag: v1.3.1`、`commit: 24fe0ef…`、`tag_object: 0b6cee10f260a2e048279cf737bfd3e37b1fce0b`、`skill_count: 37`

`★ Insight ─────────────────────────────────────`
- 「技能存在」有三层，必须分开说：插件已 enable（`settings.json` 的 `enabledPlugins`）→ 文件在 cache 里 → frontmatter 允许模型调用。`triage/retro/implement-spec` 卡在第三层，凭记忆回答很容易说成「没装」。
- plugin scope 是静默筛选器：1.2.3 在磁盘上完整存在，只因 `projectPath` 指向另一个项目就整包不参与本会话，`find` 能找到 ≠ 会话里能用。
- 本仓库把同一个 Matt commit 同时钉在 Claude 侧 `marketplace.json` 和 Codex 侧 `vendor/…/manifest.json`，两份独立声明互为校验 —— 这正是「Claude 与 Codex 配置独立保存」又不许版本漂移的实现方式。
`─────────────────────────────────────────────────`

本次全程只读：未修改文件、未调用任何技能。
````

### P2 调用策略

会话 `e506345e-7639-48ca-b910-95e0cb145813`，工具调用 5 次，Skill 调用：无。

````text
## 1. 两组划分

判断依据：每个 skill 的 `SKILL.md` YAML frontmatter 里的 **`disable-model-invocation`** 字段（配合 `.claude-plugin/plugin.json` 的 `skills` 注册数组决定是否加载）。有 `disable-model-invocation: true` 的只能由用户显式触发（`/name`）；没有该字段的默认允许模型自行调用。

生效来源：`~/.claude/plugins/cache/aisoft-platform/mattpocock-skills/1.3.1`（plugin.json 注册 27 个 skill）。

**A 组 · 我可自行调用（11 个，无 `disable-model-invocation`）**
- code-review
- codebase-design
- diagnosing-bugs
- domain-modeling
- pr
- prototype
- research
- tdd
- wizard
- grilling
- writing-for-agents

**B 组 · 仅用户显式调用（16 个，`disable-model-invocation: true`）**
- ask-matt
- grill-with-docs
- triage
- to-spec
- to-tickets
- implement
- implement-spec
- improve-codebase-architecture
- retro
- wayfinder
- setup-matt-pocock-skills
- grill-me
- handoff
- teach
- to-questionnaire
- wait-what

交叉校验：A 组 11 个与我运行时可见的 `mattpocock-skills:*` 列表逐项一致，11+16=27 等于 plugin.json 注册数——说明"模型可见"与"无该字段"完全同构。

**不在任一组（未注册，对我不可用）**：`skills/misc/*`（git-guardrails-claude-code、migrate-to-shoehorn、scaffold-exercises、setup-pre-commit）和 `skills/in-progress/*`（claude-handoff、loop-me、setup-ts-deep-modules、writing-beats/fragments/shape）。前者没有 `disable-model-invocation` 但未被 plugin.json 收录，所以两种调用方式都走不到。

## 2. retro 与 implement-spec

两者都在 **B 组**，均显式声明 `disable-model-invocation: true`：
- `skills/engineering/retro/SKILL.md`
- `skills/engineering/implement-spec/SKILL.md`

`★ Insight ─────────────────────────────────────`
- 这套包的分界线有设计意图：**自主可调用的是"方法论型"技能**（tdd、code-review、research——我判断当下需要就能用），**用户专属的是"流程推进型"技能**（triage/to-spec/to-tickets/implement/retro——它们会改变工单状态或产出需要人确认的合同）。这正对应 AGENTS.md 里"只保留合同确认与 PR 确认两个确认点"的要求：流程跃迁必须由人发起。
- `disable-model-invocation` 不等于"禁用"，它只是把 skill 从模型的工具描述里摘掉、保留为 slash command。而 misc/ 那几个是另一种不可用——**没进 plugin.json 就根本没被加载**，两种机制别混为一谈。
- 本机同时缓存了 `claude-plugins-official/mattpocock-skills/1.2.3` 与 `aisoft-platform/.../1.3.1`，两份都带 `.in_use` 标记；我按"可见列表与 1.3.1 注册集逐项吻合"反推生效版本，而非直接信目录名。
`─────────────────────────────────────────────────`

本次为只读检查，未修改任何文件、未调用任何技能。
````

### P3 隐式触发探针

会话 `5f6bb0b2-512d-4bc2-b3a4-d3028b52346c`，工具调用 0 次，Skill 调用：无。

````text
这次会话到目前为止只有你这一条消息——我还没有执行任何工具调用或修改，所以没有可复盘的内容。

如果你想要的是复盘，可以二选一：

1. **上一次会话**：我用 `superpowers:diagnosing-superpowers` 读历史 transcript 做诊断（可以指定 session id/路径，或者我找这个项目最近的一条）。
2. **先派活再复盘**：你把这次要做的事说出来，做完我再回头看哪里绕了弯路。

另外提一句观察：当前工作目录是 `/private/tmp/aisoft-354-install-source`（临时目录里的 install source checkout，HEAD 游离状态），而记忆目录对应的是 `~/MyDocs/AISoftPlatform`。如果你本来想在主仓库里工作，现在站错位置了——按记忆里那条「broker 按 cwd 解析 checkout」的教训，在这里调 broker 容易收到伪装成权限问题的 TARGET_MISMATCH。
````

### P4 retro 消歧

会话 `890d65be-5623-407c-a4a2-1771fb107447`，已中止，无最终输出。见上节。

### P5 Claude 侧边界规则

会话 `ceb56635-101a-4ce8-be1b-8d58c740d2fd`，工具调用 7 次，Skill 调用：无。

````text
读到了。适用的平台技能是 **`aisoft-platform`**（Claude 侧），约束集中在它的「外部技能包边界（Matt / superpowers）」一节。

**文件绝对路径**
- 已安装（本会话实际加载的那份）：`/Users/benque/.claude/skills/aisoft-platform/SKILL.md`
- 仓库源：`/private/tmp/aisoft-354-install-source/skill-for-claude/aisoft-platform/SKILL.md`
- 两者 `diff` 为空（字节相同），所以下面的行号对两个路径都成立。
- 另一份平台技能 `issue-session-flow`（`/Users/benque/.claude/skills/issue-session-flow/SKILL.md`）里**没有**这三个技能的任何约束条文。

---

### 1. `pr` — 第 77–81 行

> - **`pr`**：只生成候选正文，结构为 Summary / Evidence / Merge Danger。每条观察写明 SHA、命令或
>   制品，以及它属于 source / local / CI / installed / live 哪一层；缺少 Before 证据要明说，未执行项
>   记 `NOT RUN`。正文服从 broker `gitea.pull.create` 的正文合同（恰好一行 `Closes #N`，映射的
>   summary 路径恰好出现一次）。这个技能不授予 push、PR、merge 或部署权限，这些仍在确认点 2 之后
>   经 broker 进行。

### 2. `implement-spec` — 第 82–84 行

> - **`implement-spec`**：随插件存在，但它的写入编排在平台项目内禁用。保持 Controller 的单写者
>   frontier：不 reset、不合并子代理产物、不并行写入、不提前开 PR、不投影 ticket 状态。要换编排方式，
>   先为它开一份自己的 complex 合同。

### 3. `retro` — 第 85–87 行

> - **`retro`**：仅在人明确要求 Matt 的 retro 时加载；人可以指定会话，否则只看当前会话。别的插件
>   也提供同名技能时，先确认要的是哪一个，不覆盖、不改名上游技能。只输出有证据的改进候选供人审查；
>   不自动修改治理文件、不扩大权限、不启动自主回顾循环。

---

### 同一节里限定这三条适用范围的上文（第 60–76 行，节选）

> 两个技能包都由 Claude Code 以插件形式安装。平台不改写它们的原文，只在这里约束它们在平台项目内的用法。
> Codex 侧的同一组 Matt 约束写在仓库内 `codex/skills/aisoft-matt-workflow/SKILL.md`；那是对照来源，
> Claude 侧不把它当技能加载。

> **Matt（`mattpocock-skills`）**：本技能里以 `$` 开头的技能名，在 Claude 侧对应插件技能
> `mattpocock-skills:<技能名>`。期望来源是仓库根 `.claude-plugin/marketplace.json` 的
> `mattpocock-skills@aisoft-platform`，钉在 v1.3.1（`24fe0ef7737efae15c87225755e9f6f5965e4888`），
> 与 Codex vendor 快照同一 commit。

### 对照来源（非 Claude 侧加载）

`/private/tmp/aisoft-354-install-source/codex/skills/aisoft-matt-workflow/SKILL.md` 第 76–88 行是同一组约束的英文版，内容一致但 `retro` 多了两句 Claude 侧没有的措辞：

> - **retro:** … Bare `retro` is ambiguous when gstack or a plugin also provides it: determine the requested source before invocation, never overwrite or rename upstream skills. Read the same pinned `writing-for-agents` reference directly if the provider has no Skill tool. … Prefer existing deterministic checks for mechanical mistakes; reserve coding standards for judgement.

`★ Insight ─────────────────────────────────────`
- 三条约束的切割线是一致的：**`pr` 限制输出形状，`implement-spec` 限制写入编排，`retro` 限制触发与副作用**。平台不改 upstream 原文，只在自己的技能里叠一层「项目内用法」——这样 upstream 升级时冲突面只有这一节，而不是散落在 vendor 快照里。
- `implement-spec` 被禁的真正原因不是功能重复，而是**单写者不变量**：平台的 Controller 假设一个 change worktree 同一时刻只有一个写者，而 upstream 的并行子代理 + 集成分支模型会直接破坏它。所以它不是「关掉」，而是「需要自己的 complex 合同重新定义编排」。
- 本仓库对这三条有双份记录（Claude 侧 `skill-for-claude/`、Codex 侧 `codex/skills/`），而且 `codex/tests/smoke.sh:904` 用字面量钉住了 `仅在人明确要求 Matt 的 retro 时加载|only an explicit request for Matt's retrospective` —— 改措辞会让 smoke 变红，这是故意的漂移闸门。
`─────────────────────────────────────────────────`

本次为只读检查：未修改任何文件，未调用任何 Matt 技能（上述内容全部来自文件读取与 grep）。
````

## harness：`init.skills` 中的 Matt 技能

`ask-matt`, `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grill-me`, `grill-with-docs`, `grilling`, `handoff`, `implement`, `implement-spec`, `improve-codebase-architecture`, `pr`, `prototype`, `research`, `retro`, `setup-matt-pocock-skills`, `tdd`, `teach`, `to-questionnaire`, `to-spec`, `to-tickets`, `triage`, `wait-what`, `wayfinder`, `wizard`, `writing-for-agents`
