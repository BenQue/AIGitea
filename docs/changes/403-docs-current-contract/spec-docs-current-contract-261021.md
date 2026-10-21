---
issue: 403
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/403
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - ci-change
depends_on:
  - 391
  - 395
  - 396
status: approved
branch: change/403-docs-current-contract
created: 2026-10-21
updated: 2026-10-21
git_scope:
  - 01-基础设施-VM-Gitea-Runner.md
  - 02-CI与自动部署流水线.md
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 04-Agent编排与定时任务.md
  - 05-通知与多人协作.md
  - 06-运维手册与踩坑集.md
  - 07-内网与生产平移路线.md
  - 08-双工具共存与实施.md
  - 12-Linux-GitHub-Gitea-双服务器自动部署方案.md
  - 13-项目结果迁移与内网切换实施手册.md
  - README.md
  - GLOSSARY.md
  - architecture/README.md
  - codex/config/project-leak-baseline.json
  - codex/tests/smoke.sh
  - codex/tests/smoke-pin-baseline.json
  - codex/tools/aisoft-platform-readiness.sh
  - codex/tests/test-platform-readiness.sh
  - codex/runtime/tests/test_architecture_governance.py
  - docs/governance/remediation-roadmap.md
  - docs/changes/403-docs-current-contract/summary-docs-current-contract-261021.md
  - docs/changes/403-docs-current-contract/spec-docs-current-contract-261021.md
  - docs/changes/403-docs-current-contract/plan-docs-current-contract-261021.md
  - docs/changes/403-docs-current-contract/verification-docs-current-contract-261021.md
---

# R14 文档现行态：分册只写现行合同，README 状态机器生成，smoke 钉子棘轮

## 目标与原因

01–08 与 README 仍是变更日志体：规则、Issue 叙事、过时的「尚未运行」、手写日期与版本混在一起，读者分不清哪句是现行合同；smoke 与单测逐字钉正文，改一句话就红，于是没人敢删陈旧段落。本票把分册改成「现行合同 + 来历」两段式，让 README 的状态由工具从源码事实算出来，并给 smoke 的正文钉子设棘轮。顺带收掉 R13 交接遗留的文档站点值。

基线：`main` = `fdf93c1`（R10a、R10b、R13、R16、#370 均已合并）。度量基准：`77ad607` 时 `rg -c '#[0-9]{2,3}' 03*.md` = 53 行；开工时 57 行。smoke `grep -c 'grep -Fq'` = 100。

## 范围

### 1. 体例（01–08）

- 每册标题下一段 `> 现行合同：…`，一到三句话说本册管什么、权威来源在哪；不写日期、版本号、「本次核对」。
- 正文只写现行规则与命令。删除：已完成 Issue 的过程叙事（「#163 之前…」「这不是推演」类段落）、已经过时的状态句（如 `03` §3「#360 T02 只更新合同文档，runtime 尚未运行」，#360 已于 `06afadf` 合并）、「本节同步 #N 已合并的治理合同」类开场白。规则背后的理由保留一句，不保留故事。
- 文末一节 `## 来历`，表头 `| Issue | 合并 | 一句话 |`：每行一个（或一组相关）Issue、合并 commit 短 SHA（取自 `git log --merges`）、一句话说它给本册带来了什么。读者要细节就点 Issue 目录。
- 「未实施」不再散在各册：README 新增 `## 未实施清单`，一行一项（内容、承载 Issue 或「无」、所在分册小节）；分册里只留一句「见 README 未实施清单」或直接不提。
- **被技能、模板与使用合同引用的小节编号与标题保持不变**：`01` §1、§5；`03` §1、§3（含「何时声明 `verification`」「模板是 vendored 副本」两个小节标题开头）、§8、§11、「交叉审核」；`06` §1.0、§1.1、踩坑编号、「旧 `ci-bot` gate（已退役）」；`08` §5、§7.3。这样技能、模板与 `usage/` 都不用改，本票不触发发布包升版，也不和 R11 撞发布包。

### 2. 各册要点

