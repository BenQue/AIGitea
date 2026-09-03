---
issue: 233
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/233
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
reason: 清除平台仓活文档中已兑现的接入条件、已退役身份的条件句、以 Codex-first 为前提的章节与只剩历史意义的状态条目，把历史证据迁入 archive/；改写必须保持判级规则、命名元组、单闸门、broker 路径与 routine merge 条件的语义等价（contract_effect=unchanged）。但范围触及安装到两侧的 Agent 行为源（skill-for-codex/SKILL.md、references、codex/skills）、根 AGENTS.md 目录段与 smoke.sh 守卫，命中 Agent/平台治理强制规则，effective complexity=complex；change_control=production 需 spec+plan
risk_flags:
  - agent-governance
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-prune-stale-docs-260902.md
  spec: spec-prune-stale-docs-260902.md
  plan: plan-prune-stale-docs-260902.md
  verification: verification-prune-stale-docs-260902.md
confidence: high
override_reason: ''
depends_on:
  - 231
  - 232
status: pr-open
branch: change/233-prune-stale-docs
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/236
created: 2026-09-02
updated: 2026-09-03
---

## 问题/需求总结

平台仓的活文档仍保留一批已经兑现或已经退役的表述：

- `08-Codex双工具共存与实施.md` §8「Claude Code 接入条件」把 Claude adapter 写成尚未发生的前置条件，
  而 Claude adapter 已随 Issue #1 完成并通过 17 项 parity 测试；§1 与 `04` §3 的组件图仍写
  「Codex adapter（先验证）/ Claude adapter（后接入）」，`04` §10 标题仍是「Codex-first 验证顺序」，
  README §5 导航行仍叫「08-Codex-first 与双工具共存」。
- `skill-for-codex/SKILL.md` 与 `references/onboarding-runbook.md` §1.2 仍保留「After Issue #35 is merged
  and its live rollout is explicitly authorized…」与整段「Legacy `ci-bot` collaborator gate（迁移期）」；
  #35 已 `deployed`，共享 `ci-bot` 已退出全部 manifest 仓库（`06` §「旧 `ci-bot` gate（已退役）」）。
  `codex/skills/gitea-platform-ops/SKILL.md` 第 8/10 条、`04` §11「最小权限 ci-bot」、`06` 四处
  「Issue #N 发布后」同属已兑现的条件句。
- README §1「当前状态」有 11 条 ✅ 条目只剩历史意义（#21 主机职责收口、legacy 制品收口、prod-sim
  退役、v2 试点 #4、Windows/内网目标设计、Docker release evidence 等）。
- `09` 保留规划与决策演进，但没有一张「哪些已落地到哪个文件、哪些仍未实施」的对照。
- #232 给 02/12–15 加的定位说明以「去留由后续过时文档清理 Issue 处置」收尾，本 Issue 就是该 Issue，
  必须给出判定并把这句条件句本身收掉。

2026-09-02 定案：平台着重流程管控，项目相关内容由项目自身决定，平台更通用化；Claude Code 与 Codex
等价、不分主辅；过时的文档和概念要及时清除。活文档只描述当前合同，历史证据归 `archive/`。

本 Issue 的合同是 Issue #233 正文的「初始盘点」「验收标准」「非目标」；验收第 1 条要求 spec 先给出
逐条清单（文件、行号、处置），第 5 条要求 spec 逐条对照改写前后合同语义等价。本 summary 只做判级与
路由（Matt `$triage` 的输出）。依赖 #231（PR #234，merge `aefb1358f4063cc23e36ab6bdc827ebc47eff915`）
与 #232（PR #235，merge `0df92177497c1b4b16d9ed0c0bc5780849d7e7fb`）均已合并，本变更在其之上。

## 影响范围

- 编号分册：`08-Codex双工具共存与实施.md`（改名为 `08-双工具共存与实施.md`，§1/§4/§7/§8/§10 改写）、
  `04-Agent编排与定时任务.md`（§3 组件图、§10 标题与第 8 条、§11 第 1 条）、`06-运维手册与踩坑集.md`
  （四处「发布后」条件句改现在时）、`09-v3平台简化与Loop-Engineering文档改造规划.md`（header、新增
  §0.2 落地对照、§9 文件名同步）、`02`、`12-Linux…`、`12-Windows…`、`13`、`14`、`15`（仅定位 blockquote
  尾句改为本 Issue 的判定）。
- 总纲与治理：`README.md`（header 日期、§1 状态条目迁出与合并、§5 导航行）、根 `AGENTS.md` 目录段
  （`08` 与 `archive/` 两行，独立原子 commit）。
- 两侧技能安装内容：`skill-for-codex/SKILL.md`、`skill-for-codex/references/onboarding-runbook.md`、
  `skill-for-codex/references/private-gitea-access.md`、`codex/skills/gitea-platform-ops/SKILL.md`。
