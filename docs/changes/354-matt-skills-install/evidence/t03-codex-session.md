# #354 T03 · Codex fresh session 证据

日期：2026-10-08。目标：当前 Mac，codex-cli 0.147.0。执行于 T02 的 S7 之后，受管入口为 v1.3.1。

## 结论

| 检查 | 结论 | 证据层 |
|---|---|---|
| 发现 | PARTIAL | harness：15 个允许隐式调用的受管技能全部在模型可见列表中，且解析到 v1.3.1。其余 22 个只验证到文件层，未在模型回合中验证 |
| 显式来源 | PARTIAL | harness：模型可见的 15 个受管入口真实路径都在 `releases/v1.3.1/`。`triage`、`retro`、`implement-spec` 的显式调用未在模型回合中验证 |
| 禁止隐式调用 | PARTIAL | harness：22 个 `disable_model_invocation` 技能无一出现在模型可见列表。行为探针 P3 未运行 |
| `retro` 消歧 | GAP / NOT RUN | 没有模型回合。harness 事实见下文：模型可见的 `retro` 只有 gstack 一个 |
| 模型回合（P1–P4） | GAP / NOT RUN | `codex exec` 三次失败，同一根因 |

没有用 Claude 侧的任何结果代替以上各项。

## `codex exec` 三次尝试

命令形态：`codex exec --ephemeral --sandbox read-only --color never --json -c model_reasoning_effort="medium" [-m <model>] - < P1`，
工作目录 `/private/tmp/aisoft-354-install-source`。

| # | 模型 | 退出码 | 服务端返回 |
|---|---|---|---|
| 1 | 配置默认 `gpt-6.1-sol` | 1 | `The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account.` |
| 2 | `gpt-6-astra` | 1 | `The 'gpt-6-astra' model requires a newer version of Codex. Please upgrade to the latest app or CLI and try again.` |
| 3 | `gpt-5-codex` | 1 | `The 'gpt-5-codex' model is not supported when using Codex with a ChatGPT account.` |

根因相同：本机 CLI 0.147.0 拿不到该账号可用的模型。按合同三次即停。

三次启动都在模型请求之前打印了同一条 harness 事件：

```text
Exceeded skills context budget. All skill descriptions were removed and 57 additional skills were not included in the model-visible skills list.
```

同一次启动还报 `Model metadata for <model> not found. Defaulting to fallback metadata`。预算可能取自回退元数据，
所以这条截断在新版本 Codex 中是否出现未知。它说明：在这台机器的 CLI 上，技能数量已超过模型可见列表的预算。

## harness 层：模型可见的技能列表

命令：`codex debug prompt-input "ping"`。它渲染会话开始时发给模型的输入，不发起模型请求。
列表共 301 条，技能根 20 个。以下只摘录与 Matt 相关的条目。

受管来源，根为 `~/.agents/skills`，共 15 条，真实路径全部在 `releases/v1.3.1/`：

| 名称 | 解析到 `releases/` 下的路径 |
|---|---|
| `code-review` | `v1.3.1/skills/engineering/code-review/SKILL.md` |
| `codebase-design` | `v1.3.1/skills/engineering/codebase-design/SKILL.md` |
| `diagnosing-bugs` | `v1.3.1/skills/engineering/diagnosing-bugs/SKILL.md` |
| `domain-modeling` | `v1.3.1/skills/engineering/domain-modeling/SKILL.md` |
| `git-guardrails-claude-code` | `v1.3.1/skills/misc/git-guardrails-claude-code/SKILL.md` |
| `grilling` | `v1.3.1/skills/productivity/grilling/SKILL.md` |
| `migrate-to-shoehorn` | `v1.3.1/skills/misc/migrate-to-shoehorn/SKILL.md` |
| `pr` | `v1.3.1/skills/engineering/pr/SKILL.md` |
| `prototype` | `v1.3.1/skills/engineering/prototype/SKILL.md` |
| `research` | `v1.3.1/skills/engineering/research/SKILL.md` |
| `scaffold-exercises` | `v1.3.1/skills/misc/scaffold-exercises/SKILL.md` |
| `setup-pre-commit` | `v1.3.1/skills/misc/setup-pre-commit/SKILL.md` |
| `tdd` | `v1.3.1/skills/engineering/tdd/SKILL.md` |
| `wizard` | `v1.3.1/skills/engineering/wizard/SKILL.md` |
| `writing-for-agents` | `v1.3.1/skills/productivity/writing-for-agents/SKILL.md` |

