---
issue: 440
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/440
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
branch: change/440-preprod-batch-flow
created: 2026-11-09
updated: 2026-11-09
---

# 验证记录：开发阶段批次 Issue 与单确认点

## 基线与范围

- Commit SHA：实现候选 `08a8b52297f459fa629fd155439fd53d1cc430a7`（之后只有本证据提交）
- 基线：`origin/main` = `109ab6ba64cfbfc8085f1786cfcb78f3d0fa4ba0`
- 环境：Mac，源码 runtime；未重装任何 installer
- 本记录负责证明的 acceptance criteria：AC-1 至 AC-5

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| 先改测试、未改 runtime：`python3 -m unittest tests.test_route_policy tests.test_contract` | FAIL（预期） | `FAILED (failures=4, errors=61)`：细化规则表多出 `C1`，解释器拒绝 |
| 改 `route_policy`/`contract` 后同上，加 `tests.test_session_contract` | PASS | `Ran 71 tests … OK`（只有一条「规则集合」断言待改为含 `C1`，已改） |
| `bash codex/tests/smoke.sh`（HEAD `3a288482`） | rc=1 | `test_development_project_prepares_the_synthetic_ticket`：development 夹具卡仍写 `confirm: 2`，被新校验拒绝；夹具改为 `confirm: 1`（`c3be580a`），该问题随后由 R1 P2 的旧卡兼容彻底处置 |
| `bash codex/tests/smoke.sh`（HEAD `c3be580a`） | rc=0 | `Ran 812 tests … OK`；`Codex platform static smoke checks passed.` |
| `bash codex/tests/smoke.sh`（HEAD `08a8b522`） | rc=0 | `Ran 812 tests … OK`；`Codex platform static smoke checks passed.` |
| 反向证明：删掉 `validate_provider_route` 里 stored 2 / policy 1 的例外，跑 `tests.test_route_policy.PreC1CardTests` | FAIL（预期） | `FAILED (errors=1)`；已 `git checkout` 还原 |
| `bash codex/tools/usage-bundle.sh --release 1.23.0 --compatibility minor …`（R1 修复后从 `origin/main` 的 bundle.json 重发同号）与 `--verify` | PASS | `VERIFIED 1.23.0 sha256:064add28b47cd25200469a91377d2894f0edb502034e09a8d4286c37558608fb` |
| `aisoft classify --apply 440` 与 `--verify 440` | PASS | `result: projected`（platform / complex） |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | PASS | `ExecutableRouteTests` 全矩阵：development 得 `confirm: 1` 且记 `C1`，production 得 `2`；`test_route_confirm_one_is_the_development_phase_only` 拒绝 `complex-production` + `1`；`confirm: 3` 越界被拒 |
| AC-2 | PASS | route-policy、`03` §1「开发阶段」与 §7、CONTRACT §2/§3/§5、项目 AGENTS 模板、issue-session-flow、aisoft-platform 技能与 getting-started/greenfield-planning/execution-adapter/onboarding-runbook、aisoft-matt-workflow、GLOSSARY、USER-GUIDE、README/04/08 写明例外；生产阶段原句保留；R2 审查无发现 |
| AC-3 | PASS | 确认点 1/2 标题与原钉子保留；`test_development_phase_keeps_only_confirmation_point_1` 与 runbook 例外钉子新增 |
| AC-4 | PASS | 发布包 `VERIFIED 1.23.0`；新 HEAD smoke rc=0 |
| AC-5 | PASS | 见下节，R2 PASS |

## 交叉审查

| 轮次 | 实现方 | 审查方 | exact head | 结论 | 发现与处置 |
|---|---|---|---|---|---|
| 1 | Claude | Codex gpt-6-astra / high（hc 终端 `review-440`，Herdr 空间 `~` 可见，`--sandbox read-only --ask-for-approval never`） | `3a2884824e80066de572ff2b297639e4d42cde8a`；补审 `c3be580aa3c45c3ea7c2f574abb5432ee93b4a60` | FAIL | 2 P2：存量 development 卡（`confirm: 2`）被拒且阻断 resolve-route，已修为 stored 2 / policy 1 不计差异并加测试与反向证明；多处规范性文字仍无条件要求确认点 2，已在 runbook、技能、execution-adapter、route-policy、getting-started、matt-workflow、README/04/08 加例外并加钉子 |
| 2 | Claude | 同上，同一终端 | `08a8b52297f459fa629fd155439fd53d1cc430a7` | PASS | R1 两项 fixed，新发现无；审查方在只读沙箱跑 28 项定向测试与发布包校验，全量 smoke 由实现方实跑（上表） |

## 遗留风险与未完成项

- 存量 development 项目在采用 1.23.0 后，旧卡仍按两个确认点执行（更严）；会话在 resolve-route 看到 `confirm` 差异后可把卡改为 `1`。
- 「首次生产发布前必须切换到 production」只是合同不变量，没有工具强制；平台不知道项目何时发布生产。
- 本机技能未重装；合并后由人按 issue-session-flow「平台仓重装读回」重装（`NOT RUN`）。
