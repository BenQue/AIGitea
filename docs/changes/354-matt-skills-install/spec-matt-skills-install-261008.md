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
status: approved
branch: change/354-matt-skills-install
created: 2026-10-08
updated: 2026-10-08
git_scope:
  - docs/changes/354-matt-skills-install/evidence/fresh-session-prompts.md
  - docs/changes/354-matt-skills-install/evidence/inventory.py
  - docs/changes/354-matt-skills-install/evidence/t01-baseline.json
  - docs/changes/354-matt-skills-install/evidence/t02-codex-managed-install.json
  - docs/changes/354-matt-skills-install/evidence/t03-codex-session.md
  - docs/changes/354-matt-skills-install/evidence/t04-claude-plugin.json
  - docs/changes/354-matt-skills-install/evidence/t05-claude-session.md
  - docs/changes/354-matt-skills-install/plan-matt-skills-install-261008.md
  - docs/changes/354-matt-skills-install/spec-matt-skills-install-261008.md
  - docs/changes/354-matt-skills-install/summary-matt-skills-install-261008.md
  - docs/changes/354-matt-skills-install/verification-matt-skills-install-261008.md
---

# #354 Matt skills 本机受控安装合同

## 目标与原因

把已合并的 Matt v1.3.1 装到当前 Mac，并证明它在两个 provider 的真实会话里按平台合同被发现和调用。
#352 只交付了源码；本机三个分发面都还是旧版本，`check-installed-drift` 的 install-skills 面为 GAP。

本合同只授权下文列出的路径与命令。合同之外的写入一律停止并报告。

## Acceptance criteria

沿用 Issue #354 的 AC-1 至 AC-6，下列为判定方式。

- [ ] **AC-1** 执行前记录上游 tag、平台 source pin、目标的链接、版本、受管文件哈希、属主与权限，
  并列出全部将写入的路径。判定：`evidence/t01-baseline.json` 与本文「目标路径清单」。
- [ ] **AC-2** 备份覆盖 8 个 adapter、全部受管入口与 Matt 快照元数据；恢复方案覆盖整个写入范围，
  不只依赖 `--rollback`。判定：备份清单逐文件哈希相等；恢复步骤在真实目标上执行过一次并读回基线。
- [ ] **AC-3** 安装后读回 pinned manifest、37 个技能及目录哈希、current/previous、权限、
  `resolving-merge-conflicts` 入口退役、无关文件不变；重复安装的前后清单逐项相等。
- [ ] **AC-4** 在真实目标上回到 N-1（v1.2.2）并读回，再回到 v1.3.1 并读回；前后证据完整保留。
- [ ] **AC-5** Codex 与 Claude 各自在真实 fresh session 中完成技能发现、显式来源、禁止隐式调用、
  `retro` 消歧四项检查。未执行或 provider 不支持的项记 GAP / NOT RUN，不用另一侧结果代替。
- [ ] **AC-6** verification 按 source / local / CI / installed / provider-session 分层；受管安装结果
  与两个独立插件的状态分开报告。

## 固定来源

| 对象 | 值 |
|---|---|
| 上游 release | v1.3.1，2026-10-08 `git ls-remote` 读回为最新 tag |
| tag object | `0b6cee10f260a2e048279cf737bfd3e37b1fce0b` |
| commit | `24fe0ef7737efae15c87225755e9f6f5965e4888` |
| 平台 source pin（阶段一） | `8162fe7d71dd58b13ca80ef26467a2549973f4df` |
| vendor 快照 | `codex/vendor/mattpocock/v1.3.1/`，37 个技能 |
| N-1 | `codex/vendor/mattpocock/v1.2.2/`，35 个技能 |

上游 main 已领先 v1.3.1，本票不追踪 main。开工时重新读回上游 tag：若出现高于 v1.3.1 的 release，
停止并报告版本差异，不改目标。

安装源是一个专用的只读 worktree：`/private/tmp/aisoft-354-install-source`，detached 在 pin 上。
它不与任何会话共享 HEAD，installer 打印的 commit 就是 pin。source guard 对 detached HEAD 会报
`staleness unchecked`；新鲜度由执行前的 broker `git.fetch.main` 读回补足。

## 阶段一：Codex 受管快照

命令：`bash codex/install-skills.sh /Users/benque`，从安装源 worktree 执行。不需要 sudo。

### 目标路径清单

