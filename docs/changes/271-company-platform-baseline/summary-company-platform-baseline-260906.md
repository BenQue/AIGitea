---
issue: 271
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/271
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增公司平台只读接管证据合同和采集器，涉及安全与严格 schema，固定走 manual。
risk_flags:
  - security
  - schema
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-company-platform-baseline-260906.md
  spec: spec-company-platform-baseline-260906.md
  plan: plan-company-platform-baseline-260906.md
  verification: verification-company-platform-baseline-260906.md
depends_on:
  - 268
status: approved
branch: change/271-company-platform-baseline
pr_url:
created: 2026-09-06
updated: 2026-09-06
---

## 问题/需求总结

来源 #268 B1 与调度任务 01a0762f-10f7-7543-8936-d90ec3907706。建立公司既有 scm-ci/Gitea 的只读接管基线；用户已批准本 Issue 合同与启动，现场 mutation 未授权。

## 影响范围

只新增本 Issue 文档、独立 baseline collector/schema/用户检查包及针对性测试。现有 company-delivery 安装器、AGENTS.md、skills、controller、CI、broker manifests 均不修改。

## 初步方案与建议

固定环境、主机指纹、source/collector SHA 和 evidence UUID，stdout 输出脱敏 inventory/checksum/receipt；current/historical 分层，缺失当前证据 fail closed。不能访问公司主机时交付版本化用户只读采集包，现场保持 BLOCKED_EXTERNAL。

## 风险

- 历史或 mock PASS 被误当作当前现场证据。
- 诊断泄露配置/日志/凭据；collector 使用固定命令和输出投影。
- 错误将 adopt 决策继承为后续写入授权。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增公司平台只读接管证据合同和采集器，涉及安全与严格 schema，固定走 manual。
risk_flags:
  - security
  - schema
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- Issue #271 正文及零评论已通过 broker 读回。
- 既有 aisoft_company_delivery.collector 只支持 greenfield preflight/post-install 且写文件，不能直接满足本 Issue。
- 公司现场未访问；#268 spec/plan 已读取。

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。
