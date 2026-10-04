---
issue: 337
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/337
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
confidence: high
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
depends_on: []
status: approved
branch: change/337-restore-hsdb-governance
created: 2026-10-04
updated: 2026-10-04
reason: 恢复已退出 HSDB 的平台治理注册，命中平台治理、Agent、安全和共享核心强制复杂规则
required_docs:
  - summary
  - spec
  - plan
  - verification
documents:
  summary: summary-restore-hsdb-governance-261004.md
  spec: spec-restore-hsdb-governance-261004.md
  plan: plan-restore-hsdb-governance-261004.md
  verification: verification-restore-hsdb-governance-261004.md
override_reason: ''
pr_url:
---

# Summary 恢复 HSDB 治理注册

## 问题/需求总结

2026-10-04 用户已授权总调度「HSDB 调度：接入、修复、UAT 与公司试运行」按顺序推进，
本会话只负责平台恢复注册。#252 退出记录保持历史原样；新工作绑定 #337，
owner=`01a10739-4622-7be1-ba10-0a92d8fc9905`，总调度=`01a1071e-d973-71a1-99a8-da35d447d1cd`。
Blocked by：none；#327/#333/#336 非授权或凭据来源。

fresh 平台 `origin/main=e2edb3e08194624a6647212571c6cc866298575b`，干净 main；open PR 为空，
未发现重复 HSDB 恢复 Issue。source/installed 两份 manifest 均没有 HSDB，installed broker 拒绝该 project。

## 影响范围

只恢复 `project_id=hsdb` / `admin/HSDB`。两份 manifest、相关花名册断言、HSDB 最小权限回归、
README/03 在册描述及本 Issue 证据；具体受控授权以 mapped spec 为准。
没有生产 runtime、Agent 行为、AGENTS、controller、CI、部署/安装脚本改动。

## 初步方案与建议

以独立治理步骤恢复 Mac typed 注册，`vm_profile=null`、remote 默认 `origin`。
保留 private、`hsdb-agent` Write、人工 main merge、`CI / test (pull_request)`；
routine merger=null、auto-merge=false。production change control 和 selective deploy 默认值保持原合同。
VM 精确集合仍为 aisoft-platform/LocalWMS/NewEMaint；没有启用自动 analyzer/implementation/timer。
两份 manifest 与 NewEMaint non-target seal 同原子 commit 更新。

## 风险

- 两份 manifest 与 seal 必须同时提交，否则整份 broker contract fail closed。
- live `hsdb-agent` Write 但 `prohibit_login=true`；Mac token 文件存在、mode=0600，仅读 metadata。
  未证明凭据可用；解除停用、Secret provision/rotation 均需独立 HSDB scope。
- HSDB live main=`6114c912310bbaf281bbfe77743abd8cff99087d`，本地 main=`8e7f5d19c0e7cdc627907dc0962f7285025fb860`。
  下游必须 fresh 对齐；本会话不更改项目 checkout、Issue #15/#18 或业务代码。
- source/local PASS 不代表 CI、installed、live adoption、UAT 或公司部署 PASS。

## AI 判级

```yaml
change_type: platform
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 恢复已退出 HSDB 的平台治理注册，命中平台治理、Agent、安全和共享核心强制复杂规则
risk_flags:
  - platform-governance
  - agent-governance
  - security
  - shared-core
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

- 两份 manifest、#252 history 与 [fresh preflight](evidence/preflight.json) 证明注册缺失。
- live main protection 为 private/manual 与 exact required CI；恢复注册涉及安全/平台治理，强制 complex。
- [spec](spec-restore-hsdb-governance-261004.md) 与 [plan](plan-restore-hsdb-governance-261004.md) 完整限定治理步骤。
- 合同/启动授权来自本会话收到的用户 T01 指令，允许补齐合同并立即实施；不增加重复启动确认。

### 缺失的 acceptance criteria 或决策

本地治理切片无未决合同。最终 PR 提交、人工 merge 和受保护安装各遵循具体门禁；
现场账号/credential readiness 与下游应用基线差异为真实 GAP。

## 本地候选结果

治理 commit `2aeb5b2a69ea581a64fdbc78d93cff8f2957c0da`；严格/246 targeted/full smoke/源码 rollback 本地 PASS。
分类标签读回 projected。状态为 AWAITING_PR_CONFIRMATION；source merge、required PR CI、installed、account/Secret、UAT/部署未完成。
最终 exact candidate receipt 在本聊天共享证据目录；[verification](verification-restore-hsdb-governance-261004.md) 保留分层事实与安装恢复卡。
