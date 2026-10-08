---
issue: 354
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/354
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - rollback
  - external-contract
depends_on:
  - 355
status: in-progress
branch: change/354-matt-skills-install
created: 2026-10-08
updated: 2026-10-08
---

# #354 验证记录

## 基线与范围

- 平台 source pin：`8162fe7d71dd58b13ca80ef26467a2549973f4df`
- 基线：`origin/main` = `8162fe7d71dd58b13ca80ef26467a2549973f4df`，2026-10-08 经 broker `git.fetch.main` 读回
- 环境：当前 Mac，target-home `/Users/benque`；Claude Code 2.1.228，codex-cli 0.147.0
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-6

## T01 只读基线（2026-10-08）

本节全部来自只读命令，没有写入 `~/.agents`、`~/.claude`、`~/.codex`。完整清单见
[t01-baseline.json](evidence/t01-baseline.json)，由 [inventory.py](evidence/inventory.py) 生成。

| 对象 | 观测 |
|---|---|
| 上游 tag | `git ls-remote --tags` 最高为 v1.3.1，tag object `0b6cee1…`，peel 到 `24fe0ef…`；main 为 `f3fc5632…` |
| 官方 marketplace | `anthropics/claude-plugins-official` HEAD `b78ac49…`，Matt 条目 `sha` 仍为 `c55ee46…` |
| 受管入口 | `current -> releases/v1.2.2`，无 `previous`；只有 `releases/v1.2.2`，35/35 技能目录哈希等于 manifest，整树等于仓库 vendor |
| 受管链接 | 35 个，全部指向 `../vendor/mattpocock/current/...` |
| adapter | 8 个目录，18 个文件；4 个文件与 pin 源字节不同 |
| 无关条目 | 117 个，含 `gstack/` 与 12 个指向 OpenSpec 的链接 |
| 旧 lock | `.skill-lock.json` sha256 `4444d0db…`，41 条记录来源为 `mattpocock/skills` |
| 权限 | `~/.agents` 0700，`skills/`、`vendor/` 及以下 0755，属主 benque:staff |
| 安装预检 | `matt_snapshot preflight-install` 对真实 HOME 通过：新增 `implement-spec`、`pr`、`retro`，退役 `resolving-merge-conflicts`；两条 warning 为旧 lock 保留与 `retro` 同名 |
| 漂移检查 | install-skills 面 GAP：期望 `releases/v1.3.1`，已装 `releases/v1.2.2`；skill-for-claude 面 PASS；其余六个面 GAP |
| Codex 独立插件 | `mattpocock-skills@claude-plugins-official`，已启用，1.2.3，`c55ee46…` |
| Claude 独立插件 | 两条记录，user 与 project 作用域各一，均为 1.2.3，`2ab9580…`；user 作用域已启用 |
| Claude marketplace | 另有名为 `mattpocock` 的直连条目，跟踪 `mattpocock/skills`，`autoUpdate` 为真，没有插件从它安装 |
| Claude 侧 gstack | `~/.claude/skills/` 下没有 `gstack` 或 `retro` |

三个基线摘要，供 T02 的 S0 比对：

| 摘要 | 值 |
|---|---|
| matt_links | `167ac8bbf9d152b6a8a4808d8b82686f2b5a1a62066ac9d476bee1c042cb6b55` |
| adapters | `f8e892625fb6d0b530526cf1c98f17aeb38318cd9a45083604b85c8f9161c700` |
| unrelated | `8fefe466016a04eef30af07b873956dd72382fdfab2fe9430890efdf9cd584d5` |

## T02 阶段一：Codex 受管安装（2026-10-08）

确认点 1 通过后执行。命令 `bash codex/install-skills.sh /Users/benque`，安装源为 detached 在 pin 上的
`/private/tmp/aisoft-354-install-source`。完整记录见 [t02-codex-managed-install.json](evidence/t02-codex-managed-install.json)。

