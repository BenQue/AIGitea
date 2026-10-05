---
issue: 342
gitea_url: http://gitea-ci.orb.local:3000/admin/aisoft-platform/issues/342
change_type: security
requested_complexity: complex
assessed_complexity: complex
effective_complexity: complex
contract_effect: restore
confidence: high
risk_flags:
  - security
  - rollback
depends_on:
  - 337
  - 339
branch: change/342-hsdb-login-recovery
created: 2026-10-05
updated: 2026-10-05
status: contract-drafting
---

# #342 · 运维计划

## Ticket graph

| Ticket | Delivers | Blocked by | Status |
|---|---|---|---|
| T01 | 唯一Issue/claimed worktree/四文档/只读before/安全政策核查/完整操作卡与hash | - | done |
| T02 | exact用户批准后30分钟内UID5单flag操作、typed验收与必要sameflag恢复，脱敏结果 | T01 | pending |
| T03 | 分层handoff/唯一最终文档PR候选；另经PR提交确认后required CI与人工merge | T02 | pending |

## Expected touch points

- T01/T03只修改本票 `docs/changes/342-hsdb-login-recovery/` 的四个映射文件，本票Issue正文/标签和本聊天artifact。
- T02只有spec中UID5 UI单flag；不改runtime、AGENTS、manifest、安装面或HSDB应用，所有其它owner保持。
- T02尚未获批；人工approval是外部执行前置，表格pending不会触发provider。保持IMPLEMENT_PROVIDER=none。

## 测试与验收映射

| AC | Ticket | 命令/观测 |
|---|---|---|
| AC-1 | T01 | typed issue.list/read，claim-worktree，resolve-required-documents 342，check-change-documents，classification读回，git diff --check |
| AC-2 | T01 | source/policy-findings与UI完整before，spec操作卡人工审阅、卡/文档/正文sha256；无账号写入 |
| AC-3 | T02 | 用户一次exact批准回执；fresh admin/UID/version/完整字段/窗口核对；唯一Update保存及fresh读回 |
| AC-4 | T02 | spec中3条typed入口逐项exit0/PASS；失败停止并sameflag恢复 |
| AC-5 | T02 | before/after完整protection JSON/CI集合、HSDB ACL/private/remote main、UID3对照与唯一UID5写轨迹 |
| AC-6 | T02 | 只有实际失败才sameUID/sameflag有限恢复；没有失败不得造真故障或宣称恢复PASS |
| AC-7 | T03 | source/doc/installed/credential/live/UAT分层handoff；最终PR/merge门另按issue-session-flow |

## 数据库迁移、安装与部署

无DB访问、迁移、installer、服务或应用部署。source pin保持固定；本票不补credential工具、不读取Secret，
不复用#339任何安装/恢复授权或#333 grant。

## 失败恢复与出口

T02严格执行spec的T0+10/+20/+30分钟窗口；最多一次enable保存、至多一次sameflag恢复保存。
批准缺失/漂移/过期则零写入STOP；恢复不可验证/超时STOP并升级，不扩大为manager/PAT/ACL修复。
本阶段T01完成后停 `AWAITING_EXACT_ACCOUNT_CHANGE_APPROVAL`。
#339技术前置PASS不等于其Issue终态，Controller日后依赖门不得绕过；总调度仅核验、T02 adoption仍由原owner实施。
