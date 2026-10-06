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
updated: 2026-10-06
status: contract-drafting
---


## 2026-10-06 实际执行结果

当前终态：**ROLLED_BACK_FLAG / ACCESS_GAP / STOP**。本次批准的有限账号尝试和失败恢复已完成；访问恢复目标未达成，不再启用或追加认证修复。

- 批准绑定原卡 SHA256 `763aa652022da7f045220444087e14f81f5a098bfee5aa3b3404e210b2b31a21`、原doc head `1bd4d61e8992f4f93a21b17619be44ce671c05c0`、原Issue body SHA256 `a3bb337e9db57f328619eab8d5289e5f835b67d70cc079b6f0313674ae7a9619`；原卡及原正文快照保留，以下回填不追溯改写批准对象。
- 直接用户完整批准已收到；首次取消开关点击被CUA自动审核拒绝，账号未变。随后在总调度聊天直接人类答复“确认现在执行原卡单字段操作”，本owner通过read_thread核对userMessage `01a10e95-0a86-7782-89b4-3361c3dc2d3d`，满足操作当下确认后执行。
- 原窗口T0日本时间09:12:51；首次保存截止09:22:51、验收09:32:51、失败恢复09:42:51；未延长。09:21:34.788以现有admin UI保存UID5 `Disable Sign-In true→false`一次，fresh读回false。09:22:11三项固定typed after验收仍各exit20 `HTTP_401 / BLOCKED_EXTERNAL`，故访问恢复FAIL/GAP。
- 09:22:44.024仅同UID5同flag保存false→true恢复一次，随后fresh读回true；实际失败恢复PASS。共1次enable保存+1次restore保存，其它账号无写入。
- UID5其它可见字段与Password空输入保持；Email仅比较相等、不收集；Language UI前后均空且未选择，原始存储值仍NOT VERIFIED，不扩张为全量存储字段审计。UID3 flags、HSDB agent Write/manager Administrator、private、remote main `6114c912310bbaf281bbfe77743abd8cff99087d`和完整protection JSON未漂移；requiredCI仍为 `CI / test (pull_request)`。
- fresh source pin仍 `c9b5ef4e74592cbc68d6bdc6219568a1d51b6853`；Mac installed相关源文件逐字相符。VM安装只沿用此前#339独立验收，本轮未再验或安装。PAT有效性与manager-mutation根因仍NOT VERIFIED，不由401推断。
- 本次只回填本票四文档、Issue正文及脱敏evidence。账号/PAT/password/ACL/protection/profile/binding/provider/timer、Secret/grant/DB、工具安装/服务/HSDB应用或公司部署、push/PR/CI/merge/UAT均未追加执行；provider未启动。冻结合同中的零写入与NOT RUN语句是准备阶段历史。

真实执行证据位于 `/Users/benque/.codex/visualizations/2026/10/05/01a10c83-389d-7ab3-b364-59e108f1ca46/hsdb-account-recovery` 的 `execution-handoff.json`、`execution-human-action-time-confirmation.json`、`execution-before-*.json`、`execution-after-*.json`、保存时间/AX/flags截图及 `账号执行与失败恢复回执.md`。

T02访问目标未通过，Ticket保持pending并因外部访问GAP停止；T03最终PR仍pending。账号窗口已结束，不借此票重试或修改凭据；进一步诊断/安全操作须单独确定具体scope。PR提交及人工合并仍是独立门。

## 本轮文档候选 frontier 与外部动作点

T02 的访问目标仍 pending/FAIL，T03 只完成本地候选准备，未满足最终发表或完成条件。原 Ticket graph 和 depends_on [337,339] 保留；#337/#339 已 closed/completed，不再空等其 merge 或安装。

| 缺口 | 归属 | 本票允许的处理 |
|---|---|---|
| 普通 FF/first-publish 合法通道 | #327 原 owner | 记录缺口和适用证明要求；不借用其本人自举特许、不调用 lease-force |
| 完整 PR 历史公开 reader | #336 原 owner | 等待既有合同真实发表、合并和独立 installed 验收；不安装其未合并候选 |
| #342 同编号 namespace 公开证明 | 对应平台能力 owner 协调现行覆盖范围 | #336 当前仅覆盖 #333；保留 GAP，不擅改其范围、不新建绕行工具或票 |
| 原 AC-4 未达成后的合同终结处置 | 人类负责人 | 提供有界失败尝试候选与后继目标提案；未决定前保持 open/pending，不清依赖 |
| 最终 manual PR 提交 | 人类负责人，在上述硬门满足后 | 才一次请求 exact #342/branch/manual 确认，随后 final-head CI；当前不发可执行提交请求 |

本轮所有无阻塞动作仅四文档回填、角色/文档/分类/差异/claim/clean 检查、原操作及恢复 evidence 完整性复核和本票 Issue 正文回填。平台 owner 的能力动作不由本票实施或发消息催办。

#343 A2/B2 已提供无历史记录的交接提案；只引用其证据，不再次索取旧记录，不启动其安全恢复或清依赖。HSDB 具体项目接入、部署和 UAT 回到项目主控；本票的文档发表缺口不自动阻塞全部项目工作。

## 批准时准备记录（历史快照）

以下保留原准备合同内容；其中“当前未批准/账号写入0/after NOT RUN”均描述2026-10-05准备阶段，不代表上述实际执行结果。原批准文档字节可从原doc head复核。
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