| # | 路径 | 动作 |
|---|---|---|
| W1 | `~/.agents/`、`~/.agents/skills/` | `install -d`，现有权限 0700 / 0755 不变 |
| W2 | `~/.agents/skills/` 下 8 个 adapter 目录：`aisoft-matt-workflow`、`aisoft-platform`、`gitea-analyze-change`、`gitea-development-loop`、`gitea-implement-change`、`gitea-platform-ops`、`gitea-spec-plan`、`issue-session-flow` | 覆盖复制 18 个文件；基线时 4 个文件字节不同，无新增或删除 |
| W3 | `~/.agents/vendor/mattpocock/releases/v1.3.1/` | 新建，先写同级 `.v1.3.1.stage.*` 再改名 |
| W4 | `~/.agents/skills/implement-spec`、`pr`、`retro` | 新建指向 `../vendor/mattpocock/current/...` 的链接 |
| W5 | `~/.agents/skills/resolving-merge-conflicts` | 删除链接；它是上一受管 release 的入口 |
| W6 | `~/.agents/vendor/mattpocock/previous` | 新建，指向 `releases/v1.2.2` |
| W7 | `~/.agents/vendor/mattpocock/current` | 原子替换为 `releases/v1.3.1` |
| W8 | `~/.agents/backup-issue-354-<UTC 时间戳>/` | 本合同的备份目录，权限 0700 |

其余 34 个 Matt 入口的链接文本在两个版本间相同，installer 不重写。

不写入：`~/.agents/.skill-lock.json`、`skill-sources/`、`skills-unmanaged-backup-20260811/`、
`releases/v1.2.2/`，以及 `~/.agents/skills/` 下 117 个无关条目（含 `gstack/` 与 12 个 OpenSpec 链接）中的任何一个；
`~/.claude/` 与 `~/.codex/` 下的任何路径。

### 备份

安装前写入 W8：

- `adapters/<name>/`：8 个 adapter 目录的完整副本。
- `links.json`：`~/.agents/skills/` 下全部链接的名称与目标，以及 `current`、`previous`。
- `inventory.json`：`evidence/inventory.py` 的完整输出，含每个条目的属主、权限与树哈希。

`releases/v1.2.2/` 不复制：installer 不改写已有 release，它的树哈希记录在清单里，逐字节相同的副本在
仓库 `codex/vendor/mattpocock/v1.2.2/`。备份写完后逐文件比对哈希，不相等则不开始安装。
备份目录在本票结束后保留，由人决定何时删除。

### 执行序列

每一步之后运行清单脚本并断言，任何断言不成立即停止并进入「失败恢复」。

| 步 | 动作 | 断言 |
|---|---|---|
| S0 | broker `git.fetch.main`；建安装源 worktree；重读清单 | origin/main 等于 pin；链接、adapter、无关条目三个摘要与 `t01-baseline.json` 相等 |
| S1 | 写备份 | 备份与原件哈希相等 |
| S2 | 安装 | current 为 v1.3.1，previous 为 v1.2.2；v1.3.1 的 37/37 技能目录哈希等于 manifest 且整树等于 pin 源；入口恰为 manifest 的 37 个名称；`resolving-merge-conflicts` 不存在；8 个 adapter 与 pin 源 `diff -r` 无差异；无关条目摘要、lock 哈希、`v1.2.2` 树哈希不变；`~/.agents` 仍为 0700 |
| S3 | 再次安装 | 清单与 S2 逐项相等，previous 仍为 v1.2.2 |
| S4 | `--rollback` | current 为 v1.2.2，previous 为 v1.3.1；入口摘要等于基线 |
| S5 | 从备份恢复 8 个 adapter | adapter 摘要等于基线；整个写入范围除 `releases/v1.3.1/` 与 `previous` 外等于基线 |
| S6 | 第三次安装 | 清单与 S2 逐项相等 |
| S7 | `check-installed-drift` | install-skills 面为 PASS；其余安装面的结论与执行前相同 |

若 S0 发现 origin/main 已前进：受管源（`codex/skills`、`skill-for-codex`、`codex/vendor/mattpocock`、
`codex/install-skills.sh`、`codex/runtime/aisoft_loop/matt_snapshot.py`）相对 pin 无差异时仍按 pin 安装并记录；
有差异则停止，交回人重新确认 pin。

### 失败恢复

- installer 非零退出：它在切换 `current` 前失败时不改任何入口，切换中失败时自行恢复原链接。
  读回清单与基线比较，确认后停止并报告。
