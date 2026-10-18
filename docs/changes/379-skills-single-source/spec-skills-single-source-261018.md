---
issue: 379
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/379
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: approved
branch: change/379-skills-single-source
created: 2026-10-18
updated: 2026-10-18
git_scope:
  - 02-CI与自动部署流水线.md
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 07-内网与生产平移路线.md
  - 08-双工具共存与实施.md
  - 12-Linux-GitHub-Gitea-双服务器自动部署方案.md
  - 12-Windows平台自动部署方案.md
  - 13-项目结果迁移与内网切换实施手册.md
  - 14-Windows部署与迁移验收清单.md
  - 15-VMware-Fusion-Windows-ARM原型实施手册.md
  - AGENTS.md
  - README.md
  - codex/check-drift.sh
  - codex/install-skills.sh
  - codex/lib/skills-manifest.sh
  - codex/runtime/tests/test_architecture_governance.py
  - codex/runtime/tests/test_routine_merge.py
  - codex/skills/aisoft-matt-workflow/SKILL.md
  - codex/skills/aisoft-matt-workflow/agents/openai.yaml
  - codex/skills/gitea-analyze-change/SKILL.md
  - codex/skills/gitea-analyze-change/agents/openai.yaml
  - codex/skills/gitea-development-loop/SKILL.md
  - codex/skills/gitea-development-loop/agents/openai.yaml
  - codex/skills/gitea-implement-change/SKILL.md
  - codex/skills/gitea-implement-change/agents/openai.yaml
  - codex/skills/gitea-platform-ops/SKILL.md
  - codex/skills/gitea-platform-ops/agents/openai.yaml
  - codex/skills/gitea-spec-plan/SKILL.md
  - codex/skills/gitea-spec-plan/agents/openai.yaml
  - codex/skills/issue-session-flow/SKILL.md
  - codex/tests/fixtures/installed-drift/test-installed-drift.py
  - codex/tests/smoke.sh
  - codex/tests/test-external-skill-versions.sh
  - codex/tests/test-install-claude-skills.sh
  - codex/tests/test-installer-source-guard.sh
  - codex/tests/test-usage-bundle.sh
  - codex/tools/check-external-skill-versions.py
  - codex/tools/check-external-skill-versions.sh
  - codex/tools/check-installed-drift.py
  - codex/tools/usage-bundle.py
  - company-delivery/README.md
  - docs/adr/0001-platform-boundary.md
  - docs/changes/379-skills-single-source/plan-skills-single-source-261018.md
  - docs/changes/379-skills-single-source/spec-skills-single-source-261018.md
  - docs/changes/379-skills-single-source/summary-skills-single-source-261018.md
  - docs/changes/379-skills-single-source/verification-skills-single-source-261018.md
  - docs/governance/remediation-roadmap.md
  - skill-for-claude/aisoft-platform/SKILL.md
  - skill-for-claude/check-drift.sh
  - skill-for-claude/install.sh
  - skill-for-claude/issue-session-flow/SKILL.md
  - skill-for-claude/skills.manifest
  - skill-for-codex/SKILL.md
  - skill-for-codex/agents/openai.yaml
  - skill-for-codex/references/onboarding-runbook.md
  - skill-for-codex/references/private-gitea-access.md
  - skill-for-codex/references/project-align.md
  - skills/aisoft-matt-workflow/SKILL.md
  - skills/aisoft-matt-workflow/agents/openai.yaml
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/agents/openai.yaml
  - skills/aisoft-platform/references/onboarding-runbook.md
  - skills/aisoft-platform/references/private-gitea-access.md
  - skills/aisoft-platform/references/project-align.md
  - skills/gitea-analyze-change/SKILL.md
  - skills/gitea-analyze-change/agents/openai.yaml
  - skills/gitea-development-loop/SKILL.md
  - skills/gitea-development-loop/agents/openai.yaml
  - skills/gitea-implement-change/SKILL.md
  - skills/gitea-implement-change/agents/openai.yaml
  - skills/gitea-platform-ops/SKILL.md
  - skills/gitea-platform-ops/agents/openai.yaml
  - skills/gitea-spec-plan/SKILL.md
  - skills/gitea-spec-plan/agents/openai.yaml
  - skills/issue-session-flow/SKILL.md
  - skills/skills.manifest
  - templates/project/cursor/aisoft-platform.mdc
  - usage/bundle.json
