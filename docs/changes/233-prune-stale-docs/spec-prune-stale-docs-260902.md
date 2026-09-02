---
issue: 233
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/233
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on:
  - 231
  - 232
status: approved
branch: change/233-prune-stale-docs
created: 2026-09-02
updated: 2026-09-03
---

# Spec · 清除过时文档与概念

## 目标与原因

让平台仓的活文档（排除 `archive/`、`docs/changes/`、`codex/vendor/`）只描述当前合同：删除已兑现的
接入条件、退役身份的迁移期段落，把 Codex-first 章节改为 provider 中性表述，把只剩历史意义的状态
条目迁入 `archive/`，并对 #232 留下的两项（12–15 与 02 正文去留、smoke 守卫是否扩到 references）
给出判定。全部改写保持合同语义等价。

本 spec 把 Issue #233 正文的 5 条验收标准落成可观察结果，并按验收第 1 条先给出逐条清单；Issue
正文是合同源，本文不扩张。行号以 `origin/main` = `0df92177497c1b4b16d9ed0c0bc5780849d7e7fb` 为准。

## 术语

- **活文档**：仓库内除 `archive/`、`docs/changes/`、`codex/vendor/`、`.git/` 之外的全部文件。
- **治理集**：#231 定义的 7 份治理文件（`smoke.sh` 中 `governance_set`）。本 Issue 改动其中的
  `skill-for-codex/SKILL.md`。
- **五类合同**：Issue 验收第 5 条点名的判级规则、命名元组、单闸门、broker 路径、routine merge 条件。
- **处置**：`删除` / `迁 archive` / `改为现在时` / `改为中性`（provider 等价措辞）/ `保留`。

## 逐条清单（验收第 1 条）

### A · Codex-first 与 provider 先后顺序

