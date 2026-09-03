---
issue: 241
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/241
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更改写 Codex 兼容 adapter 技能 codex/skills/gitea-platform-ops/SKILL.md（Agent 行为文件）——去项目名反例、把某一种交付形态的运维步骤改写为形态中立原则并指向目标项目的部署文档与脚本；同时把 Issue 231 的 smoke 项目名/交付形态守卫从两个点名的 codex/skills 文件扩展到 codex/skills 下全部 SKILL.md。属 Agent 行为与平台治理文件的合同变更，强制 complex，change_control=production 需 spec+plan
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-platform-ops-neutral-260903.md
  spec: spec-platform-ops-neutral-260903.md
  plan: plan-platform-ops-neutral-260903.md
  verification: verification-platform-ops-neutral-260903.md
confidence: high
override_reason: ''
depends_on:
  - 231
status: approved
branch: change/241-platform-ops-neutral
pr_url:
created: 2026-09-03
updated: 2026-09-03
---

## 问题/需求总结

去项目化调度收口终检（2026-09-03）发现最后一处残留：`codex/skills/gitea-platform-ops/SKILL.md`
不在 #231 的治理文件守卫集合（`governance_set`）内，仍含项目名反例（第 9 行「Never assume rsDesign
or any example repository」）与某一种交付形态的运维步骤（第 3 行 description 与第 24、27、31 行的
PM2、release symlink、`sqlite3 .backup`、PM2 delete+start）。按 2026-09-02 定案（平台只管流程管控与
环境级指导，部署步骤与细节在项目仓实现），这些应改为形态中立的诊断/回滚流程原则，并指向目标
项目自己的部署文档与脚本。

本 Issue 的合同是 Issue #241 正文的「验收标准」「非目标」，本 summary 只做判级与路由。

## 影响范围

- `codex/skills/gitea-platform-ops/SKILL.md`：description 与第 8、9、24、27、31 行措辞（编号项 1、2、11、14、18）。
- `codex/tests/smoke.sh`：#231 `governance_set` 从两个点名的 `codex/skills/…/SKILL.md` 条目扩展为
  `codex/skills/*/SKILL.md` 全部文件；交付形态守卫 pattern 与 Issue AC-1 的 grep 对齐（追加
  `sqlite3 .backup|release symlink`）。
- `docs/changes/241-platform-ops-neutral/`：四份语义文档。

不改 `codex/runtime/`、broker 操作表、标签 manifest、`docker-release/`、`codex/vendor/`、其它
`codex/skills/*/SKILL.md`（基线 grep 已为空）、`agents/openai.yaml`（不含项目名与交付形态名）；
不安装或更新任何全局 skills。

## 初步方案与建议

1. 逐行改写：description 去掉 `PM2`；第 1 项改为「先读 `02`/`06` 取平台级不变量，再读目标项目自己的
   部署文档与脚本取具体步骤」；第 2 项反例去项目名；第 11 项证据清单把「release symlink、PM2 state」
   改为「按目标项目部署文档定义的当前 release 与服务状态」；第 14 项「synthetic PM2」改为
   「synthetic service」；第 18 项改为形态中立顺序（停服 → 已验证备份 → 切换 release → 重启 → 在线断言
   → 按精确 release SHA 健康检查），具体命令来自目标项目的部署文档与脚本。
2. 守卫扩展：`governance_set` 用 `"$ROOT"/codex/skills/*/SKILL.md` 替换两条点名条目，并在 grep 前逐个
   `[[ -f ]]` 断言存在（防 glob 未展开时 rg 因缺文件退 2 被 `if` 当作「无命中」）；交付形态 pattern
   追加 `sqlite3 .backup|release symlink`。
3. 反向证明：向一个新纳入的 `codex/skills/*/SKILL.md` 临时注入项目名，`bash codex/tests/smoke.sh`
   应 rc=1；恢复后真实树 rc=0；两次结果写进 verification。

## 风险

- 治理文件变更：本次运行遵循根 `AGENTS.md`，不在范围内；被改的是 Codex 技能源，本机安装副本在本
  Issue 内不重装（非目标），`codex/check-drift.sh` 会如实报 DRIFT，重装是合并后由用户独立执行的动作。
- `smoke.sh` 既有断言 `never begin with anonymous API access` 与 `retire-shared-bot` 仍指向本技能，
  改写时必须保留这两段原文。
- 守卫 pattern 对 `Compose`、`IIS` 用 `-i`，改写文本不得引入 `compose`/`iis` 子串。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更改写 Codex 兼容 adapter 技能 codex/skills/gitea-platform-ops/SKILL.md（Agent 行为文件）——去项目名反例、把某一种交付形态的运维步骤改写为形态中立原则并指向目标项目的部署文档与脚本；同时把 Issue 231 的 smoke 项目名/交付形态守卫从两个点名的 codex/skills 文件扩展到 codex/skills 下全部 SKILL.md。属 Agent 行为与平台治理文件的合同变更，强制 complex，change_control=production 需 spec+plan
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue 正文自述「complex（Agent 行为文件；强制规则）。change_control=production，需 spec + plan」。
- 根 `AGENTS.md` 工作原则：「Agent 或平台治理变更一律按 complex 处理」；被改文件由
  `codex/install-skills.sh` 安装到 `~/.agents/skills/gitea-platform-ops/`，是 Agent 行为源。
- `contract_effect: change`：技能第 1、11、18 项对 Agent 的指令内容改变（从某一形态的具体步骤改为
  形态中立顺序并指向项目文档）；`smoke.sh` 守卫覆盖范围扩大，对未来所有 `codex/skills/*/SKILL.md`
  写入形成新约束。
- `verification` 的声明依据是 `03` §3：改动前基线 grep 命中、守卫反向注入 rc=1、`check-drift.sh`
  基线 CLEAN / 改动后 DRIFT 都是 required CI 不复现的一次性观测。
- 基线观测（2026-09-03，`origin/main` = `b80af37`）：Issue AC-1 两条 grep 对 `codex/skills/*/SKILL.md`
  只命中 `gitea-platform-ops/SKILL.md` 第 3、9、24、27、31 行；两侧 `check-drift.sh` 均 CLEAN。

### 缺失的 acceptance criteria 或决策

- 无。守卫 pattern 追加 `sqlite3 .backup|release symlink` 是为了与 Issue AC-1 的 grep 一致（基线下
  整个治理集合对这两项只命中本技能被改写的两行），属守卫扩展的自然范围，不改变 #231 三条守卫的既有语义。
