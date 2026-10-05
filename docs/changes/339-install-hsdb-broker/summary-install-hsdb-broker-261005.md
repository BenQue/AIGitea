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
status: approved
branch: change/339-install-hsdb-broker
pr_url:
created: 2026-10-05
updated: 2026-10-05
---

# #339 HSDB 注册安装运维合同 · 已安装验收

原合同和Revision2增量/新窗口已批准。完成两端同pin两次安装→真实fresh snapshot restore→原baseline验收→同pin再安装→最终七仓38的完整闭环；当前 **INSTALLED_ACCEPTANCE_PASS**，不再处于STOP或待新窗口批准。
本票唯一owner/tuple未变，source/current main=c9b5ef4e74592cbc68d6bdc6219568a1d51b6853。T01B安装AC-1至AC-6 PASS；账号/credential/access仍HTTP_401 GAP，AC-7总调度独立核验PASS，已于2026-10-05T23:08:43+09:00单独激活T02。本票不修该GAP或借安装批准运行canary/Secret步骤。

## 已批准并验证的完整共享面差异

比较基线是本窗口两端真实非Secret snapshots，不是旧source SHA。Mac与VM结果相同；逐字段全量比较见 `full-installed-policy-diff.json`。

| 对象 | 实际 installed → exact pin 候选 | 影响/批准边界 |
|---|---|---|
| 原六仓 host项目项 | 仅 `sfm-digital-board/dependency_read_targets` absent → `["aisoft-platform"]` | Revision2已明确批准；installed目标字节及manifest已核验，新操作未实际调用 |
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


## 交接与生命周期

完整实测见[verification](verification-install-hsdb-broker-261005.md)，合同AC和冻结卡见[spec](spec-install-hsdb-broker-261005.md)，已完成ticket及后续边界见[plan](plan-install-hsdb-broker-261005.md)。[机读handoff](/Users/benque/.codex/visualizations/2026/10/05/01a10bea-8743-7d12-bd55-addf317088bc/t01b-install-execution/window-2/handoff-339.json)分开source/installed/credential/现场证据。
没有source/runtime/AGENTS改动；只写本票四份文档、#339正文和本聊天artifact。complex/security/change/manual；IMPLEMENT_PROVIDER=none。source #337保持closed，#333/#327/#336及其它owner归属不动。
本地文档提交不等于已push/PR/CI或manual merge；最终唯一文档PR仍需既定提交确认和人审。安装结果不传递部署、账号/Secret或其它项目现场授权。Issue保持open；本轮fresh判级读回仍缺type/security与complexity/complex。原安装卡明确排除labels/push/PR，相关后续写入需要独立具体授权。未投影approved/completed。

总调度退出门与T02激活证据已fresh读回；详见verification。安装完成与Issue文档交付收尾分别核验。