- 已切换后断言不成立：执行 `--rollback` 恢复 Matt 入口，再从备份恢复 adapter，读回基线。
- 恢复后可能残留 `releases/v1.3.1/`、`previous` 与 `.v1.3.1.stage.*`。它们不被 `current` 引用。
  删除目录在本会话受权限策略限制，命令交回人执行，残留如实记录。
- 同一根因失败三次即停止，不换路径绕过。

不在真实目标上做故意失败注入。失败路径的证据是 #352 在隔离 HOME 上的 9 个 installer 测试。

### Codex fresh session

在 S7 之后启动一个新的 Codex 会话，使用 `evidence/fresh-session-prompts.md` 中固定的提示词，
原样保存输出。四项检查：

| 检查 | 期望 |
|---|---|
| 发现 | 受管路径提供 manifest 的 37 个名称；不再提供 `resolving-merge-conflicts` |
| 显式来源 | `triage`、`pr`、`retro`、`implement-spec` 解析到 `releases/v1.3.1/` 下的 SKILL.md |
| 禁止隐式调用 | manifest 中 `disable_model_invocation` 为真的 22 个技能不在可隐式调用之列；`retro`、`implement-spec` 不被中性提示触发 |
| `retro` 消歧 | 裸 `retro` 请求下，会话指出 Matt 与 gstack 两个来源并等待指定，不擅自选择 |

先用 `codex exec` 以只读沙箱运行。本机 CLI 曾因模型不可用而失败；同一根因三次即停，改为把提示词
交给人在新的 Codex 会话中执行并回传，证据标注为人工转述。两条路都走不通则记 GAP / NOT RUN。
模型自述弱于 harness 日志，只有自述时该项记 PARTIAL。

### Codex 独立插件

`mattpocock-skills@claude-plugins-official` 在 Codex 中已安装并启用，版本 1.2.3，
commit `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`。

| 入口 | 命令或位置 |
|---|---|
| 更新 | `codex plugin marketplace upgrade` 后 `codex plugin add`；官方 marketplace 仍钉在 `c55ee46`，更新为 no-op |
| 备份 | `~/.codex/config.toml` 的插件段；`~/.codex/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3/` |
| 回滚 | `codex plugin remove` 后重新 `add`，或恢复 `config.toml` 的 `enabled` 值 |

阶段一不修改它，只在 fresh session 中记录它与受管 v1.3.1 的并存情况。

## 阶段二：Claude 侧

### 启动规则

阶段二的平台 pin 今天未知，由下列规则确定。全部成立才开始，任一不成立即停止并报告：

1. #355 已关闭，其 merge commit 是 broker fetch 后 origin/main 的祖先；该 origin/main 记为 P2。
2. P2 是阶段一 pin 的后代。
3. `codex/vendor/mattpocock/`、`codex/install-skills.sh`、`matt_snapshot.py` 在阶段一 pin 与 P2 之间无差异。
4. P2 上 `.claude-plugin/marketplace.json` 的 `mattpocock-skills` 条目 `sha` 等于上表 commit，
   `skill-for-claude/check-plugin-pin.sh --source-only` 输出 `PIN_SOURCE_OK`。
5. 上游 v1.3.1 仍解析到同一 commit。

P2 的 40 位 SHA 在任何写入前记入 verification。#355 合并后的交付物若与本节假设不符
（文件位置、marketplace 名称、检查工具的结论集合），按合同冲突处理，停止并报告。

### 目标路径清单

| # | 路径 | 动作 |
|---|---|---|
| X1 | `~/.claude/backup-issue-354-<UTC 时间戳>/` | 备份目录，权限 0700 |
| X2 | `~/.claude/skills/aisoft-platform/`、`~/.claude/skills/issue-session-flow/` | `skill-for-claude/install.sh /Users/benque`，装入 #355 的边界规则 |
| X3 | `~/.agents/skills/` 下 8 个 adapter | 仅当 P2 使 install-skills 面再次漂移时重跑 `install-skills.sh`；Matt 部分必须为 no-op |
| X4 | `~/.claude/plugins/known_marketplaces.json`、`~/.claude/plugins/marketplaces/` | `claude plugin marketplace add` 注册平台 marketplace |
| X5 | `~/.claude/plugins/installed_plugins.json`、`~/.claude/settings.json` 的 `enabledPlugins` | 只经 `claude plugin` CLI 写入 |
| X6 | `~/.claude/plugins/cache/<平台 marketplace>/mattpocock-skills/` | CLI 写入新版本缓存 |

