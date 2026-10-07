---
issue: 355
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/355
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - external-contract
depends_on: []
status: local-verified
branch: change/355-claude-skill-pack-align
created: 2026-10-08
updated: 2026-10-08
---

# Verification · Claude 侧外部技能包对齐

## 基线与范围

- Commit SHA: 实现 commit `f400f6c`（T01）、`bf0cf0e`（T02）、`066ede9`（T03 导航）、`ebcb301`（T04），
  合同修订 `56460bb`。全量 smoke 在 `56460bb` 上执行；本记录在其后提交，只改本文件，最终 head 见提交确认候选
- 基线：`origin/main` = `8162fe7d71dd58b13ca80ef26467a2549973f4df`（2026-10-08 经 broker `git.fetch.main` 读回）
- 环境: Mac 交互会话，macOS bash 3.2.57、Python 3.14.4、Claude Code 2.1.228；另在本地容器
  `python:3.12-bookworm`（bash 5.2.15、Python 3.12.15，无网络）复跑 pin 测试
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-8
- 范围追加：合同确认后用户追加「升级后的适配检查清单」（AC-8）。来源会话转达后，本会话向用户再次确认，
  用户选择并入本票、正文写在 08 §5 并在两侧平台技能各加一个入口；随后经 broker `gitea.issue.update`
  把范围第 4 项与 AC-8 写入 Issue 正文并读回（标题与标签未变）

证据分层：下文每条结论只属于它标注的那一层。**source / local** 是本会话真实执行的；**CI** 要等 PR 建出后
由 required CI 给出，本记录写作时为 NOT RUN；**installed / provider-session** 全部属于 #354，NOT RUN。

### 改动前基线（2026-10-08，本机只读）

| 观测 | 结果 |
|---|---|
| `codex/vendor/mattpocock/v1.3.1/manifest.json` 的 `commit` | `24fe0ef7737efae15c87225755e9f6f5965e4888` |
| 官方 marketplace 的 `mattpocock-skills` 条目 `sha` | `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` |
| 本机 `installed_plugins.json` 的 Matt 记录 | `mattpocock-skills@claude-plugins-official`，user 与 project 两条，版本 `1.2.3`，`gitCommitSha` `2ab958093e83e0ec752e6c1c5932da465bf23e0c` |
| 上游 pin commit 的 `.claude-plugin/plugin.json` 版本（公开读取） | `1.3.1` |
| `claude plugin list --json` 是否暴露 commit | 否，仅 `id`、`version`、`scope`、`enabled` 与时间戳 |
| `skill-for-claude/` 中以 `$` 开头的技能名 | `$triage`、`$to-spec`、`$to-tickets`、`$implement`、`$aisoft-matt-workflow`；末项不在 vendor manifest 技能集合内 |
| 仓库内 `docs/superpowers/`、`.superpowers/` | 均不存在；`.gitignore` 无对应条目 |
| `bash codex/tests/smoke.sh`（`8162fe7`，未改动） | PASS，exit 0，末行 `Codex platform static smoke checks passed.` |

官方 marketplace 的 pin 与本机已装记录的 commit 不同，而两者的插件版本同为 `1.2.3`。这是 pin 检查以
commit 为主键的直接依据。

## 执行结果

