---
issue: 130
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/130
change_type: platform
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - external-contract
  - shared-core
  - deployment
  - compatibility
  - reliability
  - platform-governance
depends_on: []
status: pr-open
branch: change/130-greenfield-legacy-decouple
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/131
created: 2026-08-19
updated: 2026-08-19
---

# Verification：greenfield legacy decoupling

## 边界

本文件只记录 AISoftPlatform source、tests、portable fake bundle 与 PR CI。公司内网、Stage20、安装、
appserver-prod inventory、新 Stage00 archive 和所有 legacy Gitea 操作均 `NOT RUN`。

## Acceptance evidence

| AC | 状态 | 证据 |
|---|---|---|
| AC-1 Zero legacy probes | PASS | preflight/post-install collector 删除 legacy port、Docker discovery 与 legacy HTTP；spy 断言 preflight `candidate_http_calls=0`、所有模式无 `docker ps`，v3 输出拒绝 `legacy` 字段 |
| AC-2 Candidate isolation | PASS | 固定 8888/55432、paths、units、automation 与 candidate health 的 PASS/BLOCKED 回归通过 |
| AC-3 Strict version boundary | PASS | active transition 只接受 inventory v3/operator 1.2.0；历史 v2/v1 仅由历史 loader/verifier 读取，不能进入 v2 transition |
| AC-4 Transition decoupling | PASS | transition v2 无 legacy baseline/backup/equality，Stage50 prerequisite=`candidate-post-install-health` |
| AC-5 Controlled-upgrade isolation | PASS | active enum 只有 `greenfield-isolated-install|BLOCKED`；controlled-upgrade 输入被拒绝 |
| AC-6 No-echo and security | PASS | candidate health 的 5xx、duplicate JSON、sensitive key 与 version mismatch 均 fail closed，不保存 body/Secret |
| AC-7 Portable consistency | PASS | VERSION/runtime/schema/template/matrix/runbook/handoff 全部为 1.2.0/v3/v2；bundle repeat-build test PASS |
| AC-8 Regression evidence | PASS | focused 41 tests、full 76 tests、platform smoke 437 tests、JSON/bash/diff gates 全部 PASS |
| AC-9 Governed delivery | IN PROGRESS | broker push 与唯一 PR #131 已读回；等待最终 head 的 CI readback |
| AC-10 Company boundary | PASS | 本次未连接公司内网、未生成 archive、未执行 Stage20/安装/appserver inventory/legacy action |

## 命令记录

- `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery.CompanyDeliveryCollectorTests codex.runtime.tests.test_company_delivery.CompanyDeliveryContractTests`：PASS，41 tests。
- `PYTHONPATH=codex/runtime python3 -m unittest codex.runtime.tests.test_company_delivery`：PASS，76 tests。
- `bash codex/tests/smoke.sh`：PASS，437 Python tests + platform static smoke。
- 全部 `company-delivery/**/*.json` 经 `python3 -m json.tool`：PASS。
- 全部 `codex|company-delivery/**/*.sh` 经 `bash -n`，operator 经 ShellCheck：PASS。
- `git diff --check origin/main...HEAD` 与 clean worktree：PASS。
- `test_repeat_build_is_byte_identical_and_self_verifying`：PASS；这是 local fake deterministic bundle test，不是公司候选包。

## Review

- runtime/schema/template/compatibility/runbook consistency：`PASS`
- zero legacy Docker/API calls：`PASS`
- candidate isolation fail closed：`PASS`
- no-secret/no-raw-output：`PASS`
- protected main：历史 live readback 为 direct/force push denied、人工 admin merge only；最终 PR/CI readback 待完成

## 公司状态

- Stage00 1.1.1：历史 `PASS`，不作为 1.2.0 前置。
- Stage10 1.1.1 SCM：历史 `BLOCKED` evidence 保留，不覆盖。
- Stage10 appserver-prod：`NOT RUN`。
- Stage20–110、Gitea/PostgreSQL/Runner 安装与 legacy mutation：`NOT RUN`。
