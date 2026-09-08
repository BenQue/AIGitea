---
issue: 278
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/278
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - schema
  - security
  - external-contract
  - shared-core
depends_on: []
status: pending
branch: change/278-baseline-probe-remediation
created: 2026-09-08
updated: 2026-09-08
---

# Verification · #278 baseline probe remediation

## 基线与范围

- Commit SHA：NOT RUN；实现尚未开始。
- 基线：`origin/main = 874e7169d9f8efbfe707114e71992e5d4333138f`。
- 环境：Mac 本地隔离 worktree `/private/tmp/issue-278-baseline-probe-remediation`；公司 installed/live 不可从开发机访问。
- 本记录负责证明：AC-1 至 AC-10 的 source/local compatibility、安全边界、bundle 可复核性及 installed/live 分层。

## 改动前一次性证据

| Observation | Result | Boundary |
|---|---|---|
| NewEMaint #79 v2 envelope offline verify | PASS（结构）/ BLOCKED_EXTERNAL（采用） | schema、checksum、pins 与 receipt 一致；不代表 current 事实满足 profile |
| Gitea service | PASS | `enabled + active`；仅说明 systemd 状态 |
| Gitea binary | 现场事实 PASS / collector BLOCKED | 实际输出使用小写 `gitea version 1.26.4 built with ...`；现 regex 只接受大写前缀 |
| PostgreSQL service | 现场事实 GAP / collector BLOCKED | `enabled-runtime + active`；现 schema 无法表达；不得提升为持久 enabled |
| Gitea listener/health/API | GAP / BLOCKED | 8888 无监听，两个固定 GET 均 `ConnectionRefusedError`；不扫描其它端口 |
| Runner unit | GAP | `not-found + inactive`；Runner activation 不在本 Issue |
| UFW | BLOCKED | 非特权调用 rc=1、stdout 为空；`false/0` 是空输出解析默认值，不是防火墙事实 |

以上为用户经独立授权从公司现场回传的脱敏结果；本 Issue 不保存 host hash、内部地址、配置、规则、日志或 Secret，也不把它们重解释为平台 source PASS。

## 执行结果

| Command / check | Result | Evidence |
|---|---|---|
| broker open-Issue duplicate check | PASS | 创建前 `count=0` |
| broker create/read/labels/comments for #278 | PASS | Issue #278 open；`needs-analysis`；正文回读一致；comments=[] |
| broker `git.fetch.main` | PASS | project=`aisoft-platform`；`origin/main=874e716…` |
| analyzer result validation/render | PASS | `platform / complex / change / manual`；slug=`baseline-probe-remediation`；required summary/spec/plan/verification |
| implementation/tests | NOT RUN | 等待合同/启动确认 |
| diagnostic review bundle | NOT RUN | source 尚未实现；公司执行不在本 Issue 授权内 |

## Acceptance criteria 结果

| AC | 结论 | 证据 |
|---|---|---|
| AC-1 | NOT RUN | 待实现与回归 |
| AC-2 | NOT RUN | 待实现与回归 |
| AC-3 | NOT RUN | 待实现与回归 |
| AC-4 | NOT RUN | 待实现与回归 |
| AC-5 | NOT RUN | 待实现与回归 |
| AC-6 | NOT RUN | 待实现与回归 |
| AC-7 | NOT RUN | 待实现与回归 |
| AC-8 | NOT RUN | 待静态与 Secret sentinel 审查 |
| AC-9 | NOT RUN | 待生成 disposable review bundle |
| AC-10 | NOT RUN | 公司安装/执行固定不运行；source/local 待验证 |

## 遗留风险与未完成项

- #278 尚未取得绑定 exact Issue/branch/spec/plan 的 Development Loop 启动确认。
- 不修改或追溯改写 NewEMaint #79 的旧 envelope；平台 merge 后必须由项目仓另行 repin、重新授权并使用新 UUID。
- Gitea 8888、PostgreSQL persistent enablement、Runner 与 UFW owner review 是现场整改/审核事项，不由本 source PR 执行。
- 公司诊断、安装、service/UFW/Runner/database mutation、PR merge 全部 NOT RUN。