- `03`：按体例重写；§2.1 routine、§6.1 PAT 轮换、§10 依赖、§11 终态各节只留规则与命令；§11「已经错过窗口的 Issue」处置表并入「来历」一行。验收标准 1 的计数以此为准。
- `04`：R10a 已压成一页，本票只补体例（现行合同段、来历表）并核对与 ADR 0002 一致。
- `08`：§1 去掉手写版本行；§4 压成一句加链接；§5 三张「已填写的示例」升级适配表移到「来历」之后的 `## 附：升级适配记录`（表内容原样，只搬位置）；§7.3 不动。
- `06`：踩坑表原样保留（编号是正文引用号）。§1 开头的命令块只放命令；§1.0–§1.3 每小节先写规则、再写命令，叙事移除。其余小节按体例处理。
- `01`：§4.3 Flutter SDK 标注「按项目需求提供的 runner 能力，不是平台默认工具链」（Codex D5 残留）；as-built 日期留在 as-built 表内作为观测时间，不放进规则句。
- `02`、`05`、`07`：按体例处理；`05` §1「部署失败与回滚通知」现状写进 README 未实施清单。
- `GLOSSARY.md`：补 ADR 0002 术语（路由卡、路由表、process、tier/effort、确认点 1/2、执行引擎、合成 T01、`change_control`、交叉审核）；修正指向已迁出分册的旧链接（如 `AWAITING_PR_CONFIRMATION` 指向 `04`）。

### 3. README

- 删除 §1 手写状态表与页首「版本 / 文档核对 / 源码基线」行；§1 改为三句话：稳定源码的含义、各层证据分开、当前状态用 `bash codex/tools/aisoft-platform-readiness.sh --render-readme` 生成。
- 其余各节去掉手写日期、版本号与 Issue 叙事（mermaid 里的 `Gitea 1.26.4` 等也去掉）；导航表与链接目标里的日期、版本不算。
- 新增 `## 未实施清单`。

### 4. `aisoft-platform-readiness.sh --render-readme`

- 新模式只读源码，不调用 broker、不读已安装面、不联网，向 stdout 输出一张 Markdown 表：源码 SHA、治理仓库数、broker 操作数、installer 数、标签数、使用发布包最新版本、Matt 与 superpowers 的 pin（版本 + 短 commit）、architecture catalog revision。每格的取值来源写在第三列。
- 输出**不嵌入** README（选择见下）；`test-platform-readiness.sh` 用隔离 fixture 断言表头、行集合与取值来源，并断言该模式不调用 broker。

### 5. smoke 钉子与棘轮

- 新增 `codex/tests/smoke-pin-baseline.json`：`{"grep_fq_lines": <N>}`。smoke 计算 `grep -c 'grep -Fq' codex/tests/smoke.sh`，大于基线即红，小于基线打印 NOTE 提示收紧。
- 01–08/README 的正文短语钉子改为小节标题钉子：新增一个 `require_heading <文件> <标题>` 辅助函数，按整行精确匹配 Markdown 标题（`^#{1,6} 标题$`），一次调用一个标题。保留的钉子只钉标题或 front matter 字段；当前钉 `03`、`04`、`05`、`06`、`07`、`08`、`02` 正文短语的约 15 处逐条改写或删除，改写清单写进 verification。
- 新增 README 守卫：链接目标与导航表以外出现 `YYYY-MM-DD` 日期或 `vN.N` 版本号即红。
- `codex/runtime/tests/test_architecture_governance.py` 钉 README、`07`、`12` 正文短语的那条用例改为钉小节标题。`test_session_contract.py` 对 `08` §3 单写者条目的变异测试不在本票范围（它测的是合同句本身，`08` §3 那一条保持原文）。
- 基线取改写后的实际计数，必须 < 100。

### 6. 站点值

- 01、02、03、05、07、README、12、13、`architecture/README.md` 里作为指令写死的站点值（Gitea 地址、OrbStack 机器名、运维账号、凭据根、检出路径）改为引用 broker manifest 的 `site` 段键名；as-built 观测表、`architecture/evidence/`、`architecture/decisions/` 原样保留。
- 跑 `python3 codex/tests/check-project-leak.py --write-baseline` 收紧 `site_files`，计数只降不升。

