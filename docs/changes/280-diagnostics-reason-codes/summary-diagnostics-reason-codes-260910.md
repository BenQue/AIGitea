---
issue: 280
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/280
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
confidence: high
risk_flags:
  - external-contract
  - security
  - deployment
depends_on: []
status: approved
branch: change/280-diagnostics-reason-codes
created: 2026-09-10
updated: 2026-09-10
reason: 新增 closed diagnostics v2 原因枚举与协议存在性投影，影响外部证据 schema、兼容和离线制品，命中强制 complex
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-diagnostics-reason-codes-260910.md
  spec: spec-diagnostics-reason-codes-260910.md
  plan: plan-diagnostics-reason-codes-260910.md
  verification: verification-diagnostics-reason-codes-260910.md
override_reason: ''
pr_url:
---

## 问题/需求总结

来源为 NewEMaint #79、总控 #80 的明确委派。#278 已合并交付 diagnostics v1，其 fail-closed 行为未被推翻；
新问题是不同原因输出同一结果，现场操作员无法确定下一步。平台全量 146 Issues 查重无开放承接后，
建立唯一 #280；用户随后明确回复“实施批准”，broker 已回读 approved/complexity/complex/type/platform。

## 影响范围

固定基点 origin/main = de4581ede598150904695a1821c5489e9cd9a6ad。
唯一 tuple 为 change/280-diagnostics-reason-codes、issue-280-diagnostics-reason-codes 和本目录。
平台 manifest 未声明 change_control，按 production 处理。本票实施已获批准；已新增独立 v2 runtime/schema/builder/guide 与本地测试。

## 初步方案与建议

新增独立 company-platform-baseline-diagnostics/v2，v1 全部历史代码/schema/包保持原字节。
以 protocol_state 表达 missing/http/other，以固定原因枚举表达探针失败阶段。未知输入继续 BLOCKED，
不采用 Gitea 默认值，不跳过未知 UFW 行，不新增现场探针或输出原始配置。
详见 spec AC-1–7 与 plan T01–T03。

## 风险

新版本必须使用独立入口与 schema，拒绝版本混淆；不能将 command-failed 推定为权限不足。
现场 UFW 根因仍未知。源码通过不等于现场通过，#79 approved 不授权本票实施。
最终 PR 为 manual，本轮不 push/PR/merge/安装/现场操作。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增 closed diagnostics v2 原因枚举与协议存在性投影，影响外部证据 schema、兼容和离线制品，命中强制 complex
risk_flags:
  - external-contract
  - security
  - deployment
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

12 个合成用例证明缺失/注释/https 协议映射相同，六类 UFW 失败映射相同。
新增外部 schema 与离线交付格式属于 add/complex。verification 保存改动前证据及原始源码摘要；
v2 targeted 25/25 与包含旧版的回归 104/104 PASS；现场仍 NOT RUN。

### 缺失的 acceptance criteria 或决策

合同技术选择已固定，无实施方向未决项。T01–T03 已按实施批准完成本地实现与回归；等待最终 PR 提交确认。
