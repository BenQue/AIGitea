---
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 两端共享 broker 安装及恢复涉及安全、共享核心和平台治理，强制按 complex/manual 处理。
risk_flags:
  - security
  - shared-core
  - deployment
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
documents:
  summary: summary-install-hsdb-broker-261005.md
  spec: spec-install-hsdb-broker-261005.md
  plan: plan-install-hsdb-broker-261005.md
  verification: verification-install-hsdb-broker-261005.md
issue: 339
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/339
depends_on:
  - 337
status: contract-drafting
branch: change/339-install-hsdb-broker
pr_url:
created: 2026-10-05
updated: 2026-10-05
---

# #339 HSDB 注册安装运维合同

## 问题/需求总结

#337 已 closed/completed、source PR #338人工合并；Mac/gitea-ci root安装面仍六仓/36操作且拒绝HSDB。本票追踪独立安装与注册验收，保留账号/credential/onboarding GAP，供总调度决定T02准入。

本轮授权只有立案、Issue合同发布、独立本地语义文档准备；当前没有approved、PR、安装、恢复或Secret授权。完整合同已在本Issue正文可审阅，本地文件不冒充main或已发布PR。

## 影响范围

| 对象 | exact范围 |
|---|---|
| Issue | [#339](http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/339)，admin/aisoft-platform |
| 唯一writer/执行owner建议 | 01a10bea-8743-7d12-bd55-addf317088bc，本T01B聊天 |
| branch/worktree | change/339-install-hsdb-broker / /private/tmp/issue-339-install-hsdb-broker；已claim，无接管其它owner |
| source pin | c9b5ef4e74592cbc68d6bdc6219568a1d51b6853；本worktree是文档准备，禁止作为安装源 |
| 当前文件范围 | 本目录映射summary/spec/plan/verification四份文档 |
| 原六仓 | 共享runtime全部会更新；原声明/权限保留，仅NewEMaint非目标seal随集合重pin |
| installed delta | operations36→38；25固定source目标+生成receipt；四新增、六更新、十六同字节 |
| 既有owner | #333保持helper/PAT现场范围；#327/#336 source归属保留 |
| 前置 | depends_on #337（已终态）；其它Issue无硬依赖；窗口排他是现场gate |
| policy | complex/security/change/manual；IMPLEMENT_PROVIDER=none；不新增配置字段 |

## 初步方案与建议

完整目标/影响/AC/命令/恢复方案见[spec](spec-install-hsdb-broker-261005.md)，执行顺序见[plan](plan-install-hsdb-broker-261005.md)，实测记录见[verification](verification-install-hsdb-broker-261005.md)。

建议本聊天作为唯一执行owner，通过Mac benque和gitea-ci benque/sudo消费已合并版本化installer；授权者为人类用户。
窗口从绑定exact Issue/pin/scope的明确确认后开始45分钟，失败时只允许限定snapshot恢复顺延最多15分钟，合计最多60分钟。全部是proposal，未获批；不要求另增现场人工人名，不代人签署。

## 合同、安装与文档PR边界

本票不修改installer/manifests/runtime/AGENTS或现行规则。现行条款要求消费已合并source及独立exact pin/窗口授权，没有证明必须先把本运维记录PR合并才能消费已有c9b5ef4e installer；因此不额外添加此门禁。
四件套最终入库仍走本票唯一manual PR的确认/CI/人审流程。本轮没有推送/PR；后续若先合并文档PR导致main前进，旧pin会落后，必须重新审变化、选择新pin、更新安装卡。
任何实际治理/工具代码变更必须先受控源合同/人工PR合并并STOP，fresh run后另选pin，不可从本worktree自举安装。

## 风险

primary仍clean main=e2edb3e…、落后5提交；安装前FF需要具体授权且必须再次核无归属冲突。
两端previous installed source SHA仍NOT VERIFIED；observed-byte快照只能证明可恢复字节基线，实际restore NOT RUN。helper/receipt变化即STOP，禁止无artifact清空其它owner声明。
未知账号状态/凭据有效性不以metadata替代。身份、GiteaPAT和sudo权限互不传递。helper:null保留轮换能力未验收。
安装/恢复/root范围等待一次具体审批，不把合同draft或triage label当approved。

## AI 判级

```yaml
change_type: security
requested_complexity: auto
assessed_complexity: complex
effective_complexity: complex
contract_effect: change
reason: 两端共享 broker 安装及恢复涉及安全、共享核心和平台治理，强制按 complex/manual 处理。
risk_flags:
  - security
  - shared-core
  - deployment
  - rollback
  - platform-governance
required_docs:
  - summary
  - spec
  - plan
  - verification
confidence: high
override_reason: ''
```

### 判级证据

共享root runtime、authentication/credential-operator定义、两端非Secret备份恢复与平台治理涉及强制复杂风险；纯文档准备不把后续现场scope降级为small。
verification必须保留本轮before-state和实际installed/restore证据，不由diff/CI可完全复现。

### 待人确认的具体范围

[Spec的确认卡](spec-install-hsdb-broker-261005.md)绑定实际#339、current source pin、source FF、两端installer/readback、真实window snapshot restore与同pin再安装及上述执行owner/OS身份/相对窗口。没有approved投影；安装/账号/Secret/服务均NOT RUN。