| Command / check | 层 | Result | Evidence |
|---|---|---|---|
| `bash skill-for-claude/check-plugin-pin.sh --source-only` | source | PASS | `PIN_SOURCE_OK`；`expected: mattpocock-skills@aisoft-platform ref=v1.3.1 commit=24fe0ef7737efae15c87225755e9f6f5965e4888`；exit 0 |
| `claude plugin validate .` | local | PASS | `Validating marketplace manifest: …/.claude-plugin/marketplace.json`；`✔ Validation passed`；exit 0 |
| `claude plugin validate --strict .` | local | PASS | exit 0（告警按错误处理时仍通过，条目无未知字段） |
| `bash codex/tests/test-claude-plugin-pin.sh` | source | PASS | `PASS: test-claude-plugin-pin`；exit 0 |
| 同一测试在 `python:3.12-bookworm` 容器内（`--network none`，工作树只读挂载） | local | PASS | bash 5.2.15、Python 3.12.15；`PASS: test-claude-plugin-pin`；exit 0 |
| pin 测试的反向证明：在暂存副本里逐一改掉检查器的 6 处判定后重跑测试 | local | PASS | 6 处全部变红，见下「反向证明」 |
| `bash skill-for-claude/install.sh <隔离 HOME>` 后 `bash skill-for-claude/check-drift.sh <隔离 HOME>` | local | PASS | `Claude skills installed … aisoft-platform issue-session-flow`；`Pruned 0 stale entries`；读回 `CLEAN`，exit 0；装出的 `aisoft-platform/SKILL.md` 含「外部技能包边界」 |
| `bash skill-for-claude/check-plugin-pin.sh <隔离 HOME>` | local | PASS | `PIN_NOT_INSTALLED`，exit 0 |
| `bash skill-for-claude/check-plugin-pin.sh`（本机真实 HOME，只读） | local | 如实非 CLEAN | `PIN_DRIFT`，两条 `DRIFT: mattpocock-skills@claude-plugins-official … version=1.2.3 commit=2ab958093e83e0ec752e6c1c5932da465bf23e0c expected=24fe0ef7737efae15c87225755e9f6f5965e4888`；exit 1。这是 #354 执行前的期望读数，不是本票的失败 |
| `bash codex/tests/test-install-claude-skills.sh` | source | PASS | `claude skill install tests passed` |
| `bash codex/tools/check-installed-drift.sh --source-only` | source | PASS | `SOURCE PASS: skill-for-claude/install {"references": {"expected": 3}, "skills": {"expected": 2}}`；`RESULT PASS`——八安装面的映射与计数未变 |
| smoke 三组守卫的反向证明：把已提交的守卫段原样抽出，对 12 份暂存副本运行 | local | PASS | 未改动副本通过，11 份反例全部变红，见下「反向证明」 |
| `bash -n` 与 `shellcheck`：`skill-for-claude/check-plugin-pin.sh`、`codex/tests/test-claude-plugin-pin.sh` | source | PASS | 均无输出，exit 0；`bash -n codex/tests/smoke.sh` 通过 |
| `git diff --stat origin/main -- codex/vendor codex/skills codex/install-skills.sh AGENTS.md skill-for-claude/skills.manifest skill-for-claude/install.sh skill-for-claude/check-drift.sh codex/tools` | source | PASS | 输出 0 行：上游原文、Codex adapter、Codex 安装器、`AGENTS.md` 与既有检查零 diff |
| `python3 -m aisoft_loop.cli resolve-documents 355 --repo .` | source | PASS | 返回四个角色到本目录四个文件的映射 |
| `python3 -m aisoft_loop.cli check-change-documents --repo .` | source | PASS | `result: changes=162 pass=2 gap=0` |
| `bash codex/tests/smoke.sh`（`066ede9`，T04 之前，全量，工作树清洁） | source | PASS | exit 0；末行 `Codex platform static smoke checks passed.`；日志含 `PIN_SOURCE_OK` 与 `PASS: test-claude-plugin-pin` |
| `bash codex/tests/smoke.sh`（`56460bb`，含 T04，全量，工作树清洁） | source | PASS | exit 0；末行 `Codex platform static smoke checks passed.`；日志含 `PIN_SOURCE_OK` 与 `PASS: test-claude-plugin-pin`；运行前后 `git status --short` 为空，head 未变 |
| AC-8 清单守卫的反向证明：已提交的 `#355` 守卫段整段抽出，对 9 份暂存副本运行 | local | PASS | 未改动副本通过，8 份反例全部变红，见下「反向证明」 |
| 下列快速检查在 `56460bb` 上重跑（pin source、pin 测试、`claude plugin validate` 及 `--strict`、隔离 HOME 安装与 `check-drift.sh`、隔离与真实 HOME 的 pin 读回、ShellCheck、零 diff 清单） | source / local | PASS | 结果与上表逐项相同；隔离 HOME 装出的 `aisoft-platform/SKILL.md` 含清单入口；真实 HOME 仍为 `PIN_DRIFT` |
| `codex/tools/apply-classification-labels.sh --verify 355`（`56460bb`） | live（Gitea 标签） | PASS | `"result":"projected"`，`change_type` `platform`，`complexity` `complex` |
| required CI（PR 建出后） | CI | NOT RUN | 确认点 2 之后才有 PR |