marketplace 按目录注册，目录为 manifest 的 `mac_checkout`（`/Users/benque/MyDocs/AISoftPlatform`），
注册前断言其 HEAD 等于 P2 且工作树干净。这样不新增 broker 之外的 Gitea 访问路径。

不写入：`superpowers` 及其它插件的记录与缓存；名为 `mattpocock` 的直连 marketplace 条目；
其它项目的 `.claude/settings.json`；任何凭据文件。`settings.json` 不整份读入证据，只读两项插件键。

### 备份、步骤与回滚

备份：`installed_plugins.json`、`known_marketplaces.json`、`settings.json` 三个文件的副本，
以及两个平台技能目录的副本，写入 X1 并比对哈希。旧缓存目录的树哈希记入清单。

步骤：备份 → X2 → 需要时 X3 → `claude plugin validate` → 注册 marketplace → 卸载 user 作用域的
`mattpocock-skills@claude-plugins-official` → 安装 `mattpocock-skills@aisoft-platform` → 读回。

读回断言：记录的 `gitCommitSha` 等于上表 commit；缓存内 37 个技能目录的哈希逐一等于 vendor manifest；
`skill-for-claude/check-drift.sh` 为 `CLEAN`；`check-plugin-pin.sh /Users/benque` 的结论照实记录。

回滚演练：卸载平台来源的插件，重新安装官方来源，读回 1.2.3，再回到平台 pin 并读回。
CLI 回滚得到官方 marketplace 当前 pin `c55ee46`，而安装前记录是 `2ab958093e83e0ec752e6c1c5932da465bf23e0c`。
逐字节回到安装前状态的办法是恢复 X1 中的三个文件；旧缓存目录仍在磁盘上。该恢复只在失败时执行。

### Claude fresh session

用 `claude -p` 在平台仓目录启动新进程，使用同一份固定提示词，原样保存输出。检查项与 Codex 侧相同，
来源期望改为平台 marketplace 的 1.3.1 缓存；另加一项：新会话能给出已安装 `aisoft-platform` 技能中
`pr`、`implement-spec`、`retro` 的边界规则。Claude 侧若没有 gstack 的 `retro`，消歧项记为不适用并附
不存在的证据。

安装 X2 会改变本会话正在遵循的技能文本。安装后本会话只记录证据，不依据新文本改变做法；
新规则的验证由上述新进程完成。

## 待确认的选择

三项都有默认值。2026-10-08 人在确认点 1 三项均选定默认值。

| # | 选择 | 默认 | 另一选项及后果 |
|---|---|---|---|
| C1 | 执行节奏 | 分两阶段：现在做阶段一，#355 合并后做阶段二，最后一个 PR | 等 #355 合并后一次完成：只跑一轮，但此前 Codex 侧停在 v1.2.2，漂移 GAP 保留 |
| C2 | Codex 独立插件 1.2.3 | 不动，只报告并存情况 | 停用它（`enabled = false`）：去掉旧版同名技能，但改动人的全局 Codex 配置，影响所有项目 |
| C3 | 项目 `SAPWMOdataPDA` 的项目级 Claude 插件记录 | 不动；它不属于平台项目，`check-plugin-pin` 将保留一条 DRIFT，记为已知残留 | 一并迁移：pin 检查可到 `PIN_CLEAN`，但要改平台范围之外项目的配置 |

## 风险与回滚约束

- 全部写入都在 `$HOME` 下，不涉及 sudo、VM、服务、Secret、账号或权限。
- 每个阶段先备份再写入；恢复方案覆盖该阶段的整个写入范围。
- 仓库内改动只有本目录文档与证据，可直接 revert；revert 不会撤销主机上的安装。
- 安装结果只对当前 Mac 成立，不代表 gitea-ci VM 或其它主机。

## 非目标

不安装或升级 superpowers；不改 `AGENTS.md`、Controller、broker、main protection、required CI；
不改 installer、runtime 或 vendor 源码；不做 VM 安装；不处理 `check-installed-drift` 其余六个安装面的 GAP；
不删除或改写 gstack、旧 skills.sh lock、直连 `mattpocock` marketplace 或任何无关技能；
不更新 README 与 08 中的 as-built 表述；不合并 PR。

## 未决问题

除「待确认的选择」外无。