## 实现选择（确认点 1 一并确认）

1. **README 状态表按需生成、不嵌入**（推荐）。嵌入的话每次发布包升版、broker 增减操作都要同 PR 重渲 README，并行批次会在同一段行上互相冲突（`06` 的踩坑号与 smoke 计数已经吃过这个亏）。备选：嵌入 `<!-- readiness:begin/end -->` 块并由 smoke 校验与生成结果一致，好处是 README 上直接可见。
2. **棘轮只数 `grep -Fq`**，按计划原文。其它形式（`rg -q`、Python `assertIn`）本票不设棘轮，只把 01–08/README 上的正文钉子改为标题钉子。
3. **小节编号不重排**，见「体例」最后一条；代价是个别分册编号不连续（例如 `02` 现在从 §0 跳到 §7），本票不处理。

## Acceptance criteria

- [ ] AC-1 `rg -c '#[0-9]{2,3}' 03-Issue-Spec-Plan与单闸门开发流程.md` ≤ 26（`77ad607` 为 53），且每个保留引用所在的行都在 `03` 的「来历」表里（verification 附逐行清单）。
- [ ] AC-2 01–08 每册有「现行合同」段与 `## 来历` 表，来历表的合并 SHA 都能 `git cat-file -e` 解析；README 有 `## 未实施清单`，分册不再出现「尚未实施 / 尚未运行」类状态句（`rg` 结果附 verification，as-built 表与踩坑表除外）。
- [ ] AC-3 README 除导航与链接目标外没有手写日期与版本号，smoke 守卫在注入一个日期时变红（反向证明记 verification）。
- [ ] AC-4 `aisoft-platform-readiness.sh --render-readme` 输出状态表，`test-platform-readiness.sh` 覆盖它且断言不调用 broker；README §1 指向这条命令。
- [ ] AC-5 `smoke-pin-baseline.json` 存在，值 < 100 且等于实际计数；往 smoke 加一行 `grep -Fq` 时 smoke 变红（反向证明）；01–08/README 上不再有正文短语钉子（清单附 verification）。
- [ ] AC-6 `01` §4.3 有 runner 能力标注；`GLOSSARY.md` 有 ADR 0002 术语且链接都能解析到存在的文件。
- [ ] AC-7 `project-leak-baseline.json` 的 `site_files` 收紧，任何文件计数不升、总数下降。
- [ ] AC-8 技能、模板、`usage/` 零 diff（小节编号未破坏引用）；`usage-bundle.sh --verify` 通过；`bash codex/tests/smoke.sh` 全绿；`bash -n` 与 ShellCheck 通过；Codex 只读交叉审查 PASS；判级投影读回 `projected`。

## 接口、数据与兼容性影响

- 不改 broker、manifest 合同、installer、技能与发布包成员；合并后不需要两台重装，也不需要重装技能。
- `aisoft-platform-readiness.sh` 新增一个只读模式，既有输出与退出码不变。
- smoke 多一道棘轮：之后任何批次往 smoke 加 `grep -Fq` 都要同 PR 抬基线并在 PR 里说明，或改用标题钉子。并行的 R11、R16 若先合并并加了钉子，后合并的一方以 merge commit 集成 main 并按实际计数更新基线。

## 风险与回滚约束

整 PR revert 即回滚，没有数据或安装面后果。主要风险是删段落时误删现行规则：每册改写后由 Codex 对照 `86821cf` 的原文逐节核对「规则是否丢失」，结论写 verification。`06` 与 R16（PR 400 改 `06` §4 与安装面表）可能冲突，后合并者从 `origin/main` 重建冲突块。

## 非目标

不改 12–15 参考文档的正文结构（只改站点值）；不改 `docs/changes/`、`archive/`、`docs/adr/`；不改技能与模板；不重排小节编号；不给 `rg -q` / `assertIn` 设棘轮；不处理 R16 的漂移棘轮与 PAT 周期；不推 GitHub 镜像。

## 未决问题

无。
