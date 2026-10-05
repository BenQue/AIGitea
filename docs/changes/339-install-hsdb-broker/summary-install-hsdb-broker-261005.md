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
status: awaiting-triage
branch: change/339-install-hsdb-broker
pr_url:
created: 2026-10-05
updated: 2026-10-05
---

# #339 HSDB 注册安装运维合同 · 执行后修正

原合同/完整卡已人类批准，本票唯一owner/branch/worktree未变。原窗口21:54:55–22:39:55已STOP；primary已exact FF至c9b5ef4e74592cbc68d6bdc6219568a1d51b6853。两端首次installer exit0，但实际installed→候选发现原卡遗漏的SFMDigitalBoard依赖读取边，停止后真实恢复两端baseline并独立验证PASS。

当前状态：STOP_BASELINE_RESTORED / WAITING_INCREMENTAL_SCOPE_WINDOW_APPROVAL。两端installed均六仓36操作/HSDB unknown，previous installed source SHA仍NOT VERIFIED；T01B未完成，T02仍WAITING_DEPENDENCY。

## 实际 installed 与候选的完整共享面差异

比较基线是本窗口两端真实非Secret snapshots，不是旧source SHA。Mac与VM结果相同；逐字段全量比较见 `full-installed-policy-diff.json`。

| 对象 | 实际 installed → exact pin 候选 | 影响/批准边界 |
|---|---|---|
| 原六仓 host项目项 | 仅 `sfm-digital-board/dependency_read_targets` absent → `["aisoft-platform"]` | 新增受管跨仓Issue依赖只读边；原卡遗漏，必须明确纳入修正版范围 |
| 原36项 operations | 全部定义同字节/同字段，无删除或更改 | 既有操作声明保持 |
| 新operations | `gitea.dependency.read`：manager-audit、mutating=false、reference；`gitea.credential.rotate`：credential-operator | 安装声明；本票不调用这两项 |
| host顶层 | 新增 `credential_rotation_policy` | UID0、固定grant/receipt/helper/operator/Gitea路径和Gitea1.26.4约束；不创建grant/Secret、不启用轮换 |
| 原六仓 governance | 仅 NewEMaint `routine_live_pilot/non_target_repositories_sha256`：4969422f72782de90155881cc4a92720dfd1ee5f468e940bd30ac7a666b0df85 → d45a20abb3224a5e02b1e22c338429017c9ff88d80fd5fc597bffb97a90e9334 | HSDB加入非目标集合后的seal重pin；routine policy和启用状态不变 |
| 新项目/仓库 | host `hsdb`、governance `HSDB` | Mac-only、vm_profile:null |
| labels / 其它顶层 / 其余原六仓字段 | 全部相同 | 无其它遗漏或删除 |
| VM profiles | 精确 aisoft-platform/localwms/emaintenance；newemaint是project_id，emaintenance是profile name | HSDB不进入VM profile；保留IMPLEMENT_PROVIDER=none |

字段来源：`f98c90ee0a34aa2c90b217c1c69a29b3be8386a7`，`feat(#286 T02): resolve manifest-bound dependency references through audit reads`。它在旧source e2edb3e已存在，但两端实际installed尚未包含，所以相对旧source无变化不能推出相对installed无变化。
源码 `resolve_target()` 只允许canonical owner/受管repo及显式source→target edge；`_read_dependency()` 用manager-audit，要求精确非site-admin身份、禁止redirect、限制response大小；返回repository/number/reference/state/labels，不返回Issue正文。这个字段不增加sfm-board-agent的Gitea collaborator权限、Git写入或merge/deploy授权，但确实新增broker允许的跨仓只读边，因此不能继续宣称原六仓policy完全不变。
本窗口没有实际调用SFMDigitalBoard依赖读取，也没有调用credential rotation；上述影响来自exact pin源码和manifest，不冒充live capability验收。

## 下一frontier

[spec](spec-install-hsdb-broker-261005.md)包含Revision 2完整卡与AC；[plan](plan-install-hsdb-broker-261005.md)定义下一完整窗口；[verification](verification-install-hsdb-broker-261005.md)区分首次安装/真实恢复/NOT RUN。
原批准有效且有原始人类记录；修正版新增读取边/具体root入口/新窗口尚未批准。总调度先审阅，再向用户询问具体增量和新窗口，本聊天不重开窗口或重复原scope审批。

只更新四份文档及Issue正文、本聊天artifact。complex/security/change/manual，IMPLEMENT_PROVIDER=none；无source/runtime/AGENTS修改，#333/#327/#336归属保留。最终唯一manual文档PR仍未push/提交/CI，需原平台门禁；若main未来变化，重新审pin，不因文档准备自行安装。