---

# #379 spec：技能单一来源、Cursor 使用层落点与交叉审核固定步骤（R7）

负责人于 2026-10-18 在项目主线回复“那么 R7 继续”，批准本合同（含三项默认选择）并启动实现。

## 目标与原因

ADR 0001 D8 要求技能正文只写一份、由安装器生成多种落点；D6 要求 Cursor 只进使用层、交叉审核成为维护层固定步骤；D5 把三处技能目录归为“后续合并为单一来源”。负责人的总目标是平台对任何项目实例没有硬依赖，只保留流程与方案模式。

## 已核对的事实（2026-10-18）

- 技能源三处：`skill-for-claude/{aisoft-platform,issue-session-flow}/SKILL.md`（中文，110 与 231 行），`skill-for-codex/SKILL.md`（英文 156 行）与 `references/` 三份共享参考，`codex/skills/` 七个技能（英文，其中五个 `gitea-*` 与 `aisoft-matt-workflow` 带 `agents/openai.yaml`）。两份 `issue-session-flow` 差异 409 行。
- 安装：`skill-for-claude/install.sh` 按 `skills.manifest` 精确装 SKILL.md 与 references 到 `~/.claude/skills`；`codex/install-skills.sh` 整目录复制到 `~/.agents/skills` 并管理 Matt 快照。各有一份 `check-drift.sh`，`check-installed-drift.py` 汇总两侧。
- Cursor 3.24.12：技能目录为 `~/.cursor/skills/<name>/` 与项目 `.cursor/skills/<name>/`（内置 create-skill 说明），规则为 `.cursor/rules/*.mdc`（front matter `description`、`globs`、`alwaysApply`）。插件缓存 `~/.cursor/plugins/cache/` 里 Matt 1.2.0（平台 pin v1.3.1）、superpowers 6.1.1（适配记录 7.0.0），均不受管。
- 正文里的单家工具名只有少量：“Claude Code”、“Skill tool”、“subagent/子代理”。`$name` 是平台全仓通用的“调用技能 name”记法，不算单家工具名。

## Acceptance criteria

