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
status: pending
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

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T01 只读基线与安装预检 | PASS，仅只读 | 上节 |
| T02 备份、安装、重复安装、回滚、恢复、再安装 | NOT RUN | 等确认点 1 |
| T03 Codex fresh session | NOT RUN | 等 T02 |
| T04 Claude 侧技能与插件切换、回滚演练 | NOT RUN | 等 #355 合并 |
| T05 Claude fresh session | NOT RUN | 等 T04 |
| push / PR / required CI / merge | NOT RUN | 等确认点 2 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PARTIAL | 基线与路径清单已记录；S0 的执行前重读未运行 |
| AC-2 | NOT RUN | 备份与恢复未执行 |
| AC-3 | NOT RUN | 未安装 |
| AC-4 | NOT RUN | 未回滚 |
| AC-5 | NOT RUN | 两侧 fresh session 未运行 |
| AC-6 | NOT RUN | 分层结果表待执行后填写 |

## 遗留风险与未完成项

- 主机上尚无任何安装动作。
- gitea-ci VM 不在本票目标内，本记录不对它作任何结论。
- `check-installed-drift` 其余六个安装面的 GAP 与本票无关，原样保留。
