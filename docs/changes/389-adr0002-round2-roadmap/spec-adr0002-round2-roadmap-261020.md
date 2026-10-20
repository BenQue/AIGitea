---
issue: 389
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/389
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - agent-governance
  - platform-governance
depends_on: []
status: approved
branch: change/389-adr0002-round2-roadmap
created: 2026-10-20
updated: 2026-10-20
git_scope:
  - docs/changes/389-adr0002-round2-roadmap/summary-adr0002-round2-roadmap-261020.md
  - docs/changes/389-adr0002-round2-roadmap/spec-adr0002-round2-roadmap-261020.md
  - docs/changes/389-adr0002-round2-roadmap/plan-adr0002-round2-roadmap-261020.md
  - docs/adr/0002-deterministic-development-flow.md
  - docs/governance/remediation-roadmap.md
  - docs/governance/platform-e2e-acceptance.md
  - README.md
  - AGENTS.md
---

# #389 spec：ADR 0002 确定性开发流程（路由合同与执行引擎分离）、第二轮路线与平台级 E2E 验收表

## 目标与原因

把 2026-10-20 的 D1 裁决写成仓内 ADR，作为第二轮 R10a（引擎退出）、R10b（路由卡）、R10c（外部技能三端一致）的共同依据；把第二轮批次与退出条件写进活路线图；建立平台级 E2E 验收表，让"平台是否真的被用起来"有一张可读回的表。

## 裁决输入（已齐，2026-10-20）

- D1（03:02Z）负责人原话：「按你的建议。判定开发强度，决定如何开发，确定开发的方案和计划和路线图都交给技能来处理就可以了」。即提案 a′：退出 VM 执行引擎，保留并升级路由合同，由技能承载。
- 03:30–03:41Z 续裁：Matt 定需求与计划、superpowers 开发；大需求先 `grill-me`；brainstorming 只在 how 未收敛时用；避免过度设计，路由表只钉必用与禁用；一套技能一套流程三端一致（D6，superpowers vendor pin，新增 R10c）；D4 a、D5 a、D7 a（#370 由 Codex 实现、Claude 审）、D8 a。
- 模型档位初始映射：Claude Code standard = Sonnet 5.5、frontier = Opus 5.5、max = Fable 5.1；Codex standard = 默认模型、frontier/max = 高推理档；Cursor 由项目 profile 选。

## Acceptance criteria

- [ ] AC-1 新增 `docs/adr/0002-deterministic-development-flow.md`，含「状态 / 日期 / 依据 / 决定 / 后果 / 重开条件」六节（背景并入依据）；决定一节是四条：路由合同是产品；VM 执行引擎退出；执行引擎三阶段与阶段 3 触发条件；合并永远是人；并逐字引用 D1 原话。
- [ ] AC-2 ADR 0002 写明路由卡字段（process、tier、effort、skills、method、verify、review、confirm）与推导表的合同形状，并写明：路由表单一来源在 `aisoft-platform` 技能的 references 内、只钉必用与禁用、其余技能模型自选；型号只在 `08` §7 按工具映射，合同只写档位；不新增 `route/*` 标签维度。具体落地归 R10b。
- [ ] AC-3 ADR 0002「后果」列出退出范围（Loop controller/provider/verifier、只服务 Loop 的 `codex/agent` 脚本、`codex/systemd/`、`install-vm.sh`、routine merge 与 pilot schema、`vm.profile.*`）与保留范围（判级规则引擎、文档合同、会话工具），并指向 R10a、R10b、R10c；不在本批删除任何文件。
- [ ] AC-4 ADR 0002「重开条件」写明阶段 3（Mac 上 headless implement，只对 small-direct）的三个触发条件：E2E 表有行、某项目 small 占比 ≥ 30% 且月度 ≥ 10 条、阶段 2 稳定一个月；只在 Mac 重建，不回 VM，不恢复 routine 自动合并。
- [ ] AC-5 `docs/governance/remediation-roadmap.md` 追加「第二轮」表（R9、#370、R10a、R10b、R10c、R11–R16），每行有批次、内容、依赖、状态四列；表后列四条第二轮退出条件；「推荐顺序」末句改为 R8 之后的实际状态并给出第二轮顺序。第一轮表与总规则不改。
- [ ] AC-6 新增 `docs/governance/platform-e2e-acceptance.md`：列为项目、发布包版本、日期、覆盖阶段、证据、未覆盖；首行为 NewEMaint #279 M1（发布包 1.2.0；构建、发布、test 部署、健康 SHA、同版本 noop、回滚；证据 NewEMaint PR 308 verification、GitHub run 39118940079、Release 416386339、公司 Gitea run 6/10/13；未覆盖 database restore 与生产）。
- [ ] AC-7 `README.md` 导航表有 ADR 0002 与 E2E 验收表入口，整改路线一行改为 R0–R16；不新增项目名（泄漏守卫基线只降不升）。
- [ ] AC-8 `AGENTS.md` 加 ADR 0002 指针，单独 commit，文件仍 ≤ 5 KB。
- [ ] AC-9 `bash codex/tests/smoke.sh` 全绿；Codex 以 `codex exec -s read-only` 对候选 head 审查 PASS，结论写项目库 `codex-review-389.md`。

## 接口、数据与兼容性影响

无代码、schema、broker、manifest、技能或发布包成员变化；发布包不升版。ADR 0002 不撤销 ADR 0001 的任何决定，只把 ADR 0001 D1 表中 K3 的 "Controller" 与 K2 的 "routine merger" 标为"按 ADR 0002 退出，由 R10a 执行"。

## 风险与回滚约束

风险是决定措辞偏离裁决，导致 R10a/R10b 照错的合同执行；以逐字引用与交叉审查缓解。回滚为 revert 本 PR，无运行时影响。

## 非目标

不删代码、不改 manifest、不碰 VM、不改技能、不改 `03`/`04`/`08` 正文（分别归 R10a、R10b、R14）、不补 `GLOSSARY.md`（R14）。

## 未决问题

无。
