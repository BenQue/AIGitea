---
issue: 444
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/444
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - shared-core
  - external-contract
depends_on: []
git_scope:
  - 03-Issue-Spec-Plan与单闸门开发流程.md
  - 08-双工具共存与实施.md
  - AGENTS.md
  - GLOSSARY.md
  - codex/runtime/aisoft_loop/classification.py
  - codex/runtime/aisoft_loop/contract.py
  - codex/runtime/aisoft_loop/route_policy.py
  - codex/runtime/aisoft_loop/ticket_execution.py
  - codex/runtime/tests/test_classification.py
  - codex/runtime/tests/test_contract.py
  - codex/runtime/tests/test_route_policy.py
  - codex/runtime/tests/test_ticket_execution.py
  - docs/changes/444-dev-complex-plan-required/plan-dev-complex-plan-required-261110.md
  - docs/changes/444-dev-complex-plan-required/spec-dev-complex-plan-required-261110.md
  - docs/changes/444-dev-complex-plan-required/summary-dev-complex-plan-required-261110.md
  - docs/changes/444-dev-complex-plan-required/verification-dev-complex-plan-required-261110.md
  - docs/governance/review-evidence-index.md
  - skills/aisoft-matt-workflow/SKILL.md
  - skills/aisoft-platform/SKILL.md
  - skills/aisoft-platform/references/execution-adapter.md
  - skills/aisoft-platform/references/greenfield-planning.md
  - skills/aisoft-platform/references/onboarding-runbook.md
  - skills/aisoft-platform/references/route-policy.md
  - skills/gitea-analyze-change/SKILL.md
  - skills/gitea-development-loop/SKILL.md
  - skills/gitea-spec-plan/SKILL.md
  - templates/project/AGENTS.md
  - usage/CONTRACT.md
  - usage/bundle.json
branch: change/444-dev-complex-plan-required
created: 2026-11-10
updated: 2026-11-10
---

# 开发阶段 complex Issue 一律要求 plan

## 目标与原因

负责人裁决：开发阶段（`change_control: development`）的 complex Issue 一律写 plan。现行路由表「文档义务」只在
R2 含高风险 flag 时（D2）要求 plan，无高风险 flag 的 R2（D3）写简版 spec、不写 plan，由合成 `T01` 一次实现
spec 全部验收标准。批次 Issue（#440）往往覆盖多个功能点，一个合成 T01 没有切片、依赖与逐票验证，执行与审查
都不可分段。本变更让开发阶段 complex 与生产阶段一样按 plan 的 Txx 执行。

## 范围与非范围

范围：

- 路由表「文档义务」D3 的 plan 改为 `required`；spec 形态保持 D3 简版、D2 完整版（见未决问题 a）。
- runtime 读取同一张表：`document_obligations`、`Classification.route` 的 development complex 最小文档、
  确认点 1 文档预检、`ticket_execution` 的 plan 判定随之变化。
- 已批准、尚未完成且按旧规则未写 plan 的 D3 change 不被追溯阻塞（见未决问题 c）。
- 分册、技能、模板、使用合同、GLOSSARY 中「无高风险 flag 的 development complex 免 plan / 合成 T01」措辞同步；
  随使用发布包分发的成员改动发布 bundle 1.23.2。

非范围：

- 开发阶段 small（R5、D5）保持 plan `none`，不变。
- 推导表 R1–R5 的条件、process、method、confirm 与 C1 不变；R2 必用技能不变（见未决问题 b）。
- 生产阶段（R3/R4、D4）不变。
- 不回填、不改写任何项目仓已有 change 文档。

## Acceptance criteria

- [ ] AC-1：`route-policy.md`「文档义务」中 D2 与 D3 的 plan 都是 `required`；对无高风险 flag 的 development complex，
  `aisoft resolve-route` 的 `documents` 读回 `row: D3`、`plan: required`、`required_docs` 含 `plan`。
- [ ] AC-2：确认点 1 文档预检对未声明 plan 的新 development complex 报「summary required_docs 缺 plan（文档义务 D3）」；
  声明并创建 plan 后为 OK。
- [ ] AC-3：development small 的文档义务仍为 D5、`plan: none`，相关测试不变绿。
- [ ] AC-4：`ticket_execution` 对 status 已为 `approved`、文档义务为 D3、summary `required_docs` 未声明 plan 的
  旧合同仍以合成 `T01` 执行（不追溯）；对 D2 含高风险 flag 缺 plan 仍拒绝（#436 行为不变）；对声明了 plan
  却缺文件的仍拒绝。均有单测，并做一次反向证明（去掉兼容分支后对应测试变红）。
- [ ] AC-5：git_scope 列出的分册、技能、模板、使用合同与 GLOSSARY 中不再有「无高风险 flag 的 development complex
  不写 plan」的现行规则表述；合成 `T01` 只作为 D3 旧合同兼容路径描述。
- [ ] AC-6：`usage/bundle.json` 发布 1.23.2（`usage-bundle.sh --release`），bundle 校验通过。
- [ ] AC-7：`python3 -m unittest discover codex/runtime/tests` 与 `bash codex/tests/smoke.sh` 通过；未运行的写 NOT RUN。
- [ ] AC-8：平台仓 complex 交叉审查（Codex，未参与实现）对候选 head PASS，结论写进 verification 与
  `docs/governance/review-evidence-index.md`。

## 风险与回滚约束

- 已批准的 D3 旧合同若不加兼容会在执行入口被拒；AC-4 覆盖。项目只有升级到 1.23.2 后才受新规则约束。
- 回滚：revert 本 PR 并重新发布下一个 bundle 版本；已按新规则写的 plan 在旧规则下只是多出的可选文档，不阻塞。

## 接口、数据与兼容性影响

- `resolve-route` / `classify` 的 `documents` 输出对 D3 从 `plan: none` 变为 `required`，`required_docs` 多出 `plan`。
- `Classification.route(change_control="development")` 的 complex 最小文档从 summary+spec 变为 summary+spec+plan。
- 兼容判据只看已有字段（summary `status: approved` 与 `required_docs`），不新增 front matter 字段、不改模板。
- 使用发布包 1.23.1 → 1.23.2；项目升包后新开的 development complex 需要 plan。

## 未决问题

- a. 无高风险 flag 的 development complex 写简版还是完整版 spec？建议：简版（只改 plan，最小变更）。
- b. R2 必用技能是否加 `to-tickets` 与 `@plan`？建议：不加。plan 按文档义务写，执行入口已按 provider 默认落到
  `@plan`；改技能会让已批准的 development route 卡与重新解析结果不一致。
- c. 是否追溯已批准、未写 plan 的 development complex？建议：不追溯（AC-4 的兼容路径）。
