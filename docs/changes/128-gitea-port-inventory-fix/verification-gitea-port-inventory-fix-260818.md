---
issue: 128
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/128
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
depends_on:
  - 126
status: pr-open
branch: change/128-gitea-port-inventory-fix
pr_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/pulls/129
created: 2026-08-18
updated: 2026-08-18
---

# Verification：Stage 10 固定端口 8888 与 inventory 兼容修复

## 执行边界

- Repository source baseline：`origin/main` `d4ff948332dd9aacff5292c9f283346b4ee743b7`。
- 本 Change 只修改 AISoftPlatform source/docs/tests，不访问公司内网或读取公司 Secret。
- 公司 operator 1.1.0 Stage 00：`PASS`（公司侧独立 evidence，不复制到本仓库）。
- 公司 Stage 10 `scm-ci`：strict inventory 结构验证通过，outcome=`BLOCKED`；旧 evidence 保持不变。
- 公司 Stage 10 `appserver-prod` 与 Stage 20–110：`NOT RUN`。
- Gitea/PostgreSQL/Runner/service/Docker/network/repository mutation：`NOT RUN`。

## 验证矩阵

| Gate | Result | Evidence |
|---|---|---|
| mapped documents / tuple resolver | PASS | `resolve-documents 128` 精确返回同一目录的 summary/spec/plan/verification 四个 basename |
| focused collector tests | PASS | `CompanyDeliveryCollectorTests`：18 tests OK；覆盖 8888、Ubuntu unit pair、PostgreSQL template 与 legacy HTTP 固定 reason |
| full company-delivery runtime | PASS | `python3 -m unittest codex.runtime.tests.test_company_delivery`：77 tests OK |
| shell harness / smoke | PASS | real-release harness PASS；`bash codex/tests/smoke.sh` exit 0，438 tests OK，结尾 static smoke PASS |
| JSON/schema parse | PASS | transition schema、compatibility 与全部 templates 通过 `json.tool`；smoke 对全部 company-delivery JSON 再校验 |
| deterministic bundle repeatability | PASS（local fake only） | bundle repeatability/self-verification unit 与 smoke PASS；`docker_calls=0`，不是公司 Stage 00 |
| no-secret/no-raw review | PASS | sensitive JSON key、raw body/status/exception sentinel 与 Docker raw-output negatives 全部 fail closed 且 no-echo |
| diff check / dual-axis review | PASS | `git diff --check origin/main...HEAD`、bash `-n`、ShellCheck PASS；source/schema/runtime/tests 与 docs/templates/compatibility 对账 0 finding |
| Gitea branch/PR/protection/CI readback | PARTIAL | PR #129 open/mergeable/unmerged；初始 head `c714da8d0b2f4ef97ca57b7c75fc740b3e62916f`；main 禁止 push/force-push，仅 `admin` 可合并；初始 CI pending，最终 projection head 待 push/readback |
| company Stage 10 rerun | NOT RUN | 需新版本合并、重新 Stage 00 与独立批准 |

## Acceptance criteria 结果

| AC | Result | Evidence |
|---|---|---|
| AC-1 | PASS | fixed runtime/transition/schema/template/compatibility/docs target 为 `127.0.0.1:8888`；平台自身 3000 references 未改 |
| AC-2 | PASS | 3000 occupied 不再被探测；8888 free 可通过，occupied/unknown 精确 BLOCKED |
| AC-3 | PASS | 仅 enabled=`not-found` + active=`inactive|not-found` 归一化；unsafe pair negatives PASS |
| AC-4 | PASS | preflight 只接受 PostgreSQL `not-found/not-found` 或 `disabled/inactive`；post-install 仍为 `enabled/active` |
| AC-5 | PASS | 3xx/4xx/5xx/request/invalid/sensitive/oversized/duplicate 响应均为固定 reason 且 no-echo |
| AC-6 | PASS | runtime 与 schema 接受 exact safe states，拒绝 target、version、service 与 inventory drift |
| AC-7 | PASS（local fake only） | operator/templates/bundle 全部为 1.1.1；repeatability、tamper 与 no-secret tests PASS |
| AC-8 | PARTIAL | 唯一 PR #129、exact branch/body 与人工 merge protection 已回读；最终 projection head/CI 待 push/readback |
| AC-9 | PASS | 本 Change 未运行公司命令；Stage10 appserver 与 Stage20+ 保持 NOT RUN |

## Ticket 执行记录

| Ticket | Result | Atomic commit / evidence |
|---|---|---|
| T01 | PASS | mapped complex docs + regression baseline：`7a317d113f109c5813d132cd98376d0ae103d6ac` |
| T02–T03 | PASS | 8888/systemd/health collector + runtime/schema：`c6d4928bd4427fe61ed12e29bf7f3c7e4eecd3e1` |
| T04 | PASS | operator 1.1.1、transition/templates/compatibility/runbook/package tests：`64eb9feb461c1719bcc11f66058a6990f3f68293` |
| T05 | PARTIAL | local verification/review PASS；PR #129 已创建；final projection commit、push/head/CI readback 待执行 |

## Review findings 与剩余风险

- Standards review：PASS，0 hard violation / 0 judgement finding。
- Spec review：PASS，AC-1–AC-7/AC-9 由 tests、schema、docs 与 no-echo negatives 覆盖；AC-8 只剩远端 handoff。
- 计划中的 `codex/tests/test-company-delivery.sh` 在 baseline 不存在；实际执行仓库存在的
  `test-company-delivery-real-release-harness.sh` 与全仓 `smoke.sh`，不存在路径不记为 PASS。
- PR #129 body 精确包含一次 mapped summary 和一行 `Closes #128`；protected `main` 禁止 agent push/force-push，
  merge whitelist 仅为 `admin`。最终 projection head 与 CI 通过 typed broker 写入 Issue audit comment，避免文档自引用。
- `8888` 只能在未来公司 1.1.1 collector 实测后写为 free；本地 fake test、PR 或 CI 均不能替代。
- 旧 1.1.0 Stage00/Stage10 evidence 保留历史身份，transition 明确拒绝复用；`appserver-prod` 继续 `NOT RUN`。