| # | 文件:行 | 现状 | 处置 | 语义对照 |
|---|---|---|---|---|
| A-01 | `08-Codex双工具共存与实施.md`（文件名） | 文件名以 Codex 为中心 | `git mv` → `08-双工具共存与实施.md`；同步 `README.md:164`、`AGENTS.md:38`、`09…md:510`、`archive/11-Codex-Loop运行时实施计划.md:5`（只改链接目标）；`archive/10` 与 `docs/changes/` 中的代码跨度是历史文本，不改 | 内容不变，只改名与链接 |
| A-02 | `08:3` | `更新：2026-08-26` | 改为 `2026-09-03`，状态句保留 | 无合同语义 |
| A-03 | `08:14–15` | `Codex adapter（先实现和验证）` / `Claude adapter（后接入）` | 改为中性：两行各去括注，图下加一行「两个 adapter 等价、可互换，由 `IMPLEMENT_PROVIDER` 显式选择」 | provider 选择规则不变（`09` §13.1 决策 1） |
| A-04 | `08:48–84` §4「现有 Codex 基础」 | Codex 试点历史叙事 + Claude adapter 事后补记 | 标题改「当前 provider 基础」；`50–56`（Codex CLI/auth/sandbox 清单）与 `66–72`（Issue #8/PR #9 试点、`bb0d5d5`、installer smoke）迁 archive；`58–64` 与 `74–80` 合并为「两个 adapter 共用的 source baseline」现在时清单；`82`「仍未完成」与 `84` 启用边界保留 | 启用边界与默认 `none` 不变 |
| A-05 | `08:119`、`08:131` | `## 7. Codex 验证矩阵`；`Codex 无权部署生产` | 改为中性：`## 7. Provider 验证矩阵`；`provider 无权部署生产` | 生产边界不变 |
| A-06 | `08:145` | 「这些是 Issue #8 runtime 实现前必须新增并先看到失败的 classifier 合同测试；本次文档更新不代表 VM wrapper 已支持这些 case」 | 改为现在时：「这些 case 由 `codex/runtime/tests`（`test_classification.py` 等）固化」；证据：该文件含 `override_reason`/`needs-human-decision` 用例 | 判级 case 表本身不改 |
| A-07 | `08:147–155` §8「Claude Code 接入条件」 | 已兑现的前置条件（Issue #1） | 删除整节；§9/§10 顺延为 §8/§9（全仓无 `08 §9`/`08 §10` 引用，`09` §13.2 引用的 `08 §7` 不受影响） | 接入条件已由 `04` §2 表「Claude adapter 已在中央 source」陈述 |
| A-08 | `08:165` | 「在 Loop 验证完成前保持 `IMPLEMENT_PROVIDER=none`」 | 改为现在时：「默认 `IMPLEMENT_PROVIDER=none`；启用是每项目独立验收门」 | 与根 `AGENTS.md`「`IMPLEMENT_PROVIDER=none` 是默认值」一致 |
| A-09 | `08:167` | 「Codex 不可用时不自动切换 Claude 执行同一 active Issue；先结束或转移状态，再显式选择 provider」 | 改为中性：「任一 provider 不可用时不自动切换到另一 provider 执行同一 active Issue；先结束或转移状态，再显式选择 provider」 | 无自动回退规则不变 |
| A-10 | `08:168` | 「不删除现有 Claude/Codex 认证、旧脚本或 skills，直到两个 provider 完成 parity 验证并另行批准清理」 | 改为现在时：「删除任一 provider 的认证、脚本或 skills 须另行批准；两者配置独立保存（§3）」 | 与根 `AGENTS.md`「新增一个提供者时不得破坏或删除另一个」一致 |
| A-11 | `04:37–38` | `Codex adapter（先验证）` / `Claude adapter（Codex 验证后）` | 改为中性：去括注，图下加同 A-03 的一句 | 同 A-03 |
| A-12 | `04:147`、`04:156` | `## 10. Codex-first 验证顺序`；第 8 条「共享 Codex runtime 与 profile 隔离验证通过后接 Claude adapter，并用同一通用矩阵做 parity；项目级 enablement 仍是独立门禁」 | 改为中性：`## 10. Provider 验证矩阵`；第 8 条「两个 provider 用同一通用矩阵做 parity 验证；项目级 enablement 仍是独立门禁」 | 独立门禁不变 |
| A-13 | `README.md:164` | `[08-Codex-first 与双工具共存](08-Codex双工具共存与实施.md) \| 共享 controller、Codex 验证矩阵、Claude parity 条件` | 改为 `[08-双工具共存与实施](08-双工具共存与实施.md) \| 共享契约、controller/adapter、provider 验证矩阵、部署边界与回滚 \| 接入或切换 provider` | 导航行 |
| A-14 | `AGENTS.md:38` | `08-Codex双工具共存与实施.md`：Codex 方案、实施步骤与验收状态 | 改为 `08-双工具共存与实施.md`：Claude Code 与 Codex 共存的共享契约、provider 验证矩阵与部署边界（目录段，独立 commit） | 目录描述 |
| A-15 | `09…md:510` | 表格首列旧文件名 | 同步新文件名 | 历史矩阵表，只改名 |

### B · 退役身份与已兑现条件句

