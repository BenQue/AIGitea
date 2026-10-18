---
issue: 375
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/375
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - platform-governance
depends_on: []
status: approved
branch: change/375-skills-update
created: 2026-10-18
updated: 2026-10-18
git_scope:
  - docs/changes/375-skills-update/summary-skills-update-261018.md
  - docs/changes/375-skills-update/spec-skills-update-261018.md
  - docs/changes/375-skills-update/plan-skills-update-261018.md
  - docs/changes/375-skills-update/verification-skills-update-261018.md
  - 08-双工具共存与实施.md
  - skill-for-claude/aisoft-platform/SKILL.md
  - skill-for-codex/SKILL.md
  - codex/config/external-skill-adaptation.json
  - codex/config/project-leak-baseline.json
  - codex/tools/check-external-skill-versions.sh
  - codex/tools/check-external-skill-versions.py
  - codex/tests/test-external-skill-versions.sh
  - codex/tests/smoke.sh
  - docs/governance/remediation-roadmap.md
---

# #375 spec：技能更新（R5）

负责人于 2026-10-18 在项目线程“R5 技能更新”回复“确认”，批准本合同并启动实现。

## 目标与原因

ADR 0001 与整改路线 R5：外部技能包升级要先过 `08` §5 的适配检查，两个 provider 对等。现状是 Claude 侧 superpowers 已在 2026-10-17 随官方 marketplace 自动更新到 7.0.0，适配检查没有做；Codex 侧实际生效版本无人核实；本机已装的两侧平台技能落后于源；CLI 升级后没有重跑 provider 矩阵。人工“定期查看版本”也缺一个能一眼看清差距的只读工具。

## 已核对的事实（2026-10-18，本机，确认前取证）

- Claude 侧：`~/.claude/plugins/installed_plugins.json` 记录 `superpowers@claude-plugins-official` 7.0.0，commit `bb92a77741419a4ab5f06e711a283343f1ada0c3`，最后更新 2026-10-17。`08` §5 最近一次适配示例是 6.4.1 → 6.4.2。
- Codex 侧：`~/.codex/config.toml` 启用的是 `superpowers@openai-curated`，但 `[marketplaces]` 表里没有 `openai-curated`；该缓存目录里是 5.1.3，另有未启用的 `openai-curated-remote` 6.4.2 缓存。`codex debug prompt-input` 的模型可见技能列表里没有任何 superpowers 技能，技能根目录也不含这两个 marketplace。结论：Codex 侧 superpowers 当前**未生效**。
- CLI：Claude Code 2.1.228，codex-cli 0.161.0。
- 已装平台技能漂移：`check-installed-drift.sh` 报 `install-skills` 5 个文件、`skill-for-claude/install` 4 个文件 bytes-differ；Matt 插件 `PIN_CLEAN`。

## superpowers 6.4.2 → 7.0.0 适配核对（依据上游 `RELEASE-NOTES.md` v7.0.0 一节与已装 7.0.0 的技能正文）

| # | 上游变化 | 结论 | 处置 |
|---|---|---|---|
| 1 | 无技能增删（两版都是同样 15 个技能）；brainstorming 内部的 spec 文档审查提示换成 builder check 提示 | 无影响 | - |
| 2 | brainstorming 先理解需求再定级：快速清楚的任务“直接做”，小改动在聊天里确认后按常规流程做，项目写设计文档；用户跳过提问时硬闸门一起取消；用户同意的 spike 可以先做 | 需要更新 | 两侧平台技能写明：brainstorming 的定级与聊天内确认不替代平台判级与 `approved`；在平台项目内，写文件前仍要有 Issue、判级与确认点 1 |
| 3 | 设计文档仍写 `docs/superpowers/specs/` 并 commit；visual companion 仍用 `.superpowers/brainstorm/` | 无影响 | 既有落点映射不变 |
| 4 | builder check 派一个只读子代理审设计；`sdd-workspace` 不再覆盖仓库自带的 `.superpowers/sdd/.gitignore`；无新的 push、PR 或 merge 行为 | 无影响 | 只读子代理符合既有“只读调查可以并行”；`.superpowers/` 整体已在 `.gitignore` |

## Acceptance criteria

