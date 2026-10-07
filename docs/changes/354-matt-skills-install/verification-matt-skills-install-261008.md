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

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T01 只读基线与安装预检 | PASS，仅只读 | 「T01 只读基线」节 |
| T02 备份、安装、重复安装、回滚、恢复、再安装、漂移读回 | PASS，installed 层 | 「T02」节与 t02 证据 |
| T03 Codex harness 层技能列表 | PASS，harness 层，CLI 0.147.0 | t03 证据 |
| T03 Codex 模型回合 P1–P4 | GAP / NOT RUN | 三次 `codex exec` 失败；人工转述未执行 |
| T04 Claude 侧技能与插件切换、回滚演练 | NOT RUN | 等 #355 合并 |
| T05 Claude fresh session | NOT RUN | 等 T04 |
| push / PR / required CI / merge | NOT RUN | 等确认点 2 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS（阶段一） | 基线、路径清单、S0 执行前重读；阶段二的 P2 尚未确定 |
| AC-2 | PASS（阶段一） | S1 备份比对；S4 加 S5 在真实目标上恢复整个写入范围并读回基线；阶段二备份未执行 |
| AC-3 | PASS | S2 断言全表、S3 前后相等、S7 漂移读回 |
| AC-4 | PARTIAL | 受管快照的 N-1 往返已证明；Claude 插件的回滚演练未执行 |
| AC-5 | PARTIAL | Codex 仅有 harness 层证据，模型回合 GAP / NOT RUN；Claude 侧 NOT RUN |
| AC-6 | PARTIAL | 受管安装与 Codex 插件已分开报告；Claude 插件待阶段二 |

## 遗留风险与未完成项

- 阶段二全部未执行，前置是 #355 合并。
- Codex 模型回合缺失。补法是由人在新开的 Codex 会话里发送固定提示词并回传；不回传则该项保持 GAP。
- Codex 独立插件 1.2.3 与受管 v1.3.1 并存，退役的 `resolving-merge-conflicts` 仍经插件可见。按 C2 不处置。
- 主机残留：`~/.agents/backup-issue-354-20261007T234458Z/` 按合同保留；安装源 worktree
  `/private/tmp/aisoft-354-install-source` 在阶段二结束后移除。
- gitea-ci VM 不在本票目标内，本记录不对它作任何结论。
- `check-installed-drift` 其余六个安装面的 GAP 与本票无关，原样保留。