### 反向证明

**pin 检查器**——把检查器、条目、vendor manifest、安装器与测试拷到暂存目录，每次只改一处判定，再跑同一份测试：

| 改掉的判定 | 测试结果 |
|---|---|
| 不再把「来自其它 marketplace」算作漂移 | FAIL（other-marketplace 用例读出 `PIN_CLEAN`） |
| 不再校验 `installed_plugins.json` 的 schema 版本 | FAIL（schema-3 用例读出 `PIN_CLEAN`） |
| 不再比较条目 `sha` 与 vendor manifest `commit` | FAIL（改掉 `sha` 的 source 用例读出 `PIN_SOURCE_OK`） |
| 不再拒绝符号链接的安装记录 | FAIL |
| 不再拒绝重复键 | FAIL（duplicate-key 用例读出 `PIN_CLEAN`） |
| 不再比较条目 `ref` 与安装器 `matt_version` | FAIL（改掉安装器版本的 source 用例读出 `PIN_SOURCE_OK`） |

**smoke 守卫**——把 `smoke.sh` 中已提交的 `#355` 守卫段原样抽出为独立脚本，`ROOT` 指向暂存副本：

| 副本 | 结果 |
|---|---|
| 未改动 | 通过 |
| 把 `$aisoft-matt-workflow` 写回 Claude 技能 | 变红：`Claude 侧技能引用了无法解析的 $aisoft-matt-workflow（#355 AC-3）` |
| 去掉 Claude 技能里全部 `$` 技能引用 | 变红（守卫不空转） |
| 删除 Claude 侧 `pr` 规则的锚定短语 | 变红：`两侧 Matt 规则不再成对：不授予 push、PR、merge 或部署权限 ↔ …` |
| 把 Codex adapter 的 `writing orchestration is disabled` 改为 enabled | 变红 |
| 删除 Claude 侧 `retro` 的「不启动自主回顾循环」 | 变红 |
| 把 Claude 侧「定义冲突时停止」改为继续 | 变红 |
| 把 Claude 侧的 pin 换成官方 marketplace 的 commit | 变红 |
| 从 `.gitignore` 删除 `.superpowers/` | 变红 |
| 新建 `docs/superpowers/specs/` | 变红：`…不得落在 docs/superpowers/（#355 AC-4）` |
| 删除 superpowers 映射里的 `finishing-a-development-branch` | 变红 |
| 删除 `issue-session-flow` 里指向「外部技能包边界」的短句 | 变红 |

**AC-8 清单守卫**——同样的做法，副本另含 08 分册与 Codex 侧平台技能：

| 副本 | 结果 |
|---|---|
| 未改动 | 通过 |
| 删除检查项「调用方式」 | 变红，报出缺少的是第 2 项「调用方式」并标注 `#355 AC-8` |
| 删除检查项「Git / PR / 并行写入副作用」 | 变红 |
| 删除结论「明确禁用并写明边界」 | 变红 |
| 删除示例标题 `Matt 1.2.3 → 1.3.1` | 变红 |
| 删除示例标题 `superpowers 6.4.1 → 6.4.2` | 变红 |
| 删除小节标题 | 变红 |
| 删除 Claude 侧入口 | 变红：`平台技能缺少升级适配清单入口：…/skill-for-claude/aisoft-platform/SKILL.md` |
| 删除 Codex 侧入口 | 变红：`平台技能缺少升级适配清单入口：…/skill-for-codex/SKILL.md` |

这一组的首次运行 9 份副本全部通过：抽取脚本在第一个 `done` 处就截断，没有带上 AC-8 守卫段，是空转。
改为按守卫段的实际首尾抽取后重跑，得到上表。

