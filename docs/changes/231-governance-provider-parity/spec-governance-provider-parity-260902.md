---
issue: 231
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/231
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
depends_on: []
status: contract-drafting
branch: change/231-governance-provider-parity
created: 2026-09-02
updated: 2026-09-02
---

# Spec · 平台治理去项目化、去部署细节，Claude/Codex 等价

## 目标与原因

把平台仓两侧技能（`skill-for-claude/`、`skill-for-codex/SKILL.md`、`codex/skills/`）、VM 全局 Codex
指令（`codex/global-AGENTS.md`）与下游项目常驻指针模板（`templates/project/AGENTS.md`）收敛到
2026-09-02 定案的平台定位：

- **只管流程管控**：平台治理文本只写流程不变量，不写任何项目的名字、端口、交付形态实现。
- **去项目化**：项目相关内容由项目自身的 profile 与 `AGENTS.md` 决定。
- **Claude Code 与 Codex 等价、不分主辅**：两个模型互相取长补短、目标一致。#207 写入的「Codex 默认
  主处理者 / Claude 对等补位」与模板里的「Claude=开发 / Codex=运维」两处互相矛盾，一并统一。
- **过时表述及时清除**：技能正文不再复述踩坑成因，只指向 `06` 的编号。

本 spec 把 Issue #231 正文的 7 条验收标准逐条落成可观察结果；Issue 正文是合同源，本文不扩张。

## 术语

- **范围文件（governance set）**：Issue 正文「范围」列出的 7 份治理文件：
  `skill-for-claude/aisoft-platform/SKILL.md`、`skill-for-claude/issue-session-flow/SKILL.md`、
  `skill-for-codex/SKILL.md`、`codex/skills/aisoft-matt-workflow/SKILL.md`、
  `codex/skills/issue-session-flow/SKILL.md`、`codex/global-AGENTS.md`、`templates/project/AGENTS.md`。
- **活文档**：仓库内除 `archive/`、`docs/changes/`、`codex/vendor/`、`.git/` 之外的全部文件。
- **等价句**：AC-3 定义的同一句工具分工表述，中文版逐字相同，英文技能用同义翻译。

## Acceptance criteria

- [ ] **AC-1 去项目化**：对范围文件执行
  `grep -rn -iE 'NewEMaint|SFMDigitalBoard|HSDB|WMPDA|SapTable|rsdesign|myapp|smoke-test|LocalWMS'`
  输出为空；`skill-for-claude/aisoft-platform/SKILL.md` 与 `skill-for-codex/SKILL.md` 的 front matter
  `description` 只用通用触发词（Issue、判级、change 分支、broker、接入平台等），不列项目名。
- [ ] **AC-2 去部署细节**：对范围文件执行 `grep -rn -iE 'docker-release|PM2|Compose|systemd-native|IIS'`
  输出为空。`skill-for-claude/aisoft-platform/SKILL.md` 的「部署边界」只保留流程不变量
  （不可变制品、同字节晋级、健康检查、可回滚、生产 script-only、AI 可参与非生产首次部署并固化为
  脚本），并用一句话指向「交付形态由项目自己的 profile 与 `AGENTS.md` 声明和实现」。
- [ ] **AC-3 provider 等价**：对活文档执行
  `grep -rn -E '默认主处理者|primary handler|维护与部署|开发与设计|Codex 为主|对等补位'` 输出为空；
  `skill-for-claude/aisoft-platform/SKILL.md` 与 `templates/project/AGENTS.md` 的「工具分工」段为逐字
  相同的等价句；`skill-for-codex/SKILL.md` 与 `codex/global-AGENTS.md` 用同义英文表述。等价句内容：
  Claude Code 与 Codex 共用同一平台合同，能力等价、可互换、不分主辅，两个模型互相取长补短、目标一致，
  都不各自发明流程；自动化 provider 仍由项目 profile 的 `ANALYSIS_PROVIDER`/`IMPLEMENT_PROVIDER`
  显式选择（默认 `none`）。
- [ ] **AC-4 Claude 侧简化取向**：`skill-for-claude/aisoft-platform/SKILL.md` 与
  `skill-for-claude/issue-session-flow/SKILL.md` 各含一段「approved 之后默认自主推进」与一段「只在这些
  情况暂停」，暂停条件覆盖：合同冲突、范围扩张、破坏性迁移、安全/权限/架构新决策、直接生产动作、
  外部依赖缺失、验证不可靠、同因三次失败；语义与 `codex/skills/issue-session-flow/SKILL.md`
  「Default autonomy after approval」一致但不逐字复制。`aisoft-platform` 技能「会话标准动作」第 4–7 步
  各压缩为一行，并分别指向 `06` 的对应编号（第 4 步→踩坑 20、21；第 5 步→`03` §3 / §11 与 `06` §6；
  第 6、7 步→`06` §1.0 broker 段落），正文不再复述成因。
