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
status: passed
branch: change/444-dev-complex-plan-required
created: 2026-11-10
updated: 2026-11-10
---

# 开发阶段 complex 一律要求 plan · 验证记录

## 基线与范围

- Commit SHA: `efc9019d1738390492395681d309d32b61c99837`（候选 head；之后只有本记录与审查索引的证据提交）
- 基线：起点 `origin/main` = `30c8994e`；开发中 #445 合并，以 merge commit 并入 `origin/main` = `70c2b1f7`
- 环境: macOS 本机，平台仓 change worktree `/private/tmp/issue-444-dev-complex-plan-required`
- 本记录负责证明的 acceptance criteria: AC-1 至 AC-8

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| `python3 -m unittest discover -s tests -t .`（codex/runtime，`07362dc`） | PASS | Ran 819 tests, OK |
| `bash codex/tests/smoke.sh`（`07362dc`） | PASS | rc=0，`Codex platform static smoke checks passed.` |
| 同上两项（`baf3605`，R1 修复后） | PASS | Ran 820 tests, OK；smoke rc=0 |
| 同上两项（`efc9019`，并入 main 并重发 1.24.0 后） | PASS | Ran 835 tests, OK；smoke rc=0 |
| `bash codex/tools/usage-bundle.sh --verify`（`efc9019`） | PASS | `VERIFIED 1.24.0 sha256:502c3e5b427cce0ddc7aad3b3d4d00fbdb29fab0e12f297a746701e7a38f08f7` |
| 反向证明：去掉 `ticket_execution` 兼容分支跑 `tests.test_ticket_execution` | 红→恢复后绿 | 去掉后 `test_small_rejected_and_development_uses_spec_without_plan` ERROR、`test_development_without_spec_ac_is_rejected` FAIL，均报 `route policy requires a mapped plan (文档义务 D3)`；恢复后 21 tests OK |
| `aisoft resolve-route 444 --provider claude` / `aisoft classify 444` | PASS | 路由与 summary 一致；文档预检 OK |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | route-policy D3 `lite`/`required`；`test_every_route_owes_a_spec_and_the_plan_follows_risk` 断言 D3 `required_docs` 含 plan |
| AC-2 | PASS | `test_preflight_requires_a_plan_for_development_complex`：缺 plan 报「缺 plan（文档义务 D3）」，补齐声明、映射、文件与 git_scope 后为 OK |
| AC-3 | PASS | D5 用例仍为 `lite`/`none` |
| AC-4 | PASS | `test_small_rejected_and_development_uses_spec_without_plan`（旧合同合成 T01）、`test_pre_444_compat_reads_only_the_approved_summary_fields`、`test_high_risk_development_without_a_plan_is_not_synthesized`、`test_d3_contract_declaring_a_plan_never_falls_back_to_t01`；反向证明见上 |
| AC-5 | PASS | rg 旧表述只剩 small 与旧合同兼容描述；交叉审查 R1 P2 指出的 SKILL.md:180 已修 |
| AC-6 | PASS | 1.24.0（minor）追加在 1.23.2 之后，verify 通过 |
| AC-7 | PASS | 见执行结果 |
| AC-8 | PASS | 交叉审查 R4 PASS，见下 |

## 交叉审查

审查方在 hc 终端 `review-444`（Herdr 标签页可见）运行 Codex，`-m gpt-6-astra -c model_reasoning_effort="high" -s read-only -a never`，界面读回 `GPT-6-Astra high`。

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex gpt-6-astra / high | `07362dc2fc49a5ffeea5a6e45a7230aa4275d6d1` | FAIL | P1 兼容判据分不清新旧 D3；P2 SKILL.md:180 残留免 plan；nit AC-2 缺正向断言。在 `baf3605` 修（P1 先加 created 截止） |
| 2 | Claude | Codex gpt-6-astra / high | `baf3605f46aaa5e2eea3e8c1b3c6c754e5b5f05c` | FAIL | P1 created 不能证明批准时间；P2 日期截止造成部分追溯。负责人选「只看字段」，在 `2ab7467` 撤回截止并写入 spec 决策 c |
| 3 | Claude | Codex gpt-6-astra / high | `2ab746780344492049659dfd952922d1db7d5187` | PASS | 无新发现 |
| 4 | Claude | Codex gpt-6-astra / high | `efc9019d1738390492395681d309d32b61c99837` | PASS | 集成复审：并入 #445 与重发 1.24.0，无发现 |

## 遗留风险与未完成项

- 已知取舍（负责人决定）：执行入口不能单独区分新旧 D3，新 D3 不写 plan 由确认点 1 文档预检拦截。
- 重装：合并后需按 issue-session-flow「平台仓重装读回」重装技能与 runtime（负责人 sudo 动作），读回 NOT RUN。
- 各项目升级到 1.24.0 为项目侧动作，本变更不代执行。