| # | 文件:行 | 现状 | 处置 | 语义对照 |
|---|---|---|---|---|
| B-01 | `skill-for-codex/SKILL.md:26` | 「After AISoftPlatform Issue #35 is merged and its live rollout is explicitly authorized, every local Gitea software repository must first exist…」 | 改为现在时：「Every local Gitea software repository must first exist in the strict … manifest (the Issue #35 governance contract is live).」 | manifest 先行规则不变 |
| B-02 | `skill-for-codex/SKILL.md:44–65` | fixed `ci-bot` gate 代码块与两段迁移期说明 | 删除；替换为一句：shared `ci-bot` gate is retired；`ensure-gitea-collaborator.sh` remains only as historical compatibility/regression evidence；see `06`「旧 `ci-bot` gate（已退役）」 | 与 `06` §「旧 ci-bot gate（已退役）」一致 |
| B-03 | `skill-for-codex/SKILL.md:67–70` | 「Do not use either mutation path as an inspection shortcut…Retire `ci-bot` only after…」 | 「either mutation path」→「the mutation path」；「Retire `ci-bot` only after…」句删除 | 检查快捷方式禁令不变 |
| B-04 | `skill-for-codex/SKILL.md:79` | 「After Issue #35 live rollout, use the independent platform-manager audit PAT…」 | 改为现在时：去「After Issue #35 live rollout,」 | audit PAT 规则不变 |
| B-05 | `skill-for-codex/references/onboarding-runbook.md:3` | 「rsdesign-new 只是历史试点证据，不是默认仓库、目录、端口或部署合同」 | 改为中性：「历史试点不是默认仓库、目录、端口或部署合同」（去项目名，配合 G-01） | 语义不变 |
| B-06 | `onboarding-runbook.md:19` | 「Issue #35 发布后，按顺序执行：」 | 改为现在时：「按顺序执行（治理合同来自 Issue #35，已 live）：」 | 步骤不变 |
| B-07 | `onboarding-runbook.md:43`、`:45` | 「Issue #61/#70 发布后，已在 host-access manifest 中的项目从 fixed broker 访问 host」；「Issue #73 candidate 允许项目在 manifest 中声明 strict `git_remote_name`」 | 改为现在时：「已在 host-access manifest 中的项目从 fixed broker 访问 host（#61/#70）」；「manifest 允许项目声明 strict `git_remote_name`（#73）」 | broker 路径与 remote name 规则不变 |
| B-08 | `onboarding-runbook.md:97–126` §1.2「Legacy `ci-bot` collaborator gate（迁移期）」 | 整节迁移期指令 | 替换为 `### 1.2 共享 ci-bot gate（已退役）` 三句：已退出全部 manifest 仓库；`ensure-gitea-collaborator.sh` 只保留为历史兼容/回归测试，不得用于接入、回补或作 broker fallback；历史对象见 `06`。保留 `ensure-gitea-collaborator.sh` 字面量供 `smoke.sh:448` | 与 `06` 一致 |
| B-09 | `onboarding-runbook.md:258` | 「§1.2 `ci-bot` 只服务尚未迁移的已有 profile。」 | 删除该句 | 治理 gate 段其余不变 |
| B-10 | `skill-for-codex/references/private-gitea-access.md:10` | 「a declared value such as NewEmaint's `gitea`」 | 改为中性：「a declared value such as `gitea`」 | 规则不变 |
| B-11 | `codex/skills/gitea-platform-ops/SKILL.md:21`、`:23` | 第 8 条「After Issue #35 is merged and live reconciliation is authorized, use…」；第 10 条「Keep fixed `ensure-gitea-collaborator.sh` (`ci-bot` + Write) only for already-onboarded profiles during migration…Run `gitea-governance.sh retire-shared-bot`…」 | 第 8 条改现在时；第 10 条改为：shared `ci-bot` gate retired；`ensure-gitea-collaborator.sh` 仅历史兼容/回归证据；`gitea-governance.sh retire-shared-bot` 仍是逐仓库幂等退役操作，全部 manifest 仓库已完成（见 `06`）。保留 `retire-shared-bot` 字面量供 `smoke.sh:459` | 与 `06` 一致 |
| B-12 | `04:160` | 「controller 使用专用 `coder` 用户和最小权限 ci-bot。」 | 改为现在时：「controller 使用专用 `coder` 用户；Gitea 身份是 manifest-declared project agent，经 broker typed 操作使用最小权限。」 | 与 `01` 账号表、`06` §1.0 一致 |
| B-13 | `06:70`、`:196`、`:232`、`:399` | 「不再是发布后的 profile contract」；「Issue #61 发布后优先使用 §1.0 broker」；「Issue #35 发布后的唯一目标合同是」；「Issue #35 发布后，对 manifest 中明确的单个仓库运行」 | 改为现在时：去「发布后」，Issue 号改为括注 | 访问顺序、治理合同、收尾步骤不变 |
| B-14 | `codex/tests/smoke.sh:465–466` | 断言 `skill-for-codex/SKILL.md` 含 `AISOFT_ONBOARDING_MODE=software-repository` | 删除（断言对象是 B-02 删除的退役 gate 块） | 测试变更，随 G-01 一并授权 |

核实后**保留**（已是现在时事实或现行禁令）：`01:49`、`01:79`、`05:61`、`08:42`、`README:211–212`、
`onboarding-runbook.md:39`、`:88`、`:322`、`06` §「旧 `ci-bot` gate（已退役）」、
`skill-for-codex/SKILL.md:32`（`--issue 35 --merged-sha` 是 `gitea-governance.sh apply` 的参数合同，非条件句）。

### C · README §1 状态条目

