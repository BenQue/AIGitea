---
issue: 270
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/270
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增独立平台制品、采用、执行与回退合同，涉及平台治理和部署边界。
risk_flags:
  - platform-governance
  - deployment
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-company-platform-bootstrap-260906.md
  spec: spec-company-platform-bootstrap-260906.md
  plan: plan-company-platform-bootstrap-260906.md
  verification: verification-company-platform-bootstrap-260906.md
depends_on:
  - 268
status: approved
branch: change/270-company-platform-bootstrap
pr_url:
created: 2026-09-06
updated: 2026-09-06
---

## 问题/需求总结

现有 company-delivery builder 依赖应用 release/matrix，不能独立交付公司 SCM/平台。#270 建立 platform-bootstrap/v1，来源 #268 A1。

## 影响范围

仅新增 platform-bootstrap/、codex/runtime/aisoft_platform_bootstrap/、目标测试与本目录文档；README 增加入口。现有 application bundle 保持兼容。

## 初步方案与建议

确定性离线 handoff；严格数据合同；脱敏采用分流；固定动作计划和 apply/readback/rollback 入口。

## 风险

- source/local/installed/company live 混淆
- 误将公司现有实例视为空白主机
- 不完整身份、摘要或恢复基线导致错误采用

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: add
reason: 新增独立平台制品、采用、执行与回退合同，涉及平台治理和部署边界。
risk_flags:
  - platform-governance
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

- company-delivery/README.md 和 bundle.py 强制 release_root/release_id/compatibility_matrix
- Issue #270 正文和完整空评论线程已 broker 读回
- 依赖 #268 已 closed + completed，main 包含 PR #269

### 缺失的 acceptance criteria 或决策

- 无；如后续发现缺失则回到 awaiting-triage。

## 执行授权与 triage

用户已在调度任务确认 #270 启动，本任务交接再次明确允许 source 实现与本地提交；不重复启动确认。
triage 结论：enhancement / ready-for-agent。按 release、bundle、bootstrap 概念核对，现有 application builder 不满足独立入口；无既有 platform-bootstrap 或相关拒绝记录。
Policy 为 manual。公司现场、credential、安装/服务/仓库/权限变更、push、PR、merge、deploy 均未授权。

## 状态

Development Loop：`AWAITING_PR_CONFIRMATION`。T01/T02/T03 的 source/local 工作完成，最终 PR 提交确认尚未取得。

35 项 targeted、85 项 application 兼容回归、clean implementation pin 的双次 bundle/负向/rollback dry-run PASS；host `LC_ALL=C` 完整 smoke 含 734 个 Python tests PASS。host 默认 `LC_ALL=C.UTF-8` 的 #268 F8 registry 失败为 `GAP / external to #270`，归 A2；C locale 不替代默认 locale。

实现 pin：`4caf73f9c140a01ba7afd425c9e1fd949a1a63a0`；archive SHA-256：`5aa2036b3a332f2dd0107c1c1e3e0baabc36073e2d3ecb83ae3961e0196e9b5e`。
详见 [verification](verification-company-platform-bootstrap-260906.md)。installed/company live/remote PR/CI/merge 全部 NOT RUN。

调度任务已明确：A1 的 apply/rollback 是完整 source 动作协议，不要求现场 executor；没有独立 B1/B2 绑定时 fail closed。该边界不是 A1 实现缺口。
本地 triage 结论与 live 三维分类分开：type/complexity/approved 已投影；live triage/needs-triage 尚未改变，broker 无对应 typed writer，未旁路调用 API。
