---
issue: 134
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/134
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - shared-core
depends_on: []
status: pr-open
branch: change/134-change-control-phase
pr_url: ''
created: 2026-08-21
updated: 2026-08-21
---

# Verification · 按交付阶段分级 required_docs（#134）

执行日期：2026-08-21 · 分支 `change/134-change-control-phase` · 基线 `origin/main` = `51784f4`

## AC-1 · schema 校验 fail closed

`change_control` 取以下非法值时 `load_contract` 均抛 `ContractError`，无一静默回落：
`""`、`"dev"`、`"Development"`、`"staging"`、`true`、`1`、`null`。

可选键的放行未退化为「任意键都接受」：向 repository 条目注入 `unexpected_key` 仍被
`_exact_keys` 以 `keys mismatch` 拒绝。

## AC-2 · 既有仓库行为不变

manifest 中 10 个仓库（aisoft-platform、HSDB、LocalWMS、myapp、NewEMaint、rsdesign-new、
SapTableMigrate、SFMDigitalBoard、smoke-test、WMPDA）全部解析为 `change_control=production`、
`in_development=False`。

## AC-3 · 判级输出

| analyzer 的 required_docs | 阶段 | route 输出 |
|---|---|---|
| `summary, spec, plan, verification` | production | `summary, spec, plan, verification` |
| `summary, spec, plan, verification` | development | `summary, verification` |
| `summary, spec, plan` | production | `summary, spec, plan` |
| `summary, spec, plan` | development | `summary` |

`small` 路由在两个阶段均为 `summary`，`effective_complexity`、`lifecycle_label`、
`complexity_label` 三者两阶段完全一致。非法阶段值抛 `ClassificationError`。

## AC-4 · 合同校验

| 场景 | 结果 |
|---|---|
| `development` + complex + 无 spec/plan | 通过，`required_docs == ("00-summary.md",)` |
| `production` + complex + 无 spec/plan | 拒绝（`01-spec.md`、`02-plan.md` 各自报错） |
| 缺省调用（不传 `change_control`） | 与 `production` 一致，拒绝 |

## AC-5 · 两条不放宽的门槛

**验收标准门槛**：`development` 的 complex 若 Issue 正文没有可测验收，仍以
`development-phase complex Issue requires measurable acceptance criteria in the Issue body`
拒绝。

> 这一条是实现过程中发现的真实缺口：`production` 的 complex 从 **spec** 取 acceptance
> criteria，去掉 spec 后该门槛会连带消失。改为从 Issue 正文取，门槛得以保留——verification
> 文档要证明的正是这些标准，没有标准则 verification 无从成立。

**`verification` 的条件性**：`required_docs` 含 `verification` 同时承载「该变更要部署，
终态是 `deployed` 而非 `completed`」的既有语义（`codex/tools/mark-completed-issues.sh:156`）。
实测两个阶段的条件完全相同：analyzer 未要求时，`development` 输出仅 `summary`，不会凭空
附加 verification 而把不部署的变更误判为要部署。

## AC-6 · 全量回归

| 运行 | 结果 |
|---|---|
| `origin/main` baseline（stash 后实测） | `Ran 437 tests ... OK` |
| 本分支 | `Ran 453 tests ... OK`（新增 16 个） |
| `bash codex/tests/smoke.sh` | 退出码 0，559 行，无 FAIL/ERROR |

`merge_operation_count == 0`、`operation_count == 26` 等既有守门断言全程未改动，
`test-host-access-broker.sh` 与 `test_host_access.py` 均未被触及。

## 解析器的回落路径

以下五条不确定路径实测全部回落 `production`：manifest 文件不存在、内容非法 JSON、
`repositories` 结构异常、仓库未登记、条目取值非法。

## 未在本变更中验证

- 尚无项目实际声明 `change_control: development`——该字段的首次真实取值由各项目在自己的
  manifest 变更中声明（LocalWMS 预计紧随其后）；
- analyzer 端到端（`_render_analysis` / `_apply_analysis`）的 live 运行未验证：
  aisoft-platform 的 `analysis_provider` 为 `codex`，但本变更未触发真实 analyzer 运行，
  接线正确性由单元测试与缺省值覆盖。