- [ ] AC1 适配结论落地：`08` §5 增加“**superpowers 6.4.2 → 7.0.0**”示例表（内容同上）；`08` §5 与 Claude 侧 `aisoft-platform` 的 superpowers 映射表各增一行 brainstorming 定级规则；`skill-for-codex/SKILL.md` 在外部技能包段落写同义规则；smoke 钉住新示例标题与两侧成对短语。
- [ ] AC2 Codex 生效版本：上面“已核对的事实”中的 Codex 侧证据（启用键、marketplace 注册、缓存版本、模型可见列表）写入 verification。
- [ ] AC3 只读版本核对脚本 `codex/tools/check-external-skill-versions.sh [--home DIR] [--source-only]`：
  - 适配记录 `codex/config/external-skill-adaptation.json` 记最近一次完成适配核对的 superpowers 版本与 Issue（本票写 7.0.0 与 375）。它不是 pin，平台仍不约束 superpowers 安装版本。
  - 默认读 `$HOME`（或 `--home`）下 Claude 的 `installed_plugins.json` 与 Codex 的 `config.toml`、插件缓存，并运行 `claude --version`、`codex --version`（找不到记 `NOT_FOUND`）；Matt 状态复用 `skill-for-claude/check-plugin-pin.sh <home>` 的结果。
  - 输出每侧一行：superpowers 版本与适配版本相等为 `ADAPTED`，更新为 `REVIEW_NEEDED`，更旧为 `BEHIND`，未安装为 `NOT_INSTALLED`，Codex 启用键的 marketplace 未注册为 `NOT_LOADED`，读不懂为 `UNKNOWN`。最后一行 `RESULT PASS` 或 `RESULT REVIEW_NEEDED`；任一行（含 CLI 行）出现 `REVIEW_NEEDED`、`UNKNOWN` 或 Matt 非 `PIN_CLEAN` 时退出码 1；CLI 找不到只记 `NOT_FOUND`，不算失败，否则 0。
  - `--source-only` 只校验适配记录的结构，不读任何 home，供 CI 使用。
  - 脚本自身不安装、不联网、不写任何文件（与 `check-plugin-pin.sh` 同样设置 `PYTHONDONTWRITEBYTECODE`）。
  - 回归测试 `codex/tests/test-external-skill-versions.sh` 只用伪造的 home 与伪造的 CLI，覆盖全部状态、退出码、`--source-only`、读前后 home 字节不变；按 smoke 五处登记，smoke 只跑 `--source-only` 与该测试，从不读 CI 主机自己的 home。
  - `08` §5 适配检查一节写明脚本用途：人工查看版本时使用，平台不为它设定时任务。
- [ ] AC4 平台技能重装：合并后由负责人运行 `bash codex/install-skills.sh "$HOME"` 与 `bash skill-for-claude/install.sh "$HOME"`，`check-installed-drift.sh` 读回 `install-skills` 与 `skill-for-claude/install` 两段 PASS，并运行一次新脚本；结果补记到 verification。PR 内这两项记 NOT RUN。
- [ ] AC5 provider 矩阵：本机运行 `08` §7 第 1–2 层（技能静态校验与合成 Issue 合同测试，均在全量 smoke 内）并记录 CLI 版本；第 3–9 层需要 VM 真实 pilot 与启用 provider（`IMPLEMENT_PROVIDER` 仍为 `none`），记 NOT RUN 并写明原因。
- [ ] AC6 路线文档：R4 行改为已完成（#373，PR 374，`c3d49ed`）；R5 行写本票状态。
- [ ] AC7 macOS 全量 `bash codex/tests/smoke.sh` 通过；`python3 -B codex/tests/check-project-leak.py` 不新增命中。

## 接口、数据与兼容性影响

新增一个只读工具与一份配置；不改 broker、runtime、manifest、installer。两侧平台技能各加一条规则，已装技能在负责人重装前保持旧内容。

## 风险与回滚约束

脚本依赖 Claude Code 与 Codex 本机文件格式，格式不认识时报 `UNKNOWN` 并退出 1，不会误报通过。回滚：revert 本 PR 后两侧重装技能。

## 非目标

- 不升级或启用 Codex 侧 superpowers：那是负责人的本机插件配置。verification 给出事实与可选做法，由负责人决定。
- 不给 superpowers 设 pin，不设定时检查，不自动安装。
- 不跑 VM 上的 provider 真实 pilot。

## 未决问题

无。
