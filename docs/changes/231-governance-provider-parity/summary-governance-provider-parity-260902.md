---
issue: 231
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/231
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更改写两侧 Agent 技能（skill-for-claude、skill-for-codex、codex/skills）、VM 全局 Codex 指令与下游项目常驻指针模板的治理表述——去项目名、去交付形态实现名、把「Codex 默认主处理者 / Claude=开发、Codex=运维」统一为 provider 等价，并为 Claude 侧补齐 approved 后自主推进与暂停条件；属 Agent 行为与平台治理文件的合同变更，强制 complex，change_control=production 需 spec+plan
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-governance-provider-parity-260902.md
  spec: spec-governance-provider-parity-260902.md
  plan: plan-governance-provider-parity-260902.md
  verification: verification-governance-provider-parity-260902.md
confidence: high
override_reason: ''
depends_on: []
status: pr-open
branch: change/231-governance-provider-parity
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/234
created: 2026-09-02
updated: 2026-09-02
---

## 问题/需求总结

平台仓两侧技能与项目常驻指针模板对「谁是主处理者」互相矛盾：#207 把「Codex 默认主处理者 /
Claude Code 对等补位」写进了 `skill-for-claude/aisoft-platform/SKILL.md` 与 `skill-for-codex/SKILL.md`，
而 `templates/project/AGENTS.md` 仍是更早的「Claude=开发与设计 / Codex=维护与部署」。同时两侧技能
与模板残留具体项目名（NewEMaint、SFMDigitalBoard、HSDB、WMPDA、SapTableMigrate、rsdesign-new、
myapp、smoke-test）与交付形态实现名（docker-release/v2、PM2、Compose、Windows/IIS），把项目自己
该决定的事写进了平台治理。

2026-09-02 定案：平台只管流程管控；项目相关内容由项目自身决定；平台仓治理对 Claude Code 与
Codex 等价、不分主辅，目的是让两个模型互相取长补短、目标一致；过时表述及时清除。

本 Issue 的合同是 Issue #231 正文的「范围」「验收标准」「非目标」，本 summary 只做判级与路由。

## 影响范围

只改 Issue 正文列出的文件：

- Claude 侧：`skill-for-claude/aisoft-platform/SKILL.md`、`skill-for-claude/issue-session-flow/SKILL.md`
- Codex 侧：`skill-for-codex/SKILL.md`、`codex/skills/aisoft-matt-workflow/SKILL.md`、
  `codex/skills/issue-session-flow/SKILL.md`、`codex/global-AGENTS.md`
- 下游项目模板：`templates/project/AGENTS.md`（`templates/project/CLAUDE.md` 保持 `@AGENTS.md` 一行）
- 对应测试：`codex/tests/smoke.sh`（新增静态守卫）、`codex/tests/test-project-check.sh`（fixture 按新模板占位符改写）

不改 `skill-for-codex/references/*.md`、编号分册、README、根 `AGENTS.md`、`codex/runtime/`、broker
操作表、标签 manifest；不安装或更新任何全局 skills；不改动任何下游项目仓。

下游已接入项目的 `pointer-sections` 会因模板变化转为 GAP，属预期，各项目按 project-align 在自己的
Issue 跟进。

## 初步方案与建议

1. 模板瘦身：常驻指针两节删去 Gitea 版本号、merge-only ACL、credential custody、allowlist 等平台
   内部实现，只留项目需要知道的规则；「交付形态」占位符改成环境类别取值
   （Linux 容器化 / Linux 原生 / Windows / 其它），并对齐 `test-project-check.sh` 的 fixture 匹配。
2. 两侧技能与模板的「工具分工」统一为同一句：Claude Code 与 Codex 共用同一平台合同，能力等价、
   可互换、不分主辅；自动化 provider 仍由项目 profile 的 `ANALYSIS_PROVIDER`/`IMPLEMENT_PROVIDER`
   显式选择（默认 `none`）。Codex 侧英文技能使用同义英文表述。
3. Claude 侧两份技能各补一段「approved 之后默认自主推进」与「只在这些情况暂停」，语义与
   `codex/skills/issue-session-flow` 一致但不逐字复制；`aisoft-platform` 会话标准动作第 4–7 步各压缩为
   一行并指向 `06` 对应踩坑/章节编号。
4. 去项目化与去部署细节用 Issue 正文里的 grep 命令自证，并把这三条 grep 固化进 `smoke.sh` 作为静态
   守卫，防止回流。

## 风险

- 治理文件变更：本次运行遵循的是根 `AGENTS.md`，不在范围内；被改的是技能与下游模板，
  安装到本机的技能副本在本 Issue 内**不重装**（非目标），`check-drift.sh` 会如实报 DRIFT，
  重装是合并后独立的动作。
- 下游 `pointer-sections` 转 GAP 是预期后果，不在本 Issue 内批量修复。
- 平台仓自身对 `aisoft-project-check.sh --kind docs` 的 `pointer-sections` 在基线上已是 GAP
  （平台仓根 `AGENTS.md` 不含常驻指针两节、CLAUDE.md 与模板不同），本 Issue 不改变这一结果；
  「按新模板核对」的 PASS 证据由 `test-project-check.sh` 从新模板生成的对齐 fixture 提供。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 变更改写两侧 Agent 技能（skill-for-claude、skill-for-codex、codex/skills）、VM 全局 Codex 指令与下游项目常驻指针模板的治理表述——去项目名、去交付形态实现名、把「Codex 默认主处理者 / Claude=开发、Codex=运维」统一为 provider 等价，并为 Claude 侧补齐 approved 后自主推进与暂停条件；属 Agent 行为与平台治理文件的合同变更，强制 complex，change_control=production 需 spec+plan
risk_flags:
  - agent-governance
  - platform-governance
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue 正文自述「complex（Agent 行为与平台治理文件；强制规则）。change_control=production，需要 spec + plan」。
- 根 `AGENTS.md` 工作原则：「Agent 或平台治理变更一律按 complex 处理」；被改文件是安装到
  `~/.claude/skills/`、`~/.agents/skills/` 与 VM `AGENTS.md` 的 Agent 行为源，以及所有下游项目复制的模板。
- `contract_effect: change`：技能的触发条件、工具分工语义与下游模板的常驻指针内容都会改变，
  下游 `pointer-sections` 校验结果随之改变。
- `verification` 的声明依据是 `03` §3：本机 `check-drift.sh` 改动前 CLEAN / 改动后 DRIFT 的对比与
  AC1–AC3 的全仓 grep 属 required CI 不复现的一次性观测与本地扫描。

### 缺失的 acceptance criteria 或决策

- AC5 中「对平台仓自身仍 PASS」在基线上不成立（`pointer-sections` 与 `change-templates` 在 `origin/main`
  上已是 GAP，属平台仓结构性结果）。本 summary 采用的解读：平台仓结果与基线一致
  （`change-documents`/`change-pr-url` PASS，两项结构性 GAP 不变），新模板的 `pointer-sections` PASS
  由 `test-project-check.sh` 的对齐 fixture 证明。需在确认点 1 由人认可该解读。