- [ ] **AC-5 项目模板瘦身**：`templates/project/AGENTS.md` 常驻指针两节不含 Gitea 版本号、merge-only
  ACL、credential custody、allowlist 字样；「交付形态」占位符不引用任何项目，取值示例为环境类别
  `<Linux 容器化 | Linux 原生 | Windows | 其它>`。`bash codex/tests/test-project-check.sh` 全绿，其中由新模板
  生成的对齐 fixture 读回 `PASS: pointer-sections`；`codex/tools/aisoft-project-check.sh --repo <平台仓> --kind docs`
  的结果与基线一致（`change-documents`/`change-pr-url` PASS；`pointer-sections`/`change-templates` 为
  基线既有的结构性 GAP，本 Issue 不改变，见「未决问题」的解读）。
- [ ] **AC-6 测试与漂移**：`bash codex/tests/smoke.sh` 全绿，且 `smoke.sh` 新增三条静态守卫把 AC-1、
  AC-2 的范围 grep 与 AC-3 的活文档 grep 固化；`bash skill-for-claude/check-drift.sh` 与
  `bash codex/check-drift.sh` 在本机改动后如实报 DRIFT（退出 1）；重装后 CLEAN 的观测在 verification
  中如实记录为 NOT RUN（本 Issue 非目标：不安装或更新全局 skills）。
- [ ] **AC-7 下游不动**：本 PR 的 diff 不触及任何下游项目仓；下游 `pointer-sections` 转 GAP 属预期，
  在 verification 中记录一次说明，不批量改写。

## 接口、数据与兼容性影响

- **技能 front matter `description`**：Claude 侧 `aisoft-platform` 的触发词列表改变（去项目名、去
  `docker-release`）。安装到 `~/.claude/skills/` 的副本在重装前保持旧触发词；重装是合并后的独立动作。
- **下游模板合同**：`aisoft-project-check.sh` 的 `pointer-sections` 用 `templates/project/AGENTS.md` 的
  常驻指针两节做逐字比对，模板一变所有已对齐的下游仓都转 GAP。这是模板演进的既定行为（#91），
  各项目按 project-align 在自己的 Issue 跟进。
- **`delivery-profile` 检查**：`aisoft-project-check.sh` 对下游 `AGENTS.md` 的交付形态行按
  「非占位符、有内容」判定，不依赖占位符具体取值；模板占位符改为环境类别后，已填写具体形态的
  下游仓不受影响，仍带占位符的下游仓与现在一样为 GAP。`test-project-check.sh` 的对齐 fixture 用
  awk 把占位符行替换成一个具体值，匹配模式要随新占位符改写；fixture 里的具体值代表「某个下游项目
  自己的选择」，不属于 AC-2 的范围文件。
- **`smoke.sh` 已有断言**保持成立：`codex/global-AGENTS.md` 仍含 `explicit project profile`、
  `/mnt/mac/Users/benque/MyDocs/AISoftPlatform/` 与 §「Skill routing」的全部 `$`-skill 字样；
  `skill-for-codex/SKILL.md` 仍含 `` private-repository `404` `` 与
  `AISOFT_ONBOARDING_MODE=software-repository`；`skill-for-claude/aisoft-platform/SKILL.md` 仍交叉引用
  `issue-session-flow`（`test-install-claude-skills.sh`）。
- 不改 runtime、broker 操作表、标签 manifest、`skill-for-codex/references/`、编号分册、README、
  根 `AGENTS.md`。

## 风险与回滚约束

- 回滚 = revert 本 Issue 的唯一 PR；本机已安装的 skills 用上一版源重跑 `skill-for-claude/install.sh` /
  `codex/install-skills.sh` 即恢复（本 Issue 内不执行安装）。
- 本次运行遵循根 `AGENTS.md`，不修改它；被改的治理文件是技能源与下游模板，符合「治理文件由 spec
  明确授权」的要求——本 spec 即该授权，授权范围以「术语」中的范围文件与两份测试为限。

## 非目标

- 不改 `skill-for-codex/references/*.md`、编号分册、README、根 `AGENTS.md`（含目录段）。
- 不改 `codex/runtime/`、broker 操作表、标签 manifest、`codex/tools/aisoft-project-check.sh`。
- 不安装或更新任何全局 skills；不改动任何下游项目仓。
- 不改 `04` §10「Codex-first 验证顺序」等编号分册中的历史表述（后续「过时文档与概念清理」Issue）。

## 未决问题

- **AC-5「对平台仓自身仍 PASS」的解读**：基线 `origin/main` 上
  `aisoft-project-check.sh --repo <平台仓> --kind docs` 已是 `pass=2 gap=2 skip=4`，两项 GAP
  （`pointer-sections`、`change-templates`）源于平台仓根 `AGENTS.md` 不含常驻指针两节、`CLAUDE.md`
  带 `## Agent skills`、change 模板放在 `templates/docs/changes/_template/` 而非 `docs/changes/_template/`。
  这是平台仓作为模板源的结构性事实，修它超出本 Issue 范围（要改根 `AGENTS.md`）。本 spec 采用的
  解读写在 AC-5：平台仓结果与基线一致，新模板的 `pointer-sections` PASS 由测试 fixture 证明。
  该解读在确认点 1 提请人认可；认可后清空本条。