| # | 文件:行 | 现状 | 处置 |
|---|---|---|---|
| C-01 | `README.md:3`、`:11` | `更新：2026-08-26`；`## 1. 当前状态（2026-08-26）` | 改为 `2026-09-03` |
| C-02 | `README.md:14` | ✅ 主机职责隔离（Issue #21） | 迁 archive |
| C-03 | `README.md:15` | 🟡 流水线，尾句「NewEmaint pilot 的该 role 位于本地 OrbStack DockerLab，不新增第三台公司 VM」 | 尾句迁 archive（项目放置事实），其余保留 |
| C-04 | `README.md:16` | ✅ Legacy 制品收口 | 迁 archive |
| C-05 | `README.md:17` | ✅ `prod-sim` 退役 | 迁 archive |
| C-06 | `README.md:18` | ✅ v2 试点证据 issue #4 | 迁 archive |
| C-07 | `README.md:20`、`:24` | ✅ Codex 基础；✅ Claude adapter（Issue #1）17 项 parity | 合并为一行现在时「✅ provider adapters：Codex 与 Claude adapter 共用 controller/verifier/状态/终态，等价、可互换；默认 `IMPLEMENT_PROVIDER=none`，启用是每项目独立验收；真实 VM pilot 未做」；原两行迁 archive |
| C-08 | `README.md:22` | ✅ Gitea 身份与可见性历史基线（#35）+ #208 「未获独立 live apply 授权前…不改变」 | 迁 archive；#208 尾句并入 `:23`（现有「source 合并不等于安装、provision 或 live 启用」后追加） |
| C-09 | `README.md:27` | ✅ Windows 目标设计 | 迁 archive（设计见 §5 交付形态参考 `12-Windows…`） |
| C-10 | `README.md:28` | ✅ 内网协作目标设计 | 迁 archive（`07` 为现行） |
| C-11 | `README.md:29` | ✅ Windows 快速原型设计 | 迁 archive（`15`） |
| C-12 | `README.md:31` | ✅ Docker offline V2（Issue #27） | 迁 archive |
| C-13 | `README.md:32` | ✅ Docker release 分阶段（Issue #58/#65） | 迁 archive |
| C-14 | `README.md` §1 末尾 | — | 新增一行 `📜 已完成条目的历史记录：[archive/平台状态历史-20260902.md](archive/平台状态历史-20260902.md)` |
| C-15 | `archive/平台状态历史-20260902.md`（新建）；`archive/README.md` 表格 | — | 逐字收录 C-02～C-13 与 A-04 迁出的条目，标注来源文件与迁出日期；索引表加一行 |

保留：`README.md:13`、`:19`、`:21`、`:23`、`:25`、`:26`、`:30`、`:33`、`:34`、`:35`（长期在位能力、进行中项与待办）。

### D · `09` 规划文档

| # | 文件:行 | 处置 |
|---|---|---|
| D-01 | `09…md:3–6` header | 状态行后加「落地对照：2026-09-02，见 §0.2」 |
| D-02 | `09…md` §0 末尾 | 新增 `### 0.2 落地对照（2026-09-02）` 表：§4/§4.3 → `03` + `codex/runtime/aisoft_loop/classification.py`；§5 → `03`（§5.3 的 `00-summary.md` 命名已被 #57/#75 readable tuple 取代）；§6 → `codex/config` labels manifest（27 标签）+ `03`；§7 → `04` + `codex/runtime/aisoft_loop`（§7.6 可选 review agent **未实施**，见 §13.2）；§8 → onboarding-runbook §4 + `02` §7；§9–§11 Phase D1–D5 已完成（§11「所有 Issue 都有 `00-summary.md`」一条已被 readable 命名取代）；§12.2 运行迁移已完成（§0），§12.3 回滚原则现行（`08` §9）；§13.2 两项**仍开放**；§15 → `architecture/` 已实施；§16 → #208 source 已合并，live apply / 每项目 opt-in **未执行**（README §1） |

### E · 根 `AGENTS.md` 目录段（独立原子 commit）

| # | 文件:行 | 处置 |
|---|---|---|
| E-01 | `AGENTS.md:38` | 同 A-14 |
| E-02 | `AGENTS.md:57` | `archive/`：历史实施记录、旧方案（含 10/11）与平台状态历史，只读参考，不作当前配置来源 |

### F · 12–15、02、`docker-release/`、`architecture/` 正文去留判定

