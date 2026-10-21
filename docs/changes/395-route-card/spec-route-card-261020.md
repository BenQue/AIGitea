---
issue: 395
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/395
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
depends_on:
  - 389
  - 391
  - 392
status: approved
branch: change/395-route-card
created: 2026-10-20
updated: 2026-10-20
git_scope:
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 08-双工具共存与实施.md
  - codex/config/change-template-sync.json
  - codex/runtime/aisoft_loop/contract.py
  - codex/runtime/tests/test_contract.py
  - codex/runtime/tests/test_route_policy.py
  - codex/tests/smoke.sh
  - docs/changes/395-route-card/plan-route-card-261020.md
  - docs/changes/395-route-card/spec-route-card-261020.md
  - docs/changes/395-route-card/summary-route-card-261020.md
  - docs/changes/395-route-card/verification-route-card-261020.md
  - docs/governance/remediation-roadmap.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/route-policy.md
  - skills/issue-session-flow/SKILL.md
  - templates/docs/changes/_template/summary.md
  - usage/bundle.json
---

# R10b 路由卡：判定强度、方法、技能与审查由技能按确定性表得出

## 目标与原因

ADR 0002 D1：每条 Issue 的开发方式由确定性的路由卡给出，由技能承载，不由模型自由决定。R9 只给了字段与推导表的形状；本票定稿逐格取值、必用与禁用清单，让 summary 携带 `route:`，在确认点 1 与派单任务书展示它，并把档位到型号的映射写进 `08`。三条原则：判定强度与路线交给技能；避免过度设计（只钉必用与禁用，其余技能模型自选）；一套技能一套流程，三端一致。

## 路由表（`route-policy.md` 的内容合同）

**查表输入**：summary 的 `effective_complexity`、`change_type`、`contract_effect`、`risk_flags`、`confidence`，仓库的 `change_control`（manifest，缺省 `production`），以及仓库角色（平台仓 `admin/aisoft-platform` 或项目仓）。复杂度本身仍由 `classification.py` 的规则引擎判定，路由表只做映射。

**高风险 flag**：`security`、`authentication`、`authorization`、`schema-change`、`data-migration`、`external-contract`、`shared-core`、`ci-integration`、`ci-change`、`artifact`、`deployment`、`deployment-boundary`、`rollback`、`agent-governance`、`platform-governance`；`change_type` 为 `security` 或 `data` 视同含高风险 flag。`functional-change`、`cross-module`、`cross-service` 强制 complex 但不算高风险。

| 行 | 条件（自上而下取第一行命中） | process | tier / effort | method | verify | review（平台仓 / 项目仓） |
|---|---|---|---|---|---|---|
| R1 | 判级未决：无 `effective_complexity`、`contract_effect: unclear` 或 `confidence: low` | awaiting-triage | frontier / high（只分析） | none | none | none / none |
| R2 | complex 且 `change_control: development` | complex-development | frontier / high | tdd（合成 T01） | full | human-merge / human-merge |
| R3 | complex，`production`，含高风险 flag | complex-production | frontier / max | spec-plan | full+reverse-proof | cross-provider / human-merge；含 `security`/`authentication`/`authorization` 或 `type/security` 时平台仓为 cross-provider+security |
| R4 | complex，`production`，无高风险 flag | complex-production | frontier / high | spec-plan | full；`required_docs` 含 `verification` 时 full+verification | cross-provider / human-merge |
| R5 | small | small-direct | standard / medium | `type/bugfix` 为 debug-first，其余 implement-only | targeted | human-merge / human-merge |

`confirm` 恒为 `2`。

**skills（只列必用）**：

| 行 | 必用 |
|---|---|
| R1 | `triage`；Issue 说不清时 `grill-me` |
| R2 | `verification-before-completion` |
| R3、R4 | `to-spec`、`to-tickets`、`executing-plans`、`verification-before-completion`；项目仓 R3 另加 `code-review` |
| R5 | `verification-before-completion` |
| 大需求（R3/R4 中 `change_type: feature` 或 `contract_effect: add`，或一个阶段要拆多个 Issue） | 在最前面加 `grill-me` |

**禁用与限制**（全部 process 适用）：superpowers `writing-plans` 不替代 Matt `to-tickets` 的 Txx 计划；`brainstorming` 不自行定级，只在 how 未收敛时用、只问 how、结论写进 spec「方案与决策」节；`subagent-driven-development` 只许顺序派发；`dispatching-parallel-agents` 只做只读调查；并行子代理不写同一 change worktree；`finishing-a-development-branch` 的本地 merge、push、建 PR 不可用。

**默认入口（不是硬规则）**：v3 §1.2 的重叠表——定需求 Matt、定方案默认 Matt（how 未收敛时 brainstorming 或 Matt `prototype`）、出计划 Matt、按计划执行 superpowers（Codex 用 Matt `implement`）、TDD 与排错按工具、完成前核验 superpowers（Codex 由 `issue-session-flow` 的「验证：真实结果 / NOT RUN」承担）、审查与 worktree 收尾按平台技能。其余技能由模型按 Issue 自选，verification 写明用了什么。

**档位到型号**（写在 `08` §7，路由表只引用）：Claude Code `standard = Sonnet 5.5`、`frontier = Opus 5.5`、`max = Fable 5.1`；Codex `standard = 默认模型`、`frontier/max = 高推理档`；Cursor 由项目 profile 选。`effort` 是推理强度，与 tier 独立。派单卡片由人按 tier 选型号。