- [ ] AC1 单一来源：新增顶层 `skills/<name>/`，每个平台自定义技能一份 `SKILL.md`；`aisoft-platform` 的共享参考移到 `skills/aisoft-platform/references/`；Codex 专用元数据保留为 `skills/<name>/agents/openai.yaml`（只装到 Codex 落点）。`skills/skills.manifest` 每行 `<name> <targets>` 声明维护层落点（`claude`、`codex` 的非空子集），保持现有安装集合不变：`aisoft-platform` 与 `issue-session-flow` 两侧，其余五个 `gitea-*` 与 `aisoft-matt-workflow` 仅 Codex。`skill-for-codex/`、`codex/skills/` 与 `skill-for-claude/*/SKILL.md` 删除，`skill-for-claude/` 只留脚本。
- [ ] AC2 正文合并：`aisoft-platform` 与 `issue-session-flow` 各合成一份中文正文，`description` 中英双语以保证两侧触发；逐条保留两侧独有规则（合并对照表记入 verification）。正文不出现单家工具名，需要的能力（子代理、技能调用、交互提问）用能力名写，并写明没有该能力时的降级做法。smoke 增加守卫：`skills/` 下出现约定的单家工具名清单即失败。
- [ ] AC3 安装器：两条现有重装命令不变，均改读 `skills/` 与清单。Claude 落点装 `SKILL.md` 与 `references/`，不装 `agents/`；Codex 落点整目录复制，Matt 快照逻辑不变。两份 `check-drift.sh` 与 `check-installed-drift.py` 按同一清单比较。安装来源闸门的计数同步。已安装目录名不变，不删除任一侧现有安装（D8）。
- [ ] AC4 Cursor 使用层：`usage-bundle.sh --build` 把 `skill` 成员按技能名导出到项目级 `.claude/skills/<name>/`、`.agents/skills/<name>/`、`.cursor/skills/<name>/`：技能进入哪个落点跟随 `skills.manifest` 的声明（Codex 落点跟 `codex`，Claude 与 Cursor 落点跟 `claude`），Claude 与 Cursor 落点不含 `agents/`；新增 seed 成员 `templates/project/cursor/aisoft-platform.mdc` → `.cursor/rules/aisoft-platform.mdc`，`alwaysApply: true`，只指向 `.aisoft/platform-usage.md`、lock 与 `AGENTS.md`，不复制规则正文。不往 `~/.cursor` 安装任何东西。project-align 参考写明按项目选用的工具复制对应落点。
- [ ] AC5 Cursor 外部技能纳入核对：`check-external-skill-versions.sh` 增加 Cursor 段，只读报告插件缓存里 Matt 与 superpowers 的版本，与 Matt pin、superpowers 适配记录对照（落后报 `BEHIND`，超前报 `REVIEW_NEEDED`，无 Cursor 报 `NOT_INSTALLED`，格式不认识报 `UNKNOWN`）；不安装、不升级。`08` §5 与 §7 使用层写入 Cursor 列。
- [ ] AC6 交叉审核固定步骤：`03` 的维护层流程与 `08` §7 维护层写明：complex 平台变更在确认点 2 之前，由未参与实现的另一方提供者对候选 head 做一次只读独立审查，结论（审查方、审查的 head、PASS/FAIL、发现与处置）记入该 Issue 的 verification；FAIL 修复后重审，不增加人的确认点。`issue-session-flow` 的 PR 候选步骤引用这一条。smoke 守卫钉结构（小节标题存在），不钉句子。
- [ ] AC7 发布包：`usage/bundle.json` 成员 source 改为 `skills/` 路径，加入 Cursor 薄指针，发布 `1.1.0`；origin/main 上的 1.0.0 原样保留；`--verify --baseline-ref origin/main` 通过。
- [ ] AC8 文档与路线：README 目录、`08`、`03`、ADR D5 表中技能行的处置状态、project-align 与 runbook 的路径更新；`AGENTS.md` 目录一行把技能源改为 `skills/`（只改事实路径，不改规则）；`02`、`07`、`12`–`15` 与 `company-delivery/README.md` 引用的 runbook 路径同步；路线 R7 行写本票状态。
- [ ] AC9 验证：macOS 全量 smoke 通过；在临时 HOME 里跑两条安装命令与三项漂移检查为 CLEAN；`--build` 产物三种落点齐全；Codex 独立审查结论记入 verification。合并后两侧重装与 `check-installed-drift.sh` 读回由我按交接执行并记录。

## 接口、数据与兼容性影响

技能名、安装目录与两条重装命令不变。源路径变化影响所有引用旧路径的文档、测试与发布包成员。项目侧：1.1.0 新增三种项目级技能落点与 Cursor 规则，都属 seed 或导出物，已 pin 1.0.0 的项目不受影响。不改 broker、CI workflow、docker-release、architecture、routine merger 与 manifest。

## 风险与回滚约束

正文合并可能漏规则：对照表加现有短语守卫兜底，Codex 审查专看这一项。R6b 并行改 smoke 与部分测试，后合并者 rebase 并重跑 smoke；若 R6b 先发布版本，本票改发下一号。回滚：revert 本 PR 后两侧重装。

## 非目标

- 不把 Cursor 加入维护层，不为 Cursor 写维护层安装器。
- 不改变各技能的安装集合（不新增 Claude 侧 `gitea-*`）。
- 不安装或升级任何外部技能包；Cursor 侧 Matt 是否升到 v1.3.1 由负责人按外部技能策略决定。
- 不做 R6b 的测试夹具解耦与 R8 的参考实现迁出。

## 未决问题

无。合并后正文统一用中文、Cursor 只在项目级落点、外部包只核对不安装，这三点是本合同的默认选择，确认点 1 一并确认。
