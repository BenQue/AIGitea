---
issue: 442
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/442
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - shared-core
  - external-contract
depends_on: []
git_scope:
  - codex/config/change-template-sync.json
  - codex/runtime/aisoft_loop/classification.py
  - codex/runtime/aisoft_loop/contract.py
  - codex/runtime/aisoft_loop/route_policy.py
  - codex/runtime/tests/test_classification.py
  - codex/runtime/tests/test_contract.py
  - codex/runtime/tests/test_route_policy.py
  - codex/tests/test-aisoft-entry.sh
  - codex/tools/aisoft
  - docs/changes/442-confirm-route-visibility/plan-confirm-route-visibility-261109.md
  - docs/changes/442-confirm-route-visibility/spec-confirm-route-visibility-261109.md
  - docs/changes/442-confirm-route-visibility/summary-confirm-route-visibility-261109.md
  - docs/changes/442-confirm-route-visibility/verification-confirm-route-visibility-261109.md
  - docs/governance/review-evidence-index.md
  - templates/docs/changes/_template/summary.md
  - usage/bundle.json
branch: change/442-confirm-route-visibility
created: 2026-11-09
updated: 2026-11-09
---

# classify/resolve-route 显示 confirm 与 change_control，route.skills 写法给出明确提示

## 目标与原因

#440 在 LocalWMS（`change_control: development`）试跑时暴露三处可见性缺口：确认点 1 候选的「路由」行看不出
`confirm`；`resolve-route` 不说它按哪个阶段解析，排查 `confirm` 取值要另行推断；summary 把 `route.skills`
写成 YAML flow 列表 `[a, b]` 时只得到 `unsafe YAML scalar at line N`，看不出正确写法。三处都只是输出与提示，
不改路由规则、确认点语义或解析器接受的语法。

## 方案与决策

- **D1 classify 路由行带 confirm。** `codex/tools/aisoft` 的 `route_card` 在路由行末尾追加 `· confirm <值>`，
  值取 summary `route.confirm`。缺 `confirm` 的卡在 `resolve_summary` 的合同校验处就被拒绝（路由行改为「读不出映射
  summary」并给出 `route keys must be exactly …`），所以展示层不设兜底、不猜缺省值（交叉审查 R1 P2）。
- **D2 resolve-route 输出 change_control。** `route_policy.resolve_issue_route` 在结果里加顶层 `change_control`，
  值就是 `repository_context` 实际交给 `resolve_route` 的那个阶段（`project.json` 声明优先，否则按仓库名解析）。
  只加字段，不改已有字段。
- **D3 route.skills 不放开 flow 列表。** 受限 YAML 解析器保持 fail closed（与「守卫读 Markdown 要 fail closed」一致），
  不新增 flow 列表语法。`contract._safe_scalar` 与 `classification._parse_scalar` 在值以 `[` 开头时，把错误信息改为
  写明「不支持 YAML flow 列表；列表用块列表，`route.skills` 写逗号分隔一行，例 `skills: to-spec, executing-plans`」；
  其它不安全字符的报错保持原样。summary 模板在 `route:` 上方的 HTML 注释里写同一提示（front matter 内不加 YAML 注释）。
- **D3a 模板 digest。** 模板一改，`codex/config/change-template-sync.json` 钉住的 digest 同 PR 用
  `change-template-sync.sh --refresh-digest` 刷新（smoke 硬门）；下游副本随项目采用 1.23.1 同步，不在本票改下游。
- **D4 发布包 1.23.1（patch）。** `codex/tools/aisoft`、`route_policy.py`、`contract.py`、`classification.py` 与 summary 模板
  都是 exact 成员；按发布规则同 PR `usage-bundle.sh --release 1.23.1 --compatibility patch`，notes 写明仅输出与提示变化。

## 范围与非范围

范围：`git_scope` 所列文件。

非范围：不改路由表、`confirm` 语义、`change_control` 解析、broker、`open-pr`；不放开解析器语法；
不改技能与使用合同正文（`execution-adapter` 对 resolve-route 的描述已写「读取仓库 change_control」，不需改动）；
不批改存量 summary。

## Acceptance criteria

- [ ] AC-1 `aisoft classify N` 的路由行以 `· confirm 1` 或 `· confirm 2` 结尾，取自 summary；`test-aisoft-entry.sh` 钉住。
- [ ] AC-2 `resolve_issue_route` 结果含 `change_control`，development 声明的检出为 `development`，平台仓为 `production`；有单测。
- [ ] AC-3 summary 里 `route.skills: [a, b]` 仍被拒，错误信息含「flow」与逗号分隔示例；`[` 以外的不安全字符报错不变；
  classification 解析器同样。有单测与反向证明（去掉提示分支后断言变红）。
- [ ] AC-4 summary 模板写明 `route.skills` 逗号分隔；发布包 1.23.1 发布并 `--verify`；`bash codex/tests/smoke.sh` 全绿。
- [ ] AC-5 平台仓 complex 交叉审查：Codex（未参与实现）只读审查候选 head 至 PASS，记录进 verification 与审查证据索引。

## 风险与回滚约束

- 风险：有脚本按全文匹配 classify 路由行。缓解：只在行尾追加，前缀不变（现有 `expect_contains` 前缀钉子仍成立）。
- 回滚：revert 本 PR 并按 `origin/main` 重发上一版；项目回到 1.23.0 即恢复原输出。

## 接口、数据与兼容性影响

- classify 输出与 resolve-route JSON 只增不改；解析器接受的语法不变，只改错误文本。无数据迁移。

## 未决问题

无。