## 实现选择（确认点 1 一并确认）

1. **`route:` 在 front matter 里的形状**：与 `documents:` 同样的两空格缩进映射，值都是标量；`skills` 写成逗号分隔的一行（`_safe_scalar` 禁 `[ ]`，嵌套列表要扩展解析器的第三层，不值得）。备选是扁平的 `route_process:` 等八个键，不需要改解析器但偏离 ADR 0002 的形状，不采用。
2. **`route:` 是可选块**：已有 179 个 change 没有它，`check-change-documents` 只在存在时校验；模板与新 summary 都带它。必须性留给 R11 的 `aisoft classify`。
3. **大需求链与 small 的真实走通放到后续批次的 verification**：本票自身（真实 complex，R3 行）在 PR 前走完确认点 1 展示、`executing-plans` 按 Txx 顺序执行、Codex 独立查表；真实 small 由 R11 的项目采用 Issue（D4，判 small）承接；`type/feature` 大需求链由合并后第一条 `type/feature` Issue 承接；本票 verification 列出这两项为 NOT RUN 并写明承接处。

## Acceptance criteria

- [ ] AC-1 `skills/aisoft-platform/references/route-policy.md` 存在且内容与上节逐格一致；`08` §7.1 的五类 classifier case 各查一次表，得到的 `route:` 与表逐格一致（新测试 `test_route_policy.py` 解析该文件做断言）。
- [ ] AC-2 front matter 解析接受 `route:` 映射；`check-change-documents` 对 `process`/`tier`/`effort`/`method`/`verify`/`review` 的非闭集取值、`confirm` 不为 2、未知子键、`process` 与 `effective_complexity` 矛盾（small ↔ small-direct，complex ↔ complex-*，无 → awaiting-triage）都拒绝；没有 `route:` 的旧 change 不受影响（全量 `check-change-documents` gap=0）。
- [ ] AC-3 summary 模板带 `route:` 块，`change-template-sync.sh --verify-digest` 通过。
- [ ] AC-4 `aisoft-platform` SKILL.md「现行合同」有「路由」节（`$triage` → 判级 → 查表得 `route:` → 写 summary 与判级评论 → 确认点 1 展示，人可覆盖并记 `override_reason`）；`issue-session-flow` 确认点 1 候选格式有「路由」行，派单任务书含 process/tier/skills 并写明按 tier 选型号，调度会话写明路线图产出物沿用 `docs/governance/remediation-roadmap.md` 的表形。
- [ ] AC-5 `03` §2 有「路由」小节（含大需求链：`grill-me` → `to-spec` →（how 未收敛时 `brainstorming` 或 `prototype`）→ `to-tickets` → 开发，grill 与 brainstorming 都在确认点 1 之前）；`08` §5 superpowers 映射补 brainstorming、executing-plans、subagent-driven-development、verification-before-completion 四行；`08` §7 有模型档位表并写明「型号按工具映射，合同只写档位」。
- [ ] AC-6 smoke 有路由表结构守卫（文件存在、五行齐全、tier/effort/method/verify/review 取值闭集），删掉一行或写入闭集外取值时 smoke 变红（反向证明记 verification）。
- [ ] AC-7 本 Issue summary 的 `route:` 通过 `check-change-documents`；实现按 plan 的 Txx 顺序用 `executing-plans` 执行，每张 ticket 的 commit 记 verification；Codex 只读会话对本 Issue 独立查表得到同一路由卡。
- [ ] AC-8 `bash codex/tests/smoke.sh` 全绿；`usage-bundle.sh --release 1.5.0` 后 `--verify` 通过；`bash -n` 与 ShellCheck 通过；Codex 只读交叉审查 PASS；判级投影读回 `projected`。
- [ ] AC-9 #392 Cursor 一行的更正（2026-10-20 14:48Z 实测 PASS）记在本票 verification：broker 的 Git scope 闸门不允许一个 Issue 改另一个 Issue 的 `docs/changes/` 目录（实现中由 Codex 审查发现，确认点 2 告知负责人）；路线图 R10b 行更新状态。

## 接口、数据与兼容性影响

- front matter 合同新增一个可选映射键，旧文档不变；broker 的 `git_scope` 与 summary 读取用列 0 锚定正则，不受缩进子键影响（子键不得命名为 `spec`）。
- 发布包成员新增 `route-policy.md`，升 1.5.0；下游项目按 pin 版本核对，不会自发变红。
- 不改 broker、installer 与 manifest，合并后不需要两台重装 broker；技能需重装（`install-skills.sh`、`skill-for-claude/install.sh`）。

## 风险与回滚约束

整 PR revert 即回滚；旧 change 没有 `route:`，revert 后不会有文档因此变红。治理文件（技能、`03`、`08`）先单独 commit 并停止，fresh 重读后再改 runtime。

## 非目标

不写新的 runtime 判级代码；不新建 daemon；不自动选模型；不加 `route/*` 标签维度；不生成机器读 JSON；不改 `analysis.py`/`apply-analysis`；不改 Codex 的 superpowers 来源（`PIN_NOT_INSTALLED` 如实记录）；R10a 交接留给 R11、R16 的遗留不处理。

## 未决问题

无。