| 步 | 动作 | 结果 |
|---|---|---|
| S0 | broker fetch；重读清单 | PASS。origin/main 等于 pin；上游 v1.3.1 仍 peel 到 `24fe0ef…`；清单与基线逐项相等 |
| S1 | 备份到 `~/.agents/backup-issue-354-20261007T234458Z/` | PASS。8 个 adapter 目录 18 个文件，`diff -r` 无差异；记录 47 条链接 |
| S2 | 安装 | PASS，exit 0。14 条断言全部成立，见下 |
| S3 | 再次安装 | PASS，exit 0。清单与 S2 逐项相等，previous 仍为 v1.2.2 |
| S4 | `--rollback` | PASS，exit 0。current 为 v1.2.2，previous 为 v1.3.1；35 个入口与基线相同，全部解析到 `releases/v1.2.2/` |
| S5 | 从备份恢复 8 个 adapter | PASS。全部条目与基线逐项相等；残留恰为 `releases/v1.3.1/`、`previous` 与备份目录 |
| S6 | 第三次安装 | PASS，exit 0。清单与 S2 逐项相等 |
| S7 | `check-installed-drift`、`codex/check-drift.sh` | PASS。install-skills 面由 GAP 变为 PASS；`check-drift.sh` 为 `CLEAN` |

S2 断言：入口恰为 manifest 的 37 个名称；`resolving-merge-conflicts` 不存在；37 个链接都解析到
`releases/v1.3.1/` 下存在的 SKILL.md；`releases/v1.3.1` 的 37/37 技能目录哈希等于 manifest 且整树等于 pin 源，
目录 0755、文件 0644 或 0755；8 个 adapter 与 pin 源 `diff -r` 无差异；117 个无关条目逐项不变；
旧 lock 的 sha256 不变；`releases/v1.2.2` 树哈希不变；`~/.agents` 仍为 0700；没有 stage 残留；
`~/.agents` 顶层只多出备份目录。每一步之后 Claude 与 Codex 插件两段清单都与基线相等。

installer 对 detached HEAD 打印了 `staleness unchecked` 的 WARNING，这是合同预期；新鲜度由 S0 的 broker fetch 读回补足。

S7 中其余安装面：五个面的 GAP 段落逐字节不变，skill-for-claude 面仍为 PASS。install-vm 面仍为 GAP，
少了一行 `nested-installer-gap`，因为它嵌套检查的 install-skills 已对齐；没有别的行变化。

未在真实目标上做故意失败注入，失败路径的证据只有 #352 隔离 HOME 的 installer 测试。

## T03 Codex fresh session（2026-10-08）

详见 [t03-codex-session.md](evidence/t03-codex-session.md)。

- 模型回合为 GAP / NOT RUN：`codex exec` 三次失败，根因相同，本机 CLI 0.147.0 拿不到该账号可用的模型。
- harness 层有证据：`codex debug prompt-input` 渲染的模型可见列表里，15 个允许隐式调用的受管 Matt 技能全部存在
  并解析到 v1.3.1；22 个只能显式调用的技能无一出现。
- 模型可见的 `retro` 只有 gstack 一条。用户显式输入 `retro` 时 Codex 的选择没有验证。
- Codex 独立插件 1.2.3 按 C2 未改动。它以 `mattpocock-skills:` 前缀提供 11 个技能，其中 10 个与受管 v1.3.1 同名并存，
  另一个是受管路径已退役的 `resolving-merge-conflicts`。
- CLI 启动时报告技能列表超出上下文预算，57 个技能未进入模型可见列表。该预算可能取自回退的模型元数据。
- 运行 Codex CLI 期间 `~/.codex/config.toml` 的 marketplace 元数据被 Codex 自身刷新；Matt 插件记录与缓存未变。

## T04 阶段二：Claude 侧（2026-10-08）

用户告知 #355 已合并后执行。完整记录见 [t04-claude-plugin.json](evidence/t04-claude-plugin.json)。

