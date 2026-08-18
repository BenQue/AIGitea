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
status: in-progress
branch: change/128-gitea-port-inventory-fix
pr_url: null
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
| mapped documents / tuple resolver | NOT RUN | 待 T01 |
| focused collector tests | NOT RUN | 待 T02/T03 |
| full company-delivery runtime | NOT RUN | 待 T04 |
| shell harness / smoke | NOT RUN | 待 T05 |
| JSON/schema parse | NOT RUN | 待 T04/T05 |
| deterministic bundle repeatability | NOT RUN | 待 T05 |
| no-secret/no-raw review | NOT RUN | 待 T05 |
| diff check / dual-axis review | NOT RUN | 待 T05 |
| Gitea branch/PR/protection/CI readback | NOT RUN | 待 T05 |
| company Stage 10 rerun | NOT RUN | 需新版本合并、重新 Stage 00 与独立批准 |

## Acceptance criteria 结果

| AC | Result | Evidence |
|---|---|---|
| AC-1 | NOT RUN | 待实现与全仓 scoped reference audit |
| AC-2 | NOT RUN | 待 port behavior tests |
| AC-3 | NOT RUN | 待 systemd normalization tests |
| AC-4 | NOT RUN | 待 PostgreSQL template tests |
| AC-5 | NOT RUN | 待 legacy health no-echo tests |
| AC-6 | NOT RUN | 待 runtime/schema negatives |
| AC-7 | NOT RUN | 待 1.1.1 deterministic bundle |
| AC-8 | NOT RUN | 待 PR/CI handoff |
| AC-9 | PASS | 本 Change 未运行公司命令；Stage10 appserver 与 Stage20+ 保持 NOT RUN |

## Review findings 与剩余风险

待 T05 填写。`8888` 只能在未来公司 1.1.1 collector 实测后写为 free；本地 fake test、PR 或 CI 均不能替代。