- 测试：`codex/tests/smoke.sh`（#231 AC-1 项目名守卫扩展到 `skill-for-codex/references/*.md`；删除断言
  退役 gate 块字面量的一条陈旧检查）。
- 归档：新建 `archive/平台状态历史-20260902.md`，`archive/README.md` 加一行索引，
  `archive/11-Codex-Loop运行时实施计划.md` 第 5 行链接目标随 `08` 改名同步（只改链接目标，不改正文）。

不改 `docker-release/`（#65 冻结）、`architecture/`、`codex/runtime/`、`codex/tools/`、broker 操作表、任何
manifest、`templates/`、下游项目仓；不删除 `archive/` 已有内容；不安装或更新全局 skills。

## 初步方案与建议

1. 按 spec 清单逐条处置：删除（已兑现的接入条件、退役 gate 段落）、迁 archive（README §1 与 `08` §4 的
   历史状态条目）、改为现在时（「Issue #N 发布后」「合并后才」等条件句）、改为 provider 中性表述
   （Codex-first / 先后顺序）。
2. `08` 改名为 `08-双工具共存与实施.md` 并同步全部引用；用链接检查脚本证明仓库内无悬空 `.md` 链接。
3. 12–15、02、`docker-release/`、`architecture/` 判定为保留原位（参考实现/设计，#232 已移出主线并标注
   性质），只把定位说明的尾句改为本 Issue 的判定，不再留「由后续 Issue 处置」。
4. `smoke.sh` 的项目名守卫扩展到 `skill-for-codex/references/*.md`（先清掉两处命中），交付形态名守卫
   不扩展（references §4/§9 必须列出 architecture `delivery_contract` 的取值）。
5. 验收用 Issue 正文的 grep、链接脚本、smoke、project-check 自证；语义等价用 spec 的对照表加
   `git diff` 证明五类合同的定义段落未被触及。

## 风险

- 治理文件：根 `AGENTS.md` 只改目录段两行，作为独立原子 commit（与 #232 T03 同处置），工作原则段
  一字不动；本变更没有依赖该目录段的 runtime 实施。`skill-for-codex/SKILL.md`、`codex/skills/*`、
  references 是安装到两侧的 Agent 行为源，改动后本机 `check-drift.sh` 会 DRIFT；本 Issue 不重装。
- 语义等价：被改写的句子都不是判级规则、命名元组、单闸门、broker 路径或 routine merge 条件的定义
  处；spec 用对照表逐条证明，并用 `git diff` 证明 `03` 全文、README §3/§4、runbook §1.1 第 36–41 行
  等定义段落无 diff。
- 改名：`08` 的引用分布在 README、AGENTS、`09`、`archive/11`（链接）与若干历史代码跨度；只同步链接
  与活文档引用，历史代码跨度不改。
- 超出初始盘点的补全（`08` §4 历史状态迁 archive、`06` 四处条件句、`04` §3 组件图与 §11、
  `gitea-platform-ops` 两条、`private-gitea-access` 一处项目名）在 spec 中单列，确认点 1 一并认可。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: unchanged
reason: 清除平台仓活文档中已兑现的接入条件、已退役身份的条件句、以 Codex-first 为前提的章节与只剩历史意义的状态条目，把历史证据迁入 archive/；改写必须保持判级规则、命名元组、单闸门、broker 路径与 routine merge 条件的语义等价（contract_effect=unchanged）。但范围触及安装到两侧的 Agent 行为源（skill-for-codex/SKILL.md、references、codex/skills）、根 AGENTS.md 目录段与 smoke.sh 守卫，命中 Agent/平台治理强制规则，effective complexity=complex；change_control=production 需 spec+plan
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

- Issue 正文自述「complex（平台治理文档；强制规则）。change_control=production，需要 spec + plan；spec
  必须先给出逐条清单」。
- 根 `AGENTS.md` 工作原则：「Agent 或平台治理变更一律按 complex 处理」；被改的 `skill-for-codex/SKILL.md`
  是 #231 定义的 7 份治理文件之一，references 与 `codex/skills` 由安装脚本复制为 Agent 行为，
  `smoke.sh` 守卫是测试硬门。
- `contract_effect: unchanged`：Issue 验收第 5 条要求不改变任何合同语义；所有处置都是删除已兑现条件、
  迁出历史、改时态或改 provider 中性措辞。
- `verification` 的声明依据是 `03` §3：基线 grep 命中、链接检查、`check-drift.sh` 前后状态与 smoke 守卫
  反向证明属 required CI 不复现的一次性观测。

### 缺失的 acceptance criteria 或决策

- 无。四项解读（a）`08` 改名及 `archive/11` 第 5 行链接目标同步；（b）超出初始盘点的补全项 A-04、A-11、
  B-10～B-13；（c）12–15、02、`docker-release/`、`architecture/` 保留原位；（d）`smoke.sh` 项目名守卫扩展到
  references、交付形态名守卫不扩展——已于 2026-09-03 确认点 1 由人认可。