启动规则五条全部成立：

| # | 规则 | 读回 |
|---|---|---|
| 1 | #355 已关闭，merge commit 是 origin/main 的祖先 | Issue `closed`，PR #356 的 merge commit `b356085d1d507ba0d66fe3b8d118e4a57edf7075` 即 broker fetch 后的 origin/main |
| 2 | P2 是阶段一 pin 的后代 | 是 |
| 3 | Matt 快照、installer、`matt_snapshot.py` 无差异 | `git diff --stat` 为空 |
| 4 | marketplace 条目 `sha` 等于上游 commit | `24fe0ef…`；`check-plugin-pin.sh --source-only` 输出 `PIN_SOURCE_OK` |
| 5 | 上游 v1.3.1 仍解析到同一 commit | 是 |

**P2 = `b356085d1d507ba0d66fe3b8d118e4a57edf7075`。** #355 的交付物与合同假设一致：文件在仓库根
`.claude-plugin/marketplace.json`，marketplace 名为 `aisoft-platform`，检查工具的四个结论名称不变。
change 分支已 rebase 到 P2，安装源 worktree 移到 P2。

| 步 | 动作 | 结果 |
|---|---|---|
| 备份 | 三个文件、两个 Claude 技能目录、Codex 的 `aisoft-platform` adapter，写到 `~/.claude/backup-issue-354-20261008T111330Z/` | PASS，逐项比对无差异 |
| X2 | `bash skill-for-claude/install.sh /Users/benque` | PASS，exit 0；`check-drift.sh` 为 `CLEAN`；已装技能含「外部技能包边界」一节 |
| X3 | `bash codex/install-skills.sh /Users/benque` | PASS，exit 0；只有 `aisoft-platform` adapter 变化，Matt 指针、入口、release 不变；`codex/check-drift.sh` 为 `CLEAN` |
| X4 | `claude plugin validate`；按目录注册 marketplace | PASS；注册前主 checkout HEAD 等于 P2 且干净 |
| X5 | 卸载 user 作用域的官方来源，安装 `mattpocock-skills@aisoft-platform` | PASS；记录为 1.3.1 / `24fe0ef…`；缓存内 37/37 技能目录哈希等于 vendor manifest，LICENSE 哈希相等 |
| 回滚演练 | 卸载平台来源 → 安装官方来源 → 读回 → 卸载 → 安装平台来源 → 读回 | PASS；中间态为官方 1.2.3 / `c55ee46…`；终态记录与 X5 相同，缓存仍 37/37 |
| pin 检查 | `check-plugin-pin.sh /Users/benque` | 当时为 `PIN_DRIFT`，恰一条 DRIFT：平台范围之外项目的项目级记录。PR 提交后已变为 `PIN_CLEAN`，见「PR 提交后的清理」 |
| 漂移检查 | `check-installed-drift` | install-skills 面与 skill-for-claude 面均为 PASS |

对照备份的差异：`installed_plugins.json` 33 个插件 id 中只有两个 Matt id 变化；`known_marketplaces.json` 只新增
`aisoft-platform`；`settings.json` 只有 `enabledPlugins` 的两个 Matt 键与 `extraKnownMarketplaces` 的一个键变化。

### 与合同不符之处

1. **共享缓存被覆盖。** 回滚演练重新安装官方来源时，Claude Code 把 `cache/claude-plugins-official/mattpocock-skills/1.2.3`
   重新填充为 `c55ee46` 的内容。演练前该目录是 `2ab9580` 的内容。旧字节没有备份，新检出是浅克隆，无法从磁盘恢复。
   平台范围之外那个项目的项目级记录仍写着 `2ab9580`，而它指向的就是这个目录；该项目自己的设置文件没有被写入。
   合同里「旧缓存目录仍在磁盘上」的说法是错的，C3「不动它」只做到了不动记录，没有做到不动它加载的字节。