| # | 对象 | 判定 | 理由 |
|---|---|---|---|
| F-01 | `02-CI与自动部署流水线.md` | 保留原位；`:3` 定位尾句「正文原样保留，去留由后续「过时文档清理」Issue 处置」改为「#233 判定：正文保留为参考记录；正文中「默认」「新 Linux 默认」等措辞不构成平台合同，交付形态由项目声明」 | §7「首次部署与部署变更验收」被 `03` §11、`06` §5、`smoke.sh:743` 引用；as-built 试点证据 |
| F-02 | `12-Linux-GitHub-Gitea-双服务器自动部署方案.md` | 保留原位；`:3` 尾句同 F-01 | `sync/`、`company-delivery/` 的参考合同 |
| F-03～F-06 | `12-Windows…`、`13`、`14`、`15` | 保留原位；`:3` 尾句同 F-01 | 尚未实施的设计/验收模板，不是过时内容 |
| F-07 | `docker-release/` | 不动 | #65 证据闸门冻结 |
| F-08 | `architecture/` | 不动 | 平台事实源与 CLI |

不归档理由：这些是按项目选用的参考实现/设计，#232 已把它们移出主线并标注性质；归档会使 `sync/`、
`company-delivery/`、`03`/`06` 的引用悬空，且不减少任何过时概念。

### G · `smoke.sh` 守卫

| # | 处置 | 理由 |
|---|---|---|
| G-01 | 新增独立守卫块：对 `skill-for-codex/references/*.md` 执行 #231 AC-1 项目名 pattern（`rg -ni 'NewEMaint\|SFMDigitalBoard\|HSDB\|WMPDA\|SapTable\|rsdesign\|myapp\|smoke-test\|LocalWMS'`），命中即退出 | references 随两侧技能安装到每台开发机；B-05、B-10 清掉现有两处命中后可固化 |
| G-02 | **不**把 #231 AC-2 交付形态名守卫扩到 references | runbook §4.2/§4.3/§9 必须列出 architecture `delivery_contract` 取值（`docker-release/v1`、`pm2-legacy`、`systemd-native/v1`、`windows-iis/v1`）与环境示例（IIS） |
| G-03 | 同 B-14 | 删除陈旧断言 |

## Acceptance criteria

- [ ] **AC-1 清单处置**：上表 A～G 每条在 verification 中有处置结果（删除 / 迁 archive 路径 / 改写后
  的行号 / 保留），没有「待定」。
- [ ] **AC-2 活文档 grep 为空**：
  `grep -rn -E 'Codex-first|Claude parity 条件|Claude Code 接入条件|After AISoftPlatform Issue #35|Legacy .?ci-bot.? collaborator gate' --exclude-dir=archive --exclude-dir=.git --exclude-dir=vendor . | grep -v '^./docs/changes/'`
  无输出（基线 5 处：`README.md:164`、`08:147`、`04:147`、`skill-for-codex/SKILL.md:26`、
  `onboarding-runbook.md:97`）。
- [ ] **AC-3 链接无悬空**：verification 中的脚本抽出仓库内全部相对 `.md` 链接（含 `archive/`、`docs/changes/`），
  逐一 `test -f`；改动后 `BROKEN` 集合等于基线集合，且基线集合只含 `skill-for-claude/aisoft-platform/SKILL.md`
  指向 `references/*.md` 的 3 条 install-time 链接（由 `skill-for-claude/install.sh` 复制后才存在，本 Issue 未
  引入）。`08` 改名后 `grep -rn '08-Codex双工具共存与实施.md' --include='*.md'` 只命中 `archive/10`、`docs/changes/`
  的代码跨度，无 `](…)` 链接形式。
- [ ] **AC-4 测试**：`bash codex/tests/smoke.sh` 全绿（基线 `Ran 651 tests … OK`）；
  `bash codex/tools/aisoft-project-check.sh --repo <worktree> --kind docs` 与基线逐行一致
  （`pass=2 gap=2 skip=4`：`change-documents`/`change-pr-url` PASS，`pointer-sections`/`change-templates`
  为结构性 GAP）；`bash codex/tests/test-install-claude-skills.sh` 全绿。
- [ ] **AC-5 语义等价**：五类合同的定义段落 `git diff origin/main...HEAD` 无变化——判级规则：`03` 全文、
  根 `AGENTS.md` 工作原则段、`skill-for-codex/SKILL.md:86–99`；命名元组：`03`、`skill-for-codex/SKILL.md:86–88`；
  单闸门：README §3/§4、`skill-for-codex/SKILL.md:98–99`；broker 路径：`06` §1.0、`onboarding-runbook.md:51–68`；
  routine merge 条件：`onboarding-runbook.md:36–41`、`:260–262`、`04` §9、`09` §16。上表「语义对照」列逐条
  说明被改句子为何不改变合同。
