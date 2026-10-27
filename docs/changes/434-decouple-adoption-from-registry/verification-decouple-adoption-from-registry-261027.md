---
issue: 434
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/434
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - authorization
  - authentication
  - shared-core
  - agent-governance
  - platform-governance
  - external-contract
  - artifact
depends_on: []
status: pending
branch: change/434-decouple-adoption-from-registry
created: 2026-10-27
updated: 2026-10-27
---

# Verification：通用流程采用与中央项目登记解耦

## 基线与范围

- Commit SHA：逐票记录在下表
- 基线：`origin/main` = `74dc5808`
- 环境：Mac 交互会话（Claude），平台源码 runtime；不连 live Gitea，不重装 broker
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-8

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| T01 `bash codex/tests/smoke.sh`（发版 1.18.0 后） | PASS | 尾行 `Codex platform static smoke checks passed.`。首轮依次红在发布包成员不一致、导出技能在非维护层节点名平台路径、站点值渗入守卫（`gitea-ci`），逐项修正后转绿 |
| T01 残留表述 rg（`登记与采用|先.{0,6}登记|必须先登记|新项目登记|登记新项目|已注册项目|登记进平台`，排除 `docs/changes`、`archive`、`codex/vendor`、`usage/releases`） | 已判定 | 见下表 |

T01 残留表述判定：

| 位置 | 判定 |
|---|---|
| `AGENTS.md:8`「换成任意一个已注册项目还成立吗」 | 保留：平台维护层的准入问法，与 ADR 0001 D4 同源，不构成采用前置；本 spec 未授权改 `AGENTS.md` |
| `docs/adr/0001-platform-boundary.md:49`、`:81` | 历史决策原文保持；ADR 0003 补充而不撤销 |
| `docs/governance/remediation-roadmap.md:22` | 历史整改路线证据，保持原样 |
| `architecture/README.md:250` | 描述 reference profile 不对应任何项目，与登记前置无关 |
| `docs/adr/0003-*` 命中 | 本 ADR 引述被取代的旧条款 |
| `greenfield-planning.md:12`、`:18` | 已改为「采用」，去掉登记前置 |
| 技能、getting-started、onboarding-runbook、project-align、execution-adapter、issue-session-flow、使用合同、用户手册、项目 AGENTS 模板 | 已改为三层职责；保留的 broker 表述均限定为站点来源或「当前来源的 typed 操作入口」 |

命令与输出照实抄。改动前才观测得到的证据（基线状态、改动前后对比、先看着测试红）
只有写在这里才留得下来——改动合并后就无法重放。

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | 待填写 | 待填写 |

## 交叉审查

仅平台仓 complex 变更保留本节（`03` §7「交叉审核」）；项目仓整节删除。每轮一行，`exact head` 写 40 位 SHA，
实现方与审查方不能是同一提供者。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 合同 1 | claude | codex（gpt-6-astra，high，只读） | f2f24f022ebd670224583c20ababe2270a64a1fd | REJECT | 3 BLOCKER（direct 写入前无身份硬门；无登记后项目策略无机读来源；installer 约束自相矛盾）、10 MAJOR、1 MINOR，共 14 条。处置：放弃另写 direct 传输，改为同一 broker 引擎加项目自声明来源（spec D3–D7），治理先行（plan T01），补全入口清单、反例、回滚与未验证边界，修复本文件模板残片 |
| 合同 2 | claude | codex（gpt-6-astra，high，只读） | fcd5eacfbe0bd63260f5e8a2216837416ae74a63 | REJECT | 第 1 轮 14 条：6 RESOLVED、8 PARTIAL。新发现 1 BLOCKER（单项目来源最小合同与站点入口边界未定）、6 MAJOR（路由 change_control 与模板 git_scope 消费者；身份检查只在项目来源且绑定同一凭据；project-check 站点不变与项目分支冲突；发布包依赖闭包与入口表；complete 只 dry-run；不存在的同号重发）、2 MINOR（D7 证据格式；轮 1 计数笔误）。处置：spec 新增项目上下文映射表与入口操作闭集表，站点 wrapper 固定站点来源、新增项目入口 aisoft-access；身份检查限项目来源、同一内存凭据经注入助手供 Git 写入、按完整 origin 判重定向、写明 PAT scope；project-check 两来源分支与 MANUAL 结果值；路由读项目 change_control，模板持有路径在项目来源拒绝；AC-3 增 review-candidate、complete --apply 幂等与 development 路由；AC-7 列依赖闭包；发版改为逐票递增；D7 证据字段与 protection_evidence；更正计数 |
| 合同 3 | claude | codex（gpt-6-astra，high，只读） | dd50967aa5b12130e3019c123e8e7f48c8d9a372 | ACCEPT WITH CHANGES | 第 2 轮 9 条全部 RESOLVED；无 BLOCKER、无 MAJOR。3 条 MINOR 已处置：AC-3 第 9 步注明只证明路由消费、推送仍要求 spec；open-pr 编号沿用 pull.create 回执，删去 pulls.read；删去开放式薄包装预留，只保留 labels-provision |
| 实现 | 待填写 | 待填写 | 待填写 | NOT RUN | 待填写 |


## 遗留风险与未完成项

合格标准：每条 acceptance criterion 都有一条真实执行过的命令或一次真实观测支撑；
不得把 `NOT RUN` 改写为通过；不可达的环境与未执行项在此显式写明。