2. **`settings.json` 多写了一个键。** `claude plugin marketplace add` 在 `extraKnownMarketplaces` 下加了 `aisoft-platform`。
   合同对该文件只列了 `enabledPlugins`。写入由 CLI 完成。
3. **P2 的记录时点。** P2 在第一次写入之前已确定并读回，但写进本文档是在写入之后。
4. **清单哈希口径变了。** 插件缓存的树哈希现在排除 `.in_use` 与 `.git`，前者随会话启停变化，后者每次安装都是新的浅克隆。
   T01、T02 中的缓存哈希按旧口径取得，与之后的不可比。
5. **fresh session 留下了会话记录。** 六个 `claude -p` 进程在 `~/.claude/projects` 下各留一份记录，属于 Claude Code 自身的会话存档。

## PR 提交后的清理（2026-10-08）

PR #357 提交后，用户改变了 C3 的选择，并在自己的终端里执行了项目级卸载：
`claude plugin uninstall mattpocock-skills@claude-plugins-official --scope project`，在范围外项目的目录内运行，输出为成功。
本会话只做了读回：

- Matt 插件记录只剩一条：`mattpocock-skills@aisoft-platform`，user 作用域，1.3.1 / `24fe0ef…`。
- `check-plugin-pin.sh /Users/benque` 由 `PIN_DRIFT` 变为 **`PIN_CLEAN`**；`check-drift.sh` 仍为 `CLEAN`。
- 没有任何记录再指向 `cache/claude-plugins-official/mattpocock-skills/1.2.3`。该目录仍在磁盘上，已带 Claude Code 的
  `.orphaned_at` 标记，由它自行回收。上文「共享缓存被覆盖」的后果因此消除，但恢复方案当时没有覆盖它这一事实不变。
- 范围外项目的 `.claude/settings.json` 被 CLI 删掉一个键。该文件在那个仓库受 git 管理，改动留在其工作树中，未提交。
- Codex 受管清单与 Codex 插件清单不变。

## T05 Claude fresh session（2026-10-08）

详见 [t05-claude-session.md](evidence/t05-claude-session.md)。五个提示词各用一个新进程。

- 发现、显式来源、禁止隐式调用、边界规则在场四项为 PASS，有 harness 事件与模型回合两层证据。
- 新会话加载的 Matt 插件是 `cache/aisoft-platform/mattpocock-skills/1.3.1`，27 个技能，没有 `resolving-merge-conflicts`。
- `retro` 消歧为 GAP。Claude 侧没有 gstack，预期的两来源消歧不适用。但裸 `retro` 提示下，新会话没有确认就开始做回顾：
  它绕过 `disable-model-invocation`，直接读了直连 `mattpocock` marketplace 检出里的 SKILL.md。那份文本跟踪上游 main，
  不是固定在 `24fe0ef` 的那份。会话按合同被中止，没有写入任何文件。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T01 只读基线与安装预检 | PASS，仅只读 | 「T01 只读基线」节 |
| T02 Codex 受管安装、重复安装、回滚、恢复、再安装、漂移读回 | PASS，installed 层 | 「T02」节与 t02 证据 |
| T03 Codex harness 层技能列表 | PASS，harness 层，CLI 0.147.0 | t03 证据 |
| T03 Codex 模型回合 P1–P4 | GAP / NOT RUN | 三次 `codex exec` 失败；人工转述未执行 |
| T04 Claude 侧技能、marketplace 注册、插件切换、回滚演练 | PASS，installed 层，有五处与合同不符 | 「T04」节与 t04 证据 |
| T05 Claude fresh session P1、P2、P3、P5 | PASS，provider-session 层 | t05 证据 |
| T05 Claude fresh session P4 | GAP | 会话未确认即执行，来源为未固定的检出；已中止 |
| `check-change-documents`、`resolve-documents 354`、`py_compile inventory.py` | PASS，local 层 | 提交前运行 |
| `bash codex/tests/smoke.sh` | PASS，exit 0，local 层 | 在 `ea1171f` 上完整运行，无缩减参数；之后只有本文档这一行的回填 |
| push / PR / required CI / merge | NOT RUN | 等确认点 2 |