- [ ] **AC-6 守卫**：`smoke.sh` 新增 references 项目名守卫；反向证明：向 `onboarding-runbook.md` 临时追加
  `参照 NewEMaint` 后单独执行守卫块报红并退出，恢复后 `grep -c` = 0；`smoke.sh:465–466` 陈旧断言删除。
- [ ] **AC-7 非目标守卫**：`git diff --stat origin/main...HEAD -- docker-release/ architecture/ codex/runtime codex/tools codex/config templates company-delivery` 为空；
  `git diff --stat origin/main...HEAD -- archive/` 只含新建 `平台状态历史-20260902.md`、`README.md` 一行新增、
  `11-…md` 一行链接目标；不触及下游项目仓。
- [ ] **AC-8 两侧技能安装内容随之变化**：`bash skill-for-claude/check-drift.sh` 与 `bash codex/check-drift.sh`
  在改动后报 DRIFT（rc=1）并列出 references（Codex 侧另列 `gitea-platform-ops/SKILL.md`、`aisoft-platform/SKILL.md`）；
  重装后 CLEAN 记 NOT RUN（非目标）。

## 接口、数据与兼容性影响

- **两侧技能 references 与 Codex skills**：`onboarding-runbook.md`、`private-gitea-access.md` 由两侧安装脚本
  同源复制；`skill-for-codex/SKILL.md`、`codex/skills/gitea-platform-ops/SKILL.md` 由 `codex/install-skills.sh`
  安装。安装副本在重装前保持旧文；重装是合并后的独立动作。
- **`smoke.sh` 既有断言**保持成立：runbook 仍含 `ensure-gitea-collaborator.sh`、`gitea-governance.json`、
  `gitea.labels.provision`；`gitea-platform-ops/SKILL.md` 仍含 `retire-shared-bot`、`never begin with anonymous API access`；
  `skill-for-codex/SKILL.md` 仍含 `` private-repository `404` ``；`02` 仍含 `首次部署`；`04` 仍含
  `requested_complexity`；根 `AGENTS.md` 仍含 `功能性更改`；#231 三条守卫对治理集与活文档仍为空命中。
- **`08` 改名**：链接引用只有 README、AGENTS、`09`、`archive/11` 四处；`skill-for-claude`/`codex/global-AGENTS.md`
  以编号 `08` 引用，不受影响。
- **README §1 迁出条目**：#208「未获独立 live apply 授权前，现有 allowlist、credential 与 installed bytes 均不
  改变」并入 `:23`，不丢失当前约束（#213 verification 证实 live layers 仍 NOT RUN）。
- 不改 `docker-release/`、`architecture/`、`codex/runtime/`、`codex/tools/`、broker 操作表、任何 manifest、
  `templates/`（因此无需 `change-template-sync.sh --refresh-digest`）。

## 风险与回滚约束

- 回滚 = revert 本 Issue 的唯一 PR；已安装的 skills/references 用上一版源重跑安装脚本即恢复（本 Issue
  内不执行安装）。
- 本 spec 即修改治理文件（`skill-for-codex/SKILL.md`、`codex/skills/gitea-platform-ops/SKILL.md`、共享
  references、根 `AGENTS.md` 目录段、`smoke.sh` 守卫）的授权，范围以上表为限。根 `AGENTS.md` 只改目录段
  两行并单独成 commit，本次运行遵循的工作原则段不改。

## 非目标

- 不删除 `archive/` 已有内容；不改 runtime、broker、manifest、检查器逻辑；不改下游项目仓。
- 不动 `docker-release/`（#65 冻结）与 `architecture/`；不归档 02/12–15 正文（F 组判定保留）。
- 不安装或更新任何全局 skills。
- 不改 `07`、`company-delivery/` 中的项目名与「新项目默认」措辞（另开 Issue，见 verification 遗留项）。
- 不改 `01:49`、`README:211` 等已是现在时的退役身份事实陈述。

## 未决问题

无。四项解读（a）A-01 改名与 `archive/11:5` 链接目标同步；（b）超出初始盘点的补全项 A-04、A-11、
B-10～B-13；（c）F 组保留判定；（d）G-01 扩展、G-02 不扩展，已于 2026-09-03 确认点 1 由人认可，
并分别写入上表与 AC-6/AC-7。