这 15 个名称恰好是 v1.3.1 manifest 中 `disable_model_invocation` 为假的全部技能。
另外 22 个为真的技能无一出现，其中包括 `retro`、`implement-spec`、`triage`。

独立插件来源 `mattpocock-skills@claude-plugins-official` 1.2.3，共 11 条，以 `mattpocock-skills:` 前缀并存：

| 名称 | 插件缓存内路径 |
|---|---|
| `mattpocock-skills:code-review` | `1.2.3/skills/engineering/code-review/SKILL.md` |
| `mattpocock-skills:codebase-design` | `1.2.3/skills/engineering/codebase-design/SKILL.md` |
| `mattpocock-skills:diagnosing-bugs` | `1.2.3/skills/engineering/diagnosing-bugs/SKILL.md` |
| `mattpocock-skills:domain-modeling` | `1.2.3/skills/engineering/domain-modeling/SKILL.md` |
| `mattpocock-skills:grilling` | `1.2.3/skills/productivity/grilling/SKILL.md` |
| `mattpocock-skills:prototype` | `1.2.3/skills/engineering/prototype/SKILL.md` |
| `mattpocock-skills:research` | `1.2.3/skills/engineering/research/SKILL.md` |
| `mattpocock-skills:resolving-merge-conflicts` | `1.2.3/skills/engineering/resolving-merge-conflicts/SKILL.md` |
| `mattpocock-skills:tdd` | `1.2.3/skills/engineering/tdd/SKILL.md` |
| `mattpocock-skills:wizard` | `1.2.3/skills/engineering/wizard/SKILL.md` |
| `mattpocock-skills:writing-for-agents` | `1.2.3/skills/productivity/writing-for-agents/SKILL.md` |

观察：

- 受管路径不再提供 `resolving-merge-conflicts`。独立插件仍以 `mattpocock-skills:resolving-merge-conflicts` 提供它。
- 10 个名称在两个来源同时可见，版本不同：受管为 v1.3.1，插件为 1.2.3。
- 模型可见的 `retro` 只有一条，指向 `~/.agents/skills/gstack/retro/SKILL.md`。Matt 的 `retro` 只能显式调用，
  所以不在列表中。模型自行触发 `retro` 时得到的是 gstack 的；用户显式输入 `retro` 时 Codex 选哪一个，没有验证。
- `pr` 是新技能，允许隐式调用，已可见，解析到 v1.3.1。

这层证据来自 CLI 0.147.0 的渲染。Codex 桌面应用使用更新的运行时，结果可能不同。

## 对 `~/.codex` 的副作用

T02 的 installer 没有写 `~/.codex`。运行 Codex CLI 期间，`~/.codex/config.toml` 在 08:47:12 被改写：
`marketplaces.claude-plugins-official` 的 `last_revision` 由 `85cce03…` 变为 `b78ac49…`。这是 Codex 自身的
marketplace 刷新。当时 Codex 桌面应用也在运行，无法区分是 CLI 启动还是桌面应用所为。

读回：Matt 插件仍为已启用、1.2.3、`c55ee46…`，缓存树哈希与基线相同；受管清单与 S6 逐项相等。
`--ephemeral` 没有留下会话记录，Codex 自己的日志库照常写入。

另记：`config.toml` 的 `model` 在本会话期间由 `gpt-6-astra` 变为 `gpt-6.1-sol`，第一次 `codex exec`
之前就已如此，不是本会话写入。

## 待补：人工转述的模型回合

合同的后备路径是由人在新开的 Codex 会话里依次发送 [固定提示词](fresh-session-prompts.md) 的 P1–P4 并回传输出。
尚未执行。回传后原样追加在本节，证据层标注为人工转述。