## 分层结果

| 层 | 对象 | 结果 |
|---|---|---|
| source | 平台 pin `8162fe7…` 与 P2 `b356085…`；上游 v1.3.1 / `24fe0ef…` | 已读回，本票不改 source |
| local | 文档 resolver 与审计 | PASS |
| CI | required CI | NOT RUN |
| installed · Codex 受管快照 | `~/.agents`：current 为 v1.3.1，previous 为 v1.2.2，37 个入口 | PASS |
| installed · Codex 独立插件 | `mattpocock-skills@claude-plugins-official` 1.2.3 / `c55ee46…`，已启用 | 按 C2 未改动；与受管 v1.3.1 并存 |
| installed · Claude 独立插件 | `mattpocock-skills@aisoft-platform` 1.3.1 / `24fe0ef…`，user 作用域，唯一一条 Matt 记录 | PASS；pin 检查为 `PIN_CLEAN` |
| installed · Claude 平台技能 | `~/.claude/skills` 两个技能，P2 | `CLEAN` |
| provider-session · Codex | 模型回合 | GAP / NOT RUN；仅 harness 层 |
| provider-session · Claude | 五个新进程 | 四项 PASS，`retro` 一项 GAP |
| live / VM | gitea-ci | 不在目标内 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | T01 基线与路径清单；S0 与阶段二的执行前重读；P2 记录时点见「与合同不符之处」3 |
| AC-2 | PARTIAL | 阶段一：备份完整，恢复在真实目标上执行并读回基线。阶段二：三个文件与技能目录已备份，但共享的 1.2.3 缓存目录未备份且被覆盖，恢复方案没有覆盖它。该目录在 PR 提交后已无记录引用 |
| AC-3 | PASS | S2 断言全表、S3 前后相等、S7 与阶段二的漂移读回 |
| AC-4 | PASS | 受管快照 N-1 往返；Claude 插件 N-1 往返。插件的 N-1 是官方当前 pin `c55ee46`，不是变更前记录的 `2ab9580` |
| AC-5 | PARTIAL | Claude：四项 PASS，`retro` 为 GAP。Codex：harness 层 PASS，模型回合 GAP / NOT RUN |
| AC-6 | PASS | 上表分层；受管安装、Codex 插件、Claude 插件分行报告 |

## 遗留风险与未完成项

- 范围外项目的项目级插件记录已由用户卸载。它的 `.claude/settings.json` 有一处未提交的改动，孤立的 1.2.3 缓存目录等待 Claude Code 回收。
- 直连 `mattpocock` marketplace 检出提供了一份未固定、可被直接读到的 Matt 技能文本，P4 中被实际读取。本票未动它。
- Codex 模型回合缺失。补法是由人在新开的 Codex 会话里发送固定提示词并回传；不回传则保持 GAP。
- Codex 独立插件 1.2.3 与受管 v1.3.1 并存，退役的 `resolving-merge-conflicts` 仍经插件可见。按 C2 不处置。
- `retro` 的 `disable-model-invocation` 挡不住模型直接读 SKILL.md。平台边界规则只有在 `aisoft-platform` 技能被加载时才进入上下文。
- 主机残留：两个备份目录按合同保留；安装源 worktree `/private/tmp/aisoft-354-install-source` 在收尾时移除。
- marketplace 按目录注册在主 checkout 上。主 checkout 切到没有 `.claude-plugin/marketplace.json` 的提交时，Claude Code 会报 marketplace 读取失败；已装插件不受影响。
- gitea-ci VM 不在本票目标内。`check-installed-drift` 其余六个安装面的 GAP 与本票无关。
