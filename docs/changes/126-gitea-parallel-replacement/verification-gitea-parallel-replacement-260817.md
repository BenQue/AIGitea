---
issue: 126
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/126
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema-change
  - security
  - external-contract
  - shared-core
  - cross-module
  - ci-change
  - artifact
  - deployment
  - compatibility
  - rollback
  - platform-governance
depends_on:
  - 120
  - 124
status: pending
branch: change/126-gitea-parallel-replacement
pr_url:
created: 2026-08-17
updated: 2026-08-17
---

# Verification：greenfield systemd Gitea 并行替换

## 环境与版本

- Baseline：`fbc17787bc0f3cafa4113349d6190b936311ebc3`（protected `origin/main`）。
- Implementation candidate：待实现完成后填写 exact full SHA。
- Operator source version：计划从 `1.0.1` 升至 `1.1.0`。
- Environment：Mac isolated worktree + fake runner/HTTP/port/path/release fixtures only。
- 公司 `scm-ci`、`appserver-prod` 与所有 live Gitea/PostgreSQL/service/network/repository：`NOT RUN`。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| focused company-delivery tests | NOT RUN | 待实现后填写 |
| full runtime unittest discovery | NOT RUN | 待实现后填写 |
| platform smoke | NOT RUN | 待实现后填写 |
| JSON / bash / ShellCheck / diff gates | NOT RUN | 待实现后填写 |
| deterministic 1.1.0 fake bundle x2 | NOT RUN | 待 exact clean candidate commit 执行 |
| tamper/no-secret/security negatives | NOT RUN | 待实现后填写 |
| Standards review | NOT RUN | 待实现后填写 |
| Spec review | NOT RUN | 待实现后填写 |
| protected main / PR / exact head / CI readback | NOT RUN | 待 PR 建立后由 typed broker 回读 |

## Acceptance criteria 结果

| AC | Result | Evidence |
|---|---|---|
| AC-1 Inventory v2 | NOT RUN | 待 focused tests |
| AC-2 Probe safety | NOT RUN | 待 fake security matrix |
| AC-3 Transition state machine | NOT RUN | 待 schema/runtime/CLI tests |
| AC-4 Fixed target identity | NOT RUN | 待 compatibility/static review |
| AC-5 Legacy invariant | NOT RUN | 待 pre/post drift tests |
| AC-6 Initial isolation | NOT RUN | 待 runbook/static assertions |
| AC-7 Portable operator | NOT RUN | 待 bundle repeatability/tamper tests |
| AC-8 Runbook | NOT RUN | 待 stage completeness review |
| AC-9 Validation | NOT RUN | 待 full gates |
| AC-10 Governed delivery | NOT RUN | 待 broker PR/readback；merge 始终不授权 |
| AC-11 Execution boundary | NOT RUN | 公司阶段必须保持 NOT RUN |

## 重复部署

- Local fake deterministic bundle 第一次：`NOT RUN`（不是部署）。
- Local fake deterministic bundle 第二次：`NOT RUN`（不是部署）。
- 公司新 Gitea 第一次安装：`NOT RUN`。
- 公司同版本重复安装/验收：`NOT RUN`。

## 故意失败与回滚

- Local fake malformed Docker ID、multiple IDs、unhealthy legacy、candidate collision、inventory/transition tamper、
  skipped-stage fake PASS、baseline drift 和 Secret sentinel：`NOT RUN`。
- 公司新实例失败与只隔离新 namespace 的回滚：`NOT RUN`。
- legacy Docker Gitea rollback/mutation：不在本 Change 授权范围，固定 `NOT RUN`。
- database restore/delete、DNS/TLS/repo migration/phase-out：`NOT RUN`。

## 遗留风险与未完成项

- 公司 Stage 10 尚未运行，真实 OS/package manifest、legacy loopback port、capacity/collision 与 public-name
  fingerprint 尚无 evidence；在此之前 Stage 20/50 不能获批。
- 本文后续只能填写本地 source/test/bundle/PR 证据；不得把它改写为公司安装、升级或切流量成功。