「新建 `docs/superpowers/specs/`」一行的首次运行**没有**变红：macOS bash 3.2 的 `set -e` 不因 `[[ … ]]`
返回非零而退出，裸写的 `[[ ! -e "$ROOT/docs/superpowers" ]]` 在本机是静默失效的守卫。已改为显式
`if … exit 1`，上表是改后在已提交守卫上重跑的结果。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS（source / local） | 条目存在且 `claude plugin validate` 通过；条目 `sha` 与 vendor manifest `commit` 逐字相同（`PIN_SOURCE_OK`）；`sha`、`ref`、manifest、安装器等 14 种不一致 fixture 均读出 `PIN_SOURCE_MISMATCH` 并非零退出；该检查与测试登记在 `smoke.sh` 的 `bash -n`、ShellCheck 与执行三处 |
| AC-2 | PASS（source / local） | fixture 覆盖一致、不一致（非 pin commit、非 pin marketplace、混装、commit 缺失）、缺失（无文件、仅其它插件、空记录）与 10 种不可识别输入；非 CLEAN 的首行分别为 `PIN_DRIFT`、`PIN_NOT_INSTALLED`、`PIN_UNREADABLE`；放进记录多余字段、路径字段、相邻插件、`settings.json` 与 `.credentials.json` 的凭据样式字符串不出现在输出中；后两个文件权限为 000 时仍读出 `PIN_CLEAN`，目标 HOME 运行前后文件清单相同 |
| AC-3 | PASS（source / local） | Claude 侧 `aisoft-platform` 技能含 `pr`、`implement-spec`、`retro`、domain 文档四条规则；可解析性守卫通过，并对写回 `$aisoft-matt-workflow` 的副本变红；隔离 HOME 安装后 `check-drift.sh` 读回 `CLEAN` |
| AC-4 | PASS（source） | Claude 侧技能含 superpowers 四行映射；`.gitignore` 含 `.superpowers/`；`codex/vendor` 零 diff；本票未写入任何已装插件目录 |
| AC-5 | PASS（source） | 两侧对照守卫通过并对 5 种单侧改动变红；逐条对照见下表 |
| AC-6 | PASS（source / local）；CI 为 NOT RUN | 全量 smoke 在 `56460bb` 通过；新增 shell 的 `bash -n` 与 ShellCheck 通过；`resolve-documents 355` 与 `check-change-documents` 通过；写入本记录之前 `git diff --stat origin/main` 为 15 个文件 1171 行新增、1 行删除，被删的一行是 Claude 技能里那句悬空引用，没有删除测试、弱化断言或 skip。required CI 待 PR 建出后给出 |
| AC-8 | PASS（source） | 08 §5 新增「外部技能包升级后的适配检查」：四项检查、三种结论、Matt 1.2.3 → 1.3.1 与 superpowers 6.4.1 → 6.4.2 两张已填写的四行表；`skill-for-claude/aisoft-platform/SKILL.md` 与 `skill-for-codex/SKILL.md` 各有一段入口；守卫通过并对 8 种删除变红；`git diff --stat origin/main` 中没有定时任务、自动版本检查或安装动作 |
| AC-7 | PASS | 本记录按层标注每条证据；installed / provider-session 项全部列在「遗留风险与未完成项」并记 NOT RUN |

### AC-5 逐条对照

| 规则 | Codex adapter（`codex/skills/aisoft-matt-workflow/SKILL.md`） | Claude 侧（`skill-for-claude/aisoft-platform/SKILL.md`） | 语义 |
|---|---|---|---|
| pin | v1.3.1，`24fe0ef7737efae15c87225755e9f6f5965e4888`；来源为受管 `.agents` 快照或仓库内 vendor manifest | v1.3.1，同一 commit；来源为 `mattpocock-skills@aisoft-platform` | 一致；安装面不同，由各自的检查核对 |
| `pr` | Summary / Evidence / Merge Danger 候选正文；每条观察写明 SHA、命令或制品及所在层；缺 Before 明说；未执行为 `NOT RUN`；不授予 push、PR、merge、部署权限 | 同上各项；另写明正文服从 broker `gitea.pull.create` 正文合同 | 一致；Claude 侧多出的一句是 Issue 范围 2 的明文要求，不放宽任何约束 |
| `implement-spec` | 随快照存在，写入编排禁用；保持 Controller 单写者 frontier；不 reset、不合并子代理、不并行写、不提前 PR、不投影 ticket 状态；换编排需独立 complex 合同 | 逐项相同 | 一致 |
| `retro` | 仅明确要求 Matt 的 retro 时加载；可指定会话，否则当前会话；同名技能先确认来源，不覆盖不改名；只出有证据的候选供人审查；不改治理、不扩权、不启动自主循环 | 逐项相同（同名来源表述为「别的插件」，不点名） | 一致 |
| domain 文档 | 读 `docs/agents/domain.md`；新项目 `GLOSSARY.md` 与 `docs/adr/`；既有 `CONTEXT.md` / `CONTEXT-MAP.md` 并读至各项有着落；定义冲突停止迁移，不自动改名或丢弃 | 逐项相同 | 一致 |

Codex adapter 有三处内容没有对应的 Claude 规则，属于安装面与工具差异，不是约束差异：读取受管快照
manifest 的路径；`codex/install-skills.sh --rollback`；以及 provider 没有 Skill 工具时直接读取
`writing-for-agents` 的回退。Claude 侧对应前两者的是 marketplace 条目与 `check-plugin-pin.sh`。
Codex adapter 的大型多 context 项目可加 `GLOSSARY-MAP.md` 一句，Claude 侧未复述；它是可选项，不是约束。

## 遗留风险与未完成项

属于 #354 的 installed / provider-session 层，本票不执行：

- 注册 `aisoft-platform` marketplace、把本机 Matt 插件切到固定来源并升级：NOT RUN
- 升级后对真实 HOME 读回 `PIN_CLEAN`：NOT RUN（当前真实读数为 `PIN_DRIFT`，如上）
- Claude 与 Codex fresh session 中 `pr` / `implement-spec` / `retro` 的实际发现与行为：NOT RUN
- 重装 Claude 侧平台技能使本机副本含新增的「外部技能包边界」：NOT RUN（合并后本机 `check-drift.sh`
  会读出 `DRIFT: aisoft-platform/SKILL.md` 与 `DRIFT: issue-session-flow/SKILL.md`，重装后恢复 `CLEAN`）
- superpowers 版本更新：NOT RUN（跟随官方 marketplace，本票不自建 pin）
- 重装 Codex 侧技能使本机副本含 `skill-for-codex/SKILL.md` 新增的清单入口：NOT RUN（合并后 Codex 侧
  `codex/check-drift.sh` 会读出漂移，重装后恢复）
- gitea-ci VM 上的任何核对：NOT RUN
- smoke 三组守卫在 Linux bash 5 下的执行：NOT RUN（本地容器没有 `jq`；由 required CI 覆盖）

示例两张表的依据层次不同：Matt 一张依据仓库内 vendored 的 `CHANGELOG.md`，可由 diff review 复核；
superpowers 一张依据 2026-10-08 对上游 `RELEASE-NOTES.md` 的公开读取，经摘要工具转述，未在仓库内留存原文。

本票已知而未处理的事项：

- `AGENTS.md` 的目录描述未提到 `.claude-plugin/` 与 `check-plugin-pin.sh`。本票禁止修改 `AGENTS.md`，
  导航由 README 与 08 §5 承担；同步须走独立治理步骤。
- `installed_plugins.json` 是 Claude Code 未公开承诺的内部文件。格式变化时检查读出 `PIN_UNREADABLE`，
  需要一次小变更跟进；不会误判 `PIN_CLEAN`。
- `origin/main` 的 `smoke.sh` 已有 17 处单行裸写的 `[[ … ]]` 断言，在 macOS bash 3.2 下同样不会让
  `set -e` 退出（实测 `/bin/bash -c 'set -euo pipefail; [[ 1 == 2 ]]; echo survived'` 返回 0；bash 5.2
  返回 1）。它们在 required CI 的 bash 5 下有效，只在本机失效。本票只修正自己新增的两处，未改既有断言。
- 规则是文本约束。确定性的硬门仍是 broker、Controller 与 required CI。
